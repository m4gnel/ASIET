"""
Orchestrates the RAG flow: Retrieval from VectorStore -> Prompt Building -> Generation via OpenAI(Mistral)
"""
import os
import logging
from openai import OpenAI
from .vector_store import vector_store_manager, LANGCHAIN_AVAILABLE
from .prompt_builder import prompt_builder

logger = logging.getLogger(__name__)

class RAGEngine:
    def __init__(self):
        self.base_url = os.environ.get('MISTRAL_BASE_URL', 'http://127.0.0.1:1234/v1')
        self.model_name = os.environ.get('MISTRAL_MODEL_NAME', 'mistral-7b-instruct-v0.2')
        api_key = os.environ.get('MISTRAL_API_KEY', 'lm-studio')
        
        # RAG is only available if both Mistral AND langchain are available
        self.is_available = False
        self.vector_store_manager = vector_store_manager
        self.prompt_builder = prompt_builder
        self.langchain_available = LANGCHAIN_AVAILABLE

        # Check if langchain is available
        if not self.langchain_available:
            logger.warning("LangChain not available. RAG features will be disabled, using Mistral-only mode.")
            return

        try:
            # Create client with proper timeout configuration for LLM operations
            self.client = OpenAI(
                base_url=self.base_url, 
                api_key=api_key,
                timeout=120.0  # 2-minute timeout for client initialization
            )
            # Simple check to ensure model is online (30 second timeout)
            self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=5,
                timeout=30.0
            )
            self.is_available = True
            logger.info("RAG Engine (Mistral API + LangChain) is ONLINE.")
        except Exception as e:
            self.is_available = False
            logger.warning(f"RAG Engine unavailable: {e}. Using Mistral-only fallback.")

    def generate_feedback_rag(self, current_question: str, current_answer: str, company_context: str = "") -> str:
        """
        Executes the full RAG pipeline to generate feedback.
        1. Query FAISS
        2. Build Prompt
        3. Call Mistral API
        """
        if not self.is_available or not self.langchain_available:
            logger.warning("RAG unavailable. Fallback to direct Mistral processing.")
            raise ConnectionError("RAG Engine not available")

        try:
            # 1. Retrieve context (top_k=3 balances relevance vs latency)
            query_text = f"Question: {current_question}\nAnswer: {current_answer}"
            retrieved_docs = self.vector_store_manager.search_similar(query_text, top_k=3)

            logger.info(f"RAG retrieved {len(retrieved_docs)} context documents from previous sessions.")

            # 2. Build prompt
            prompt = self.prompt_builder.build_rag_prompt(
                current_question=current_question,
                current_answer=current_answer,
                retrieved_docs=retrieved_docs,
                company_context=company_context
            )

            # 3. Call Mistral — optimized: fewer tokens + stop sequences for speed
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=650,
                temperature=0.2,
                top_p=0.85,
                stop=["\n\n\n"],
                timeout=90.0
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.warning(f"RAG generation error: {e}. Falling back to Mistral-only mode.")
            raise e

    def record_session(self, question: str, user_answer: str, ai_feedback: str, rating: float, question_id: int):
        """Asynchronously (or fire&forget) add completed session to FAISS for future learning."""
        if not self.langchain_available or not self.is_available:
            logger.debug("Skipping FAISS recording - RAG not available")
            return
            
        try:
            metadata = {'question_id': question_id}
            self.vector_store_manager.add_interview_record(
                question=question,
                user_answer=user_answer,
                ai_feedback=ai_feedback,
                rating=rating,
                metadata=metadata
            )
        except Exception as e:
            logger.warning(f"Failed to record session to FAISS: {e}")

# Singleton instance with graceful degradation
rag_engine = RAGEngine()
