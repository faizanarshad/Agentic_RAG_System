"""FastAPI entrypoint for the Agentic RAG System."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

from api.routes_chat import router as chat_router
from api.routes_files import router as files_router
from core.config import settings
from utils.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    # Startup
    logger.info("Starting Agentic RAG System...")
    
    try:
        # Validate configuration
        settings.validate()
        logger.info("Configuration validated successfully")
        
        logger.info("Agentic RAG System started successfully")
        logger.info("Note: Services will be initialized on first use")
        
    except Exception as e:
        logger.error(f"Failed to start Agentic RAG System: {str(e)}")
        logger.warning("System will start but services may not work without proper API keys")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Agentic RAG System...")


# Create FastAPI application
app = FastAPI(
    title="Agentic RAG System",
    description="A Retrieval-Augmented Generation system using LangGraph, Pinecone, and OpenAI",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat_router)
app.include_router(files_router)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Agentic RAG System API",
        "version": "1.0.0",
        "description": "A Retrieval-Augmented Generation system using LangGraph, Pinecone, and OpenAI",
        "endpoints": {
            "chat": "/chat/",
            "files": "/files/",
            "docs": "/docs",
            "health": "/health"
        }
    }


@app.get("/health")
async def health():
    """System health check endpoint."""
    try:
        # Basic system health check
        return {
            "status": "healthy",
            "message": "System is operational",
            "note": "Services will be initialized on first use"
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "message": "System health check failed"
        }


if __name__ == "__main__":
    # Run the application
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level="info"
    )
