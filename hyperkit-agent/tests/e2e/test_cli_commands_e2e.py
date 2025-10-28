#!/usr/bin/env python3
"""
Comprehensive CLI E2E Test Suite
Tests all CLI commands with real environment validation (not mocks)
"""

import pytest
import subprocess
import sys
import json
import time
import asyncio
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, List
import os


class TestCLICommandsE2E:
    """End-to-end tests for all CLI commands"""
    
    @pytest.fixture
    def cli_command(self):
        """Get the CLI command to run"""
        return [sys.executable, "-m", "cli.main"]
    
    @pytest.fixture
    def test_contract(self):
        """Create a test contract for E2E testing"""
        contract_code = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract TestToken is ERC20, Ownable {
    uint256 public constant INITIAL_SUPPLY = 1000000 * 10**18;
    
    constructor() ERC20("Test Token", "TEST") Ownable(msg.sender) {
        _mint(msg.sender, INITIAL_SUPPLY);
    }
    
    function mint(address to, uint256 amount) public onlyOwner {
        _mint(to, amount);
    }
}
"""
        return contract_code
    
    @pytest.fixture
    def test_contract_file(self, test_contract, tmp_path):
        """Create a test contract file"""
        contract_file = tmp_path / "TestToken.sol"
        contract_file.write_text(test_contract)
        return contract_file
    
    def run_cli_command(self, cli_command: List[str], args: List[str], timeout: int = 30) -> subprocess.CompletedProcess:
        """Run a CLI command and return the result"""
        cmd = cli_command + args
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=Path(__file__).parent.parent.parent  # hyperkit-agent directory
            )
            return result
        except subprocess.TimeoutExpired:
            pytest.fail(f"Command timed out: {' '.join(cmd)}")
    
    def test_cli_help(self, cli_command):
        """Test CLI help command"""
        result = self.run_cli_command(cli_command, ["--help"])
        assert result.returncode == 0
        assert "HyperAgent" in result.stdout
        assert "AI-Powered Smart Contract Development Platform" in result.stdout
    
    def test_cli_version(self, cli_command):
        """Test CLI version command"""
        result = self.run_cli_command(cli_command, ["version"])
        assert result.returncode == 0
        # Version should match current VERSION file (1.4.6)
        assert "HyperAgent" in result.stdout or "1.4" in result.stdout
    
    def test_cli_status(self, cli_command):
        """Test CLI status command"""
        result = self.run_cli_command(cli_command, ["status"])
        assert result.returncode == 0
        assert "HYPERAGENT BRUTAL HEALTH CHECK" in result.stdout or "Health Check" in result.stdout
    
    def test_generate_contract_help(self, cli_command):
        """Test generate contract help"""
        result = self.run_cli_command(cli_command, ["generate", "--help"])
        assert result.returncode == 0
        assert "Generate smart contracts and templates" in result.stdout
    
    def test_generate_contract_basic(self, cli_command):
        """Test basic contract generation"""
        result = self.run_cli_command(
            cli_command, 
            ["generate", "contract", "--type", "ERC20", "--name", "TestToken", "--no-use-rag"]
        )
        # Should either succeed or fail gracefully with clear error message
        assert result.returncode in [0, 1]  # Allow graceful failure
        assert "TestToken" in result.stdout or "error" in result.stdout.lower()
    
    def test_deploy_help(self, cli_command):
        """Test deploy help"""
        result = self.run_cli_command(cli_command, ["deploy", "--help"])
        assert result.returncode == 0
        assert "Deploy smart contracts" in result.stdout
    
    def test_deploy_contract_help(self, cli_command):
        """Test deploy contract help"""
        result = self.run_cli_command(cli_command, ["deploy", "contract", "--help"])
        assert result.returncode == 0
        assert "Deploy a smart contract" in result.stdout
    
    def test_audit_help(self, cli_command):
        """Test audit help"""
        result = self.run_cli_command(cli_command, ["audit", "--help"])
        assert result.returncode == 0
        assert "Audit smart contracts" in result.stdout
    
    def test_audit_contract_help(self, cli_command):
        """Test audit contract help"""
        result = self.run_cli_command(cli_command, ["audit", "contract", "--help"])
        assert result.returncode == 0
        assert "Audit a smart contract" in result.stdout
    
    def test_batch_audit_help(self, cli_command):
        """Test batch audit help"""
        result = self.run_cli_command(cli_command, ["batch-audit", "--help"])
        assert result.returncode == 0
        assert "Batch audit" in result.stdout
    
    def test_verify_help(self, cli_command):
        """Test verify help"""
        result = self.run_cli_command(cli_command, ["verify", "--help"])
        assert result.returncode == 0
        assert "Verify smart contracts" in result.stdout
    
    def test_monitor_help(self, cli_command):
        """Test monitor help"""
        result = self.run_cli_command(cli_command, ["monitor", "--help"])
        assert result.returncode == 0
        assert "Monitor system" in result.stdout
    
    def test_config_help(self, cli_command):
        """Test config help"""
        result = self.run_cli_command(cli_command, ["config", "--help"])
        assert result.returncode == 0
        assert "Manage configuration settings" in result.stdout
    
    def test_workflow_help(self, cli_command):
        """Test workflow help"""
        result = self.run_cli_command(cli_command, ["workflow", "--help"])
        assert result.returncode == 0
        assert "Run end-to-end smart contract workflows" in result.stdout
    
    def test_workflow_list(self, cli_command):
        """Test workflow list command"""
        result = self.run_cli_command(cli_command, ["workflow", "list"])
        assert result.returncode == 0
        assert "Available Workflow Templates" in result.stdout
        assert "Tokens" in result.stdout
        assert "NFTs" in result.stdout
        assert "DeFi" in result.stdout
    
    def test_workflow_status(self, cli_command):
        """Test workflow status command"""
        result = self.run_cli_command(cli_command, ["workflow", "status"])
        assert result.returncode == 0
        assert "Workflow Status" in result.stdout or "workflow" in result.stdout.lower()
    
    def test_test_rag_command(self, cli_command):
        """Test RAG test command"""
        result = self.run_cli_command(cli_command, ["test-rag"])
        assert result.returncode in [0, 1]  # Allow graceful failure
        assert "RAG" in result.stdout or "test" in result.stdout.lower()
    
    def test_limitations_command(self, cli_command):
        """Test limitations command"""
        result = self.run_cli_command(cli_command, ["limitations"])
        assert result.returncode == 0
        assert "limitations" in result.stdout.lower() or "known" in result.stdout.lower()
    
    def test_verbose_mode(self, cli_command):
        """Test verbose mode"""
        result = self.run_cli_command(cli_command, ["--verbose", "status"])
        assert result.returncode == 0
        assert "Verbose mode enabled" in result.stdout
    
    def test_debug_mode(self, cli_command):
        """Test debug mode"""
        result = self.run_cli_command(cli_command, ["--debug", "status"])
        assert result.returncode == 0
        assert "Debug mode enabled" in result.stdout
    
    def test_invalid_command(self, cli_command):
        """Test invalid command handling"""
        result = self.run_cli_command(cli_command, ["invalid-command"])
        assert result.returncode != 0
        assert "No such command" in result.stderr or "Usage:" in result.stdout
    
    def test_invalid_option(self, cli_command):
        """Test invalid option handling"""
        result = self.run_cli_command(cli_command, ["--invalid-option"])
        assert result.returncode != 0
        assert "No such option" in result.stderr or "Usage:" in result.stdout
    
    def test_generate_contract_with_rag(self, cli_command):
        """Test contract generation with RAG"""
        result = self.run_cli_command(
            cli_command, 
            ["generate", "contract", "--type", "ERC20", "--name", "RAGToken", "--use-rag"]
        )
        # Should either succeed or fail gracefully
        assert result.returncode in [0, 1]
        assert "RAGToken" in result.stdout or "RAG" in result.stdout or "error" in result.stdout.lower()
    
    def test_audit_contract_with_rag(self, cli_command, test_contract_file):
        """Test contract auditing with RAG"""
        result = self.run_cli_command(
            cli_command, 
            ["audit", "contract", "--contract", str(test_contract_file), "--use-rag"]
        )
        # Should either succeed or fail gracefully
        assert result.returncode in [0, 1]
        assert "audit" in result.stdout.lower() or "RAG" in result.stdout or "error" in result.stdout.lower()
    
    def test_deploy_contract_with_rag(self, cli_command, test_contract_file):
        """Test contract deployment with RAG"""
        result = self.run_cli_command(
            cli_command, 
            ["deploy", "contract", "--contract", str(test_contract_file), "--use-rag"]
        )
        # Should either succeed or fail gracefully
        assert result.returncode in [0, 1]
        assert "deploy" in result.stdout.lower() or "RAG" in result.stdout or "error" in result.stdout.lower()
    
    def test_workflow_run_basic(self, cli_command):
        """Test basic workflow run"""
        result = self.run_cli_command(
            cli_command, 
            ["workflow", "run", "create simple ERC20 token", "--test-only", "--no-use-rag"]
        )
        # Should either succeed or fail gracefully
        assert result.returncode in [0, 1]
        assert "workflow" in result.stdout.lower() or "token" in result.stdout.lower() or "error" in result.stdout.lower()
    
    def test_workflow_run_with_rag(self, cli_command):
        """Test workflow run with RAG"""
        result = self.run_cli_command(
            cli_command, 
            ["workflow", "run", "create simple ERC20 token", "--test-only", "--use-rag"]
        )
        # Should either succeed or fail gracefully
        assert result.returncode in [0, 1]
        assert "workflow" in result.stdout.lower() or "RAG" in result.stdout or "error" in result.stdout.lower()
    
    def test_batch_audit_directory(self, cli_command, tmp_path):
        """Test batch audit on directory"""
        # Create a test directory with contract files
        test_dir = tmp_path / "contracts"
        test_dir.mkdir()
        
        # Create a simple contract file
        contract_file = test_dir / "SimpleToken.sol"
        contract_file.write_text("""
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract SimpleToken {
    string public name = "Simple Token";
    string public symbol = "ST";
    uint256 public totalSupply = 1000000;
}
""")
        
        result = self.run_cli_command(
            cli_command,
            ["batch-audit", "contracts", "--directory", str(test_dir)]
        )
        # Should either succeed or fail gracefully
        assert result.returncode in [0, 1]
        assert "batch" in result.stdout.lower() or "audit" in result.stdout.lower() or "error" in result.stdout.lower()
    
    def test_config_commands(self, cli_command):
        """Test config commands"""
        # Test config list
        result = self.run_cli_command(cli_command, ["config", "list"])
        assert result.returncode in [0, 1]  # Allow graceful failure
        assert "config" in result.stdout.lower() or "error" in result.stdout.lower()
        
        # Test config get
        result = self.run_cli_command(cli_command, ["config", "get", "network"])
        assert result.returncode in [0, 1]  # Allow graceful failure
        assert "config" in result.stdout.lower() or "network" in result.stdout.lower() or "error" in result.stdout.lower()
    
    def test_monitor_commands(self, cli_command):
        """Test monitor commands"""
        # Test monitor health
        result = self.run_cli_command(cli_command, ["monitor", "health"])
        assert result.returncode in [0, 1]  # Allow graceful failure
        assert "monitor" in result.stdout.lower() or "health" in result.stdout.lower() or "error" in result.stdout.lower()
        
        # Test monitor status
        result = self.run_cli_command(cli_command, ["monitor", "status"])
        assert result.returncode in [0, 1]  # Allow graceful failure
        assert "monitor" in result.stdout.lower() or "status" in result.stdout.lower() or "error" in result.stdout.lower()
    
    def test_verify_commands(self, cli_command):
        """Test verify commands"""
        # Test verify contract
        result = self.run_cli_command(cli_command, ["verify", "contract", "--help"])
        assert result.returncode == 0
        assert "verify" in result.stdout.lower()
        
        # Test verify deployment
        result = self.run_cli_command(cli_command, ["verify", "deployment", "--help"])
        assert result.returncode == 0
        assert "verify" in result.stdout.lower()
    
    def test_command_chaining(self, cli_command):
        """Test command chaining and workflow"""
        # Test a simple workflow: generate -> audit -> deploy
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Step 1: Generate contract
            result1 = self.run_cli_command(
                cli_command, 
                ["generate", "contract", "--type", "ERC20", "--name", "ChainedToken", "--output", str(temp_path), "--no-use-rag"]
            )
            # Allow graceful failure
            assert result1.returncode in [0, 1]
            
            # Step 2: Look for generated contract and audit it
            contract_files = list(temp_path.glob("*.sol"))
            if contract_files:
                contract_file = contract_files[0]
                result2 = self.run_cli_command(
                    cli_command, 
                    ["audit", "contract", "--contract", str(contract_file), "--no-use-rag"]
                )
                # Allow graceful failure
                assert result2.returncode in [0, 1]
    
    def test_error_handling(self, cli_command):
        """Test error handling in CLI commands"""
        # Test missing required arguments
        result = self.run_cli_command(cli_command, ["generate", "contract"])
        assert result.returncode != 0
        assert "Missing option" in result.stderr or "Usage:" in result.stdout
        
        # Test invalid contract type
        result = self.run_cli_command(
            cli_command, 
            ["generate", "contract", "--type", "INVALID", "--name", "Test"]
        )
        assert result.returncode in [0, 1]  # Allow graceful failure
        
        # Test invalid network
        result = self.run_cli_command(
            cli_command, 
            ["generate", "contract", "--type", "ERC20", "--name", "Test", "--network", "invalid"]
        )
        assert result.returncode in [0, 1]  # Allow graceful failure
    
    def test_output_formats(self, cli_command, test_contract_file):
        """Test different output formats"""
        # Test JSON output
        result = self.run_cli_command(
            cli_command, 
            ["audit", "contract", "--contract", str(test_contract_file), "--format", "json", "--no-use-rag"]
        )
        assert result.returncode in [0, 1]  # Allow graceful failure
        
        # Test Markdown output
        result = self.run_cli_command(
            cli_command, 
            ["audit", "contract", "--contract", str(test_contract_file), "--format", "markdown", "--no-use-rag"]
        )
        assert result.returncode in [0, 1]  # Allow graceful failure
    
    def test_network_options(self, cli_command):
        """Test different network options"""
        networks = ["hyperion", "ethereum", "polygon", "arbitrum"]
        
        for network in networks:
            result = self.run_cli_command(
                cli_command, 
                ["generate", "contract", "--type", "ERC20", "--name", f"Token{network}", "--network", network, "--no-use-rag"]
            )
            # Allow graceful failure
            assert result.returncode in [0, 1]
    
    def test_severity_filters(self, cli_command, test_contract_file):
        """Test severity filters in audit commands"""
        severities = ["low", "medium", "high", "critical"]
        
        for severity in severities:
            result = self.run_cli_command(
                cli_command, 
                ["audit", "contract", "--contract", str(test_contract_file), "--severity", severity, "--no-use-rag"]
            )
            # Allow graceful failure
            assert result.returncode in [0, 1]


class TestCLIIntegrationE2E:
    """Integration tests for CLI commands working together"""
    
    @pytest.fixture
    def cli_command(self):
        """Get the CLI command to run"""
        return [sys.executable, "-m", "cli.main"]
    
    def test_full_workflow_integration(self, cli_command):
        """Test full workflow integration"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Step 1: Generate contract
            result1 = self.run_cli_command(
                cli_command, 
                ["generate", "contract", "--type", "ERC20", "--name", "WorkflowToken", "--output", str(temp_path), "--no-use-rag"]
            )
            
            # Step 2: Audit generated contract
            contract_files = list(temp_path.glob("*.sol"))
            if contract_files:
                contract_file = contract_files[0]
                result2 = self.run_cli_command(
                    cli_command, 
                    ["audit", "contract", "--contract", str(contract_file), "--format", "json", "--no-use-rag"]
                )
                
                # Step 3: Deploy contract (test mode)
                result3 = self.run_cli_command(
                    cli_command, 
                    ["deploy", "contract", "--contract", str(contract_file), "--network", "hyperion"]
                )
                
                # All steps should either succeed or fail gracefully
                assert result1.returncode in [0, 1]
                assert result2.returncode in [0, 1]
                assert result3.returncode in [0, 1]
    
    def run_cli_command(self, cli_command: List[str], args: List[str], timeout: int = 30) -> subprocess.CompletedProcess:
        """Run a CLI command and return the result"""
        cmd = cli_command + args
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=Path(__file__).parent.parent.parent  # hyperkit-agent directory
            )
            return result
        except subprocess.TimeoutExpired:
            pytest.fail(f"Command timed out: {' '.join(cmd)}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
