"""Callback handlers for streaming LLM output."""

from langchain.callbacks.base import BaseCallbackHandler
from typing import Any, Dict, List
from src.logger import get_logger


class StreamingCallbackHandler(BaseCallbackHandler):
    """Callback handler for streaming tokens from LLM."""
    
    def __init__(self,streamlit_container=None, on_token_callback=None):
        """Initialize the callback handler.
        
        Args:
            streamlit_container: Optional Streamlit container for UI updates (DEPRECATED - use on_token_callback)
            on_token_callback: Optional callback function(token: str) -> None for custom handling
        """
        self.logger = get_logger()
        self.current_tokens = []
        self.token_count = 0

        # NEW: Support for callback function (more flexible than container)
        self.on_token_callback = on_token_callback
        
        # Legacy support for container
        self.streamlit_container = streamlit_container
        self.placeholder = None
        
        if self.streamlit_container:
            try:
                import streamlit as st
                self.placeholder = self.streamlit_container.empty()
            except ImportError:
                self.logger.warning("Streamlit not available for streaming")
    
    def on_llm_start(
        self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any
    ) -> None:
        """Run when LLM starts running."""
        self.logger.info("🤖 LLM started generating response...")
        self.logger.debug(f"Prompt preview: {prompts[0][:200]}...")
        self.current_tokens = []
        self.token_count = 0
    
    def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        """Run on new LLM token. Only available when streaming is enabled."""
        # Print token to console for real-time streaming
        print(token, end='', flush=True)
        self.current_tokens.append(token)
        self.token_count += 1

        # NEW: Call custom callback if provided
        if self.on_token_callback:
            try:
                self.on_token_callback(token)
            except Exception as e:
                self.logger.error(f"Token callback error: {e}")
        
        # Legacy: Update Streamlit placeholder (less flexible)
        elif self.placeholder:
            try:
                accumulated = ''.join(self.current_tokens)
                self.placeholder.markdown(accumulated)
            except Exception as e:
                self.logger.error(f"Streamlit update error: {e}")
    
    def on_llm_end(self, response: Any, **kwargs: Any) -> None:
        """Run when LLM ends running."""
        print()  # New line after streaming
        full_response = ''.join(self.current_tokens)
        self.logger.info(f"✅ LLM finished. Tokens generated: {self.token_count}")
        self.logger.debug(f"Full response length: {len(full_response)} characters")
    
    def on_llm_error(self, error: Exception, **kwargs: Any) -> None:
        """Run when LLM errors."""
        self.logger.error(f"LLM error: {str(error)}")
    
    def on_chain_start(
        self, serialized: Dict[str, Any], inputs: Dict[str, Any], **kwargs: Any
    ) -> None:
        """Run when chain starts running."""
        chain_name = serialized.get("name", "Unknown")
        self.logger.debug(f"Chain started: {chain_name}")
    
    def on_chain_end(self, outputs: Dict[str, Any], **kwargs: Any) -> None:
        """Run when chain ends running."""
        self.logger.debug("Chain completed")
    
    def on_chain_error(self, error: Exception, **kwargs: Any) -> None:
        """Run when chain errors."""
        self.logger.error(f"Chain error: {str(error)}")
    
    def on_tool_start(
        self, serialized: Dict[str, Any], input_str: str, **kwargs: Any
    ) -> None:
        """Run when tool starts running."""
        tool_name = serialized.get("name", "Unknown")
        self.logger.info(f"🔧 Tool started: {tool_name}")
    
    def on_tool_end(self, output: str, **kwargs: Any) -> None:
        """Run when tool ends running."""
        self.logger.debug(f"Tool output: {output[:100]}...")
    
    def on_tool_error(self, error: Exception, **kwargs: Any) -> None:
        """Run when tool errors."""
        self.logger.error(f"Tool error: {str(error)}")

    def get_accumulated_text(self) -> str:
            """Get the accumulated text from all tokens.
            
            Returns:
                Complete text from all streamed tokens
            """
            return ''.join(self.current_tokens)
    
    def reset(self):
        """Reset token accumulator for new generation."""
        self.current_tokens = []
        self.token_count = 0