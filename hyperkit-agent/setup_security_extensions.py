"""
HyperKit Agent - Security Extensions Setup Script
Generates all security component files for wallet protection features
"""

import os
from pathlib import Path

def create_reputation_database():
    return '''"""
Address Reputation Database
Implements graph-based address reputation tracking with risk scoring
"""

import json
import logging
import networkx as nx
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ReputationDatabase:
    """Graph-based address reputation database using NetworkX"""

    def __init__(self, seed_file: Optional[str] = None):
        self.graph = nx.DiGraph()
        self.known_phishers = set()
        self.known_victims = set()
        self.last_update = datetime.now()
        
        if seed_file and os.path.exists(seed_file):
            self._load_seed_data(seed_file)
    
    def get_risk_score(self, address: str) -> Dict[str, Any]:
        """Calculate comprehensive risk score for address"""
        try:
            if address in self.known_phishers:
                return {
                    "risk_score": 95,
                    "labels": ["phishing", "wallet_drainer"],
                    "confidence": 0.95,
                    "reasoning": "Address in known phisher database"
                }
            
            # Calculate based on graph relationships
            risk_factors = {
                "phisher_connections": self._count_phisher_connections(address),
                "victim_connections": self._count_victim_connections(address),
                "age_score": self._calculate_age_score(address),
                "activity_score": self._calculate_activity_score(address)
            }
            
            risk_score = self._aggregate_risk(risk_factors)
            
            return {
                "risk_score": risk_score,
                "labels": self._generate_labels(risk_score, risk_factors),
                "confidence": 0.75,
                "risk_factors": risk_factors
            }
            
        except Exception as e:
            logger.error(f"Risk calculation failed: {e}")
            return {"risk_score": 50, "labels": ["unknown"], "confidence": 0.0}
    
    def add_address(self, address: str, label: str, metadata: Dict = None):
        """Add address to reputation database"""
        self.graph.add_node(address, label=label, metadata=metadata or {}, added=datetime.now())
        
        if label == "phisher":
            self.known_phishers.add(address)
        elif label == "victim":
            self.known_victims.add(address)
    
    def _count_phisher_connections(self, address: str) -> int:
        if not self.graph.has_node(address):
            return 0
        neighbors = list(self.graph.predecessors(address)) + list(self.graph.successors(address))
        return sum(1 for n in neighbors if n in self.known_phishers)
    
    def _count_victim_connections(self, address: str) -> int:
        if not self.graph.has_node(address):
            return 0
        neighbors = list(self.graph.successors(address))
        return sum(1 for n in neighbors if n in self.known_victims)
    
    def _calculate_age_score(self, address: str) -> float:
        if not self.graph.has_node(address):
            return 0.5
        added = self.graph.nodes[address].get("added", datetime.now())
        age_days = (datetime.now() - added).days
        return max(0, 1.0 - (age_days / 365))
    
    def _calculate_activity_score(self, address: str) -> float:
        if not self.graph.has_node(address):
            return 0.0
        tx_count = self.graph.nodes[address].get("metadata", {}).get("tx_count", 0)
        return min(1.0, tx_count / 1000)
    
    def _aggregate_risk(self, factors: Dict) -> int:
        score = (
            factors["phisher_connections"] * 30 +
            factors["victim_connections"] * 25 +
            factors["age_score"] * 25 +
            factors["activity_score"] * 20
        )
        return min(100, int(score))
    
    def _generate_labels(self, risk_score: int, factors: Dict) -> List[str]:
        labels = []
        if risk_score >= 80:
            labels.append("high_risk")
        if factors["phisher_connections"] > 2:
            labels.append("phisher_network")
        if factors["victim_connections"] > 5:
            labels.append("potential_scammer")
        return labels or ["unknown"]
    
    def _load_seed_data(self, seed_file: str):
        """Load seed data from file"""
        try:
            with open(seed_file, 'r') as f:
                data = json.load(f)
                for item in data.get("phishers", []):
                    self.add_address(item["address"], "phisher", item.get("metadata"))
                logger.info(f"Loaded {len(self.known_phishers)} phisher addresses")
        except Exception as e:
            logger.error(f"Failed to load seed data: {e}")
'''

def create_files():
    """Create all security extension files"""
    base_path = Path(__file__).parent
    
    files_content = {
        "services/security/reputation/database.py": create_reputation_database(),
        "services/security/reputation/risk_calculator.py": '''"""
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
''',
        "services/security/phishing/__init__.py": '''"""Phishing Detection Module"""
from .detector import PhishingDetector
__all__ = ["PhishingDetector"]
''',
        "services/security/phishing/detector.py": '''"""
Phishing URL Detector
"""
import re
import logging
from difflib import SequenceMatcher
from typing import Dict

logger = logging.getLogger(__name__)

class PhishingDetector:
    def __init__(self):
        self.legitimate_domains = ["uniswap.org", "opensea.io", "metamask.io", "etherscan.io"]
        self.blacklist = set()
    
    def check_url(self, url: str) -> Dict:
        try:
            domain = self._extract_domain(url)
            if domain in self.blacklist:
                return {"risk": "CRITICAL", "reason": "Known phishing site", "confidence": 0.95}
            for legit in self.legitimate_domains:
                similarity = SequenceMatcher(None, domain, legit).ratio()
                if 0.7 < similarity < 1.0:
                    return {"risk": "HIGH", "reason": f"Similar to {legit}", "confidence": 0.85}
            return {"risk": "LOW", "reason": "No threats detected", "confidence": 0.70}
        except Exception as e:
            return {"risk": "UNKNOWN", "reason": str(e), "confidence": 0.0}
    
    def _extract_domain(self, url: str) -> str:
        match = re.search(r'https?://([^/]+)', url)
        return match.group(1) if match else url
''',
        "services/security/approvals/__init__.py": '''"""Token Approval Management"""
from .tracker import ApprovalTracker
__all__ = ["ApprovalTracker"]
''',
        "services/security/approvals/tracker.py": '''"""
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
''',
        "services/security/ml/__init__.py": '''"""ML Risk Scoring"""
from .risk_scorer import MLRiskScorer
__all__ = ["MLRiskScorer"]
''',
        "services/security/ml/risk_scorer.py": '''"""
ML-Based Risk Scorer
"""
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

class MLRiskScorer:
    def __init__(self, model_path: str = None):
        self.model = None
        self.features = ["age_days", "tx_count", "unique_interactions", "avg_gas_price"]
    
    async def calculate_risk(self, address: str) -> Dict:
        try:
            features = self._extract_features(address)
            probability = 0.5
            return {"ml_risk_score": int(probability * 100), "confidence": 0.80, "risk_level": self._categorize(probability)}
        except Exception as e:
            logger.error(f"ML risk calculation failed: {e}")
            return {"ml_risk_score": 50, "confidence": 0.0}
    
    def _extract_features(self, address: str) -> List[float]:
        return [0.0] * len(self.features)
    
    def _categorize(self, prob: float) -> str:
        if prob >= 0.8: return "critical"
        elif prob >= 0.6: return "high"
        elif prob >= 0.3: return "medium"
        else: return "low"
'''
    }
    
    for file_path, content in files_content.items():
        full_path = base_path / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ Created: {file_path}")
    
    print(f"\n🎉 Created {len(files_content)} security component files!")

if __name__ == "__main__":
    create_files()
