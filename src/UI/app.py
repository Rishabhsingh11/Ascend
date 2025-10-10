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
        temp_path = Path(f"temp_{uploaded_file.name}")
        with open(temp_path, 'wb') as f:
            f.write(uploaded_file.getbuffer())
        
        if st.button("🚀 Analyze Resume", type="primary", width='stretch'):
            analyze_resume(str(temp_path), uploaded_file.name)


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
    """Analyze resume from Google Drive."""
    
    # Progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Initialize agent if not exists
        if st.session_state.agent is None:
            status_text.text("🤖 Initializing AI Agent...")
            progress_bar.progress(10)
            st.session_state.agent = JobSearchAgent()
        
        status_text.text("📥 Downloading from Google Drive...")
        progress_bar.progress(30)
        
        # Download file
        drive_handler = st.session_state.drive_handler
        file_content = drive_handler.download_file(file_id, file_name)
        
        status_text.text("📄 Processing resume...")
        progress_bar.progress(60)
        
        # Process resume using the agent's process_resume method
        result = st.session_state.agent.process_resume(
            file_id=file_id,
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
        st.exception(e)  # Show full traceback
        progress_bar.empty()
        status_text.empty()



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
