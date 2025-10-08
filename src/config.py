"""Configuration management for the Job Search Agent."""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Ollama configuration (no API key needed for local)
    ollama_model: str = "mistral"
    ollama_base_url: str = "http://localhost:11434"
    
    # Google Drive configuration
    google_credentials_path: str = "credentials/credentials.json"
    google_drive_folder_name: str = "Ascend_Root"  # Folder to search for resumes
    
    # Processing settings
    max_resume_length: int = 50000
    temperature: float = 0.1
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"


def get_settings() -> Settings:
    """Get application settings instance."""
    return Settings()
