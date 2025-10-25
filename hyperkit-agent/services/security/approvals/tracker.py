"""
Token Approval Tracker
"""
import logging
from typing import Dict, List
from web3 import Web3

logger = logging.getLogger(__name__)

class ApprovalTracker:
    def __init__(self, w3: Web3 = None):
        self.w3 = w3
    
    async def get_approvals(self, user_address: str, token_addresses: List[str]) -> List[Dict]:
        approvals = []
        for token_addr in token_addresses:
            try:
                logger.info(f"Checking approvals for token: {token_addr}")
            except Exception as e:
                logger.error(f"Failed to check approvals: {e}")
        return approvals
    
    def analyze_approval(self, tx_params: Dict) -> Dict:
        data = tx_params.get("data", "")
        if data.startswith("0x095ea7b3"):
            if "f" * 60 in data:
                return {"is_approval": True, "is_unlimited": True, "risk_level": "high", "warning": "Unlimited approval"}
            return {"is_approval": True, "is_unlimited": False, "risk_level": "medium"}
        return {"is_approval": False}
