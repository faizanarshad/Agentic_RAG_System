"""Data ingestion service for PDF processing and text chunking."""

import uuid
from typing import List, Dict, Any
import PyPDF2
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document

from core.config import settings
from utils.logger import logger


class DataIngestionService:
    """Service for extracting text from PDFs and creating text chunks."""
    
    def __init__(self):
        """Initialize the data ingestion service."""
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
    
    def extract_text_from_pdf(self, pdf_file_path: str) -> str:
        """
        Extract text content from a PDF file.
        
        Args:
            pdf_file_path: Path to the PDF file
            
        Returns:
            Extracted text content
            
        Raises:
            Exception: If PDF extraction fails
        """
        try:
            logger.info(f"Extracting text from PDF: {pdf_file_path}")
            
            with open(pdf_file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text += page.extract_text() + "\n"
                
                logger.info(f"Successfully extracted {len(text)} characters from PDF")
                return text
                
        except Exception as e:
            logger.error(f"Error extracting text from PDF {pdf_file_path}: {str(e)}")
            raise Exception(f"Failed to extract text from PDF: {str(e)}")
    
    def chunk_text(self, text: str, file_id: str) -> List[Document]:
        """
        Split text into chunks using the configured text splitter.
        
        Args:
            text: Text content to chunk
            file_id: Unique identifier for the file
            
        Returns:
            List of Document objects with metadata
        """
        try:
            logger.info(f"Chunking text for file {file_id}")
            
            # Create documents with metadata
            documents = self.text_splitter.create_documents(
                texts=[text],
                metadatas=[{"file_id": file_id, "source": "pdf"}]
            )
            
            # Add chunk index to metadata
            for i, doc in enumerate(documents):
                doc.metadata["chunk_index"] = i
                doc.metadata["total_chunks"] = len(documents)
            
            logger.info(f"Created {len(documents)} chunks for file {file_id}")
            return documents
            
        except Exception as e:
            logger.error(f"Error chunking text for file {file_id}: {str(e)}")
            raise Exception(f"Failed to chunk text: {str(e)}")
    
    def process_pdf_file(self, pdf_file_path: str) -> Dict[str, Any]:
        """
        Complete PDF processing pipeline: extract text and create chunks.
        
        Args:
            pdf_file_path: Path to the PDF file
            
        Returns:
            Dictionary containing file_id and processed documents
        """
        try:
            # Generate unique file ID
            file_id = str(uuid.uuid4())
            
            # Extract text from PDF
            text = self.extract_text_from_pdf(pdf_file_path)
            
            if not text.strip():
                raise Exception("PDF file appears to be empty or text extraction failed")
            
            # Create text chunks
            documents = self.chunk_text(text, file_id)
            
            logger.info(f"Successfully processed PDF file {pdf_file_path} with file_id: {file_id}")
            
            return {
                "file_id": file_id,
                "documents": documents,
                "total_chunks": len(documents),
                "text_length": len(text)
            }
            
        except Exception as e:
            logger.error(f"Error processing PDF file {pdf_file_path}: {str(e)}")
            raise Exception(f"Failed to process PDF file: {str(e)}")
    
    def validate_pdf_file(self, file_path: str) -> bool:
        """
        Validate that the file is a valid PDF.
        
        Args:
            file_path: Path to the file to validate
            
        Returns:
            True if valid PDF, False otherwise
        """
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                # Try to access the first page to validate
                if len(pdf_reader.pages) > 0:
                    return True
                return False
        except Exception:
            return False
