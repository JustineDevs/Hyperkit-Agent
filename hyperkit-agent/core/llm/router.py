"""
Cloud-Based LLM Router with Intelligent Model Selection
Routes requests to Google Gemini and OpenAI with automatic model selection based on token optimization.
"""

import os
import logging
from typing import Optional, Dict, Any

from .model_selector import ModelSelector

logger = logging.getLogger(__name__)


class HybridLLMRouter:
    """Routes requests to cloud-based AI providers: Google Gemini and OpenAI."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize cloud-based AI clients with intelligent model selection."""
        self.config = config or {}
        self.gemini_available = False
        self.openai_available = False
        self.alith_available = False
        
        # Initialize intelligent model selector
        self.model_selector = ModelSelector(config)

        # Initialize Google Gemini
        # Check config first, then fall back to environment variable
        google_key = None
        if self.config:
            # Try multiple config paths where the key might be stored
            google_key = (
                self.config.get("GOOGLE_API_KEY") or
                self.config.get("google_api_key") or
                self.config.get("ai_providers", {}).get("google", {}).get("api_key")
            )
        
        # Fall back to environment variable if not in config
        if not google_key:
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
                logger.info(f"✅ Google Gemini client initialized (key found in config: {bool(self.config.get('GOOGLE_API_KEY') or self.config.get('ai_providers', {}).get('google', {}).get('api_key'))})")
            except Exception as e:
                logger.warning(f"❌ Failed to initialize Google Gemini: {e}")
                self.gemini_available = False
        else:
            logger.warning("⚠️ Google Gemini API key not found or invalid")
            logger.debug(f"  - Config GOOGLE_API_KEY: {bool(self.config.get('GOOGLE_API_KEY'))}")
            logger.debug(f"  - Config ai_providers.google.api_key: {bool(self.config.get('ai_providers', {}).get('google', {}).get('api_key'))}")
            logger.debug(f"  - Env GOOGLE_API_KEY: {bool(os.getenv('GOOGLE_API_KEY'))}")

        # Initialize OpenAI
        # Check config first, then fall back to environment variable
        openai_key = None
        if self.config:
            # Try multiple config paths where the key might be stored
            openai_key = (
                self.config.get("OPENAI_API_KEY") or
                self.config.get("openai_api_key") or
                self.config.get("ai_providers", {}).get("openai", {}).get("api_key")
            )
        
        # Fall back to environment variable if not in config
        if not openai_key:
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
        
        # Initialize Alith SDK (NEW)
        alith_config = self.config.get("alith", {})
        # Alith SDK integration - use directly (services.alith is just a stub)
        if alith_config.get("enabled", False) or self.config.get("ALITH_ENABLED", False):
            if openai_key:  # Alith requires OpenAI key
                try:
                    from alith import Agent
                    self.alith_agent = Agent(api_key=openai_key)
                    self.alith_available = True
                    logger.info("✅ Alith AI agent initialized for advanced auditing")
                except ImportError:
                    logger.warning("Alith SDK not installed. Install with: pip install alith>=0.12.0")
                    logger.warning("Advanced AI features will use fallback LLM only")
                    self.alith_available = False
                except Exception as e:
                    logger.warning(f"Failed to initialize Alith: {e}")
                    self.alith_available = False
            else:
                logger.warning("Alith SDK requires OPENAI_API_KEY - using fallback LLM only")
                self.alith_available = False
        else:
            self.alith_available = False

    def route(
        self, prompt: str, task_type: str = "general", prefer_local: bool = False,
        expected_output_length: Optional[int] = None
    ) -> str:
        """
        Route requests to available cloud-based AI providers with intelligent model selection.

        Args:
            prompt: The input prompt
            task_type: Type of task (code, reasoning, general)
            prefer_local: Ignored (cloud-based only)
            expected_output_length: Expected output length in characters (for token estimation)

        Returns:
            Generated response from available AI provider
        """
        # Auto-select best model based on token usage
        model_name, model_spec, token_estimates = self.model_selector.auto_select_for_prompt(
            prompt=prompt,
            expected_output_length=expected_output_length,
            task_type=task_type
        )
        
        if not model_name or not model_spec:
            logger.error("❌ No suitable model found, falling back to basic selection")
            return self._route_fallback(prompt, task_type)
        
        logger.info(
            f"📊 Token estimates: {token_estimates['input_tokens']} input / "
            f"{token_estimates['output_tokens']} output (total: {token_estimates['total_tokens']})"
        )
        
        # Route to selected model
        try:
            if model_spec.provider == "google":
                response = self._query_gemini_with_model(prompt, model_name, task_type)
                # Record usage (estimate actual tokens from response)
                actual_output_tokens = self.model_selector.estimate_tokens(response)
                self.model_selector.record_usage(
                    model_name,
                    token_estimates['input_tokens'],
                    actual_output_tokens
                )
                return response
            elif model_spec.provider == "openai":
                response = self._query_openai_with_model(prompt, model_name, task_type)
                actual_output_tokens = self.model_selector.estimate_tokens(response)
                self.model_selector.record_usage(
                    model_name,
                    token_estimates['input_tokens'],
                    actual_output_tokens
                )
                return response
        except Exception as e:
            logger.warning(f"❌ Model {model_name} failed: {e}, trying fallback")
            # Fallback to basic routing
            return self._route_fallback(prompt, task_type)
    
    def _route_fallback(self, prompt: str, task_type: str) -> str:
        """Fallback routing when model selection fails"""
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
        """Query Google Gemini API with basic model selection."""
        import google.generativeai as genai

        # Select model based on task type (legacy method)
        if task_type == "code":
            model_name = "gemini-2.5-pro"  # Best for code generation
        else:
            model_name = "gemini-2.5-flash"  # Fast and efficient for general tasks

        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            # Try fallback models if primary fails
            logger.warning(f"Model {model_name} failed: {e}, trying fallback")
            fallback_models = ["gemini-2.5-flash-lite", "gemini-2.0-flash-lite", "gemini-1.5-flash"]
            for fallback in fallback_models:
                try:
                    model = genai.GenerativeModel(fallback)
                    response = model.generate_content(prompt)
                    logger.info(f"✅ Fallback model {fallback} succeeded")
                    return response.text
                except Exception:
                    continue
            raise e
    
    def _query_gemini_with_model(self, prompt: str, model_name: str, task_type: str) -> str:
        """Query Google Gemini API with specific model."""
        import google.generativeai as genai

        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)
        return response.text

    def _query_openai(self, prompt: str, task_type: str) -> str:
        """Query OpenAI API with basic model selection."""
        # Select model based on task type (legacy method)
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
    
    def _query_openai_with_model(self, prompt: str, model_name: str, task_type: str) -> str:
        """Query OpenAI API with specific model."""
        # Estimate max tokens based on model limits
        model_spec = self.model_selector.available_models.get(model_name)
        max_tokens = model_spec.output_tokens if model_spec else 4000
        
        response = self.openai_client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=min(max_tokens, 16000),  # Cap at reasonable limit
            temperature=0.7
        )
        return response.choices[0].message.content

    def get_available_models(self) -> Dict[str, bool]:
        """Get status of available models."""
        return {
            "google_gemini": self.gemini_available,
            "openai": self.openai_available
        }
    
    def get_model_stats(self) -> Dict:
        """Get token usage statistics for all models."""
        return self.model_selector.get_usage_stats()
    
    def get_model_selector(self) -> ModelSelector:
        """Get the model selector instance for advanced usage."""
        return self.model_selector
