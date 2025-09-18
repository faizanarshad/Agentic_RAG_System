"""Vector database service for Pinecone operations."""

from typing import List, Dict, Any, Optional
from pinecone import Pinecone, ServerlessSpec

from core.config import settings
from utils.logger import logger


class VectorDBService:
    """Service for managing vector database operations with Pinecone."""
    
    def __init__(self):
        """Initialize the vector database service."""
        self.pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        self.index_name = settings.PINECONE_INDEX_NAME
        self.index = None
        self._initialize_index()
    
    def _initialize_index(self) -> None:
        """Initialize or connect to the Pinecone index."""
        try:
            # Check if index exists
            if self.index_name not in self.pc.list_indexes().names():
                logger.info(f"Creating new Pinecone index: {self.index_name}")
                
                # Get embedding dimension
                from .embeddings_service import EmbeddingsService
                embeddings_service = EmbeddingsService()
                dimension = embeddings_service.get_embedding_dimension()
                
                # Create index
                self.pc.create_index(
                    name=self.index_name,
                    dimension=dimension,
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws",
                        region="us-east-1"
                    )
                )
                
                logger.info(f"Successfully created index {self.index_name} with dimension {dimension}")
            else:
                logger.info(f"Using existing Pinecone index: {self.index_name}")
            
            # Connect to index
            self.index = self.pc.Index(self.index_name)
            logger.info("Successfully connected to Pinecone index")
            
        except Exception as e:
            logger.error(f"Error initializing Pinecone index: {str(e)}")
            raise Exception(f"Failed to initialize vector database: {str(e)}")
    
    def upsert_documents(self, documents: List[Dict[str, Any]]) -> None:
        """
        Insert or update documents in the vector database.
        
        Args:
            documents: List of document dictionaries with id, text, embedding, and metadata
            
        Raises:
            Exception: If upsert operation fails
        """
        try:
            logger.info(f"Upserting {len(documents)} documents to vector database")
            
            # Prepare vectors for upsert
            vectors = []
            for doc in documents:
                vector = {
                    "id": doc["id"],
                    "values": doc["embedding"],
                    "metadata": {
                        "text": doc["text"],
                        "file_id": doc["metadata"].get("file_id"),
                        "chunk_index": doc["metadata"].get("chunk_index"),
                        "total_chunks": doc["metadata"].get("total_chunks"),
                        "source": doc["metadata"].get("source", "pdf")
                    }
                }
                vectors.append(vector)
            
            # Upsert to Pinecone
            self.index.upsert(vectors=vectors)
            logger.info(f"Successfully upserted {len(vectors)} vectors")
            
        except Exception as e:
            logger.error(f"Error upserting documents: {str(e)}")
            raise Exception(f"Failed to upsert documents: {str(e)}")
    
    def search_similar(self, query_embedding: List[float], top_k: int = None) -> List[Dict[str, Any]]:
        """
        Search for similar documents using vector similarity.
        
        Args:
            query_embedding: Query vector embedding
            top_k: Number of top results to return
            
        Returns:
            List of similar documents with metadata and scores
        """
        try:
            if top_k is None:
                top_k = settings.MAX_RETRIEVAL_RESULTS
            
            logger.info(f"Searching for similar documents with top_k={top_k}")
            
            # Search in Pinecone
            results = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True
            )
            
            # Format results
            similar_docs = []
            for match in results.matches:
                doc = {
                    "id": match.id,
                    "text": match.metadata.get("text", ""),
                    "score": match.score,
                    "metadata": {
                        "file_id": match.metadata.get("file_id"),
                        "chunk_index": match.metadata.get("chunk_index"),
                        "total_chunks": match.metadata.get("total_chunks"),
                        "source": match.metadata.get("source", "pdf")
                    }
                }
                similar_docs.append(doc)
            
            logger.info(f"Found {len(similar_docs)} similar documents")
            return similar_docs
            
        except Exception as e:
            logger.error(f"Error searching similar documents: {str(e)}")
            raise Exception(f"Failed to search similar documents: {str(e)}")
    
    def delete_by_file_id(self, file_id: str) -> None:
        """
        Delete all vectors associated with a specific file ID.
        
        Args:
            file_id: File ID to delete vectors for
            
        Raises:
            Exception: If delete operation fails
        """
        try:
            logger.info(f"Deleting vectors for file_id: {file_id}")
            
            # Query to find all vectors with the file_id
            results = self.index.query(
                vector=[0.0] * self.index.describe_index_stats().dimension,  # Dummy vector
                filter={"file_id": {"$eq": file_id}},
                top_k=10000,  # Large number to get all matches
                include_metadata=True
            )
            
            if results.matches:
                # Extract IDs to delete
                ids_to_delete = [match.id for match in results.matches]
                logger.info(f"Found {len(ids_to_delete)} vectors to delete for file_id: {file_id}")
                
                # Delete vectors
                self.index.delete(ids=ids_to_delete)
                logger.info(f"Successfully deleted {len(ids_to_delete)} vectors")
            else:
                logger.info(f"No vectors found for file_id: {file_id}")
            
        except Exception as e:
            logger.error(f"Error deleting vectors for file_id {file_id}: {str(e)}")
            raise Exception(f"Failed to delete vectors: {str(e)}")
    
    def get_index_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector database index.
        
        Returns:
            Dictionary containing index statistics
        """
        try:
            stats = self.index.describe_index_stats()
            return {
                "total_vector_count": stats.total_vector_count,
                "dimension": stats.dimension,
                "index_fullness": stats.index_fullness
            }
        except Exception as e:
            logger.error(f"Error getting index stats: {str(e)}")
            raise Exception(f"Failed to get index statistics: {str(e)}")
    
    def health_check(self) -> bool:
        """
        Check if the vector database is healthy and accessible.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            stats = self.get_index_stats()
            logger.info("Vector database health check passed")
            return True
        except Exception as e:
            logger.error(f"Vector database health check failed: {str(e)}")
            return False
