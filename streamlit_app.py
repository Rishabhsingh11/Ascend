"""Streamlit entry point for Ascend Resume Analyzer."""

import streamlit as st
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.UI.app import main

if __name__ == "__main__":
    main()
