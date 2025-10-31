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
            # Look for existing artifacts in the foundry project (hyperkit-agent/)
            # Path from services/deployment/foundry_deployer.py: .. -> services, .. -> hyperkit-agent (foundry project root)
            foundry_project_dir = Path(__file__).parent.parent.parent
            out_dir = foundry_project_dir / "out"
            
            if not out_dir.exists():
                return {
                    "success": False,
                    "error": "No compiled artifacts found. Run 'forge build' first.",
                    "suggestions": ["Run 'forge build' in project root", "Check if contracts directory exists"]
                }
            
            # Find the specific contract artifact (robust path handling)
            artifact_file = None
            potential_paths = [
                out_dir / f"{contract_name}.sol" / f"{contract_name}.json",
                out_dir / f"{contract_name}.json",
                out_dir / "GamingToken.sol" / "GameToken.json",  # Fallback for legacy
            ]
            
            # Try to resolve paths and check existence
            for path in potential_paths:
                try:
                    resolved_path = path.resolve()
                    if resolved_path.exists() and resolved_path.is_file():
                        artifact_file = resolved_path
                        logger.debug(f"Found artifact at: {artifact_file}")
                        break
                except (OSError, RuntimeError) as e:
                    logger.debug(f"Path resolution failed for {path}: {e}")
                    continue
            
            # If not found, look for any JSON files in the out directory
            if not artifact_file:
                try:
                    for json_file in out_dir.rglob("*.json"):
                        try:
                            resolved_json = json_file.resolve()
                            if not resolved_json.is_file():
                                continue
                            
                            with open(resolved_json, 'r', encoding='utf-8') as f:
                                artifact_data = json.load(f)
                                if "bytecode" in artifact_data and "abi" in artifact_data:
                                    # Check if this has the right constructor signature
                                    for item in artifact_data['abi']:
                                        if item.get('type') == 'constructor':
                                            if len(item.get('inputs', [])) == 5:  # GamingToken has 5 inputs
                                                artifact_file = resolved_json
                                                logger.info(f"✅ Found artifact with 5 constructor inputs: {artifact_file}")
                                                break
                                            break
                                    if artifact_file:
                                        break
                        except (json.JSONDecodeError, OSError, IOError) as e:
                            logger.debug(f"Skipping invalid artifact file {json_file}: {e}")
                            continue
                except (OSError, PermissionError) as e:
                    logger.warning(f"Failed to search for artifacts in {out_dir}: {e}")
            
            if not artifact_file or not artifact_file.exists():
                # List available artifacts for debugging
                available_artifacts = []
                try:
                    for json_file in out_dir.rglob("*.json"):
                        available_artifacts.append(str(json_file.relative_to(out_dir)))
                except:
                    pass
                
                return {
                    "success": False,
                    "error": f"Artifact not found in {out_dir.resolve()}",
                    "available_artifacts": available_artifacts[:10] if available_artifacts else [],
                    "suggestions": [
                        "Run 'forge build' in project root",
                        f"Check contract name matches: {contract_name}",
                        f"Check artifacts directory exists: {out_dir}",
                        "Verify contract was compiled successfully"
                    ]
                }
            
            # Read artifact with proper error handling
            try:
                with open(artifact_file, 'r', encoding='utf-8') as f:
                    artifact = json.load(f)
            except (json.JSONDecodeError, OSError, IOError) as e:
                return {
                    "success": False,
                    "error": f"Failed to read artifact file {artifact_file}: {e}",
                    "suggestions": [
                        "Artifact file may be corrupted",
                        "Check file permissions",
                        "Re-run 'forge build' to regenerate artifacts"
                    ]
                }
            
            bytecode = artifact["bytecode"]["object"]
            abi = artifact["abi"]
            
            logger.info(f"✅ Artifacts loaded from: {artifact_file}")
            
            # Create versioned artifact copy for rollback support
            version_id = None
            try:
                from services.deployment.artifact_versioning import ArtifactVersionManager
                # Use foundry project directory for artifact versioning
                # Path from services/deployment/foundry_deployer.py: .. -> services, .. -> hyperkit-agent
                foundry_project_dir = Path(__file__).parent.parent.parent
                version_manager = ArtifactVersionManager(foundry_project_dir)
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
                try:
                    tx = contract_factory.constructor(*constructor_args).build_transaction({
                        'from': account.address,
                        'nonce': w3.eth.get_transaction_count(account.address),
                        'gas': 3000000,
                        'gasPrice': w3.eth.gas_price,
                        'chainId': chain_id
                    })
                except Exception as e:
                    # Constructor args mismatch - provide detailed error
                    constructor_abi = None
                    for item in abi:
                        if item.get('type') == 'constructor':
                            constructor_abi = item
                            break
                    
                    expected_params = []
                    if constructor_abi and constructor_abi.get('inputs'):
                        expected_params = [f"{inp.get('type')} {inp.get('name', '')}" for inp in constructor_abi.get('inputs', [])]
                    
                    error_msg = (
                        f"Constructor arguments mismatch: {str(e)}\n"
                        f"Expected parameters: {expected_params}\n"
                        f"Provided arguments: {constructor_args}\n"
                        f"Provide correct constructor args or use --constructor-args flag"
                    )
                    logger.error(error_msg)
                    raise ValueError(error_msg) from e
            else:
                # FIXED: Use source code parsing as primary, validate against ABI
                from services.deployment.constructor_parser import ConstructorArgumentParser
                parser = ConstructorArgumentParser()
                
                # Extract from source code (more reliable than ABI)
                source_params = parser.extract_constructor_params(contract_source_code)
                if source_params and source_params[1]:
                    logger.info(f"Extracting constructor args from source code: {len(source_params[1])} params")
                    # Generate args from source code parsing (more accurate)
                    source_args = parser.generate_constructor_args(
                        contract_source_code,
                        account.address
                    )
                    logger.info(f"Generated from source code: {source_args}")
                else:
                    source_args = []
                
                # Validate against ABI as secondary check
                constructor_abi = None
                for item in abi:
                    if item.get('type') == 'constructor':
                        constructor_abi = item
                        break
                
                abi_param_count = len(constructor_abi.get('inputs', [])) if constructor_abi else 0
                source_param_count = len(source_params[1]) if source_params and source_params[1] else 0
                
                if abi_param_count != source_param_count:
                    logger.warning(
                        f"Param count mismatch: ABI={abi_param_count}, Source={source_param_count}. "
                        f"Using source code params (more reliable)."
                    )
                
                # Validate generated args against both source and ABI before using
                if source_args:
                    # Validate against source code signature
                    validation = parser.validate_constructor_args(contract_source_code, source_args)
                    if not validation.get('success'):
                        logger.error(f"Constructor args validation failed: {validation.get('error')}")
                        logger.error(f"Expected signature: {validation.get('signature', [])}")
                        raise ValueError(
                            f"Generated constructor args don't match contract signature: {validation.get('error')}"
                        )
                    
                    final_args = source_args
                    logger.info(f"✅ Using validated source-code-extracted constructor args: {final_args}")
                elif constructor_abi and constructor_abi.get('inputs'):
                    # Fallback to ABI-based generation
                    logger.warning("Falling back to ABI-based arg generation (less reliable)")
                    abi_args = []
                    for input_param in constructor_abi.get('inputs', []):
                        param_type = input_param.get('type', '')
                        param_name = input_param.get('name', '')
                        
                        logger.info(f"Generating arg for {param_name}: {param_type}")
                        
                        # Handle tuple types (structs)
                        if param_type.startswith('tuple'):
                            struct_values = []
                            for component in input_param.get('components', []):
                                comp_type = component.get('type', '')
                                comp_name = component.get('name', '')
                                struct_values.append(self._generate_arg_for_type(comp_type, comp_name, account.address))
                            abi_args.append(tuple(struct_values))
                        # Handle arrays
                        elif param_type.endswith('[]'):
                            abi_args.append([])
                        elif '[' in param_type and ']' in param_type:
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
                                abi_args.append(1000000)
                            elif 'maxSupply' in param_name.lower():
                                abi_args.append(10000000)
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
                    
                    final_args = abi_args
                    logger.info(f"Using ABI-based constructor args: {final_args}")
                    
                    # Validate ABI-based args against source code if available
                    if contract_source_code:
                        validation = parser.validate_constructor_args(contract_source_code, final_args)
                        if not validation.get('success'):
                            logger.warning(f"ABI-based args validation failed: {validation.get('error')}")
                            logger.warning("Proceeding with ABI-based args anyway (may fail at deployment)")
                else:
                    # No constructor or no inputs - deploy without arguments
                    logger.info("No constructor inputs found, deploying without arguments")
                    final_args = []
                
                # Build transaction with validated args
                try:
                    if final_args:
                        # Final validation: try building transaction to catch type mismatches early
                        try:
                            # Test build transaction first to catch any ABI mismatches
                            test_tx = contract_factory.constructor(*final_args).build_transaction({
                                'from': account.address,
                                'nonce': w3.eth.get_transaction_count(account.address),
                                'gas': 3000000,
                                'gasPrice': w3.eth.gas_price,
                                'chainId': chain_id
                            })
                            tx = test_tx
                        except Exception as build_error:
                            # If build fails, provide detailed error message
                            constructor_abi = None
                            for item in abi:
                                if item.get('type') == 'constructor':
                                    constructor_abi = item
                                    break
                            
                            expected_params = []
                            if constructor_abi and constructor_abi.get('inputs'):
                                expected_params = [f"{inp.get('type')} {inp.get('name', '')}" for inp in constructor_abi.get('inputs', [])]
                            
                            error_msg = (
                                f"Constructor arguments type mismatch during transaction build: {str(build_error)}\n"
                                f"Expected parameters (from ABI): {expected_params}\n"
                                f"Provided arguments: {final_args}\n"
                                f"Argument types: {[type(a).__name__ for a in final_args]}\n"
                                f"Tip: Check that argument types match ABI exactly (address strings must be checksummed, ints must match size)"
                            )
                            logger.error(error_msg)
                            raise ValueError(error_msg) from build_error
                        
                        # Use the validated transaction
                        tx = test_tx
                    else:
                        tx = contract_factory.constructor().build_transaction({
                            'from': account.address,
                            'nonce': w3.eth.get_transaction_count(account.address),
                            'gas': 3000000,
                            'gasPrice': w3.eth.gas_price,
                            'chainId': chain_id
                        })
                except Exception as e:
                    # Constructor args mismatch - provide detailed error
                    expected_params = []
                    if constructor_abi and constructor_abi.get('inputs'):
                        expected_params = [f"{inp.get('type')} {inp.get('name', '')}" for inp in constructor_abi.get('inputs', [])]
                    
                    error_msg = (
                        f"Constructor arguments mismatch: {str(e)}\n"
                        f"Expected parameters: {expected_params}\n"
                        f"Generated arguments: {final_args}\n"
                        f"Contract: {contract_name}\n"
                        f"Fix: Provide correct constructor args via --constructor-args flag"
                    )
                    logger.error(f"❌ {error_msg}")
                    raise ValueError(error_msg) from e
            
            # Sign and send transaction
            signed_tx = account.sign_transaction(tx)
            # Use raw_transaction (snake_case) for Web3.py v6+, fallback to rawTransaction for v5
            raw_tx = getattr(signed_tx, 'raw_transaction', None) or getattr(signed_tx, 'rawTransaction', None)
            if not raw_tx:
                raise ValueError("Could not find raw transaction in signed transaction object")
            tx_hash = w3.eth.send_raw_transaction(raw_tx)
            
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
                        # Use foundry project directory for artifact versioning
                        # Path from services/deployment/foundry_deployer.py: .. -> services, .. -> hyperkit-agent
                        foundry_project_dir = Path(__file__).parent.parent.parent
                        version_manager = ArtifactVersionManager(foundry_project_dir)
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