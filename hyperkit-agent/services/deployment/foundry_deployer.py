"""
Foundry-based smart contract deployer
Uses Foundry (forge) for compilation and deployment
Replaces solcx for better cross-platform support
"""

import os
import json
import subprocess
import logging
from pathlib import Path
from typing import Dict, Any
from web3 import Web3
from eth_account import Account

logger = logging.getLogger(__name__)

class FoundryDeployer:
    """Deploy smart contracts using Foundry (forge)"""
    
    def __init__(self, foundry_home: str = None):
        """
        Initialize Foundry deployer
        
        Args:
            foundry_home: Path to foundry installation (auto-detected if None)
        """
        self.foundry_home = foundry_home or os.getenv("FOUNDRY_HOME", "~/.foundry")
        self.foundry_path = Path(self.foundry_home).expanduser()
        self.forge_bin = self.foundry_path / "bin" / "forge"
        
        if not self.forge_bin.exists():
            logger.warning(f"Foundry not found at {self.forge_bin}")
            logger.info("Install Foundry: curl -L https://foundry.paradigm.xyz | bash")
        
        logger.info(f"Using Foundry at: {self.forge_bin}")
    
    def deploy(self, contract_source_code: str, rpc_url: str, 
               chain_id: int = 133717, contract_name: str = "Contract") -> dict:
        """
        Deploy contract using Foundry
        
        Args:
            contract_source_code: Solidity contract code (STRING)
            rpc_url: RPC endpoint URL (STRING)
            chain_id: Blockchain chain ID (INT)
            contract_name: Contract name for deployment
        
        Returns:
            {"success": True/False, "transaction_hash": "...", "contract_address": "..."}
        """
        try:
            # Type validation
            if not isinstance(contract_source_code, str):
                raise TypeError(f"source_code must be str, got {type(contract_source_code)}")
            
            if not isinstance(rpc_url, str):
                raise TypeError(f"rpc_url must be str, got {type(rpc_url)}")
            
            if not isinstance(chain_id, int):
                raise TypeError(f"chain_id must be int, got {type(chain_id)}")
            
            logger.info(f"Deploying via Foundry to RPC: {rpc_url[:40]}... (Chain: {chain_id})")
            
            # ✅ Check Foundry installation
            if not self.forge_bin.exists():
                return {
                    "success": False,
                    "error": f"Foundry not installed at {self.forge_bin}",
                    "suggestions": [
                        "Install Foundry: curl -L https://foundry.paradigm.xyz | bash",
                        "Set FOUNDRY_HOME if installed elsewhere"
                    ]
                }
            
            # ✅ Verify RPC connection
            w3 = Web3(Web3.HTTPProvider(rpc_url))
            if not w3.is_connected():
                return {
                    "success": False,
                    "error": f"Cannot connect to RPC: {rpc_url}",
                    "suggestions": ["Check RPC URL", "Verify network is online"]
                }
            
            logger.info("✅ Connected to RPC")
            
            # ✅ Get deployment account
            private_key = os.getenv("DEFAULT_PRIVATE_KEY")
            if not private_key:
                return {
                    "success": False,
                    "error": "DEFAULT_PRIVATE_KEY not in .env",
                    "suggestions": ["Add DEFAULT_PRIVATE_KEY to .env file"]
                }
            
            account = Account.from_key(private_key)
            logger.info(f"✅ Using account: {account.address}")
            
            # ✅ Create temporary Foundry project
            project_dir = Path("/tmp/hyperagent_foundry")
            project_dir.mkdir(exist_ok=True)
            
            # Create Foundry.toml
            foundry_toml = project_dir / "foundry.toml"
            foundry_toml.write_text("""
[profile.default]
src = "src"
out = "out"
libs = ["lib"]

[dependencies]
@openzeppelin/contracts = { git = "https://github.com/OpenZeppelin/openzeppelin-contracts.git" }
""")
            
            # Create contract file
            src_dir = project_dir / "src"
            src_dir.mkdir(exist_ok=True)
            contract_file = src_dir / f"{contract_name}.sol"
            contract_file.write_text(contract_source_code)
            
            logger.info(f"✅ Created contract file: {contract_file}")
            
            # ✅ Compile with forge
            logger.info("Compiling contract with Foundry...")
            
            compile_cmd = [
                str(self.forge_bin),
                "build",
                "--root", str(project_dir),
                "--out", str(project_dir / "out")
            ]
            
            result = subprocess.run(
                compile_cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                logger.error(f"Compilation failed: {result.stderr}")
                return {
                    "success": False,
                    "error": f"Compilation failed: {result.stderr}",
                    "suggestions": ["Check contract syntax", "Verify imports"]
                }
            
            logger.info("✅ Compilation successful")
            
            # ✅ Read compiled artifacts
            artifact_file = project_dir / "out" / f"{contract_name}.sol" / f"{contract_name}.json"
            if not artifact_file.exists():
                return {
                    "success": False,
                    "error": f"Artifact not found: {artifact_file}",
                    "suggestions": ["Check contract name", "Verify compilation"]
                }
            
            with open(artifact_file) as f:
                artifact = json.load(f)
            
            bytecode = artifact["bytecode"]["object"]
            abi = artifact["abi"]
            
            logger.info("✅ Artifacts loaded")
            
            # ✅ Deploy contract
            logger.info("Deploying contract...")
            
            contract_factory = w3.eth.contract(abi=abi, bytecode=bytecode)
            
            tx = contract_factory.constructor().build_transaction({
                'from': account.address,
                'nonce': w3.eth.get_transaction_count(account.address),
                'gas': 3000000,
                'gasPrice': w3.eth.gas_price,
                'chainId': chain_id
            })
            
            signed_tx = account.sign_transaction(tx)
            tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            logger.info(f"✅ TX sent: {tx_hash.hex()}")
            
            # ✅ Wait for receipt
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
            
            contract_address = receipt['contractAddress']
            
            logger.info(f"✅ Deployed to: {contract_address}")
            
            return {
                "success": True,
                "transaction_hash": tx_hash.hex(),
                "contract_address": contract_address,
                "gas_used": receipt['gasUsed'],
                "block_number": receipt['blockNumber']
            }
        
        except TypeError as te:
            logger.error(f"Type error: {te}")
            return {
                "success": False,
                "error": f"Type error: {str(te)}",
                "suggestions": ["Ensure rpc_url is a string", "Check all parameters types"]
            }
        except subprocess.TimeoutExpired:
            logger.error("Compilation timeout")
            return {
                "success": False,
                "error": "Compilation timeout",
                "suggestions": ["Contract too complex", "Try simpler contract"]
            }
        except Exception as e:
            logger.error(f"Deploy error: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
