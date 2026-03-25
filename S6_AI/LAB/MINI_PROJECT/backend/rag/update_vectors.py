"""
Utility script to seed the FAISS vector database with all existing completed interview answers and feedback from the SQLite database.
Run this script manually whenever you want to hard-sync the FAISS index from the SQL DB.
"""
import os
import sys

# Ensure backend root is in the python path to allow imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db, Answer, Feedback, Question
from rag.vector_store import vector_store_manager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_all_vectors():
    """Fetches all past answers and feedback and ingests them into FAISS."""
    with app.app_context():
        # Get all completed answers that have a score (implies feedback was generated)
        answers = Answer.query.filter(Answer.score.isnot(None)).all()
        
        if not answers:
            logger.info("No scored answers found in the SQLite database to seed FAISS.")
            return

        logger.info(f"Found {len(answers)} past answers. Processing embeddings...")

        success_count = 0
        
        # We process them one by one for simplicity (FAISS supports batching, but we reuse the manager methods)
        for ans in answers:
            try:
                # Need the original question text
                question = db.session.get(Question, ans.question_id) if ans.question_id else None
                q_text = question.text if question else "Unknown question"
                
                # Need the AI feedback
                feedback = Feedback.query.filter_by(answer_id=ans.id).first()
                f_text = feedback.detailed_feedback if feedback else "No detailed feedback available."
                
                # Add to FAISS via manager
                metadata = {
                    'answer_id': ans.id,
                    'question_id': ans.question_id,
                    'interview_id': ans.interview_id
                }
                
                vector_store_manager.add_interview_record(
                    question=q_text,
                    user_answer=ans.text,
                    ai_feedback=f_text,
                    rating=ans.score,
                    metadata=metadata
                )
                
                success_count += 1
            except Exception as e:
                logger.error(f"Failed to process answer ID {ans.id}: {e}")

        logger.info(f"Successfully seeded {success_count}/{len(answers)} records into FAISS vector database.")

if __name__ == "__main__":
    update_all_vectors()
