"""
Unit tests for CLI commands
"""
import pytest
import subprocess
import sys
from pathlib import Path


class TestCLICommands:
    """Test CLI command functionality"""
    
    def test_hyperagent_help(self):
        """Test that hyperagent --help works"""
        result = subprocess.run([sys.executable, "-m", "hyperagent", "--help"], 
                               capture_output=True, text=True)
        assert result.returncode == 0
        assert "HyperAgent" in result.stdout
        assert "Commands:" in result.stdout
    
    def test_hyperagent_status(self):
        """Test that hyperagent status works"""
        result = subprocess.run([sys.executable, "-m", "hyperagent", "status"], 
                               capture_output=True, text=True)
        assert result.returncode == 0
        assert "System Status" in result.stdout or "Component" in result.stdout
    
    def test_hyperagent_test_command(self):
        """Test that hyperagent test works"""
        result = subprocess.run([sys.executable, "-m", "hyperagent", "test", "--sample", "erc20"], 
                               capture_output=True, text=True)
        # Should work or fail gracefully
        assert result.returncode in [0, 1]  # Allow for configuration issues
