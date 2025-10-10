"""Main LangGraph agent for job search assistance with Ollama."""

import os
from langgraph.graph import StateGraph, END
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
from typing import Dict, Any, List

from src.state import (
    AgentState, ParsedResume, JobRoleMatch, 
    ResumeSummary
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
        
        self.drive_handler = GoogleDriveHandler(settings.google_credentials_path)
        self.text_extractor = ResumeTextExtractor()
        self.downloaded_files = []  # Track downloaded files for cleanup
        
        self.workflow = self._build_graph()
        
        self.logger.info("✅ Agent initialization complete")
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow.
        
        Returns:
            Compiled state graph
        """
        self.logger.debug("Building LangGraph workflow...")
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("download_resume", self._download_resume)
        workflow.add_node("parse_resume", self._parse_resume)
        workflow.add_node("analyze_job_roles", self._analyze_job_roles)
        workflow.add_node("generate_summary", self._generate_summary)
        
        # Define edges
        workflow.set_entry_point("download_resume")
        workflow.add_edge("download_resume", "parse_resume")
        workflow.add_edge("parse_resume", "analyze_job_roles")
        workflow.add_edge("analyze_job_roles", "generate_summary")
        workflow.add_edge("generate_summary", END)
        
        self.logger.debug("✅ LangGraph workflow built successfully")
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
                    str(temp_file_path)  # Use temp directory path
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
                
                # Use enhanced parser instead of LLM
                parser = EnhancedResumeParser(
                    file_path=state['file_name'],
                    debug=True  # Set to True for troubleshooting
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
    
    def process_resume(self, file_id: str, file_name: str) -> Dict[str, Any]:
        """Process a resume through the entire pipeline with caching.
        
        Args:
            file_id: Google Drive file ID
            file_name: Name of the resume file
            
        Returns:
            Final agent state with all results
        """
        self.logger.log_section("STARTING RESUME PROCESSING PIPELINE")
        
        with self.logger.timer("Total Resume Processing"):
            # Initialize document store
            doc_store = DocumentStore()
            
            try:
                # Step 1: Download the resume (needed for hashing)
                self.logger.info(f"📥 Downloading resume: {file_name}")
                
                temp_dir = Path("temp_resumes")
                temp_dir.mkdir(exist_ok=True)
                temp_file_path = temp_dir / file_name

                
                file_content = self.drive_handler.download_file(file_id, file_name)
                self.downloaded_files.append(file_name)
                
                # Step 2: Compute hash of downloaded file
                with self.logger.timer("Compute Resume Hash"):
                    resume_hash = hash_file(file_name)
                    self.logger.info(f"🔑 Resume hash: {resume_hash[:16]}...")
                
                # Step 3: Check cache
                cached_data = doc_store.get_cached_resume(resume_hash)
                
                if cached_data:
                    self.logger.log_section("📦 USING CACHED RESULTS")
                    self.logger.info(f"✅ Found cached analysis for this resume")
                    self.logger.info(f"   Originally processed: {cached_data['created_at']}")
                    self.logger.info(f"   Skipping PDF parsing and LLM analysis")
                    
                    # Reconstruct state from cache
                    from src.state import ParsedResume, JobRoleMatch, ResumeSummary
                    
                    final_state = {
                        "messages": [HumanMessage(content=f"Loaded cached analysis for {file_name}")],
                        "file_id": file_id,
                        "file_name": file_name,
                        "raw_resume_text": "",  # Not stored in cache
                        "parsed_resume": ParsedResume.model_validate(cached_data['parsed_data']) if cached_data['parsed_data'] else None,
                        "job_role_matches": [JobRoleMatch.model_validate(match) for match in cached_data['job_roles']] if cached_data['job_roles'] else None,
                        "resume_summary": ResumeSummary.model_validate(cached_data['summary']) if cached_data['summary'] else None,
                        "current_step": "complete",
                        "error": None
                    }
                    
                    # Cleanup and close
                    self.cleanup_downloaded_files()
                    doc_store.close()
                    
                    self.logger.info("✅ Cache retrieval complete")
                    return final_state
                
                # Step 4: No cache hit - run full pipeline
                self.logger.log_section("🔄 PROCESSING NEW RESUME")
                self.logger.info("ℹ️  No cache found - running full analysis pipeline")
                
                # Extract text for raw text storage
                self.logger.info("📄 Extracting text from resume...")
                raw_text = self.text_extractor.extract_text(file_name)
                self.logger.info(f"✅ Extracted {len(raw_text)} characters, {len(raw_text.split())} words")
                
                # Build initial state for workflow
                initial_state = {
                    "messages": [HumanMessage(content=f"Processing {file_name}")],
                    "file_id": file_id,
                    "file_name": file_name,
                    "raw_resume_text": raw_text,
                    "parsed_resume": None,
                    "job_role_matches": None,
                    "resume_summary": None,
                    "current_step": "download_complete",
                    "error": None
                }
                
                # Run the full workflow (parse → analyze → summarize)
                final_state = self.workflow.invoke(initial_state)
                
                # Step 5: Save results to cache if successful
                if final_state.get('parsed_resume') and final_state.get('current_step') == 'complete':
                    self.logger.info("💾 Saving results to cache...")
                    
                    doc_store.save_cached_resume(
                        resume_hash=resume_hash,
                        file_name=file_name,
                        parsed_data=final_state['parsed_resume'].model_dump(),
                        job_roles=[match.model_dump() for match in final_state['job_role_matches']] if final_state.get('job_role_matches') else None,
                        summary=final_state['resume_summary'].model_dump() if final_state.get('resume_summary') else None
                    )
                    
                    self.logger.info("✅ Results cached for future use")
                else:
                    self.logger.warning("⚠️  Pipeline incomplete - results not cached")
                
                # Cleanup
                self.cleanup_downloaded_files()
                doc_store.close()
                
                return final_state
                
            except Exception as e:
                self.logger.error(f"❌ Pipeline execution failed: {str(e)}")
                # Cleanup even on error
                self.cleanup_downloaded_files()
                doc_store.close()
                raise
