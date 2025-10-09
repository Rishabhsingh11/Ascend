"""Compare parsing behavior across two resumes."""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.enhanced_resume_parser import EnhancedResumeParser

def analyze_resume(file_path: str):
    """Analyze a resume and print diagnostic info."""
    print(f"\n{'='*80}")
    print(f"ANALYZING: {file_path}")
    print(f"{'='*80}\n")
    
    parser = EnhancedResumeParser(file_path, debug=True)
    
    # Extract lines first to inspect
    lines = parser.extract_with_layout()
    
    print(f"\nTotal lines extracted: {len(lines)}")
    print("\n--- First 30 Lines (with metadata) ---")
    for i, line in enumerate(lines[:30]):
        print(f"Line {i:3d} | Font: {line['font_size']:5.1f} | Bold: {line['bold']:5} | Text: {line['text'][:60]}")
    
    print("\n--- Parsing Results ---")
    result = parser.parse()
    
    print(f"\nContact: {result.contact_info.name}")
    print(f"Skills: {len(result.skills)}")
    print(f"Experience: {len(result.experience)}")
    print(f"Education: {len(result.education)}")
    
    if len(result.experience) == 0:
        print("\n⚠️ WARNING: No experience found! Check section detection.")
    
    if len(result.education) == 0:
        print("\n⚠️ WARNING: No education found! Check section detection.")

if __name__ == "__main__":
    # Working resume
    print("\n" + "="*80)
    print("RESUME 1: Known Working Resume")
    print("="*80)
    analyze_resume("test_input/Rishabh_Singh_Resume.pdf")
    
    # Problematic resume
    print("\n\n" + "="*80)
    print("RESUME 2: Problematic Resume")
    print("="*80)
    analyze_resume("test_input/Rishabh_Dinesh_Singh_resume.pdf")
