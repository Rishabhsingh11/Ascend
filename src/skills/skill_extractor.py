# src/skills/skill_extractor.py
"""Extract skills from job descriptions"""

import re
from typing import List, Set
import spacy

from src.logger import get_logger

logger = get_logger()

class SkillExtractor:
    """Extract technical and soft skills from text"""
    
    # Common technical skills (extend this list)
    TECHNICAL_SKILLS = {
        # Programming languages
        'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'ruby',
        'php', 'swift', 'kotlin', 'go', 'rust', 'scala', 'r', 'matlab',
        
        # Frameworks
        'react', 'angular', 'vue', 'django', 'flask', 'spring', 'laravel',
        'express', 'fastapi', 'next.js', 'nuxt.js', '.net', 'asp.net',
        
        # Databases
        'sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch',
        'oracle', 'sql server', 'dynamodb', 'cassandra', 'neo4j',
        
        # Cloud & DevOps
        'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins', 'gitlab',
        'terraform', 'ansible', 'ci/cd', 'github actions',
        
        # AI/ML
        'machine learning', 'deep learning', 'tensorflow', 'pytorch',
        'scikit-learn', 'keras', 'nlp', 'computer vision', 'llm',
        
        # Tools
        'git', 'jira', 'confluence', 'figma', 'adobe xd', 'postman',
        'slack', 'tableau', 'power bi', 'excel', 'spark', 'hadoop',
        
        # Methodologies
        'agile', 'scrum', 'kanban', 'devops', 'microservices', 'rest api',
        'graphql', 'oauth', 'jwt', 'tdd', 'bdd'
    }
    
    SOFT_SKILLS = {
        'leadership', 'communication', 'teamwork', 'problem solving',
        'critical thinking', 'time management', 'adaptability',
        'creativity', 'collaboration', 'mentoring', 'presentation skills'
    }
    
    def __init__(self):
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("spaCy model not found. Using fallback method.")
            self.nlp = None
    
    def extract_skills(self, text: str) -> List[str]:
        """
        Extract skills from text (job description or resume)
        
        Args:
            text: Input text
        
        Returns:
            List of extracted skills
        """
        if not text:
            return []
        
        text_lower = text.lower()
        found_skills = set()
        
        # Method 1: Direct keyword matching
        for skill in self.TECHNICAL_SKILLS | self.SOFT_SKILLS:
            if self._skill_in_text(skill, text_lower):
                found_skills.add(skill)
        
        # Method 2: NLP-based extraction (if spaCy is available)
        if self.nlp:
            found_skills.update(self._extract_with_nlp(text))
        
        return sorted(list(found_skills))
    
    def _skill_in_text(self, skill: str, text: str) -> bool:
        """Check if skill exists in text (word boundary aware)"""
        # Use word boundaries to avoid partial matches
        pattern = r'\b' + re.escape(skill) + r'\b'
        return bool(re.search(pattern, text, re.IGNORECASE))
    
    def _extract_with_nlp(self, text: str) -> Set[str]:
        """Extract skills using NLP (noun phrases, entities)"""
        doc = self.nlp(text)
        skills = set()
        
        # Extract noun chunks that might be skills
        for chunk in doc.noun_chunks:
            chunk_text = chunk.text.lower()
            # Check if it matches known skills
            if chunk_text in self.TECHNICAL_SKILLS | self.SOFT_SKILLS:
                skills.add(chunk_text)
        
        return skills
    
    def categorize_skill(self, skill: str) -> str:
        """Categorize skill as technical, soft, tool, etc."""
        skill_lower = skill.lower()
        
        if skill_lower in self.SOFT_SKILLS:
            return "soft"
        elif skill_lower in self.TECHNICAL_SKILLS:
            if any(lang in skill_lower for lang in ['python', 'java', 'javascript', 'c++']):
                return "language"
            elif any(fw in skill_lower for fw in ['react', 'django', 'spring']):
                return "framework"
            elif any(db in skill_lower for db in ['sql', 'mongodb', 'redis']):
                return "database"
            elif any(cloud in skill_lower for cloud in ['aws', 'azure', 'docker']):
                return "cloud"
            else:
                return "technical"
        else:
            return "other"
