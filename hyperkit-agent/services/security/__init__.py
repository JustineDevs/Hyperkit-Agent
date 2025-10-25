"""
HyperKit Agent - Wallet Security Extension Suite
Provides transaction simulation, address reputation, phishing detection, and more

Foundation Components:
- TransactionSimulator: Pocket Universe-style pre-signature simulation
- ReputationDatabase: GoPlus Security-style address reputation tracking
- PhishingDetector: Scam Sniffer-style URL/domain analysis
- ApprovalTracker: Revoke.cash-style token approval management
- MLRiskScorer: ML-based risk prediction
- SecurityAnalysisPipeline: Orchestrates all security checks
"""

from .simulator import TransactionSimulator
from .pipeline import SecurityAnalysisPipeline
from .reputation.database import ReputationDatabase
from .phishing.detector import PhishingDetector
from .approvals.tracker import ApprovalTracker
from .ml.risk_scorer import MLRiskScorer

__all__ = [
    "TransactionSimulator",
    "SecurityAnalysisPipeline",
    "ReputationDatabase",
    "PhishingDetector",
    "ApprovalTracker",
    "MLRiskScorer",
]

