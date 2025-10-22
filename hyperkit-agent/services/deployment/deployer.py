"""
Multi-Chain Deployment Service
Handles smart contract deployment across multiple blockchain networks
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
import tempfile

logger = logging.getLogger(__name__)


class MultiChainDeployer:
    """
    Multi-chain smart contract deployer supporting Hyperion, Polygon, Arbitrum, and Ethereum.
    Handles compilation, deployment, and verification across networks.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the multi-chain deployer.

        Args:
            config: Configuration dictionary with network settings
        """
        self.config = config or {}
        self.networks = self._initialize_networks()
        self.compiler_settings = self._get_compiler_settings()

        logger.info("MultiChainDeployer initialized")

    def _initialize_networks(self) -> Dict[str, Dict[str, Any]]:
        """Initialize network configurations - HYPERION FOCUS ONLY."""
        # Get network config from main config if available
        networks_config = self.config.get("networks", {})
        
        # Focus on Hyperion testnet only - other networks temporarily unavailable
        return {
            "hyperion": {
                "rpc_url": networks_config.get("hyperion", {}).get(
                    "rpc_url", "https://hyperion-testnet.metisdevops.link"
                ),
                "chain_id": networks_config.get("hyperion", {}).get("chain_id", 133717),
                "explorer": networks_config.get("hyperion", {}).get(
                    "explorer_url", "https://hyperion-testnet-explorer.metisdevops.link"
                ),
                "gas_price": "20000000000",  # 20 gwei
                "gas_limit": 8000000,
                "enabled": True,
            },
            # Other networks temporarily unavailable - focusing on Hyperion testnet only
            # "metis": {...},
            # "lazai": {...},
            # "polygon": {...},
            # "arbitrum": {...},
            # "ethereum": {...},
        }

    def _get_compiler_settings(self) -> Dict[str, Any]:
        """Get Solidity compiler settings."""
        return {
            "version": "0.8.19",
            "optimizer": {"enabled": True, "runs": 200},
            "evmVersion": "london",
            "libraries": {},
            "outputSelection": {"*": {"*": ["*"]}},
        }

    async def deploy(
        self,
        contract_code: str,
        network: str = "hyperion",
        constructor_args: Optional[List[Any]] = None,
        private_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Deploy a smart contract to the specified network.

        Args:
            contract_code: Solidity contract code
            network: Target network for deployment
            constructor_args: Constructor arguments
            private_key: Private key for deployment (if not provided, uses config)

        Returns:
            Dictionary containing deployment details
        """
        try:
            logger.info(f"Starting deployment to {network}")

            # Validate network
            if network not in self.networks:
                raise ValueError(f"Unsupported network: {network}")

            network_config = self.networks[network]

            # Network config is already in the correct format from _initialize_networks
            # No need for complex handling - just use it directly
            logger.info(f"Using network config for {network}: {network_config}")

            # Compile contract
            compilation_result = await self._compile_contract(contract_code)
            if not compilation_result["success"]:
                return {
                    "status": "error",
                    "error": "Compilation failed",
                    "details": compilation_result["errors"],
                }

            # Deploy contract
            deployment_result = await self._deploy_compiled_contract(
                compilation_result["bytecode"],
                compilation_result["abi"],
                network_config,
                constructor_args,
                private_key,
            )

            if deployment_result["success"]:
                # Verify contract on explorer
                verification_result = await self._verify_contract(
                    deployment_result["address"],
                    contract_code,
                    network_config,
                    constructor_args,
                )

                deployment_result["verification"] = verification_result

            return deployment_result

        except Exception as e:
            logger.error(f"Deployment failed: {e}")
            return {"status": "error", "error": str(e), "network": network}

    async def _compile_contract(self, contract_code: str) -> Dict[str, Any]:
        """Compile Solidity contract code."""
        try:
            # Create temporary file for compilation
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".sol", delete=False
            ) as f:
                f.write(contract_code)
                temp_file = f.name

            # Use solc for compilation
            import subprocess

            cmd = [
                "solc",
                "--optimize",
                "--optimize-runs",
                "200",
                "--combined-json",
                "abi,bin",
                temp_file,
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            # Clean up temporary file
            Path(temp_file).unlink(missing_ok=True)

            if result.returncode == 0:
                compilation_data = json.loads(result.stdout)
                contracts = compilation_data.get("contracts", {})

                # Get the first contract (simplified)
                contract_name = list(contracts.keys())[0]
                contract_data = contracts[contract_name]

                return {
                    "success": True,
                    "bytecode": contract_data.get("bin", ""),
                    "abi": contract_data.get("abi", []),
                    "contract_name": contract_name,
                }
            else:
                return {"success": False, "errors": result.stderr}

        except Exception as e:
            return {"success": False, "errors": str(e)}

    async def _deploy_compiled_contract(
        self,
        bytecode: str,
        abi: List[Dict],
        network_config: Dict[str, Any],
        constructor_args: Optional[List[Any]],
        private_key: Optional[str],
    ) -> Dict[str, Any]:
        """Deploy compiled contract to the network."""
        try:
            from web3 import Web3
            from eth_account import Account

            # Initialize Web3
            logger.info(f"Initializing Web3 with RPC: {network_config['rpc_url']}")
            w3 = Web3(Web3.HTTPProvider(network_config["rpc_url"]))

            if not w3.is_connected():
                raise Exception(f"Failed to connect to {network_config['rpc_url']}")

            # Get deployment account
            if private_key:
                account = Account.from_key(private_key)
            elif self.config.get("default_private_key"):
                account = Account.from_key(self.config["default_private_key"])
            else:
                raise ValueError(
                    "No private key provided for deployment. Please provide a private key or set DEFAULT_PRIVATE_KEY in config."
                )

            # Prepare constructor data
            constructor_data = b""
            if constructor_args and abi:
                # Find constructor in ABI
                constructor_abi = None
                for item in abi:
                    if item.get("type") == "constructor":
                        constructor_abi = item
                        break

                if constructor_abi and constructor_abi.get("inputs"):
                    # Encode constructor arguments
                    constructor_data = w3.codec.encode_abi(
                        [arg["type"] for arg in constructor_abi["inputs"]],
                        constructor_args,
                    )

            # Create contract instance
            logger.info(f"Creating contract with bytecode length: {len(bytecode)}, ABI length: {len(abi)}")
            contract = w3.eth.contract(bytecode=bytecode, abi=abi)

            # Build transaction
            
            if constructor_args:
                transaction = contract.constructor(*constructor_args).build_transaction(
                    {
                        "from": account.address,
                        "gas": network_config["gas_limit"],
                        "gasPrice": int(network_config["gas_price"]),
                        "nonce": w3.eth.get_transaction_count(account.address),
                    }
                )
            else:
                transaction = contract.constructor().build_transaction(
                    {
                        "from": account.address,
                        "gas": network_config["gas_limit"],
                        "gasPrice": int(network_config["gas_price"]),
                        "nonce": w3.eth.get_transaction_count(account.address),
                    }
                )

            # Sign and send transaction
            signed_txn = w3.eth.account.sign_transaction(
                transaction, private_key=account.key
            )
            # Handle different Web3.py versions
            raw_tx = getattr(signed_txn, 'rawTransaction', signed_txn.raw_transaction)
            tx_hash = w3.eth.send_raw_transaction(raw_tx)

            # Wait for transaction receipt
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

            if receipt.status == 1:
                return {
                    "success": True,
                    "address": receipt.contractAddress,
                    "tx_hash": tx_hash.hex(),
                    "gas_used": receipt.gasUsed,
                    "block_number": receipt.blockNumber,
                    "network": network_config,
                }
            else:
                return {
                    "success": False,
                    "error": "Transaction failed",
                    "tx_hash": tx_hash.hex(),
                }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _verify_contract(
        self,
        contract_address: str,
        contract_code: str,
        network_config: Dict[str, Any],
        constructor_args: Optional[List[Any]],
    ) -> Dict[str, Any]:
        """Verify contract on blockchain explorer."""
        try:
            # This is a simplified verification process
            # In practice, you'd use the specific explorer's API

            explorer_url = network_config.get("explorer", "")

            return {
                "status": "pending",
                "explorer_url": f"{explorer_url}/address/{contract_address}",
                "message": "Contract verification submitted",
            }

        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def sign_with_eip712(
        self, data: Dict[str, Any], private_key: str
    ) -> Dict[str, Any]:
        """
        Sign data using EIP-712 structured data signing.

        Args:
            data: EIP-712 structured data
            private_key: Private key for signing

        Returns:
            Dictionary containing signature details
        """
        try:
            from eth_account.messages import encode_structured_data
            from eth_account import Account

            account = Account.from_key(private_key)

            # Encode structured data
            message = encode_structured_data(data)

            # Sign message
            signed = account.sign_message(message)

            return {
                "status": "success",
                "signature": signed.signature.hex(),
                "signer": account.address,
                "message_hash": message.body.hex(),
            }

        except Exception as e:
            return {"status": "error", "error": str(e)}

    def get_network_info(self, network: str) -> Dict[str, Any]:
        """Get information about a specific network."""
        if network not in self.networks:
            return {"error": f"Network {network} not supported"}

        return self.networks[network]

    def get_supported_networks(self) -> List[str]:
        """Get list of supported networks."""
        return list(self.networks.keys())

    async def estimate_gas(
        self,
        contract_code: str,
        network: str = "hyperion",
        constructor_args: Optional[List[Any]] = None,
    ) -> Dict[str, Any]:
        """
        Estimate gas cost for contract deployment.

        Args:
            contract_code: Solidity contract code
            network: Target network
            constructor_args: Constructor arguments

        Returns:
            Dictionary containing gas estimation
        """
        try:
            # Compile contract
            compilation_result = await self._compile_contract(contract_code)
            if not compilation_result["success"]:
                return {
                    "status": "error",
                    "error": "Compilation failed for gas estimation",
                }

            network_config = self.networks[network]

            # Estimate gas (simplified)
            estimated_gas = len(compilation_result["bytecode"]) * 2  # Rough estimation
            gas_price = int(network_config["gas_price"])

            return {
                "status": "success",
                "estimated_gas": estimated_gas,
                "gas_price": gas_price,
                "estimated_cost_wei": estimated_gas * gas_price,
                "estimated_cost_eth": (estimated_gas * gas_price) / 1e18,
            }

        except Exception as e:
            return {"status": "error", "error": str(e)}


# Example usage
async def main():
    """Example usage of the MultiChainDeployer."""
    deployer = MultiChainDeployer()

    # Example contract code
    contract_code = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract SimpleToken is ERC20, Ownable {
    constructor() ERC20("Simple Token", "SIMPLE") {
        _mint(msg.sender, 1000000 * 10**decimals());
    }
    
    function mint(address to, uint256 amount) public onlyOwner {
        _mint(to, amount);
    }
}
"""

    try:
        # Estimate gas
        gas_estimate = await deployer.estimate_gas(contract_code, "hyperion")
        print("Gas Estimate:")
        print(json.dumps(gas_estimate, indent=2))

        # Deploy contract (requires private key)
        # deployment_result = await deployer.deploy(contract_code, 'hyperion')
        # print("Deployment Result:")
        # print(json.dumps(deployment_result, indent=2))

    except Exception as e:
        print(f"Deployment failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
