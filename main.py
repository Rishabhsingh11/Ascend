"""Main entry point for the Job Search Agent with Ollama."""

import os
import json
import subprocess
from dotenv import load_dotenv

from src.agent import JobSearchAgent
from src.google_drive_handler import GoogleDriveHandler
from src.config import get_settings


def check_ollama_running():
    """Check if Ollama is running."""
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        return response.status_code == 200
    except:
        return False


def check_model_available(model_name: str = "mistral"):
    """Check if the specified model is downloaded."""
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        if response.status_code == 200:
            models = response.json().get('models', [])
            return any(model_name in model.get('name', '') for model in models)
        return False
    except:
        return False


def display_results(result: dict):
    """Display formatted results to console.
    
    Args:
        result: Final agent state with all results
    """
    print("\n" + "="*80)
    print("📄 RESUME ANALYSIS RESULTS")
    print("="*80)
    
    if result.get('error'):
        print(f"\n❌ Error: {result['error']}")
        print(f"Failed at step: {result.get('current_step', 'unknown')}")
        return
    
    # Display parsed resume info
    if result.get('parsed_resume'):
        parsed = result['parsed_resume']
        contact = parsed.contact_info
        
        print(f"\n👤 Candidate: {contact.name or 'N/A'}")
        print(f"📧 Email: {contact.email or 'N/A'}")
        print(f"📍 Location: {contact.location or 'N/A'}")
        
        if parsed.skills:
            print(f"\n🛠️  Skills ({len(parsed.skills)}): {', '.join(parsed.skills[:10])}")
            if len(parsed.skills) > 10:
                print(f"   ... and {len(parsed.skills) - 10} more")
        
        if parsed.experience:
            print(f"\n💼 Experience ({len(parsed.experience)} positions)")
            for exp in parsed.experience[:3]:
                print(f"   • {exp.position} at {exp.company} ({exp.duration})")
    
    # Display job role recommendations
    if result.get('job_role_matches'):
        print("\n" + "="*80)
        print("🎯 TOP 3 JOB ROLE RECOMMENDATIONS")
        print("="*80)
        
        for idx, match in enumerate(result['job_role_matches'], 1):
            print(f"\n{idx}. {match.role_title}")
            print(f"   Confidence Score: {match.confidence_score:.1%}")
            print(f"   Reasoning: {match.reasoning}")
            print(f"   Matching Skills: {', '.join(match.key_matching_skills[:5])}")
    
    # Display resume summary
    if result.get('resume_summary'):
        summary = result['resume_summary']
        
        print("\n" + "="*80)
        print("📊 RESUME QUALITY ASSESSMENT")
        print("="*80)
        
        print(f"\n⭐ Quality Score: {summary.quality_score}/10")
        print(f"\n📝 Summary:\n{summary.overall_summary}")
        
        if summary.years_of_experience:
            print(f"\n🕐 Years of Experience: {summary.years_of_experience}")
        
        if summary.key_strengths:
            print(f"\n💪 Key Strengths:")
            for strength in summary.key_strengths:
                print(f"   • {strength}")
        
        if summary.grammatical_issues:
            print(f"\n⚠️  Issues Found:")
            for issue in summary.grammatical_issues:
                print(f"   • {issue}")
        
        if summary.improvement_suggestions:
            print(f"\n💡 Improvement Suggestions:")
            for suggestion in summary.improvement_suggestions:
                print(f"   • {suggestion}")
    
    print("\n" + "="*80)


def save_results(result: dict, output_file: str = "output_result.json"):
    """Save results to JSON file.
    
    Args:
        result: Final agent state with all results
        output_file: Output file path
    """
    output = {
        "file_name": result.get('file_name'),
        "current_step": result.get('current_step'),
        "error": result.get('error'),
        "parsed_resume": result['parsed_resume'].model_dump() if result.get('parsed_resume') else None,
        "job_role_matches": [match.model_dump() for match in result['job_role_matches']] if result.get('job_role_matches') else [],
        "resume_summary": result['resume_summary'].model_dump() if result.get('resume_summary') else None
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Results saved to {output_file}")


def main():
    """Main execution function."""
    # Load environment variables
    load_dotenv()
    
    settings = get_settings()
    
    print("\n🤖 Job Search Agent - Resume Analysis (Powered by Ollama)")
    print("="*80)
    
    # Check Ollama is running
    print("\n🔍 Checking Ollama status...")
    if not check_ollama_running():
        print("\n❌ Ollama is not running!")
        print("\nPlease start Ollama:")
        print("1. Open a new Command Prompt window")
        print("2. Run: ollama serve")
        print("\nOr Ollama should be running automatically if installed.")
        return
    
    print("✅ Ollama is running")
    
    # Check if model is available
    model_name = settings.ollama_model
    print(f"\n🔍 Checking if '{model_name}' model is available...")
    if not check_model_available(model_name):
        print(f"\n❌ Model '{model_name}' not found!")
        print(f"\nPlease download the model:")
        print(f"   ollama pull {model_name}")
        return
    
    print(f"✅ Model '{model_name}' is ready")
    
    # Initialize agent
    try:
        agent = JobSearchAgent()
        drive_handler = GoogleDriveHandler()
    except Exception as e:
        print(f"\n❌ Initialization failed: {str(e)}")
        print("\nPlease ensure:")
        print("1. .env file exists with OLLAMA_MODEL")
        print("2. credentials/credentials.json exists with Google Cloud credentials")
        return
    
    # Check if folder exists
    folder_name = settings.google_drive_folder_name
    print(f"\n🔍 Looking for folder: '{folder_name}'...")
    
    folder_id = drive_handler.find_folder_by_name(folder_name)
    
    if not folder_id:
        print(f"\n❌ Folder '{folder_name}' not found in Google Drive!")
        print(f"\nPlease:")
        print(f"1. Create a folder named '{folder_name}' in your Google Drive")
        print(f"2. Upload resume files (PDF or DOCX) to this folder")
        print(f"3. Or update GOOGLE_DRIVE_FOLDER_NAME in .env file")
        return
    
    print(f"✅ Found folder: '{folder_name}'")
    
    # List available resumes
    try:
        print(f"\n📁 Fetching resumes from '{folder_name}' folder...")
        resumes = drive_handler.list_resumes(folder_name=folder_name)
        
        if not resumes:
            print(f"\n⚠️  No resumes found in '{folder_name}' folder")
            print(f"Please upload PDF or DOCX resume files to the '{folder_name}' folder in Google Drive")
            return
        
        print(f"\n✅ Found {len(resumes)} resume(s) in '{folder_name}':\n")
        for idx, resume in enumerate(resumes, 1):
            size_kb = int(resume.get('size', 0)) / 1024 if resume.get('size') else 0
            print(f"{idx}. {resume['name']} ({size_kb:.1f} KB)")
        
        # Select resume
        if len(resumes) == 1:
            selected_idx = 0
            print(f"\n🎯 Auto-selecting: {resumes[0]['name']}")
        else:
            while True:
                try:
                    choice = input(f"\nSelect resume (1-{len(resumes)}): ")
                    selected_idx = int(choice) - 1
                    if 0 <= selected_idx < len(resumes):
                        break
                    print(f"Please enter a number between 1 and {len(resumes)}")
                except ValueError:
                    print("Please enter a valid number")
        
        selected_resume = resumes[selected_idx]
        
        # Process resume
        result = agent.process_resume(
            file_id=selected_resume['id'],
            file_name=selected_resume['name']
        )
        
        # Display and save results
        display_results(result)
        save_results(result)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Process interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
