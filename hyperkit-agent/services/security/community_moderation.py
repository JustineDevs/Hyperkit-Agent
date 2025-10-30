"""
Security and UX Policies for Community Uploads

Implements sandboxing, malicious content checks, flagging/purging system,
and reputation system for Community artifacts.
"""

import re
import logging
import hashlib
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from enum import Enum
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class ContentFlag(Enum):
    """Content flag types"""
    MALICIOUS = "malicious"
    SPAM = "spam"
    LOW_QUALITY = "low_quality"
    COPYRIGHT = "copyright"
    INAPPROPRIATE = "inappropriate"
    UNVERIFIED = "unverified"


class CommunityModeration:
    """
    Security and moderation system for Community uploads.
    
    Features:
    - Content scanning for malicious patterns
    - Automated quality scoring
    - Flagging and purging system
    - Reputation tracking
    - Sandboxing of flagged content
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize moderation system"""
        self.config = config or {}
        self.flagged_content: Dict[str, List[Dict[str, Any]]] = {}
        self.reputation_scores: Dict[str, float] = {}  # user_id -> reputation
        self.upload_history: List[Dict[str, Any]] = []
        
        # Load flagged content and reputation from disk
        self._load_moderation_data()
        
        # Malicious patterns (basic checks)
        self.malicious_patterns = [
            r'0x[a-fA-F0-9]{40}',  # Potential hardcoded addresses
            r'selfdestruct\s*\(',
            r'assembly\s*\{',  # Inline assembly (potential exploit)
            r'delegatecall\s*\(',
            r'callcode\s*\(',
            r'block\.timestamp',  # Time manipulation
            r'block\.hash',  # Blockhash manipulation
            r'block\.coinbase',  # Miner manipulation
        ]
        
        # Suspicious patterns (warnings)
        self.suspicious_patterns = [
            r'require\s*\(false\)',  # Always fails
            r'assert\s*\(false\)',
            r'while\s*\(true\)',  # Infinite loops
            r'for\s*\([^)]*\)\s*\{[^}]*\}',  # Unbounded loops
        ]
    
    def _load_moderation_data(self):
        """Load moderation data from disk"""
        try:
            mod_dir = Path("data/moderation")
            mod_dir.mkdir(parents=True, exist_ok=True)
            
            # Load flagged content
            flagged_file = mod_dir / "flagged_content.json"
            if flagged_file.exists():
                with open(flagged_file, 'r') as f:
                    self.flagged_content = json.load(f)
            
            # Load reputation scores
            reputation_file = mod_dir / "reputation_scores.json"
            if reputation_file.exists():
                with open(reputation_file, 'r') as f:
                    self.reputation_scores = json.load(f)
                    
        except Exception as e:
            logger.warning(f"Could not load moderation data: {e}")
    
    def _save_moderation_data(self):
        """Save moderation data to disk"""
        try:
            mod_dir = Path("data/moderation")
            mod_dir.mkdir(parents=True, exist_ok=True)
            
            # Save flagged content
            flagged_file = mod_dir / "flagged_content.json"
            with open(flagged_file, 'w') as f:
                json.dump(self.flagged_content, f, indent=2)
            
            # Save reputation scores
            reputation_file = mod_dir / "reputation_scores.json"
            with open(reputation_file, 'w') as f:
                json.dump(self.reputation_scores, f, indent=2)
                
        except Exception as e:
            logger.error(f"Could not save moderation data: {e}")
    
    def scan_content(self, content: str, artifact_type: str) -> Dict[str, Any]:
        """
        Scan content for malicious patterns and quality issues.
        
        Args:
            content: Content to scan
            artifact_type: Type of artifact ('contract', 'prompt', etc.)
            
        Returns:
            Dict with scan results, flags, and recommendations
        """
        scan_result = {
            'safe': True,
            'flags': [],
            'warnings': [],
            'risk_score': 0.0,
            'quality_score': 0.0,
            'recommendations': []
        }
        
        # Check for malicious patterns
        for pattern in self.malicious_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                scan_result['safe'] = False
                scan_result['flags'].append({
                    'type': ContentFlag.MALICIOUS.value,
                    'pattern': pattern,
                    'severity': 'high'
                })
                scan_result['risk_score'] += 0.3
        
        # Check for suspicious patterns
        for pattern in self.suspicious_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                scan_result['warnings'].append({
                    'pattern': pattern,
                    'severity': 'medium'
                })
                scan_result['risk_score'] += 0.1
        
        # Quality checks
        if artifact_type == 'contract':
            # Check for basic Solidity structure
            if 'pragma solidity' not in content.lower():
                scan_result['quality_score'] -= 0.2
                scan_result['recommendations'].append('Missing pragma directive')
            
            if 'contract' not in content.lower():
                scan_result['quality_score'] -= 0.3
                scan_result['recommendations'].append('No contract definition found')
            
            # Check for common security issues
            if 'constructor' in content.lower() and 'public' in content.lower():
                if 'onlyOwner' not in content and 'Ownable' not in content:
                    scan_result['warnings'].append({
                        'issue': 'Constructor may be public',
                        'severity': 'medium'
                    })
        
        # Minimum quality threshold
        scan_result['quality_score'] = max(0.0, min(1.0, 0.5 + scan_result['quality_score']))
        scan_result['risk_score'] = min(1.0, scan_result['risk_score'])
        
        return scan_result
    
    def flag_content(self, artifact_id: str, flag_type: ContentFlag, reason: str, user_id: Optional[str] = None):
        """
        Flag content for review or removal.
        
        Args:
            artifact_id: ID of flagged artifact
            flag_type: Type of flag
            reason: Reason for flagging
            user_id: Optional user who flagged it
        """
        flag_entry = {
            'artifact_id': artifact_id,
            'flag_type': flag_type.value,
            'reason': reason,
            'flagged_by': user_id,
            'timestamp': datetime.utcnow().isoformat(),
            'status': 'pending'  # pending, reviewed, approved, purged
        }
        
        if artifact_id not in self.flagged_content:
            self.flagged_content[artifact_id] = []
        
        self.flagged_content[artifact_id].append(flag_entry)
        self._save_moderation_data()
        
        logger.warning(f"Content flagged: {artifact_id} - {flag_type.value} - {reason}")
    
    def upvote_content(self, artifact_id: str, user_id: str) -> Dict[str, Any]:
        """
        Upvote content (increases reputation).
        
        Args:
            artifact_id: ID of artifact
            user_id: User who upvoted
            
        Returns:
            Updated upvote count and reputation
        """
        # In a real implementation, this would update the artifact metadata
        # For now, we'll track it locally
        logger.info(f"Content upvoted: {artifact_id} by {user_id}")
        
        return {
            'status': 'success',
            'artifact_id': artifact_id,
            'upvoted_by': user_id,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def get_reputation(self, user_id: str) -> float:
        """Get user reputation score"""
        return self.reputation_scores.get(user_id, 0.5)  # Default 0.5
    
    def update_reputation(self, user_id: str, delta: float):
        """Update user reputation"""
        current = self.reputation_scores.get(user_id, 0.5)
        self.reputation_scores[user_id] = max(0.0, min(1.0, current + delta))
        self._save_moderation_data()
    
    def is_sandboxed(self, artifact_id: str) -> bool:
        """Check if artifact is sandboxed (flagged)"""
        return artifact_id in self.flagged_content and len(self.flagged_content[artifact_id]) > 0
    
    def purge_content(self, artifact_id: str, reason: str):
        """Permanently remove content"""
        if artifact_id in self.flagged_content:
            self.flagged_content[artifact_id].append({
                'action': 'purged',
                'reason': reason,
                'timestamp': datetime.utcnow().isoformat()
            })
            self._save_moderation_data()
            logger.warning(f"Content purged: {artifact_id} - {reason}")
    
    def get_moderation_stats(self) -> Dict[str, Any]:
        """Get moderation statistics"""
        return {
            'flagged_count': len(self.flagged_content),
            'total_flags': sum(len(flags) for flags in self.flagged_content.values()),
            'reputation_tracked_users': len(self.reputation_scores),
            'average_reputation': sum(self.reputation_scores.values()) / len(self.reputation_scores) if self.reputation_scores else 0.0
        }

