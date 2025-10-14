"""State definitions for the LangGraph agent."""

from typing import TypedDict, List, Optional, Annotated
from pydantic import BaseModel, Field
from langgraph.graph.message import add_messages


class ContactInfo(BaseModel):
    """Contact information from resume."""
    name: Optional[str] = Field(None, description="Full name of the candidate")
    email: Optional[str] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    linkedin: Optional[str] = Field(None, description="LinkedIn profile URL")
    location: Optional[str] = Field(None, description="Current location")


class Experience(BaseModel):
    """Work experience entry."""
    company: str = Field(..., description="Company name")
    position: str = Field(..., description="Job position/title")
    duration: str = Field(..., description="Duration of employment")
    location: str = Field(..., description="Job Location")
    description: List[str] = Field(
        default_factory=list, 
        description="Job responsibilities and achievements"
    )


class Education(BaseModel):
    """Education entry."""
    institution: str = Field(..., description="Educational institution name")
    degree: str = Field(..., description="Degree earned")
    field: Optional[str] = Field(None, description="Field of study")
    graduation_year: Optional[str] = Field(None, description="Graduation year")


class JobRoleMatch(BaseModel):
    """Job role recommendation with confidence score."""
    role_title: str = Field(..., description="Recommended job role title")
    confidence_score: float = Field(
        ..., 
        ge=0.0, 
        le=1.0, 
        description="Confidence score between 0 and 1"
    )
    reasoning: str = Field(..., description="Explanation for the recommendation")
    key_matching_skills: List[str] = Field(
        default_factory=list,
        description="Skills that match this role"
    )


class ResumeSummary(BaseModel):
    """Summary and quality assessment of resume."""
    overall_summary: str = Field(..., description="Brief summary of candidate profile")
    years_of_experience: Optional[int] = Field(None, description="Total years of experience")
    key_strengths: List[str] = Field(
        default_factory=list, 
        description="Key strengths identified"
    )
    grammatical_issues: List[str] = Field(
        default_factory=list,
        description="Grammar and text issues found"
    )
    improvement_suggestions: List[str] = Field(
        default_factory=list,
        description="Suggestions for improvement"
    )
    quality_score: float = Field(
        ..., 
        ge=0.0, 
        le=10.0,
        description="Overall resume quality score out of 10"
    )


class ParsedResume(BaseModel):
    """Complete structured resume data."""
    contact_info: ContactInfo
    summary: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    experience: List[Experience] = Field(default_factory=list)
    education: List[Education] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    projects: List[str] = Field(default_factory=list)


# ===== NEW MODELS FOR PHASE 2: SKILL GAP ANALYSIS =====

class JobPosting(BaseModel):
    """Individual job posting from job search APIs."""
    title: str = Field(..., description="Job title")
    company: str = Field(..., description="Company name")
    location: str = Field(..., description="Job location")
    description: str = Field(..., description="Full job description")
    required_skills: List[str] = Field(
        default_factory=list,
        description="Skills extracted from job description"
    )
    url: Optional[str] = Field(None, description="Link to apply")
    salary: Optional[str] = Field(None, description="Salary range if available")
    posted_date: Optional[str] = Field(None, description="Date job was posted")
    source: str = Field(..., description="API source (adzuna, jsearch, jooble)")


class SkillCategory(BaseModel):
    """Categorization of a skill."""
    name: str = Field(..., description="Skill name")
    category: str = Field(
        ..., 
        description="Category: technical, soft, tool, language, framework, database, cloud"
    )
    importance: str = Field(
        ..., 
        description="Importance level: required, preferred, nice-to-have"
    )
    frequency: int = Field(
        default=0,
        description="Number of job postings mentioning this skill"
    )


class SkillGap(BaseModel):
    """Individual skill gap identified."""
    skill_name: str = Field(..., description="Name of the missing skill")
    category: str = Field(..., description="Skill category")
    found_in_jobs_count: int = Field(
        ..., 
        description="Number of jobs requiring this skill"
    )
    priority: str = Field(
        ..., 
        description="Learning priority: high, medium, low"
    )
    learning_resources: List[str] = Field(
        default_factory=list,
        description="Suggested learning resources (URLs, courses)"
    )
    estimated_learning_time: Optional[str] = Field(
        None,
        description="Estimated time to learn (e.g., '2-3 weeks', '1-2 months')"
    )


class RoleSkillAnalysis(BaseModel):
    """Skill gap analysis for a single job role."""
    job_role: str = Field(..., description="Job role being analyzed")
    jobs_analyzed: int = Field(..., description="Number of job postings analyzed")
    
    # Skills breakdown
    matched_skills: List[str] = Field(
        default_factory=list,
        description="Skills from resume that match job requirements"
    )
    missing_skills: List[SkillGap] = Field(
        default_factory=list,
        description="Skills missing from resume but required by jobs"
    )
    emerging_skills: List[str] = Field(
        default_factory=list,
        description="Trending/emerging skills in this role"
    )
    
    # Metrics
    match_percentage: float = Field(
        ..., 
        ge=0.0, 
        le=100.0,
        description="Percentage of required skills present in resume"
    )
    skill_coverage_score: float = Field(
        ..., 
        ge=0.0, 
        le=10.0,
        description="Overall skill coverage score (0-10)"
    )
    
    # Recommendations
    top_skills_to_learn: List[str] = Field(
        default_factory=list,
        description="Top 5 skills to prioritize learning"
    )
    estimated_readiness: str = Field(
        ...,
        description="Estimated readiness for this role (e.g., 'Ready now', '2-3 months', '6+ months')"
    )


class SkillGapAnalysis(BaseModel):
    """Complete skill gap analysis across all recommended job roles."""
    
    # Per-role analysis
    role_analyses: List[RoleSkillAnalysis] = Field(
        default_factory=list,
        description="Skill analysis for each of the top 3 job roles"
    )
    
    # Cross-role insights
    common_gaps: List[str] = Field(
        default_factory=list,
        description="Skills missing across ALL recommended roles (highest priority)"
    )
    quick_wins: List[str] = Field(
        default_factory=list,
        description="Easy-to-learn skills that appear frequently (fast ROI)"
    )
    long_term_goals: List[str] = Field(
        default_factory=list,
        description="Complex skills requiring significant time investment"
    )
    niche_skills: List[str] = Field(
        default_factory=list,
        description="Specialized skills for specific roles"
    )
    
    # Market insights
    trending_skills: List[str] = Field(
        default_factory=list,
        description="Skills gaining popularity in the job market"
    )
    declining_skills: List[str] = Field(
        default_factory=list,
        description="Skills becoming less relevant"
    )
    
    # Action plans
    immediate_actions: List[str] = Field(
        default_factory=list,
        description="Actions to take in the next 2 weeks"
    )
    one_month_plan: List[str] = Field(
        default_factory=list,
        description="Skills to focus on in the next month"
    )
    three_month_plan: List[str] = Field(
        default_factory=list,
        description="Skills to develop over 3 months"
    )
    six_month_plan: List[str] = Field(
        default_factory=list,
        description="Long-term skill development goals (6 months)"
    )
    
    # Overall metrics
    overall_market_readiness: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Overall readiness for job market (percentage)"
    )
    total_jobs_analyzed: int = Field(
        ...,
        description="Total number of job postings analyzed"
    )
    analysis_date: str = Field(
        ...,
        description="Date when analysis was performed"
    )


class AgentState(TypedDict):
    """State for the LangGraph agent."""
    messages: Annotated[list, add_messages]
    file_id: str
    file_name: str
    raw_resume_text: str
    parsed_resume: Optional[ParsedResume]
    job_role_matches: Optional[List[JobRoleMatch]]
    resume_summary: Optional[ResumeSummary]
    current_step: str
    error: Optional[str]
    job_postings: List[JobPosting]  # Jobs fetched from APIs
    skill_gap_analysis: Optional[SkillGapAnalysis]  # Complete skill gap analysis
    enable_skill_gap: bool  # Toggle to enable/disable skill gap feature
    # Additional metadata
    cache_hit: Optional[bool]  # Whether results came from cache
    processing_time: Optional[float]  # Total processing time in seconds