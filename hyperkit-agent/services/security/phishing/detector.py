"""
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
