"""
COPY-PASTE IMPLEMENTATION SNIPPETS
For your submit_answer function in app.py

Each section is marked with where to add it in the existing code.
This makes integration step-by-step and painless.
"""

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION A: ADD THESE IMPORTS TO TOP OF APP.PY
# ═══════════════════════════════════════════════════════════════════════════════

# Add after line ~75 (with other imports)
from feedback_handler import get_feedback_handler
import uuid

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION B: ADD AFTER APP INITIALIZATION (around line 120)
# ═══════════════════════════════════════════════════════════════════════════════

# Initialize feedback handler system (3-tier: instant + fast + async)
try:
    feedback_handlers = get_feedback_handler(app, db, mistral_agent)
    app.logger.info("[Init] Feedback handler system initialized")
except Exception as e:
    app.logger.error(f"[Init] Feedback handler failed: {e}")
    feedback_handlers = None

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION C: ADD THESE MODELS TO YOUR MODELS SECTION
# ═══════════════════════════════════════════════════════════════════════════════

# Add to models section (around line 200-300 where other models are)

class FeedbackEnhancementTask(db.Model):
    """Tracks async AI feedback enhancement tasks"""
    __tablename__ = 'feedback_enhancement_tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.String(36), unique=True, nullable=False, index=True)
    answer_id = db.Column(db.Integer, db.ForeignKey('answer.id'), nullable=True)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    interview_id = db.Column(db.Integer, db.ForeignKey('interview.id'), nullable=False)
    
    status = db.Column(db.String(20), default='QUEUED')  # QUEUED, PROCESSING, COMPLETE, ERROR
    instant_feedback_json = db.Column(db.Text)
    ai_enhanced_feedback_json = db.Column(db.Text)
    error_message = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    processing_time_ms = db.Column(db.Integer)
    
    def get_instant_feedback(self):
        return json.loads(self.instant_feedback_json) if self.instant_feedback_json else {}
    
    def get_enhanced_feedback(self):
        return json.loads(self.ai_enhanced_feedback_json) if self.ai_enhanced_feedback_json else None
    
    def set_complete(self, enhanced_feedback):
        self.status = 'COMPLETE'
        self.ai_enhanced_feedback_json = json.dumps(enhanced_feedback)
        if self.started_at:
            self.processing_time_ms = int((datetime.utcnow() - self.started_at).total_seconds() * 1000)
        self.completed_at = datetime.utcnow()
        db.session.commit()

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION D: REPLACE THE ANALYSIS SECTION IN submit_answer
# ═══════════════════════════════════════════════════════════════════════════════

# Find this section (around line 3080):
#
#   if cached_result:
#       # USE CACHED ANALYSIS (HIT!)
#       analysis = cached_result.cached_analysis_dict()
#       analysis['source'] = 'cache'
#   else:
#       # ── STEP 2: QUICK HEURISTIC SCORING
#
# REPLACE that entire else block with:

            if cached_result:
                # USE CACHED ANALYSIS (HIT!)
                analysis = cached_result.cached_analysis_dict()
                analysis['source'] = 'cache'
                app.logger.info(f"[Analysis] CACHE HIT - Pre-computed analysis")
            else:
                # ── GET INSTANT FEEDBACK FROM DATABASE ────────────────────────
                # This gives user feedback IMMEDIATELY while Mistral loads async
                
                if feedback_handlers:
                    analysis = feedback_handlers['instant'].analyze_answer_instant(
                        answer_text=answer_text,
                        question=question,
                        interview=interview,
                        field=interview.field,
                        level=interview.level
                    )
                    app.logger.info(f"[Analysis] Instant DB feedback ({analysis.get('analysis_time_ms', 0):.1f}ms)")
                else:
                    # Fallback if feedback handler not initialized
                    word_count = len(answer_text.split())
                    analysis = {
                        'score': min(9.0, 5.0 + (word_count / 50) * 2),
                        'technical_accuracy': 6.5,
                        'depth_score': 6.0,
                        'clarity_score': 6.0,
                        'relevance_score': 6.5,
                        'communication_score': 6.5,
                        'confidence_score': 6.0,
                        'strengths': ['Answer submitted'],
                        'weaknesses': ['Pending analysis...'],
                        'feedback': 'Answer received. Analysis in progress...',
                        'improvement_plan': ['Detailed feedback coming'],
                        'model': 'fallback-heuristic',
                    }

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION E: REPLACE THE ASYNC THREAD SECTION IN submit_answer
# ═══════════════════════════════════════════════════════════════════════════════

# Find this section (around line 3206):
#
#   # Start async thread
#   async_thread = threading.Thread(target=async_analyze_and_cache, daemon=True, name=f"AsyncAnalysis-{interview.id}")
#   async_thread.start()
#
# REPLACE with:

                # ── START ASYNC AI ENHANCEMENT (Non-blocking background task) ──
                # Create task entry first
                enhancement_task = None
                task_id = str(uuid.uuid4())
                try:
                    enhancement_task = FeedbackEnhancementTask(
                        task_id=task_id,
                        question_id=question.id,
                        interview_id=interview.id,
                        status='QUEUED',
                        instant_feedback_json=json.dumps(analysis)
                    )
                    db.session.add(enhancement_task)
                    db.session.flush()  # Get the ID
                    app.logger.debug(f"[Async] Task {task_id} created")
                except Exception as e:
                    app.logger.warning(f"[Async] Task creation failed: {e}")
                    task_id = None
                
                # Define async AI enhancement function
                def async_ai_enhancement():
                    """Background: Enhance feedback with Mistral AI"""
                    with app.app_context():
                        try:
                            if not task_id:
                                return
                            
                            task = FeedbackEnhancementTask.query.filter_by(task_id=task_id).first()
                            if not task:
                                app.logger.error(f"[AsyncAI] Task {task_id} not found")
                                return
                            
                            task.status = 'PROCESSING'
                            task.started_at = datetime.utcnow()
                            db.session.commit()
                            
                            app.logger.info(f"[AsyncAI] Processing task {task_id}")
                            
                            # Try RAG first (most powerful)
                            ai_analysis = None
                            try:
                                from rag.rag_engine import rag_engine
                                if hasattr(rag_engine, 'is_available') and rag_engine.is_available:
                                    raw_feedback = rag_engine.generate_feedback_rag(
                                        current_question=question.text,
                                        current_answer=answer_text,
                                        company_context=interview.company
                                    )
                                    ai_analysis = mistral_agent._parse_analysis(raw_feedback, answer_text)
                                    ai_analysis['source'] = 'rag-enhanced'
                                    app.logger.info(f"[AsyncAI] RAG enhanced feedback")
                            except Exception as e:
                                app.logger.debug(f"[AsyncAI] RAG unavailable: {type(e).__name__}")
                            
                            # Fallback to standard Mistral
                            if not ai_analysis:
                                ai_analysis = mistral_agent.analyze_answer(
                                    question=question.text,
                                    answer=answer_text,
                                    field=interview.field,
                                    level=interview.level,
                                    company=interview.company,
                                    question_type=interview.question_type,
                                )
                                ai_analysis['source'] = 'mistral-async'
                            
                            # Cache the result for future similar answers
                            try:
                                cache_entry = AnswerCache(
                                    question_hash=question_hash,
                                    answer_hash=answer_hash,
                                    answer_length=answer_length_bucket,
                                    cached_analysis=json.dumps(ai_analysis)
                                )
                                db.session.add(cache_entry)
                                db.session.commit()
                                app.logger.debug(f"[Cache] Result cached for future use")
                            except Exception as e:
                                app.logger.warning(f"[Cache] Failed to cache: {e}")
                            
                            # Update user analytics
                            try:
                                user_analytics = UserAnalytics.query.filter_by(user_id=interview.user_id).first()
                                if not user_analytics:
                                    user_analytics = UserAnalytics(user_id=interview.user_id)
                                    db.session.add(user_analytics)
                                
                                user_analytics.total_questions = (user_analytics.total_questions or 0) + 1
                                user_analytics.avg_technical_accuracy = (
                                    ((user_analytics.avg_technical_accuracy or 0) * (user_analytics.total_questions - 1) + 
                                     ai_analysis.get('technical_accuracy', 5)) / user_analytics.total_questions
                                )
                                
                                db.session.add(user_analytics)
                                db.session.commit()
                                app.logger.debug(f"[Analytics] Updated")
                            except Exception as e:
                                app.logger.warning(f"[Analytics] Update failed: {e}")
                            
                            # Mark task complete with AI feedback
                            task.set_complete(ai_analysis)
                            app.logger.info(f"[AsyncAI] Task {task_id} complete (AI feedback ready)")
                            
                        except Exception as e:
                            app.logger.error(f"[AsyncAI] Error: {type(e).__name__}: {str(e)[:80]}")
                            try:
                                task = FeedbackEnhancementTask.query.filter_by(task_id=task_id).first()
                                if task:
                                    task.status = 'ERROR'
                                    task.error_message = str(e)[:200]
                                    db.session.commit()
                            except:
                                pass
                
                # Start async thread (non-blocking)
                # NOTE: threading is imported at module level (line 60), don't re-import
                try:
                    async_thread = threading.Thread(
                        target=async_ai_enhancement,
                        daemon=True,
                        name=f"AsyncAI-{task_id[:8]}"
                    )
                    async_thread.start()
                    app.logger.info(f"[Async] Enhancement thread started for task {task_id}")
                except Exception as e:
                    app.logger.error(f"[Async] Thread creation failed: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION F: UPDATE RESPONSE TO INCLUDE TASK_ID
# ═══════════════════════════════════════════════════════════════════════════════

# Find the return statement (around line 3300) and add task_id:

        # Return response with task_id for polling
        return jsonify({
            'answer_id': answer.uuid,
            'question_number': question.question_number,
            'task_id': task_id,  # ← ADD THIS LINE for feedback polling
            'analysis': {
                'score': analysis['score'],
                'technical_accuracy': analysis['technical_accuracy'],
                'depth_score': analysis['depth_score'],
                'clarity_score': analysis['clarity_score'],
                'relevance_score': analysis['relevance_score'],
                'communication_score': analysis['communication_score'],
                'confidence_score': analysis['confidence_score'],
                'strengths': analysis['strengths'],
                'weaknesses': analysis['weaknesses'],
                'feedback': analysis['feedback'],
                'improvement_plan': analysis.get('improvement_plan', []),
                'model': analysis.get('model', 'hybrid'),
            }
        }), 201

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION G: ADD POLLING ENDPOINTS (New routes)
# ═══════════════════════════════════════════════════════════════════════════════

# Add these new routes after submit_answer function:

@app.route('/api/feedback/<task_id>/status', methods=['GET'])
@jwt_required()
def get_feedback_enhancement_status(task_id):
    """
    Poll the status of AI feedback enhancement task.
    Returns instant feedback immediately, AI feedback when ready.
    """
    try:
        user_id = int(get_jwt_identity())
        task = FeedbackEnhancementTask.query.filter_by(task_id=task_id).first()
        
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        
        # Verify user owns this interview
        interview = Interview.query.filter_by(id=task.interview_id, user_id=user_id).first()
        if not interview:
            return jsonify({'error': 'Unauthorized'}), 403
        
        response = {
            'task_id': task_id,
            'status': task.status,  # QUEUED, PROCESSING, COMPLETE, ERROR
            'instant_feedback': task.get_instant_feedback(),
            'ai_feedback': task.get_enhanced_feedback(),  # None until COMPLETE
            'created_at': task.created_at.isoformat() if task.created_at else None,
            'completed_at': task.completed_at.isoformat() if task.completed_at else None,
            'processing_time_ms': task.processing_time_ms,
        }
        
        # Include error if task failed
        if task.status == 'ERROR':
            response['error'] = task.error_message
        
        return jsonify(response), 200
    
    except Exception as e:
        app.logger.error(f"[Feedback] Status check failed: {e}")
        return jsonify({'error': str(e)[:80]}), 500


@app.route('/api/interview/<interview_uuid>/feedback', methods=['GET'])
@jwt_required()
def get_interview_feedback_tasks(interview_uuid):
    """List all feedback tasks for an interview"""
    try:
        user_id = int(get_jwt_identity())
        interview = Interview.query.filter_by(uuid=interview_uuid, user_id=user_id).first()
        
        if not interview:
            return jsonify({'error': 'Interview not found'}), 404
        
        tasks = FeedbackEnhancementTask.query\
            .filter_by(interview_id=interview.id)\
            .order_by(FeedbackEnhancementTask.created_at.desc())\
            .limit(50)\
            .all()
        
        return jsonify({
            'interview_uuid': interview_uuid,
            'task_count': len(tasks),
            'tasks': [{
                'task_id': t.task_id,
                'question_id': t.question_id,
                'status': t.status,
                'instant_feedback_available': bool(t.instant_feedback_json),
                'ai_feedback_available': bool(t.ai_enhanced_feedback_json),
                'created_at': t.created_at.isoformat() if t.created_at else None,
                'completed_at': t.completed_at.isoformat() if t.completed_at else None,
            } for t in tasks]
        }), 200
    
    except Exception as e:
        app.logger.error(f"[Feedback] List failed: {e}")
        return jsonify({'error': str(e)[:80]}), 500

# ═══════════════════════════════════════════════════════════════════════════════
# FINAL STEP: CREATE DATABASE TABLES
# ═══════════════════════════════════════════════════════════════════════════════

# In PowerShell/Terminal:
# cd c:\projects\ai_coach_demo_p2\backend
# python
# >>> from app import db, FeedbackEnhancementTask
# >>> db.create_all()
# >>> print("Tables created!")
# >>> exit()

# Done! Start your server:
# python app.py
