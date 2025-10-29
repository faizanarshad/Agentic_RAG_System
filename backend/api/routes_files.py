"""API routes for file management operations."""

import os
import tempfile
from fastapi import APIRouter, HTTPException, UploadFile, File, Path
from pydantic import BaseModel
from typing import Dict, Any

from services.rag_service import RAGService
from services.data_injestion_service import DataIngestionService
from services.csv_processor import CSVProcessor
from utils.logger import logger

router = APIRouter(prefix="/files", tags=["files"])

# Initialize services lazily
rag_service = None
data_ingestion = None
csv_processor = None

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

def get_csv_processor():
    global csv_processor
    if csv_processor is None:
        csv_processor = CSVProcessor()
    return csv_processor


async def process_csv_file(file_path: str, filename: str) -> Dict[str, Any]:
    """Process CSV file and add to RAG system"""
    import uuid
    
    # Generate file ID
    file_id = str(uuid.uuid4())
    
    # Process CSV to documents
    csv_processor = get_csv_processor()
    documents = csv_processor.process_csv_to_documents(file_path, file_id)
    
    # Add documents to RAG system
    rag_service = get_rag_service()
    
    # Process each document through embeddings and vector store
    total_chunks = 0
    total_text_length = 0
    
    # Import Document class
    from langchain.schema import Document
    from services.embeddings_service import EmbeddingsService
    from services.vectordb_service import VectorDBService
    
    # Initialize services
    embeddings_service = EmbeddingsService()
    vectordb_service = VectorDBService()
    
    # Convert documents to LangChain Document format
    langchain_docs = []
    for doc in documents:
        langchain_doc = Document(
            page_content=doc['text'],
            metadata=doc['metadata']
        )
        langchain_docs.append(langchain_doc)
        total_chunks += 1
        total_text_length += len(doc['text'])
    
    # Process documents ONE AT A TIME to handle variable document sizes
    # Some documents may be very large and exceed token limits even in small batches
    if langchain_docs:
        total_docs = len(langchain_docs)
        logger.info(f"Processing {total_docs} documents individually to handle variable sizes")
        
        for idx, doc in enumerate(langchain_docs, 1):
            if idx % 10 == 0:  # Log every 10 documents
                logger.info(f"Processing document {idx} of {total_docs}")
            
            try:
                # Generate embedding for single document
                embedding_docs = embeddings_service.process_documents([doc])
                
                # Store in vector database
                vectordb_service.upsert_documents(embedding_docs)
            except Exception as e:
                # Log error but continue with other documents
                logger.error(f"Error processing document {idx}: {str(e)}")
                continue
        
        logger.info(f"Completed processing all {total_docs} documents")
    
    logger.info(f"Successfully processed CSV file {filename}: {total_chunks} documents, {total_text_length} characters")
    
    return {
        "file_id": file_id,
        "message": f"Successfully processed CSV file with {total_chunks} documents",
        "total_chunks": total_chunks,
        "text_length": total_text_length
    }


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
        allowed_extensions = ['.pdf', '.csv']
        file_ext = None
        for ext in allowed_extensions:
            if file.filename.lower().endswith(ext):
                file_ext = ext
                break
        
        if file_ext is None:
            raise HTTPException(
                status_code=400,
                detail="Only PDF and CSV files are supported"
            )
        
        # Save uploaded file temporarily
        suffix = file_ext
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            if file_ext == '.pdf':
                # Validate PDF file
                data_ingestion = get_data_ingestion_service()
                if not data_ingestion.validate_pdf_file(temp_file_path):
                    raise HTTPException(
                        status_code=400,
                        detail="Invalid PDF file or file is corrupted"
                    )
                
                # Process PDF file through RAG service
                rag_service = get_rag_service()
                result = rag_service.add_document(temp_file_path)
                
            elif file_ext == '.csv':
                # Validate CSV file
                csv_processor = get_csv_processor()
                if not csv_processor.validate_csv_file(temp_file_path):
                    raise HTTPException(
                        status_code=400,
                        detail="Invalid CSV file or file cannot be read"
                    )
                
                # Process CSV file
                result = await process_csv_file(temp_file_path, file.filename)
            
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported file type: {file_ext}"
                )
            
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


@router.post("/csv_info")
async def get_csv_info(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Get information about a CSV file before uploading.
    
    Args:
        file: CSV file to analyze
        
    Returns:
        CSV file information including medical content detection and processing time estimate
    """
    try:
        if not file.filename.lower().endswith('.csv'):
            raise HTTPException(
                status_code=400,
                detail="Only CSV files are supported for this endpoint"
            )
        
        # Save file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            csv_processor = get_csv_processor()
            csv_info = csv_processor.get_csv_info(temp_file_path)
            
            # Calculate estimated processing time (1.5 seconds per document average)
            estimated_docs = csv_info.get('estimated_documents', 0)
            estimated_time_seconds = estimated_docs * 1.5
            estimated_time_minutes = estimated_time_seconds / 60
            
            # Determine if file is too large
            is_large = estimated_docs > 100
            is_very_large = estimated_docs > 500
            
            warning = None
            if is_very_large:
                warning = f"⚠️ Very large file! Will create ~{estimated_docs} documents. Processing may take {estimated_time_minutes:.1f} minutes. Consider splitting the file."
            elif is_large:
                warning = f"⚠️ Large file! Will create ~{estimated_docs} documents. Processing may take {estimated_time_minutes:.1f} minutes."
            
            return {
                "filename": file.filename,
                "csv_info": csv_info,
                "estimated_documents": estimated_docs,
                "estimated_time_seconds": int(estimated_time_seconds),
                "estimated_time_minutes": round(estimated_time_minutes, 1),
                "is_large": is_large,
                "is_very_large": is_very_large,
                "warning": warning,
                "supported": True
            }
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
                
    except Exception as e:
        logger.error(f"Error analyzing CSV file: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze CSV file: {str(e)}"
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
