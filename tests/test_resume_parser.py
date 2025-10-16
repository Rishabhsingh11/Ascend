"""Comprehensive test scenarios for resume parser - email extraction focus."""

import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.enhanced_resume_parser import (
    extract_email,
    extract_phone,
    extract_linkedin,
    EnhancedResumeParser
)


# ============================================================================
# EMAIL EXTRACTION TESTS
# ============================================================================

def test_extract_email_simple():
    """Test simple email extraction."""
    text = "Contact me at john.doe@example.com for more info"
    result = extract_email(text)
    assert result == "john.doe@example.com"
    print("✅ Simple email extraction passed")


def test_extract_email_pipe_separated():
    """Test email extraction from pipe-separated line (THE BUG FIX)."""
    text = "rishabhdineshsingh@gmail.com|LinkedIn|Portfolio"
    result = extract_email(text)
    
    # This should extract ONLY the email, not the entire line
    assert result is not None, "Email should be found"
    assert result == "rishabhdineshsingh@gmail.com", f"Expected clean email, got: {result}"
    assert "|" not in result, "Email should not contain pipe character"
    assert "LinkedIn" not in result, "Email should not contain LinkedIn text"
    
    print(f"✅ Pipe-separated email extraction passed: {result}")


def test_extract_email_with_label():
    """Test email with label prefix."""
    text = "Email: contact@company.com | Phone: 555-1234"
    result = extract_email(text)
    assert result == "contact@company.com"
    print("✅ Email with label extraction passed")


def test_extract_email_multiple():
    """Test extraction when multiple emails present (should get first)."""
    text = "Primary: first@email.com, Backup: second@email.com"
    result = extract_email(text)
    assert result == "first@email.com"
    print("✅ Multiple email extraction passed")


def test_extract_email_none():
    """Test when no email present."""
    text = "Just some random text without email"
    result = extract_email(text)
    assert result is None
    print("✅ No email case passed")


def test_extract_email_special_chars():
    """Test email with special characters."""
    text = "Contact: user.name+tag@sub-domain.example.com"
    result = extract_email(text)
    assert result == "user.name+tag@sub-domain.example.com"
    print("✅ Email with special characters passed")


# ============================================================================
# PHONE EXTRACTION TESTS
# ============================================================================

def test_extract_phone_us_format():
    """Test US phone number extraction."""
    text = "Call me at (555) 123-4567"
    result = extract_phone(text)
    assert result is not None
    assert "555" in result
    print(f"✅ US phone extraction passed: {result}")


def test_extract_phone_international():
    """Test international phone format."""
    text = "Phone: +1 555-123-4567"
    result = extract_phone(text)
    assert result is not None
    print(f"✅ International phone extraction passed: {result}")


# ============================================================================
# LINKEDIN EXTRACTION TESTS
# ============================================================================

def test_extract_linkedin_full_url():
    """Test LinkedIn full URL extraction."""
    text = "Profile: https://www.linkedin.com/in/johndoe"
    result = extract_linkedin(text)
    assert result == "https://www.linkedin.com/in/johndoe"
    print("✅ LinkedIn full URL extraction passed")


def test_extract_linkedin_partial():
    """Test LinkedIn partial URL extraction."""
    text = "Find me: linkedin.com/in/johndoe"
    result = extract_linkedin(text)
    
    # LinkedIn extractor adds https:// prefix automatically
    assert result is not None
    assert "linkedin.com/in/johndoe" in result
    print(f"✅ LinkedIn partial URL extraction passed: {result}")


def test_extract_linkedin_pipe_separated():
    """Test LinkedIn from pipe-separated text."""
    text = "email@test.com | LinkedIn: linkedin.com/in/johndoe | Portfolio"
    result = extract_linkedin(text)
    assert result is not None
    assert "linkedin" in result.lower()
    print(f"✅ LinkedIn pipe-separated extraction passed: {result}")


# ============================================================================
# INTEGRATION TESTS WITH REAL RESUME
# ============================================================================

def test_contact_info_extraction_with_pipes():
    """Test full contact info extraction from resume with pipe-separated fields."""
    
    # Create a mock resume with pipe-separated contact line
    test_resume_lines = [
        {'text': 'JOHN DOE', 'font_size': 16, 'bold': True},
        {'text': 'Software Engineer', 'font_size': 11, 'bold': False},
        {'text': 'john.doe@example.com|LinkedIn: linkedin.com/in/johndoe|New York, NY', 'font_size': 10, 'bold': False},
        {'text': '(555) 123-4567', 'font_size': 10, 'bold': False},
    ]
    
    # Mock the parser's extract_contact_info method
    parser = EnhancedResumeParser(file_path="dummy.pdf")
    contact = parser.extract_contact_info(test_resume_lines)
    
    # Verify email is clean
    assert contact.email is not None, "Email should be extracted"
    assert contact.email == "john.doe@example.com", f"Expected clean email, got: {contact.email}"
    assert "|" not in contact.email, "Email should not contain pipe"
    
    print("✅ Contact info extraction with pipes passed")
    print(f"   Name: {contact.name}")
    print(f"   Email: {contact.email}")
    print(f"   Phone: {contact.phone}")
    print(f"   LinkedIn: {contact.linkedin}")


def test_full_resume_parsing():
    """Test parsing with real resume file if available."""
    
    test_input_dir = Path("test_input")
    
    if not test_input_dir.exists():
        pytest.skip("test_input directory not found")
    
    # Find PDF files
    pdf_files = list(test_input_dir.glob("*.pdf"))
    
    if not pdf_files:
        pytest.skip("No PDF files found in test_input")
    
    # Use first PDF
    test_resume = pdf_files[0]
    
    print(f"\n🧪 Testing with real resume: {test_resume.name}")
    
    parser = EnhancedResumeParser(file_path=str(test_resume))
    parsed = parser.parse()
    
    # Verify contact info
    contact = parsed.contact_info
    
    print(f"\n📧 Extracted Contact Info:")
    print(f"   Name: {contact.name or 'N/A'}")
    print(f"   Email: {contact.email or 'N/A'}")
    print(f"   Phone: {contact.phone or 'N/A'}")
    print(f"   LinkedIn: {contact.linkedin or 'N/A'}")
    print(f"   Location: {contact.location or 'N/A'}")
    
    # Critical validations
    if contact.email:
        assert "|" not in contact.email, f"Email contains pipe: {contact.email}"
        assert "@" in contact.email, f"Invalid email format: {contact.email}"
        assert " " not in contact.email, f"Email contains space: {contact.email}"
        print(f"\n✅ Email validation passed: {contact.email}")
    
    # Additional info
    print(f"\n📊 Resume Statistics:")
    print(f"   Skills: {len(parsed.skills)}")
    print(f"   Experience: {len(parsed.experience)} positions")
    print(f"   Education: {len(parsed.education)} degrees")
    print(f"   Projects: {len(parsed.projects)}")
    
    print(f"\n✅ Full resume parsing test passed!")


# ============================================================================
# EDGE CASE TESTS
# ============================================================================

def test_malformed_email():
    """Test handling of malformed email-like strings."""
    text = "Contact: not-an-email@.com"
    result = extract_email(text)
    # Should either extract it or return None, but shouldn't crash
    print(f"✅ Malformed email handled: {result}")


def test_multiple_pipes_in_line():
    """Test line with multiple pipe separators."""
    text = "email@test.com | LinkedIn | Portfolio | GitHub | Website"
    result = extract_email(text)
    assert result == "email@test.com"
    assert "|" not in result
    print("✅ Multiple pipes handled correctly")


def test_unicode_characters():
    """Test handling of unicode in contact info."""
    text = "Contact: user@example.com – Location: New York"
    result = extract_email(text)
    assert result == "user@example.com"
    print("✅ Unicode handling passed")


# ============================================================================
# RUN ALL TESTS
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("COMPREHENSIVE RESUME PARSER TESTS")
    print("=" * 80)
    print()
    
    # Run all tests
    pytest.main([__file__, "-v", "-s"])
