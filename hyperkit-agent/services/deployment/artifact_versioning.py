"""
Artifact Versioning and Rollback Support
Manages versioned artifacts for deployment rollback capability
"""

import json
import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class ArtifactVersionManager:
    """Manages versioned contract artifacts with rollback support"""
    
    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)
        self.artifacts_dir = self.project_root / "artifacts" / "versions"
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        self.manifest_file = self.artifacts_dir / "manifest.json"
        self.manifest = self._load_manifest()
    
    def _load_manifest(self) -> Dict[str, Any]:
        """Load artifact manifest"""
        if self.manifest_file.exists():
            try:
                with open(self.manifest_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load manifest: {e}")
        
        return {
            "versions": [],
            "current_version": None,
            "created_at": datetime.now().isoformat()
        }
    
    def _save_manifest(self):
        """Save artifact manifest"""
        try:
            with open(self.manifest_file, 'w') as f:
                json.dump(self.manifest, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save manifest: {e}")
    
    def create_version(self, contract_name: str, artifact_path: Path, metadata: Dict[str, Any] = None) -> str:
        """
        Create a versioned copy of an artifact.
        
        Args:
            contract_name: Name of the contract
            artifact_path: Path to the artifact file
            metadata: Additional metadata
            
        Returns:
            Version ID (SHA256 hash)
        """
        try:
            if not artifact_path.exists():
                raise FileNotFoundError(f"Artifact not found: {artifact_path}")
            
            # Read artifact
            with open(artifact_path, 'r') as f:
                artifact_data = json.load(f)
            
            # Generate version ID from content hash
            artifact_str = json.dumps(artifact_data, sort_keys=True)
            version_id = hashlib.sha256(artifact_str.encode()).hexdigest()[:16]
            
            # Create versioned artifact path
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            versioned_name = f"{contract_name}_{version_id}_{timestamp}.json"
            versioned_path = self.artifacts_dir / versioned_name
            
            # Copy artifact
            with open(versioned_path, 'w') as f:
                json.dump(artifact_data, f, indent=2)
            
            # Add to manifest
            version_entry = {
                "version_id": version_id,
                "contract_name": contract_name,
                "original_path": str(artifact_path),
                "versioned_path": str(versioned_path),
                "timestamp": timestamp,
                "created_at": datetime.now().isoformat(),
                "metadata": metadata or {},
                "deployed": False
            }
            
            self.manifest["versions"].append(version_entry)
            self.manifest["current_version"] = version_id
            self._save_manifest()
            
            logger.info(f"Created artifact version {version_id} for {contract_name}")
            return version_id
            
        except Exception as e:
            logger.error(f"Failed to create artifact version: {e}")
            raise
    
    def get_version(self, version_id: str) -> Optional[Dict[str, Any]]:
        """Get version information by ID"""
        for version in self.manifest["versions"]:
            if version["version_id"] == version_id:
                return version
        return None
    
    def list_versions(self, contract_name: str = None) -> List[Dict[str, Any]]:
        """List all versions, optionally filtered by contract name"""
        versions = self.manifest["versions"]
        if contract_name:
            versions = [v for v in versions if v["contract_name"] == contract_name]
        return sorted(versions, key=lambda x: x["created_at"], reverse=True)
    
    def rollback(self, version_id: str, target_path: Path) -> bool:
        """
        Rollback to a specific artifact version.
        
        Args:
            version_id: Version ID to rollback to
            target_path: Path where to restore the artifact
            
        Returns:
            True if rollback successful
        """
        try:
            version = self.get_version(version_id)
            if not version:
                logger.error(f"Version {version_id} not found")
                return False
            
            versioned_path = Path(version["versioned_path"])
            if not versioned_path.exists():
                logger.error(f"Versioned artifact not found: {versioned_path}")
                return False
            
            # Copy versioned artifact to target
            import shutil
            shutil.copy2(versioned_path, target_path)
            
            # Update manifest
            self.manifest["current_version"] = version_id
            for v in self.manifest["versions"]:
                if v["version_id"] == version_id:
                    v["deployed"] = True
            
            self._save_manifest()
            
            logger.info(f"Rolled back to version {version_id}")
            return True
            
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return False
    
    def mark_deployed(self, version_id: str, deployment_info: Dict[str, Any]):
        """Mark a version as deployed with deployment information"""
        version = self.get_version(version_id)
        if version:
            version["deployed"] = True
            version["deployment_info"] = deployment_info
            version["deployed_at"] = datetime.now().isoformat()
            self._save_manifest()

