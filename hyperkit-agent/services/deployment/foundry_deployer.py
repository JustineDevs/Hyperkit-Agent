import os
import json
import subprocess
from pathlib import Path
from web3 import Web3
from eth_account import Account
import logging

class FoundryDeployer:
    """Deploy contracts using Foundry"""
    
    def __init__(self):
        self.forge_bin = Path(__file__).parent.parent.parent / "foundry" / "forge.exe"
        if not self.forge_bin.exists():
            # Try system forge
            self.forge_bin = "forge"
    
    def get_network_config(self, network: str) -> dict:
        """Get network configuration"""
        networks = {
            "ethereum": {
                "chain_id": 1,
                "explorer_url": "https://etherscan.io",
                "rpc_url": "https://eth-mainnet.g.alchemy.com/v2/YOUR_KEY"
            },
            "polygon": {
                "chain_id": 137,
                "explorer_url": "https://polygonscan.com",
                "rpc_url": "https://polygon-rpc.com"
            },
            "arbitrum": {
                "chain_id": 42161,
                "explorer_url": "https://arbiscan.io",
                "rpc_url": "https://arb1.arbitrum.io/rpc"
            },
            "hyperion": {
                "chain_id": 1001,
                "explorer_url": "https://hyperion-testnet-explorer.metisdevops.link",
                "rpc_url": "https://hyperion-testnet.metisdevops.link"
            },
            "andromeda": {
                "chain_id": 1088,
                "explorer_url": "https://andromeda-explorer.metisdevops.link",
                "rpc_url": "https://andromeda.metis.io/?owner=1088"
            },
            "metis": {
                "chain_id": 1088,
                "explorer_url": "https://andromeda-explorer.metisdevops.link",
                "rpc_url": "https://andromeda.metis.io/?owner=1088"
            }
        }
        return networks.get(network)
    
    def deploy_contract(self, contract_source_code: str, network: str, constructor_args: list = None) -> dict:
        """Deploy a contract using Foundry"""
        try:
            logging.info(f"Deploying contract on {network}")
            
            # ✅ Get network configuration
            network_config = self.get_network_config(network)
            if not network_config:
                return {
                    "success": False,
                    "error": f"Network {network} not supported",
                    "suggestions": ["Check network configuration", "Use supported networks"]
                }
            
            rpc_url = network_config["rpc_url"]
            chain_id = network_config["chain_id"]
            
            # ✅ Connect to RPC
            w3 = Web3(Web3.HTTPProvider(rpc_url))
            if not w3.is_connected():
                return {
                    "success": False,
                    "error": f"Cannot connect to RPC: {rpc_url}",
                    "suggestions": ["Check RPC URL", "Verify network is online"]
                }
            
            logging.info("✅ Connected to RPC")
            
            # ✅ Get deployment account
            private_key = os.getenv("DEFAULT_PRIVATE_KEY") or os.getenv("PRIVATE_KEY")  # Support both
            if not private_key:
                return {
                    "success": False,
                    "error": "DEFAULT_PRIVATE_KEY not in .env",
                    "suggestions": ["Add DEFAULT_PRIVATE_KEY to .env file", "Or use PRIVATE_KEY for legacy support"]
                }
            
            account = Account.from_key(private_key)
            logging.info(f"✅ Using account: {account.address}")
            
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
                out_dir / "GamingToken.sol" / "GameToken.json",  # Our specific case
                out_dir / f"{contract_name}.sol" / f"{contract_name}.json",
                out_dir / f"{contract_name}.json"
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
                                            logging.info(f"✅ Found artifact with 5 constructor inputs: {artifact_file}")
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
            
            logging.info(f"✅ Artifacts loaded from: {artifact_file}")
            
            # Debug: Log constructor info
            constructor_abi = None
            for item in abi:
                if item.get('type') == 'constructor':
                    constructor_abi = item
                    break
            
            if constructor_abi:
                logging.info(f"Constructor inputs: {len(constructor_abi.get('inputs', []))}")
                for i, input_param in enumerate(constructor_abi.get('inputs', [])):
                    logging.info(f"  {i}: {input_param.get('type')} {input_param.get('name')}")
            else:
                logging.info("No constructor found in ABI")
            
            # ✅ Deploy contract
            logging.info("Deploying contract...")
            
            contract_factory = w3.eth.contract(abi=abi, bytecode=bytecode)
            
            # Extract contract name from the contract source
            import re
            contract_match = re.search(r'contract\s+([A-Z][a-zA-Z0-9_]*)', contract_source_code)
            contract_name = contract_match.group(1) if contract_match else "TestToken"
            
            # Use provided constructor arguments or extract from code
            if constructor_args:
                logging.info(f"Using provided constructor args: {constructor_args}")
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
                        
                        logging.info(f"Generating arg for {param_name}: {param_type}")
                        
                        if param_type == 'address':
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
                    
                    logging.info(f"Using ABI-based constructor args: {abi_args}")
                    tx = contract_factory.constructor(*abi_args).build_transaction({
                        'from': account.address,
                        'nonce': w3.eth.get_transaction_count(account.address),
                        'gas': 3000000,
                        'gasPrice': w3.eth.gas_price,
                        'chainId': chain_id
                    })
                else:
                    # No constructor or no inputs - deploy without arguments
                    logging.info("No constructor inputs found, deploying without arguments")
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
            
            logging.info(f"✅ Transaction sent: {tx_hash.hex()}")
            
            # Wait for receipt
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
            
            if receipt.status == 1:
                contract_address = receipt.contractAddress
                logging.info(f"✅ Contract deployed at: {contract_address}")
                
                return {
                    "success": True,
                    "contract_address": contract_address,
                    "tx_hash": tx_hash.hex(),
                    "gas_used": receipt.gasUsed,
                    "block_number": receipt.blockNumber
                }
            else:
                return {
                    "success": False,
                    "error": "Transaction failed",
                    "suggestions": ["Check gas limit", "Verify contract code"]
                }
                
        except Exception as e:
            logger.error(f"Deployment error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "suggestions": ["Check contract code", "Verify network connection", "Check account balance"]
            }