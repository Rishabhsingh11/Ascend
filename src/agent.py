"""Main LangGraph agent for job search assistance with Ollama."""

import os
import sys
from pathlib import Path
# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from langgraph.graph import StateGraph, END
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
from typing import Dict, Any, List, Optional

from src.state import (
    AgentState, ParsedResume, JobRoleMatch, 
    ResumeSummary, JobPosting, SkillGapAnalysis
)
from src.resume_parser import ResumeTextExtractor
from src.google_drive_handler import GoogleDriveHandler
from src.config import get_settings
from src.logger import get_logger
from src.callbacks import StreamingCallbackHandler
from pydantic import BaseModel
from src.enhanced_resume_parser import EnhancedResumeParser
from src.document_store import DocumentStore
from src.utils import hash_file

# ===== NEW IMPORTS FOR PHASE 2 =====
from src.api.job_api_client import JobAPIClient
from src.skills.skill_extractor import SkillExtractor
from src.skills.skill_comparator import SkillComparator
from src.skills.skill_gap_analyzer import SkillGapAnalyzer
from src.csv_job_exporter import CSVJobExporter
from src.email_sender import EmailSender


def _handle_streaming_error(self, error: Exception, operation_name: str) -> Dict[str, Any]:
    """Centralized error handling for streaming operations.
    
    Args:
        error: Exception that occurred
        operation_name: Name of operation that failed
        
    Returns:
        Error state dictionary
    """
    error_msg = f"{operation_name} failed: {str(error)}"
    self.logger.error(error_msg)
    
    return {
        'error': error_msg,
        'current_step': f"{operation_name.lower().replace(' ', '_')}_failed",
        'messages': [HumanMessage(content=error_msg)]
    }


class JobSearchAgent:
    """AI Agent for job search assistance using LangGraph and Ollama."""
    
    def __init__(self, model_name: str = None):
        """Initialize the agent with Ollama.
        
        Args:
            model_name: Ollama model name (default: from config)
        """
        self.logger = get_logger()
        settings = get_settings()
        
        self.logger.info("Initializing Job Search Agent...")
        
        # Initialize streaming callback
        self.callback_handler = StreamingCallbackHandler()
        
        # Initialize Ollama LLM with streaming
        self.llm = ChatOllama(
            model=model_name or settings.ollama_model,
            base_url=settings.ollama_base_url,
            temperature=settings.temperature,
            streaming=True,  # Enable streaming
            callbacks=[self.callback_handler]
        )
        
        self.logger.info(f"✅ Initialized Ollama with model: {model_name or settings.ollama_model}")
        
        self.drive_handler = GoogleDriveHandler()
        self.text_extractor = ResumeTextExtractor()
        self.downloaded_files = []  # Track downloaded files for cleanup
        
        # ===== NEW: Initialize Phase 2 components =====
        self.job_api_client = None  # Lazy initialization
        self.skill_extractor = None
        self.skill_comparator = None
        self.skill_gap_analyzer = None
        
        self.workflow = self._build_graph()
        
        self.logger.info("✅ Agent initialization complete")
    
    def _initialize_phase2_components(self):
        """Lazy initialization of Phase 2 components (only when needed)."""
        if self.job_api_client is None:
            self.logger.info("🔧 Initializing Phase 2 components (Skill Gap Analysis)...")
            try:
                self.job_api_client = JobAPIClient()
                self.skill_extractor = SkillExtractor()
                self.skill_comparator = SkillComparator()
                self.skill_gap_analyzer = SkillGapAnalyzer(
                    self.skill_extractor, 
                    self.skill_comparator
                )
                # NEW: Initialize JobStore for Phase 3
                from src.jobs.job_store import JobStore
                self.job_store = JobStore()
                self.csv_exporter = CSVJobExporter()
                self.email_sender = EmailSender()
                self.logger.info("✅ Phase 2 and 3 components initialized")
            except Exception as e:
                self.logger.warning(f"⚠️  Phase 2/3 initialization failed: {e}")
                self.logger.warning("   Skill gap analysis will be skipped")
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow with skill gap analysis.
        
        Returns:
            Compiled state graph
        """
        self.logger.debug("Building LangGraph workflow...")
        workflow = StateGraph(AgentState)
        
        # ===== PHASE 1 NODES (EXISTING) =====
        workflow.add_node("download_resume", self._download_resume)
        workflow.add_node("parse_resume", self._parse_resume)
        workflow.add_node("analyze_job_roles", self._analyze_job_roles)
        workflow.add_node("generate_summary", self._generate_summary)
        
        # ===== PHASE 2 NODES (NEW) =====
        workflow.add_node("fetch_job_postings", self._fetch_job_postings)
        workflow.add_node("analyze_skill_gaps", self._analyze_skill_gaps)
        workflow.add_node("export_and_email", self._export_and_email_results)
        
        # ===== PHASE 1 EDGES (EXISTING) =====
        workflow.set_entry_point("download_resume")
        workflow.add_edge("download_resume", "parse_resume")
        workflow.add_edge("parse_resume", "analyze_job_roles")
        workflow.add_edge("analyze_job_roles", "generate_summary")
    
        
        # ===== PHASE 2 EDGES (NEW) =====
        workflow.add_edge("generate_summary", "fetch_job_postings")
        workflow.add_edge("fetch_job_postings", "analyze_skill_gaps")
        workflow.add_edge("analyze_skill_gaps", "export_and_email")
        workflow.add_edge("export_and_email", END)
        
        self.logger.debug("✅ LangGraph workflow built successfully (Phase 1 + Phase 2)")

        return workflow.compile()
    
    def _download_resume(self, state: AgentState) -> Dict[str, Any]:
        """Node: Download resume from Google Drive.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state dictionary
        """
        with self.logger.timer("Download Resume from Google Drive"):
            try:
                self.logger.info(f"📥 Downloading resume: {state['file_name']}")
                
                # Create temp directory in project root
                temp_dir = Path("temp_resumes")
                temp_dir.mkdir(exist_ok=True)
                
                # Save to temp directory instead of project root
                temp_file_path = temp_dir / state['file_name']
                
                file_content = self.drive_handler.download_file(
                    state["file_id"], 
                    str(temp_file_path)
                )
                
                # Track downloaded file for cleanup
                self.downloaded_files.append(str(temp_file_path))
                
                # Extract text
                self.logger.info("📄 Extracting text from resume...")
                raw_text = self.text_extractor.extract_text(str(temp_file_path))
                
                self.logger.info(f"✅ Extracted {len(raw_text)} characters, {len(raw_text.split())} words")
                
                return {
                    "raw_resume_text": raw_text,
                    "current_step": "download_complete",
                    "messages": [HumanMessage(content=f"Downloaded and extracted text from {state['file_name']}")],
                }
            except Exception as e:
                self.logger.error(f"Download/Extraction failed: {str(e)}")
                return {
                    "error": str(e),
                    "current_step": "download_failed"
                }
    
    def _parse_resume(self, state: AgentState) -> Dict[str, Any]:
        """Node: Parse resume into structured format using PDFPlumber.
    
        Args:
            state: Current agent state
        
        Returns:
            Updated state dictionary
        """
        with self.logger.timer("Parse Resume with PDFPlumber"):
            try:
                self.logger.info("🔍 Parsing resume with PDFPlumber (layout-aware)...")
                # Get the file name from state
                file_name = state.get('file_name')

                if not file_name:
                    raise ValueError("No file_name in state")
            
                temp_file_path = Path("temp_resumes") / file_name

                # Check if file exists
                if not temp_file_path.exists():
                    self.logger.error(f"File not found at: {temp_file_path}")
                    raise FileNotFoundError(f"Resume file not found: {temp_file_path}") 
                
                # Use enhanced parser instead of LLM
                parser = EnhancedResumeParser(
                    file_path=str(temp_file_path),
                    debug=True
                )
                parsed_resume = parser.parse()
                
                self.logger.info("✅ Resume parsed successfully")
                self.logger.debug(f"Parsed {len(parsed_resume.skills)} skills, "
                                f"{len(parsed_resume.experience)} experiences, "
                                f"{len(parsed_resume.education)} education entries")
                
                return {
                    "parsed_resume": parsed_resume,
                    "current_step": "parsing_complete",
                    "messages": [HumanMessage(content="Resume parsed successfully with PDFPlumber")],
                }
            except Exception as e:
                self.logger.error(f"Parsing failed: {str(e)}")
                return {
                    "error": f"Parsing error: {str(e)}",
                    "current_step": "parsing_failed"
                }
    
    def _analyze_job_roles(self, state: AgentState) -> Dict[str, Any]:
        """Node: Analyze and recommend job roles.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state dictionary
        """
        with self.logger.timer("Analyze Job Roles"):
            system_prompt = """You are an experienced career coach with deep knowledge of job markets and roles.

Based on the candidate's resume, identify the TOP 3 job roles they are best suited for.
For each role, provide:
1. Role title
2. Confidence score (0.0 to 1.0) - how well the candidate fits
3. Detailed reasoning for the recommendation
4. Key skills from their resume that match this role

Consider:
- Years of experience
- Technical skills
- Domain expertise
- Career progression
- Industry trends

Be realistic and specific in your recommendations."""
            
            resume_json = state['parsed_resume'].model_dump_json(indent=2)
            user_prompt = f"""Analyze this resume and recommend the top 3 job roles:

{resume_json}

Provide detailed analysis for each role."""
            
            # Create a list model for structured output
            class JobRoleMatches(BaseModel):
                matches: List[JobRoleMatch]
            
            structured_llm = self.llm.with_structured_output(JobRoleMatches)
            
            try:
                self.logger.info("🎯 Analyzing suitable job roles with Ollama...")
                self.logger.info("💭 LLM is evaluating career fit and generating recommendations...")
                
                result = structured_llm.invoke([
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_prompt)
                ])
                
                self.logger.info(f"✅ Generated {len(result.matches)} job role recommendations")
                for idx, match in enumerate(result.matches, 1):
                    self.logger.debug(f"  {idx}. {match.role_title} (confidence: {match.confidence_score:.2%})")
                
                return {
                    "job_role_matches": result.matches,
                    "current_step": "analysis_complete",
                    "messages": [HumanMessage(content="Job role analysis complete")],
                }
            except Exception as e:
                self.logger.error(f"Analysis failed: {str(e)}")
                return {
                    "error": f"Analysis error: {str(e)}",
                    "current_step": "analysis_failed"
                }
    
    def _generate_summary(self, state: AgentState) -> Dict[str, Any]:
        """Node: Generate resume summary and quality assessment.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state dictionary
        """
        with self.logger.timer("Generate Resume Summary"):
            system_prompt = """You are an expert resume reviewer and editor.

Provide a comprehensive summary and quality assessment:
1. Overall summary of the candidate's profile (2-3 sentences)
2. Total years of experience
3. Key strengths (top 3-5)
4. Grammatical and text correctness issues found
5. Improvement suggestions
6. Overall quality score (0-10)

Be constructive, specific, and actionable in your feedback."""
            
            resume_json = state['parsed_resume'].model_dump_json(indent=2)
            user_prompt = f"""Review this resume and provide a comprehensive summary and quality assessment:

{resume_json}

Raw Resume Text (for grammar checking):
{state['raw_resume_text'][:3000]}

Provide detailed feedback."""
            
            structured_llm = self.llm.with_structured_output(ResumeSummary)
            
            try:
                self.logger.info("📊 Generating resume summary and quality assessment with Ollama...")
                self.logger.info("💭 LLM is reviewing quality and generating improvement suggestions...")
                
                summary = structured_llm.invoke([
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_prompt)
                ])
                
                self.logger.info(f"✅ Summary generated (Quality Score: {summary.quality_score}/10)")
                self.logger.debug(f"Identified {len(summary.key_strengths)} strengths, {len(summary.grammatical_issues)} issues")
                
                return {
                    "resume_summary": summary,
                    "current_step": "complete",
                    "messages": [HumanMessage(content="Summary generation complete")],
                }
            except Exception as e:
                self.logger.error(f"Summary generation failed: {str(e)}")
                return {
                    "error": f"Summary error: {str(e)}",
                    "current_step": "summary_failed"
                }
    
    # ===== NEW PHASE 2 NODES =====
    
    def _fetch_job_postings(self, state: AgentState) -> Dict[str, Any]:
        """Node: Fetch job postings and save to database.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state dictionary with job postings and session_id
        """
        self.logger.log_section("PHASE 2: FETCHING JOB POSTINGS")
        
        with self.logger.timer("Fetch Job Postings"):
            try:
                # Check if skill gap analysis is enabled
                if not state.get('enable_skill_gap', True):
                    self.logger.info("⏭️  Skill gap analysis disabled, skipping job fetch")
                    return {
                        "job_postings": [],
                        "current_step": "job_fetch_skipped",
                        "messages": [HumanMessage(content="Skill gap analysis disabled")]
                    }
                
                # Ensure we have job roles
                if not state.get('job_role_matches'):
                    self.logger.warning("⚠️  No job roles available, skipping job fetch")
                    return {
                        "job_postings": [],
                        "current_step": "job_fetch_skipped",
                        "messages": [HumanMessage(content="No job roles to fetch postings for")]
                    }
                
                # Initialize Phase 2 & 3 components if needed
                self._initialize_phase2_components()
                
                if self.job_api_client is None:
                    self.logger.error("❌ Job API client not initialized")
                    return {
                        "job_postings": [],
                        "error": "Job API client initialization failed",
                        "current_step": "job_fetch_failed"
                    }
                
                # Get search parameters from config or state
                from src.config import get_settings
                settings = get_settings()
                
                posting_hours = state.get('posting_hours', settings.default_posting_hours)
                country = state.get('country', settings.default_country)
                employment_type = state.get('employment_type', settings.employment_type)
                max_results = state.get('max_results', settings.jobs_per_api_call)
                
                self.logger.info("🔍 Fetching job postings from multiple APIs...")
                self.logger.info(f"   Country: {country}")
                self.logger.info(f"   Posted within: {posting_hours} hours")
                self.logger.info(f"   Employment type: {employment_type}")
                self.logger.info(f"   Max results per role: {max_results}")
                
                all_jobs = []
                
                # Fetch jobs for each of the top 3 roles
                for idx, job_role in enumerate(state['job_role_matches'][:3], 1):
                    self.logger.info(f"📋 [{idx}/3] Fetching jobs for: {job_role.role_title}")
                    
                    try:
                        jobs = self.job_api_client.search_jobs(
                            job_title=job_role.role_title,
                            country=country,
                            posting_hours=posting_hours,
                            employment_type=employment_type,
                            max_results=max_results
                        )
                        all_jobs.extend(jobs)
                        self.logger.info(f"    ✅ Found {len(jobs)} jobs")
                    except Exception as e:
                        self.logger.warning(f"    ⚠️  Failed to fetch jobs: {e}")
                        continue
                
                self.logger.info(f"\n✅ Total jobs fetched: {len(all_jobs)}")
                self.logger.info(f"   Sources: Adzuna, JSearch, Jooble")
                
                # ===== NEW: Save jobs to database =====
                session_id = None
                
                if all_jobs and self.job_store:
                    try:
                        self.logger.info("💾 Saving jobs to database...")
                        
                        # Extract candidate info from parsed resume
                        parsed_resume = state.get('parsed_resume')
                        contact = parsed_resume.contact_info if parsed_resume else None
                        
                        # Get or compute resume hash
                        from src.utils import hash_file
                        resume_hash = state.get('resume_hash')
                        
                        # If no hash in state, compute from file
                        if not resume_hash and state.get('file_path'):
                            resume_hash = hash_file(state['file_path'])
                        elif not resume_hash:
                            # Fallback: use file_id or generate temporary hash
                            import hashlib
                            resume_hash = hashlib.md5(
                                (state.get('file_name', 'unknown') + 
                                state.get('file_id', 'unknown')).encode()
                            ).hexdigest()
                        
                        # Create job search session
                        session_id = self.job_store.create_session(
                            resume_hash=resume_hash,
                            resume_filename=state.get('file_name', 'unknown'),
                            candidate_name=contact.name if contact else None,
                            candidate_email=contact.email if contact else None,
                            job_roles=[r.role_title for r in state['job_role_matches'][:3]],
                            market_readiness=None  # Will update after skill gap analysis
                        )
                        
                        self.logger.info(f"   Created session: {session_id}")
                        
                        # Save all jobs in batch
                        saved_count = self.job_store.save_jobs_batch(
                            session_id=session_id,
                            jobs=all_jobs,
                            job_roles=[r.role_title for r in state['job_role_matches'][:3]]
                        )
                        
                        self.logger.info(f"   💾 Saved {saved_count} jobs to database")
                        
                    except Exception as e:
                        self.logger.error(f"❌ Failed to save jobs to database: {e}")
                        # Don't fail the entire process if DB save fails
                        session_id = None
                
                return {
                    "job_postings": all_jobs,
                    "job_session_id": session_id,  # NEW: Track session ID
                    "posting_hours": posting_hours,
                    "current_step": "job_fetch_complete",
                    "messages": [HumanMessage(content=f"Fetched {len(all_jobs)} job postings")]
                }
                
            except Exception as e:
                self.logger.error(f"❌ Job fetching failed: {str(e)}")
                return {
                    "job_postings": [],
                    "error": f"Job fetch error: {str(e)}",
                    "current_step": "job_fetch_failed"
                }

    
    def _analyze_skill_gaps(self, state: AgentState) -> Dict[str, Any]:
        """Node: Analyze skill gaps and update database with market readiness.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state dictionary with skill gap analysis
        """
        self.logger.log_section("PHASE 2: ANALYZING SKILL GAPS")
        
        with self.logger.timer("Skill Gap Analysis"):
            try:
                # Skip if disabled or no data
                if not state.get('enable_skill_gap', True):
                    self.logger.info("⏭️  Skill gap analysis disabled")
                    return {
                        "skill_gap_analysis": None,
                        "current_step": "skill_gap_skipped"
                    }
                
                if not state.get('job_postings'):
                    self.logger.warning("⚠️  No job postings available for skill gap analysis")
                    return {
                        "skill_gap_analysis": None,
                        "current_step": "skill_gap_skipped",
                        "messages": [HumanMessage(content="No job postings to analyze")]
                    }
                
                # Initialize Phase 2 components if needed
                self._initialize_phase2_components()
                
                if self.skill_gap_analyzer is None:
                    self.logger.error("❌ Skill gap analyzer not initialized")
                    return {
                        "skill_gap_analysis": None,
                        "error": "Skill gap analyzer initialization failed",
                        "current_step": "skill_gap_failed"
                    }
                
                # Extract resume skills
                resume_skills = state['parsed_resume'].skills if state.get('parsed_resume') else []
                job_roles = [match.role_title for match in state['job_role_matches'][:3]]
                
                self.logger.info(f"📊 Analyzing skill gaps...")
                self.logger.info(f"   Resume skills: {len(resume_skills)}")
                self.logger.info(f"   Job postings: {len(state['job_postings'])}")
                self.logger.info(f"   Roles: {', '.join(job_roles)}")
                
                # Perform skill gap analysis
                skill_gap = self.skill_gap_analyzer.analyze(
                    resume_skills=resume_skills,
                    job_postings=state['job_postings'],
                    job_roles=job_roles
                )
                
                self.logger.info(f"\n✅ Skill gap analysis complete!")
                self.logger.info(f"   Common gaps across roles: {len(skill_gap.common_gaps)}")
                self.logger.info(f"   Quick win skills: {len(skill_gap.quick_wins)}")
                self.logger.info(f"   Long-term goals: {len(skill_gap.long_term_goals)}")
                self.logger.info(f"   Overall market readiness: {skill_gap.overall_market_readiness:.1f}%")
                
                # ===== NEW: Update database with market readiness =====
                if skill_gap and self.job_store and state.get('job_session_id'):
                    try:
                        session_id = state['job_session_id']
                        
                        self.logger.info("💾 Updating database with market readiness...")
                        
                        self.job_store.update_session_market_readiness(
                            session_id=session_id,
                            market_readiness=skill_gap.overall_market_readiness
                        )
                        
                        self.logger.info(f"   ✅ Database updated: {skill_gap.overall_market_readiness:.1f}% readiness")
                        
                    except Exception as e:
                        self.logger.warning(f"⚠️  Failed to update database: {e}")
                        # Don't fail the process if DB update fails
                
                return {
                    "skill_gap_analysis": skill_gap,
                    'job_session_id': state.get('job_session_id'),
                    "current_step": "complete",
                    "messages": [HumanMessage(content="Skill gap analysis complete")]
                }
                
            except Exception as e:
                self.logger.error(f"❌ Skill gap analysis failed: {str(e)}")
                import traceback
                self.logger.error(traceback.format_exc())
                return {
                    "skill_gap_analysis": None,
                    "error": f"Skill gap analysis error: {str(e)}",
                    "current_step": "skill_gap_failed"
                }

    
    # ===== STREAMING VARIANTS (EXISTING - KEEP AS-IS) =====
    
    def _analyze_job_roles_streaming(self, state: AgentState, token_callback=None) -> dict[str, any]:
        """Node: Analyze and recommend job roles WITH STREAMING.
        
        This is a hybrid approach:
        1. Stream raw tokens to UI via callback
        2. Parse complete response into structured Pydantic objects
        
        Args:
            state: Current agent state
            token_callback: Optional function(token: str) to handle each token
            
        Returns:
            Updated state dictionary with structured job role matches
        """
        with self.logger.timer("Analyze Job Roles (Streaming)"):
            system_prompt = """You are an experienced career coach with deep knowledge of job markets and roles.

Based on the candidate's resume, identify the TOP 3 job roles they are best suited for.
For each role, provide:
1. Role title
2. Confidence score (0.0 to 1.0) - how well the candidate fits
3. Detailed reasoning for the recommendation
4. Key skills from their resume that match this role

Consider:
- Years of experience
- Technical skills
- Domain expertise
- Career progression
- Industry trends

IMPORTANT: Format your response as a valid JSON array of objects with these exact fields:
- role_title (string)
- confidence_score (number between 0.0 and 1.0)
- reasoning (string)
- key_matching_skills (array of strings)

Example format:
[
{
    "role_title": "Senior Data Engineer",
    "confidence_score": 0.92,
    "reasoning": "Strong experience in...",
    "key_matching_skills": ["Python", "SQL", "AWS"]
}
]

Be realistic and specific in your recommendations."""
            
            resume_json = state['parsed_resume'].model_dump_json(indent=2)
            user_prompt = f"""Analyze this resume and recommend the top 3 job roles:

{resume_json}

Provide detailed analysis for each role in JSON format."""
            
            try:
                self.logger.info("🎯 Analyzing suitable job roles with streaming...")
                
                # Create callback handler for streaming
                streaming_callback = StreamingCallbackHandler(on_token_callback=token_callback)
                
                # Create LLM WITHOUT structured output for streaming
                streaming_llm = ChatOllama(
                    model=self.llm.model,
                    base_url=self.llm.base_url,
                    temperature=self.llm.temperature,
                    streaming=True,
                    callbacks=[streaming_callback],
                    format='json'
                )
                
                # Stream the response
                response = streaming_llm.invoke([
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_prompt)
                ])
                
                # Get the complete streamed text
                complete_text = streaming_callback.get_accumulated_text()
                
                self.logger.debug(f"Raw LLM response: {complete_text[:500]}...")
                
                # Parse the JSON response into Pydantic objects
                import json
                import re
                
                # Extract JSON from response
                json_match = re.search(r'\[.*\]', complete_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    json_str = complete_text
                
                # Parse JSON
                matches_data = json.loads(json_str)
                
                # Validate and convert to Pydantic models
                job_matches = []
                for match_dict in matches_data[:3]:
                    try:
                        job_match = JobRoleMatch(
                            role_title=match_dict.get('role_title', ''),
                            confidence_score=float(match_dict.get('confidence_score', 0.0)),
                            reasoning=match_dict.get('reasoning', ''),
                            key_matching_skills=match_dict.get('key_matching_skills', [])
                        )
                        job_matches.append(job_match)
                    except Exception as e:
                        self.logger.warning(f"Failed to parse job match: {e}")
                        continue
                
                self.logger.info(f"✅ Generated {len(job_matches)} job role recommendations")
                for idx, match in enumerate(job_matches, 1):
                    self.logger.debug(f"  {idx}. {match.role_title} (confidence: {match.confidence_score:.2%})")
                
                return {
                    "job_role_matches": job_matches,
                    "current_step": "analysis_complete",
                    "messages": [HumanMessage(content="Job role analysis complete with streaming")],
                }
                
            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse JSON response: {e}")
                self.logger.error(f"Raw response: {complete_text}")
                return {
                    "error": f"JSON parsing error: {str(e)}",
                    "current_step": "analysis_failed"
                }
            except Exception as e:
                self.logger.error(f"Analysis failed: {str(e)}")
                return {
                    "error": f"Analysis error: {str(e)}",
                    "current_step": "analysis_failed"
                }

    def _generate_summary_streaming(self, state: AgentState, token_callback=None) -> dict[str, any]:
        """Node: Generate resume summary and quality assessment WITH STREAMING.
        
        Args:
            state: Current agent state
            token_callback: Optional function(token: str) to handle each token
            
        Returns:
            Updated state dictionary with structured summary
        """
        with self.logger.timer("Generate Resume Summary (Streaming)"):
            system_prompt = """You are an expert resume reviewer and editor.

Provide a comprehensive summary and quality assessment in JSON format with these exact fields:
- overall_summary (string): 2-3 sentence summary of candidate's profile
- years_of_experience (integer): Total years of professional experience
- key_strengths (array of strings): Top 3-5 strengths
- grammatical_issues (array of strings): Grammar and formatting issues found
- improvement_suggestions (array of strings): Specific actionable suggestions
- quality_score (number): Overall score from 0 to 10

Example format:
{
"overall_summary": "Experienced data professional with...",
"years_of_experience": 5,
"key_strengths": ["Strong technical skills", "Leadership experience"],
"grammatical_issues": ["Inconsistent tense in bullets"],
"improvement_suggestions": ["Add metrics to achievements"],
"quality_score": 7.5
}

Be constructive, specific, and actionable in your feedback."""
            
            resume_json = state['parsed_resume'].model_dump_json(indent=2)
            raw_text_preview = state.get('raw_resume_text', '')[:3000]
            
            user_prompt = f"""Review this resume and provide a comprehensive summary and quality assessment:

{resume_json}

Raw Resume Text (for grammar checking):
{raw_text_preview}

Provide detailed feedback in JSON format."""
            
            try:
                self.logger.info("📊 Generating resume summary with streaming...")
                
                # Create callback handler for streaming
                streaming_callback = StreamingCallbackHandler(on_token_callback=token_callback)
                
                # Create LLM WITHOUT structured output for streaming
                streaming_llm = ChatOllama(
                    model=self.llm.model,
                    base_url=self.llm.base_url,
                    temperature=self.llm.temperature,
                    streaming=True,
                    callbacks=[streaming_callback],
                    format='json'
                )
                
                # Stream the response
                response = streaming_llm.invoke([
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_prompt)
                ])
                
                # Get the complete streamed text
                complete_text = streaming_callback.get_accumulated_text()
                
                self.logger.debug(f"Raw LLM response: {complete_text[:500]}...")
                
                # Parse the JSON response into Pydantic object
                import json
                import re
                
                # Extract JSON from response
                json_match = re.search(r'\{.*\}', complete_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    json_str = complete_text
                
                # Parse JSON
                summary_data = json.loads(json_str)
                
                # Validate and convert to Pydantic model
                summary = ResumeSummary(
                    overall_summary=summary_data.get('overall_summary', ''),
                    years_of_experience=summary_data.get('years_of_experience'),
                    key_strengths=summary_data.get('key_strengths', []),
                    grammatical_issues=summary_data.get('grammatical_issues', []),
                    improvement_suggestions=summary_data.get('improvement_suggestions', []),
                    quality_score=float(summary_data.get('quality_score', 0.0))
                )
                
                self.logger.info(f"✅ Summary generated (Quality Score: {summary.quality_score}/10)")
                self.logger.debug(f"Identified {len(summary.key_strengths)} strengths, {len(summary.grammatical_issues)} issues")
                
                return {
                    "resume_summary": summary,
                    "current_step": "complete",
                    "messages": [HumanMessage(content="Summary generation complete with streaming")],
                }
                
            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse JSON response: {e}")
                self.logger.error(f"Raw response: {complete_text}")
                return {
                    "error": f"JSON parsing error: {str(e)}",
                    "current_step": "summary_failed"
                }
            except Exception as e:
                self.logger.error(f"Summary generation failed: {str(e)}")
                return {
                    "error": f"Summary error: {str(e)}",
                    "current_step": "summary_failed"
                }
    
    # ===== CLEANUP & PROCESS METHODS =====
    
    def cleanup_downloaded_files(self):
        """Delete all downloaded resume files."""
        self.logger.info("🗑️  Cleaning up downloaded files...")
        
        for filename in self.downloaded_files:
            try:
                if os.path.exists(filename):
                    os.remove(filename)
                    self.logger.info(f"✅ Deleted: {filename}")
                else:
                    self.logger.warning(f"File not found for cleanup: {filename}")
            except Exception as e:
                self.logger.error(f"Failed to delete {filename}: {str(e)}")
        
        self.downloaded_files.clear()
        self.logger.info("✅ Cleanup complete")
    
    def process_resume(self, file_id: str, file_name: str, enable_skill_gap: bool = True) -> Dict[str, Any]:
        """Process a resume through the entire pipeline with caching.
        
        Args:
            file_id: Google Drive file ID
            file_name: Name of the resume file
            enable_skill_gap: Whether to enable Phase 2 skill gap analysis (default: True)
            
        Returns:
            Final agent state with all results
        """
        self.logger.log_section("STARTING RESUME PROCESSING PIPELINE")
        
        with self.logger.timer("Total Resume Processing"):
            # Initialize document store
            doc_store = DocumentStore()
            
            try:
                # Step 1: Download the resume
                self.logger.info(f"📥 Downloading resume: {file_name}")
                
                temp_dir = Path("temp_resumes")
                temp_dir.mkdir(exist_ok=True)
                temp_file_path = temp_dir / file_name
                
                file_content = self.drive_handler.download_file(file_id, str(temp_file_path))
                self.downloaded_files.append(str(temp_file_path))
                
                # Step 2: Compute hash
                with self.logger.timer("Compute Resume Hash"):
                    resume_hash = hash_file(str(temp_file_path))
                    self.logger.info(f"🔑 Resume hash: {resume_hash[:16]}...")
                
                # Step 3: Check cache
                cached_data = doc_store.get_cached_resume(resume_hash)
                
                if cached_data:
                    self.logger.log_section("📦 USING CACHED RESULTS")
                    self.logger.info(f"✅ Found cached analysis for this resume")
                    self.logger.info(f"   Originally processed: {cached_data['created_at']}")
                    self.logger.info(f"   Skipping Phase 1 analysis")
                    
                    # Reconstruct state from cache
                    final_state = {
                        "messages": [HumanMessage(content=f"Loaded cached analysis for {file_name}")],
                        "file_id": file_id,
                        "file_name": file_name,
                        "raw_resume_text": "",
                        "parsed_resume": ParsedResume.model_validate(cached_data['parsed_data']) if cached_data['parsed_data'] else None,
                        "job_role_matches": [JobRoleMatch.model_validate(match) for match in cached_data['job_roles']] if cached_data['job_roles'] else None,
                        "resume_summary": ResumeSummary.model_validate(cached_data['summary']) if cached_data['summary'] else None,
                        "current_step": "complete",
                        "error": None,
                        "job_postings": [],
                        "skill_gap_analysis": None,
                        "enable_skill_gap": enable_skill_gap,
                        "cache_hit": True
                    }
                    
                    # If skill gap is enabled, run Phase 2 even with cached Phase 1
                    if enable_skill_gap:
                        self.logger.info("🔄 Running Phase 2 on cached results...")
                        
                        # Run Phase 2 nodes
                        job_state = self._fetch_job_postings(final_state)
                        final_state.update(job_state)

                        # ✅ DEBUG: Check what we got
                        self.logger.debug(f"After job fetch - job_session_id: {final_state.get('job_session_id')}")
                        self.logger.debug(f"After job fetch - job_postings count: {len(final_state.get('job_postings', []))}")
                        
                        if final_state.get('job_postings'):
                            skill_state = self._analyze_skill_gaps(final_state)
                            final_state.update(skill_state)
                            # ✅ DEBUG: Check if still there
                            self.logger.debug(f"After skill analysis - job_session_id: {final_state.get('job_session_id')}")
                            self.logger.debug(f"After skill analysis - skill_gap exists: {bool(final_state.get('skill_gap_analysis'))}")

                            # ✅ NEW: Run Phase 3 - Export & Email
                            if final_state.get('skill_gap_analysis'):
                                self.logger.info("📧 Running Phase 3: Export & Email...")
                                # ✅ DEBUG: Check before export
                                self.logger.debug(f"Before export - job_session_id: {final_state.get('job_session_id')}")
                                self.logger.debug(f"Before export - email: {final_state['parsed_resume'].contact_info.email if final_state.get('parsed_resume') else 'None'}")
                                # Make sure we have job_session_id from skill gap analysis
                                if not final_state.get('job_session_id') and skill_state.get('job_session_id'):
                                    final_state['job_session_id'] = skill_state['job_session_id']
                                export_state = self._export_and_email_results(final_state)
                                final_state.update(export_state)
                                # ✅ DEBUG: Check result
                                self.logger.debug(f"After export - email_sent: {export_state.get('email_sent')}")
                                self.logger.debug(f"After export - csv_path: {export_state.get('csv_path')}")
                    
                    # Cleanup and close
                    self.cleanup_downloaded_files()
                    doc_store.close()
                    
                    return final_state
                
                # Step 4: No cache - run full pipeline
                self.logger.log_section("🔄 PROCESSING NEW RESUME")
                
                # Extract text
                self.logger.info("📄 Extracting text from resume...")
                raw_text = self.text_extractor.extract_text(str(temp_file_path))
                self.logger.info(f"✅ Extracted {len(raw_text)} characters")
                
                # Build initial state
                initial_state = {
                    "messages": [HumanMessage(content=f"Processing {file_name}")],
                    "file_id": file_id,
                    "file_name": file_name,
                    "raw_resume_text": raw_text,
                    "parsed_resume": None,
                    "job_role_matches": None,
                    "resume_summary": None,
                    "current_step": "download_complete",
                    "error": None,
                    "job_postings": [],
                    "skill_gap_analysis": None,
                    "enable_skill_gap": enable_skill_gap,
                    "cache_hit": False
                }
                
                # Run the full workflow
                final_state = self.workflow.invoke(initial_state)
                
                # Step 5: Save Phase 1 results to cache
                if final_state.get('parsed_resume') and final_state.get('current_step') == 'complete':
                    self.logger.info("💾 Saving Phase 1 results to cache...")
                    
                    doc_store.save_cached_resume(
                        resume_hash=resume_hash,
                        file_name=file_name,
                        parsed_data=final_state['parsed_resume'].model_dump(),
                        job_roles=[match.model_dump() for match in final_state['job_role_matches']] if final_state.get('job_role_matches') else None,
                        summary=final_state['resume_summary'].model_dump() if final_state.get('resume_summary') else None
                    )
                    
                    self.logger.info("✅ Phase 1 results cached")
                
                # Cleanup
                self.cleanup_downloaded_files()
                doc_store.close()
                
                return final_state
                
            except Exception as e:
                self.logger.error(f"❌ Pipeline execution failed: {str(e)}")
                self.cleanup_downloaded_files()
                doc_store.close()
                raise

    def _export_and_email_results(self, state: AgentState) -> Dict[str, Any]:
        """Node: Export job recommendations to CSV and email to candidate."""
        
        self.logger.log_section("PHASE 3: EXPORTING & EMAILING RESULTS")
        
        with self.logger.timer("Export and Email"):
            try:
                # Skip if no jobs or email disabled
                if not state.get('enable_skill_gap', True) or not state.get('job_postings'):
                    self.logger.info("⏭️  Export skipped (no jobs found)")
                    return {"current_step": "export_skipped"}
                
                # Get candidate info
                parsed_resume = state.get('parsed_resume')
                contact = parsed_resume.contact_info if parsed_resume else None
                
                if not contact or not contact.email:
                    self.logger.warning("⚠️  No candidate email found, skipping email delivery")
                    return {"current_step": "export_skipped"}
                
                candidate_name = contact.name or "Candidate"
                # ✅ CLEAN EMAIL - Extract only email part if pipe-separated
                raw_email = contact.email
                candidate_email = self._extract_clean_email(raw_email)

                if not candidate_email:
                    self.logger.warning(f"⚠️  Invalid email format: {raw_email}")
                    return {"current_step": "export_skipped"}
                
                # Get job info
                jobs = state['job_postings']
                job_roles = [r.role_title for r in state.get('job_role_matches', [])[:3]]
                market_readiness = state.get('skill_gap_analysis')
                market_readiness_score = market_readiness.overall_market_readiness if market_readiness else None
                
                self.logger.info(f"📊 Exporting {len(jobs)} jobs for {candidate_name}")
                
                # Create CSV
                csv_path, _ = self.csv_exporter.create_job_recommendations_csv(
                    jobs=jobs,
                    candidate_name=candidate_name,
                    job_roles=job_roles,
                    market_readiness=market_readiness_score,
                    upload_to_drive=False
                )
                
                self.logger.info(f"✅ CSV created: {csv_path}")
                
                # Send email
                self.logger.info(f"📧 Sending email to {candidate_email}...")
                
                email_success = self.email_sender.send_job_recommendations(
                    recipient_email=candidate_email,
                    candidate_name=candidate_name,
                    csv_path=csv_path,
                    job_count=len(jobs),
                    market_readiness=market_readiness_score
                )
                
                if email_success:
                    self.logger.info(f"✅ Email sent successfully to {candidate_email}")
                    
                    # Update database with export info
                    if self.job_store and state.get('job_session_id'):
                        try:
                            # You can add a method to track email sent
                            session_id = state['job_session_id']
                            # self.job_store.mark_email_sent(session_id, csv_path)
                            pass
                        except Exception as e:
                            self.logger.warning(f"Failed to update email status in DB: {e}")
                    
                    return {
                        "csv_path": csv_path,
                        "email_sent": True,
                        "current_step": "complete"
                    }
                else:
                    self.logger.error("❌ Failed to send email")
                    return {
                        "csv_path": csv_path,
                        "email_sent": False,
                        "current_step": "email_failed"
                    }
            
            except Exception as e:
                self.logger.error(f"❌ Export/email failed: {str(e)}")
                import traceback
                self.logger.error(traceback.format_exc())
                return {
                    "error": f"Export error: {str(e)}",
                    "current_step": "export_failed"
                }

    def _extract_clean_email(self, email_string: str) -> Optional[str]:
        """
        Extract clean email address from potentially pipe-separated string.
        
        Args:
            email_string: Email string that might contain "email|LinkedIn|Portfolio"
            
        Returns:
            Clean email address or None if invalid
        """
        import re
        
        if not email_string:
            return None
        
        # If pipe-separated, split and find the email part
        if '|' in email_string:
            parts = email_string.split('|')
            for part in parts:
                part = part.strip()
                if '@' in part and '.' in part:
                    # Basic email validation
                    if re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', part):
                        return part.lower()
        else:
            # Single email, validate it
            email_string = email_string.strip()
            if re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email_string):
                return email_string.lower()
        
        return None