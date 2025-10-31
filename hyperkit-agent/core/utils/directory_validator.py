"""
Robust directory validation and auto-creation system.
Ensures all required directories exist with loud failures and actionable fix steps.
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional

logger = logging.getLogger(__name__)


class DirectoryValidator:
    """Validates and ensures required directories exist with clear error messages"""
    
    REQUIRED_DIRS = [
        ".workflow_contexts",
        ".temp_envs",
        "logs",
        "artifacts",
    ]
    
    OPTIONAL_DIRS = [
        "artifacts/workflows",
        "artifacts/generate",
        "artifacts/audit",
        "artifacts/deploy",
        "artifacts/verify",
        "artifacts/test",
    ]
    
    def __init__(self, workspace_dir: Path):
        """
        Initialize directory validator.
        
        Args:
            workspace_dir: Base workspace directory (typically hyperkit-agent/)
        """
        self.workspace_dir = Path(workspace_dir).resolve()
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.fixes: List[str] = []
    
    def validate_all(self, auto_create: bool = True) -> Tuple[bool, Dict[str, any]]:
        """
        Validate all required directories exist.
        
        Args:
            auto_create: If True, attempt to create missing directories
            
        Returns:
            Tuple of (success: bool, details: dict)
        """
        self.errors.clear()
        self.warnings.clear()
        self.fixes.clear()
        
        # Validate workspace directory exists
        if not self.workspace_dir.exists():
            self.errors.append(f"Workspace directory does not exist: {self.workspace_dir}")
            self.fixes.append(f"Create workspace directory: mkdir -p {self.workspace_dir}")
            return False, self._get_result()
        
        if not self.workspace_dir.is_dir():
            self.errors.append(f"Workspace path is not a directory: {self.workspace_dir}")
            self.fixes.append(f"Remove file and create directory: rm {self.workspace_dir} && mkdir -p {self.workspace_dir}")
            return False, self._get_result()
        
        # Check write permissions
        if not os.access(self.workspace_dir, os.W_OK):
            self.errors.append(f"No write permission for workspace directory: {self.workspace_dir}")
            self.fixes.append(f"Fix permissions: chmod +w {self.workspace_dir}")
            return False, self._get_result()
        
        # Validate/create required directories
        for dir_name in self.REQUIRED_DIRS:
            dir_path = self.workspace_dir / dir_name
            success = self._validate_directory(dir_path, required=True, auto_create=auto_create)
            if not success and not auto_create:
                return False, self._get_result()
        
        # Validate/create optional directories
        for dir_name in self.OPTIONAL_DIRS:
            dir_path = self.workspace_dir / dir_name
            self._validate_directory(dir_path, required=False, auto_create=auto_create)
        
        return len(self.errors) == 0, self._get_result()
    
    def _validate_directory(self, dir_path: Path, required: bool = True, auto_create: bool = True) -> bool:
        """
        Validate a single directory exists and is accessible.
        
        Args:
            dir_path: Path to directory
            required: If True, error on missing; if False, only warn
            auto_create: If True, attempt to create missing directory
            
        Returns:
            True if directory exists and is accessible, False otherwise
        """
        try:
            # Resolve path to handle symlinks and relative paths
            resolved_path = dir_path.resolve()
            
            # Check if it exists
            if not resolved_path.exists():
                if required:
                    if auto_create:
                        try:
                            resolved_path.mkdir(parents=True, exist_ok=True)
                            logger.info(f"✅ Created required directory: {resolved_path}")
                            self.fixes.append(f"Created: {resolved_path}")
                        except (OSError, PermissionError) as e:
                            self.errors.append(
                                f"Required directory missing and cannot be created: {resolved_path}\n"
                                f"  Error: {str(e)}"
                            )
                            self.fixes.append(f"Create manually: mkdir -p {resolved_path}")
                            self.fixes.append(f"Fix permissions: chmod +w {resolved_path.parent}")
                            return False
                    else:
                        self.errors.append(f"Required directory missing: {resolved_path}")
                        self.fixes.append(f"Create directory: mkdir -p {resolved_path}")
                        return False
                else:
                    if auto_create:
                        try:
                            resolved_path.mkdir(parents=True, exist_ok=True)
                            logger.debug(f"Created optional directory: {resolved_path}")
                        except (OSError, PermissionError) as e:
                            self.warnings.append(f"Optional directory missing and cannot be created: {resolved_path} ({e})")
                    else:
                        self.warnings.append(f"Optional directory missing: {resolved_path}")
                    return True  # Optional directories don't block
            
            # Check if it's actually a directory
            if not resolved_path.is_dir():
                if required:
                    self.errors.append(
                        f"Required path exists but is not a directory: {resolved_path}\n"
                        f"  Current type: {self._get_path_type(resolved_path)}"
                    )
                    self.fixes.append(f"Remove file and create directory: rm {resolved_path} && mkdir -p {resolved_path}")
                    return False
                else:
                    self.warnings.append(f"Optional path exists but is not a directory: {resolved_path}")
                    return True
            
            # Check write permissions
            if not os.access(resolved_path, os.W_OK):
                if required:
                    self.errors.append(f"No write permission for required directory: {resolved_path}")
                    self.fixes.append(f"Fix permissions: chmod +w {resolved_path}")
                    return False
                else:
                    self.warnings.append(f"No write permission for optional directory: {resolved_path}")
            
            # Check read permissions
            if not os.access(resolved_path, os.R_OK):
                if required:
                    self.errors.append(f"No read permission for required directory: {resolved_path}")
                    self.fixes.append(f"Fix permissions: chmod +r {resolved_path}")
                    return False
                else:
                    self.warnings.append(f"No read permission for optional directory: {resolved_path}")
            
            return True
            
        except Exception as e:
            if required:
                self.errors.append(
                    f"Error validating required directory {dir_path}: {str(e)}"
                )
                self.fixes.append(f"Check directory manually: ls -la {dir_path.parent}")
                return False
            else:
                self.warnings.append(f"Error validating optional directory {dir_path}: {str(e)}")
                return True
    
    def _get_path_type(self, path: Path) -> str:
        """Get human-readable type of path"""
        if path.is_file():
            return "file"
        elif path.is_dir():
            return "directory"
        elif path.is_symlink():
            return "symlink"
        elif path.exists():
            return "unknown (exists but not file/dir/symlink)"
        else:
            return "does not exist"
    
    def _get_result(self) -> Dict[str, any]:
        """Get validation result dictionary"""
        return {
            "success": len(self.errors) == 0,
            "errors": self.errors.copy(),
            "warnings": self.warnings.copy(),
            "fixes": self.fixes.copy(),
            "workspace_dir": str(self.workspace_dir),
            "required_dirs": [str(self.workspace_dir / d) for d in self.REQUIRED_DIRS],
            "optional_dirs": [str(self.workspace_dir / d) for d in self.OPTIONAL_DIRS],
        }
    
    def ensure_all_directories(self) -> Tuple[bool, Dict[str, any]]:
        """
        Ensure all required and optional directories exist (alias for validate_all with auto_create=True).
        
        Returns:
            Tuple of (success: bool, details: dict)
        """
        return self.validate_all(auto_create=True)
    
    def check_only(self) -> Tuple[bool, Dict[str, any]]:
        """
        Check directories without creating them (alias for validate_all with auto_create=False).
        
        Returns:
            Tuple of (success: bool, details: dict)
        """
        return self.validate_all(auto_create=False)


def ensure_workspace_directories(workspace_dir: Path, fail_loud: bool = True) -> bool:
    """
    Convenience function to ensure all workspace directories exist.
    
    Args:
        workspace_dir: Base workspace directory
        fail_loud: If True, raise exception on failure; if False, return False
        
    Returns:
        True if all directories exist and are accessible, False otherwise
        
    Raises:
        RuntimeError: If fail_loud=True and validation fails
    """
    validator = DirectoryValidator(workspace_dir)
    success, details = validator.ensure_all_directories()
    
    if not success:
        error_msg = "\n".join([
            "=" * 60,
            "CRITICAL: Required directories are missing or inaccessible",
            "=" * 60,
            "",
            f"Workspace: {workspace_dir}",
            "",
            "Errors:",
            *[f"  ❌ {e}" for e in details["errors"]],
            "",
            "Fix Steps:",
            *[f"  💡 {f}" for f in details["fixes"]],
            "",
            "=" * 60,
        ])
        
        logger.error(error_msg)
        
        if fail_loud:
            raise RuntimeError(
                f"Directory validation failed. {len(details['errors'])} error(s).\n"
                f"See logs above for details and fix steps."
            )
    
    if details.get("warnings"):
        warning_msg = "\n".join([
            "Warnings:",
            *[f"  ⚠️  {w}" for w in details["warnings"]],
        ])
        logger.warning(warning_msg)
    
    return success

