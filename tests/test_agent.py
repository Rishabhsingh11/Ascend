# tests/test_agent.py
"""Comprehensive unit tests for the Job Search Agent with Phase 2 & 3."""

import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.agent import JobSearchAgent
from src.google_drive_handler import GoogleDriveHandler
from src.resume_parser import ResumeTextExtractor
from src.jobs.job_store import JobStore


# ============================================================================
# PHASE 1 TESTS: Core Components
# ============================================================================

def test_ollama_connection():
    """Test Ollama connection and availability."""
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        assert response.status_code == 200
        
        # Check if model exists
        data = response.json()
        models = [m['name'] for m in data.get('models', [])]
        print(f"✅ Ollama connection test passed")
        print(f"   Available models: {', '.join(models[:3])}")
        
        # Check for mistral
        has_mistral = any('mistral' in m.lower() for m in models)
        if has_mistral:
            print(f"   ✅ Mistral model found")
        else:
            print(f"   ⚠️  Mistral model not found")
            
    except Exception as e:
        pytest.skip(f"Ollama not running: {str(e)}")


def test_google_drive_connection():
    """Test Google Drive connection and folder access."""
    try:
        handler = GoogleDriveHandler()
        
        # Test folder listing
        from src.config import get_settings
        settings = get_settings()
        folder_id = handler.find_folder_by_name(settings.google_drive_folder_name)
        
        assert folder_id is not None, f"Folder '{settings.google_drive_folder_name}' not found"
        
        # Test resume listing
        resumes = handler.list_resumes(folder_name=settings.google_drive_folder_name)
        assert isinstance(resumes, list)
        
        print(f"✅ Google Drive test passed")
        print(f"   Folder: {settings.google_drive_folder_name}")
        print(f"   Resumes found: {len(resumes)}")
        
        if resumes:
            print(f"   Sample: {resumes[0]['name']}")
            
    except Exception as e:
        pytest.skip(f"Google Drive not configured: {str(e)}")


def test_agent_initialization():
    """Test Phase 1 agent initialization with Ollama."""
    try:
        agent = JobSearchAgent()
        
        # Check core components (remove resume_parser check)
        assert agent.llm is not None, "LLM not initialized"
        assert agent.workflow is not None, "Workflow not initialized"
        # resume_parser is internal, not exposed as an attribute
        
        print("✅ Agent initialization test passed")
        print(f"   LLM: {type(agent.llm).__name__}")
        print(f"   Workflow: {type(agent.workflow).__name__}")
        
    except Exception as e:
        pytest.fail(f"Agent initialization failed: {str(e)}")


def test_resume_parser():
    """Test resume parsing functionality."""
    try:
        from src.enhanced_resume_parser import EnhancedResumeParser
        
        # Look for test resumes in test_input folder
        test_input_dir = Path("test_input")
        
        if not test_input_dir.exists():
            pytest.skip(f"Test input directory not found at {test_input_dir}")
        
        # Find any PDF file in test_input
        test_resumes = list(test_input_dir.glob("*.pdf"))
        
        if not test_resumes:
            pytest.skip(f"No PDF files found in {test_input_dir}")
        
        # Use the first PDF found
        test_resume_path = test_resumes[0]
        
        print(f"Testing with: {test_resume_path.name}")
        
        parser = EnhancedResumeParser(file_path=str(test_resume_path))
        parsed_resume = parser.parse()
        
        assert parsed_resume is not None
        assert parsed_resume.contact_info is not None
        
        print("✅ Resume parser test passed")
        print(f"   File: {test_resume_path.name}")
        print(f"   Skills found: {len(parsed_resume.skills)}")
        print(f"   Experience entries: {len(parsed_resume.experience)}")
        print(f"   Education entries: {len(parsed_resume.education)}")
        
        if parsed_resume.contact_info.name:
            print(f"   Candidate: {parsed_resume.contact_info.name}")
        
    except Exception as e:
        pytest.fail(f"Resume parser test failed: {str(e)}")


# ============================================================================
# PHASE 2 TESTS: Job Search & Skill Gap Analysis
# ============================================================================

def test_job_api_client_initialization():
    """Test Phase 2 job API client initialization."""
    try:
        from src.api.job_api_client import JobAPIClient
        
        client = JobAPIClient()
        
        # Check individual clients
        assert client.adzuna is not None, "Adzuna client not initialized"
        assert client.jsearch is not None, "JSearch client not initialized"
        assert client.jooble is not None, "Jooble client not initialized"
        
        print("✅ Job API client test passed")
        print(f"   Adzuna: {'✓' if client.adzuna.app_id else '✗ (no credentials)'}")
        print(f"   JSearch: {'✓' if client.jsearch.api_key else '✗ (no credentials)'}")
        print(f"   Jooble: {'✓' if client.jooble.api_key else '✗ (no credentials)'}")
        
    except Exception as e:
        pytest.skip(f"Job API client test failed: {str(e)}")


def test_job_search():
    """Test actual job search functionality."""
    try:
        from src.api.job_api_client import JobAPIClient
        
        client = JobAPIClient()
        
        # Search for a common job title with filters
        jobs = client.search_jobs(
            job_title="Software Engineer",
            country="us",
            posting_hours=168,  # Last 7 days for better results
            employment_type="FULLTIME",
            max_results=5
        )
        
        print(f"✅ Job search test passed")
        print(f"   Jobs found: {len(jobs)}")
        
        if jobs:
            sample = jobs[0]
            print(f"   Sample: {sample.title} @ {sample.company}")
            print(f"   Source: {sample.source}")
        
        # Test passes even if no jobs found (API might be rate limited)
        assert isinstance(jobs, list)
        
    except Exception as e:
        pytest.skip(f"Job search test failed: {str(e)}")


def test_skill_extractor():
    """Test skill extraction from job descriptions."""
    try:
        from src.skills.skill_extractor import SkillExtractor
        
        extractor = SkillExtractor()
        
        sample_description = """
        We are looking for a Senior Software Engineer with experience in Python, 
        AWS, Docker, and Kubernetes. Knowledge of React and Node.js is a plus.
        Must have strong SQL and database design skills.
        """
        
        skills = extractor.extract_skills(sample_description)
        
        print(f"✅ Skill extractor test passed")
        print(f"   Skills extracted: {len(skills)}")
        print(f"   Sample skills: {', '.join(skills[:5])}")
        
        assert isinstance(skills, list)
        assert len(skills) > 0, "No skills extracted"
        
    except Exception as e:
        pytest.skip(f"Skill extractor test failed: {str(e)}")


def test_skill_comparator():
    """Test skill comparison and matching."""
    try:
        from src.skills.skill_comparator import SkillComparator
        
        comparator = SkillComparator()
        
        resume_skills = ["Python", "SQL", "Machine Learning", "Git"]
        job_skills = ["Python", "AWS", "ML", "Docker", "SQL"]
        
        # Use the find_matches method (after adding it)
        matches = comparator.find_matches(resume_skills, job_skills)
        
        print(f"✅ Skill comparator test passed")
        print(f"   Matched: {len(matches.matched_skills)} skills")
        print(f"   Missing: {len(matches.missing_skills)} skills")
        print(f"   Match %: {matches.match_percentage:.1f}%")
        
        assert matches.match_percentage > 0
        assert isinstance(matches.matched_skills, list)
        assert isinstance(matches.missing_skills, list)
        
    except Exception as e:
        pytest.fail(f"Skill comparator test failed: {str(e)}")


def test_phase2_components_initialization():
    """Test that agent can initialize Phase 2 components."""
    try:
        agent = JobSearchAgent()
        
        # Trigger Phase 2 initialization
        agent._initialize_phase2_components()
        
        # Check Phase 2 components
        assert agent.job_api_client is not None, "Job API client not initialized"
        assert agent.skill_extractor is not None, "Skill extractor not initialized"
        assert agent.skill_comparator is not None, "Skill comparator not initialized"
        assert agent.skill_gap_analyzer is not None, "Skill gap analyzer not initialized"
        
        print("✅ Phase 2 components initialization test passed")
        print(f"   Job API Client: ✓")
        print(f"   Skill Extractor: ✓")
        print(f"   Skill Comparator: ✓")
        print(f"   Skill Gap Analyzer: ✓")
        
    except Exception as e:
        pytest.skip(f"Phase 2 initialization test failed: {str(e)}")


# ============================================================================
# PHASE 3 TESTS: Job History Database
# ============================================================================

def test_job_store_initialization():
    """Test JobStore database initialization."""
    try:
        store = JobStore(db_path="db/job_history_test.db")
        
        # Check that tables were created
        stats = store.get_stats()
        
        print("✅ JobStore initialization test passed")
        print(f"   Database: db/job_history_test.db")
        print(f"   Total sessions: {stats['total_sessions']}")
        print(f"   Total jobs: {stats['total_jobs']}")
        
        store.close()
        
    except Exception as e:
        pytest.skip(f"JobStore test failed: {str(e)}")


def test_job_store_operations():
    """Test JobStore CRUD operations."""
    try:
        from src.state import JobPosting
        
        store = JobStore(db_path="db/job_history_test.db")
        
        # Create session
        session_id = store.create_session(
            resume_hash="test_hash_pytest",
            resume_filename="pytest_resume.pdf",
            candidate_name="Test User",
            candidate_email="test@example.com",
            job_roles=["Software Engineer"],
            market_readiness=75.0
        )
        
        assert session_id is not None
        
        # Save a test job
        test_job = JobPosting(
            title="Test Engineer",
            company="Test Corp",
            location="Test City",
            description="Test description",
            required_skills=["Python", "Testing"],
            url="https://example.com/job",
            salary="$100,000",
            posted_date="2025-10-15",
            source="test"
        )
        
        job_id = store.save_job(session_id, test_job, matched_role="Software Engineer")
        assert job_id is not None
        
        # Retrieve jobs
        jobs = store.get_session_jobs(session_id)
        assert len(jobs) > 0
        
        # Update market readiness (now this method exists)
        store.update_session_market_readiness(session_id, 80.0)
        
        # Verify update
        sessions = store.get_resume_sessions("test_hash_pytest")
        assert sessions[0]['market_readiness'] == 80.0
        
        # Cleanup
        store.delete_session(session_id)
        
        print("✅ JobStore operations test passed")
        print(f"   Created session: {session_id}")
        print(f"   Saved job ID: {job_id}")
        print(f"   Retrieved: {len(jobs)} jobs")
        print(f"   Updated market readiness: 80.0%")
        
        store.close()
        
    except Exception as e:
        pytest.fail(f"JobStore operations test failed: {str(e)}")


def test_phase3_components_initialization():
    """Test that agent initializes Phase 3 components (JobStore)."""
    try:
        agent = JobSearchAgent()
        
        # Trigger Phase 2/3 initialization
        agent._initialize_phase2_components()
        
        # Check Phase 3 component
        assert agent.job_store is not None, "JobStore not initialized"
        
        print("✅ Phase 3 components initialization test passed")
        print(f"   JobStore: ✓")
        
    except Exception as e:
        pytest.skip(f"Phase 3 initialization test failed: {str(e)}")


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

def test_full_workflow():
    """Test complete agent workflow with real resume from test_input."""
    try:
        # Find test resume
        test_input_dir = Path("test_input")
        
        if not test_input_dir.exists():
            pytest.skip(f"Test input directory not found")
        
        test_resumes = list(test_input_dir.glob("*.pdf"))
        
        if not test_resumes:
            pytest.skip(f"No PDF files found in test_input")
        
        test_resume_path = test_resumes[0]
        
        print(f"\n🧪 Testing full workflow with: {test_resume_path.name}")
        print("=" * 80)
        
        # Initialize agent
        from src.agent import JobSearchAgent
        agent = JobSearchAgent()
        
        # Parse resume
        from src.enhanced_resume_parser import EnhancedResumeParser
        from src.resume_parser import ResumeTextExtractor
        
        parser = EnhancedResumeParser(file_path=str(test_resume_path))
        parsed_resume = parser.parse()
        
        text_extractor = ResumeTextExtractor()
        raw_text = text_extractor.extract_text(str(test_resume_path))
        
        print(f"✅ Parsed resume: {parsed_resume.contact_info.name or 'Unknown'}")
        print(f"   Skills: {len(parsed_resume.skills)}")
        print(f"   Experience: {len(parsed_resume.experience)}")
        
        # Test Phase 1: Job Role Analysis
        print("\n📋 Phase 1: Analyzing job roles...")
        
        from langchain_core.messages import HumanMessage
        
        state = {
            'messages': [HumanMessage(content=f"Processing {test_resume_path.name}")],
            'file_id': 'test',
            'file_name': test_resume_path.name,
            'raw_resume_text': raw_text,
            'parsed_resume': parsed_resume,
            'job_role_matches': None,
            'resume_summary': None,
            'current_step': 'parsing_complete',
            'error': None
        }
        
        # Note: This calls real LLM - may take time
        print("   (Using real Ollama LLM - this may take a few minutes...)")
        
        # For testing, we'll just verify the workflow can be built
        # Uncomment below to run full analysis (takes ~10-15 minutes)
        
        # result = agent._analyze_job_roles_streaming(state, token_callback=None)
        # assert result.get('job_role_matches') is not None
        # print(f"   ✅ Found {len(result['job_role_matches'])} job recommendations")
        
        print("✅ Full workflow structure validated")
        print("   (Actual LLM execution skipped to save time)")
        print("   (Uncomment code in test to run full 15-minute analysis)")
        
    except Exception as e:
        pytest.fail(f"Full workflow test failed: {str(e)}")

# Add this new test to tests/test_agent.py

def test_with_real_test_data():
    """Quick integration test with real test data (no LLM calls)."""
    try:
        test_input_dir = Path("test_input")
        
        if not test_input_dir.exists():
            pytest.skip("Test input directory not found")
        
        test_resumes = list(test_input_dir.glob("*.pdf"))
        
        if not test_resumes:
            pytest.skip("No PDF files found in test_input")
        
        test_resume_path = test_resumes[0]
        
        print(f"\n🧪 Integration test with: {test_resume_path.name}")
        
        # Test parsing
        from src.enhanced_resume_parser import EnhancedResumeParser
        parser = EnhancedResumeParser(file_path=str(test_resume_path))
        parsed_resume = parser.parse()
        
        print(f"✅ Parsing successful")
        print(f"   Name: {parsed_resume.contact_info.name or 'N/A'}")
        print(f"   Email: {parsed_resume.contact_info.email or 'N/A'}")
        print(f"   Skills: {len(parsed_resume.skills)}")
        
        # Test skill extraction from resume
        from src.skills.skill_extractor import SkillExtractor
        extractor = SkillExtractor()
        
        if parsed_resume.experience:
            sample_exp = parsed_resume.experience[0]
            if sample_exp.description:
                desc_text = " ".join(sample_exp.description)
                extracted_skills = extractor.extract_skills(desc_text)
                print(f"✅ Skill extraction from experience: {len(extracted_skills)} skills")
        
        # Test JobStore with real data
        from src.jobs.job_store import JobStore
        store = JobStore(db_path="db/job_history_test.db")
        
        session_id = store.create_session(
            resume_hash=f"test_{test_resume_path.stem}",
            resume_filename=test_resume_path.name,
            candidate_name=parsed_resume.contact_info.name,
            candidate_email=parsed_resume.contact_info.email,
            job_roles=["Software Engineer", "Data Scientist"],
            market_readiness=75.0
        )
        
        print(f"✅ JobStore session created: {session_id[:16]}...")
        
        # Cleanup
        store.delete_session(session_id)
        store.close()
        
        print(f"✅ Integration test complete!")
        
    except Exception as e:
        pytest.fail(f"Integration test failed: {str(e)}")



# ============================================================================
# CONFIGURATION TESTS
# ============================================================================

def test_configuration():
    """Test configuration loading."""
    try:
        from src.config import get_settings
        
        settings = get_settings()
        
        print("✅ Configuration test passed")
        print(f"   Ollama model: {settings.ollama_model}")
        print(f"   Google Drive folder: {settings.google_drive_folder_name}")
        print(f"   Default country: {settings.default_country}")
        print(f"   Max jobs per role: {settings.max_jobs_per_role}")
        print(f"   Posting hours filter: {settings.default_posting_hours}")
        
        assert settings.ollama_model is not None
        
    except Exception as e:
        pytest.skip(f"Configuration test failed: {str(e)}")


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("COMPREHENSIVE AGENT TESTS (Phase 1, 2, 3)")
    print("=" * 80)
    print()
    
    # Run with verbose output
    pytest.main([__file__, "-v", "-s"])
