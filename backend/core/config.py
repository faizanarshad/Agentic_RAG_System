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
