"""Embeddings service for generating vector embeddings using OpenAI."""

from typing import List, Dict, Any
from openai import OpenAI
from langchain.schema import Document

from core.config import settings
from utils.logger import logger


class EmbeddingsService:
    """Service for generating embeddings using OpenAI's embedding models."""
    
    def __init__(self):
        """Initialize the embeddings service."""
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_EMBEDDING_MODEL
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to generate embedding for
            
        Returns:
            List of float values representing the embedding
            
        Raises:
            Exception: If embedding generation fails
        """
        try:
            logger.debug(f"Generating embedding for text of length: {len(text)}")
            
            # Check text length (rough estimate: 1 token ≈ 4 characters)
            estimated_tokens = len(text) / 4
            if estimated_tokens > 8000:
                logger.warning(f"Text may exceed token limit: ~{estimated_tokens:.0f} tokens")
                # Truncate if too long
                max_chars = 8000 * 4
                text = text[:max_chars] + "\n\n[Text truncated to fit token limit]"
            
            response = self.client.embeddings.create(
                model=self.model,
                input=text
            )
            
            embedding = response.data[0].embedding
            logger.debug(f"Successfully generated embedding of dimension: {len(embedding)}")
            return embedding
            
        except Exception as e:
            error_msg = str(e)
            
            # Handle specific OpenAI errors
            if "maximum context length" in error_msg.lower() or "token" in error_msg.lower():
                logger.error(f"Token limit exceeded for text of length {len(text)}")
                # Return a placeholder embedding of zeros to avoid crashing
                logger.warning("Skipping this document due to token limit")
                raise Exception("Text exceeds token limit - please split into smaller chunks")
            else:
                logger.error(f"Error generating embedding: {error_msg}")
                raise Exception(f"Failed to generate embedding: {error_msg}")
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batch.
        
        Args:
            texts: List of texts to generate embeddings for
            
        Returns:
            List of embeddings (list of float lists)
            
        Raises:
            Exception: If batch embedding generation fails
        """
        try:
            logger.info(f"Generating embeddings for {len(texts)} texts")
            
            response = self.client.embeddings.create(
                model=self.model,
                input=texts
            )
            
            embeddings = [data.embedding for data in response.data]
            logger.info(f"Successfully generated {len(embeddings)} embeddings")
            return embeddings
            
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {str(e)}")
            raise Exception(f"Failed to generate batch embeddings: {str(e)}")
    
    def process_documents(self, documents: List[Document]) -> List[Dict[str, Any]]:
        """
        Process documents to generate embeddings and prepare for vector storage.
        
        Args:
            documents: List of Document objects to process
            
        Returns:
            List of dictionaries containing document data and embeddings
        """
        try:
            logger.info(f"Processing {len(documents)} documents for embedding generation")
            
            # Extract texts from documents
            texts = [doc.page_content for doc in documents]
            
            # Generate embeddings
            embeddings = self.generate_embeddings_batch(texts)
            
            # Prepare data for vector storage
            processed_docs = []
            for i, (doc, embedding) in enumerate(zip(documents, embeddings)):
                processed_doc = {
                    "id": f"{doc.metadata.get('file_id', 'unknown')}_{i}",
                    "text": doc.page_content,
                    "embedding": embedding,
                    "metadata": doc.metadata
                }
                processed_docs.append(processed_doc)
            
            logger.info(f"Successfully processed {len(processed_docs)} documents with embeddings")
            return processed_docs
            
        except Exception as e:
            logger.error(f"Error processing documents: {str(e)}")
            raise Exception(f"Failed to process documents: {str(e)}")
    
    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of embeddings produced by the current model.
        
        Returns:
            Embedding dimension
        """
        try:
            # Generate a test embedding to determine dimension
            test_embedding = self.generate_embedding("test")
            return len(test_embedding)
        except Exception as e:
            logger.error(f"Error determining embedding dimension: {str(e)}")
            # Return default dimension for text-embedding-ada-002
            return 1536
