"""Configuration management for the RAG system."""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Ensure requests/urllib3 use certifi CA bundle to avoid SSL issues
try:
    import certifi  # type: ignore
    ca_bundle_path = certifi.where()
    # Only set if not already configured by the environment
    os.environ.setdefault("SSL_CERT_FILE", ca_bundle_path)
    os.environ.setdefault("REQUESTS_CA_BUNDLE", ca_bundle_path)
except Exception:
    # certifi not available; proceed without overriding SSL certs
    pass


class Settings:
    """Application settings loaded from environment variables."""
    
    # OpenAI Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    OPENAI_EMBEDDING_MODEL: str = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-ada-002")
    
    # Pinecone Configuration
    PINECONE_API_KEY: str = os.getenv("PINECONE_API_KEY", "")
    PINECONE_ENVIRONMENT: str = os.getenv("PINECONE_ENVIRONMENT", "")
    PINECONE_INDEX_NAME: str = os.getenv("PINECONE_INDEX_NAME", "rag-documents")
    
    # Application Configuration
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "1000"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "200"))
    MAX_RETRIEVAL_RESULTS: int = int(os.getenv("MAX_RETRIEVAL_RESULTS", "5"))
    
    # Legal Document Intelligence Configuration
    LEGAL_MODEL: str = os.getenv("LEGAL_MODEL", "gpt-4.1-mini")
    LEGAL_DATA_DIR: str = os.getenv(
        "LEGAL_DATA_DIR",
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "legal")
    )
    LEGAL_OCR_MAX_PAGES: int = int(os.getenv("LEGAL_OCR_MAX_PAGES", "30"))
    LEGAL_FULL_TEXT_QA_CHARS: int = int(os.getenv("LEGAL_FULL_TEXT_QA_CHARS", "60000"))
    LEGAL_MAX_BATCH_DOCS: int = int(os.getenv("LEGAL_MAX_BATCH_DOCS", "100"))
    LEGAL_MAX_FILE_MB: int = int(os.getenv("LEGAL_MAX_FILE_MB", "25"))
    LEGAL_WORKERS: int = int(os.getenv("LEGAL_WORKERS", "4"))
    
    # Engineering Drawing & Documentation Agent Configuration
    ENGINEERING_MODEL: str = os.getenv("ENGINEERING_MODEL", "gpt-4.1")
    ENGINEERING_DATA_DIR: str = os.getenv(
        "ENGINEERING_DATA_DIR",
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "engineering")
    )
    ENGINEERING_MAX_PAGES: int = int(os.getenv("ENGINEERING_MAX_PAGES", "6"))
    ENGINEERING_MAX_FILE_MB: int = int(os.getenv("ENGINEERING_MAX_FILE_MB", "50"))
    
    # Authentication, admin and analytics
    PLATFORM_DATA_DIR: str = os.getenv(
        "PLATFORM_DATA_DIR",
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "platform")
    )
    FRONTEND_ORIGINS: list = [
        origin.strip().rstrip("/")
        for origin in os.getenv("FRONTEND_ORIGINS", "http://localhost:3001").split(",")
        if origin.strip()
    ]
    SESSION_COOKIE_NAME: str = os.getenv("SESSION_COOKIE_NAME", "ada_session")
    SESSION_TTL_HOURS: int = int(os.getenv("SESSION_TTL_HOURS", "168"))
    COOKIE_SECURE: bool = os.getenv("COOKIE_SECURE", "False").lower() == "true"
    LOGIN_MAX_ATTEMPTS: int = int(os.getenv("LOGIN_MAX_ATTEMPTS", "5"))
    LOGIN_LOCKOUT_MINUTES: int = int(os.getenv("LOGIN_LOCKOUT_MINUTES", "15"))
    PASSWORD_MIN_LENGTH: int = int(os.getenv("PASSWORD_MIN_LENGTH", "10"))
    ANALYTICS_ENABLED: bool = os.getenv("ANALYTICS_ENABLED", "True").lower() == "true"

    # API Configuration
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    def validate(self) -> None:
        """Validate that required environment variables are set."""
        required_vars = [
            ("OPENAI_API_KEY", self.OPENAI_API_KEY),
            ("PINECONE_API_KEY", self.PINECONE_API_KEY),
            ("PINECONE_ENVIRONMENT", self.PINECONE_ENVIRONMENT),
        ]
        
        missing_vars = [var_name for var_name, var_value in required_vars if not var_value]
        
        if missing_vars:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing_vars)}. "
                "Please check your .env file."
            )


# Global settings instance
settings = Settings()
