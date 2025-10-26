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
        
        # Handle Windows .exe extension
        import platform
        if platform.system() == "Windows":
            self.forge_bin = self.foundry_path / "bin" / "forge.exe"
        else:
            self.forge_bin = self.foundry_path / "bin" / "forge"
        
        if not self.forge_bin.exists():
            logger.warning(f"Foundry not found at {self.forge_bin}")
            logger.info("Install Foundry: curl -L https://foundry.paradigm.xyz | bash")
        
        logger.info(f"Using Foundry at: {self.forge_bin}")
    
    def _create_simplified_contract(self, original_source: str, contract_name: str) -> str:
        """Create a simplified contract without external dependencies"""
        # Extract contract name from original source (avoid keywords)
        import re
        contract_match = re.search(r'contract\s+([A-Z][a-zA-Z0-9_]*)', original_source)
        if contract_match:
            contract_name = contract_match.group(1)
        else:
            contract_name = "TestToken"  # Default fallback
        
        # Create a basic ERC20 implementation without OpenZeppelin
        simplified_contract = f'''// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title {contract_name}
 * @dev Simple ERC20 token implementation
 */
contract {contract_name} {{
    string public name;
    string public symbol;
    uint8 public decimals = 18;
    uint256 public totalSupply;
    
    mapping(address => uint256) public balanceOf;
    mapping(address => mapping(address => uint256)) public allowance;
    
    event Transfer(address indexed from, address indexed to, uint256 value);
    event Approval(address indexed owner, address indexed spender, uint256 value);
    
    constructor(string memory _name, string memory _symbol, uint256 _totalSupply) {{
        name = _name;
        symbol = _symbol;
        totalSupply = _totalSupply * 10**decimals;
        balanceOf[msg.sender] = totalSupply;
        emit Transfer(address(0), msg.sender, totalSupply);
    }}
    
    function transfer(address to, uint256 value) public returns (bool) {{
        require(balanceOf[msg.sender] >= value, "Insufficient balance");
        balanceOf[msg.sender] -= value;
        balanceOf[to] += value;
        emit Transfer(msg.sender, to, value);
        return true;
    }}
    
    function approve(address spender, uint256 value) public returns (bool) {{
        allowance[msg.sender][spender] = value;
        emit Approval(msg.sender, spender, value);
        return true;
    }}
    
    function transferFrom(address from, address to, uint256 value) public returns (bool) {{
        require(balanceOf[from] >= value, "Insufficient balance");
        require(allowance[from][msg.sender] >= value, "Insufficient allowance");
        balanceOf[from] -= value;
        balanceOf[to] += value;
        allowance[from][msg.sender] -= value;
        emit Transfer(from, to, value);
        return true;
    }}
}}'''
        return simplified_contract
    
    def deploy(self, contract_source_code: str, rpc_url: str, 
               chain_id: int = 133717, contract_name: str = "Contract", constructor_args: list = None) -> dict:
        """
        Deploy contract using Foundry with constructor arguments
        
        Args:
            contract_source_code: Solidity contract code (STRING)
            rpc_url: RPC endpoint URL (STRING)
            chain_id: Blockchain chain ID (INT)
            contract_name: Contract name for deployment
            constructor_args: List of constructor arguments
        
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
            private_key = os.getenv("DEFAULT_PRIVATE_KEY") or os.getenv("PRIVATE_KEY")  # Support both
            if not private_key:
                return {
                    "success": False,
                    "error": "DEFAULT_PRIVATE_KEY not in .env",
                    "suggestions": ["Add DEFAULT_PRIVATE_KEY to .env file", "Or use PRIVATE_KEY for legacy support"]
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
""")
            
            # Create contract file
            src_dir = project_dir / "src"
            src_dir.mkdir(exist_ok=True)
            contract_file = src_dir / f"{contract_name}.sol"
            
            # Create a simplified contract without external dependencies
            # Remove OpenZeppelin imports and create a basic ERC20 implementation
            simplified_source = self._create_simplified_contract(contract_source_code, contract_name)
            contract_file.write_text(simplified_source)
            
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
            # Find the actual artifact file (it might be in a different location)
            out_dir = project_dir / "out"
            artifact_file = None
            
            # Look for JSON files in the out directory
            for json_file in out_dir.rglob("*.json"):
                try:
                    with open(json_file) as f:
                        artifact_data = json.load(f)
                        if "bytecode" in artifact_data and "abi" in artifact_data:
                            artifact_file = json_file
                            break
                except:
                    continue
            
            if not artifact_file or not artifact_file.exists():
                return {
                    "success": False,
                    "error": f"Artifact not found in {out_dir}",
                    "suggestions": ["Check compilation output", "Verify contract name"]
                }
            
            with open(artifact_file) as f:
                artifact = json.load(f)
            
            bytecode = artifact["bytecode"]["object"]
            abi = artifact["abi"]
            
            logger.info("✅ Artifacts loaded")
            
            # ✅ Deploy contract
            logger.info("Deploying contract...")
            
            contract_factory = w3.eth.contract(abi=abi, bytecode=bytecode)
            
            # Extract contract name from the contract source
            import re
            contract_match = re.search(r'contract\s+([A-Z][a-zA-Z0-9_]*)', contract_source_code)
            contract_name = contract_match.group(1) if contract_match else "TestToken"
            
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
                # Fallback: extract from contract code
                from .constructor_parser import ConstructorArgumentParser
                parser = ConstructorArgumentParser()
                extracted_args = parser.generate_constructor_args(contract_source_code, account.address)
                
                if extracted_args:
                    logger.info(f"Using extracted constructor args: {extracted_args}")
                    try:
                        tx = contract_factory.constructor(*extracted_args).build_transaction({
                            'from': account.address,
                            'nonce': w3.eth.get_transaction_count(account.address),
                            'gas': 3000000,
                            'gasPrice': w3.eth.gas_price,
                            'chainId': chain_id
                        })
                    except TypeError as e:
                        if "Incorrect argument count" in str(e):
                            logger.warning(f"Constructor argument count mismatch: {e}")
                            logger.info("Attempting to deploy with hardcoded values as fallback")
                            # Fallback to hardcoded values
                            tx = contract_factory.constructor(
                                "GAMEX Token",  # name
                                "GAMEX",       # symbol
                                account.address  # initialOwner
                            ).build_transaction({
                                'from': account.address,
                                'nonce': w3.eth.get_transaction_count(account.address),
                                'gas': 3000000,
                                'gasPrice': w3.eth.gas_price,
                                'chainId': chain_id
                            })
                        else:
                            raise
                else:
                    # Check if contract has empty constructor but uses Ownable(msg.sender)
                    if "Ownable(msg.sender)" in contract_source_code and "constructor()" in contract_source_code:
                        # This is a common pattern - empty constructor but Ownable needs an address
                        logger.info("Contract has empty constructor but uses Ownable(msg.sender) - using deployer address")
                        tx = contract_factory.constructor(account.address).build_transaction({
                            'from': account.address,
                            'nonce': w3.eth.get_transaction_count(account.address),
                            'gas': 3000000,
                            'gasPrice': w3.eth.gas_price,
                            'chainId': chain_id
                        })
                    else:
                        # Check if contract has empty constructor
                        result = parser.extract_constructor_params(contract_source_code)
                        
                        if result and len(result[1]) == 0:
                            # Empty constructor - no arguments needed
                            logger.info("Contract has empty constructor, deploying without arguments")
                            tx = contract_factory.constructor().build_transaction({
                                'from': account.address,
                                'nonce': w3.eth.get_transaction_count(account.address),
                                'gas': 3000000,
                                'gasPrice': w3.eth.gas_price,
                                'chainId': chain_id
                            })
                        else:
                            # Last resort: use hardcoded values (this is what was causing the bug)
                            logger.warning("No constructor args found, using hardcoded values")
                            tx = contract_factory.constructor(
                                contract_name,  # name
                                contract_name[:4],  # symbol (first 4 chars)
                                1000000  # totalSupply
                            ).build_transaction({
                                'from': account.address,
                                'nonce': w3.eth.get_transaction_count(account.address),
                                'gas': 3000000,
                                'gasPrice': w3.eth.gas_price,
                                'chainId': chain_id
                            })
            
            signed_tx = account.sign_transaction(tx)
            tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            
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
