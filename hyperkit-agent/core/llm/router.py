"""
Google Gemini Router
Routes all requests to Google Gemini only
"""

import os
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class HybridLLMRouter:
    """Routes all requests to Google Gemini only."""
    
    def __init__(self):
        """Initialize Google Gemini client only."""
        self.gemini_available = False
        
        # Initialize Google Gemini (only provider)
        google_key = os.getenv('GOOGLE_API_KEY')
        if google_key and google_key.strip() and google_key != 'your_google_api_key_here':
            try:
                import google.generativeai as genai
                genai.configure(api_key=google_key)
                self.gemini_available = True
                logger.info("Google Gemini client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Google Gemini: {e}")
        else:
            logger.warning("Google Gemini API key not found or invalid")
    
    def route(self, prompt: str, task_type: str = 'general', prefer_local: bool = True) -> str:
        """
        Route all requests to Google Gemini.
        
        Args:
            prompt: The input prompt
            task_type: Type of task (ignored, always uses Gemini)
            prefer_local: Ignored, always uses Gemini
            
        Returns:
            Generated response from Google Gemini
        """
        if not self.gemini_available:
            raise Exception("Google Gemini not available. Please check your API key.")
        
        try:
            return self._query_gemini(prompt)
        except Exception as e:
            logger.error(f"Google Gemini query failed: {e}")
            raise Exception(f"Google Gemini failed: {e}")
    
    def _query_gemini(self, prompt: str) -> str:
        """Query Google Gemini API."""
        import google.generativeai as genai
        # Use the working model we identified
        model = genai.GenerativeModel('gemini-2.5-pro-preview-03-25')
        response = model.generate_content(prompt)
        return response.text
    
    def get_available_models(self) -> Dict[str, bool]:
        """Get status of available models."""
        return {
            'google_gemini': self.gemini_available
        }