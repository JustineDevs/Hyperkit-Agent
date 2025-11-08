"""
Model Performance Tracker
Tracks success/failure rates per model for intelligent rotation and weighted selection.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict, field

logger = logging.getLogger(__name__)


@dataclass
class ModelPerformance:
    """Performance metrics for a single model"""
    model_name: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_tokens_used: int = 0
    avg_response_time_ms: float = 0.0
    last_used: Optional[str] = None
    consecutive_failures: int = 0
    success_rate: float = 0.0
    
    def update_success(self, tokens_used: int = 0, response_time_ms: float = 0.0):
        """Update metrics on successful request"""
        self.total_requests += 1
        self.successful_requests += 1
        self.total_tokens_used += tokens_used
        self.consecutive_failures = 0
        self.last_used = datetime.utcnow().isoformat()
        self.success_rate = self.successful_requests / self.total_requests if self.total_requests > 0 else 0.0
        
        # Update average response time (exponential moving average)
        if self.avg_response_time_ms == 0.0:
            self.avg_response_time_ms = response_time_ms
        else:
            self.avg_response_time_ms = (self.avg_response_time_ms * 0.9) + (response_time_ms * 0.1)
    
    def update_failure(self, tokens_used: int = 0):
        """Update metrics on failed request"""
        self.total_requests += 1
        self.failed_requests += 1
        self.total_tokens_used += tokens_used
        self.consecutive_failures += 1
        self.last_used = datetime.utcnow().isoformat()
        self.success_rate = self.successful_requests / self.total_requests if self.total_requests > 0 else 0.0


class ModelPerformanceTracker:
    """
    Tracks model performance for intelligent rotation and weighted selection.
    """
    
    def __init__(self, workspace_dir: Path):
        """
        Initialize performance tracker.
        
        Args:
            workspace_dir: Base workspace directory
        """
        self.workspace_dir = Path(workspace_dir)
        self.performance_file = self.workspace_dir / ".workflow_contexts" / "model_performance.json"
        self.performance: Dict[str, ModelPerformance] = {}
        
        # Load existing performance data
        self._load_performance()
    
    def _load_performance(self):
        """Load performance data from disk"""
        if self.performance_file.exists():
            try:
                with open(self.performance_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.performance = {
                        model_name: ModelPerformance(**perf_data)
                        for model_name, perf_data in data.get('models', {}).items()
                    }
                logger.debug(f"Loaded performance data for {len(self.performance)} models")
            except Exception as e:
                logger.warning(f"Failed to load model performance data: {e}")
                self.performance = {}
        else:
            self.performance = {}
    
    def _save_performance(self):
        """Save performance data to disk"""
        try:
            self.performance_file.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "version": "1.0",
                "last_updated": datetime.utcnow().isoformat(),
                "models": {
                    model_name: asdict(perf)
                    for model_name, perf in self.performance.items()
                }
            }
            with open(self.performance_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            logger.debug(f"Saved performance data for {len(self.performance)} models")
        except Exception as e:
            logger.warning(f"Failed to save model performance data: {e}")
    
    def record_success(
        self,
        model_name: str,
        tokens_used: int = 0,
        response_time_ms: float = 0.0
    ):
        """
        Record a successful model request.
        
        Args:
            model_name: Name of the model used
            tokens_used: Number of tokens consumed
            response_time_ms: Response time in milliseconds
        """
        if model_name not in self.performance:
            self.performance[model_name] = ModelPerformance(model_name=model_name)
        
        self.performance[model_name].update_success(tokens_used, response_time_ms)
        self._save_performance()
        logger.debug(f"Recorded success for {model_name} (success rate: {self.performance[model_name].success_rate:.2%})")
    
    def record_failure(self, model_name: str, tokens_used: int = 0):
        """
        Record a failed model request.
        
        Args:
            model_name: Name of the model used
            tokens_used: Number of tokens consumed (if any)
        """
        if model_name not in self.performance:
            self.performance[model_name] = ModelPerformance(model_name=model_name)
        
        self.performance[model_name].update_failure(tokens_used)
        self._save_performance()
        logger.debug(f"Recorded failure for {model_name} (consecutive failures: {self.performance[model_name].consecutive_failures})")
    
    def get_performance(self, model_name: str) -> Optional[ModelPerformance]:
        """Get performance metrics for a model"""
        return self.performance.get(model_name)
    
    def get_weighted_score(self, model_name: str) -> float:
        """
        Calculate weighted score for model selection.
        Higher score = better choice.
        
        Factors:
        - Success rate (0.0 to 1.0) - weight: 0.5
        - Consecutive failures penalty - weight: 0.3
        - Recent usage (prefer less recently used) - weight: 0.2
        """
        if model_name not in self.performance:
            return 1.0  # New models get default score
        
        perf = self.performance[model_name]
        
        # Success rate component (0.0 to 1.0)
        success_component = perf.success_rate
        
        # Consecutive failures penalty (exponential decay)
        failure_penalty = 1.0 / (1.0 + perf.consecutive_failures * 0.5)
        
        # Recent usage component (prefer models not used recently)
        recent_usage_score = 1.0
        if perf.last_used:
            try:
                last_used_time = datetime.fromisoformat(perf.last_used.replace('Z', '+00:00'))
                hours_since_use = (datetime.utcnow() - last_used_time.replace(tzinfo=None)).total_seconds() / 3600
                # Prefer models not used in last 24 hours
                recent_usage_score = min(1.0, hours_since_use / 24.0)
            except Exception:
                pass
        
        # Weighted combination
        weighted_score = (
            success_component * 0.5 +
            failure_penalty * 0.3 +
            recent_usage_score * 0.2
        )
        
        return weighted_score
    
    def select_best_model(self, available_models: List[str]) -> Optional[str]:
        """
        Select best model based on weighted performance scores.
        
        Args:
            available_models: List of available model names
            
        Returns:
            Best model name or None if no models available
        """
        if not available_models:
            return None
        
        # Calculate scores for all available models
        model_scores = []
        for model_name in available_models:
            score = self.get_weighted_score(model_name)
            model_scores.append((model_name, score))
        
        # Sort by score (descending)
        model_scores.sort(key=lambda x: x[1], reverse=True)
        
        best_model = model_scores[0][0]
        best_score = model_scores[0][1]
        
        logger.info(f"Selected model: {best_model} (weighted score: {best_score:.3f})")
        
        return best_model
    
    def rotate_model(self, available_models: List[str], exclude_models: Optional[List[str]] = None) -> Optional[str]:
        """
        Rotate to next model (round-robin with performance weighting).
        
        Args:
            available_models: List of available model names
            exclude_models: Optional list of models to exclude (e.g., recently failed)
            
        Returns:
            Rotated model name or None
        """
        if not available_models:
            return None
        
        # Filter out excluded models
        candidate_models = [m for m in available_models if m not in (exclude_models or [])]
        if not candidate_models:
            candidate_models = available_models  # Fall back to all if all excluded
        
        # Filter out models with too many consecutive failures
        filtered_models = []
        for model_name in candidate_models:
            if model_name in self.performance:
                perf = self.performance[model_name]
                # Exclude models with 3+ consecutive failures
                if perf.consecutive_failures >= 3:
                    logger.debug(f"Excluding {model_name} due to {perf.consecutive_failures} consecutive failures")
                    continue
            filtered_models.append(model_name)
        
        if not filtered_models:
            filtered_models = candidate_models  # Fall back if all filtered out
        
        # Use weighted selection
        return self.select_best_model(filtered_models)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get overall performance statistics"""
        if not self.performance:
            return {
                "total_models": 0,
                "total_requests": 0,
                "overall_success_rate": 0.0
            }
        
        total_requests = sum(p.total_requests for p in self.performance.values())
        total_successful = sum(p.successful_requests for p in self.performance.values())
        
        return {
            "total_models": len(self.performance),
            "total_requests": total_requests,
            "total_successful": total_successful,
            "overall_success_rate": total_successful / total_requests if total_requests > 0 else 0.0,
            "models": {
                model_name: {
                    "success_rate": perf.success_rate,
                    "total_requests": perf.total_requests,
                    "consecutive_failures": perf.consecutive_failures
                }
                for model_name, perf in self.performance.items()
            }
        }
    
    def reset_performance(self, model_name: Optional[str] = None):
        """
        Reset performance data (for testing or after model updates).
        
        Args:
            model_name: Optional specific model to reset, or None to reset all
        """
        if model_name:
            if model_name in self.performance:
                del self.performance[model_name]
                logger.info(f"Reset performance data for {model_name}")
        else:
            self.performance = {}
            logger.info("Reset all performance data")
        
        self._save_performance()

