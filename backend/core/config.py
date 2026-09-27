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
    # Any OpenAI-compatible endpoint: Azure OpenAI (https://<resource>.openai.azure.com/openai/v1/, stays in your
    # tenant) or a self-hosted model server such as vLLM or Ollama (http://localhost:11434/v1), so documents never
    # leave your infrastructure. Empty = api.openai.com.
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "")
    
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
    # Replace identifiers (emails, phone numbers, SSNs, MRNs, full dates...) in medical text before it is
    # embedded or sent to the model provider
    MEDICAL_REDACT_PHI: bool = os.getenv("MEDICAL_REDACT_PHI", "True").lower() == "true"
    # Automatic backups of every database and uploaded file (see manage.py backup / restore)
    BACKUP_DIR: str = os.getenv("BACKUP_DIR") or os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backups"
    )
    BACKUP_KEEP: int = int(os.getenv("BACKUP_KEEP", "14"))
    BACKUP_INTERVAL_HOURS: float = float(os.getenv("BACKUP_INTERVAL_HOURS", "24"))
    ANALYTICS_ENABLED: bool = os.getenv("ANALYTICS_ENABLED", "True").lower() == "true"
    # On-demand revalidation of the Next.js site when posts or settings change
    # Public website address used in emailed links (invitations, password resets)
    PUBLIC_SITE_URL: str = os.getenv("PUBLIC_SITE_URL", "http://localhost:3001").rstrip("/")
    SMTP_HOST: str = os.getenv("SMTP_HOST", "")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM: str = os.getenv("SMTP_FROM", "")
    RESET_TOKEN_MINUTES: int = int(os.getenv("RESET_TOKEN_MINUTES", "60"))
    INVITE_TOKEN_HOURS: int = int(os.getenv("INVITE_TOKEN_HOURS", "72"))
    SITE_REVALIDATE_URL: str = os.getenv("SITE_REVALIDATE_URL", "http://localhost:3001/api/revalidate")
    REVALIDATE_SECRET: str = os.getenv("REVALIDATE_SECRET", "")
    UPLOAD_MAX_MB: int = int(os.getenv("UPLOAD_MAX_MB", "8"))

    # Deployment safety
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development").strip().lower()
    # Reverse proxies whose X-Forwarded-For header is trusted (comma-separated IPs), e.g. "127.0.0.1"
    TRUSTED_PROXIES: list = [p.strip() for p in os.getenv("TRUSTED_PROXIES", "").split(",") if p.strip()]

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


    def production_problems(self) -> list:
        """Settings that are unsafe in production. The API refuses to start in production if any are found."""
        problems = []
        if not self.COOKIE_SECURE:
            problems.append("COOKIE_SECURE must be True (session cookies over HTTPS only)")
        insecure = [o for o in self.FRONTEND_ORIGINS if not o.startswith("https://") or "localhost" in o or "127.0.0.1" in o]
        if not self.FRONTEND_ORIGINS or insecure:
            problems.append(f"FRONTEND_ORIGINS must list only https:// production origins (got {self.FRONTEND_ORIGINS})")
        if len(self.REVALIDATE_SECRET) < 32:
            problems.append("REVALIDATE_SECRET must be set to a random value of at least 32 characters")
        if not self.TRUSTED_PROXIES:
            problems.append("TRUSTED_PROXIES must list your reverse proxy IPs so client IPs (sign-in throttling) are correct")
        if not os.getenv("DATA_ENCRYPTION_KEY"):
            problems.append("DATA_ENCRYPTION_KEY must be set (base64, 32 bytes) so the key is not stored beside the data")
        if self.DEBUG:
            problems.append("DEBUG must be False")
        if not self.PUBLIC_SITE_URL.startswith("https://"):
            problems.append("PUBLIC_SITE_URL must be the https:// address of the website (used in emailed links)")
        return problems


# Global settings instance
settings = Settings()
