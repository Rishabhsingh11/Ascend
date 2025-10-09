"""Enhanced Resume Parser using PDFPlumber - imports models from state.py"""

import pdfplumber
import re
from typing import List, Dict, Optional

# ✅ IMPORT PYDANTIC MODELS FROM state.py (no duplication!)
from src.state import ContactInfo, Experience, Education, ParsedResume
from src.logger import get_logger



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

def normalize_text(text: str) -> str:
        """Normalize Unicode characters to ASCII equivalents."""
        # Replace en-dash and em-dash with regular hyphen
        text = text.replace('\u2013', '-')  # en-dash
        text = text.replace('\u2014', '-')  # em-dash
        text = text.replace('\u2019', "'")  # right single quotation mark
        text = text.replace('\u2019', "'")  # right single quotation mark
        text = text.replace('\u201c', '"')  # left double quotation mark
        text = text.replace('\u201d', '"')  # right double quotation mark
        return text

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
        """Extract contact information from first few lines."""
        contact_text = ' '.join([line['text'] for line in lines[:10]])
        
        # Extract name (first bold line with larger font, or first non-empty line)
        name = None
        for line in lines[:5]:
            if line['text'] and not extract_email(line['text']):
                # Check if it's a name line (bold OR large font OR all caps)
                is_name = (
                    line['font_size'] >= 11 or  # Lowered from 13
                    line['bold'] or
                    line['text'].isupper()  # All caps names
                )
                if is_name:
                    # Clean the name (remove email/phone if present)
                    name_text = line['text'].split('|')[0].strip()
                    name = name_text
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
        """Parse experience entries - supports multiple formats.
        
        Format 1: Company + Date (bold) → Position + Location → Bullets
        Format 2: Position | Company | Location  Date (all on one bold line) → Bullets
        """
        experiences = []
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Skip empty lines and bullets
            if not line or line.startswith('•') or line.startswith('-'):
                i += 1
                continue
            
            # Check for Format 2: Position | Company | Location  Date (pipe-separated)
            if '|' in line and re.search(r'[A-Z][a-z]{2}\s+\d{4}', line):
                # Parse pipe-separated format
                parts = line.split('|')
                
                if len(parts) >= 2:
                    position = parts[0].strip()
                    company = parts[1].strip()
                    
                    # Third part has location and date
                    if len(parts) >= 3:
                        location_date = parts[2].strip()
                        # Extract date from end
                        date_match = re.search(r'([A-Z][a-z]{2}\s+\d{4}\s*[-–]\s*(?:[A-Z][a-z]{2}\s+\d{4}|Present))', location_date)
                        if date_match:
                            duration = normalize_text(date_match.group(1))
                            location = location_date[:date_match.start()].strip()
                        else:
                            duration = ""
                            location = location_date
                    else:
                        location = ""
                        duration = ""
                    
                    # Collect bullet descriptions
                    descriptions = []
                    current_bullet = ""
                    i += 1
                    
                    while i < len(lines):
                        desc_line = lines[i].strip()
                        
                        # Check if this is a new experience (has | or is a section header)
                        if ('|' in desc_line and re.search(r'[A-Z][a-z]{2}\s+\d{4}', desc_line)) or not desc_line:
                            break
                        
                        if desc_line.startswith('•') or desc_line.startswith('-'):
                            if current_bullet:
                                descriptions.append(current_bullet.strip())
                            current_bullet = desc_line.lstrip('• -').strip()
                            i += 1
                        elif current_bullet:
                            current_bullet += " " + desc_line
                            i += 1
                        else:
                            i += 1
                    
                    if current_bullet:
                        descriptions.append(current_bullet.strip())
                    
                    if company and position:
                        exp = Experience(
                            company=company,
                            position=position,
                            duration=duration,
                            location=location,
                            description=descriptions
                        )
                        experiences.append(exp)
                        continue
            
            # Check for Format 1: Company + Date (original format)
            if re.search(r'[A-Z][a-z]{2}\s+\d{4}\s*-\s*', line) and not line.startswith('•'):
                company, duration = split_company_and_date(line)
                duration = normalize_text(duration)
                
                i += 1
                position = ""
                location = ""
                if i < len(lines):
                    position_line = lines[i].strip()
                    position, location = split_position_and_location(position_line)
                
                descriptions = []
                current_bullet = ""
                i += 1
                
                while i < len(lines):
                    desc_line = lines[i].strip()
                    
                    if re.search(r'[A-Z][a-z]{2}\s+\d{4}\s*-\s*', desc_line) and not desc_line.startswith('•'):
                        break
                    
                    if desc_line.startswith('•') or desc_line.startswith('-'):
                        if current_bullet:
                            descriptions.append(current_bullet.strip())
                        current_bullet = desc_line.lstrip('• -').strip()
                        i += 1
                    elif current_bullet:
                        current_bullet += " " + desc_line
                        i += 1
                    else:
                        i += 1
                
                if current_bullet:
                    descriptions.append(current_bullet.strip())
                
                if company and position:
                    exp = Experience(
                        company=company,
                        position=position,
                        duration=duration,
                        location=location,
                        description=descriptions
                    )
                    experiences.append(exp)
            else:
                i += 1
        
        return experiences

    def parse_education_section(self, lines: List[str]) -> List[Education]:
        """Parse education entries - supports multiple formats."""
        educations = []
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Skip empty lines
            if not line:
                i += 1
                continue
            
            # Normalize Unicode characters
            line = normalize_text(line)
            
            # Format: Degree | Institution - Location  Dates (single pipe separator)
            if '|' in line and re.search(r'\b\d{4}\b', line):
                parts = line.split('|', 1)  # Split on first pipe only
                
                if len(parts) == 2:
                    degree_with_field = parts[0].strip()
                    institution_with_dates = parts[1].strip()
                    
                    # Extract degree and field from first part
                    degree = ""
                    field = None
                    
                    if ' in ' in degree_with_field:
                        degree_parts = degree_with_field.split(' in ', 1)
                        degree = degree_parts[0].strip()
                        field = degree_parts[1].strip()
                    elif ',' in degree_with_field:
                        degree_parts = degree_with_field.split(',', 1)
                        degree = degree_parts[0].strip()
                        field = degree_parts[1].strip()
                    else:
                        degree = degree_with_field
                    
                    # Extract institution from second part (before dash)
                    if ' - ' in institution_with_dates:
                        institution = institution_with_dates.split(' - ')[0].strip()
                    elif ' – ' in institution_with_dates:
                        institution = institution_with_dates.split(' – ')[0].strip()
                    else:
                        institution = institution_with_dates
                    
                    # Extract graduation year (last 4-digit year in the line)
                    graduation_year = None
                    years = re.findall(r'\b\d{4}\b', institution_with_dates)
                    if years:
                        graduation_year = years[-1]
                    
                    if institution and degree:
                        edu = Education(
                            institution=institution,
                            degree=degree,
                            field=field,
                            graduation_year=graduation_year
                        )
                        educations.append(edu)
                    
                    i += 1
                    continue
            
            # Traditional format: Institution - Location with date range
            # Then next line has degree
            if (' - ' in line or ' – ' in line) and re.search(r'\b\d{4}\b', line):
                # Split by dash to get institution
                if ' – ' in line:
                    institution_part = line.split(' – ')[0].strip()
                    remainder = ' – '.join(line.split(' – ')[1:])
                else:
                    institution_part = line.split(' - ')[0].strip()
                    remainder = ' - '.join(line.split(' - ')[1:])
                
                institution = institution_part
                
                # Extract graduation year from the remainder
                graduation_year = None
                years = re.findall(r'\b\d{4}\b', remainder)
                if years:
                    graduation_year = years[-1]
                
                # Next line should contain degree and field
                i += 1
                degree = ""
                field = None
                
                if i < len(lines):
                    degree_line = normalize_text(lines[i].strip())
                    
                    # Skip if it's a bullet or another institution line
                    if not degree_line.startswith('•') and not re.search(r'\b\d{4}\b', degree_line):
                        # Parse degree and field
                        if ' in ' in degree_line:
                            degree_parts = degree_line.split(' in ', 1)
                            degree = degree_parts[0].strip()
                            field = degree_parts[1].strip()
                        elif ',' in degree_line:
                            degree_parts = degree_line.split(',', 1)
                            degree = degree_parts[0].strip()
                            field = degree_parts[1].strip()
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