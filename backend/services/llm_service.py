"""LLM service for generating responses using OpenAI GPT models."""

from typing import List, Dict, Any
from openai import OpenAI
from langchain_core.documents import Document

from core.config import settings
from services.prompt_guard import UNTRUSTED_NOTICE, fence
from utils.logger import logger
from .usage_tracker import record_usage


class LLMService:
    """Service for generating responses using OpenAI's language models."""
    
    def __init__(self):
        """Initialize the LLM service."""
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY, base_url=settings.OPENAI_BASE_URL or None)
        self.model = settings.OPENAI_MODEL
    
    def generate_response(
        self, 
        query: str, 
        context_documents: List[Dict[str, Any]]
    ) -> str:
        """
        Generate a response based on the query and context documents.
        
        Args:
            query: User query
            context_documents: List of relevant documents with text and metadata
            
        Returns:
            Generated response string
            
        Raises:
            Exception: If response generation fails
        """
        try:
            logger.info(f"Generating response for query: {query[:100]}...")
            
            # Prepare context from documents
            context = self._prepare_context(context_documents)
            
            # Create the prompt
            prompt = self._create_prompt(query, context)
            
            # Generate response
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a helpful assistant that answers questions based on the provided context. "
                            "Use only the information from the context to answer questions. "
                            "If the context doesn't contain enough information to answer the question, "
                            "say 'I don't have enough information in the provided context to answer this question.' "
                            "Be concise and accurate in your responses."
                        ) + UNTRUSTED_NOTICE
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=1000,
                temperature=0.1
            )
            
            record_usage(self.model, response.usage, "medical-chat")
            answer = response.choices[0].message.content
            logger.info("Successfully generated response")
            return answer
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            raise Exception(f"Failed to generate response: {str(e)}")
    
    def _prepare_context(self, documents: List[Dict[str, Any]]) -> str:
        """
        Prepare context string from retrieved documents.
        
        Args:
            documents: List of document dictionaries
            
        Returns:
            Formatted context string
        """
        context_parts = []
        
        for i, doc in enumerate(documents, 1):
            text = doc.get("text", "")
            file_id = doc.get("metadata", {}).get("file_id", "unknown")
            chunk_index = doc.get("metadata", {}).get("chunk_index", "unknown")
            
            context_part = f"Document {i} (File: {file_id}, Chunk: {chunk_index}):\n{text}\n"
            context_parts.append(context_part)
        
        return "\n".join(context_parts)
    
    def _create_prompt(self, query: str, context: str) -> str:
        """
        Create the prompt for the LLM.
        
        Args:
            query: User query
            context: Context from retrieved documents
            
        Returns:
            Formatted prompt string
        """
        prompt = f"""Context:
{fence(context, "CONTEXT")}

Question: {query}

Please answer the question based on the context provided above. If the context doesn't contain enough information to answer the question, please say so."""
        
        return prompt
    
    _health_cache = {"ok": None, "checked": 0.0}

    def health_check(self) -> bool:
        """
        Check the model is reachable without spending tokens (models.retrieve is free), cached for 60 s
        so an open status panel does not call the provider every 30 seconds.
        """
        import time

        cache = LLMService._health_cache
        if cache["ok"] is not None and time.monotonic() - cache["checked"] < 60:
            return cache["ok"]
        try:
            self.client.models.retrieve(self.model)
            ok = True
            logger.info("LLM service health check passed")
        except Exception as e:
            logger.error(f"LLM service health check failed: {str(e)}")
            ok = False
        cache.update(ok=ok, checked=time.monotonic())
        return ok
