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
