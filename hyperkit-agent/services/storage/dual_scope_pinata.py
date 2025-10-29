"""
Dual-Scope Pinata IPFS Service
Implements Team (official) and Community (user-generated) artifact management
with separate namespaces, API keys, and CID registries.
"""

import json
import logging
import hashlib
from typing import Dict, Any, Optional, Literal
from pathlib import Path
from datetime import datetime
from enum import Enum
import requests

logger = logging.getLogger(__name__)


class UploadScope(Enum):
    """Upload scope classification"""
    TEAM = "team"
    COMMUNITY = "community"


class PinataScopeClient:
    """
    Dual-scope Pinata client for Team and Community artifacts.
    
    Team Scope: Official, production-vetted artifacts
    Community Scope: User-generated, experimental artifacts
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize dual-scope Pinata client.
        
        Args:
            config: Configuration dict with:
                - team_api_key: Team Pinata API key
                - team_api_secret: Team Pinata API secret
                - community_api_key: Community Pinata API key (optional)
                - community_api_secret: Community Pinata API secret (optional)
                - registry_dir: Directory for CID registries
        """
        self.team_api_key = config.get('team_api_key')
        self.team_api_secret = config.get('team_api_secret')
        self.community_api_key = config.get('community_api_key') or self.team_api_key
        self.community_api_secret = config.get('community_api_secret') or self.team_api_secret
        
        self.registry_dir = Path(config.get('registry_dir', 'data/ipfs_registries'))
        self.registry_dir.mkdir(parents=True, exist_ok=True)
        
        # Registry file paths
        self.team_registry_path = self.registry_dir / 'cid-registry-team.json'
        self.community_registry_path = self.registry_dir / 'cid-registry-community.json'
        
        # Load existing registries
        self._load_registries()
        
        if not self.team_api_key or not self.team_api_secret:
            logger.warning("Team Pinata credentials not configured - Team uploads will fail")
        
        if not self.community_api_key or not self.community_api_secret:
            logger.warning("Community Pinata credentials not configured - Community uploads will fail")
    
    def _load_registries(self):
        """Load CID registries from disk"""
        try:
            if self.team_registry_path.exists():
                with open(self.team_registry_path, 'r', encoding='utf-8') as f:
                    self.team_registry = json.load(f)
            else:
                self.team_registry = {}
        except Exception as e:
            logger.error(f"Failed to load team registry: {e}")
            self.team_registry = {}
        
        try:
            if self.community_registry_path.exists():
                with open(self.community_registry_path, 'r', encoding='utf-8') as f:
                    self.community_registry = json.load(f)
            else:
                self.community_registry = {}
        except Exception as e:
            logger.error(f"Failed to load community registry: {e}")
            self.community_registry = {}
    
    def _save_registry(self, scope: UploadScope):
        """Save CID registry to disk"""
        registry_path = (
            self.team_registry_path if scope == UploadScope.TEAM 
            else self.community_registry_path
        )
        registry = (
            self.team_registry if scope == UploadScope.TEAM
            else self.community_registry
        )
        
        try:
            with open(registry_path, 'w', encoding='utf-8') as f:
                json.dump(registry, f, indent=2, ensure_ascii=False)
            logger.debug(f"Saved {scope.value} registry to {registry_path}")
        except Exception as e:
            logger.error(f"Failed to save {scope.value} registry: {e}")
    
    def _get_api_credentials(self, scope: UploadScope) -> tuple:
        """Get API credentials for specified scope"""
        if scope == UploadScope.TEAM:
            return self.team_api_key, self.team_api_secret
        else:
            return self.community_api_key, self.community_api_secret
    
    def _calculate_content_hash(self, content: str) -> str:
        """Calculate SHA-256 hash of content for provenance tracking"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    async def upload_artifact(
        self,
        content: str,
        artifact_type: str,  # 'contract', 'prompt', 'workflow', 'metadata'
        scope: UploadScope,
        metadata: Dict[str, Any] = None,
        workflow_signature: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upload artifact to Pinata with scope classification.
        
        Args:
            content: Artifact content (contract code, prompt, etc.)
            artifact_type: Type of artifact ('contract', 'prompt', 'workflow', 'metadata')
            scope: Upload scope (TEAM or COMMUNITY)
            metadata: Additional metadata
            workflow_signature: Optional workflow identifier/hash
            user_id: Optional user identifier (for Community uploads)
            
        Returns:
            Dict with CID, scope, and upload metadata
        """
        if scope == UploadScope.TEAM:
            if not self.team_api_key or not self.team_api_secret:
                raise ValueError("Team Pinata credentials not configured")
            api_key, api_secret = self.team_api_key, self.team_api_secret
        else:
            if not self.community_api_key or not self.community_api_secret:
                raise ValueError("Community Pinata credentials not configured")
            api_key, api_secret = self.community_api_key, self.community_api_secret
        
        # Prepare metadata
        content_hash = self._calculate_content_hash(content)
        timestamp = datetime.utcnow().isoformat()
        
        pinata_metadata = {
            'name': f"{artifact_type}-{timestamp}",
            'description': metadata.get('description', '') if metadata else '',
            'tags': metadata.get('tags', []) if metadata else [],
            'keyvalues': {
                'scope': scope.value,
                'artifact_type': artifact_type,
                'content_hash': content_hash,
                'timestamp': timestamp,
                **(metadata.get('keyvalues', {}) if metadata else {})
            }
        }
        
        if workflow_signature:
            pinata_metadata['keyvalues']['workflow_signature'] = workflow_signature
        
        if user_id and scope == UploadScope.COMMUNITY:
            pinata_metadata['keyvalues']['uploader_id'] = user_id
        
        # Prepare upload
        headers = {
            'pinata_api_key': api_key,
            'pinata_secret_api_key': api_secret
        }
        
        files = {
            'file': (f"{artifact_type}.txt", content.encode('utf-8'))
        }
        
        data = {
            'pinataMetadata': json.dumps(pinata_metadata),
            'pinataOptions': json.dumps({'cidVersion': 1})
        }
        
        # Upload to Pinata
        try:
            response = requests.post(
                'https://api.pinata.cloud/pinning/pinFileToIPFS',
                headers=headers,
                files=files,
                data=data,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                cid = result.get('IpfsHash')
                
                # Register CID
                artifact_id = f"{artifact_type}-{content_hash[:16]}"
                registry_entry = {
                    'cid': cid,
                    'scope': scope.value,
                    'artifact_type': artifact_type,
                    'content_hash': content_hash,
                    'timestamp': timestamp,
                    'workflow_signature': workflow_signature,
                    'metadata': pinata_metadata,
                    'ipfs_url': f"ipfs://{cid}",
                    'gateway_url': f"https://gateway.pinata.cloud/ipfs/{cid}"
                }
                
                if user_id and scope == UploadScope.COMMUNITY:
                    registry_entry['uploader_id'] = user_id
                
                registry = (
                    self.team_registry if scope == UploadScope.TEAM
                    else self.community_registry
                )
                registry[artifact_id] = registry_entry
                self._save_registry(scope)
                
                logger.info(f"✅ Uploaded {scope.value} artifact '{artifact_type}' to IPFS: {cid}")
                
                return {
                    'status': 'success',
                    'cid': cid,
                    'scope': scope.value,
                    'artifact_id': artifact_id,
                    'ipfs_url': f"ipfs://{cid}",
                    'gateway_url': f"https://gateway.pinata.cloud/ipfs/{cid}",
                    'registry_entry': registry_entry
                }
            else:
                error_msg = f"Pinata upload failed: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)
                
        except Exception as e:
            logger.error(f"Pinata upload error for {scope.value} scope: {e}")
            raise
    
    def get_registry(self, scope: Optional[UploadScope] = None) -> Dict[str, Any]:
        """
        Get CID registry for specified scope or both.
        
        Args:
            scope: Optional scope filter (TEAM, COMMUNITY, or None for both)
            
        Returns:
            Registry dict(s)
        """
        if scope == UploadScope.TEAM:
            return {'team': self.team_registry}
        elif scope == UploadScope.COMMUNITY:
            return {'community': self.community_registry}
        else:
            return {
                'team': self.team_registry,
                'community': self.community_registry
            }

