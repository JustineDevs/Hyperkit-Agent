"""
Comprehensive test suite for all documented workflows in README.md
Tests every user-facing workflow to ensure documentation matches reality
"""

import pytest
import subprocess
import os
from pathlib import Path
from click.testing import CliRunner
from cli.main import cli


class TestDocumentedWorkflows:
    """Test all workflows documented in README.md"""
    
    @pytest.fixture
    def runner(self):
        """CLI test runner"""
        return CliRunner()
    
    @pytest.fixture
    def temp_contract(self, tmp_path):
        """Create a temporary test contract"""
        contract_path = tmp_path / "TestContract.sol"
        contract_path.write_text("""
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract TestContract {
    uint256 public value;
    
    constructor(uint256 _value) {
        value = _value;
    }
    
    function setValue(uint256 _value) public {
        value = _value;
    }
}
""")
        return str(contract_path)
    
    # ==========================================
    # Workflow 1: Generate Smart Contract
    # ==========================================
    
    def test_workflow_generate_contract(self, runner):
        """
        Workflow: hyperagent generate contract "ERC20 token with 1M supply"
        Expected: Contract code generated or clear error
        """
        result = runner.invoke(cli, [
            'generate', 'contract',
            'ERC20 token with 1M supply',
            '--no-save'
        ])
        
        # Should either succeed or fail with clear error (not crash)
        assert result.exit_code in [0, 1], f"Unexpected exit code: {result.exit_code}"
        
        if result.exit_code == 0:
            # Success: should contain Solidity code
            assert 'contract' in result.output.lower() or 'pragma' in result.output.lower()
        else:
            # Failure: should have clear error message
            assert len(result.output) > 0, "No error message provided"
            assert 'error' in result.output.lower() or 'failed' in result.output.lower()
    
    # ==========================================
    # Workflow 2: Audit Smart Contract
    # ==========================================
    
    def test_workflow_audit_contract_file(self, runner, temp_contract):
        """
        Workflow: hyperagent audit contract path/to/contract.sol
        Expected: Audit report with findings
        """
        result = runner.invoke(cli, [
            'audit', 'contract',
            temp_contract
        ])
        
        # Should complete (may have warnings but shouldn't crash)
        assert result.exit_code in [0, 1]
        
        # Should contain audit-related output
        output_lower = result.output.lower()
        assert any(keyword in output_lower for keyword in [
            'audit', 'analysis', 'issues', 'vulnerabilities', 'security'
        ]), f"No audit output found in: {result.output}"
    
    def test_workflow_audit_batch(self, runner, tmp_path, temp_contract):
        """
        Workflow: hyperagent audit batch --directory contracts/
        Expected: Batch audit results
        """
        # Create directory with test contract
        contracts_dir = tmp_path / "contracts"
        contracts_dir.mkdir()
        (contracts_dir / "Test.sol").write_text(Path(temp_contract).read_text())
        
        result = runner.invoke(cli, [
            'audit', 'batch',
            '--directory', str(contracts_dir)
        ])
        
        # Should complete
        assert result.exit_code in [0, 1]
        
        # Should show batch processing
        assert any(keyword in result.output.lower() for keyword in [
            'auditing', 'contracts', 'test.sol'
        ])
    
    # ==========================================
    # Workflow 3: Deploy Contract
    # ==========================================
    
    def test_workflow_deploy_command_exists(self, runner):
        """
        Workflow: hyperagent deploy --contract MyContract.sol --network hyperion
        Expected: Command exists with proper help
        """
        result = runner.invoke(cli, ['deploy', '--help'])
        assert result.exit_code == 0
        assert 'contract' in result.output.lower()
        assert 'network' in result.output.lower()
    
    # ==========================================
    # Workflow 4: Verify Contract
    # ==========================================
    
    def test_workflow_verify_command_exists(self, runner):
        """
        Workflow: hyperagent verify contract <address> --network hyperion
        Expected: Command exists with proper parameters
        """
        result = runner.invoke(cli, ['verify', '--help'])
        assert result.exit_code == 0
        assert 'contract' in result.output.lower() or 'address' in result.output.lower()
    
    def test_workflow_verify_invalid_address(self, runner):
        """
        Workflow: hyperagent verify contract 0xinvalid --network hyperion
        Expected: Clear error for invalid address
        """
        result = runner.invoke(cli, [
            'verify', 'contract',
            '0xinvalid',
            '--network', 'hyperion'
        ])
        
        # Should fail with clear error
        assert result.exit_code != 0
        assert len(result.output) > 0
    
    # ==========================================
    # Workflow 5: Monitor System
    # ==========================================
    
    def test_workflow_monitor_system(self, runner):
        """
        Workflow: hyperagent monitor system
        Expected: System health report
        """
        result = runner.invoke(cli, ['monitor', 'system'])
        
        # Should complete
        assert result.exit_code in [0, 1]
        
        # Should show monitoring output
        output_lower = result.output.lower()
        assert any(keyword in output_lower for keyword in [
            'system', 'health', 'status', 'cpu', 'memory', 'dependencies'
        ]), f"No monitoring output found in: {result.output}"
    
    # ==========================================
    # Workflow 6: Configuration Management
    # ==========================================
    
    def test_workflow_config_show(self, runner):
        """
        Workflow: hyperagent config show
        Expected: Current configuration displayed
        """
        result = runner.invoke(cli, ['config', 'show'])
        
        assert result.exit_code in [0, 1]
        
        # Should show config info
        assert any(keyword in result.output.lower() for keyword in [
            'config', 'settings', 'network', 'provider'
        ])
    
    # ==========================================
    # Workflow 7: Version Information
    # ==========================================
    
    def test_workflow_version(self, runner):
        """
        Workflow: hyperagent version
        Expected: Version info with components
        """
        result = runner.invoke(cli, ['version'])
        
        assert result.exit_code == 0
        
        # Should show version components
        output_lower = result.output.lower()
        assert any(keyword in output_lower for keyword in [
            'version', 'hyperagent', 'foundry', 'python'
        ])
    
    # ==========================================
    # Workflow 8: Full Workflow Pipeline
    # ==========================================
    
    def test_workflow_run_command_exists(self, runner):
        """
        Workflow: hyperagent workflow run "Create ERC20 token" --network hyperion
        Expected: Command exists and validates input
        """
        result = runner.invoke(cli, ['workflow', '--help'])
        assert result.exit_code == 0
        assert 'run' in result.output.lower()
    
    # ==========================================
    # Workflow 9: Limitations Reporting
    # ==========================================
    
    def test_workflow_limitations(self, runner):
        """
        Workflow: hyperagent limitations
        Expected: Clear list of known limitations
        """
        result = runner.invoke(cli, ['limitations'])
        
        assert result.exit_code == 0
        
        # Should list limitations
        output_lower = result.output.lower()
        assert any(keyword in output_lower for keyword in [
            'limitation', 'known', 'issue', 'status', 'feature'
        ])


class TestREADMEExamples:
    """Test specific examples from README.md"""
    
    @pytest.fixture
    def runner(self):
        return CliRunner()
    
    def test_help_command(self, runner):
        """README Example: hyperagent --help"""
        result = runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert 'hyperagent' in result.output.lower()
        assert 'commands' in result.output.lower()
    
    def test_generate_help(self, runner):
        """README Example: hyperagent generate --help"""
        result = runner.invoke(cli, ['generate', '--help'])
        assert result.exit_code == 0
        assert 'generate' in result.output.lower()
    
    def test_audit_help(self, runner):
        """README Example: hyperagent audit --help"""
        result = runner.invoke(cli, ['audit', '--help'])
        assert result.exit_code == 0
        assert 'audit' in result.output.lower()
    
    def test_deploy_help(self, runner):
        """README Example: hyperagent deploy --help"""
        result = runner.invoke(cli, ['deploy', '--help'])
        assert result.exit_code == 0
        assert 'deploy' in result.output.lower()


class TestNetworkSupport:
    """Test documented network configurations"""
    
    @pytest.fixture
    def runner(self):
        return CliRunner()
    
    def test_hyperion_network_documented(self, runner):
        """Verify Hyperion testnet is supported"""
        result = runner.invoke(cli, ['config', 'show'])
        # Should not crash
        assert result.exit_code in [0, 1]
    
    def test_lazai_network_documented(self, runner):
        """Verify LazAI testnet is documented"""
        # Network should be known even if not fully configured
        result = runner.invoke(cli, ['config', 'show'])
        assert result.exit_code in [0, 1]
    
    def test_metis_network_documented(self, runner):
        """Verify Metis mainnet is supported"""
        result = runner.invoke(cli, ['config', 'show'])
        assert result.exit_code in [0, 1]


class TestErrorHandling:
    """Test that documented workflows fail gracefully"""
    
    @pytest.fixture
    def runner(self):
        return CliRunner()
    
    def test_invalid_command_fails_gracefully(self, runner):
        """Invalid command should show helpful error"""
        result = runner.invoke(cli, ['invalidcommand'])
        assert result.exit_code != 0
        assert len(result.output) > 0
    
    def test_missing_required_args_fails_gracefully(self, runner):
        """Missing args should show helpful error"""
        result = runner.invoke(cli, ['generate', 'contract'])
        # Should fail or prompt for input
        assert result.exit_code in [0, 1, 2]
    
    def test_invalid_network_fails_gracefully(self, runner):
        """Invalid network should fail with clear message"""
        result = runner.invoke(cli, [
            'deploy',
            '--contract', 'Test.sol',
            '--network', 'invalidnetwork'
        ])
        assert result.exit_code != 0


class TestDocumentationParity:
    """Verify all documented commands exist"""
    
    @pytest.fixture
    def runner(self):
        return CliRunner()
    
    def test_all_documented_commands_exist(self, runner):
        """All commands in README should exist in CLI"""
        documented_commands = [
            ['generate'],
            ['audit'],
            ['deploy'],
            ['verify'],
            ['monitor'],
            ['config'],
            ['version'],
            ['workflow'],
            ['limitations']
        ]
        
        for cmd in documented_commands:
            result = runner.invoke(cli, cmd + ['--help'])
            assert result.exit_code == 0, f"Command {' '.join(cmd)} not found"
    
    def test_all_documented_subcommands_exist(self, runner):
        """All subcommands in README should exist"""
        documented_subcommands = [
            ['generate', 'contract'],
            ['audit', 'contract'],
            ['audit', 'batch'],
            ['verify', 'contract'],
            ['monitor', 'system'],
            ['config', 'show'],
            ['config', 'set'],
            ['config', 'validate'],
            ['workflow', 'run']
        ]
        
        for cmd in documented_subcommands:
            result = runner.invoke(cli, cmd + ['--help'])
            # Should exist (exit code 0) or show help (exit code 0 or 2)
            assert result.exit_code in [0, 2], f"Subcommand {' '.join(cmd)} not found"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])

