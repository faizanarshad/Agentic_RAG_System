"""FastAPI entrypoint for the AIDocumentAgent API."""

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

from api.routes_chat import router as chat_router
from api.routes_files import router as files_router
from api.routes_legal import router as legal_router
from api.routes_engineering import router as engineering_router
from api.routes_contact import router as contact_router
from api.routes_auth import router as auth_router
from api.routes_admin import router as admin_router
from api.routes_analytics import router as analytics_router
from api.routes_posts import admin_router as content_admin_router, public_router
from api.deps import require_user
from api.middleware import activity_logger, origin_guard, security_headers
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
    title="AIDocumentAgent API",
    description="A Retrieval-Augmented Generation system using LangGraph, Pinecone, and OpenAI",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
# Middleware order: the last added runs first. CORS must wrap everything so even
# rejected responses carry CORS headers the browser can read.
app.middleware("http")(activity_logger)
app.middleware("http")(origin_guard)
app.middleware("http")(security_headers)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.FRONTEND_ORIGINS,  # explicit origins: required for credentialed (cookie) requests
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type"],
)

# Public routers
app.include_router(auth_router)
app.include_router(contact_router)
app.include_router(analytics_router)
app.include_router(public_router)

# Workspace routers require a signed-in user; admin routes check the admin role themselves
signed_in = [Depends(require_user)]
app.include_router(chat_router, dependencies=signed_in)
app.include_router(files_router, dependencies=signed_in)
app.include_router(legal_router, dependencies=signed_in)
app.include_router(engineering_router, dependencies=signed_in)
app.include_router(admin_router)
app.include_router(content_admin_router)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "AIDocumentAgent API",
        "version": "1.0.0",
        "description": "A Retrieval-Augmented Generation system using LangGraph, Pinecone, and OpenAI",
        "endpoints": {
            "chat": "/chat/",
            "files": "/files/",
            "legal": "/legal/",
            "engineering": "/engineering/",
            "contact": "/contact",
            "auth": "/auth/",
            "admin": "/admin/",
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
        log_level="info",
        server_header=False,  # don't advertise the server software
    )
