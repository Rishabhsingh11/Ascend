"""Upload component utilities."""

import streamlit as st
from pathlib import Path


def handle_file_upload():
    """Handle file upload logic."""
    uploaded_file = st.file_uploader(
        "Choose a resume file",
        type=['pdf', 'docx'],
        help="Upload your resume in PDF or DOCX format"
    )
    
    return uploaded_file


def save_uploaded_file(uploaded_file):
    """Save uploaded file temporarily.
    
    Args:
        uploaded_file: Streamlit uploaded file object
        
    Returns:
        Path to saved file
    """
    temp_dir = Path("temp_uploads")
    temp_dir.mkdir(exist_ok=True)
    
    file_path = temp_dir / uploaded_file.name
    
    with open(file_path, 'wb') as f:
        f.write(uploaded_file.getbuffer())
    
    return file_path
