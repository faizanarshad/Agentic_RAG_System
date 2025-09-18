"""API routes for file management operations."""

import os
import tempfile
from fastapi import APIRouter, HTTPException, UploadFile, File, Path
from pydantic import BaseModel
from typing import Dict, Any

from services.rag_service import RAGService
from services.data_injestion_service import DataIngestionService
from utils.logger import logger

router = APIRouter(prefix="/files", tags=["files"])

# Initialize services lazily
rag_service = None
data_ingestion = None

def get_rag_service():
    global rag_service
    if rag_service is None:
        rag_service = RAGService()
    return rag_service

def get_data_ingestion_service():
    global data_ingestion
    if data_ingestion is None:
        data_ingestion = DataIngestionService()
    return data_ingestion


class FileResponse(BaseModel):
    """Response model for file operations."""
    file_id: str
    message: str
    total_chunks: int = 0
    text_length: int = 0


class UpdateFileResponse(BaseModel):
    """Response model for file update operations."""
    file_id: str
    message: str
    total_chunks: int
    text_length: int


@router.post("/add_file", response_model=FileResponse)
async def add_file(file: UploadFile = File(...)) -> FileResponse:
    """
    Upload a PDF file, extract text, create embeddings, and store in Pinecone.
    
    Args:
        file: Uploaded PDF file
        
    Returns:
        File response with file_id and processing results
        
    Raises:
        HTTPException: If file processing fails
    """
    try:
        logger.info(f"Received file upload: {file.filename}")
        
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=400,
                detail="Only PDF files are supported"
            )
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # Validate PDF file
            data_ingestion = get_data_ingestion_service()
            if not data_ingestion.validate_pdf_file(temp_file_path):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid PDF file or file is corrupted"
                )
            
            # Process file through RAG service
            rag_service = get_rag_service()
            result = rag_service.add_document(temp_file_path)
            
            logger.info(f"Successfully processed file: {file.filename}")
            
            return FileResponse(
                file_id=result["file_id"],
                message=result["message"],
                total_chunks=result["total_chunks"],
                text_length=result["text_length"]
            )
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing file upload: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process file: {str(e)}"
        )


@router.delete("/delete_file/{file_id}")
async def delete_file(file_id: str = Path(..., description="File ID to delete")) -> Dict[str, Any]:
    """
    Delete all vectors related to a given file ID from Pinecone.
    
    Args:
        file_id: File ID to delete
        
    Returns:
        Success or error message
        
    Raises:
        HTTPException: If deletion fails
    """
    try:
        logger.info(f"Received delete request for file_id: {file_id}")
        
        # Validate file_id
        if not file_id.strip():
            raise HTTPException(
                status_code=400,
                detail="File ID cannot be empty"
            )
        
        # Delete file through RAG service
        rag_service = get_rag_service()
        result = rag_service.delete_document(file_id)
        
        logger.info(f"Successfully deleted file: {file_id}")
        
        return {
            "file_id": result["file_id"],
            "message": result["message"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting file {file_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete file: {str(e)}"
        )


@router.put("/update_file/{file_id}", response_model=UpdateFileResponse)
async def update_file(
    file_id: str = Path(..., description="File ID to update"),
    file: UploadFile = File(...)
) -> UpdateFileResponse:
    """
    Replace the existing file's vectors with embeddings from the new PDF.
    
    Args:
        file_id: File ID to update
        file: New PDF file
        
    Returns:
        Update response with processing results
        
    Raises:
        HTTPException: If update fails
    """
    try:
        logger.info(f"Received update request for file_id: {file_id} with file: {file.filename}")
        
        # Validate file_id
        if not file_id.strip():
            raise HTTPException(
                status_code=400,
                detail="File ID cannot be empty"
            )
        
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=400,
                detail="Only PDF files are supported"
            )
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # Validate PDF file
            data_ingestion = get_data_ingestion_service()
            if not data_ingestion.validate_pdf_file(temp_file_path):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid PDF file or file is corrupted"
                )
            
            # Update file through RAG service
            rag_service = get_rag_service()
            result = rag_service.update_document(file_id, temp_file_path)
            
            logger.info(f"Successfully updated file: {file_id}")
            
            return UpdateFileResponse(
                file_id=result["file_id"],
                message=result["message"],
                total_chunks=result["total_chunks"],
                text_length=result["text_length"]
            )
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating file {file_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update file: {str(e)}"
        )


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Check the health status of the file service.
    
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
