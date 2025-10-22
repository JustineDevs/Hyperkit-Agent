"""
Cloud-Based LLM Router
Routes requests to Google Gemini and OpenAI (cloud-based only)
"""

import os
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class HybridLLMRouter:
    """Routes requests to cloud-based AI providers: Google Gemini and OpenAI."""

    def __init__(self):
        """Initialize cloud-based AI clients."""
        self.gemini_available = False
        self.openai_available = False

        # Initialize Google Gemini
        google_key = os.getenv("GOOGLE_API_KEY")
        if (
            google_key
            and google_key.strip()
            and google_key != "your_google_api_key_here"
        ):
            try:
                import google.generativeai as genai

                genai.configure(api_key=google_key)
                self.gemini_available = True
                logger.info("Google Gemini client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Google Gemini: {e}")
        else:
            logger.warning("Google Gemini API key not found or invalid")

        # Initialize OpenAI
        openai_key = os.getenv("OPENAI_API_KEY")
        if (
            openai_key
            and openai_key.strip()
            and openai_key != "your_openai_api_key_here"
        ):
            try:
                import openai
                self.openai_client = openai.OpenAI(api_key=openai_key)
                self.openai_available = True
                logger.info("OpenAI client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI: {e}")
        else:
            logger.warning("OpenAI API key not found or invalid")

    def route(
        self, prompt: str, task_type: str = "general", prefer_local: bool = False
    ) -> str:
        """
        Route requests to available cloud-based AI providers.

        Args:
            prompt: The input prompt
            task_type: Type of task (code, reasoning, general)
            prefer_local: Ignored (cloud-based only)

        Returns:
            Generated response from available AI provider
        """
        # Try Google Gemini first (preferred for most tasks)
        if self.gemini_available:
            try:
                return self._query_gemini(prompt, task_type)
            except Exception as e:
                logger.warning(f"Google Gemini failed: {e}")
        
        # Fallback to OpenAI if Gemini fails
        if self.openai_available:
            try:
                return self._query_openai(prompt, task_type)
            except Exception as e:
                logger.warning(f"OpenAI failed: {e}")
        
        # No providers available
        raise Exception("No cloud-based AI providers available. Please check your API keys.")

    def _query_gemini(self, prompt: str, task_type: str) -> str:
        """Query Google Gemini API."""
        import google.generativeai as genai

        # Select model based on task type
        if task_type == "code":
            model_name = "gemini-2.5-pro-preview-03-25"  # Best for code generation
        else:
            model_name = "gemini-1.5-flash"  # Fast and efficient for general tasks

        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)
        return response.text

    def _query_openai(self, prompt: str, task_type: str) -> str:
        """Query OpenAI API."""
        # Select model based on task type
        if task_type == "code":
            model_name = "gpt-4o-mini"  # Good for code generation
        else:
            model_name = "gpt-3.5-turbo"  # Cost-effective for general tasks

        response = self.openai_client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4000,
            temperature=0.7
        )
        return response.choices[0].message.content

    def get_available_models(self) -> Dict[str, bool]:
        """Get status of available models."""
        return {
            "google_gemini": self.gemini_available,
            "openai": self.openai_available
        }
