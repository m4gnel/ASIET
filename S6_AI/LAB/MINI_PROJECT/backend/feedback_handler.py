"""
╔══════════════════════════════════════════════════════════════════════════════╗
║           HYBRID FEEDBACK HANDLER - ZERO LATENCY ANSWER ANALYSIS            ║
║     Database Feedback + Async AI Enhancement + Real-Time User Response      ║
╚══════════════════════════════════════════════════════════════════════════════╝

This module provides three-tier feedback generation for interview answers:
1. INSTANT (< 10ms): Database pattern matching + heuristic scoring
2. FAST (< 500ms): Quick hybrid analysis (DB + local cache)
3. COMPLETE (async): Full Mistral AI analysis with RAG enhancement

The user always gets feedback immediately. AI analysis is done in background.
"""

import json
import time
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from hashlib import sha256
import logging

logger = logging.getLogger(__name__)


class InstantFeedbackEngine:
    """
    Provides immediate feedback by analyzing answer patterns from the database.
    Uses: word count, structural patterns, keyword analysis, historical scores.
    Response Time: < 10ms
    """
    
    def __init__(self, db):
        self.db = db
        
    def analyze_answer_instant(
        self,
        answer_text: str,
        question: Any,
        interview: Any,
        field: str,
        level: str
    ) -> Dict[str, Any]:
        """
        Provide instant feedback based on database patterns and heuristics.
        Returns immediate feedback while Mistral loads in background.
        """
        start_time = time.time()
        
        # Get similar answers from database for comparison
        similar_answers = self._find_similar_answers(answer_text, question)
        
        # Calculate instant metrics
        metrics = self._calculate_metrics(answer_text, question, similar_answers)
        
        # Get pattern-based feedback from database
        feedback_parts = self._generate_pattern_feedback(
            answer_text, question, metrics, similar_answers, field, level
        )
        
        analysis_time = (time.time() - start_time) * 1000  # Convert to ms
        
        return {
            'score': metrics['score'],
            'technical_accuracy': metrics['technical_accuracy'],
            'depth_score': metrics['depth_score'],
            'clarity_score': metrics['clarity_score'],
            'relevance_score': metrics['relevance_score'],
            'communication_score': metrics['communication_score'],
            'confidence_score': metrics['confidence_score'],
            'strengths': feedback_parts['strengths'],
            'weaknesses': feedback_parts['weaknesses'],
            'feedback': feedback_parts['main_feedback'],
            'improvement_plan': feedback_parts['improvements'],
            'model': 'hybrid-instant-db',
            'analysis_time_ms': analysis_time,
            'status': 'INSTANT_DB_FEEDBACK',
            'ready_for_ai_enhancement': True,
        }
    
    def _find_similar_answers(self, answer_text: str, question: Any, limit: int = 3) -> List[Any]:
        """Find similar answers in database for comparison and insights."""
        try:
            from app import Answer
            answer_hash = sha256(answer_text.lower().encode()).hexdigest()[:8]
            
            # Find recently answered similar questions
            similar = Answer.query.filter_by(question_id=question.id)\
                .filter(Answer.word_count.between(len(answer_text.split()) - 20, len(answer_text.split()) + 20))\
                .limit(limit)\
                .all()
            return similar if similar else []
        except Exception as e:
            logger.debug(f"[DB] Similar answer lookup failed: {e}")
            return []
    
    def _calculate_metrics(self, answer_text: str, question: Any, similar_answers: List) -> Dict:
        """Calculate quick metrics based on answer structure."""
        word_count = len(answer_text.split())
        sentence_count = len([s for s in answer_text.split('.') if s.strip()])
        
        # Baseline scoring
        base_score = 5.0
        
        # Content depth scoring
        if word_count < 20:
            base_score -= 2  # Too short
        elif word_count < 50:
            base_score -= 0.5
        elif word_count > 50:
            base_score += 1
        elif word_count > 150:
            base_score += 1.5
        
        # Structural complexity
        if sentence_count > 3:
            base_score += 0.5
        if sentence_count > 6:
            base_score += 0.5
        
        # Keyword presence
        keywords = self._extract_keywords(question.text)
        keyword_matches = sum(1 for kw in keywords if kw.lower() in answer_text.lower())
        if keyword_matches > 0:
            base_score += min(1.0, keyword_matches * 0.3)
        
        # Use similar answers for calibration
        if similar_answers:
            avg_similar_score = sum(a.score for a in similar_answers if a.score) / len(similar_answers)
            base_score = (base_score + avg_similar_score) / 2  # Blend with similar answers
        
        # Ensure score is in range [0, 10]
        final_score = max(0.0, min(10.0, base_score))
        
        return {
            'score': round(final_score, 2),
            'technical_accuracy': round(final_score * 0.9, 2),
            'depth_score': round(final_score * 0.85, 2),
            'clarity_score': round(final_score * 0.8, 2),
            'relevance_score': round(final_score * 0.95, 2),
            'communication_score': round(final_score * 0.9, 2),
            'confidence_score': round(final_score * 0.8, 2),
            'word_count': word_count,
            'sentence_count': sentence_count,
        }
    
    def _extract_keywords(self, question_text: str) -> List[str]:
        """Extract key terms from question."""
        import re
        # Remove common words
        stop_words = {'the', 'a', 'an', 'is', 'are', 'and', 'or', 'what', 'how', 'why', 'when', 'where', 'which'}
        words = re.findall(r'\b\w+\b', question_text.lower())
        return [w for w in words if len(w) > 3 and w not in stop_words]
    
    def _generate_pattern_feedback(
        self,
        answer_text: str,
        question: Any,
        metrics: Dict,
        similar_answers: List,
        field: str,
        level: str
    ) -> Dict:
        """Generate feedback based on patterns and heuristics."""
        feedback = {
            'strengths': [],
            'weaknesses': [],
            'main_feedback': '',
            'improvements': []
        }
        
        # Strengths
        if metrics['word_count'] > 50:
            feedback['strengths'].append('✓ Comprehensive answer with good detail')
        if metrics['sentence_count'] > 2:
            feedback['strengths'].append('✓ Well-structured response with multiple points')
        if any(word in answer_text.lower() for word in ['example', 'specifically', 'instance']):
            feedback['strengths'].append('✓ Provided specific examples or context')
        if not feedback['strengths']:
            feedback['strengths'].append('✓ Answer submitted and being analyzed')
        
        # Weaknesses / Areas for improvement
        if metrics['word_count'] < 30:
            feedback['weaknesses'].append('⚠ Consider expanding your answer with more details')
        if metrics['word_count'] > 300:
            feedback['weaknesses'].append('⚠ Very long answer - consider more concise points')
        if metrics['sentence_count'] < 2:
            feedback['weaknesses'].append('⚠ Break answer into multiple points')
        
        # Main feedback message
        score = metrics['score']
        if score >= 8.5:
            feedback['main_feedback'] = f"Excellent answer! ({score}/10)\n\n"
        elif score >= 7:
            feedback['main_feedback'] = f"Good answer ({score}/10). \n\n"
        elif score >= 5:
            feedback['main_feedback'] = f"Acceptable answer ({score}/10).\n\n"
        else:
            feedback['main_feedback'] = f"Answer received ({score}/10).\n\n"
        
        feedback['main_feedback'] += (
            f"📊 **DB Analysis**: Compared with {len(similar_answers)} similar answers\n"
            f"📝 **Word Count**: {metrics['word_count']} words\n"
            f"🎯 **Structure**: {metrics['sentence_count']} sentence(s)\n\n"
            f"🤖 **AI Analysis**: Loading powerful Mistral analysis in background... "
            f"Will provide detailed feedback in real-time! ⚡"
        )
        
        # Improvement suggestions
        feedback['improvements'] = [
            'Detailed AI feedback coming in real-time',
            f'Compare with top answers for {field.title()} at {level.upper()} level',
            'Practice similar question patterns'
        ]
        
        return feedback
    

class FastHybridFeedbackEngine:
    """
    Provides fast hybrid feedback combining database + local cache.
    Uses pattern matching, cache hits, and lightweight analysis.
    Response Time: 50-500ms (useful if Mistral is not yet ready)
    """
    
    def __init__(self, instant_engine: InstantFeedbackEngine):
        self.instant = instant_engine
        
    def enhance_feedback(self, instant_feedback: Dict, cache_hit: Optional[Dict]) -> Dict:
        """
        Enhance instant feedback with cache data if available.
        """
        if cache_hit:
            # Merge cache data with instant feedback
            logger.info("[FastHybrid] Using cached analysis to enhance feedback")
            return {
                **instant_feedback,
                'cache_enhanced': True,
                'cached_score': cache_hit.get('score'),
                'model': 'hybrid-cache-enhanced',
            }
        return instant_feedback


class AsyncAIEnhancementHandler:
    """
    Handles async AI analysis using Mistral that runs in background.
    User gets instant feedback immediately, AI enhancement comes later.
    The frontend polls or uses WebSocket for real-time updates.
    """
    
    def __init__(self, mistral_agent, db):
        self.mistral = mistral_agent
        self.db = db
        
    def create_enhancement_task(
        self,
        answer: Any,
        question: Any,
        interview: Any,
        answer_text: str,
        instant_feedback: Dict
    ) -> str:
        """
        Create async task for AI enhancement.
        Returns a task_id for polling or WebSocket updates.
        """
        import uuid
        task_id = str(uuid.uuid4())
        
        # Store task info in database for polling
        try:
            from app import FeedbackEnhancementTask
            task = FeedbackEnhancementTask(
                task_id=task_id,
                answer_id=answer.id,
                question_id=question.id,
                interview_id=interview.id,
                status='QUEUED',
                created_at=datetime.utcnow(),
                instant_feedback_json=json.dumps(instant_feedback)
            )
            self.db.session.add(task)
            self.db.session.commit()
            logger.info(f"[AsyncAI] Task created: {task_id}")
        except Exception as e:
            logger.warning(f"[AsyncAI] Task creation failed: {e}")
        
        return task_id


def get_feedback_handler(app, db, mistral_agent):
    """
    Factory function to create the feedback handler system.
    Usage in submit_answer:
        handler = get_feedback_handler(app, db, mistral_agent)
        instant_fb = handler.instant.analyze_answer_instant(...)
    """
    instant_engine = InstantFeedbackEngine(db)
    fast_hybrid_engine = FastHybridFeedbackEngine(instant_engine)
    async_handler = AsyncAIEnhancementHandler(mistral_agent, db)
    
    return {
        'instant': instant_engine,
        'hybrid': fast_hybrid_engine,
        'async': async_handler,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# DATABASE MODELS (Add these to your models section)
# ═══════════════════════════════════════════════════════════════════════════════

"""
# Add this to your models.py or app.py models section:

class FeedbackEnhancementTask(db.Model):
    __tablename__ = 'feedback_enhancement_tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.String(36), unique=True, nullable=False, index=True)
    answer_id = db.Column(db.Integer, db.ForeignKey('answer.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    interview_id = db.Column(db.Integer, db.ForeignKey('interview.id'), nullable=False)
    
    status = db.Column(db.String(20), default='QUEUED')  # QUEUED, PROCESSING, COMPLETE, ERROR
    instant_feedback_json = db.Column(db.Text)
    ai_enhanced_feedback_json = db.Column(db.Text)  # Updated when complete
    error_message = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    
    def get_instant_feedback(self):
        return json.loads(self.instant_feedback_json) if self.instant_feedback_json else {}
    
    def get_enhanced_feedback(self):
        return json.loads(self.ai_enhanced_feedback_json) if self.ai_enhanced_feedback_json else None
    
    def set_complete(self, enhanced_feedback):
        self.status = 'COMPLETE'
        self.ai_enhanced_feedback_json = json.dumps(enhanced_feedback)
        self.completed_at = datetime.utcnow()
        db.session.commit()
"""
