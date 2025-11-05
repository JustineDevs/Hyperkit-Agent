"""
Gemini Alith SDK Adapter
Custom adapter that makes Gemini Flash models work with Alith SDK interface.

This adapter implements the same interface as Alith SDK's Agent class,
allowing Gemini models to be used seamlessly with Alith SDK-dependent code.
"""

import logging
from typing import Optional, Dict, Any, List, Union, Callable, Mapping
import google.generativeai as genai

logger = logging.getLogger(__name__)


class GeminiAlithAdapter:
    """
    Adapter that makes Gemini Flash models compatible with Alith SDK Agent interface.
    
    This class implements the same methods as Alith SDK's Agent class,
    allowing it to be used as a drop-in replacement for Alith SDK Agent
    when using Gemini models.
    """
    
    def __init__(
        self,
        model: Optional[str] = None,
        name: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        tools: Optional[List[Any]] = None,
        mcp_config_path: Optional[str] = None,
        store: Optional[Any] = None,
        memory: Optional[Any] = None,
        extra_headers: Optional[Mapping[str, str]] = None,
        **kwargs
    ):
        """
        Initialize Gemini adapter with Alith SDK-compatible interface.
        
        Args:
            model: Gemini model name (e.g., 'gemini-2.5-flash-lite')
            name: Agent name (for compatibility, not used by Gemini)
            api_key: Google API key for Gemini
            base_url: Not used (Gemini uses fixed endpoints)
            tools: Not supported yet (future enhancement)
            mcp_config_path: Not used
            store: Not used
            memory: Not used
            extra_headers: Not used
        """
        if not api_key:
            raise ValueError("api_key is required for Gemini adapter")
        
        if not model:
            # Default to cheapest Gemini Flash model
            model = 'gemini-2.5-flash-lite'
        
        self.api_key = api_key
        self.model_name = model
        self.name = name or 'HyperKit Agent'
        
        # Configure Gemini
        try:
            genai.configure(api_key=api_key)
            self.gemini_model = genai.GenerativeModel(model)
            logger.info(f"âœ… Gemini adapter initialized: {model}")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini adapter: {e}")
            raise ValueError(f"Failed to initialize Gemini adapter: {e}")
        
        # Store compatibility attributes (for Alith SDK interface compatibility)
        self.store = store
        self.memory = memory
        self.extra_headers = extra_headers or {}
        self.tools = tools or []
        
        logger.info(f"âœ… Gemini Alith Adapter ready: {self.name} (model: {self.model_name})")
    
    def prompt(self, text: str, **kwargs) -> str:
        """
        Generate response using Gemini model.
        
        This method matches Alith SDK's Agent.prompt() interface.
        
        Args:
            text: Input prompt text
            **kwargs: Additional parameters (for compatibility)
        
        Returns:
            Generated text response from Gemini
        """
        try:
            # Generate content using Gemini
            response = self.gemini_model.generate_content(text)
            
            # Extract text from response
            if hasattr(response, 'text'):
                return response.text
            elif hasattr(response, 'parts') and len(response.parts) > 0:
                # Handle multi-part response
                return ''.join(part.text for part in response.parts if hasattr(part, 'text'))
            else:
                # Fallback: convert to string
                return str(response)
        
        except Exception as e:
            logger.error(f"Gemini adapter prompt failed: {e}")
            raise RuntimeError(f"Gemini generation failed: {e}")
    
    async def prompt_async(self, text: str, **kwargs) -> str:
        """
        Async version of prompt() for async workflows.
        
        Args:
            text: Input prompt text
            **kwargs: Additional parameters
        
        Returns:
            Generated text response from Gemini
        """
        import asyncio
        
        # Run synchronous prompt in executor
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.prompt, text)
    
    def __getattr__(self, name: str):
        """
        Forward any missing attributes for compatibility.
        
        This allows the adapter to work with code that expects
        Alith SDK Agent attributes that we don't implement.
        """
        # Return None for unknown attributes (many Alith SDK features)
        if name.startswith('_'):
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
        
        logger.debug(f"Gemini adapter: {name} attribute not found, returning None for compatibility")
        return None
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"GeminiAlithAdapter(name={self.name}, model={self.model_name})"
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the Gemini model being used."""
        return {
            "provider": "google",
            "model": self.model_name,
            "adapter": "GeminiAlithAdapter",
            "name": self.name
        }

