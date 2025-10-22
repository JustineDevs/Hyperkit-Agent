#!/usr/bin/env python3
"""
Gas Estimation Service
Provides gas estimation for contract deployment and function calls.
Follows .cursor/rules for production-ready implementation.
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from pathlib import Path
import asyncio
import aiohttp
from web3 import Web3
from web3.exceptions import ContractLogicError, Web3ValidationError

logger = logging.getLogger(__name__)

@dataclass
class GasEstimate:
    """Represents a gas estimate result."""
    gas_limit: int
    gas_price: int
    max_fee_per_gas: Optional[int] = None
    max_priority_fee_per_gas: Optional[int] = None
    total_cost_wei: int = 0
    total_cost_eth: float = 0.0
    confidence: str = "medium"
    method: str = "standard"
    network: str = "unknown"
    timestamp: int = 0

@dataclass
class GasOptimization:
    """Represents gas optimization suggestions."""
    current_gas: int
    optimized_gas: int
    savings: int
    savings_percentage: float
    suggestions: List[str]
    priority: str = "medium"

class GasEstimator:
    """Gas estimation service for smart contracts."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize gas estimator with configuration."""
        self.config = config
        self.networks = config.get("networks", {})
        self.web3_instances = {}
        self.gas_price_cache = {}
        self.cache_duration = 300  # 5 minutes
        
        # Initialize Web3 instances for each network
        self._initialize_web3_instances()
    
    def _initialize_web3_instances(self):
        """Initialize Web3 instances for each supported network."""
        for network, network_config in self.networks.items():
            if network_config.get("enabled", False):
                rpc_url = os.getenv(f"{network.upper()}_RPC_URL")
                if rpc_url:
                    try:
                        self.web3_instances[network] = Web3(Web3.HTTPProvider(rpc_url))
                        logger.info(f"Initialized Web3 instance for {network}")
                    except Exception as e:
                        logger.error(f"Failed to initialize Web3 for {network}: {e}")
    
    async def estimate_deployment_gas(
        self,
        contract_bytecode: str,
        constructor_args: List[Any] = None,
        network: str = "hyperion",
        gas_price_multiplier: float = 1.2
    ) -> GasEstimate:
        """
        Estimate gas for contract deployment.
        
        Args:
            contract_bytecode: Compiled contract bytecode
            constructor_args: Constructor arguments
            network: Target network
            gas_price_multiplier: Multiplier for gas price safety margin
            
        Returns:
            GasEstimate object with gas information
        """
        try:
            if network not in self.web3_instances:
                raise ValueError(f"Network {network} not supported")
            
            web3 = self.web3_instances[network]
            
            # Get current gas price
            gas_price = await self._get_gas_price(network)
            
            # Estimate gas limit for deployment
            gas_limit = await self._estimate_deployment_gas_limit(
                web3, contract_bytecode, constructor_args
            )
            
            # Apply safety margin
            gas_limit = int(gas_limit * gas_price_multiplier)
            
            # Calculate costs
            total_cost_wei = gas_limit * gas_price
            total_cost_eth = web3.from_wei(total_cost_wei, 'ether')
            
            # Get EIP-1559 gas parameters if supported
            max_fee_per_gas, max_priority_fee_per_gas = await self._get_eip1559_gas_params(network)
            
            return GasEstimate(
                gas_limit=gas_limit,
                gas_price=gas_price,
                max_fee_per_gas=max_fee_per_gas,
                max_priority_fee_per_gas=max_priority_fee_per_gas,
                total_cost_wei=total_cost_wei,
                total_cost_eth=float(total_cost_eth),
                confidence="high",
                method="deployment_estimation",
                network=network,
                timestamp=int(asyncio.get_event_loop().time())
            )
            
        except Exception as e:
            logger.error(f"Failed to estimate deployment gas: {e}")
            # Return fallback estimate
            return GasEstimate(
                gas_limit=2000000,  # Conservative fallback
                gas_price=20000000000,  # 20 gwei
                total_cost_wei=40000000000000000,  # 0.04 ETH
                total_cost_eth=0.04,
                confidence="low",
                method="fallback",
                network=network,
                timestamp=int(asyncio.get_event_loop().time())
            )
    
    async def estimate_function_call_gas(
        self,
        contract_address: str,
        function_abi: Dict[str, Any],
        function_name: str,
        function_args: List[Any] = None,
        network: str = "hyperion",
        gas_price_multiplier: float = 1.1
    ) -> GasEstimate:
        """
        Estimate gas for function call.
        
        Args:
            contract_address: Contract address
            function_abi: Function ABI
            function_name: Function name
            function_args: Function arguments
            network: Target network
            gas_price_multiplier: Multiplier for gas price safety margin
            
        Returns:
            GasEstimate object with gas information
        """
        try:
            if network not in self.web3_instances:
                raise ValueError(f"Network {network} not supported")
            
            web3 = self.web3_instances[network]
            
            # Get current gas price
            gas_price = await self._get_gas_price(network)
            
            # Create contract instance
            contract = web3.eth.contract(
                address=contract_address,
                abi=[function_abi]
            )
            
            # Estimate gas limit for function call
            function = getattr(contract.functions, function_name)
            if function_args:
                gas_limit = function(*function_args).estimate_gas()
            else:
                gas_limit = function().estimate_gas()
            
            # Apply safety margin
            gas_limit = int(gas_limit * gas_price_multiplier)
            
            # Calculate costs
            total_cost_wei = gas_limit * gas_price
            total_cost_eth = web3.from_wei(total_cost_wei, 'ether')
            
            # Get EIP-1559 gas parameters if supported
            max_fee_per_gas, max_priority_fee_per_gas = await self._get_eip1559_gas_params(network)
            
            return GasEstimate(
                gas_limit=gas_limit,
                gas_price=gas_price,
                max_fee_per_gas=max_fee_per_gas,
                max_priority_fee_per_gas=max_priority_fee_per_gas,
                total_cost_wei=total_cost_wei,
                total_cost_eth=float(total_cost_eth),
                confidence="high",
                method="function_call_estimation",
                network=network,
                timestamp=int(asyncio.get_event_loop().time())
            )
            
        except Exception as e:
            logger.error(f"Failed to estimate function call gas: {e}")
            # Return fallback estimate
            return GasEstimate(
                gas_limit=100000,  # Conservative fallback
                gas_price=20000000000,  # 20 gwei
                total_cost_wei=2000000000000000,  # 0.002 ETH
                total_cost_eth=0.002,
                confidence="low",
                method="fallback",
                network=network,
                timestamp=int(asyncio.get_event_loop().time())
            )
    
    async def _get_gas_price(self, network: str) -> int:
        """Get current gas price for network."""
        cache_key = f"{network}_gas_price"
        current_time = int(asyncio.get_event_loop().time())
        
        # Check cache
        if cache_key in self.gas_price_cache:
            cached_data = self.gas_price_cache[cache_key]
            if current_time - cached_data["timestamp"] < self.cache_duration:
                return cached_data["gas_price"]
        
        try:
            web3 = self.web3_instances[network]
            gas_price = web3.eth.gas_price
            
            # Cache the result
            self.gas_price_cache[cache_key] = {
                "gas_price": gas_price,
                "timestamp": current_time
            }
            
            return gas_price
            
        except Exception as e:
            logger.error(f"Failed to get gas price for {network}: {e}")
            # Return fallback gas price
            return 20000000000  # 20 gwei
    
    async def _get_eip1559_gas_params(self, network: str) -> Tuple[Optional[int], Optional[int]]:
        """Get EIP-1559 gas parameters if supported."""
        try:
            web3 = self.web3_instances[network]
            
            # Check if network supports EIP-1559
            latest_block = web3.eth.get_block('latest')
            if 'baseFeePerGas' in latest_block:
                # Calculate max fee per gas (base fee + priority fee)
                base_fee = latest_block['baseFeePerGas']
                priority_fee = await self._get_priority_fee(network)
                max_fee = base_fee * 2 + priority_fee
                
                return max_fee, priority_fee
            
        except Exception as e:
            logger.debug(f"EIP-1559 not supported for {network}: {e}")
        
        return None, None
    
    async def _get_priority_fee(self, network: str) -> int:
        """Get priority fee for EIP-1559 transactions."""
        try:
            # Use a simple priority fee calculation
            # In production, you might want to use a more sophisticated method
            gas_price = await self._get_gas_price(network)
            return gas_price // 10  # 10% of gas price as priority fee
        except Exception:
            return 2000000000  # 2 gwei fallback
    
    async def _estimate_deployment_gas_limit(
        self,
        web3: Web3,
        bytecode: str,
        constructor_args: List[Any] = None
    ) -> int:
        """Estimate gas limit for contract deployment."""
        try:
            # Create a test transaction for gas estimation
            if constructor_args:
                # Encode constructor arguments
                constructor_data = web3.eth.contract(bytecode=bytecode).constructor(*constructor_args).data_in_transaction
            else:
                constructor_data = bytecode
            
            # Estimate gas using eth_estimateGas
            gas_estimate = web3.eth.estimate_gas({
                'data': constructor_data
            })
            
            return gas_estimate
            
        except Exception as e:
            logger.error(f"Failed to estimate deployment gas limit: {e}")
            # Return conservative fallback
            return 2000000
    
    async def analyze_gas_optimization(
        self,
        contract_source: str,
        current_gas_usage: int
    ) -> GasOptimization:
        """
        Analyze contract for gas optimization opportunities.
        
        Args:
            contract_source: Solidity source code
            current_gas_usage: Current gas usage
            
        Returns:
            GasOptimization object with suggestions
        """
        suggestions = []
        estimated_savings = 0
        
        # Analyze common gas optimization patterns
        if "memory" in contract_source.lower():
            suggestions.append("Consider using storage instead of memory for frequently accessed data")
            estimated_savings += 1000
        
        if "for (" in contract_source and "i++" in contract_source:
            suggestions.append("Use ++i instead of i++ in loops")
            estimated_savings += 100
        
        if "require(" in contract_source and "msg.sender" in contract_source:
            suggestions.append("Consider using custom errors instead of require statements")
            estimated_savings += 200
        
        if "mapping(" in contract_source and "struct" in contract_source:
            suggestions.append("Optimize struct packing to reduce storage slots")
            estimated_savings += 500
        
        if "external" not in contract_source:
            suggestions.append("Use external functions for better gas efficiency")
            estimated_savings += 50
        
        # Calculate optimization metrics
        optimized_gas = max(current_gas_usage - estimated_savings, current_gas_usage * 0.8)
        savings = current_gas_usage - optimized_gas
        savings_percentage = (savings / current_gas_usage) * 100 if current_gas_usage > 0 else 0
        
        return GasOptimization(
            current_gas=current_gas_usage,
            optimized_gas=int(optimized_gas),
            savings=int(savings),
            savings_percentage=savings_percentage,
            suggestions=suggestions,
            priority="high" if savings_percentage > 20 else "medium"
        )
    
    async def get_network_gas_info(self, network: str) -> Dict[str, Any]:
        """Get comprehensive gas information for a network."""
        try:
            if network not in self.web3_instances:
                raise ValueError(f"Network {network} not supported")
            
            web3 = self.web3_instances[network]
            
            # Get current gas price
            gas_price = await self._get_gas_price(network)
            
            # Get latest block for additional info
            latest_block = web3.eth.get_block('latest')
            
            # Get EIP-1559 parameters if supported
            max_fee_per_gas, max_priority_fee_per_gas = await self._get_eip1559_gas_params(network)
            
            return {
                "network": network,
                "gas_price_wei": gas_price,
                "gas_price_gwei": gas_price / 1e9,
                "gas_price_eth": float(web3.from_wei(gas_price, 'ether')),
                "max_fee_per_gas": max_fee_per_gas,
                "max_priority_fee_per_gas": max_priority_fee_per_gas,
                "block_number": latest_block.number,
                "block_gas_limit": latest_block.gasLimit,
                "block_gas_used": latest_block.gasUsed,
                "base_fee_per_gas": latest_block.get('baseFeePerGas'),
                "supports_eip1559": 'baseFeePerGas' in latest_block,
                "timestamp": int(asyncio.get_event_loop().time())
            }
            
        except Exception as e:
            logger.error(f"Failed to get gas info for {network}: {e}")
            return {
                "network": network,
                "error": str(e),
                "timestamp": int(asyncio.get_event_loop().time())
            }
    
    async def estimate_batch_deployment_gas(
        self,
        contracts: List[Dict[str, Any]],
        network: str = "hyperion"
    ) -> List[GasEstimate]:
        """Estimate gas for multiple contract deployments."""
        estimates = []
        
        for contract in contracts:
            estimate = await self.estimate_deployment_gas(
                contract_bytecode=contract["bytecode"],
                constructor_args=contract.get("constructor_args"),
                network=network
            )
            estimates.append(estimate)
        
        return estimates
    
    def format_gas_estimate(self, estimate: GasEstimate) -> str:
        """Format gas estimate for display."""
        return f"""
Gas Estimate for {estimate.network}:
├── Gas Limit: {estimate.gas_limit:,} gas
├── Gas Price: {estimate.gas_price / 1e9:.2f} Gwei
├── Total Cost: {estimate.total_cost_eth:.6f} ETH
├── Confidence: {estimate.confidence}
└── Method: {estimate.method}
"""
    
    def format_optimization(self, optimization: GasOptimization) -> str:
        """Format gas optimization for display."""
        return f"""
Gas Optimization Analysis:
├── Current Gas: {optimization.current_gas:,} gas
├── Optimized Gas: {optimization.optimized_gas:,} gas
├── Savings: {optimization.savings:,} gas ({optimization.savings_percentage:.1f}%)
├── Priority: {optimization.priority}
└── Suggestions:
{chr(10).join(f"    • {suggestion}" for suggestion in optimization.suggestions)}
"""

# Example usage and testing
async def main():
    """Example usage of GasEstimator."""
    config = {
        "networks": {
            "hyperion": {"enabled": True},
            "metis": {"enabled": True},
            "lazai": {"enabled": True}
        }
    }
    
    estimator = GasEstimator(config)
    
    # Example contract bytecode (simplified)
    bytecode = "0x608060405234801561001057600080fd5b50600436106100365760003560e01c8063..."
    
    # Estimate deployment gas
    estimate = await estimator.estimate_deployment_gas(
        contract_bytecode=bytecode,
        network="hyperion"
    )
    
    print(estimator.format_gas_estimate(estimate))
    
    # Get network gas info
    gas_info = await estimator.get_network_gas_info("hyperion")
    print(f"Network Gas Info: {json.dumps(gas_info, indent=2)}")

if __name__ == "__main__":
    asyncio.run(main())
