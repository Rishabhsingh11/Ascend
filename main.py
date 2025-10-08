"""Main entry point for the Job Search Agent with Ollama."""

import os
import json
from dotenv import load_dotenv

from src.agent import JobSearchAgent
from src.google_drive_handler import GoogleDriveHandler
from src.config import get_settings
from src.logger import get_logger, set_logger, AgentLogger


def check_ollama_running():
    """Check if Ollama is running."""
    logger = get_logger()
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        logger.debug(f"Ollama health check response: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        logger.debug(f"Ollama health check failed: {str(e)}")
        return False


def check_model_available(model_name: str = "mistral"):
    """Check if the specified model is downloaded."""
    logger = get_logger()
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        if response.status_code == 200:
            models = response.json().get('models', [])
            available = any(model_name in model.get('name', '') for model in models)
            logger.debug(f"Model '{model_name}' available: {available}")
            return available
        return False
    except Exception as e:
        logger.debug(f"Model check failed: {str(e)}")
        return False


def print_section(title: str):
    """Print a section header to console."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def display_results(result: dict):
    """Display formatted results to console.
    
    Args:
        result: Final agent state with all results
    """
    logger = get_logger()
    logger.info("Displaying results to user")
    
    print_section("RESUME ANALYSIS RESULTS")
    
    if result.get('error'):
        print(f"\n❌ Error: {result['error']}")
        print(f"Failed at step: {result.get('current_step', 'unknown')}")
        logger.error(f"Processing failed: {result['error']}")
        return
    
    # Display parsed resume info
    if result.get('parsed_resume'):
        parsed = result['parsed_resume']
        contact = parsed.contact_info
        
        print(f"\n👤 Candidate: {contact.name or 'N/A'}")
        print(f"📧 Email: {contact.email or 'N/A'}")
        print(f"📍 Location: {contact.location or 'N/A'}")
        
        if parsed.skills:
            skills_preview = ', '.join(parsed.skills[:10])
            print(f"\n🛠️  Skills ({len(parsed.skills)}): {skills_preview}")
            if len(parsed.skills) > 10:
                print(f"   ... and {len(parsed.skills) - 10} more")
        
        if parsed.experience:
            print(f"\n💼 Experience ({len(parsed.experience)} positions):")
            for exp in parsed.experience[:3]:
                print(f"   • {exp.position} at {exp.company} ({exp.duration})")
    
    # Display job role recommendations
    if result.get('job_role_matches'):
        print_section("TOP 3 JOB ROLE RECOMMENDATIONS")
        
        for idx, match in enumerate(result['job_role_matches'], 1):
            print(f"\n{idx}. {match.role_title}")
            print(f"   Confidence Score: {match.confidence_score:.1%}")
            print(f"   Reasoning: {match.reasoning}")
            skills_preview = ', '.join(match.key_matching_skills[:5])
            print(f"   Matching Skills: {skills_preview}")
    
    # Display resume summary
    if result.get('resume_summary'):
        summary = result['resume_summary']
        
        print_section("RESUME QUALITY ASSESSMENT")
        
        print(f"\n⭐ Quality Score: {summary.quality_score}/10")
        print(f"\n📝 Summary:")
        print(f"{summary.overall_summary}")
        
        if summary.years_of_experience:
            print(f"\n🕐 Years of Experience: {summary.years_of_experience}")
        
        if summary.key_strengths:
            print("\n💪 Key Strengths:")
            for strength in summary.key_strengths:
                print(f"   • {strength}")
        
        if summary.grammatical_issues:
            print("\n⚠️  Issues Found:")
            for issue in summary.grammatical_issues:
                print(f"   • {issue}")
        
        if summary.improvement_suggestions:
            print("\n💡 Improvement Suggestions:")
            for suggestion in summary.improvement_suggestions:
                print(f"   • {suggestion}")
    
    print("\n" + "=" * 80)


def save_results(result: dict, output_file: str = "output_result.json"):
    """Save results to JSON file.
    
    Args:
        result: Final agent state with all results
        output_file: Output file path
    """
    logger = get_logger()
    
    print(f"\n💾 Saving results to {output_file}...")
    logger.info(f"Saving results to {output_file}")
    
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
    
    print(f"✅ Results saved to {output_file}")
    logger.info(f"Results saved successfully")


def main():
    """Main execution function."""
    # Load environment variables
    load_dotenv()
    
    # Initialize logger (background only)
    logger = AgentLogger()
    set_logger(logger)
    
    # User-facing output
    print_section("JOB SEARCH AGENT - RESUME ANALYSIS")
    print("Powered by Ollama + Mistral")
    
    logger.info("=== APPLICATION STARTED ===")
    
    settings = get_settings()
    
    # Check Ollama is running
    print("\n🔍 Checking Ollama status...")
    logger.info("Checking Ollama status")
    
    if not check_ollama_running():
        print("❌ Ollama is not running!")
        print("\nPlease start Ollama:")
        print("1. Open a new Command Prompt window")
        print("2. Run: ollama serve")
        logger.error("Ollama is not running")
        return
    
    print("✅ Ollama is running")
    logger.info("Ollama is running")
    
    # Check if model is available
    model_name = settings.ollama_model
    print(f"🔍 Checking if '{model_name}' model is available...")
    logger.info(f"Checking model availability: {model_name}")
    
    if not check_model_available(model_name):
        print(f"❌ Model '{model_name}' not found!")
        print(f"\nPlease download the model:")
        print(f"   ollama pull {model_name}")
        logger.error(f"Model '{model_name}' not available")
        return
    
    print(f"✅ Model '{model_name}' is ready")
    logger.info(f"Model '{model_name}' is ready")
    
    # Initialize agent
    try:
        print("\n⚙️  Initializing agent...")
        logger.info("Starting agent initialization")
        
        with logger.timer("Agent Initialization"):
            agent = JobSearchAgent()
            drive_handler = GoogleDriveHandler()
        
        print("✅ Agent initialized")
        
    except Exception as e:
        print(f"\n❌ Initialization failed: {str(e)}")
        print("\nPlease ensure:")
        print("1. .env file exists with OLLAMA_MODEL")
        print("2. credentials/credentials.json exists with Google Cloud credentials")
        logger.error(f"Initialization failed: {str(e)}")
        return
    
    # Check if folder exists
    folder_name = settings.google_drive_folder_name
    print(f"\n📁 Looking for folder: '{folder_name}'...")
    logger.info(f"Searching for folder: {folder_name}")
    
    folder_id = drive_handler.find_folder_by_name(folder_name)
    
    if not folder_id:
        print(f"❌ Folder '{folder_name}' not found in Google Drive!")
        print(f"\nPlease:")
        print(f"1. Create a folder named '{folder_name}' in your Google Drive")
        print(f"2. Upload resume files (PDF or DOCX) to this folder")
        print(f"3. Or update GOOGLE_DRIVE_FOLDER_NAME in .env file")
        logger.error(f"Folder '{folder_name}' not found")
        return
    
    print(f"✅ Found folder: '{folder_name}'")
    logger.info(f"Found folder: {folder_name} (ID: {folder_id})")
    
    # List available resumes
    try:
        print(f"\n📄 Fetching resumes from '{folder_name}' folder...")
        logger.info("Fetching resume list from Google Drive")
        
        resumes = drive_handler.list_resumes(folder_name=folder_name)
        
        if not resumes:
            print(f"\n⚠️  No resumes found in '{folder_name}' folder")
            print(f"Please upload PDF or DOCX resume files to the '{folder_name}' folder in Google Drive")
            logger.warning(f"No resumes found in folder")
            return
        
        print(f"✅ Found {len(resumes)} resume(s):\n")
        for idx, resume in enumerate(resumes, 1):
            size_kb = int(resume.get('size', 0)) / 1024 if resume.get('size') else 0
            print(f"  {idx}. {resume['name']} ({size_kb:.1f} KB)")
        
        logger.info(f"Found {len(resumes)} resumes")
        
        # Select resume
        if len(resumes) == 1:
            selected_idx = 0
            print(f"\n🎯 Auto-selecting: {resumes[0]['name']}")
            logger.info(f"Auto-selected resume: {resumes[0]['name']}")
        else:
            print("\n" + "=" * 80)
            while True:
                try:
                    choice = input(f"Select resume (1-{len(resumes)}): ")
                    selected_idx = int(choice) - 1
                    if 0 <= selected_idx < len(resumes):
                        break
                    print(f"Please enter a number between 1 and {len(resumes)}")
                except ValueError:
                    print("Please enter a valid number")
            
            logger.info(f"User selected resume: {resumes[selected_idx]['name']}")
        
        selected_resume = resumes[selected_idx]
        print(f"\n📋 Processing: {selected_resume['name']}")
        print("=" * 80)
        
        # Process resume
        logger.info(f"Starting resume processing: {selected_resume['name']}")
        
        result = agent.process_resume(
            file_id=selected_resume['id'],
            file_name=selected_resume['name']
        )
        
        # Display and save results
        display_results(result)
        save_results(result)
        
        print_section("EXECUTION COMPLETE")
        print(f"📄 Log file saved to: {logger.log_file}")
        logger.info("=== APPLICATION COMPLETED SUCCESSFULLY ===")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Process interrupted by user")
        logger.warning("Process interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        logger.error(f"Error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())


if __name__ == "__main__":
    main()
