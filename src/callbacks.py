"""Callback handlers for streaming LLM output."""

from langchain.callbacks.base import BaseCallbackHandler
from typing import Any, Dict, List
from src.logger import get_logger


class StreamingCallbackHandler(BaseCallbackHandler):
    """Callback handler for streaming tokens from LLM."""
    
    def __init__(self):
        """Initialize the callback handler."""
        self.logger = get_logger()
        self.current_tokens = []
        self.token_count = 0
    
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
