"""
HyperKit Agent Services
Consolidated service modules for production deployment
"""

from .core.ai_agent import HyperKitAIAgent
from .core.blockchain import HyperKitBlockchainService
from .core.storage import HyperKitStorageService
from .core.security import HyperKitSecurityService
from .core.monitoring import HyperKitMonitoringService
from .core.rag import HyperKitRAGService
from .core.verification import HyperKitVerificationService

# Consolidated service instances
ai_agent = HyperKitAIAgent()
blockchain = HyperKitBlockchainService()
storage = HyperKitStorageService()
security = HyperKitSecurityService()
monitoring = HyperKitMonitoringService()
rag = HyperKitRAGService()
verification = HyperKitVerificationService()

__all__ = [
    'ai_agent',
    'blockchain', 
    'storage',
    'security',
    'monitoring',
    'rag',
    'verification'
]
