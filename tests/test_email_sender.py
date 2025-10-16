# tests/test_email_sender.py
"""Test email sender."""

import sys
from pathlib import Path
import time

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.email_sender import EmailSender
from src.csv_job_exporter import CSVJobExporter
from src.state import JobPosting

def test_email_sender():
    """Test sending job recommendations email."""
    
    print("=" * 80)
    print("TESTING EMAIL SENDER")
    print("=" * 80)
    print()
    
    # Create test CSV first
    test_jobs = [
        JobPosting(
            title="Software Engineer",
            company="Google",
            location="Mountain View",
            description="Build stuff",
            required_skills=["Python"],
            url="https://example.com/1",
            salary="$150K",
            posted_date="2025-10-16",
            source="test"
        )
    ]
    
    exporter = CSVJobExporter()
    csv_path, _ = exporter.create_job_recommendations_csv(
        jobs=test_jobs,
        candidate_name="Test User",
        job_roles=["Software Engineer"],
        market_readiness=75.0,
        upload_to_drive=False  # Skip Drive upload
    )
    
    print(f"✅ CSV created: {csv_path}\n")
    
    # Send email
    sender = EmailSender()
    
    # Change this to YOUR email for testing
    test_recipient = "captainvague11@gmail.com"  # <-- CHANGE THIS
    
    print(f"Sending test email to: {test_recipient}")
    
    success = sender.send_job_recommendations(
        recipient_email=test_recipient,
        candidate_name="Test User",
        csv_path=csv_path,
        job_count=len(test_jobs),
        market_readiness=75.0
    )
    
    if success:
        print("\n✅ Email sent successfully!")
        print(f"   Check your inbox: {test_recipient}")
    else:
        print("\n❌ Email failed to send")
        print("   Check your email credentials in .env")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    test_email_sender()
