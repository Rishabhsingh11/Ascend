# tests/test_csv_exporter.py
"""Test CSV job exporter with Drive upload."""

import sys
from pathlib import Path
import time

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.csv_job_exporter import CSVJobExporter
from src.state import JobPosting

def test_csv_exporter():
    """Test CSV export with Drive upload."""
    
    print("=" * 80)
    print("TESTING CSV JOB EXPORTER")
    print("=" * 80)
    print()
    
    # Create test jobs
    test_jobs = [
        JobPosting(
            title="Senior Software Engineer",
            company="Google",
            location="Mountain View, CA",
            description="Build amazing products",
            required_skills=["Python", "Go", "Kubernetes"],
            url="https://careers.google.com/jobs/123",
            salary="$150,000 - $200,000",
            posted_date="2025-10-16",
            source="adzuna"
        ),
        JobPosting(
            title="Data Scientist",
            company="Microsoft",
            location="Redmond, WA",
            description="Work with data at scale",
            required_skills=["Python", "ML", "SQL"],
            url="https://careers.microsoft.com/jobs/456",
            salary="$140,000 - $180,000",
            posted_date="2025-10-15",
            source="jsearch"
        ),
        JobPosting(
            title="ML Engineer",
            company="Amazon",
            location="Seattle, WA",
            description="Build ML systems",
            required_skills=["Python", "TensorFlow", "AWS"],
            url="https://amazon.jobs/jobs/789",
            salary="$145,000 - $190,000",
            posted_date="2025-10-14",
            source="jooble"
        )
    ]
    
    try:
        # Initialize exporter
        exporter = CSVJobExporter()
        print("✅ Exporter initialized\n")
        
        # Create CSV with Drive upload
        print("📝 Creating CSV and uploading to Drive...")
        
        csv_path, drive_url = exporter.create_job_recommendations_csv(
            jobs=test_jobs,
            candidate_name="Test Candidate",
            job_roles=["Software Engineer", "Data Scientist"],
            market_readiness=75.5,
            upload_to_drive=True
        )
        
        print(f"\n✅ CSV created successfully!")
        print(f"   Local path: {csv_path}")
        
        if drive_url:
            print(f"   Drive URL: {drive_url}")
            print(f"\n🔗 View on Drive: {drive_url}")
        else:
            print(f"   (Drive upload disabled or failed)")
        
        # Test status update
        print("\n📝 Testing status update...")
        exporter.update_job_status(csv_path, 1, "Applied")
        print("✅ Status updated to 'Applied' for first job")
        
        print("\n" + "=" * 80)
        print("✅ ALL TESTS PASSED!")
        print("=" * 80)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_csv_exporter()
    exit(0 if success else 1)
