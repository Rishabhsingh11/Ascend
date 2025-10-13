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
                    drive_handler = GoogleDriveHandler(settings.google_credentials_path)
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
    """Analyze locally uploaded resume with cache-aware streaming.
    
    This function mirrors analyze_resume_from_drive but skips the Google Drive download step.
    
    Flow:
    1. Parse resume (no download needed - file already local)
    2. Compute hash and check cache
    3. If cached: Simulate streaming with cached data (instant ~5s)
    4. If not cached: Run real LLM streaming and cache results (~14 min)
    
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
        
        time.sleep(0.3)  # Brief pause for UX
        
        # ========== STEP 2: Compute Hash & Check Cache ==========
        show_streaming_progress(
            "Computing resume hash & checking cache",
            20,
            status_placeholder,
            progress_placeholder
        )
        
        # File is already downloaded from Streamlit uploader
        parsing_container.info(f"📄 Processing: {file_name}")
        
        # Compute hash
        resume_hash = hash_file(file_path)
        
        # Initialize document store and check cache
        doc_store = DocumentStore()
        cached_data = doc_store.get_cached_resume(resume_hash)
        
        # ========== CACHE HIT PATH (Instant Results) ==========
        if cached_data:
            st.success(f"📦 **Cache Hit!** This resume was analyzed on {cached_data['created_at']}")
            st.info("⚡ Loading cached results with simulated streaming for UX consistency...")
            
            # Parse cached data
            from src.state import ParsedResume, JobRoleMatch, ResumeSummary
            
            parsed_resume = ParsedResume.model_validate(cached_data['parsed_data'])
            job_matches = [JobRoleMatch.model_validate(m) for m in cached_data['job_roles']]
            summary = ResumeSummary.model_validate(cached_data['summary'])
            
            # ===== Parsing Section =====
            show_streaming_progress(
                "Loading cached parsing results",
                30,
                status_placeholder,
                progress_placeholder
            )
            
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
            show_streaming_progress(
                "Simulating job role analysis (cached)",
                50,
                status_placeholder,
                progress_placeholder
            )
            
            # Build text representation of job roles for streaming
            roles_text = "**Top 3 Job Role Recommendations:**\n\n"
            for idx, match in enumerate(job_matches, 1):
                roles_text += f"**{idx}. {match.role_title}**\n"
                roles_text += f"- **Confidence:** {match.confidence_score:.1%}\n"
                roles_text += f"- **Reasoning:** {match.reasoning}\n"
                roles_text += f"- **Matching Skills:** {', '.join(match.key_matching_skills[:5])}\n\n"
            
            # Simulate streaming (faster than real LLM)
            simulate_streaming_from_cache(
                roles_container,
                roles_text,
                prefix="📦 Cached Analysis",
                chars_per_token=8,
                delay_ms=20  # 20ms delay = very fast
            )
            
            roles_container.success("✅ Job role analysis complete (from cache)")
            
            # ===== Summary Section (Simulated Streaming) =====
            show_streaming_progress(
                "Simulating quality assessment (cached)",
                70,
                status_placeholder,
                progress_placeholder
            )
            
            # Build text representation of summary
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
            
            # Simulate streaming
            simulate_streaming_from_cache(
                summary_container,
                summary_text,
                prefix="📦 Cached Assessment",
                chars_per_token=8,
                delay_ms=20
            )
            
            summary_container.success("✅ Quality assessment complete (from cache)")
            
            # Store in session state
            st.session_state.processed_resume = {
                'parsed_resume': parsed_resume,
                'job_role_matches': job_matches,
                'resume_summary': summary,
                'file_name': file_name,
                'current_step': 'complete',
                'error': None
            }
            
            show_streaming_progress(
                "Complete!",
                100,
                status_placeholder,
                progress_placeholder
            )
            
            # Cleanup
            doc_store.close()
            
            # Delete temp file
            temp_file = Path(file_path)
            if temp_file.exists():
                temp_file.unlink()
            
            time.sleep(1)
            st.success("🎉 Resume loaded from cache!")
            st.balloons()
            
            progress_placeholder.empty()
            status_placeholder.empty()
            
            st.info("👉 Go to **Analysis Results** tab to view detailed insights")
            return
        
        # ========== CACHE MISS PATH (Real LLM Streaming) ==========
        st.info("🔄 **Cache Miss** - Running full AI analysis (this will take 10-15 minutes)")
        
        # ===== Parse Resume =====
        show_streaming_progress(
            "Parsing resume structure (PDFPlumber)",
            30,
            status_placeholder,
            progress_placeholder
        )
        
        from src.enhanced_resume_parser import EnhancedResumeParser
        from src.resume_parser import ResumeTextExtractor
        
        # Parse with PDFPlumber
        parser = EnhancedResumeParser(file_path=file_path, debug=False)
        parsed_resume = parser.parse()
        
        # Extract raw text for summary analysis
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
        show_streaming_progress(
            "Analyzing job role fit (LLM streaming - ~6 minutes)",
            50,
            status_placeholder,
            progress_placeholder
        )
        
        from src.state import AgentState
        from langchain_core.messages import HumanMessage
        
        # Build state for LLM analysis
        current_state = {
            'messages': [HumanMessage(content=f"Processing {file_name}")],
            'file_id': 'local',  # Local upload doesn't have Drive file_id
            'file_name': file_name,
            'raw_resume_text': raw_text,
            'parsed_resume': parsed_resume,
            'job_role_matches': None,
            'resume_summary': None,
            'current_step': 'parsing_complete',
            'error': None
        }
        
        # Setup streaming handler for job roles
        roles_handler = StreamlitTokenHandler(
            roles_container,
            prefix="🤖 AI Analysis in Progress (Live Streaming)..."
        )
        
        # Call streaming analysis
        roles_result = st.session_state.agent._analyze_job_roles_streaming(
            current_state,
            token_callback=roles_handler.on_token
        )
        
        # Check for errors
        if roles_result.get('error'):
            roles_container.error(f"❌ Analysis failed: {roles_result['error']}")
            doc_store.close()
            return
        
        # Finalize streaming display
        roles_handler.clear()
        roles_container.success("✅ Job role analysis complete")
        
        # Display structured results
        job_matches = roles_result['job_role_matches']
        for idx, match in enumerate(job_matches, 1):
            roles_container.markdown(f"""
            **{idx}. {match.role_title}**
            - **Confidence:** {match.confidence_score:.1%}
            - **Reasoning:** {match.reasoning}
            - **Matching Skills:** {', '.join(match.key_matching_skills[:5])}
            """)
        
        # ===== Generate Summary with REAL LLM STREAMING =====
        show_streaming_progress(
            "Generating quality assessment (LLM streaming - ~8 minutes)",
            70,
            status_placeholder,
            progress_placeholder
        )
        
        # Update state with job roles
        current_state['job_role_matches'] = job_matches
        current_state['current_step'] = 'analysis_complete'
        
        # Setup streaming handler for summary
        summary_handler = StreamlitTokenHandler(
            summary_container,
            prefix="🤖 AI Review in Progress (Live Streaming)..."
        )
        
        # Call streaming summary generation
        summary_result = st.session_state.agent._generate_summary_streaming(
            current_state,
            token_callback=summary_handler.on_token
        )
        
        # Check for errors
        if summary_result.get('error'):
            summary_container.error(f"❌ Summary failed: {summary_result['error']}")
            doc_store.close()
            return
        
        # Finalize streaming display
        summary_handler.clear()
        summary_container.success("✅ Quality assessment complete")
        
        # Display structured summary
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
        
        # ===== Save to Cache =====
        show_streaming_progress(
            "Saving to cache for future instant access",
            90,
            status_placeholder,
            progress_placeholder
        )
        
        st.info("💾 Saving results to cache for future instant access...")
        
        doc_store.save_cached_resume(
            resume_hash=resume_hash,
            file_name=file_name,
            parsed_data=parsed_resume.model_dump(),
            job_roles=[match.model_dump() for match in job_matches],
            summary=summary.model_dump()
        )
        
        st.success("✅ Results cached - next time this resume will load instantly!")
        
        # ===== Complete =====
        show_streaming_progress(
            "Analysis complete!",
            100,
            status_placeholder,
            progress_placeholder
        )
        
        # Store result in session state
        st.session_state.processed_resume = {
            'parsed_resume': parsed_resume,
            'job_role_matches': job_matches,
            'resume_summary': summary,
            'file_name': file_name,
            'current_step': 'complete',
            'error': None
        }
        
        # Cleanup
        doc_store.close()
        
        # Delete temp file
        temp_file = Path(file_path)
        if temp_file.exists():
            temp_file.unlink()
        
        time.sleep(1)
        st.success("🎉 Resume analyzed successfully!")
        st.balloons()
        
        # Clear progress indicators
        progress_placeholder.empty()
        status_placeholder.empty()
        
        st.info("👉 Go to **Analysis Results** tab to view detailed insights")
        
    except Exception as e:
        st.error(f"❌ Error analyzing resume: {str(e)}")
        progress_placeholder.empty()
        status_placeholder.empty()
        
        # Show detailed error in expander
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
    """Analyze resume from Google Drive with cache-aware streaming.
    
    Flow:
    1. Download & parse resume
    2. Compute hash and check cache
    3. If cached: Simulate streaming with cached data (instant)
    4. If not cached: Run real LLM streaming and cache results
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
    import json
    
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
        
        # ========== STEP 2: Download Resume ==========
        show_streaming_progress(
            "Downloading from Google Drive",
            20,
            status_placeholder,
            progress_placeholder
        )
        
        drive_handler = st.session_state.drive_handler
        
        # Create temp directory
        temp_dir = Path("temp_resumes")
        temp_dir.mkdir(exist_ok=True)
        temp_file_path = temp_dir / file_name
        
        # Download file
        file_content = drive_handler.download_file(file_id, str(temp_file_path))
        
        parsing_container.success(f"✅ Downloaded: {file_name}")
        
        # ========== STEP 3: Compute Hash & Check Cache ==========
        show_streaming_progress(
            "Computing resume hash & checking cache",
            30,
            status_placeholder,
            progress_placeholder
        )
        
        resume_hash = hash_file(str(temp_file_path))
        
        # Initialize document store
        doc_store = DocumentStore()
        cached_data = doc_store.get_cached_resume(resume_hash)
        
        # ========== CACHE HIT PATH (Instant Results) ==========
        if cached_data:
            st.success(f"📦 **Cache Hit!** This resume was analyzed on {cached_data['created_at']}")
            st.info("⚡ Loading cached results with simulated streaming for UX consistency...")
            
            # Parse cached data
            from src.state import ParsedResume, JobRoleMatch, ResumeSummary
            
            parsed_resume = ParsedResume.model_validate(cached_data['parsed_data'])
            job_matches = [JobRoleMatch.model_validate(m) for m in cached_data['job_roles']]
            summary = ResumeSummary.model_validate(cached_data['summary'])
            
            # ===== Parsing Section =====
            show_streaming_progress("Loading cached parsing results", 40, status_placeholder, progress_placeholder)
            
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
            show_streaming_progress("Simulating job role analysis (cached)", 60, status_placeholder, progress_placeholder)
            
            # Build text representation of job roles for streaming
            roles_text = "**Top 3 Job Role Recommendations:**\n\n"
            for idx, match in enumerate(job_matches, 1):
                roles_text += f"**{idx}. {match.role_title}**\n"
                roles_text += f"- **Confidence:** {match.confidence_score:.1%}\n"
                roles_text += f"- **Reasoning:** {match.reasoning}\n"
                roles_text += f"- **Matching Skills:** {', '.join(match.key_matching_skills[:5])}\n\n"
            
            # Simulate streaming
            simulate_streaming_from_cache(
                roles_container,
                roles_text,
                prefix="📦 Cached Analysis",
                chars_per_token=8,
                delay_ms=20
            )
            
            roles_container.success("✅ Job role analysis complete (from cache)")
            
            # ===== Summary Section (Simulated Streaming) =====
            show_streaming_progress("Simulating quality assessment (cached)", 80, status_placeholder, progress_placeholder)
            
            # Build text representation of summary
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
            
            # Simulate streaming
            simulate_streaming_from_cache(
                summary_container,
                summary_text,
                prefix="📦 Cached Assessment",
                chars_per_token=8,
                delay_ms=20
            )
            
            summary_container.success("✅ Quality assessment complete (from cache)")
            
            # Store in session state
            st.session_state.processed_resume = {
                'parsed_resume': parsed_resume,
                'job_role_matches': job_matches,
                'resume_summary': summary,
                'file_name': file_name,
                'current_step': 'complete',
                'error': None
            }
            
            show_streaming_progress("Complete!", 100, status_placeholder, progress_placeholder)
            
            # Cleanup
            doc_store.close()
            if temp_file_path.exists():
                temp_file_path.unlink()
            
            st.success("🎉 Resume loaded from cache!")
            st.balloons()
            
            progress_placeholder.empty()
            status_placeholder.empty()
            
            st.info("👉 Go to **Analysis Results** tab to view detailed insights")
            return
        
        # ========== CACHE MISS PATH (Real LLM Streaming) ==========
        st.info("🔄 **Cache Miss** - Running full AI analysis (this will take 5-10 minutes)")
        
        # ===== Parse Resume =====
        show_streaming_progress(
            "Parsing resume structure (PDFPlumber)",
            40,
            status_placeholder,
            progress_placeholder
        )
        
        from src.enhanced_resume_parser import EnhancedResumeParser
        from src.resume_parser import ResumeTextExtractor
        
        parser = EnhancedResumeParser(file_path=str(temp_file_path), debug=False)
        parsed_resume = parser.parse()
        
        text_extractor = ResumeTextExtractor()
        raw_text = text_extractor.extract_text(str(temp_file_path))
        
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
        show_streaming_progress(
            "Analyzing job role fit (LLM streaming - ~6 minutes)",
            60,
            status_placeholder,
            progress_placeholder
        )
        
        from src.state import AgentState
        from langchain_core.messages import HumanMessage
        
        current_state = {
            'messages': [HumanMessage(content=f"Processing {file_name}")],
            'file_id': file_id,
            'file_name': file_name,
            'raw_resume_text': raw_text,
            'parsed_resume': parsed_resume,
            'job_role_matches': None,
            'resume_summary': None,
            'current_step': 'parsing_complete',
            'error': None
        }
        
        # Setup streaming handler
        roles_handler = StreamlitTokenHandler(
            roles_container,
            prefix="🤖 AI Analysis in Progress (Live Streaming)..."
        )
        
        # Call streaming analysis
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
        
        # Display structured results
        job_matches = roles_result['job_role_matches']
        for idx, match in enumerate(job_matches, 1):
            roles_container.markdown(f"""
            **{idx}. {match.role_title}**
            - **Confidence:** {match.confidence_score:.1%}
            - **Reasoning:** {match.reasoning}
            - **Matching Skills:** {', '.join(match.key_matching_skills[:5])}
            """)
        
        # ===== Generate Summary with REAL LLM STREAMING =====
        show_streaming_progress(
            "Generating quality assessment (LLM streaming - ~8 minutes)",
            80,
            status_placeholder,
            progress_placeholder
        )
        
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
        
        # ===== Save to Cache =====
        st.info("💾 Saving results to cache for future instant access...")
        
        doc_store.save_cached_resume(
            resume_hash=resume_hash,
            file_name=file_name,
            parsed_data=parsed_resume.model_dump(),
            job_roles=[match.model_dump() for match in job_matches],
            summary=summary.model_dump()
        )
        
        st.success("✅ Results cached - next time this resume will load instantly!")
        
        # ===== Complete =====
        show_streaming_progress(
            "Analysis complete!",
            100,
            status_placeholder,
            progress_placeholder
        )
        
        st.session_state.processed_resume = {
            'parsed_resume': parsed_resume,
            'job_role_matches': job_matches,
            'resume_summary': summary,
            'file_name': file_name,
            'current_step': 'complete',
            'error': None
        }
        
        # Cleanup
        doc_store.close()
        if temp_file_path.exists():
            temp_file_path.unlink()
        
        st.success("🎉 Resume analyzed successfully!")
        st.balloons()
        
        progress_placeholder.empty()
        status_placeholder.empty()
        
        st.info("👉 Go to **Analysis Results** tab to view detailed insights")
        
    except Exception as e:
        st.error(f"❌ Error analyzing resume: {str(e)}")
        progress_placeholder.empty()
        status_placeholder.empty()
        
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
