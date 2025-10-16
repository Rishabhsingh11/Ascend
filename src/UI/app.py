"""Main Streamlit application for Ascend Resume Analyzer."""

import streamlit as st
from streamlit_option_menu import option_menu
import time
from pathlib import Path

# Import your existing components
from src.agent import JobSearchAgent
from src.google_drive_handler import GoogleDriveHandler
from src.document_store import DocumentStore
from src.config import get_settings
from src.logger import get_logger, set_logger, AgentLogger
from src.callbacks import StreamingCallbackHandler
from src.state import AgentState
from langchain_ollama import ChatOllama

from src.UI.streaming_utils import StreamlitTokenHandler, create_analysis_section, show_streaming_progress
from pathlib import Path

# Import UI components
from src.UI.components.results import render_results
from src.UI.components.cache_viewer import render_cache_stats


def init_session_state():
    """Initialize session state variables."""
    if 'processed_resume' not in st.session_state:
        st.session_state.processed_resume = None
    if 'selected_file' not in st.session_state:
        st.session_state.selected_file = None
    if 'agent' not in st.session_state:
        st.session_state.agent = None
    if 'drive_handler' not in st.session_state:
        st.session_state.drive_handler = None
    if 'enable_skill_gap' not in st.session_state:
        st.session_state.enable_skill_gap = True  # Default enabled
    if 'skill_gap_loading' not in st.session_state:
        st.session_state.skill_gap_loading = False


def load_custom_css():
    """Load custom CSS styling."""
    css_file = Path(__file__).parent / "styles" / "custom.css"
    
    # Additional inline CSS for text visibility
    inline_css = """
    <style>
        /* Force text visibility */
        .stExpander p, .stExpander div, .stExpander span {
            color: #1F2937 !important;
        }
        
        /* Fix markdown in expanders */
        .stExpander .stMarkdown {
            color: #1F2937 !important;
        }
        
        /* Ensure subheaders are visible */
        .stMarkdown h2, .stMarkdown h3 {
            color: #1E3A8A !important;
        }
    </style>
    """
    
    st.markdown(inline_css, unsafe_allow_html=True)
    
    # Load external CSS if exists
    if css_file.exists():
        with open(css_file, 'r') as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)


def main():
    """Main Streamlit application."""
    
    # Page configuration
    st.set_page_config(
        page_title="Ascend - AI Resume Analyzer",
        page_icon="🚀",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            'Get Help': 'https://github.com/Rishabhsingh11/Ascend-',
            'Report a bug': "https://github.com/Rishabhsingh11/Ascend-/issues",
            'About': "# Ascend Resume Analyzer\nAI-powered resume analysis and job matching tool."
        }
    )
    
    # Initialize session state
    init_session_state()
    
    # Load custom CSS
    load_custom_css()
    
    # Header
    st.markdown("""
        <div style='text-align: center; padding: 2rem 0;'>
            <h1 style='color: #1E3A8A; font-size: 3rem; margin-bottom: 0;'>
                🚀 Ascend
            </h1>
            <p style='color: #64748B; font-size: 1.2rem; margin-top: 0.5rem;'>
                AI-Powered Resume Analysis & Job Matching Platform
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    # Navigation menu
    selected = option_menu(
        menu_title=None,
        options=["📤 Upload Resume", "📊 Analysis Results", "💾 Cache Manager", "ℹ️ About"],
        icons=['cloud-upload', 'bar-chart-fill', 'database-fill', 'info-circle'],
        menu_icon="cast",
        default_index=0,
        orientation="horizontal",
        styles={
            "container": {"padding": "0!important", "background-color": "#F8FAFC"},
            "icon": {"color": "#3B82F6", "font-size": "20px"}, 
            "nav-link": {
                "font-size": "16px",
                "text-align": "center",
                "margin": "0px",
                "--hover-color": "#E0E7FF",
            },
            "nav-link-selected": {"background-color": "#3B82F6"},
        }
    )
    
    # Render selected page
    if selected == "📤 Upload Resume":
        render_upload_page()
    elif selected == "📊 Analysis Results":
        render_results_page()
    elif selected == "💾 Cache Manager":
        render_cache_page()
    elif selected == "ℹ️ About":
        render_about_page()


def render_upload_page():
    """Render the resume upload page."""
    st.header("📤 Upload & Analyze Resume")

    st.markdown("---")
    col_toggle1, col_toggle2 = st.columns([3, 1])
    with col_toggle1:
        st.markdown("### ⚙️ Analysis Options")
        enable_skill_gap = st.checkbox(
            "🔍 Enable Skill Gap Analysis",
            value=st.session_state.enable_skill_gap,
            help="Fetch real job postings and analyze skill gaps (adds 2-3 minutes)"
        )
        st.session_state.enable_skill_gap = enable_skill_gap
        
        if enable_skill_gap:
            st.info("✨ **Phase 2 Enabled:** Will fetch live job data and analyze skill gaps")
        else:
            st.warning("⚠️ **Phase 2 Disabled:** Only basic resume analysis will run")
    
    st.markdown("---")
    
    # Two-column layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Choose Upload Method")
        
        upload_method = st.radio(
            "Select method:",
            ["📁 Upload Local File", "☁️ From Google Drive"],
            horizontal=True
        )
        
        if upload_method == "📁 Upload Local File":
            render_local_upload()
        else:
            render_drive_upload()
    
    with col2:
        st.subheader("ℹ️ How It Works")
        st.info("""
        **Step 1:** Upload your resume (PDF or DOCX)
        
        **Step 2:** Our AI analyzes:
        - 📝 Contact information
        - 💼 Work experience
        - 🎓 Education
        - 🛠️ Skills
        
        **Step 3:** Get insights:
        - 🎯 Top 3 job matches
        - 📊 Quality score
        - 💡 Improvement tips
        
        **⚡ Cached resumes load instantly!**
        """)


def render_local_upload():
    """Handle local file upload."""
    uploaded_file = st.file_uploader(
        "Choose a resume file",
        type=['pdf', 'docx'],
        help="Upload your resume in PDF or DOCX format"
    )
    
    if uploaded_file is not None:
        st.success(f"✅ File uploaded: {uploaded_file.name}")
        
        # Save uploaded file temporarily
        temp_path = Path(f"temp_resumes/{uploaded_file.name}")
        temp_path.parent.mkdir(exist_ok=True)
        
        with open(temp_path, 'wb') as f:
            f.write(uploaded_file.getbuffer())
        
        if st.button("🚀 Analyze Resume", type="primary", use_container_width=True):
            analyze_local_resume(str(temp_path), uploaded_file.name)  # NEW: Use streaming function



def render_drive_upload():
    """Handle Google Drive file selection."""
    
    # Initialize session state for drive resumes
    if 'drive_resumes' not in st.session_state:
        st.session_state.drive_resumes = None
    if 'drive_connected' not in st.session_state:
        st.session_state.drive_connected = False
    
    st.info("🔐 Google Drive integration requires authentication")
    
    # Show connect button only if not connected
    if not st.session_state.drive_connected:
        if st.button("🔗 Connect to Google Drive"):
            with st.spinner("Connecting to Google Drive..."):
                try:
                    settings = get_settings()
                    drive_handler = GoogleDriveHandler()
                    st.session_state.drive_handler = drive_handler
                    
                    # List resumes
                    resumes = drive_handler.list_resumes(folder_name=settings.google_drive_folder_name)
                    
                    if resumes:
                        # Store resumes in session state
                        st.session_state.drive_resumes = resumes
                        st.session_state.drive_connected = True
                        st.success(f"✅ Found {len(resumes)} resume(s)")
                        st.rerun()  # Rerun to show the selector
                    else:
                        st.warning("⚠️ No resumes found in Google Drive folder")
                        
                except Exception as e:
                    st.error(f"❌ Error connecting to Google Drive: {str(e)}")
                    st.exception(e)
    
    # Show resume selector if connected
    if st.session_state.drive_connected and st.session_state.drive_resumes:
        st.success(f"✅ Connected - {len(st.session_state.drive_resumes)} resume(s) available")
        
        # Disconnect button
        if st.button("🔌 Disconnect", type="secondary"):
            st.session_state.drive_connected = False
            st.session_state.drive_resumes = None
            st.session_state.drive_handler = None
            st.rerun()
        
        st.markdown("---")
        
        # Build resume options
        resume_options = {}
        for r in st.session_state.drive_resumes:
            # Safely handle file size
            size_kb = "Unknown"
            if r.get('size'):
                try:
                    size_kb = f"{int(r['size']) // 1024} KB"
                except (ValueError, TypeError):
                    size_kb = "Unknown"
            
            display_name = f"{r['name']} ({size_kb})"
            resume_options[display_name] = r
        
        # Resume selector
        selected = st.selectbox(
            "Select a resume to analyze:",
            list(resume_options.keys()),
            key="resume_selector"
        )
        
        # Analyze button
        if st.button("📥 Download & Analyze", type="primary", width='stretch'):
            resume = resume_options[selected]
            with st.spinner("Analyzing resume..."):
                analyze_resume_from_drive(resume['id'], resume['name'])
            
def analyze_local_resume(file_path: str, file_name: str):
    """Analyze locally uploaded resume with cache-aware streaming + Phase 2 skill gap.
    
    Flow:
    1. Parse resume (no download needed)
    2. Compute hash and check cache for Phase 1 results
    3. If cached: Load Phase 1 from cache (instant)
    4. If not cached: Run Phase 1 with real LLM and cache results
    5. ALWAYS run Phase 2 (job market data changes constantly)
    
    Args:
        file_path: Path to locally uploaded resume file
        file_name: Original filename
    """
    
    from src.UI.streaming_utils import (
        StreamlitTokenHandler, 
        create_analysis_section, 
        show_streaming_progress,
        simulate_streaming_from_cache
    )
    from pathlib import Path
    from src.document_store import DocumentStore
    from src.utils import hash_file
    import time
    
    # Create progress indicators
    progress_placeholder = st.empty()
    status_placeholder = st.empty()
    
    # Create expandable sections for streaming output
    parsing_expander, parsing_container = create_analysis_section(
        "📄 Resume Parsing", 
        icon="📄", 
        expanded=True
    )
    
    roles_expander, roles_container = create_analysis_section(
        "🎯 Job Role Analysis",
        icon="🎯",
        expanded=True
    )
    
    summary_expander, summary_container = create_analysis_section(
        "📊 Quality Assessment",
        icon="📊",
        expanded=True
    )
    
    try:
        # ========== STEP 1: Initialize Agent ==========
        show_streaming_progress(
            "Initializing AI Agent",
            10,
            status_placeholder,
            progress_placeholder
        )
        
        if st.session_state.agent is None:
            from src.agent import JobSearchAgent
            st.session_state.agent = JobSearchAgent()
        
        time.sleep(0.3)
        
        # ========== STEP 2: Compute Hash & Check Cache ==========
        show_streaming_progress(
            "Computing resume hash & checking cache",
            20,
            status_placeholder,
            progress_placeholder
        )
        
        parsing_container.info(f"📄 Processing: {file_name}")
        
        resume_hash = hash_file(file_path)
        doc_store = DocumentStore()
        cached_data = doc_store.get_cached_resume(resume_hash)
        
        # Variables to store Phase 1 results
        parsed_resume = None
        job_matches = None
        summary = None
        raw_text = None
        
        # ========== CACHE HIT PATH (Load Phase 1 from cache) ==========
        if cached_data:
            st.success(f"📦 **Cache Hit!** Phase 1 loaded from {cached_data['created_at']}")
            st.info("⚡ Loading cached Phase 1 results... Phase 2 will still run with live data")
            
            # Parse cached data
            from src.state import ParsedResume, JobRoleMatch, ResumeSummary
            
            parsed_resume = ParsedResume.model_validate(cached_data['parsed_data'])
            job_matches = [JobRoleMatch.model_validate(m) for m in cached_data['job_roles']]
            summary = ResumeSummary.model_validate(cached_data['summary'])
            
            # ===== Parsing Section =====
            show_streaming_progress("Loading cached parsing results", 30, status_placeholder, progress_placeholder)
            
            parsing_container.success("✅ Resume parsed (from cache)")
            parsing_container.markdown(f"""
            **Extracted Information:**
            - **Name:** {parsed_resume.contact_info.name or 'N/A'}
            - **Email:** {parsed_resume.contact_info.email or 'N/A'}
            - **Skills:** {len(parsed_resume.skills)} identified
            - **Experience:** {len(parsed_resume.experience)} positions
            - **Education:** {len(parsed_resume.education)} degrees
            """)
            
            # ===== Job Roles Section (Simulated Streaming) =====
            show_streaming_progress("Simulating job role analysis (cached)", 50, status_placeholder, progress_placeholder)
            
            roles_text = "**Top 3 Job Role Recommendations:**\n\n"
            for idx, match in enumerate(job_matches, 1):
                roles_text += f"**{idx}. {match.role_title}**\n"
                roles_text += f"- **Confidence:** {match.confidence_score:.1%}\n"
                roles_text += f"- **Reasoning:** {match.reasoning}\n"
                roles_text += f"- **Matching Skills:** {', '.join(match.key_matching_skills[:5])}\n\n"
            
            simulate_streaming_from_cache(
                roles_container,
                roles_text,
                prefix="📦 Cached Analysis",
                chars_per_token=8,
                delay_ms=20
            )
            
            roles_container.success("✅ Job role analysis complete (from cache)")
            
            # ===== Summary Section (Simulated Streaming) =====
            show_streaming_progress("Simulating quality assessment (cached)", 70, status_placeholder, progress_placeholder)
            
            summary_text = f"**Quality Score:** {summary.quality_score}/10\n\n"
            summary_text += f"**Summary:**\n{summary.overall_summary}\n\n"
            summary_text += f"**Years of Experience:** {summary.years_of_experience or 'N/A'}\n\n"
            summary_text += f"**Key Strengths:**\n"
            summary_text += '\n'.join([f"- {s}" for s in summary.key_strengths]) + "\n\n"
            summary_text += f"**Improvement Suggestions:**\n"
            summary_text += '\n'.join([f"- {s}" for s in summary.improvement_suggestions])
            
            if summary.grammatical_issues:
                summary_text += f"\n\n**Grammatical Issues:**\n"
                summary_text += '\n'.join([f"- {i}" for i in summary.grammatical_issues])
            
            simulate_streaming_from_cache(
                summary_container,
                summary_text,
                prefix="📦 Cached Assessment",
                chars_per_token=8,
                delay_ms=20
            )
            
            summary_container.success("✅ Quality assessment complete (from cache)")
            
            # Need raw_text for Phase 2, extract it
            from src.resume_parser import ResumeTextExtractor
            text_extractor = ResumeTextExtractor()
            raw_text = text_extractor.extract_text(file_path)
        
        # ========== CACHE MISS PATH (Run Phase 1 with LLM) ==========
        else:
            st.info("🔄 **Cache Miss** - Running full Phase 1 analysis (10-15 minutes)")
            
            # ===== Parse Resume =====
            show_streaming_progress("Parsing resume structure (PDFPlumber)", 30, status_placeholder, progress_placeholder)
            
            from src.enhanced_resume_parser import EnhancedResumeParser
            from src.resume_parser import ResumeTextExtractor
            
            parser = EnhancedResumeParser(file_path=file_path, debug=False)
            parsed_resume = parser.parse()
            
            text_extractor = ResumeTextExtractor()
            raw_text = text_extractor.extract_text(file_path)
            
            parsing_container.success("✅ Resume parsed successfully")
            parsing_container.markdown(f"""
            **Extracted Information:**
            - **Name:** {parsed_resume.contact_info.name or 'N/A'}
            - **Email:** {parsed_resume.contact_info.email or 'N/A'}
            - **Skills:** {len(parsed_resume.skills)} identified
            - **Experience:** {len(parsed_resume.experience)} positions
            - **Education:** {len(parsed_resume.education)} degrees
            """)
            
            # ===== Analyze Job Roles with REAL LLM STREAMING =====
            show_streaming_progress("Analyzing job role fit (LLM streaming - ~6 minutes)", 50, status_placeholder, progress_placeholder)
            
            from src.state import AgentState
            from langchain_core.messages import HumanMessage
            
            current_state = {
                'messages': [HumanMessage(content=f"Processing {file_name}")],
                'file_id': 'local',
                'file_name': file_name,
                'raw_resume_text': raw_text,
                'parsed_resume': parsed_resume,
                'job_role_matches': None,
                'resume_summary': None,
                'current_step': 'parsing_complete',
                'error': None
            }
            
            roles_handler = StreamlitTokenHandler(
                roles_container,
                prefix="🤖 AI Analysis in Progress (Live Streaming)..."
            )
            
            roles_result = st.session_state.agent._analyze_job_roles_streaming(
                current_state,
                token_callback=roles_handler.on_token
            )
            
            if roles_result.get('error'):
                roles_container.error(f"❌ Analysis failed: {roles_result['error']}")
                doc_store.close()
                return
            
            roles_handler.clear()
            roles_container.success("✅ Job role analysis complete")
            
            job_matches = roles_result['job_role_matches']
            for idx, match in enumerate(job_matches, 1):
                roles_container.markdown(f"""
                **{idx}. {match.role_title}**
                - **Confidence:** {match.confidence_score:.1%}
                - **Reasoning:** {match.reasoning}
                - **Matching Skills:** {', '.join(match.key_matching_skills[:5])}
                """)
            
            # ===== Generate Summary with REAL LLM STREAMING =====
            show_streaming_progress("Generating quality assessment (LLM streaming - ~8 minutes)", 70, status_placeholder, progress_placeholder)
            
            current_state['job_role_matches'] = job_matches
            current_state['current_step'] = 'analysis_complete'
            
            summary_handler = StreamlitTokenHandler(
                summary_container,
                prefix="🤖 AI Review in Progress (Live Streaming)..."
            )
            
            summary_result = st.session_state.agent._generate_summary_streaming(
                current_state,
                token_callback=summary_handler.on_token
            )
            
            if summary_result.get('error'):
                summary_container.error(f"❌ Summary failed: {summary_result['error']}")
                doc_store.close()
                return
            
            summary_handler.clear()
            summary_container.success("✅ Quality assessment complete")
            
            summary = summary_result['resume_summary']
            summary_container.markdown(f"""
            **Quality Score:** {summary.quality_score}/10
            
            **Summary:**
            {summary.overall_summary}
            
            **Years of Experience:** {summary.years_of_experience or 'N/A'}
            
            **Key Strengths:**
            {chr(10).join(['- ' + s for s in summary.key_strengths])}
            
            **Improvement Suggestions:**
            {chr(10).join(['- ' + s for s in summary.improvement_suggestions])}
            
            **Grammatical Issues:**
            {chr(10).join(['- ' + i for i in summary.grammatical_issues]) if summary.grammatical_issues else '- None found'}
            """)
            
            # ===== Save Phase 1 to Cache =====
            st.info("💾 Saving Phase 1 results to cache...")
            
            doc_store.save_cached_resume(
                resume_hash=resume_hash,
                file_name=file_name,
                parsed_data=parsed_resume.model_dump(),
                job_roles=[match.model_dump() for match in job_matches],
                summary=summary.model_dump()
            )
            
            st.success("✅ Phase 1 cached - future loads will be instant!")
        
        # ========== PHASE 2: SKILL GAP ANALYSIS (ALWAYS RUNS) ==========
        # Initialize result variables
        job_postings = []
        skill_gap_analysis = None
        
        if st.session_state.enable_skill_gap:
            st.markdown("---")
            st.subheader("🔍 Phase 2: Skill Gap Analysis")
            st.info("📡 Phase 2 always runs with live job market data (not cached)")
            
            jobs_expander = st.expander("📋 Job Postings", expanded=True)
            gaps_expander = st.expander("📊 Skill Gap Analysis", expanded=True)
            
            with jobs_expander:
                jobs_container = st.container()
            
            with gaps_expander:
                gaps_container = st.container()
            
            try:
                # ===== Fetch Job Postings =====
                show_streaming_progress(
                    "Fetching live job postings from APIs",
                    80,
                    status_placeholder,
                    progress_placeholder
                )
                
                jobs_container.info("🌐 Fetching job postings for your top 3 recommended roles...")
                
                # Build Phase 2 state
                phase2_state = {
                    'messages': [],
                    'file_id': 'local',
                    'file_name': file_name,
                    'raw_resume_text': raw_text,
                    'parsed_resume': parsed_resume,
                    'job_role_matches': job_matches,
                    'resume_summary': summary,
                    'current_step': 'complete',
                    'error': None,
                    'job_postings': [],
                    'skill_gap_analysis': None,
                    'enable_skill_gap': True
                }
                
                # Fetch jobs
                job_fetch_result = st.session_state.agent._fetch_job_postings(phase2_state)
                
                if job_fetch_result.get('error'):
                    jobs_container.warning(f"⚠️ Could not fetch jobs: {job_fetch_result['error']}")
                else:
                    job_postings = job_fetch_result.get('job_postings', [])
                    
                    if job_postings:
                        jobs_container.success(f"✅ Fetched {len(job_postings)} job postings")
                        
                        # Show job summary by role
                        jobs_by_role = {}
                        for job in job_postings:
                            matched_role = None
                            for role_match in job_matches:
                                if any(word.lower() in job.title.lower() 
                                      for word in role_match.role_title.split() 
                                      if len(word) > 3):
                                    matched_role = role_match.role_title
                                    break
                            
                            if matched_role:
                                if matched_role not in jobs_by_role:
                                    jobs_by_role[matched_role] = []
                                jobs_by_role[matched_role].append(job)
                        
                        for role, role_jobs in jobs_by_role.items():
                            with jobs_container.expander(f"📌 {role} ({len(role_jobs)} jobs)", expanded=False):
                                for idx, job in enumerate(role_jobs[:3], 1):
                                    st.markdown(f"""
                                    **{idx}. {job.title}** @ {job.company}
                                    - 📍 {job.location}
                                    - 💰 {job.salary or 'Not specified'}
                                    - 🔗 [Apply]({job.url})
                                    """)
                        
                        # ===== Analyze Skill Gaps =====
                        show_streaming_progress(
                            "Analyzing skill gaps",
                            90,
                            status_placeholder,
                            progress_placeholder
                        )
                        
                        gaps_container.info("🧠 Analyzing your skills vs market requirements...")
                        
                        phase2_state['job_postings'] = job_postings
                        skill_gap_result = st.session_state.agent._analyze_skill_gaps(phase2_state)
                        
                        if skill_gap_result.get('error'):
                            gaps_container.error(f"❌ Skill gap analysis failed: {skill_gap_result['error']}")
                        else:
                            skill_gap_analysis = skill_gap_result.get('skill_gap_analysis')
                            
                            if skill_gap_analysis:
                                gaps_container.success("✅ Skill gap analysis complete!")
                                
                                gaps_container.metric(
                                    "📊 Overall Market Readiness",
                                    f"{skill_gap_analysis.overall_market_readiness}%"
                                )
                                
                                gaps_container.markdown(f"""
                                **Analysis Summary:**
                                - 📈 Jobs Analyzed: {skill_gap_analysis.total_jobs_analyzed}
                                - 🎯 Roles Evaluated: {len(skill_gap_analysis.role_analyses)}
                                - 🚨 Common Gaps: {len(skill_gap_analysis.common_gaps)}
                                - ⚡ Quick Wins: {len(skill_gap_analysis.quick_wins)}
                                - 📅 Date: {skill_gap_analysis.analysis_date}
                                """)
                                
                                gaps_container.info("👉 Go to **Analysis Results** to see detailed insights")
                    else:
                        jobs_container.warning("⚠️ No job postings found")
                        
            except Exception as e:
                st.error(f"❌ Phase 2 error: {str(e)}")
                with st.expander("🐛 Error Details"):
                    st.exception(e)
        
        # ===== Complete & Store Results =====
        show_streaming_progress("Analysis complete!", 100, status_placeholder, progress_placeholder)
        
        # Store complete results in session state (INCLUDING Phase 2)
        st.session_state.processed_resume = {
            'parsed_resume': parsed_resume,
            'job_role_matches': job_matches,
            'resume_summary': summary,
            'job_postings': job_postings,  # NEW: Phase 2 data
            'skill_gap_analysis': skill_gap_analysis,  # NEW: Phase 2 data
            'file_name': file_name,
            'current_step': 'complete',
            'error': None,
            'enable_skill_gap': st.session_state.enable_skill_gap
        }
        
        # Cleanup
        doc_store.close()
        
        temp_file = Path(file_path)
        if temp_file.exists():
            temp_file.unlink()
        
        time.sleep(1)
        st.success("🎉 Resume analyzed successfully!")
        st.balloons()
        
        progress_placeholder.empty()
        status_placeholder.empty()
        
        st.info("👉 Go to **Analysis Results** tab to view complete insights")
        
    except Exception as e:
        st.error(f"❌ Error analyzing resume: {str(e)}")
        progress_placeholder.empty()
        status_placeholder.empty()
        
        with st.expander("🐛 Error Details"):
            st.exception(e)



def analyze_resume(file_path: str, file_name: str):
    """Analyze a resume file."""
    
    # Progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Initialize agent if not exists
        if st.session_state.agent is None:
            status_text.text("🤖 Initializing AI Agent...")
            progress_bar.progress(20)
            st.session_state.agent = JobSearchAgent()
        
        status_text.text("📄 Processing resume...")
        progress_bar.progress(40)
        
        # Process resume
        result = st.session_state.agent.process_resume(
            file_id="local",
            file_name=file_name
        )
        
        progress_bar.progress(100)
        status_text.text("✅ Analysis complete!")
        
        # Store result in session state
        st.session_state.processed_resume = result
        
        time.sleep(1)
        st.success("🎉 Resume analyzed successfully!")
        st.balloons()
        
        # Switch to results tab
        st.info("👉 Go to **Analysis Results** tab to view detailed insights")
        
    except Exception as e:
        st.error(f"❌ Error analyzing resume: {str(e)}")
        progress_bar.empty()
        status_text.empty()


def analyze_resume_from_drive(file_id: str, file_name: str):
    """Analyze resume using the agent's workflow."""
    
    progress = st.progress(0)
    status = st.empty()
    
    try:
        # Initialize agent
        if st.session_state.agent is None:
            from src.agent import JobSearchAgent
            st.session_state.agent = JobSearchAgent()
        
        status.info("🚀 Starting resume analysis...")
        progress.progress(10)
        
        # Run workflow
        result = st.session_state.agent.process_resume(
            file_id=file_id,
            file_name=file_name,
            enable_skill_gap=True
        )
        
        progress.progress(100)
        status.empty()
        progress.empty()
        
        if result.get('error'):
            st.error(f"❌ Analysis failed: {result['error']}")
            return
        
        # Store results
        st.session_state.processed_resume = result
        
        st.success("✅ Analysis complete!")
        
        # ========== PHASE 1 RESULTS ==========
        st.markdown("---")
        st.subheader("📋 Phase 1: Resume Analysis")
        
        if result.get('cache_hit'):
            st.info("⚡ Phase 1 loaded from cache (instant)")
        
        # Parsing
        if result.get('parsed_resume'):
            with st.expander("📄 Resume Parsing", expanded=True):
                pr = result['parsed_resume']
                st.markdown(f"""
                **Candidate Information:**
                - **Name:** {pr.contact_info.name or 'N/A'}
                - **Email:** {pr.contact_info.email or 'N/A'}
                - **Phone:** {pr.contact_info.phone or 'N/A'}
                - **Location:** {pr.contact_info.location or 'N/A'}
                - **LinkedIn:** {pr.contact_info.linkedin or 'N/A'}
                
                **Resume Content:**
                - **Skills:** {len(pr.skills)} identified
                - **Experience:** {len(pr.experience)} positions
                - **Education:** {len(pr.education)} degrees
                - **Certifications:** {len(pr.certifications)}
                - **Projects:** {len(pr.projects)}
                """)
        
        # Job Roles
        if result.get('job_role_matches'):
            with st.expander("🎯 Job Role Recommendations", expanded=True):
                for idx, match in enumerate(result['job_role_matches'], 1):
                    st.markdown(f"""
                    ### {idx}. {match.role_title}
                    - **Confidence Score:** {match.confidence_score:.1%}
                    - **Reasoning:** {match.reasoning}
                    - **Matching Skills:** {', '.join(match.key_matching_skills[:8])}
                    """)
                    st.markdown("---")
        
        # Summary
        if result.get('resume_summary'):
            with st.expander("📊 Quality Assessment", expanded=True):
                summary = result['resume_summary']
                
                col1, col2 = st.columns([1, 3])
                with col1:
                    st.metric("Quality Score", f"{summary.quality_score}/10")
                with col2:
                    st.metric("Experience", f"{summary.years_of_experience or 'N/A'} years")
                
                st.markdown(f"**Summary:**\n\n{summary.overall_summary}")
                
                st.markdown(f"**Key Strengths:**")
                for strength in summary.key_strengths:
                    st.markdown(f"- {strength}")
                
                if summary.improvement_suggestions:
                    st.markdown(f"**Improvement Suggestions:**")
                    for suggestion in summary.improvement_suggestions:
                        st.markdown(f"- {suggestion}")
        
        # ========== PHASE 2 RESULTS ==========
        if result.get('job_postings') or result.get('skill_gap_analysis'):
            st.markdown("---")
            st.subheader("🔍 Phase 2: Job Market Analysis")
        
        # Job Postings
        if result.get('job_postings'):
            with st.expander(f"📋 Job Postings ({len(result['job_postings'])} found)", expanded=False):
                jobs = result['job_postings']
                
                # Group by role
                from collections import defaultdict
                jobs_by_source = defaultdict(list)
                for job in jobs:
                    jobs_by_source[job.source].append(job)
                
                for source, source_jobs in jobs_by_source.items():
                    st.markdown(f"**{source.title()}** ({len(source_jobs)} jobs)")
                    for job in source_jobs[:5]:  # Show first 5 per source
                        st.markdown(f"""
                        - **{job.title}** @ {job.company}
                          - 📍 {job.location}
                          - 💰 {job.salary or 'Not specified'}
                          - 🔗 [Apply]({job.url})
                        """)
        
        # Skill Gap Analysis
        if result.get('skill_gap_analysis'):
            with st.expander("🎯 Skill Gap Analysis", expanded=True):
                gap = result['skill_gap_analysis']
                
                # Metrics
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Market Readiness", f"{gap.overall_market_readiness}%")
                col2.metric("Jobs Analyzed", gap.total_jobs_analyzed)
                col3.metric("Common Gaps", len(gap.common_gaps))
                col4.metric("Quick Wins", len(gap.quick_wins))
                
                st.markdown("---")
                
                # Common gaps
                if gap.common_gaps:
                    st.markdown("**🎯 Skills to Focus On (Common Gaps):**")
                    for skill in gap.common_gaps[:10]:
                        st.markdown(f"- {skill}")
                
                # Quick wins
                if gap.quick_wins:
                    st.markdown("**⚡ Quick Wins (Easy to learn):**")
                    for skill in gap.quick_wins:
                        st.markdown(f"- {skill}")
                
                # Long-term goals
                if gap.long_term_goals:
                    st.markdown("**🎓 Long-term Goals:**")
                    for skill in gap.long_term_goals:
                        st.markdown(f"- {skill}")
                
                # Action plans
                st.markdown("---")
                st.markdown("**📅 Action Plans:**")
                
                if gap.immediate_actions:
                    st.markdown("*Immediate (Next 2 weeks):*")
                    for action in gap.immediate_actions:
                        st.markdown(f"- {action}")
                
                if gap.one_month_plan:
                    st.markdown("*1 Month Plan:*")
                    for action in gap.one_month_plan:
                        st.markdown(f"- {action}")
        
        # ========== PHASE 3 RESULTS ==========
        if result.get('csv_path') or result.get('email_sent'):
            st.markdown("---")
            st.subheader("📧 Phase 3: Export & Email")
            
            with st.expander("📤 Export Results", expanded=True):
                if result.get('csv_path'):
                    st.success(f"✅ CSV created: `{result['csv_path']}`")
                    st.download_button(
                        label="📥 Download CSV",
                        data=open(result['csv_path'], 'rb').read(),
                        file_name=result['csv_path'].split('/')[-1],
                        mime='text/csv'
                    )
                
                if result.get('email_sent'):
                    st.success(f"✅ Email sent to {result['parsed_resume'].contact_info.email}")
                    st.info("📬 Check your inbox for job recommendations!")
                elif result.get('email_sent') == False:
                    st.warning("⚠️ Email could not be sent (check SMTP settings in .env)")
                    st.info("CSV file is still available for download above")
        
        st.balloons()
        
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        with st.expander("🐛 Error Details"):
            st.exception(e)




def render_results_page():
    """Render analysis results page."""
    if st.session_state.processed_resume is None:
        st.info("📤 Please upload and analyze a resume first")
        return
    
    render_results(st.session_state.processed_resume)


def render_cache_page():
    """Render cache statistics page."""
    st.header("💾 Cache Manager")
    render_cache_stats()


def render_about_page():
    """Render about page."""
    st.header("ℹ️ About Ascend")
    
    st.markdown("""
    ## 🚀 What is Ascend?
    
    Ascend is an AI-powered resume analysis platform that helps job seekers:
    - 📊 Get detailed resume analysis
    - 🎯 Find matching job roles
    - 💡 Receive improvement suggestions
    - ⚡ Leverage intelligent caching for fast results
    
    ## 🛠️ Technology Stack
    
    - **Frontend:** Streamlit
    - **AI/ML:** Ollama (Mistral LLM), LangChain, LangGraph
    - **Parsing:** PDFPlumber, Python-DOCX
    - **Storage:** SQLite (Caching)
    - **Cloud:** Google Drive API
    
    ## 👨‍💻 Developer
    
    Built by **Rishabh Dinesh Singh**
    - 💼 Data Engineer at Aretove Technologies
    - 📧 rishabhdineshsingh@gmail.com
    - 🔗 [LinkedIn](https://linkedin.com/in/rishabhdineshsingh)
    - 🐙 [GitHub](https://github.com/Rishabhsingh11)
    
    ## 📜 Version
    
    **v1.0.0** - Phase 1 Complete
    - ✅ Resume parsing
    - ✅ Job matching
    - ✅ Quality assessment
    - ✅ Intelligent caching
    
    **Coming Soon:** Phase 2A - Skills Gap Analysis & Web Search Tools
    """)


if __name__ == "__main__":
    main()
