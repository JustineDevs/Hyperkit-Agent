"""
Risk Calculation Engine
"""
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class RiskCalculator:
    def __init__(self, weights: Dict[str, float] = None):
        self.weights = weights or {"simulation": 0.20, "reputation": 0.30, "approval": 0.25, "phishing": 0.25}
    
    def calculate(self, scores: Dict[str, float]) -> Dict[str, Any]:
        total = sum(scores.get(k, 0) * w for k, w in self.weights.items())
        return {"risk_score": int(total), "risk_level": self._categorize(total), "recommendation": self._recommend(total)}
    
    def _categorize(self, score: float) -> str:
        if score >= 86: return "critical"
        elif score >= 61: return "high"
        elif score >= 31: return "medium"
        else: return "low"
    
    def _recommend(self, score: float) -> str:
        if score >= 86: return "block"
        elif score >= 61: return "warn"
        elif score >= 31: return "caution"
        else: return "allow"
