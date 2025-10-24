"""
Centralized path management for organized directory structure
"""

from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class PathManager:
    """Manage all project paths"""
    
    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = Path(base_dir) if base_dir else Path.cwd()
        self.artifacts_dir = self.base_dir / "artifacts"
    
    @property
    def contracts_dir(self) -> Path:
        """Main contracts directory"""
        return self.artifacts_dir / "contracts"
    
    def get_category_dir(self, category: str) -> Path:
        """Get directory for specific category"""
        return self.contracts_dir / category / "generated"
    
    def get_contract_path(self, filename: str, category: str) -> Path:
        """Get full path for contract file"""
        return self.get_category_dir(category) / filename
    
    def get_audit_dir(self, category: str = None) -> Path:
        """Get audit directory"""
        if category:
            return self.artifacts_dir / "audits" / category
        return self.artifacts_dir / "audits"
    
    def get_deployment_dir(self, network: str, category: str = None) -> Path:
        """Get deployment directory by network and category"""
        if category:
            return self.artifacts_dir / "deployments" / network / category
        return self.artifacts_dir / "deployments" / network
    
    def get_verification_dir(self, network: str) -> Path:
        """Get verification directory"""
        return self.artifacts_dir / "verification" / network
    
    def create_all_dirs(self):
        """Create all necessary directories"""
        categories = ['tokens', 'gaming', 'defi', 'nft', 'governance', 'bridge', 'launchpad', 'other']
        
        for category in categories:
            self.get_category_dir(category).mkdir(parents=True, exist_ok=True)
            self.get_audit_dir(category).mkdir(parents=True, exist_ok=True)
        
        logger.info("✅ All directories created")
