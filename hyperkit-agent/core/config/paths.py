"""
Centralized path management for organized directory structure
"""

from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class PathManager:
    """Manage all project paths organized by command type"""
    
    def __init__(self, base_dir: Optional[str] = None, command_type: str = "workflow"):
        if base_dir:
            self.base_dir = Path(base_dir)
        else:
            # Always use hyperkit-agent directory relative to this file
            current_file = Path(__file__)
            # Navigate from core/config/paths.py to hyperkit-agent root
            self.base_dir = current_file.parent.parent.parent
        self.artifacts_dir = self.base_dir / "artifacts"
        self.command_type = command_type  # workflow, generate, audit, deploy, verify, test
    
    @property
    def contracts_dir(self) -> Path:
        """Main contracts directory for artifacts/organization"""
        return self.artifacts_dir / "contracts"
    
    @property
    def foundry_contracts_dir(self) -> Path:
        """Foundry project contracts directory (for compilation/deployment)"""
        return self.base_dir / "contracts"
    
    def get_command_dir(self, command_type: str = None) -> Path:
        """Get directory for specific command type"""
        cmd = command_type or self.command_type
        return self.artifacts_dir / cmd
    
    def get_workflow_dir(self) -> Path:
        """Get workflow-specific directory"""
        return self.artifacts_dir / "workflows"
    
    def get_generate_dir(self) -> Path:
        """Get generate command directory"""
        return self.artifacts_dir / "generate"
    
    def get_audit_command_dir(self) -> Path:
        """Get audit command directory"""
        return self.artifacts_dir / "audit"
    
    def get_deploy_command_dir(self) -> Path:
        """Get deploy command directory"""
        return self.artifacts_dir / "deploy"
    
    def get_verify_command_dir(self) -> Path:
        """Get verify command directory"""
        return self.artifacts_dir / "verify"
    
    def get_test_command_dir(self) -> Path:
        """Get test command directory"""
        return self.artifacts_dir / "test"
    
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
        """Create all necessary directories organized by command type"""
        categories = ['tokens', 'gaming', 'defi', 'nft', 'governance', 'bridge', 'launchpad', 'other']
        commands = ['workflows', 'generate', 'audit', 'deploy', 'verify', 'test']
        
        # Create command-specific directories
        for command in commands:
            cmd_dir = self.artifacts_dir / command
            cmd_dir.mkdir(parents=True, exist_ok=True)
            
            # Create category subdirectories for each command
            for category in categories:
                (cmd_dir / category).mkdir(parents=True, exist_ok=True)
        
        # Create legacy structure for backward compatibility
        for category in categories:
            self.get_category_dir(category).mkdir(parents=True, exist_ok=True)
            self.get_audit_dir(category).mkdir(parents=True, exist_ok=True)
        
        logger.info("✅ All directories created (organized by command type)")
