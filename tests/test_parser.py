"""Test the enhanced parser independently."""

from src.enhanced_resume_parser import EnhancedResumeParser

def test_parser():
    parser = EnhancedResumeParser(
        file_path="test_input/Rishabh_Singh_Resume.pdf",
        debug=True  # Enable debug output
    )
    
    result = parser.parse()
    
    print("\n=== PARSED RESULTS ===")
    print(f"Name: {result.contact_info.name}")
    print(f"Email: {result.contact_info.email}")
    print(f"Skills: {len(result.skills)}")
    print(f"Experience: {len(result.experience)}")
    print(f"Education: {len(result.education)}")
    
    # Save to JSON
    import json
    with open("test_output.json", "w") as f:
        json.dump(result.model_dump(), f, indent=2)
    
    print("\n✅ Test passed! Check test_output.json")

if __name__ == "__main__":
    test_parser()
