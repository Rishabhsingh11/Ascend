# src/skills/skill_comparator.py
"""Compare skills between resume and job postings."""

import re
from typing import List, Dict, Set, Tuple
from collections import Counter
from difflib import SequenceMatcher

from src.logger import get_logger

logger = get_logger()


class SkillComparator:
    """Compare and match skills between resume and job requirements."""
    
    # Skill synonyms/aliases (expand this as needed)
    SKILL_ALIASES = {
        'js': 'javascript',
        'ts': 'typescript',
        'py': 'python',
        'react.js': 'react',
        'reactjs': 'react',
        'vue.js': 'vue',
        'node.js': 'node',
        'nodejs': 'node',
        'postgresql': 'postgres',
        'mongo': 'mongodb',
        'k8s': 'kubernetes',
        'ci/cd': 'cicd',
        'ml': 'machine learning',
        'ai': 'artificial intelligence',
        'nlp': 'natural language processing',
        'aws': 'amazon web services',
        'gcp': 'google cloud platform',
    }
    
    # Skill importance weights (used for prioritization)
    IMPORTANCE_WEIGHTS = {
        'required': 3,
        'preferred': 2,
        'nice-to-have': 1
    }
    
    def __init__(self):
        """Initialize skill comparator."""
        self.similarity_threshold = 0.85  # 85% similarity to consider a match
    
    def normalize_skill(self, skill: str) -> str:
        """
        Normalize skill name for consistent matching.
        
        Args:
            skill: Raw skill name
            
        Returns:
            Normalized skill name
        """
        # Convert to lowercase
        normalized = skill.lower().strip()
        
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', normalized)
        
        # Check for aliases
        if normalized in self.SKILL_ALIASES:
            normalized = self.SKILL_ALIASES[normalized]
        
        # Remove special characters (keep alphanumeric and spaces)
        normalized = re.sub(r'[^a-z0-9\s\+\#\.]', '', normalized)
        
        return normalized
    
    def skills_match(self, skill1: str, skill2: str) -> bool:
        """
        Check if two skills match (exact or fuzzy).
        
        Args:
            skill1: First skill
            skill2: Second skill
            
        Returns:
            True if skills match
        """
        norm1 = self.normalize_skill(skill1)
        norm2 = self.normalize_skill(skill2)
        
        # Exact match
        if norm1 == norm2:
            return True
        
        # Fuzzy match (handles typos, variations)
        similarity = SequenceMatcher(None, norm1, norm2).ratio()
        if similarity >= self.similarity_threshold:
            return True
        
        # Check if one is substring of another (e.g., "react" in "react native")
        if norm1 in norm2 or norm2 in norm1:
            if len(norm1) > 3 and len(norm2) > 3:  # Avoid false positives with short strings
                return True
        
        return False
    
    def find_matching_skills(
        self, 
        resume_skills: List[str], 
        job_skills: List[str]
    ) -> Tuple[List[str], List[str]]:
        """
        Find matched and missing skills.
        
        Args:
            resume_skills: Skills from candidate's resume
            job_skills: Skills required by job posting
            
        Returns:
            Tuple of (matched_skills, missing_skills)
        """
        matched = []
        missing = []
        
        # Normalize all skills
        resume_skills_normalized = [self.normalize_skill(s) for s in resume_skills]
        
        for job_skill in job_skills:
            job_skill_norm = self.normalize_skill(job_skill)
            
            # Check if this job skill matches any resume skill
            found_match = False
            for resume_skill, resume_skill_norm in zip(resume_skills, resume_skills_normalized):
                if self.skills_match(job_skill_norm, resume_skill_norm):
                    matched.append(resume_skill)  # Use original casing from resume
                    found_match = True
                    break
            
            if not found_match:
                missing.append(job_skill)  # Use original casing from job
        
        # Remove duplicates while preserving order
        matched = list(dict.fromkeys(matched))
        missing = list(dict.fromkeys(missing))
        
        return matched, missing
    
    def calculate_match_percentage(
        self, 
        matched_skills: List[str], 
        total_required_skills: int
    ) -> float:
        """
        Calculate skill match percentage.
        
        Args:
            matched_skills: Skills that matched
            total_required_skills: Total skills required by job
            
        Returns:
            Match percentage (0-100)
        """
        if total_required_skills == 0:
            return 100.0
        
        match_pct = (len(matched_skills) / total_required_skills) * 100
        return min(match_pct, 100.0)  # Cap at 100%
    
    def prioritize_missing_skills(
        self, 
        missing_skills: List[str], 
        skill_frequency: Dict[str, int],
        total_jobs: int
    ) -> List[Tuple[str, str, float]]:
        """
        Prioritize missing skills based on frequency across jobs.
        
        Args:
            missing_skills: Skills missing from resume
            skill_frequency: How many jobs mention each skill
            total_jobs: Total number of jobs analyzed
            
        Returns:
            List of (skill, priority, frequency_percentage) tuples
        """
        prioritized = []
        
        for skill in missing_skills:
            freq = skill_frequency.get(self.normalize_skill(skill), 0)
            freq_pct = (freq / total_jobs * 100) if total_jobs > 0 else 0
            
            # Determine priority
            if freq_pct >= 60:
                priority = "high"  # 60%+ of jobs require this
            elif freq_pct >= 30:
                priority = "medium"  # 30-60% of jobs
            else:
                priority = "low"  # <30% of jobs
            
            prioritized.append((skill, priority, freq_pct))
        
        # Sort by frequency (most common first)
        prioritized.sort(key=lambda x: x[2], reverse=True)
        
        return prioritized
    
    def identify_quick_wins(
        self, 
        missing_skills: List[str], 
        skill_frequency: Dict[str, int]
    ) -> List[str]:
        """
        Identify "quick win" skills (easy to learn, high impact).
        
        Quick wins are:
        - Frequently required (mentioned in many jobs)
        - Related to existing skills (easier to learn)
        - Tools/technologies (faster to pick up than languages/frameworks)
        
        Args:
            missing_skills: Skills missing from resume
            skill_frequency: How many jobs mention each skill
            
        Returns:
            List of quick win skills
        """
        quick_wins = []
        
        # Keywords indicating tools/technologies (easier to learn)
        tool_keywords = [
            'git', 'jira', 'docker', 'jenkins', 'postman', 
            'figma', 'slack', 'confluence', 'tableau', 'excel',
            'ci/cd', 'agile', 'scrum'
        ]
        
        for skill in missing_skills:
            skill_norm = self.normalize_skill(skill)
            freq = skill_frequency.get(skill_norm, 0)
            
            # Quick win criteria: frequent + tool/methodology
            if freq >= 3 and any(keyword in skill_norm for keyword in tool_keywords):
                quick_wins.append(skill)
        
        return quick_wins
    
    def identify_long_term_goals(
        self, 
        missing_skills: List[str], 
        skill_frequency: Dict[str, int]
    ) -> List[str]:
        """
        Identify long-term skill goals (complex, time-intensive).
        
        Long-term goals are:
        - Programming languages
        - Frameworks requiring deep knowledge
        - Complex cloud/infrastructure skills
        
        Args:
            missing_skills: Skills missing from resume
            skill_frequency: How many jobs mention each skill
            
        Returns:
            List of long-term goal skills
        """
        long_term = []
        
        # Keywords indicating complex skills
        complex_keywords = [
            'java', 'c++', 'scala', 'rust', 'go', 'ruby',
            'spring', 'django', 'angular', 'vue',
            'kubernetes', 'terraform', 'aws', 'azure', 'gcp',
            'machine learning', 'deep learning', 'data science',
            'microservices', 'distributed systems'
        ]
        
        for skill in missing_skills:
            skill_norm = self.normalize_skill(skill)
            
            # Long-term criteria: complex technology
            if any(keyword in skill_norm for keyword in complex_keywords):
                long_term.append(skill)
        
        return long_term
    
    def calculate_skill_coverage_score(
        self, 
        match_percentage: float, 
        resume_skill_count: int,
        avg_job_skill_count: float
    ) -> float:
        """
        Calculate overall skill coverage score (0-10 scale).
        
        Considers:
        - Match percentage
        - Breadth of skills (how many skills candidate has)
        - Market alignment
        
        Args:
            match_percentage: Percentage of required skills matched
            resume_skill_count: Total skills in resume
            avg_job_skill_count: Average skills required per job
            
        Returns:
            Coverage score (0-10)
        """
        # Base score from match percentage (0-7 points)
        base_score = (match_percentage / 100) * 7
        
        # Bonus for skill breadth (0-2 points)
        breadth_ratio = min(resume_skill_count / avg_job_skill_count, 1.5) if avg_job_skill_count > 0 else 1
        breadth_bonus = breadth_ratio * 2
        
        # Bonus for exceeding requirements (0-1 point)
        excellence_bonus = 1 if match_percentage >= 90 else 0
        
        total_score = base_score + breadth_bonus + excellence_bonus
        
        return min(round(total_score, 1), 10.0)  # Cap at 10.0
    
    def estimate_learning_time(self, skill: str, priority: str) -> str:
        """
        Estimate time to learn a skill.
        
        Args:
            skill: Skill name
            priority: Priority level (high/medium/low)
            
        Returns:
            Time estimate string
        """
        skill_norm = self.normalize_skill(skill)
        
        # Tool/methodology skills (quick to learn)
        if any(kw in skill_norm for kw in ['git', 'jira', 'docker', 'agile', 'scrum']):
            return "1-2 weeks"
        
        # Framework/library skills (medium time)
        if any(kw in skill_norm for kw in ['react', 'vue', 'angular', 'django', 'flask']):
            return "1-2 months"
        
        # Programming language skills (longer time)
        if any(kw in skill_norm for kw in ['java', 'python', 'javascript', 'c++', 'go']):
            return "2-4 months"
        
        # Complex infrastructure/ML skills (longest time)
        if any(kw in skill_norm for kw in ['kubernetes', 'aws', 'machine learning', 'deep learning']):
            return "3-6 months"
        
        # Default based on priority
        if priority == "high":
            return "2-3 months"
        elif priority == "medium":
            return "1-2 months"
        else:
            return "2-4 weeks"
    
    def analyze_skill_trends(
        self, 
        all_job_skills: List[str], 
        resume_skills: List[str]
    ) -> Tuple[List[str], List[str]]:
        """
        Identify trending and declining skills.
        
        Args:
            all_job_skills: All skills from all job postings
            resume_skills: Skills from resume
            
        Returns:
            Tuple of (trending_skills, declining_skills)
        """
        # Count skill frequency
        skill_counter = Counter([self.normalize_skill(s) for s in all_job_skills])
        resume_skills_norm = [self.normalize_skill(s) for s in resume_skills]
        
        # Trending: frequently mentioned in jobs, high demand
        trending = []
        for skill, count in skill_counter.most_common(10):
            if count >= 5 and skill not in resume_skills_norm:  # Appears in 5+ jobs
                # Find original casing
                original = next((s for s in all_job_skills if self.normalize_skill(s) == skill), skill)
                trending.append(original)
        
        # Declining: in resume but rarely/never in jobs (potentially outdated)
        declining = []
        outdated_keywords = [
            'jquery', 'flash', 'silverlight', 'visual basic', 'perl',
            'xml', 'soap', 'jsp', 'struts'
        ]
        
        for skill in resume_skills:
            skill_norm = self.normalize_skill(skill)
            if skill_norm in outdated_keywords or skill_counter.get(skill_norm, 0) == 0:
                declining.append(skill)
        
        return trending[:5], declining[:5]  # Top 5 of each


logger.info("✅ SkillComparator initialized")
