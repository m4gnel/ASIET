"""
Provides the embedding model used for the RAG pipeline.
"""
import os
import logging
import warnings
import sys

logger = logging.getLogger(__name__)

# ════════════════════════════════════════════════════════════════════════════════
# SUPPRESS ALL NON-CRITICAL WARNINGS IMMEDIATELY (before any imports)
# ════════════════════════════════════════════════════════════════════════════════
warnings.filterwarnings("ignore", message=".*Hugging Face.*SSL.*")
warnings.filterwarnings("ignore", message=".*unauthenticated requests.*")
warnings.filterwarnings("ignore", message=".*HF_TOKEN.*")
warnings.filterwarnings("ignore", message=".*position_ids.*")
warnings.filterwarnings("ignore", message=".*UNEXPECTED.*")
warnings.filterwarnings("ignore", message=".*Some weights of the model checkpoint.*")
warnings.filterwarnings("ignore", message=".*deprecated.*", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning, message=".*Core Pydantic V1.*")
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# Gracefully handle missing langchain libraries
LANGCHAIN_AVAILABLE = False
try:
    from langchain_community.embeddings import HuggingFaceEmbeddings
    LANGCHAIN_AVAILABLE = True
except ImportError as e:
    logger.warning(f"LangChain not available: {e}. RAG embeddings will be disabled.")
    HuggingFaceEmbeddings = None

# Additional warning suppression for sentence-transformers and torch
if LANGCHAIN_AVAILABLE:
    try:
        import sentence_transformers
        warnings.filterwarnings("ignore", message=".*position_ids.*")
        warnings.filterwarnings("ignore", message=".*UNEXPECTED.*")
    except:
        pass
    
    try:
        import torch
        warnings.filterwarnings("ignore", message=".*torch.*")
    except:
        pass
    
    try:
        import langchain.core._api.deprecation
        langchain.core._api.deprecation._warn_deprecated = lambda **kwargs: None
    except:
        pass

# Default model: lightweight, fast, and good for semantic search
DEFAULT_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

class EmbeddingService:
    """Singleton service for managing embeddings."""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EmbeddingService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, model_name: str = DEFAULT_MODEL_NAME):
        if self._initialized:
            return
        self.model_name = model_name
        self.embeddings = None
        self.available = LANGCHAIN_AVAILABLE
        if self.available:
            self._initialize()
        else:
            logger.info("LangChain not available - RAG embeddings disabled")
        self._initialized = True

    def _initialize(self):
        """Initialize embeddings if langchain is available."""
        if not LANGCHAIN_AVAILABLE:
            logger.warning("Cannot initialize embeddings - LangChain not installed")
            return
            
        try:
            logger.info(f"Loading embedding model: {self.model_name}")
            # Suppress ALL warnings during initialization
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                self.embeddings = HuggingFaceEmbeddings(model_name=self.model_name)
            logger.info("[OK] Embedding model loaded successfully (cached for reuse)")
        except Exception as e:
            logger.warning(f"Failed to load embedding model: {e}. RAG will be unavailable.")
            self.embeddings = None
            self.available = False

    def get_embeddings(self):
        """Returns the cached HuggingFaceEmbeddings instance, or None if unavailable."""
        if not self.available or not self.embeddings:
            return None
        return self.embeddings

# Singleton instance for easy import - gracefully handles missing langchain
embedding_service = EmbeddingService()
