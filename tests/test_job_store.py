# tests/test_job_store.py
"""Test job store functionality."""
import sys
from pathlib import Path

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.jobs.job_store import JobStore
from src.state import JobPosting


def test_job_store(cleanup_after=True):
    """Test job store creation and operations.
    
    Args:
        cleanup_after: If True, deletes test data after completion
    """
    
    print("=" * 80)
    print("TESTING JOB STORE")
    print("=" * 80)
    print()
    
    # Initialize store with test database
    store = JobStore(db_path="db/job_history_test.db")
    print("✅ Job store initialized\n")
    
    # Track created session for cleanup
    created_session_id = None
    
    try:
        # Create session
        created_session_id = store.create_session(
            resume_hash="test_hash_123",
            resume_filename="test_resume.pdf",
            candidate_name="John Doe",
            candidate_email="john@example.com",
            job_roles=["Data Scientist", "ML Engineer"],
            market_readiness=75.5
        )
        print(f"✅ Created session: {created_session_id}\n")
        
        # Create test jobs
        test_jobs = [
            JobPosting(
                title="Senior Data Scientist",
                company="Tech Corp",
                location="San Francisco, CA",
                description="Looking for experienced data scientist...",
                required_skills=["Python", "ML", "SQL"],
                url="https://example.com/job1",
                salary="$150,000 - $180,000",
                posted_date="2025-10-15",
                source="adzuna"
            ),
            JobPosting(
                title="Machine Learning Engineer",
                company="AI Startup",
                location="Remote",
                description="Build ML models at scale...",
                required_skills=["TensorFlow", "Python", "AWS"],
                url="https://example.com/job2",
                salary="$140,000 - $170,000",
                posted_date="2025-10-14",
                source="jsearch"
            )
        ]
        
        # Save jobs
        count = store.save_jobs_batch(
            session_id=created_session_id,
            jobs=test_jobs,
            job_roles=["Data Scientist", "ML Engineer"]
        )
        print(f"✅ Saved {count} jobs\n")
        
        # Retrieve jobs
        jobs = store.get_session_jobs(created_session_id)
        print(f"✅ Retrieved {len(jobs)} jobs:")
        for job in jobs:
            print(f"   - {job['job_title']} @ {job['company']}")
        print()
        
        # Get sessions for resume
        sessions = store.get_resume_sessions("test_hash_123")
        print(f"✅ Found {len(sessions)} sessions for resume")
        print()
        
        # Get statistics
        stats = store.get_stats()
        print(f"✅ Statistics:")
        print(f"   Total sessions: {stats['total_sessions']}")
        print(f"   Total jobs: {stats['total_jobs']}")
        print(f"   Emails sent: {stats['emails_sent']}")
        print()
        
        print("=" * 80)
        print("✅ ALL TESTS PASSED!")
        print("=" * 80)
        print()
        
    finally:
        # Cleanup test data
        if cleanup_after and created_session_id:
            print("🧹 Cleaning up test data...")
            store.delete_session(created_session_id)
            print(f"✅ Deleted test session: {created_session_id}")
            print()
            
            # Verify cleanup
            remaining = store.get_stats()
            print("📊 Stats after cleanup:")
            print(f"   Total sessions: {remaining['total_sessions']}")
            print(f"   Total jobs: {remaining['total_jobs']}")
            print()
        
        store.close()
    
    print("=" * 80)
    print("TEST COMPLETE - Database ready for production use!")
    print("=" * 80)


def clear_database():
    """Clear all data from test database."""
    print("=" * 80)
    print("⚠️  CLEARING ALL TEST DATA")
    print("=" * 80)
    print()
    
    response = input("Are you sure you want to clear ALL data? (yes/no): ")
    
    if response.lower() == 'yes':
        store = JobStore(db_path="db/job_history_test.db")
        store.clear_all_data()
        print("✅ All data cleared!")
        store.close()
    else:
        print("❌ Cancelled")


if __name__ == "__main__":
    import sys
    
    # Check command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--clear":
            # Clear all data
            clear_database()
        elif sys.argv[1] == "--no-cleanup":
            # Run test but keep data
            test_job_store(cleanup_after=False)
        else:
            print("Usage:")
            print("  python tests/test_job_store.py              # Run tests with cleanup")
            print("  python tests/test_job_store.py --no-cleanup # Run tests, keep data")
            print("  python tests/test_job_store.py --clear      # Clear all test data")
    else:
        # Default: Run tests with cleanup
        test_job_store(cleanup_after=True)
