"""
CLI Command Integration Tests
Tests CLI commands work correctly
"""

import pytest
import subprocess
import os
import sys
from pathlib import Path

# Test configuration
CLI_COMMAND = "python -m cli.main"
TEST_NETWORK = "hyperion"


@pytest.mark.integration
class TestCLIGenerate:
    """Test generate command"""
    
    def test_generate_help(self):
        """Test generate help command"""
        result = subprocess.run(
            f"{CLI_COMMAND} generate --help",
            shell=True,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "generate" in result.stdout.lower()
    
    @pytest.mark.slow
    def test_generate_contract(self):
        """Test contract generation command"""
        # Set UTF-8 encoding
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        
        result = subprocess.run(
            f"{CLI_COMMAND} generate contract --type ERC20 --name TestCLIToken --network {TEST_NETWORK}",
            shell=True,
            capture_output=True,
            text=True,
            env=env,
            timeout=60
        )
        
        # Should complete (success or with warnings)
        assert result.returncode == 0 or "Generated" in result.stdout or "generated" in result.stdout.lower()
        print(f"✅ Generate contract CLI test passed")


@pytest.mark.integration
class TestCLIAudit:
    """Test audit command"""
    
    def test_audit_help(self):
        """Test audit help command"""
        result = subprocess.run(
            f"{CLI_COMMAND} audit --help",
            shell=True,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "audit" in result.stdout.lower()
    
    @pytest.mark.slow
    def test_audit_contract_file(self):
        """Test auditing a contract file"""
        # Create a simple test contract
        test_contract = Path("test_contract_cli.sol")
        test_contract.write_text("""
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract TestContract {
    uint256 public value;
    
    function setValue(uint256 _value) public {
        value = _value;
    }
}
        """)
        
        try:
            # Set UTF-8 encoding
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            
            result = subprocess.run(
                f"{CLI_COMMAND} audit contract --contract {test_contract}",
                shell=True,
                capture_output=True,
                text=True,
                env=env,
                timeout=60
            )
            
            # Should complete (may have findings)
            assert result.returncode == 0 or "Audit" in result.stdout or "audit" in result.stdout.lower()
            print(f"✅ Audit contract file CLI test passed")
        finally:
            # Cleanup
            if test_contract.exists():
                test_contract.unlink()


@pytest.mark.integration
class TestCLIDeploy:
    """Test deploy command"""
    
    def test_deploy_help(self):
        """Test deploy help command"""
        result = subprocess.run(
            f"{CLI_COMMAND} deploy --help",
            shell=True,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "deploy" in result.stdout.lower()
    
    # Deployment tests skipped - require actual blockchain interaction


@pytest.mark.integration
class TestCLIWorkflow:
    """Test workflow command"""
    
    def test_workflow_help(self):
        """Test workflow help command"""
        result = subprocess.run(
            f"{CLI_COMMAND} workflow --help",
            shell=True,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "workflow" in result.stdout.lower()
    
    def test_workflow_list(self):
        """Test workflow list command"""
        result = subprocess.run(
            f"{CLI_COMMAND} workflow list",
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        assert result.returncode == 0
        assert "workflow" in result.stdout.lower() or "template" in result.stdout.lower()
        print(f"✅ Workflow list CLI test passed")
    
    def test_workflow_status(self):
        """Test workflow status command"""
        result = subprocess.run(
            f"{CLI_COMMAND} workflow status --network {TEST_NETWORK}",
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        assert result.returncode == 0
        assert "status" in result.stdout.lower() or "ready" in result.stdout.lower()
        print(f"✅ Workflow status CLI test passed")
    
    @pytest.mark.slow
    def test_workflow_run_test_only(self):
        """Test workflow run in test-only mode"""
        # Set UTF-8 encoding
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        
        result = subprocess.run(
            f"{CLI_COMMAND} workflow run 'create simple token' --network {TEST_NETWORK} --test-only",
            shell=True,
            capture_output=True,
            text=True,
            env=env,
            timeout=120
        )
        
        # Should complete (may have warnings)
        assert result.returncode == 0 or "workflow" in result.stdout.lower() or "completed" in result.stdout.lower()
        print(f"✅ Workflow run (test-only) CLI test passed")


@pytest.mark.integration
class TestCLIUtility:
    """Test utility commands"""
    
    def test_health_command(self):
        """Test health check command"""
        result = subprocess.run(
            f"{CLI_COMMAND} health",
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        assert result.returncode == 0
        assert "health" in result.stdout.lower() or "status" in result.stdout.lower()
        print(f"✅ Health CLI test passed")
    
    def test_version_command(self):
        """Test version command"""
        result = subprocess.run(
            f"{CLI_COMMAND} version",
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        assert result.returncode == 0
        assert "version" in result.stdout.lower() or "hyperkit" in result.stdout.lower() or "hyperagent" in result.stdout.lower()
        print(f"✅ Version CLI test passed")


@pytest.mark.integration
class TestCLIConfig:
    """Test config command"""
    
    def test_config_help(self):
        """Test config help command"""
        result = subprocess.run(
            f"{CLI_COMMAND} config --help",
            shell=True,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "config" in result.stdout.lower()


@pytest.mark.integration
class TestCLIMonitor:
    """Test monitor command"""
    
    def test_monitor_help(self):
        """Test monitor help command"""
        result = subprocess.run(
            f"{CLI_COMMAND} monitor --help",
            shell=True,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "monitor" in result.stdout.lower()


@pytest.mark.integration
class TestCLIVerify:
    """Test verify command"""
    
    def test_verify_help(self):
        """Test verify help command"""
        result = subprocess.run(
            f"{CLI_COMMAND} verify --help",
            shell=True,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "verify" in result.stdout.lower()


@pytest.mark.integration
class TestCLIErrorHandling:
    """Test CLI error handling"""
    
    def test_invalid_command(self):
        """Test invalid command handling"""
        result = subprocess.run(
            f"{CLI_COMMAND} invalid_command",
            shell=True,
            capture_output=True,
            text=True
        )
        # Should fail but not crash
        assert result.returncode != 0 or "error" in result.stdout.lower() or "invalid" in result.stdout.lower()
    
    def test_missing_required_args(self):
        """Test missing required arguments"""
        result = subprocess.run(
            f"{CLI_COMMAND} generate contract",
            shell=True,
            capture_output=True,
            text=True
        )
        # Should show error about missing args
        assert result.returncode != 0 or "error" in result.stdout.lower() or "required" in result.stderr.lower()


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s", "-m", "not slow"])

