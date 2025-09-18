"""API routes for chat functionality."""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any

from services.rag_service import RAGService
from utils.logger import logger

router = APIRouter(prefix="/chat", tags=["chat"])

# Initialize RAG service lazily
rag_service = None

def get_rag_service():
    global rag_service
    if rag_service is None:
        rag_service = RAGService()
    return rag_service


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    query: str


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    answer: str
    query: str
    context_count: int
    context_documents: list = []


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Process a chat query and return a response.
    
    Args:
        request: Chat request containing the query
        
    Returns:
        Chat response with answer and metadata
        
    Raises:
        HTTPException: If query processing fails
    """
    try:
        logger.info(f"Received chat request: {request.query[:100]}...")
        
        # Validate query
        if not request.query.strip():
            raise HTTPException(
                status_code=400,
                detail="Query cannot be empty"
            )
        
        # Process query through RAG pipeline
        rag_service = get_rag_service()
        result = rag_service.process_query(request.query)
        
        # Prepare response
        response = ChatResponse(
            answer=result["answer"],
            query=result["query"],
            context_count=result["context_count"],
            context_documents=result.get("context_documents", [])
        )
        
        logger.info("Successfully processed chat request")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Check the health status of the chat service.
    
    Returns:
        Health status of all RAG components
    """
    try:
        rag_service = get_rag_service()
        health_status = rag_service.health_check()
        return health_status
    except Exception as e:
        logger.error(f"Error during health check: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Health check failed: {str(e)}"
        )
