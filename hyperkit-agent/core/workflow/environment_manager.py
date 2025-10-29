"""
Environment Isolation Manager
Creates isolated temp directories and environments for each workflow run.
"""

import shutil
import tempfile
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class EnvironmentManager:
    """
    Manages isolated build/test/deploy environments for workflow runs.
    Creates temp directories, cleans up on success, preserves on failure.
    """
    
    def __init__(self, workspace_dir: Path, workflow_id: str):
        """
        Initialize environment manager.
        
        Args:
            workspace_dir: Base workspace directory
            workflow_id: Unique workflow identifier
        """
        self.workspace_dir = Path(workspace_dir)
        self.workflow_id = workflow_id
        self.temp_dir: Optional[Path] = None
        self.build_dir: Optional[Path] = None
        self.created_at: Optional[str] = None
        
        logger.info(f"EnvironmentManager initialized for workflow: {workflow_id}")
    
    def create_isolated_environment(self) -> Path:
        """
        Create isolated temporary environment for this workflow run.
        
        Returns:
            Path to temporary directory
        """
        # Create temp directory with workflow ID
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        temp_name = f"workflow_{self.workflow_id}_{timestamp}"
        
        self.temp_dir = self.workspace_dir / ".temp_envs" / temp_name
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        self.build_dir = self.temp_dir / "build"
        self.build_dir.mkdir(exist_ok=True)
        
        self.created_at = timestamp
        
        logger.info(f"📁 Created isolated environment: {self.temp_dir}")
        return self.temp_dir
    
    def get_build_dir(self) -> Path:
        """Get build directory path"""
        if not self.build_dir:
            self.create_isolated_environment()
        return self.build_dir
    
    def cleanup(self, preserve_on_error: bool = False, had_errors: bool = False):
        """
        Clean up temporary environment.
        
        Args:
            preserve_on_error: Whether to preserve directory on error
            had_errors: Whether workflow had errors
        """
        if not self.temp_dir or not self.temp_dir.exists():
            return
        
        should_preserve = preserve_on_error and had_errors
        
        if should_preserve:
            logger.info(f"🔒 Preserving temp environment for debugging: {self.temp_dir}")
            logger.info(f"   Clean up manually: rm -rf {self.temp_dir}")
        else:
            try:
                shutil.rmtree(self.temp_dir)
                logger.info(f"🧹 Cleaned up temp environment: {self.temp_dir}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to clean up temp directory: {e}")
                logger.info(f"   Manual cleanup: rm -rf {self.temp_dir}")
    
    def preserve_for_debugging(self):
        """Mark environment for preservation (called on error)"""
        logger.info(f"🔒 Temp environment preserved for debugging: {self.temp_dir}")
        if self.temp_dir and self.temp_dir.exists():
            # Create a marker file
            marker = self.temp_dir / ".preserve_for_debug"
            marker.write_text(f"Workflow ID: {self.workflow_id}\nCreated: {self.created_at}\n")

