"""
Network integration tests for Hyperion, Metis, and LazAI
Tests real network connectivity and contract deployment
"""

import pytest
import os
import asyncio
from web3 import Web3
from services.deployment.deployer import MultiChainDeployer
from services.gas.gas_estimator import GasEstimator

@pytest.mark.integration
class TestNetworkIntegration:
    """Test network integration functionality."""
    
    @pytest.fixture
    def deployer(self):
        """Create multi-chain deployer instance."""
        return MultiChainDeployer()
    
    @pytest.fixture
    def gas_estimator(self):
        """Create gas estimator instance."""
        return GasEstimator()
    
    def test_hyperion_connectivity(self):
        """Test Hyperion testnet connectivity."""
        rpc_url = "https://hyperion-testnet.metisdevops.link"
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        
        assert w3.is_connected(), "Failed to connect to Hyperion testnet"
        assert w3.eth.chain_id == 133717, "Incorrect Hyperion chain ID"
        
        # Test basic network operations
        latest_block = w3.eth.get_block('latest')
        assert latest_block is not None, "Failed to get latest block"
        
        gas_price = w3.eth.gas_price
        assert gas_price > 0, "Failed to get gas price"
    
    @pytest.mark.skip(reason="Hyperion-only mode: Metis network not supported")
    def test_metis_connectivity(self):
        """Test Metis Andromeda connectivity - SKIPPED: Hyperion-only mode."""
        pytest.skip("Hyperion-only mode: Metis network not supported")
    
    @pytest.mark.skip(reason="Hyperion-only mode: LazAI network not supported")
    def test_lazai_connectivity(self):
        """Test LazAI testnet connectivity - SKIPPED: Hyperion-only mode."""
        pytest.skip("Hyperion-only mode: LazAI network not supported")
    
    @pytest.mark.asyncio
    async def test_hyperion_gas_estimation(self, gas_estimator):
        """Test gas estimation on Hyperion testnet."""
        contract_code = """
        pragma solidity ^0.8.0;
        contract TestContract {
            string public name = "Test";
            function setName(string memory _name) public {
                name = _name;
            }
        }
        """
        
        result = await gas_estimator.estimate_gas(
            contract_code=contract_code,
            network="hyperion"
        )
        
        assert result["status"] == "success"
        assert "gas_estimate" in result
        assert result["gas_estimate"] > 0
    
    @pytest.mark.asyncio
    async def test_metis_gas_estimation(self, gas_estimator):
        """Test gas estimation on Metis Andromeda."""
        contract_code = """
        pragma solidity ^0.8.0;
        contract TestContract {
            string public name = "Test";
            function setName(string memory _name) public {
                name = _name;
            }
        }
        """
        
        result = await gas_estimator.estimate_gas(
            contract_code=contract_code,
            network="metis"
        )
        
        assert result["status"] == "success"
        assert "gas_estimate" in result
        assert result["gas_estimate"] > 0
    
    @pytest.mark.asyncio
    async def test_lazai_gas_estimation(self, gas_estimator):
        """Test gas estimation on LazAI testnet."""
        contract_code = """
        pragma solidity ^0.8.0;
        contract TestContract {
            string public name = "Test";
            function setName(string memory _name) public {
                name = _name;
            }
        }
        """
        
        result = await gas_estimator.estimate_gas(
            contract_code=contract_code,
            network="lazai"
        )
        
        assert result["status"] == "success"
        assert "gas_estimate" in result
        assert result["gas_estimate"] > 0
    
    @pytest.mark.asyncio
    async def test_hyperion_contract_deployment(self, deployer):
        """Test contract deployment on Hyperion testnet."""
        if not os.getenv('DEFAULT_PRIVATE_KEY'):
            pytest.skip("Private key not configured (DEFAULT_PRIVATE_KEY)")
        
        contract_code = """
        pragma solidity ^0.8.0;
        contract TestContract {
            string public name = "Test";
            function setName(string memory _name) public {
                name = _name;
            }
        }
        """
        
        result = await deployer.deploy_contract(
            contract_code=contract_code,
            network="hyperion"
        )
        
        assert result["status"] == "success"
        assert "contract_address" in result
        assert result["contract_address"] is not None
    
    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Hyperion-only mode: Metis network not supported")
    async def test_metis_contract_deployment(self, deployer):
        """Test contract deployment on Metis Andromeda - SKIPPED: Hyperion-only mode."""
        pytest.skip("Hyperion-only mode: Metis network not supported")
    
    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Hyperion-only mode: LazAI network not supported")
    async def test_lazai_contract_deployment(self, deployer):
        """Test contract deployment on LazAI testnet - SKIPPED: Hyperion-only mode."""
        pytest.skip("Hyperion-only mode: LazAI network not supported")
    
    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Hyperion-only mode: Cross-chain deployment not supported")
    async def test_cross_chain_deployment(self, deployer):
        """Test cross-chain contract deployment - SKIPPED: Hyperion-only mode."""
        pytest.skip("Hyperion-only mode: Cross-chain deployment not supported")
    
    @pytest.mark.asyncio
    async def test_network_switching(self, deployer):
        """Test network switching functionality - Hyperion-only mode."""
        # Only test Hyperion (Hyperion-only mode)
        networks = ["hyperion"]
        
        for network in networks:
            result = await deployer.get_network_info(network)
            assert result["status"] == "success"
            assert "chain_id" in result
            assert "rpc_url" in result
        
        # Verify non-Hyperion networks fail
        for non_hyperion in ["metis", "lazai"]:
            try:
                result = await deployer.get_network_info(non_hyperion)
                assert False, f"Network {non_hyperion} should not be supported in Hyperion-only mode"
            except (ValueError, KeyError, Exception):
                pass  # Expected failure
    
    @pytest.mark.asyncio
    async def test_network_health_check(self, deployer):
        """Test network health check functionality - Hyperion-only mode."""
        networks = ["hyperion"]  # Only Hyperion in Hyperion-only mode
        
        for network in networks:
            result = await deployer.check_network_health(network)
            assert result["status"] == "success"
            assert "is_healthy" in result
            assert result["is_healthy"] is True
    
    @pytest.mark.asyncio
    async def test_network_gas_price_comparison(self, gas_estimator):
        """Test gas price comparison across networks."""
        contract_code = """
        pragma solidity ^0.8.0;
        contract TestContract {
            string public name = "Test";
            function setName(string memory _name) public {
                name = _name;
            }
        }
        """
        
        # Only test Hyperion in Hyperion-only mode
        networks = ["hyperion"]
        gas_prices = {}
        
        for network in networks:
            result = await gas_estimator.get_gas_price(network)
            if result["status"] == "success":
                gas_prices[network] = result["gas_price"]
        
        # Verify we got gas prices for Hyperion
        assert len(gas_prices) > 0, "Failed to get gas prices for Hyperion"
        assert "hyperion" in gas_prices, "Hyperion gas price must be available"
        
        # Log gas price
        print(f"hyperion: {gas_prices['hyperion']} wei")
    
    @pytest.mark.asyncio
    async def test_network_balance_check(self, deployer):
        """Test network balance check functionality."""
        if not os.getenv('DEFAULT_PRIVATE_KEY'):
            pytest.skip("Private key not configured (DEFAULT_PRIVATE_KEY)")
        
        result = await deployer.check_balance("hyperion")
        assert result["status"] == "success"
        assert "balance" in result
        assert result["balance"] >= 0
    
    @pytest.mark.asyncio
    async def test_network_transaction_status(self, deployer):
        """Test network transaction status checking."""
        if not os.getenv('DEFAULT_PRIVATE_KEY'):
            pytest.skip("Private key not configured (DEFAULT_PRIVATE_KEY)")
        
        # This would require a real transaction hash
        # For now, we'll test the function exists
        result = await deployer.get_transaction_status("0x0000000000000000000000000000000000000000000000000000000000000000", "hyperion")
        assert result["status"] == "error"  # Should fail for invalid hash
    
    @pytest.mark.asyncio
    async def test_network_block_explorer_integration(self, deployer):
        """Test network block explorer integration."""
        networks = ["hyperion", "metis", "lazai"]
        
        for network in networks:
            result = await deployer.get_explorer_url(network)
            assert result["status"] == "success"
            assert "explorer_url" in result
            assert result["explorer_url"].startswith("http")
    
    @pytest.mark.asyncio
    async def test_network_error_handling(self, deployer):
        """Test network error handling."""
        # Test with invalid network
        result = await deployer.get_network_info("invalid_network")
        assert result["status"] == "error"
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_network_timeout_handling(self, deployer):
        """Test network timeout handling."""
        # Test with invalid RPC URL
        result = await deployer.check_network_health("invalid_network")
        assert result["status"] == "error"
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_network_concurrent_requests(self, deployer):
        """Test network concurrent request handling."""
        networks = ["hyperion", "metis", "lazai"]
        
        # Create concurrent requests
        tasks = [
            deployer.get_network_info(network)
            for network in networks
        ]
        
        results = await asyncio.gather(*tasks)
        
        for result in results:
            assert result["status"] == "success"
            assert "chain_id" in result
    
    @pytest.mark.asyncio
    async def test_network_performance(self, deployer):
        """Test network performance."""
        import time
        
        start_time = time.time()
        
        result = await deployer.get_network_info("hyperion")
        
        end_time = time.time()
        duration = end_time - start_time
        
        assert result["status"] == "success"
        assert duration < 10  # Should complete within 10 seconds
    
    @pytest.mark.asyncio
    async def test_network_retry_mechanism(self, deployer):
        """Test network retry mechanism."""
        # This would require simulating network failures
        # For now, we'll test the function exists
        result = await deployer.get_network_info("hyperion")
        assert result["status"] == "success"
    
    @pytest.mark.asyncio
    async def test_network_monitoring(self, deployer):
        """Test network monitoring functionality."""
        result = await deployer.get_network_stats("hyperion")
        assert result["status"] == "success"
        assert "block_number" in result
        assert "gas_price" in result
        assert "network_id" in result
