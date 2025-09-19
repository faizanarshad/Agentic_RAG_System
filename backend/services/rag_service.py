"""Main RAG service that orchestrates the complete RAG pipeline."""

from typing import List, Dict, Any
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

from .data_injestion_service import DataIngestionService
from .embeddings_service import EmbeddingsService
from .vectordb_service import VectorDBService
from .llm_service import LLMService
from utils.logger import logger


class RAGState(TypedDict):
    """State for the RAG graph."""
    messages: List[BaseMessage]
    query: str
    context_documents: List[Dict[str, Any]]
    answer: str


class RAGService:
    """Main service that orchestrates the RAG pipeline using LangGraph."""
    
    def __init__(self):
        """Initialize the RAG service with all required components."""
        self.data_ingestion = DataIngestionService()
        self.embeddings = EmbeddingsService()
        self.vectordb = VectorDBService()
        self.llm = LLMService()
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow for RAG."""
        
        def retrieve_documents(state: RAGState) -> RAGState:
            """Retrieve relevant documents from vector database."""
            try:
                logger.info("Retrieving relevant documents")
                query = state["query"]
                
                # Generate query embedding
                query_embedding = self.embeddings.generate_embedding(query)
                
                # Search for similar documents
                context_documents = self.vectordb.search_similar(query_embedding)
                
                state["context_documents"] = context_documents
                logger.info(f"Retrieved {len(context_documents)} relevant documents")
                
                return state
            except Exception as e:
                logger.error(f"Error retrieving documents: {str(e)}")
                state["context_documents"] = []
                return state
        
        def generate_answer(state: RAGState) -> RAGState:
            """Generate answer using LLM with retrieved context."""
            try:
                logger.info("Generating answer")
                query = state["query"]
                context_documents = state["context_documents"]
                
                if not context_documents:
                    answer = "I don't have enough information to answer this question."
                else:
                    answer = self.llm.generate_response(query, context_documents)
                
                state["answer"] = answer
                logger.info("Successfully generated answer")
                
                return state
            except Exception as e:
                logger.error(f"Error generating answer: {str(e)}")
                state["answer"] = "I encountered an error while generating the answer."
                return state
        
        # Build the graph
        workflow = StateGraph(RAGState)
        
        # Add nodes
        workflow.add_node("retrieve", retrieve_documents)
        workflow.add_node("generate", generate_answer)
        
        # Add edges
        workflow.add_edge("retrieve", "generate")
        workflow.add_edge("generate", END)
        
        # Set entry point
        workflow.set_entry_point("retrieve")
        
        return workflow.compile()
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """
        Process a user query through the complete RAG pipeline.
        
        Args:
            query: User query string
            
        Returns:
            Dictionary containing the answer and metadata
        """
        try:
            logger.info(f"Processing query: {query[:100]}...")
            
            # Create initial state
            initial_state = {
                "messages": [HumanMessage(content=query)],
                "query": query,
                "context_documents": [],
                "answer": ""
            }
            
            # Run the graph
            result = self.graph.invoke(initial_state)
            
            # Prepare response
            response = {
                "answer": result["answer"],
                "query": query,
                "context_count": len(result["context_documents"]),
                "context_documents": result["context_documents"]
            }
            
            logger.info("Successfully processed query")
            return response
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            return {
                "answer": "I encountered an error while processing your query.",
                "query": query,
                "context_count": 0,
                "context_documents": [],
                "error": str(e)
            }
    
    def add_document(self, pdf_file_path: str) -> Dict[str, Any]:
        """
        Add a new document to the RAG system.
        
        Args:
            pdf_file_path: Path to the PDF file
            
        Returns:
            Dictionary containing file_id and processing results
        """
        try:
            logger.info(f"Adding document: {pdf_file_path}")
            
            # Process PDF file
            processing_result = self.data_ingestion.process_pdf_file(pdf_file_path)
            file_id = processing_result["file_id"]
            documents = processing_result["documents"]
            
            # Generate embeddings
            processed_docs = self.embeddings.process_documents(documents)
            
            # Store in vector database
            self.vectordb.upsert_documents(processed_docs)
            
            logger.info(f"Successfully added document with file_id: {file_id}")
            
            return {
                "file_id": file_id,
                "message": "Document successfully added to the system",
                "total_chunks": len(processed_docs),
                "text_length": processing_result["text_length"]
            }
            
        except Exception as e:
            logger.error(f"Error adding document: {str(e)}")
            raise Exception(f"Failed to add document: {str(e)}")
    
    def delete_document(self, file_id: str) -> Dict[str, Any]:
        """
        Delete a document from the RAG system.
        
        Args:
            file_id: File ID to delete
            
        Returns:
            Dictionary containing deletion results
        """
        try:
            logger.info(f"Deleting document with file_id: {file_id}")
            
            # Delete from vector database
            self.vectordb.delete_by_file_id(file_id)
            
            logger.info(f"Successfully deleted document with file_id: {file_id}")
            
            return {
                "file_id": file_id,
                "message": "Document successfully deleted from the system"
            }
            
        except Exception as e:
            logger.error(f"Error deleting document: {str(e)}")
            raise Exception(f"Failed to delete document: {str(e)}")
    
    def update_document(self, file_id: str, pdf_file_path: str) -> Dict[str, Any]:
        """
        Update an existing document in the RAG system.
        
        Args:
            file_id: File ID to update
            pdf_file_path: Path to the new PDF file
            
        Returns:
            Dictionary containing update results
        """
        try:
            logger.info(f"Updating document {file_id} with file: {pdf_file_path}")
            
            # First delete the existing document
            self.delete_document(file_id)
            
            # Process the new PDF file
            processing_result = self.data_ingestion.process_pdf_file(pdf_file_path)
            documents = processing_result["documents"]
            
            # Update metadata to use the same file_id
            for doc in documents:
                doc.metadata["file_id"] = file_id
            
            # Generate embeddings
            processed_docs = self.embeddings.process_documents(documents)
            
            # Update IDs to use the same file_id
            for i, doc in enumerate(processed_docs):
                doc["id"] = f"{file_id}_{i}"
                doc["metadata"]["file_id"] = file_id
            
            # Store in vector database
            self.vectordb.upsert_documents(processed_docs)
            
            logger.info(f"Successfully updated document with file_id: {file_id}")
            
            return {
                "file_id": file_id,
                "message": "Document successfully updated in the system",
                "total_chunks": len(processed_docs),
                "text_length": processing_result["text_length"]
            }
            
        except Exception as e:
            logger.error(f"Error updating document: {str(e)}")
            raise Exception(f"Failed to update document: {str(e)}")
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on all RAG components.
        
        Returns:
            Dictionary containing health status of all components
        """
        try:
            health_status = {
                "vectordb": self.vectordb.health_check(),
                "llm": self.llm.health_check(),
                "overall": True
            }
            
            # Check if any component is unhealthy
            if not all(health_status.values()):
                health_status["overall"] = False
            
            logger.info(f"Health check completed: {health_status}")
            return health_status
            
        except Exception as e:
            logger.error(f"Error during health check: {str(e)}")
            return {
                "vectordb": False,
                "llm": False,
                "overall": False,
                "error": str(e)
            }
