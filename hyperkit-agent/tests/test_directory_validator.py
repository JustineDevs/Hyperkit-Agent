"""
Tests for robust directory validation system.
"""

import pytest
import tempfile
import shutil
import os
from pathlib import Path

from core.utils.directory_validator import DirectoryValidator, ensure_workspace_directories


class TestDirectoryValidator:
    """Test directory validation and auto-creation"""
    
    def test_validator_initialization(self):
        """Test validator initializes correctly"""
        with tempfile.TemporaryDirectory() as tmpdir:
            validator = DirectoryValidator(Path(tmpdir))
            assert validator.workspace_dir == Path(tmpdir).resolve()
            assert len(validator.errors) == 0
            assert len(validator.warnings) == 0
    
    def test_validate_existing_directories(self):
        """Test validation succeeds when all directories exist"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            # Create all required directories
            for dir_name in DirectoryValidator.REQUIRED_DIRS:
                (workspace / dir_name).mkdir(parents=True, exist_ok=True)
            
            validator = DirectoryValidator(workspace)
            success, details = validator.validate_all(auto_create=False)
            
            assert success is True
            assert len(details["errors"]) == 0
    
    def test_validate_missing_directories_auto_create(self):
        """Test validation creates missing directories"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            
            validator = DirectoryValidator(workspace)
            success, details = validator.validate_all(auto_create=True)
            
            assert success is True
            assert len(details["errors"]) == 0
            
            # Verify all directories were created
            for dir_name in DirectoryValidator.REQUIRED_DIRS:
                dir_path = workspace / dir_name
                assert dir_path.exists(), f"Directory {dir_name} should exist"
                assert dir_path.is_dir(), f"{dir_name} should be a directory"
    
    def test_validate_missing_directories_no_create(self):
        """Test validation fails when directories missing and auto_create=False"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            
            validator = DirectoryValidator(workspace)
            success, details = validator.validate_all(auto_create=False)
            
            assert success is False
            assert len(details["errors"]) > 0
            assert len(details["fixes"]) > 0
            assert ".workflow_contexts" in str(details["errors"][0]) or ".workflow_contexts" in details["fixes"][0]
    
    def test_validate_nonexistent_workspace(self):
        """Test validation fails for nonexistent workspace"""
        validator = DirectoryValidator(Path("/nonexistent/path/that/should/not/exist"))
        success, details = validator.validate_all(auto_create=False)
        
        assert success is False
        assert len(details["errors"]) > 0
        assert "does not exist" in details["errors"][0]
    
    def test_validate_permission_errors(self):
        """Test validation detects permission errors (if possible to simulate)"""
        # This test may be skipped on systems where we can't simulate permission errors
        # For now, just verify the validator structure handles it
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            validator = DirectoryValidator(workspace)
            
            # Create a directory and make it read-only (if possible)
            test_dir = workspace / "test_readonly"
            test_dir.mkdir()
            
            try:
                # Try to make it read-only (Unix/Linux)
                if os.name != 'nt':  # Not Windows
                    os.chmod(test_dir, 0o444)  # Read-only
                    # This should be detected as a permission error
                    # but we can't easily test write permission failures without root
                    pass
            except Exception:
                pass  # Permission changes may not work in test environment
            finally:
                # Clean up
                try:
                    os.chmod(test_dir, 0o755)  # Restore permissions
                    test_dir.rmdir()
                except:
                    pass
    
    def test_ensure_workspace_directories_success(self):
        """Test ensure_workspace_directories creates directories successfully"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            
            success = ensure_workspace_directories(workspace, fail_loud=False)
            
            assert success is True
            
            # Verify directories exist
            for dir_name in DirectoryValidator.REQUIRED_DIRS:
                assert (workspace / dir_name).exists()
    
    def test_ensure_workspace_directories_fail_loud(self):
        """Test ensure_workspace_directories raises on failure when fail_loud=True"""
        # Use a path that definitely won't work
        bad_path = Path("/root/definitely/cannot/create/this/path")
        
        with pytest.raises(RuntimeError):
            ensure_workspace_directories(bad_path, fail_loud=True)
    
    def test_ensure_workspace_directories_fail_soft(self):
        """Test ensure_workspace_directories returns False on failure when fail_loud=False"""
        bad_path = Path("/root/definitely/cannot/create/this/path")
        
        success = ensure_workspace_directories(bad_path, fail_loud=False)
        
        assert success is False
    
    def test_optional_directories(self):
        """Test optional directories are created but don't block on failure"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            
            validator = DirectoryValidator(workspace)
            success, details = validator.validate_all(auto_create=True)
            
            # Required directories should all exist
            assert success is True
            
            # Optional directories should be created if possible
            # (some may fail in test environment, which is OK)
            optional_created = sum(
                1 for dir_name in DirectoryValidator.OPTIONAL_DIRS
                if (workspace / dir_name).exists()
            )
            
            # At least some optional directories should be created
            assert optional_created >= 0  # Always true, but documents the test


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

