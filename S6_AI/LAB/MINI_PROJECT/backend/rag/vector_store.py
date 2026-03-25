"""
Manages the FAISS vector database for persistent storage and retrieval of interview sessions.
"""
import os
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# Gracefully handle missing langchain libraries
try:
    from langchain_community.vectorstores import FAISS
    from langchain_core.documents import Document
    from .embedding_service import embedding_service
    LANGCHAIN_AVAILABLE = True
except ImportError as e:
    logger.warning(f"LangChain not available: {e}. RAG features will be disabled.")
    LANGCHAIN_AVAILABLE = False
    FAISS = None
    Document = None
    embedding_service = None

# Define where the FAISS index will be saved locally
FAISS_INDEX_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'interview_vectors')

class VectorStoreManager:
    def __init__(self):
        self.index_path = FAISS_INDEX_PATH
        self.vector_store = None
        self.embeddings = None
        
        if LANGCHAIN_AVAILABLE:
            try:
                self.embeddings = embedding_service.get_embeddings()
                self._load_or_create_index()
                self.langchain_enabled = True
            except Exception as e:
                logger.error(f"Failed to initialize VectorStoreManager: {e}")
                # Cannot modify global LANGCHAIN_AVAILABLE here (would cause UnboundLocalError)
                # Instead, mark this instance as having failed langchain initialization
                self.langchain_enabled = False
        else:
            logger.info("RAG/FAISS disabled. Application will use Mistral-only mode.")
            self.langchain_enabled = False

    def _load_or_create_index(self):
        """Loads an existing FAISS index from disk, or prepares an empty state if none exists."""
        if not LANGCHAIN_AVAILABLE or self.embeddings is None:
            return
            
        if os.path.exists(os.path.join(self.index_path, "index.faiss")):
            try:
                logger.info(f"Loading existing FAISS index from {self.index_path}")
                self.vector_store = FAISS.load_local(
                    folder_path=self.index_path, 
                    embeddings=self.embeddings,
                    allow_dangerous_deserialization=True
                )
            except Exception as e:
                logger.warning(f"Error loading FAISS index: {e}. Starting fresh.")
                self.vector_store = None
        else:
            logger.info(f"No existing FAISS index found at {self.index_path}. Will create on first insertion.")
            self.vector_store = None

    def add_documents(self, documents: List[Dict[str, Any]]):
        """Adds documents to the FAISS index and saves to disk."""
        if not LANGCHAIN_AVAILABLE or not documents:
            return
            
        try:
            # Convert dict documents to langchain Documents
            lang_docs = []
            for doc in documents:
                if isinstance(doc, dict):
                    lang_docs.append(Document(
                        page_content=doc.get('content', ''),
                        metadata=doc.get('metadata', {})
                    ))
                else:
                    lang_docs.append(doc)
            
            if self.vector_store is None:
                logger.info("Initializing new FAISS vector store.")
                self.vector_store = FAISS.from_documents(lang_docs, self.embeddings)
            else:
                logger.info(f"Adding {len(lang_docs)} new documents to existing FAISS vector store.")
                self.vector_store.add_documents(lang_docs)
            
            # Save the updated index to disk immediately
            os.makedirs(self.index_path, exist_ok=True)
            self.vector_store.save_local(self.index_path)
            logger.info(f"Successfully saved FAISS index to {self.index_path}")
        except Exception as e:
            logger.warning(f"Failed to add documents to FAISS index: {e}")

    def add_interview_record(self, question: str, user_answer: str, ai_feedback: str, rating: float, metadata: Dict[str, Any] = None):
        """Helper method to format an interview record into a Document and add it to FAISS."""
        if not LANGCHAIN_AVAILABLE:
            return
            
        try:
            page_content = f"Question: {question}\nAnswer: {user_answer}\nFeedback: {ai_feedback}\nScore: {rating}/10"
            
            doc_metadata = {
                "type": "interview_qa",
                "score": rating
            }
            if metadata:
                doc_metadata.update(metadata)
                
            doc = Document(page_content=page_content, metadata=doc_metadata)
            self.add_documents([doc])
        except Exception as e:
            logger.warning(f"Failed to record interview in FAISS: {e}")

    def search_similar(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Performs a similarity search against the FAISS index."""
        if not LANGCHAIN_AVAILABLE or self.vector_store is None:
            logger.debug("FAISS search unavailable - returning empty results")
            return []
            
        try:
            results = self.vector_store.similarity_search(query, k=top_k)
            # Convert langchain Documents back to dicts for compatibility
            return [
                {
                    'content': doc.page_content,
                    'metadata': doc.metadata
                } for doc in results
            ]
        except Exception as e:
            logger.warning(f"Error executing similarity search: {e}")
            return []

# Singleton instance with graceful fallback
vector_store_manager = VectorStoreManager()
