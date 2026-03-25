"""
Builds context-aware prompts by combining user questions with relevant past feedback retrieved from the FAISS vector store.
"""
from typing import List, Dict, Any, Union

# Gracefully handle missing langchain
try:
    from langchain_core.documents import Document
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    Document = None

class PromptBuilder:
    def __init__(self):
        self.system_prompt = (
            "You are an expert AI interview coach that helps users improve their interview answers "
            "using knowledge from previous interview sessions."
        )
        self.instruction = "Use the following context from past interview feedback to guide your response."

    def build_rag_prompt(self, current_question: str, current_answer: str, retrieved_docs: List[Union[Dict[str, Any], Any]], company_context: str = "") -> str:
        """Constructs a concise prompt leveraging FAISS context for faster inference."""
        
        context_str = ""
        if retrieved_docs:
            context_str = "PAST SESSIONS:\n"
            for i, doc in enumerate(retrieved_docs):
                if isinstance(doc, dict):
                    content = doc.get('content', '')
                    score = doc.get('metadata', {}).get('score', 'N/A') if isinstance(doc.get('metadata'), dict) else 'N/A'
                else:
                    content = doc.page_content if hasattr(doc, 'page_content') else str(doc)
                    metadata = doc.metadata if hasattr(doc, 'metadata') else {}
                    score = metadata.get('score', 'N/A') if isinstance(metadata, dict) else 'N/A'
                # Truncate long context to reduce prompt size
                if len(content) > 300:
                    content = content[:300] + "..."
                context_str += f"[{i+1}|Score:{score}] {content}\n"

        company_line = f"Company: {company_context}\n" if company_context else ""
        prompt = f"""Expert interview coach. Score this answer using past feedback context.
{context_str}
{company_line}Q: {current_question}
A: {current_answer}

Reply EXACTLY in this format (scores 0-10):
TECHNICAL_ACCURACY: [score]
DEPTH: [score]
CLARITY: [score]
RELEVANCE: [score]
COMMUNICATION: [score]
CONFIDENCE: [score]
OVERALL_SCORE: [score]
STRENGTHS:
- [point]
- [point]
- [point]
IMPROVEMENTS:
- [point]
- [point]
- [point]
DETAILED_FEEDBACK: [2 sentences. Reference past attempts if context available.]
IMPROVEMENT_PLAN:
- [action]
- [action]
- [action]"""

        return prompt

# Singleton instance
prompt_builder = PromptBuilder()
