"""
Intelligent Model Selection Service
Automatically selects the best AI model based on token usage, cost optimization, and availability.
Optimizes for Gemini models (cheaper) while maintaining quality.
"""

import logging
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ModelTier(Enum):
    """Model tiers for cost/performance optimization"""
    LITE = "lite"  # Cheapest, fastest
    FLASH = "flash"  # Balanced
    PRO = "pro"  # Most capable, expensive


@dataclass
class ModelSpec:
    """Model specification with token limits and metadata"""
    name: str
    provider: str  # "google", "openai", etc.
    tier: ModelTier
    input_tokens: int  # Maximum input tokens
    output_tokens: int  # Maximum output tokens
    cost_per_1k_input: float = 0.0  # Cost per 1K input tokens
    cost_per_1k_output: float = 0.0  # Cost per 1K output tokens
    enabled: bool = True
    priority: int = 0  # Lower = higher priority for selection


class ModelSelector:
    """
    Intelligent model selector that optimizes for:
    1. Token usage (select cheapest model that can handle the task)
    2. Cost efficiency (prefer Gemini Flash/Lite models)
    3. Automatic fallback when limits are exceeded
    """
    
    # Gemini models with token limits (from user's data)
    GEMINI_MODELS = {
        "gemini-2.5-pro": ModelSpec(
            name="gemini-2.5-pro",
            provider="google",
            tier=ModelTier.PRO,
            input_tokens=240_000_000,
            output_tokens=30_000_000,
            cost_per_1k_input=0.001,  # Estimated
            cost_per_1k_output=0.002,  # Estimated
            priority=3  # Higher cost, use as fallback
        ),
        "gemini-2.5-flash": ModelSpec(
            name="gemini-2.5-flash",
            provider="google",
            tier=ModelTier.FLASH,
            input_tokens=1_000_000_000,
            output_tokens=120_000_000,
            cost_per_1k_input=0.0001,  # Cheaper
            cost_per_1k_output=0.0003,  # Cheaper
            priority=2  # Good balance
        ),
        "gemini-2.5-flash-lite": ModelSpec(
            name="gemini-2.5-flash-lite",
            provider="google",
            tier=ModelTier.LITE,
            input_tokens=3_000_000_000,
            output_tokens=750_000_000,
            cost_per_1k_input=0.00005,  # Cheapest
            cost_per_1k_output=0.0001,  # Cheapest
            priority=1  # Highest priority (cheapest)
        ),
        "gemini-2.0-flash": ModelSpec(
            name="gemini-2.0-flash",
            provider="google",
            tier=ModelTier.FLASH,
            input_tokens=2_000_000_000,
            output_tokens=500_000_000,
            cost_per_1k_input=0.00008,
            cost_per_1k_output=0.0002,
            priority=2
        ),
        "gemini-2.0-flash-lite": ModelSpec(
            name="gemini-2.0-flash-lite",
            provider="google",
            tier=ModelTier.LITE,
            input_tokens=4_000_000_000,
            output_tokens=1_000_000_000,
            cost_per_1k_input=0.00004,  # Very cheap
            cost_per_1k_output=0.00008,  # Very cheap
            priority=1  # Highest priority
        ),
    }
    
    # OpenAI models (fallback)
    OPENAI_MODELS = {
        "gpt-4o-mini": ModelSpec(
            name="gpt-4o-mini",
            provider="openai",
            tier=ModelTier.FLASH,
            input_tokens=128_000,
            output_tokens=16_000,
            cost_per_1k_input=0.00015,
            cost_per_1k_output=0.0006,
            priority=4  # Fallback only
        ),
        "gpt-3.5-turbo": ModelSpec(
            name="gpt-3.5-turbo",
            provider="openai",
            tier=ModelTier.LITE,
            input_tokens=16_385,
            output_tokens=4_096,
            cost_per_1k_input=0.0005,
            cost_per_1k_output=0.0015,
            priority=5  # Last resort
        ),
    }
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize model selector with configuration"""
        self.config = config or {}
        self.available_models: Dict[str, ModelSpec] = {}
        self.token_usage_history: Dict[str, List[int]] = {}  # Track usage per model
        self._load_available_models()
    
    def _load_available_models(self):
        """Load available models from config and environment"""
        import os
        
        # Check Google/Gemini availability
        # Check config first, then fall back to environment variable
        google_key = None
        if self.config:
            # Try multiple config paths where the key might be stored
            google_key = (
                self.config.get("GOOGLE_API_KEY") or
                self.config.get("google_api_key") or
                self.config.get("google", {}).get("api_key") or
                self.config.get("ai_providers", {}).get("google", {}).get("api_key")
            )
        
        # Fall back to environment variable if not in config
        if not google_key:
            google_key = os.getenv("GOOGLE_API_KEY")
        
        if google_key and google_key.strip() and google_key != "your_google_api_key_here":
            for model_name, spec in self.GEMINI_MODELS.items():
                self.available_models[model_name] = spec
            logger.info(f"✅ Loaded {len(self.GEMINI_MODELS)} Gemini models")
        
        # Check OpenAI availability (fallback)
        # Check config first, then fall back to environment variable
        openai_key = None
        if self.config:
            # Try multiple config paths where the key might be stored
            openai_key = (
                self.config.get("OPENAI_API_KEY") or
                self.config.get("openai_api_key") or
                self.config.get("openai", {}).get("api_key") or
                self.config.get("ai_providers", {}).get("openai", {}).get("api_key")
            )
        
        # Fall back to environment variable if not in config
        if not openai_key:
            openai_key = os.getenv("OPENAI_API_KEY")
        
        if openai_key and openai_key.strip() and openai_key != "your_openai_api_key_here":
            for model_name, spec in self.OPENAI_MODELS.items():
                self.available_models[model_name] = spec
            logger.info(f"✅ Loaded {len(self.OPENAI_MODELS)} OpenAI models (fallback)")
    
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text.
        Simple estimation: ~4 characters per token for code, ~3 for natural language.
        """
        # For code/contracts, assume more tokens
        if any(keyword in text.lower() for keyword in ['pragma', 'contract', 'function', 'solidity']):
            return len(text) // 3  # ~3 chars per token for Solidity
        return len(text) // 4  # ~4 chars per token for natural language
    
    def select_best_model(
        self,
        estimated_input_tokens: int,
        estimated_output_tokens: int,
        task_type: str = "general",
        prefer_cheap: bool = True
    ) -> Tuple[Optional[str], Optional[ModelSpec]]:
        """
        Select the best model based on token requirements and cost optimization.
        
        Args:
            estimated_input_tokens: Estimated input token count
            estimated_output_tokens: Estimated output token count
            task_type: Type of task (code, general, analysis)
            prefer_cheap: Prefer cheaper models when possible
        
        Returns:
            Tuple of (model_name, ModelSpec) or (None, None) if no suitable model
        """
        # Filter models that can handle the token requirements
        suitable_models = []
        
        for model_name, spec in self.available_models.items():
            if not spec.enabled:
                continue
            
            # Check if model can handle input/output tokens
            if estimated_input_tokens > spec.input_tokens:
                continue
            if estimated_output_tokens > spec.output_tokens:
                continue
            
            # Calculate estimated cost
            estimated_cost = (
                (estimated_input_tokens / 1000) * spec.cost_per_1k_input +
                (estimated_output_tokens / 1000) * spec.cost_per_1k_output
            )
            
            suitable_models.append({
                "name": model_name,
                "spec": spec,
                "cost": estimated_cost,
                "priority": spec.priority,
                "tier": spec.tier
            })
        
        if not suitable_models:
            logger.error(f"❌ No suitable model found for {estimated_input_tokens} input / {estimated_output_tokens} output tokens")
            # Try to find best fallback (largest capacity)
            fallback = max(
                self.available_models.items(),
                key=lambda x: min(x[1].input_tokens, x[1].output_tokens),
                default=(None, None)
            )
            if fallback[0]:
                logger.warning(f"⚠️  Using fallback model: {fallback[0]} (may exceed limits)")
                return fallback
            return None, None
        
        # Sort by priority (lower = better), then by cost
        if prefer_cheap:
            suitable_models.sort(key=lambda x: (x["priority"], x["cost"]))
        else:
            suitable_models.sort(key=lambda x: (x["priority"], -x["cost"]))
        
        best = suitable_models[0]
        model_name = best["name"]
        spec = best["spec"]
        
        logger.info(
            f"✅ Selected model: {model_name} "
            f"(tier: {spec.tier.value}, cost: ${best['cost']:.6f}, "
            f"capacity: {spec.input_tokens:,} input / {spec.output_tokens:,} output)"
        )
        
        return model_name, spec
    
    def auto_select_for_prompt(
        self,
        prompt: str,
        expected_output_length: Optional[int] = None,
        task_type: str = "general"
    ) -> Tuple[Optional[str], Optional[ModelSpec], Dict[str, int]]:
        """
        Automatically select model based on prompt analysis.
        
        Args:
            prompt: Input prompt text
            expected_output_length: Expected output length in characters (optional)
            task_type: Type of task (code, general, analysis)
        
        Returns:
            Tuple of (model_name, ModelSpec, token_estimates)
        """
        # Estimate tokens
        input_tokens = self.estimate_tokens(prompt)
        if expected_output_length:
            output_tokens = self.estimate_tokens(" " * expected_output_length)
        else:
            # Default estimation based on task type
            if task_type == "code":
                output_tokens = 2000  # Typical contract length
            elif task_type == "analysis":
                output_tokens = 1000
            else:
                output_tokens = 500
        
        token_estimates = {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens
        }
        
        # Select best model
        model_name, spec = self.select_best_model(
            input_tokens,
            output_tokens,
            task_type=task_type,
            prefer_cheap=True
        )
        
        return model_name, spec, token_estimates
    
    def record_usage(self, model_name: str, input_tokens: int, output_tokens: int):
        """Record actual token usage for model"""
        if model_name not in self.token_usage_history:
            self.token_usage_history[model_name] = []
        
        self.token_usage_history[model_name].append(input_tokens + output_tokens)
        
        # Keep only last 100 records per model
        if len(self.token_usage_history[model_name]) > 100:
            self.token_usage_history[model_name] = self.token_usage_history[model_name][-100:]
    
    def get_usage_stats(self) -> Dict[str, Dict]:
        """Get token usage statistics per model"""
        stats = {}
        for model_name, usage_list in self.token_usage_history.items():
            if usage_list:
                stats[model_name] = {
                    "total_requests": len(usage_list),
                    "avg_tokens": sum(usage_list) / len(usage_list),
                    "total_tokens": sum(usage_list),
                    "min_tokens": min(usage_list),
                    "max_tokens": max(usage_list)
                }
        return stats
    
    def rotate_model(self, task_type: str = "general") -> Optional[str]:
        """
        Rotate to next available model for load balancing.
        Currently returns cheapest suitable model (future: round-robin).
        """
        models_by_tier = {
            ModelTier.LITE: [],
            ModelTier.FLASH: [],
            ModelTier.PRO: []
        }
        
        for model_name, spec in self.available_models.items():
            if spec.enabled:
                models_by_tier[spec.tier].append(model_name)
        
        # Prefer LITE > FLASH > PRO for rotation
        for tier in [ModelTier.LITE, ModelTier.FLASH, ModelTier.PRO]:
            if models_by_tier[tier]:
                selected = models_by_tier[tier][0]
                logger.info(f"🔄 Rotated to model: {selected} (tier: {tier.value})")
                return selected
        
        return None

