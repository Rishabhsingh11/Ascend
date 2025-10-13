"""Demo app to test streaming in Streamlit."""

import streamlit as st
import sys
from pathlib import Path
import time

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.UI.streaming_utils import StreamlitTokenHandler

st.set_page_config(page_title="Streaming Demo", layout="wide")

st.title("🚀 LLM Streaming Demo")

# Test 1: Simple streaming simulation
st.header("Test 1: Basic Streaming")

if st.button("Run Basic Stream Test"):
    placeholder = st.empty()
    
    test_text = "This is a test of the streaming functionality. Each character appears one by one, simulating LLM token generation."
    
    accumulated = ""
    for char in test_text:
        accumulated += char
        placeholder.markdown(accumulated)
        time.sleep(0.05)
    
    st.success("✅ Basic streaming works!")

# Test 2: Multiple containers
st.header("Test 2: Multiple Streaming Sections")

if st.button("Run Multi-Section Test"):
    with st.expander("📄 Section 1", expanded=True):
        container1 = st.container()
    
    with st.expander("🎯 Section 2", expanded=True):
        container2 = st.container()
    
    # Stream to section 1
    placeholder1 = container1.empty()
    text1 = "Streaming to first section..."
    acc1 = ""
    for char in text1:
        acc1 += char
        placeholder1.markdown(acc1)
        time.sleep(0.05)
    
    container1.success("✅ Section 1 complete")
    
    # Stream to section 2
    placeholder2 = container2.empty()
    text2 = "Streaming to second section..."
    acc2 = ""
    for char in text2:
        acc2 += char
        placeholder2.markdown(acc2)
        time.sleep(0.05)
    
    container2.success("✅ Section 2 complete")

# Test 3: Real LLM streaming
st.header("Test 3: Real LLM Streaming")

if st.button("Run Real LLM Test"):
    from src.UI.streaming_utils import StreamlitTokenHandler, create_analysis_section
    from src.agent import JobSearchAgent
    from src.state import ParsedResume, ContactInfo
    
    expander, container = create_analysis_section("🤖 LLM Response", expanded=True)
    
    # Create dummy resume
    dummy_contact = ContactInfo(name="John Doe", email="john@test.cpom")
    dummy_resume = ParsedResume(
        contact_info=dummy_contact,
        skills=["Python", "SQL"],
        experience=[],
        education=[]
    )
    
    state = {
        'messages': [],
        'file_id': 'test',
        'file_name': 'test.pdf',
        'raw_resume_text': 'Test content',
        'parsed_resume': dummy_resume,
        'job_role_matches': None,
        'resume_summary': None,
        'current_step': 'parsing_complete',
        'error': None
    }
    
    # Setup handler
    handler = StreamlitTokenHandler(container, prefix="🤖 AI Thinking...")
    
    # Run streaming analysis
    agent = JobSearchAgent()
    result = agent._analyze_job_roles_streaming(state, token_callback=handler.on_token)
    
    # Finalize
    handler.clear()
    
    if result.get('error'):
        container.error(f"❌ Error: {result['error']}")
    else:
        container.success("✅ LLM streaming complete!")
        container.json(result.get('job_role_matches', []))
