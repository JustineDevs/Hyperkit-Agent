"""
LazAI/Alith SDK Integration Service
Real integration with LazAI network using EVM address: 0xa43b752b6e941263eb5a7e3b96e2e0dea1a586ff
"""

import asyncio
import json
import os
from typing import Dict, Any, Optional, List
from core.config.manager import config
from .logging_system import logger, LogCategory, log_info, log_error, log_warning

try:
    from lazai import LazAIClient
    from alith import Agent
    LAZAI_AVAILABLE = True
except ImportError:
    LAZAI_AVAILABLE = False
    print("⚠️  WARNING: LazAI SDK not available - Install with: pip install lazai alith")

class HyperKitLazAIIntegration:
    """
    Real LazAI/Alith SDK integration for HyperKit Agent
    Uses EVM address: 0xa43b752b6e941263eb5a7e3b96e2e0dea1a586ff
    """
    
    def __init__(self):
        self.config = config
        self.evm_address = self.config.get('LAZAI_EVM_ADDRESS', '0xa43b752b6e941263eb5a7e3b96e2e0dea1a586ff')
        self.private_key = self.config.get('PRIVATE_KEY')
        self.rsa_private_key = self.config.get('LAZAI_RSA_PRIVATE_KEY')
        self.ipfs_jwt = self.config.get('IPFS_JWT')
        self.lazai_configured = self._check_lazai_config()
        
        self.client = None
        self.agent = None
        
        if self.lazai_configured and LAZAI_AVAILABLE:
            self._initialize_lazai()
    
    def _check_lazai_config(self) -> bool:
        """Check if LazAI is properly configured"""
        return (self.private_key is not None and 
                self.private_key.strip() != '' and
                self.private_key != 'your_ethereum_private_key_here' and
                LAZAI_AVAILABLE)
    
    def _initialize_lazai(self):
        """Initialize LazAI client and agent"""
        try:
            log_info(LogCategory.AI_AGENT, f"Initializing LazAI client for EVM address: {self.evm_address}")
            
            # Initialize LazAI client with private key
            self.client = LazAIClient()
            
            # Initialize Alith agent
            self.agent = Agent(model="gpt-4o-mini")
            
            log_info(LogCategory.AI_AGENT, "LazAI client and agent initialized successfully")
            print("✅ LazAI client and agent initialized successfully")
            
        except Exception as e:
            log_error(LogCategory.AI_AGENT, "Failed to initialize LazAI client", e)
            print(f"❌ Failed to initialize LazAI client: {e}")
            self.lazai_configured = False
    
    async def register_user(self, amount: int = 10000000) -> Dict[str, Any]:
        """Register user on LazAI network"""
        if not self.lazai_configured:
            return {"status": "error", "message": "LazAI not configured"}
        
        try:
            log_info(LogCategory.AI_AGENT, f"Registering user {self.evm_address} with amount {amount}")
            
            # Check if user already exists
            try:
                user_info = self.client.get_user(self.client.wallet.address)
                log_info(LogCategory.AI_AGENT, f"User already exists: {user_info}")
                return {
                    "status": "success",
                    "message": "User already registered",
                    "user_info": user_info
                }
            except Exception:
                # User doesn't exist, register new user
                log_info(LogCategory.AI_AGENT, "Adding new user and funding inference account")
                result = self.client.add_user(amount=amount)
                
                # Deposit inference funds
                inference_deposit = self.client.deposit_inference(
                    '0xc3e98E8A9aACFc9ff7578C2F3BA48CA4477Ecf49', 
                    1000000
                )
                
                log_info(LogCategory.AI_AGENT, f"User registered successfully: {result}")
                return {
                    "status": "success",
                    "message": "User registered successfully",
                    "registration": result,
                    "inference_deposit": inference_deposit
                }
                
        except Exception as e:
            log_error(LogCategory.AI_AGENT, "User registration failed", e)
            return {
                "status": "error",
                "error": str(e),
                "message": "User registration failed"
            }
    
    async def mint_data_token(self, file_path: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Mint a data token for the uploaded file"""
        if not self.lazai_configured:
            return {"status": "error", "message": "LazAI not configured"}
        
        try:
            log_info(LogCategory.AI_AGENT, f"Minting data token for file: {file_path}")
            
            # Upload file and mint data token
            result = self.client.mint_data_token(
                file_path=file_path,
                metadata=metadata or {}
            )
            
            file_id = result.get('file_id')
            log_info(LogCategory.AI_AGENT, f"Data token minted successfully. File ID: {file_id}")
            
            return {
                "status": "success",
                "file_id": file_id,
                "result": result,
                "message": "Data token minted successfully"
            }
            
        except Exception as e:
            log_error(LogCategory.AI_AGENT, "Data token minting failed", e)
            return {
                "status": "error",
                "error": str(e),
                "message": "Data token minting failed"
            }
    
    async def run_inference(self, file_id: str, prompt: str, model: str = "gpt-4o-mini") -> Dict[str, Any]:
        """Run private inference on LazAI network"""
        if not self.lazai_configured:
            return {"status": "error", "message": "LazAI not configured"}
        
        try:
            log_info(LogCategory.AI_AGENT, f"Running inference on file {file_id} with prompt: {prompt[:50]}...")
            
            # Ensure user is registered
            await self.register_user()
            
            # Run inference using Alith agent
            result = self.agent.infer(
                file_id=file_id,
                prompt=prompt,
                client=self.client
            )
            
            log_info(LogCategory.AI_AGENT, f"Inference completed successfully")
            
            return {
                "status": "success",
                "result": result,
                "file_id": file_id,
                "prompt": prompt,
                "model": model
            }
            
        except Exception as e:
            log_error(LogCategory.AI_AGENT, "Inference failed", e)
            return {
                "status": "error",
                "error": str(e),
                "message": "Inference failed"
            }
    
    async def generate_contract_with_lazai(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Generate smart contract using LazAI inference"""
        if not self.lazai_configured:
            return {"status": "error", "message": "LazAI not configured"}
        
        try:
            log_info(LogCategory.AI_AGENT, f"Generating contract with LazAI: {requirements.get('name', 'Unknown')}")
            
            # Create a temporary file with requirements
            requirements_file = "temp_requirements.json"
            with open(requirements_file, 'w') as f:
                json.dump(requirements, f, indent=2)
            
            # Mint data token for requirements
            mint_result = await self.mint_data_token(requirements_file)
            if mint_result["status"] != "success":
                return mint_result
            
            file_id = mint_result["file_id"]
            
            # Create contract generation prompt
            prompt = f"""
            Generate a smart contract based on these requirements:
            - Name: {requirements.get('name', 'Contract')}
            - Type: {requirements.get('type', 'ERC20')}
            - Features: {requirements.get('features', 'Standard')}
            - Security: {requirements.get('security', 'High')}
            - Gas Optimization: {requirements.get('gas_optimization', True)}
            
            Please generate a complete, secure, and optimized Solidity contract.
            Include proper documentation, error handling, and security best practices.
            """
            
            # Run inference
            inference_result = await self.run_inference(file_id, prompt)
            if inference_result["status"] != "success":
                return inference_result
            
            # Clean up temporary file
            if os.path.exists(requirements_file):
                os.remove(requirements_file)
            
            log_info(LogCategory.AI_AGENT, "Contract generated successfully with LazAI")
            
            return {
                "status": "success",
                "contract_code": inference_result["result"],
                "file_id": file_id,
                "requirements": requirements,
                "method": "lazai_inference"
            }
            
        except Exception as e:
            log_error(LogCategory.AI_AGENT, "Contract generation with LazAI failed", e)
            return {
                "status": "error",
                "error": str(e),
                "message": "Contract generation with LazAI failed"
            }
    
    async def audit_contract_with_lazai(self, contract_code: str) -> Dict[str, Any]:
        """Audit smart contract using LazAI inference"""
        if not self.lazai_configured:
            return {"status": "error", "message": "LazAI not configured"}
        
        try:
            log_info(LogCategory.AI_AGENT, "Auditing contract with LazAI")
            
            # Create a temporary file with contract code
            contract_file = "temp_contract.sol"
            with open(contract_file, 'w') as f:
                f.write(contract_code)
            
            # Mint data token for contract
            mint_result = await self.mint_data_token(contract_file)
            if mint_result["status"] != "success":
                return mint_result
            
            file_id = mint_result["file_id"]
            
            # Create audit prompt
            prompt = """
            Perform a comprehensive security audit of this smart contract.
            Analyze for:
            1. Reentrancy vulnerabilities
            2. Integer overflow/underflow
            3. Access control issues
            4. Gas optimization opportunities
            5. Best practice violations
            6. Potential attack vectors
            
            Provide a detailed security report with:
            - Vulnerability severity levels (Critical, High, Medium, Low)
            - Specific line numbers and code snippets
            - Detailed explanations of each issue
            - Recommended fixes and improvements
            - Overall security score (0-100)
            """
            
            # Run inference
            inference_result = await self.run_inference(file_id, prompt)
            if inference_result["status"] != "success":
                return inference_result
            
            # Clean up temporary file
            if os.path.exists(contract_file):
                os.remove(contract_file)
            
            log_info(LogCategory.AI_AGENT, "Contract audit completed with LazAI")
            
            return {
                "status": "success",
                "audit_report": inference_result["result"],
                "file_id": file_id,
                "method": "lazai_inference"
            }
            
        except Exception as e:
            log_error(LogCategory.AI_AGENT, "Contract audit with LazAI failed", e)
            return {
                "status": "error",
                "error": str(e),
                "message": "Contract audit with LazAI failed"
            }
    
    async def get_user_info(self) -> Dict[str, Any]:
        """Get user information from LazAI network"""
        if not self.lazai_configured:
            return {"status": "error", "message": "LazAI not configured"}
        
        try:
            log_info(LogCategory.AI_AGENT, f"Retrieving user info for {self.evm_address}")
            
            user_info = self.client.get_user(self.client.wallet.address)
            
            return {
                "status": "success",
                "user_info": user_info,
                "evm_address": self.evm_address
            }
            
        except Exception as e:
            log_error(LogCategory.AI_AGENT, "Failed to get user info", e)
            return {
                "status": "error",
                "error": str(e),
                "message": "Failed to get user info"
            }
    
    async def deposit_inference_funds(self, amount: int = 1000000) -> Dict[str, Any]:
        """Deposit funds for inference operations"""
        if not self.lazai_configured:
            return {"status": "error", "message": "LazAI not configured"}
        
        try:
            log_info(LogCategory.AI_AGENT, f"Depositing {amount} for inference operations")
            
            result = self.client.deposit_inference(
                '0xc3e98E8A9aACFc9ff7578C2F3BA48CA4477Ecf49', 
                amount
            )
            
            log_info(LogCategory.AI_AGENT, f"Inference funds deposited successfully: {result}")
            
            return {
                "status": "success",
                "deposit_result": result,
                "amount": amount
            }
            
        except Exception as e:
            log_error(LogCategory.AI_AGENT, "Failed to deposit inference funds", e)
            return {
                "status": "error",
                "error": str(e),
                "message": "Failed to deposit inference funds"
            }
    
    def get_integration_status(self) -> Dict[str, Any]:
        """Get LazAI integration status"""
        return {
            "status": "success",
            "lazai_available": LAZAI_AVAILABLE,
            "lazai_configured": self.lazai_configured,
            "evm_address": self.evm_address,
            "client_initialized": self.client is not None,
            "agent_initialized": self.agent is not None,
            "private_key_configured": self.private_key is not None and self.private_key.strip() != '',
            "rsa_key_configured": self.rsa_private_key is not None and self.rsa_private_key.strip() != '',
            "ipfs_jwt_configured": self.ipfs_jwt is not None and self.ipfs_jwt.strip() != ''
        }
