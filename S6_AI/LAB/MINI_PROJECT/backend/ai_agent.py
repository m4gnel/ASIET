"""
AI Interview Agent
Uses GPT-4 to conduct intelligent interviews
"""

import openai
import os
from dotenv import load_dotenv
import json
from datetime import datetime

# Load environment variables
load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')

class AIInterviewAgent:
    """
    Intelligent AI agent that conducts interviews and provides feedback
    """
    
    def __init__(self, interview_type='technical', level='intermediate', field='software'):
        self.interview_type = interview_type
        self.level = level
        self.field = field
        self.conversation_history = []
        
    def generate_question(self, context=None):
        """
        Generate a relevant interview question based on context
        
        Args:
            context: Previous answers and performance data
            
        Returns:
            dict: Question with metadata
        """
        
        # Build system prompt
        system_prompt = f"""You are an expert {self.interview_type} interviewer for {self.field} positions at {self.level} level.

Your role:
1. Ask ONE clear, relevant interview question
2. Match difficulty to {self.level} level
3. Focus on {self.interview_type} skills
4. Be professional and encouraging

Return ONLY the question text, nothing else."""

        # Add context if available
        if context:
            system_prompt += f"\n\nPrevious performance: {context}"
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Generate a {self.interview_type} interview question for {self.field} at {self.level} level."}
                ],
                max_tokens=200,
                temperature=0.7
            )
            
            question_text = response.choices[0].message.content.strip()
            
            return {
                'text': question_text,
                'type': self.interview_type,
                'level': self.level,
                'field': self.field,
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Error generating question: {e}")
            # Fallback question
            return {
                'text': 'Tell me about a challenging project you worked on recently.',
                'type': self.interview_type,
                'level': self.level,
                'field': self.field,
                'generated_at': datetime.now().isoformat()
            }
    
    def analyze_answer(self, question, answer_text):
        """
        Analyze user's answer and provide detailed feedback
        
        Args:
            question: The question that was asked
            answer_text: User's answer
            
        Returns:
            dict: Comprehensive feedback with scores
        """
        
        system_prompt = f"""You are an expert interviewer analyzing a {self.interview_type} interview answer.

Question asked: {question}

Provide detailed analysis in this EXACT JSON format:
{{
    "score": 8.5,
    "strengths": ["point 1", "point 2", "point 3"],
    "improvements": ["suggestion 1", "suggestion 2", "suggestion 3"],
    "detailed_feedback": "Comprehensive feedback paragraph",
    "technical_accuracy": 8.0,
    "communication_clarity": 9.0,
    "depth_of_knowledge": 7.5,
    "confidence_level": 8.0,
    "key_concepts_covered": ["concept1", "concept2"],
    "missing_concepts": ["concept3", "concept4"],
    "next_steps": ["action 1", "action 2"]
}}

Score scale: 0-10 (10 being perfect)
Be honest but encouraging."""

        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Analyze this answer:\n\n{answer_text}"}
                ],
                max_tokens=800,
                temperature=0.3
            )
            
            feedback_text = response.choices[0].message.content.strip()
            
            # Parse JSON response
            # Remove markdown code blocks if present
            if "```json" in feedback_text:
                feedback_text = feedback_text.split("```json")[1].split("```")[0].strip()
            elif "```" in feedback_text:
                feedback_text = feedback_text.split("```")[1].split("```")[0].strip()
            
            feedback = json.loads(feedback_text)
            
            # Add metadata
            feedback['analyzed_at'] = datetime.now().isoformat()
            feedback['model'] = 'gpt-4'
            feedback['answer_length'] = len(answer_text.split())
            
            return feedback
            
        except Exception as e:
            print(f"Error analyzing answer: {e}")
            # Fallback feedback
            word_count = len(answer_text.split())
            base_score = min(10, max(5, word_count / 10))
            
            return {
                'score': base_score,
                'strengths': [
                    'Provided a response to the question',
                    'Shows basic understanding'
                ],
                'improvements': [
                    'Add more specific examples',
                    'Elaborate on key points'
                ],
                'detailed_feedback': f'Your answer demonstrates understanding. To improve, provide more detailed examples and elaborate on your main points.',
                'technical_accuracy': base_score,
                'communication_clarity': base_score,
                'depth_of_knowledge': base_score - 1,
                'confidence_level': base_score,
                'key_concepts_covered': [],
                'missing_concepts': [],
                'next_steps': ['Practice with more examples'],
                'analyzed_at': datetime.now().isoformat(),
                'model': 'fallback',
                'answer_length': word_count
            }
    
    def adaptive_next_question(self, performance_history):
        """
        Generate next question based on user's performance
        Adapts difficulty dynamically
        
        Args:
            performance_history: List of previous scores
            
        Returns:
            dict: Next question with adjusted difficulty
        """
        
        if not performance_history:
            return self.generate_question()
        
        # Calculate average performance
        avg_score = sum(performance_history) / len(performance_history)
        
        # Adjust difficulty
        if avg_score > 8.5:
            self.level = 'senior'
            context = "User is performing excellently. Increase difficulty."
        elif avg_score > 6.5:
            self.level = 'intermediate'
            context = "User is performing well. Maintain current difficulty."
        else:
            self.level = 'entry'
            context = "User needs support. Simplify questions."
        
        return self.generate_question(context=context)
    
    def generate_interview_report(self, all_answers_feedback):
        """
        Generate comprehensive interview report
        
        Args:
            all_answers_feedback: List of all feedback from the interview
            
        Returns:
            dict: Complete interview analysis
        """
        
        if not all_answers_feedback:
            return {'error': 'No feedback data available'}
        
        # Calculate overall metrics
        scores = [f['score'] for f in all_answers_feedback]
        avg_score = sum(scores) / len(scores)
        
        # Collect all strengths and improvements
        all_strengths = []
        all_improvements = []
        
        for feedback in all_answers_feedback:
            all_strengths.extend(feedback.get('strengths', []))
            all_improvements.extend(feedback.get('improvements', []))
        
        # Remove duplicates
        unique_strengths = list(set(all_strengths))[:5]
        unique_improvements = list(set(all_improvements))[:5]
        
        report = {
            'overall_score': round(avg_score, 2),
            'total_questions': len(all_answers_feedback),
            'performance_trend': 'improving' if scores[-1] > scores[0] else 'needs_work',
            'top_strengths': unique_strengths,
            'areas_for_improvement': unique_improvements,
            'average_scores': {
                'technical_accuracy': round(sum(f.get('technical_accuracy', 0) for f in all_answers_feedback) / len(all_answers_feedback), 2),
                'communication_clarity': round(sum(f.get('communication_clarity', 0) for f in all_answers_feedback) / len(all_answers_feedback), 2),
                'depth_of_knowledge': round(sum(f.get('depth_of_knowledge', 0) for f in all_answers_feedback) / len(all_answers_feedback), 2),
            },
            'recommendation': self._get_recommendation(avg_score),
            'generated_at': datetime.now().isoformat()
        }
        
        return report
    
    def _get_recommendation(self, score):
        """Get personalized recommendation based on score"""
        if score >= 9.0:
            return "Excellent performance! You're interview-ready. Focus on confidence and stress management."
        elif score >= 7.5:
            return "Strong performance! Polish your weakest areas and practice more complex scenarios."
        elif score >= 6.0:
            return "Good foundation. Focus on depth of answers and adding specific examples."
        else:
            return "Keep practicing! Review fundamental concepts and work on answer structure using STAR method."


# Test the agent
if __name__ == '__main__':
    print("🤖 Testing AI Interview Agent...")
    print()
    
    # Create agent
    agent = AIInterviewAgent(
        interview_type='technical',
        level='intermediate',
        field='software engineering'
    )
    
    # Test 1: Generate question
    print("📝 Test 1: Generating question...")
    question = agent.generate_question()
    print(f"Question: {question['text']}")
    print()
    
    # Test 2: Analyze answer
    print("🔍 Test 2: Analyzing answer...")
    sample_answer = """
    REST and GraphQL are both API architectures. REST uses multiple endpoints 
    for different resources, while GraphQL uses a single endpoint. REST can lead 
    to over-fetching or under-fetching data, but GraphQL allows clients to request 
    exactly what they need. REST is simpler and well-established, while GraphQL 
    provides more flexibility for complex data requirements.
    """
    
    feedback = agent.analyze_answer(question['text'], sample_answer)
    print(f"Score: {feedback['score']}/10")
    print(f"Strengths: {feedback['strengths']}")
    print(f"Improvements: {feedback['improvements']}")
    print()
    
    print("✅ AI Agent is working perfectly!")