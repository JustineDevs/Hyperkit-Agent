"""
Alith SDK Integration for HyperKit Agent
Provides AI-powered smart contract auditing and natural language DeFi interactions

NOTE: services/alith/agent.py not implemented yet - using direct Alith SDK imports
"""

def is_alith_available() -> bool:
    """Check if Alith SDK is available"""
    try:
        from alith import Agent
        return True
    except ImportError:
        return False

# Temporary stub until agent.py is implemented
class HyperKitAlithAgent:
    """Stub for HyperKitAlithAgent - direct Alith SDK used in ai_agent.py instead"""
    def __init__(self, config):
        pass

__all__ = ["HyperKitAlithAgent", "is_alith_available"]

