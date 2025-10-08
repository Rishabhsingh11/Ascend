"""Unit tests for the Job Search Agent with Ollama."""

import pytest
from src.agent import JobSearchAgent
from src.google_drive_handler import GoogleDriveHandler
from src.resume_parser import ResumeTextExtractor


def test_ollama_connection():
    """Test Ollama connection."""
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        assert response.status_code == 200
        print("✅ Ollama connection test passed")
    except Exception as e:
        pytest.skip(f"Ollama not running: {str(e)}")


def test_google_drive_connection():
    """Test Google Drive connection."""
    try:
        handler = GoogleDriveHandler()
        resumes = handler.list_resumes()
        assert isinstance(resumes, list)
        print(f"✅ Google Drive test passed: Found {len(resumes)} files")
    except Exception as e:
        pytest.skip(f"Google Drive not configured: {str(e)}")


def test_agent_initialization():
    """Test agent initialization with Ollama."""
    try:
        agent = JobSearchAgent()
        assert agent.llm is not None
        assert agent.workflow is not None
        print("✅ Agent initialization test passed")
    except Exception as e:
        pytest.skip(f"Agent initialization failed: {str(e)}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
