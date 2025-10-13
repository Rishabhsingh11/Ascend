"""Utilities for handling LLM streaming in Streamlit."""

import streamlit as st
from datetime import time
from typing import Callable, Any


class StreamlitTokenHandler:
    """Handle LLM token streaming in Streamlit UI."""
    
    def __init__(self, container, prefix=""):
        """Initialize handler.
        
        Args:
            container: Streamlit container to display tokens
            prefix: Optional prefix text to show before tokens
        """
        self.container = container
        self.prefix = prefix
        self.accumulated_text = ""
        self.placeholder = container.empty()
        
        # Display prefix if provided
        if prefix:
            self.placeholder.markdown(f"**{prefix}**\n\n")
    
    def on_token(self, token: str):
        """Callback for each new token.
        
        Args:
            token: New token from LLM
        """
        self.accumulated_text += token
        
        # Update display with accumulated text
        display_text = f"**{self.prefix}**\n\n{self.accumulated_text}" if self.prefix else self.accumulated_text
        self.placeholder.markdown(display_text)
    
    def finalize(self, final_text: str = None):
        """Finalize streaming and display complete text.
        
        Args:
            final_text: Optional final text to display (uses accumulated if not provided)
        """
        text_to_display = final_text if final_text else self.accumulated_text
        
        if self.prefix:
            self.placeholder.markdown(f"**{self.prefix}**\n\n{text_to_display}")
        else:
            self.placeholder.markdown(text_to_display)
    
    def clear(self):
        """Clear the display."""
        self.placeholder.empty()

def simulate_streaming_from_cache(
    container,
    cached_text: str,
    prefix: str = "",
    chars_per_token: int = 4,
    delay_ms: int = 30
):
    """Simulate LLM streaming by displaying cached text gradually.
    
    This creates the illusion of streaming for cached results,
    providing immediate feedback while maintaining UX consistency.
    
    Args:
        container: Streamlit container to display in
        cached_text: Pre-generated text from cache
        prefix: Optional prefix text
        chars_per_token: Characters per simulated token (controls speed)
        delay_ms: Delay between tokens in milliseconds
        
    Returns:
        Complete cached text
    """
    import time
    
    placeholder = container.empty()
    
    # Display prefix
    if prefix:
        placeholder.markdown(f"**{prefix}**\n\n")
        time.sleep(0.3)
    
    # Simulate token-by-token display
    accumulated = ""
    for i in range(0, len(cached_text), chars_per_token):
        accumulated = cached_text[:i + chars_per_token]
        
        if prefix:
            placeholder.markdown(f"**{prefix}**\n\n{accumulated}")
        else:
            placeholder.markdown(accumulated)
        
        time.sleep(delay_ms / 1000.0)  # Convert to seconds
    
    # Ensure complete text is displayed
    if prefix:
        placeholder.markdown(f"**{prefix}**\n\n{cached_text}")
    else:
        placeholder.markdown(cached_text)
    
    return cached_text


def create_analysis_section(title: str, icon: str = "🤖", expanded: bool = True):
    """Create an expandable section for LLM analysis.
    
    Args:
        title: Section title
        icon: Icon to display
        expanded: Whether section starts expanded
        
    Returns:
        Tuple of (expander, container) for streaming
    """
    expander = st.expander(f"{icon} {title}", expanded=expanded)
    container = expander.container()
    
    return expander, container


def show_streaming_progress(
    step_name: str,
    progress_value: int,
    status_placeholder,
    progress_placeholder
):
    """Update streaming progress indicators.
    
    Args:
        step_name: Name of current step
        progress_value: Progress percentage (0-100)
        status_placeholder: Streamlit placeholder for status text
        progress_placeholder: Streamlit placeholder for progress bar
    """
    status_placeholder.text(f"⚡ {step_name}...")
    progress_placeholder.progress(progress_value)
