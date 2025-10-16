"""Configuration management for the Job Search Agent."""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # ===== PHASE 1: OLLAMA CONFIGURATION =====
    ollama_model: str = Field(
        default="mistral",
        description="Ollama model name for LLM inference"
    )
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        description="Ollama API base URL"
    )
    
    # ===== PHASE 1: GOOGLE DRIVE CONFIGURATION =====
    google_credentials_path: str = Field(
        default="credentials/credentials.json",
        description="Path to Google Cloud credentials JSON file"
    )
    google_drive_folder_name: str = Field(
        default="Ascend_Root",
        description="Google Drive folder name containing resumes"
    )
    
    # ===== PHASE 1: PROCESSING SETTINGS =====
    max_resume_length: int = Field(
        default=50000,
        description="Maximum resume text length to process"
    )
    temperature: float = Field(
        default=0.1,
        description="LLM temperature for generation"
    )
    
    # ===== PHASE 2: ADZUNA API CONFIGURATION =====
    adzuna_app_id: Optional[str] = Field(
        default=None,
        description="Adzuna API Application ID"
    )
    adzuna_app_key: Optional[str] = Field(
        default=None,
        description="Adzuna API Application Key"
    )
    
    # ===== PHASE 2: RAPIDAPI JSEARCH CONFIGURATION =====
    rapidapi_key: Optional[str] = Field(
        default=None,
        description="RapidAPI Key for JSearch (Google Jobs)"
    )
    rapidapi_host: str = Field(
        default="jsearch.p.rapidapi.com",
        description="RapidAPI Host for JSearch"
    )
    
    # ===== PHASE 2: JOOBLE API CONFIGURATION =====
    jooble_api_key: Optional[str] = Field(
        default=None,
        description="Jooble API Key"
    )
    
    # ===== PHASE 2: JOB SEARCH SETTINGS =====
    default_country: str = Field(
        default="us",
        description="Default country code for job search (us, uk, de, etc.)"
    )
    max_jobs_per_role: int = Field(
        default=10,
        description="Maximum number of jobs to fetch per job role"
    )
    skill_extraction_enabled: bool = Field(
        default=True,
        description="Enable automatic skill extraction from job descriptions"
    )
    default_results_per_page: int = Field(
        default=20,
        description="Default number of results per page for API calls"
    )

    default_posting_hours: int = Field(
        default=24,
        description="Default hours for job posting filter (24 = last 24 hours)"
    )
    employment_type: str = Field(
        default="FULLTIME",
        description="Employment type filter (FULLTIME, PARTTIME, CONTRACTOR)"
    )
    jobs_per_api_call: int = Field(
        default=20,
        description="Number of jobs to fetch per API call (mindful of rate limits)"
    )
    allow_retry_with_relaxed_filters: bool = Field(
        default=True,
        description="Allow user to retry with relaxed date filters if no jobs found"
    )
    
    # ===== LOGGING CONFIGURATION =====
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR)"
    )

    google_owner_email: str = Field(
        default="rishabhdineshsingh@gmail.com",
        description="Email to transfer sheet ownership to"
    )

    smtp_server: str = Field(
        default="smtp.gmail.com",
        description="SMTP server for sending emails"
    )
    smtp_port: int = Field(
        default=587,
        description="SMTP port (587 for TLS)"
    )
    sender_email: Optional[str] = Field(
        default=None,
        description="Email address to send from"
    )
    sender_password: Optional[str] = Field(
        default=None,
        description="Email password or app password"
    )
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False  # Allow case-insensitive env var names
        extra = "ignore"  # Ignore extra fields in .env to avoid validation errors


def get_settings() -> Settings:
    """Get application settings instance.
    
    Returns:
        Settings: Singleton settings instance loaded from environment variables
    """
    return Settings()
