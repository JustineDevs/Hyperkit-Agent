"""
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
