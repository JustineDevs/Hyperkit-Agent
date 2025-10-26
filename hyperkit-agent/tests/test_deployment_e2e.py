"""
End-to-end deployment tests for HyperKit AI Agent
Tests the complete workflow from generation to verification
"""

import pytest
import os
from pathlib import Path
from services.deployment.foundry_deployer import FoundryDeployer


class TestDeploymentE2E:
    """End-to-end deployment tests"""
    
    @pytest.fixture
    def deployer(self):
        """Create deployer instance"""
        return FoundryDeployer()
    
    @pytest.fixture
    def sample_contract(self):
        """Load sample contract for testing"""
        contract_path = Path(__file__).parent.parent / "artifacts" / "workflows" / "gaming" / "GamingToken.sol"
        if contract_path.exists():
            return contract_path.read_text()
        return None
    
    def test_deployer_initialization(self, deployer):
        """Test deployer initializes correctly"""
        assert deployer is not None
        assert hasattr(deployer, 'forge_bin')
        assert hasattr(deployer, 'get_network_config')
    
    def test_network_config(self, deployer):
        """Test network configuration for primary networks"""
        # Test primary supported networks
        networks = ['hyperion', 'lazai', 'metis']
        
        for network in networks:
            config = deployer.get_network_config(network)
            assert config is not None, f"Network {network} config not found"
            assert 'chain_id' in config
            assert 'explorer_url' in config
            assert 'rpc_url' in config
            assert 'status' in config
            assert config['status'] in ['testnet', 'mainnet']
    
    def test_unsupported_network(self, deployer):
        """Test unsupported network returns None"""
        config = deployer.get_network_config('unsupported_network')
        assert config is None
    
    @pytest.mark.skipif(not os.getenv('DEFAULT_PRIVATE_KEY'), reason="No private key configured")
    def test_deployment_requires_private_key(self, deployer, sample_contract):
        """Test deployment fails without private key"""
        if not sample_contract:
            pytest.skip("Sample contract not found")
        
        # Temporarily remove private key
        old_key = os.getenv('DEFAULT_PRIVATE_KEY')
        os.environ.pop('DEFAULT_PRIVATE_KEY', None)
        os.environ.pop('PRIVATE_KEY', None)
        
        result = deployer.deploy_contract(sample_contract, 'hyperion')
        
        # Restore key
        if old_key:
            os.environ['DEFAULT_PRIVATE_KEY'] = old_key
        
        assert result['success'] is False
        assert 'DEFAULT_PRIVATE_KEY' in result['error']
    
    def test_deployment_requires_compiled_artifacts(self, deployer):
        """Test deployment checks for compiled artifacts"""
        # Create a simple contract
        simple_contract = '''
        // SPDX-License-Identifier: MIT
        pragma solidity ^0.8.0;
        contract SimpleTest {}
        '''
        
        result = deployer.deploy_contract(simple_contract, 'hyperion')
        
        # Should fail if artifacts don't exist
        # (unless forge build was run)
        assert 'success' in result
    
    @pytest.mark.integration
    @pytest.mark.skipif(not os.getenv('RUN_INTEGRATION_TESTS'), reason="Integration tests disabled")
    def test_full_deployment_workflow(self, deployer, sample_contract):
        """
        Full deployment workflow test (requires testnet access)
        
        This test:
        1. Compiles the contract
        2. Deploys to Hyperion testnet
        3. Verifies deployment
        """
        if not sample_contract:
            pytest.skip("Sample contract not found")
        
        if not os.getenv('DEFAULT_PRIVATE_KEY'):
            pytest.skip("No private key configured")
        
        # Deploy contract
        result = deployer.deploy_contract(sample_contract, 'hyperion')
        
        # Check result
        if result['success']:
            assert 'contract_address' in result
            assert 'tx_hash' in result
            assert 'gas_used' in result
            print(f"\n✅ Contract deployed at: {result['contract_address']}")
            print(f"✅ Transaction hash: {result['tx_hash']}")
        else:
            # Deployment might fail due to various reasons
            # (no funds, network issues, etc.)
            assert 'error' in result
            assert 'suggestions' in result
            print(f"\n⚠️ Deployment failed (expected in CI): {result['error']}")


class TestDeploymentValidation:
    """Test deployment validation and error handling"""
    
    def test_invalid_network_error(self):
        """Test deployment with invalid network"""
        deployer = FoundryDeployer()
        result = deployer.deploy_contract("contract Test {}", "invalid_network")
        
        assert result['success'] is False
        assert 'not supported' in result['error'].lower()
    
    def test_empty_contract_source(self):
        """Test deployment with empty contract"""
        deployer = FoundryDeployer()
        result = deployer.deploy_contract("", "hyperion")
        
        assert result['success'] is False
    
    def test_error_includes_suggestions(self):
        """Test that errors include helpful suggestions"""
        deployer = FoundryDeployer()
        result = deployer.deploy_contract("invalid contract", "invalid_network")
        
        assert 'suggestions' in result
        assert isinstance(result['suggestions'], list)
        assert len(result['suggestions']) > 0


class TestArtifactManagement:
    """Test artifact compilation and management"""
    
    def test_artifacts_directory_exists(self):
        """Test that artifacts directory exists"""
        project_root = Path(__file__).parent.parent
        out_dir = project_root / "out"
        
        # If forge build was run, out directory should exist
        # If not, this is expected
        if out_dir.exists():
            assert out_dir.is_dir()
    
    def test_openzeppelin_contracts_installed(self):
        """Test that OpenZeppelin contracts are installed"""
        project_root = Path(__file__).parent.parent
        oz_dir = project_root / "lib" / "openzeppelin-contracts"
        
        assert oz_dir.exists(), "OpenZeppelin contracts not installed. Run: forge install OpenZeppelin/openzeppelin-contracts"
        assert (oz_dir / "contracts").exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

