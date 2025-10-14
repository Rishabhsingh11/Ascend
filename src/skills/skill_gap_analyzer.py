# src/skills/skill_gap_analyzer.py
"""Main skill gap analysis orchestrator."""

from typing import List, Dict
from collections import Counter, defaultdict
from datetime import datetime

from src.state import (
    JobPosting, SkillGap, RoleSkillAnalysis, 
    SkillGapAnalysis, SkillCategory
)
from src.skills.skill_extractor import SkillExtractor
from src.skills.skill_comparator import SkillComparator
from src.logger import get_logger

logger = get_logger()


class SkillGapAnalyzer:
    """Main orchestrator for comprehensive skill gap analysis."""
    
    def __init__(self, skill_extractor: SkillExtractor, skill_comparator: SkillComparator):
        """
        Initialize skill gap analyzer.
        
        Args:
            skill_extractor: Skill extraction component
            skill_comparator: Skill comparison component
        """
        self.extractor = skill_extractor
        self.comparator = skill_comparator
        self.logger = get_logger()
    
    def analyze(
        self, 
        resume_skills: List[str], 
        job_postings: List[JobPosting],
        job_roles: List[str]
    ) -> SkillGapAnalysis:
        """
        Perform comprehensive skill gap analysis.
        
        Args:
            resume_skills: Skills extracted from candidate's resume
            job_postings: Job postings fetched from APIs
            job_roles: Top 3 recommended job roles
            
        Returns:
            Complete skill gap analysis
        """
        self.logger.info("🔍 Starting comprehensive skill gap analysis...")
        
        # Step 1: Extract skills from all job descriptions
        self.logger.info("📊 Extracting skills from job descriptions...")
        self._extract_job_skills(job_postings)
        
        # Step 2: Group jobs by role
        jobs_by_role = self._group_jobs_by_role(job_postings, job_roles)
        
        # Step 3: Analyze each role separately
        self.logger.info(f"🎯 Analyzing {len(job_roles)} job roles...")
        role_analyses = []
        
        for role in job_roles:
            role_jobs = jobs_by_role.get(role, [])
            if role_jobs:
                self.logger.info(f"   → {role}: {len(role_jobs)} jobs")
                role_analysis = self._analyze_role(role, resume_skills, role_jobs)
                role_analyses.append(role_analysis)
            else:
                self.logger.warning(f"   ⚠️  {role}: No jobs found")
        
        # Step 4: Generate cross-role insights
        self.logger.info("🔗 Generating cross-role insights...")
        common_gaps = self._find_common_gaps(role_analyses)
        quick_wins = self._identify_quick_wins(role_analyses, job_postings)
        long_term = self._identify_long_term_goals(role_analyses, job_postings)
        niche = self._identify_niche_skills(role_analyses)
        
        # Step 5: Analyze market trends
        self.logger.info("📈 Analyzing market trends...")
        all_job_skills = []
        for job in job_postings:
            all_job_skills.extend(job.required_skills)
        
        trending, declining = self.comparator.analyze_skill_trends(all_job_skills, resume_skills)
        
        # Step 6: Generate action plans
        self.logger.info("📋 Generating action plans...")
        immediate, one_month, three_month, six_month = self._generate_action_plans(
            common_gaps, quick_wins, long_term
        )
        
        # Step 7: Calculate overall market readiness
        avg_match = sum(r.match_percentage for r in role_analyses) / len(role_analyses) if role_analyses else 0
        
        # Create final analysis
        analysis = SkillGapAnalysis(
            role_analyses=role_analyses,
            common_gaps=common_gaps,
            quick_wins=quick_wins,
            long_term_goals=long_term,
            niche_skills=niche,
            trending_skills=trending,
            declining_skills=declining,
            immediate_actions=immediate,
            one_month_plan=one_month,
            three_month_plan=three_month,
            six_month_plan=six_month,
            overall_market_readiness=round(avg_match, 1),
            total_jobs_analyzed=len(job_postings),
            analysis_date=datetime.now().strftime("%Y-%m-%d")
        )
        
        self.logger.info(f"✅ Skill gap analysis complete!")
        self.logger.info(f"   Market readiness: {analysis.overall_market_readiness}%")
        
        return analysis
    
    def _extract_job_skills(self, job_postings: List[JobPosting]) -> None:
        """Extract skills from job descriptions and populate required_skills."""
        for job in job_postings:
            if not job.required_skills:  # Only extract if not already done
                skills = self.extractor.extract_skills(job.description)
                job.required_skills = skills
    
    def _group_jobs_by_role(
        self, 
        job_postings: List[JobPosting], 
        job_roles: List[str]
    ) -> Dict[str, List[JobPosting]]:
        """Group job postings by recommended role."""
        jobs_by_role = defaultdict(list)
        
        for job in job_postings:
            # Match job to role based on title similarity
            job_title_lower = job.title.lower()
            
            for role in job_roles:
                role_lower = role.lower()
                
                # Simple keyword matching (can be improved with NLP)
                role_keywords = role_lower.split()
                if any(keyword in job_title_lower for keyword in role_keywords if len(keyword) > 3):
                    jobs_by_role[role].append(job)
                    break  # Assign to first matching role
        
        return jobs_by_role
    
    def _analyze_role(
        self, 
        role: str, 
        resume_skills: List[str], 
        role_jobs: List[JobPosting]
    ) -> RoleSkillAnalysis:
        """Analyze skill gap for a single job role."""
        
        # Aggregate all skills required for this role
        all_required_skills = []
        skill_frequency = Counter()
        
        for job in role_jobs:
            for skill in job.required_skills:
                skill_norm = self.comparator.normalize_skill(skill)
                skill_frequency[skill_norm] += 1
                all_required_skills.append(skill)
        
        # Get unique required skills (most common version of each)
        unique_required = []
        seen_normalized = set()
        
        for skill in all_required_skills:
            skill_norm = self.comparator.normalize_skill(skill)
            if skill_norm not in seen_normalized:
                seen_normalized.add(skill_norm)
                unique_required.append(skill)
        
        # Find matched and missing skills
        matched, missing = self.comparator.find_matching_skills(resume_skills, unique_required)
        
        # Calculate match percentage
        match_pct = self.comparator.calculate_match_percentage(matched, len(unique_required))
        
        # Prioritize missing skills
        prioritized_missing = self.comparator.prioritize_missing_skills(
            missing, skill_frequency, len(role_jobs)
        )
        
        # Create SkillGap objects
        skill_gaps = []
        for skill, priority, freq_pct in prioritized_missing:
            learning_time = self.comparator.estimate_learning_time(skill, priority)
            
            gap = SkillGap(
                skill_name=skill,
                category=self.extractor.categorize_skill(skill),
                found_in_jobs_count=skill_frequency.get(self.comparator.normalize_skill(skill), 0),
                priority=priority,
                learning_resources=[],  # Can be populated with actual resources
                estimated_learning_time=learning_time
            )
            skill_gaps.append(gap)
        
        # Identify emerging skills (trending in this role)
        emerging = [
            skill for skill, count in skill_frequency.most_common(5)
            if count >= len(role_jobs) * 0.4  # In 40%+ of jobs
        ]
        
        # Calculate coverage score
        avg_skills_per_job = sum(len(j.required_skills) for j in role_jobs) / len(role_jobs) if role_jobs else 0
        coverage_score = self.comparator.calculate_skill_coverage_score(
            match_pct, len(resume_skills), avg_skills_per_job
        )
        
        # Top skills to learn (top 5 by priority)
        top_skills = [gap.skill_name for gap in sorted(
            skill_gaps, 
            key=lambda x: (
                {'high': 0, 'medium': 1, 'low': 2}[x.priority],
                -x.found_in_jobs_count
            )
        )[:5]]
        
        # Estimate readiness
        if match_pct >= 80:
            readiness = "Ready now"
        elif match_pct >= 60:
            readiness = "1-2 months"
        elif match_pct >= 40:
            readiness = "3-4 months"
        else:
            readiness = "6+ months"
        
        return RoleSkillAnalysis(
            job_role=role,
            jobs_analyzed=len(role_jobs),
            matched_skills=matched,
            missing_skills=skill_gaps,
            emerging_skills=emerging,
            match_percentage=round(match_pct, 1),
            skill_coverage_score=coverage_score,
            top_skills_to_learn=top_skills,
            estimated_readiness=readiness
        )
    
    def _find_common_gaps(self, role_analyses: List[RoleSkillAnalysis]) -> List[str]:
        """Find skills missing across ALL roles (highest priority)."""
        if not role_analyses:
            return []
        
        # Get missing skills from each role
        missing_by_role = [
            set(self.comparator.normalize_skill(gap.skill_name) for gap in analysis.missing_skills)
            for analysis in role_analyses
        ]
        
        # Find intersection (skills missing in ALL roles)
        if not missing_by_role:
            return []
        
        common = missing_by_role[0]
        for missing_set in missing_by_role[1:]:
            common &= missing_set
        
        # Get original skill names (with proper casing)
        common_skills = []
        for analysis in role_analyses:
            for gap in analysis.missing_skills:
                if self.comparator.normalize_skill(gap.skill_name) in common:
                    if gap.skill_name not in common_skills:
                        common_skills.append(gap.skill_name)
        
        return common_skills[:10]  # Top 10
    
    def _identify_quick_wins(
        self, 
        role_analyses: List[RoleSkillAnalysis],
        job_postings: List[JobPosting]
    ) -> List[str]:
        """Identify quick win skills across all roles."""
        all_missing = []
        skill_frequency = Counter()
        
        for analysis in role_analyses:
            for gap in analysis.missing_skills:
                all_missing.append(gap.skill_name)
                skill_frequency[self.comparator.normalize_skill(gap.skill_name)] += gap.found_in_jobs_count
        
        quick_wins = self.comparator.identify_quick_wins(all_missing, skill_frequency)
        
        return list(set(quick_wins))[:8]  # Top 8 unique
    
    def _identify_long_term_goals(
        self, 
        role_analyses: List[RoleSkillAnalysis],
        job_postings: List[JobPosting]
    ) -> List[str]:
        """Identify long-term skill goals."""
        all_missing = []
        skill_frequency = Counter()
        
        for analysis in role_analyses:
            for gap in analysis.missing_skills:
                all_missing.append(gap.skill_name)
                skill_frequency[self.comparator.normalize_skill(gap.skill_name)] += gap.found_in_jobs_count
        
        long_term = self.comparator.identify_long_term_goals(all_missing, skill_frequency)
        
        return list(set(long_term))[:8]  # Top 8 unique
    
    def _identify_niche_skills(self, role_analyses: List[RoleSkillAnalysis]) -> List[str]:
        """Identify niche skills (required for specific roles, not all)."""
        if len(role_analyses) < 2:
            return []
        
        # Get missing skills from each role
        missing_by_role = [
            {self.comparator.normalize_skill(gap.skill_name): gap.skill_name 
             for gap in analysis.missing_skills}
            for analysis in role_analyses
        ]
        
        # Find skills that appear in only 1 role
        all_skills = {}
        skill_count = Counter()
        
        for missing_dict in missing_by_role:
            for norm_skill, original_skill in missing_dict.items():
                skill_count[norm_skill] += 1
                if norm_skill not in all_skills:
                    all_skills[norm_skill] = original_skill
        
        # Niche = appears in only 1 role
        niche = [
            all_skills[skill] 
            for skill, count in skill_count.items() 
            if count == 1
        ]
        
        return niche[:10]  # Top 10
    
    def _generate_action_plans(
        self, 
        common_gaps: List[str],
        quick_wins: List[str],
        long_term: List[str]
    ) -> tuple:
        """Generate time-based action plans."""
        
        # Immediate actions (next 2 weeks)
        immediate = []
        for skill in quick_wins[:3]:
            immediate.append(f"Start learning {skill} (quick win)")
        if common_gaps:
            immediate.append(f"Research {common_gaps[0]} fundamentals")
        immediate.append("Update resume with recent projects highlighting existing skills")
        
        # One month plan
        one_month = []
        for skill in quick_wins[3:6]:
            one_month.append(f"Complete {skill} tutorial/certification")
        if len(common_gaps) > 1:
            one_month.append(f"Begin structured course on {common_gaps[1]}")
        one_month.append("Build small project using newly learned skills")
        
        # Three month plan
        three_month = []
        for skill in common_gaps[:2]:
            three_month.append(f"Achieve proficiency in {skill}")
        if long_term:
            three_month.append(f"Start learning {long_term[0]} (long-term goal)")
        three_month.append("Contribute to open-source projects showcasing new skills")
        three_month.append("Apply to 2-3 stretch roles to gauge market response")
        
        # Six month plan
        six_month = []
        for skill in long_term[:2]:
            six_month.append(f"Develop intermediate skills in {skill}")
        six_month.append("Complete comprehensive portfolio project")
        six_month.append("Network with professionals in target roles")
        six_month.append("Apply to target positions with confidence")
        
        return immediate, one_month, three_month, six_month


logger.info("✅ SkillGapAnalyzer initialized")
