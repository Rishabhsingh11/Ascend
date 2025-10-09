"""Final Fixed Resume Parser - Handles merged lines correctly."""

import pdfplumber
import re
from typing import List, Dict, Optional
from pydantic import BaseModel, Field


# ============= Pydantic Models (Keep same as before) =============

class ContactInfo(BaseModel):
    name: Optional[str] = Field(None, description="Full name of the candidate")
    email: Optional[str] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    linkedin: Optional[str] = Field(None, description="LinkedIn profile URL")
    location: Optional[str] = Field(None, description="Current location")


class Experience(BaseModel):
    company: str = Field(..., description="Company name")
    position: str = Field(..., description="Job position/title")
    duration: str = Field(..., description="Duration of employment")
    description: List[str] = Field(default_factory=list, description="Job responsibilities and achievements")


class Education(BaseModel):
    institution: str = Field(..., description="Educational institution name")
    degree: str = Field(..., description="Degree earned")
    field: Optional[str] = Field(None, description="Field of study")
    graduation_year: Optional[str] = Field(None, description="Graduation year")


class ParsedResume(BaseModel):
    contact_info: ContactInfo
    summary: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    experience: List[Experience] = Field(default_factory=list)
    education: List[Education] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    projects: List[str] = Field(default_factory=list)


# ============= Configuration =============

SECTION_KEYWORDS = {
    'experience': ['professional experience', 'work experience', 'experience'],
    'education': ['education', 'academic background'],
    'skills': ['skills', 'technical skills', 'core competencies'],
    'projects': ['academic projects', 'projects'],
    'summary': ['summary', 'professional summary', 'objective'],
    'certifications': ['certifications', 'certificates', 'licenses']
}


# ============= Helper Functions =============

def extract_email(text: str) -> Optional[str]:
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    match = re.search(email_pattern, text)
    return match.group(0) if match else None


def extract_phone(text: str) -> Optional[str]:
    phone_pattern = r'[\+\(]?[1-9][0-9 .\-\(\)]{8,}[0-9]'
    match = re.search(phone_pattern, text)
    return match.group(0).strip() if match else None


def extract_linkedin(text: str) -> Optional[str]:
    linkedin_pattern = r'(?:https?://)?(?:www\.)?linkedin\.com/in/[A-Za-z0-9_-]+'
    match = re.search(linkedin_pattern, text, re.IGNORECASE)
    if match:
        return match.group(0)
    if 'linkedin' in text.lower():
        parts = text.split('|')
        for part in parts:
            if 'linkedin' in part.lower() and len(part.strip()) > 8:
                return part.strip()
    return None


def classify_section(text: str) -> Optional[str]:
    text_lower = text.lower().strip()
    for section_type, keywords in SECTION_KEYWORDS.items():
        if any(keyword == text_lower or keyword in text_lower for keyword in keywords):
            return section_type
    return None


def split_company_and_date(line: str) -> tuple:
    """Split merged company and date line."""
    # Pattern: CompanyName + Month Year - Month Year or Present
    date_pattern = r'([A-Z][a-z]{2}\s+\d{4}\s*-\s*(?:[A-Z][a-z]{2}\s+\d{4}|Present))'
    match = re.search(date_pattern, line)
    if match:
        date_str = match.group(1)
        company = line[:match.start()].strip()
        return company, date_str
    return line, ""


def split_position_and_location(line: str) -> tuple:
    """Split merged position and location line."""
    # Common patterns: "PositionCity, State" or "PositionLocation"
    # Look for capitalized words that indicate location (City names, states)
    location_pattern = r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s*[A-Z]{2}|[A-Z][a-z]+,\s*[A-Z][a-z]+)$'
    match = re.search(location_pattern, line)
    if match:
        location = match.group(1)
        position = line[:match.start()].strip()
        return position, location
    return line, ""


def split_institution_location_date(line: str) -> tuple:
    """Split merged institution, location, and date line."""
    # Pattern: Institution - Location + Date range
    date_pattern = r'([A-Z][a-z]{2}\s+\d{4}\s*-\s*[A-Z][a-z]{2}\s+\d{4})'
    date_match = re.search(date_pattern, line)
    
    date_str = ""
    if date_match:
        date_str = date_match.group(1)
        line_without_date = line[:date_match.start()].strip()
    else:
        line_without_date = line
    
    # Split by " - " for institution and location
    if ' - ' in line_without_date:
        parts = line_without_date.split(' - ', 1)
        institution = parts[0].strip()
        location = parts[1].strip() if len(parts) > 1 else ""
        return institution, location, date_str
    
    return line_without_date, "", date_str


# ============= Main Parser =============

class EnhancedResumeParser:
    
    def __init__(self, file_path: str, debug: bool = False):
        self.file_path = file_path
        self.debug = debug
        
    def extract_with_layout(self) -> List[Dict]:
        all_lines = []
        
        with pdfplumber.open(self.file_path) as pdf:
            for page in pdf.pages:
                chars = page.chars
                if not chars:
                    continue
                
                current_line_top = chars[0]['top']
                line_chars = []
                
                for char in chars:
                    if abs(char['top'] - current_line_top) > 3:
                        if line_chars:
                            line_text = "".join([c['text'] for c in line_chars])
                            all_lines.append({
                                'text': line_text.strip(),
                                'font_size': line_chars[0]['size'],
                                'bold': 'bold' in line_chars[0]['fontname'].lower() or 'bd' in line_chars[0]['fontname'].lower()
                            })
                        line_chars = [char]
                        current_line_top = char['top']
                    else:
                        line_chars.append(char)
                
                if line_chars:
                    line_text = "".join([c['text'] for c in line_chars])
                    all_lines.append({
                        'text': line_text.strip(),
                        'font_size': line_chars[0]['size'],
                        'bold': 'bold' in line_chars[0]['fontname'].lower() or 'bd' in line_chars[0]['fontname'].lower()
                    })
        
        return all_lines
    
    def extract_contact_info(self, lines: List[Dict]) -> ContactInfo:
        contact_text = ' '.join([line['text'] for line in lines[:10]])
        
        name = None
        for line in lines[:5]:
            if line['text'] and line['font_size'] >= 13 and not extract_email(line['text']):
                name = line['text']
                break
        
        email = extract_email(contact_text)
        phone = extract_phone(contact_text)
        linkedin = extract_linkedin(contact_text)
        
        location = None
        for line in lines[:5]:
            text = line['text']
            if '|' in text and ('NY' in text or 'MA' in text or 'City' in text):
                location = text.split('|')[0].strip()
                break
        
        return ContactInfo(name=name, email=email, phone=phone, linkedin=linkedin, location=location)
    
    def segment_by_sections(self, lines: List[Dict]) -> Dict[str, List[str]]:
        sections = {}
        current_section = None
        current_content = []
        
        for line in lines:
            text = line['text']
            if not text:
                continue
            
            classified = classify_section(text)
            is_section_header = classified is not None and (line['bold'] or line['font_size'] >= 10.5)
            
            if is_section_header:
                if current_section and current_content:
                    sections[current_section] = current_content
                current_section = classified
                current_content = []
            elif current_section:
                current_content.append(text)
        
        if current_section and current_content:
            sections[current_section] = current_content
        
        return sections
    
    def parse_skills_section(self, lines: List[str]) -> List[str]:
        skills = []
        for line in lines:
            clean_line = line.lstrip('• -').strip()
            if ':' in clean_line:
                parts = clean_line.split(':', 1)
                if len(parts) == 2:
                    skill_text = parts[1].strip()
                    skills.extend([s.strip() for s in skill_text.split(',') if s.strip()])
            elif ',' in clean_line:
                skills.extend([s.strip() for s in clean_line.split(',') if s.strip()])
            else:
                if clean_line and len(clean_line) > 2:
                    skills.append(clean_line)
        return [s for s in skills if s and len(s) > 1]
    
    def parse_experience_section(self, lines: List[str]) -> List[Experience]:
        """Fixed: Properly collects multi-line bullet descriptions."""
        experiences = []
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Look for date pattern in line (indicates company+date line)
            if re.search(r'[A-Z][a-z]{2}\s+\d{4}\s*-\s*', line) and not line.startswith('•'):
                # Split company and date from merged line
                company, duration = split_company_and_date(line)
                
                # Next line should be position + location
                i += 1
                position = ""
                location = ""
                if i < len(lines):
                    position_line = lines[i].strip()
                    position, location = split_position_and_location(position_line)
                
                # Collect bullet descriptions (including continuation lines)
                descriptions = []
                current_bullet = ""
                i += 1
                
                while i < len(lines):
                    desc_line = lines[i].strip()
                    
                    # Check if this is the start of a new experience
                    if re.search(r'[A-Z][a-z]{2}\s+\d{4}\s*-\s*', desc_line) and not desc_line.startswith('•'):
                        break
                    
                    # If it's a bullet point, save previous and start new
                    if desc_line.startswith('•') or desc_line.startswith('-'):
                        if current_bullet:
                            descriptions.append(current_bullet.strip())
                        current_bullet = desc_line.lstrip('• -').strip()
                        i += 1
                    # Continuation of previous bullet
                    elif current_bullet:
                        current_bullet += " " + desc_line
                        i += 1
                    # Empty line or non-bullet before we started collecting
                    else:
                        i += 1
                
                # Add the last bullet if exists
                if current_bullet:
                    descriptions.append(current_bullet.strip())
                
                if company and position:
                    exp = Experience(
                        company=company,
                        position=position,
                        duration=duration,
                        description=descriptions
                    )
                    experiences.append(exp)
            else:
                i += 1
        
        return experiences

    def parse_education_section(self, lines: List[str]) -> List[Education]:
        """Fixed: Properly extracts 4-digit graduation years."""
        educations = []
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Look for institution lines (contain " - " and date pattern)
            if ' - ' in line and re.search(r'\d{4}', line):
                # Split institution, location, and date
                institution, location, date_range = split_institution_location_date(line)
                
                # Extract graduation year (last 4-digit year in range)
                graduation_year = None
                years = re.findall(r'\b\d{4}\b', date_range)  # Changed to capture all 4 digits
                if years:
                    graduation_year = years[-1]  # Take the last year (graduation year)
                
                # Next line should be degree and field
                i += 1
                degree = ""
                field = None
                if i < len(lines):
                    degree_line = lines[i].strip()
                    if not degree_line.startswith('•'):
                        if ',' in degree_line:
                            parts = degree_line.split(',', 1)
                            degree = parts[0].strip()
                            field = parts[1].strip()
                        else:
                            degree = degree_line
                
                if institution and degree:
                    edu = Education(
                        institution=institution,
                        degree=degree,
                        field=field,
                        graduation_year=graduation_year
                    )
                    educations.append(edu)
                
                i += 1
            else:
                i += 1
        
        return educations
    
    def parse_projects_section(self, lines: List[str]) -> List[str]:
        projects = []
        current_project = []
        
        for line in lines:
            line = line.strip()
            if '|' in line and not line.startswith('•'):
                if current_project:
                    projects.append(' '.join(current_project))
                current_project = [line]
            else:
                current_project.append(line)
        
        if current_project:
            projects.append(' '.join(current_project))
        
        return projects
    
    def parse(self) -> ParsedResume:
        lines = self.extract_with_layout()
        contact_info = self.extract_contact_info(lines)
        sections = self.segment_by_sections(lines)
        
        skills = self.parse_skills_section(sections.get('skills', []))
        experiences = self.parse_experience_section(sections.get('experience', []))
        educations = self.parse_education_section(sections.get('education', []))
        projects = self.parse_projects_section(sections.get('projects', []))
        certifications = sections.get('certifications', [])
        summary = ' '.join(sections.get('summary', []))if 'summary' in sections else None
        
        return ParsedResume(
            contact_info=contact_info,
            summary=summary,
            skills=skills,
            experience=experiences,
            education=educations,
            certifications=certifications,
            projects=projects
        )


# ============= Usage =============

if __name__ == "__main__":
    parser = EnhancedResumeParser(
        r"C:\\Users\\RishabhSingh\\Desktop\\Project\\Ascend-\\test_input\\Rishabh_Singh_Resume.pdf"
    )
    parsed_resume = parser.parse()
    
    print("=" * 80)
    print("PARSED RESUME - STRUCTURED OUTPUT")
    print("=" * 80)
    print(parsed_resume.model_dump_json(indent=2))
    
    with open("parsed_resume_structured.json", "w", encoding="utf-8") as f:
        f.write(parsed_resume.model_dump_json(indent=2))
    
    print("\n" + "=" * 80)
    print("Structured JSON saved to: parsed_resume_structured.json")
    print("=" * 80)