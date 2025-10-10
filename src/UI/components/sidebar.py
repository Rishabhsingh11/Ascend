"""Sidebar navigation component."""

import streamlit as st
from src.UI.components.cache_viewer import render_sidebar_cache_info


def render_sidebar():
    """Render sidebar with app information and settings."""
    
    with st.sidebar:
        st.image("https://via.placeholder.com/150x150.png?text=Ascend", width=150)
        
        st.markdown("---")
        
        st.markdown("### 🚀 Quick Stats")
        render_sidebar_cache_info()
        
        st.markdown("---")
        
        st.markdown("### ⚙️ Settings")
        
        # Model selection
        model = st.selectbox(
            "LLM Model",
            ["mistral", "llama2", "codellama"],
            help="Select the Ollama model to use"
        )
        
        # Temperature
        temperature = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=1.0,
            value=0.1,
            step=0.1,
            help="Lower = more deterministic, Higher = more creative"
        )
        
        st.markdown("---")
        
        st.markdown("### 📖 Resources")
        st.markdown("[📚 Documentation](https://github.com/Rishabhsingh11/Ascend-)")
        st.markdown("[🐛 Report Issue](https://github.com/Rishabhsingh11/Ascend-/issues)")
        st.markdown("[⭐ Star on GitHub](https://github.com/Rishabhsingh11/Ascend-)")
        
        st.markdown("---")
        
        st.markdown("### 👨‍💻 Developer")
        st.markdown("**Rishabh Dinesh Singh**")
        st.markdown("[LinkedIn](https://linkedin.com/in/rishabhdineshsingh)")
