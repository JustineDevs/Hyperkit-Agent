import os
import json
import subprocess
import logging
import re
from pathlib import Path
from web3 import Web3
from eth_account import Account

# Configure logging
logger = logging.getLogger(__name__)

class FoundryDeployer:
    """Deploy contracts using Foundry"""
    
    def __init__(self):
        self.forge_bin = Path(__file__).parent.parent.parent / "foundry" / "forge.exe"
        if not self.forge_bin.exists():
            # Try system forge
            self.forge_bin = "forge"
    
    def _generate_arg_for_type(self, param_type: str, param_name: str, deployer_address: str):
        """Helper method to generate argument for a type."""
        if param_type == 'address':
            return deployer_address
        elif param_type == 'uint256':
            if 'initialSupply' in param_name.lower():
                return 1000000
            elif 'maxSupply' in param_name.lower():
                return 10000000
            else:
                return 1000000
        elif param_type == 'string':
            if 'name' in param_name.lower():
                return "GAMEX Token"
            elif 'symbol' in param_name.lower():
                return "GAMEX"
            else:
                return "Default"
        elif param_type == 'bool':
            return False
        elif param_type.startswith('uint') or param_type.startswith('int'):
            return 0
        elif param_type.startswith('bytes'):
            if param_type == 'bytes':
                return '0x'
            else:
                bytes_size = int(param_type[5:]) if len(param_type) > 5 else 32
                return '0x' + ('00' * bytes_size)
        else:
            return 0
    
    def get_network_config(self, network: str = None) -> dict:
        """
        Get network configuration - HYPERION ONLY.
        
        CRITICAL: Hyperion is the exclusive deployment target.
        Future network support (LazAI, Metis) documented in ROADMAP.md only.
        
        Args:
            network: Ignored - Hyperion is hardcoded (kept for API compatibility)
        
        Returns:
            Hyperion testnet configuration (only supported network)
        
        Raises:
            ValueError: If network is specified and not 'hyperion'
        """
        # Hardcode Hyperion - no multi-network logic
        hyperion_config = {
            "chain_id": 133717,
            "explorer_url": "https://hyperion-testnet-explorer.metisdevops.link",
            "rpc_url": "https://hyperion-testnet.metisdevops.link",
            "status": "testnet",
            "supported": True,
            "default": True,
            "name": "Hyperion Testnet"
        }
        
        # Fail hard if non-Hyperion network requested
        if network and network.lower() != "hyperion":
            raise ValueError(
                f"CRITICAL: Network '{network}' is not supported.\n"
                f"  HYPERION-ONLY MODE: Only 'hyperion' network is supported.\n"
                f"  Future network support documented in ROADMAP.md only.\n"
                f"  Fix: Remove --network flag or use --network hyperion (default)"
            )
        
        return hyperion_config
    
    def deploy(
        self, 
        contract_source_code: str, 
        rpc_url: str,
        chain_id: int,
        contract_name: str = "Contract",
        constructor_args: list = None
    ) -> dict:
        """Deploy a contract using Foundry (matches Deployer interface)"""
        try:
            logger.info(f"Deploying {contract_name} to chain {chain_id}")
            logger.info(f"RPC URL: {rpc_url}")
            
            # ✅ Connect to RPC
            w3 = Web3(Web3.HTTPProvider(rpc_url))
            if not w3.is_connected():
                return {
                    "success": False,
                    "error": f"Cannot connect to RPC: {rpc_url}",
                    "suggestions": ["Check RPC URL", "Verify network is online"]
                }
            
            logger.info("✅ Connected to RPC")
            
            # ✅ Get deployment account
            private_key = os.getenv("DEFAULT_PRIVATE_KEY") or os.getenv("PRIVATE_KEY")  # Support both
            if not private_key:
                return {
                    "success": False,
                    "error": "DEFAULT_PRIVATE_KEY not in .env",
                    "suggestions": ["Add DEFAULT_PRIVATE_KEY to .env file", "Or use PRIVATE_KEY for legacy support"]
                }
            
            account = Account.from_key(private_key)
            logger.info(f"✅ Using account: {account.address}")
            
            # ✅ Use existing compiled artifacts
            # Look for existing artifacts in the project
            project_root = Path(__file__).parent.parent.parent
            out_dir = project_root / "out"
            
            if not out_dir.exists():
                return {
                    "success": False,
                    "error": "No compiled artifacts found. Run 'forge build' first.",
                    "suggestions": ["Run 'forge build' in project root", "Check if contracts directory exists"]
                }
            
            # Find the specific contract artifact
            artifact_file = None
            potential_paths = [
                out_dir / f"{contract_name}.sol" / f"{contract_name}.json",
                out_dir / f"{contract_name}.json",
                out_dir / "GamingToken.sol" / "GameToken.json",  # Fallback for legacy
            ]
            
            for path in potential_paths:
                if path.exists():
                    artifact_file = path
                    break
            
            # If not found, look for any JSON files in the out directory
            if not artifact_file:
                for json_file in out_dir.rglob("*.json"):
                    try:
                        with open(json_file) as f:
                            artifact_data = json.load(f)
                            if "bytecode" in artifact_data and "abi" in artifact_data:
                                # Check if this has the right constructor signature
                                for item in artifact_data['abi']:
                                    if item.get('type') == 'constructor':
                                        if len(item.get('inputs', [])) == 5:  # GamingToken has 5 inputs
                                            artifact_file = json_file
                                            logger.info(f"✅ Found artifact with 5 constructor inputs: {artifact_file}")
                                            break
                                        break
                                if artifact_file:
                                    break
                    except:
                        continue
            
            if not artifact_file or not artifact_file.exists():
                return {
                    "success": False,
                    "error": f"Artifact not found in {out_dir}",
                    "suggestions": ["Run 'forge build' in project root", "Check contract name"]
                }
            
            with open(artifact_file) as f:
                artifact = json.load(f)
            
            bytecode = artifact["bytecode"]["object"]
            abi = artifact["abi"]
            
            logger.info(f"✅ Artifacts loaded from: {artifact_file}")
            
            # Create versioned artifact copy for rollback support
            version_id = None
            try:
                from services.deployment.artifact_versioning import ArtifactVersionManager
                project_root = Path(__file__).parent.parent.parent.parent
                version_manager = ArtifactVersionManager(project_root)
                version_id = version_manager.create_version(
                    contract_name,
                    artifact_file,
                    {
                        "chain_id": chain_id,
                        "rpc_url": rpc_url[:50] + "..." if len(rpc_url) > 50 else rpc_url,
                        "deployer_address": account.address
                    }
                )
                logger.info(f"✅ Artifact versioned: {version_id}")
            except Exception as e:
                logger.warning(f"Artifact versioning failed (non-critical): {e}")
            
            # Debug: Log constructor info
            constructor_abi = None
            for item in abi:
                if item.get('type') == 'constructor':
                    constructor_abi = item
                    break
            
            if constructor_abi:
                logger.info(f"Constructor inputs: {len(constructor_abi.get('inputs', []))}")
                for i, input_param in enumerate(constructor_abi.get('inputs', [])):
                    logger.info(f"  {i}: {input_param.get('type')} {input_param.get('name')}")
            else:
                logger.info("No constructor found in ABI")
            
            # ✅ Deploy contract
            logger.info("Deploying contract...")
            
            contract_factory = w3.eth.contract(abi=abi, bytecode=bytecode)
            
            # Use provided constructor arguments or extract from code
            if constructor_args:
                logger.info(f"Using provided constructor args: {constructor_args}")
                tx = contract_factory.constructor(*constructor_args).build_transaction({
                    'from': account.address,
                    'nonce': w3.eth.get_transaction_count(account.address),
                    'gas': 3000000,
                    'gasPrice': w3.eth.gas_price,
                    'chainId': chain_id
                })
            else:
                # Use ABI constructor info instead of source code parsing
                constructor_abi = None
                for item in abi:
                    if item.get('type') == 'constructor':
                        constructor_abi = item
                        break
                
                if constructor_abi and constructor_abi.get('inputs'):
                    # Generate arguments based on ABI constructor inputs
                    abi_args = []
                    for input_param in constructor_abi.get('inputs', []):
                        param_type = input_param.get('type', '')
                        param_name = input_param.get('name', '')
                        
                        logger.info(f"Generating arg for {param_name}: {param_type}")
                        
                        # Handle tuple types (structs)
                        if param_type.startswith('tuple'):
                            # Convert struct to tuple
                            struct_values = []
                            for component in input_param.get('components', []):
                                comp_type = component.get('type', '')
                                comp_name = component.get('name', '')
                                struct_values.append(self._generate_arg_for_type(comp_type, comp_name, account.address))
                            abi_args.append(tuple(struct_values))
                        # Handle arrays
                        elif param_type.endswith('[]'):
                            # Dynamic array - return empty array
                            abi_args.append([])
                        elif '[' in param_type and ']' in param_type:
                            # Fixed-size array - parse size and generate array
                            match = re.match(r'(\w+)\[(\d+)\]', param_type)
                            if match:
                                base_type = match.group(1)
                                size = int(match.group(2))
                                array_value = [self._generate_arg_for_type(base_type, f"{param_name}[{i}]", account.address) for i in range(size)]
                                abi_args.append(array_value)
                            else:
                                abi_args.append([])
                        # Handle basic types
                        elif param_type == 'address':
                            abi_args.append(account.address)
                        elif param_type == 'uint256':
                            if 'initialSupply' in param_name.lower():
                                abi_args.append(1000000)  # Initial supply
                            elif 'maxSupply' in param_name.lower():
                                abi_args.append(10000000)  # Max supply
                            else:
                                abi_args.append(1000000)
                        elif param_type == 'string':
                            if 'name' in param_name.lower():
                                abi_args.append("GAMEX Token")
                            elif 'symbol' in param_name.lower():
                                abi_args.append("GAMEX")
                            else:
                                abi_args.append("Default")
                        elif param_type == 'bool':
                            abi_args.append(False)
                        else:
                            abi_args.append(0)
                    
                    logger.info(f"Using ABI-based constructor args: {abi_args}")
                    tx = contract_factory.constructor(*abi_args).build_transaction({
                        'from': account.address,
                        'nonce': w3.eth.get_transaction_count(account.address),
                        'gas': 3000000,
                        'gasPrice': w3.eth.gas_price,
                        'chainId': chain_id
                    })
                else:
                    # No constructor or no inputs - deploy without arguments
                    logger.info("No constructor inputs found, deploying without arguments")
                    tx = contract_factory.constructor().build_transaction({
                        'from': account.address,
                        'nonce': w3.eth.get_transaction_count(account.address),
                        'gas': 3000000,
                        'gasPrice': w3.eth.gas_price,
                        'chainId': chain_id
                    })
            
            # Sign and send transaction
            signed_tx = account.sign_transaction(tx)
            tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            logger.info(f"✅ Transaction sent: {tx_hash.hex()}")
            
            # Wait for receipt
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
            
            if receipt.status == 1:
                contract_address = receipt.contractAddress
                logger.info(f"✅ Contract deployed at: {contract_address}")
                
                # Mark artifact version as deployed
                if version_id:
                    try:
                        from services.deployment.artifact_versioning import ArtifactVersionManager
                        project_root = Path(__file__).parent.parent.parent.parent
                        version_manager = ArtifactVersionManager(project_root)
                        version_manager.mark_deployed(version_id, {
                            "contract_address": contract_address,
                            "tx_hash": tx_hash.hex(),
                            "block_number": receipt.blockNumber,
                            "gas_used": receipt.gasUsed
                        })
                    except Exception as e:
                        logger.warning(f"Failed to mark version as deployed: {e}")
                
                return {
                    "success": True,
                    "contract_address": contract_address,
                    "tx_hash": tx_hash.hex(),
                    "gas_used": receipt.gasUsed,
                    "block_number": receipt.blockNumber,
                    "artifact_version": version_id
                }
            else:
                return {
                    "success": False,
                    "error": "Transaction failed",
                    "suggestions": ["Check gas limit", "Verify contract code"]
                }
                
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            logger.error(f"Deployment error: {str(e)}")
            logger.error(f"Error traceback:\n{error_trace}")
            
            # Extract useful error context
            error_type = type(e).__name__
            error_details = {
                "error_type": error_type,
                "error_message": str(e),
                "contract_name": contract_name,
                "rpc_url": rpc_url[:50] + "..." if len(rpc_url) > 50 else rpc_url,
                "chain_id": chain_id,
                "deployer_address": account.address if 'account' in locals() else "unknown"
            }
            
            return {
                "success": False,
                "error": f"{error_type}: {str(e)}",
                "error_details": error_details,
                "error_traceback": error_trace,
                "suggestions": [
                    f"Check contract code for {contract_name}",
                    f"Verify RPC connection to {rpc_url[:30]}...",
                    "Check account balance",
                    "Verify network chain ID matches configuration",
                    f"Check error type: {error_type}"
                ]
            }