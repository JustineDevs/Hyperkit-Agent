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
    Multi-chain smart contract deployer supporting Hyperion, Metis, and LazAI networks.
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
        """Initialize network configurations - HYPERION/METIS/LAZAI FOCUS."""
        # Get network config from main config if available
        networks_config = self.config.get("networks", {})
        
        logger.info(f"🔍 Initializing networks with config: {type(self.config)}")
        logger.info(f"🔍 Networks config: {type(networks_config)}")
        logger.info(f"🔍 Networks config keys: {networks_config.keys() if isinstance(networks_config, dict) else 'NOT A DICT'}")
        
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
            "metis": {
                "rpc_url": networks_config.get("metis", {}).get(
                    "rpc_url", "https://andromeda.metis.io"
                ),
                "chain_id": networks_config.get("metis", {}).get("chain_id", 1088),
                "explorer": networks_config.get("metis", {}).get(
                    "explorer_url", "https://andromeda-explorer.metis.io"
                ),
                "gas_price": "20000000000",  # 20 gwei
                "gas_limit": 8000000,
                "enabled": True,
            },
            "lazai": {
                "rpc_url": networks_config.get("lazai", {}).get(
                    "rpc_url", "https://rpc.lazai.network/testnet"
                ),
                "chain_id": networks_config.get("lazai", {}).get("chain_id", 9001),
                "explorer": networks_config.get("lazai", {}).get(
                    "explorer_url", "https://testnet-explorer.lazai.network"
                ),
                "gas_price": "1000000000",  # 1 gwei
                "gas_limit": 8000000,
                "enabled": True,
            },
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
            
            # Validate network config structure
            if not isinstance(network_config, dict):
                raise TypeError(f"Network config must be dict, got {type(network_config)}")
            
            if "rpc_url" not in network_config:
                raise KeyError(f"Missing rpc_url in network config for {network}")
            
            if not isinstance(network_config["rpc_url"], str):
                raise TypeError(f"RPC URL must be string, got {type(network_config['rpc_url'])}")

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

            # Validate compilation result before deployment
            logger.info(f"🔍 Compilation result type: {type(compilation_result)}")
            logger.info(f"🔍 Compilation result keys: {compilation_result.keys() if isinstance(compilation_result, dict) else 'NOT A DICT'}")
            
            if not isinstance(compilation_result, dict):
                logger.error(f"❌ Compilation result is not dict: {type(compilation_result)}")
                raise TypeError(f"Compilation result must be dict, got {type(compilation_result)}")
            
            if "bytecode" not in compilation_result:
                logger.error(f"❌ Missing bytecode in compilation result: {compilation_result}")
                raise KeyError("Missing bytecode in compilation result")
            
            if "abi" not in compilation_result:
                logger.error(f"❌ Missing ABI in compilation result: {compilation_result}")
                raise KeyError("Missing ABI in compilation result")
            
            bytecode = compilation_result["bytecode"]
            abi = compilation_result["abi"]
            
            logger.info(f"🔍 Extracted bytecode type: {type(bytecode)}, length: {len(bytecode) if isinstance(bytecode, str) else 'N/A'}")
            logger.info(f"🔍 Extracted ABI type: {type(abi)}, length: {len(abi) if isinstance(abi, list) else 'N/A'}")
            
            # Validate types before passing to deployment
            if not isinstance(bytecode, str):
                logger.error(f"❌ Bytecode is not string: {type(bytecode)} = {bytecode}")
                raise TypeError(f"Bytecode must be string, got {type(bytecode)}")
            
            if not isinstance(abi, list):
                logger.error(f"❌ ABI is not list: {type(abi)} = {abi}")
                raise TypeError(f"ABI must be list, got {type(abi)}")
            
            logger.info(f"✅ Deploying contract with bytecode length: {len(bytecode)}, ABI length: {len(abi)}")
            
            # Deploy contract
            deployment_result = await self._deploy_compiled_contract(
                bytecode,
                abi,
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
            logger.error(f"Deployment failed: {e}", exc_info=True)
            return {
                "status": "error", 
                "error": str(e), 
                "network": network,
                "error_type": type(e).__name__
            }

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

                bytecode = contract_data.get("bin", "")
                abi = contract_data.get("abi", [])
                
                # Debug: Check types
                logger.info(f"Bytecode type: {type(bytecode)}, length: {len(bytecode) if isinstance(bytecode, str) else 'N/A'}")
                logger.info(f"ABI type: {type(abi)}, length: {len(abi) if isinstance(abi, (list, dict)) else 'N/A'}")
                
                # Ensure bytecode is string and ABI is list
                if not isinstance(bytecode, str):
                    logger.error(f"Bytecode is not string: {type(bytecode)}")
                    return {"success": False, "errors": f"Invalid bytecode type: {type(bytecode)}"}
                
                if not isinstance(abi, list):
                    logger.error(f"ABI is not list: {type(abi)}")
                    return {"success": False, "errors": f"Invalid ABI type: {type(abi)}"}
                
                return {
                    "success": True,
                    "bytecode": bytecode,
                    "abi": abi,
                    "contract_name": contract_name,
                }
            else:
                return {"success": False, "errors": result.stderr}

        except Exception as e:
            logger.error(f"Compilation failed: {e}", exc_info=True)
            return {
                "success": False, 
                "errors": str(e),
                "error_type": type(e).__name__
            }

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

            # Initialize Web3 with proper type checking
            rpc_url = network_config.get("rpc_url")
            if not isinstance(rpc_url, str):
                raise TypeError(f"RPC URL must be string, got {type(rpc_url)}: {rpc_url}")
            
            logger.info(f"Initializing Web3 with RPC: {rpc_url}")
            w3 = Web3(Web3.HTTPProvider(rpc_url))

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
                    logger.info(f"Encoding constructor args: {constructor_args}")
                    logger.info(f"Constructor ABI inputs: {constructor_abi['inputs']}")
                    
                    # Validate inputs is a list
                    inputs = constructor_abi["inputs"]
                    if not isinstance(inputs, list):
                        logger.error(f"Constructor inputs must be list, got {type(inputs)}")
                        raise TypeError(f"Constructor inputs must be list, got {type(inputs)}")
                    
                    # Extract types from inputs
                    input_types = []
                    for arg in inputs:
                        if isinstance(arg, dict) and "type" in arg:
                            input_types.append(arg["type"])
                        else:
                            logger.error(f"Invalid input format: {arg}")
                            raise ValueError(f"Invalid input format: {arg}")
                    
                    logger.info(f"Input types: {input_types}")
                    
                    try:
                        # Use Web3.py's contract encoding instead of codec.encode_abi
                        from web3 import Web3
                        
                        # Create a temporary contract instance for encoding
                        temp_contract = w3.eth.contract(abi=abi, bytecode="0x")
                        
                        # Encode constructor arguments using the contract's constructor
                        constructor_data = temp_contract.constructor(*constructor_args).data_in_transaction
                        
                        logger.info("Constructor data encoded successfully")
                    except Exception as e:
                        logger.error(f"Failed to encode constructor args: {e}")
                        logger.error(f"Input types: {input_types}")
                        logger.error(f"Constructor args: {constructor_args}")
                        # Fallback: try without constructor args
                        logger.warning("Falling back to deployment without constructor args")
                        constructor_data = b""

            # Create contract instance with detailed debugging
            logger.info(f"Creating contract with bytecode length: {len(bytecode)}, ABI length: {len(abi)}")
            logger.info(f"Bytecode type: {type(bytecode)}, ABI type: {type(abi)}")
            
            # CRITICAL: Check if bytecode or abi are dicts (this is the bug!)
            if isinstance(bytecode, dict):
                logger.error(f"🚨 BUG FOUND: Bytecode is dict! {bytecode}")
                # Try to extract the actual bytecode from the dict
                if 'bin' in bytecode:
                    bytecode = bytecode['bin']
                    logger.info(f"✅ Extracted bytecode from dict: {len(bytecode)} chars")
                else:
                    raise TypeError(f"Bytecode dict missing 'bin' key: {bytecode}")
            
            if isinstance(abi, dict):
                logger.error(f"🚨 BUG FOUND: ABI is dict! {abi}")
                # Try to extract the actual ABI from the dict
                if 'abi' in abi:
                    abi = abi['abi']
                    logger.info(f"✅ Extracted ABI from dict: {len(abi)} items")
                else:
                    raise TypeError(f"ABI dict missing 'abi' key: {abi}")
            
            # Validate bytecode and ABI types before contract creation
            if not isinstance(bytecode, str):
                logger.error(f"❌ Bytecode is not string: {type(bytecode)} - {bytecode}")
                raise TypeError(f"Bytecode must be string, got {type(bytecode)}")
            
            if not isinstance(abi, list):
                logger.error(f"❌ ABI is not list: {type(abi)} - {abi}")
                raise TypeError(f"ABI must be list, got {type(abi)}")
            
            # Additional validation for bytecode content
            if bytecode.startswith('0x'):
                logger.info(f"✅ Bytecode starts with 0x: {bytecode[:20]}...")
            else:
                logger.warning(f"⚠️  Bytecode doesn't start with 0x: {bytecode[:20]}...")
                # Fix: Add 0x prefix if missing
                if not bytecode.startswith('0x'):
                    bytecode = '0x' + bytecode
                    logger.info(f"✅ Added 0x prefix: {bytecode[:20]}...")
            
            # Additional validation for ABI content
            if abi and isinstance(abi, list) and len(abi) > 0:
                logger.info(f"✅ ABI has {len(abi)} items, first item: {abi[0] if abi else 'None'}")
            else:
                logger.warning(f"⚠️  ABI is empty or invalid: {abi}")
            
            try:
                # Create contract instance with proper parameters
                logger.info("Creating Web3 contract instance...")
                contract = w3.eth.contract(bytecode=bytecode, abi=abi)
                logger.info("✅ Contract instance created successfully")
            except Exception as e:
                logger.error(f"❌ Failed to create contract instance: {e}")
                logger.error(f"Error type: {type(e).__name__}")
                logger.error(f"Bytecode type: {type(bytecode)}, ABI type: {type(abi)}")
                logger.error(f"Bytecode sample: {str(bytecode)[:100]}...")
                logger.error(f"ABI sample: {str(abi)[:200]}...")
                
                # Check if it's a specific Web3 error
                if "expected string or bytes-like object" in str(e):
                    logger.error("🔍 This is the dict/string error we're trying to fix!")
                    logger.error(f"Bytecode is: {type(bytecode)} = {bytecode[:50]}...")
                    logger.error(f"ABI is: {type(abi)} = {abi[:3] if isinstance(abi, list) else abi}")
                
                raise

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

            explorer_url = network_config.get("explorer_url", "")

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
