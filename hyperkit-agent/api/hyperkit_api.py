"""
HyperKit Agent Programmatic API

Exposes all pipeline stages as callable Python functions for programmatic use.
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class HyperKitAPI:
    """
    Programmatic API for HyperKit Agent workflow stages.
    
    Usage:
        api = HyperKitAPI(config)
        result = await api.generate("Create an ERC20 token")
        compiled = await api.compile(result["contract_code"])
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize HyperKit API"""
        from core.agent.main import HyperKitAgent
        from core.config.loader import get_config
        
        if config is None:
            config = get_config().to_dict()
        
        self.agent = HyperKitAgent(config)
        self.config = config
    
    async def generate(self, prompt: str, context: str = "") -> Dict[str, Any]:
        """
        Generate a smart contract from a natural language prompt.
        
        Args:
            prompt: Natural language description of the contract
            context: Optional RAG context to enhance generation
            
        Returns:
            Dict with contract_code, contract_name, status
        """
        logger.info(f"Generating contract: {prompt}")
        return await self.agent.generate_contract(prompt, context)
    
    async def compile(self, contract_code: str, contract_name: str = None) -> Dict[str, Any]:
        """
        Compile a smart contract using Foundry.
        
        Args:
            contract_code: Solidity source code
            contract_name: Optional contract name
            
        Returns:
            Dict with success status, artifact_path, abi
        """
        logger.info(f"Compiling contract: {contract_name or 'Unknown'}")
        return await self._compile_contract(contract_name or "Contract", contract_code)
    
    async def audit(self, contract_code: str) -> Dict[str, Any]:
        """
        Audit a smart contract for security issues.
        
        Args:
            contract_code: Solidity source code
            
        Returns:
            Dict with audit results, severity, issues
        """
        logger.info("Auditing contract")
        return await self.agent.audit_contract(contract_code)
    
    async def deploy(
        self, 
        contract_code: str, 
        network: str = "hyperion",
        contract_name: str = None
    ) -> Dict[str, Any]:
        """
        Deploy a smart contract to blockchain.
        
        Args:
            contract_code: Solidity source code
            network: Target network (default: hyperion)
            contract_name: Optional contract name
            
        Returns:
            Dict with contract_address, tx_hash, status
        """
        logger.info(f"Deploying contract to {network}")
        return await self.agent.deploy_contract(contract_code, network, contract_name)
    
    async def verify(
        self, 
        contract_address: str, 
        network: str = "hyperion"
    ) -> Dict[str, Any]:
        """
        Verify a deployed contract on block explorer.
        
        Args:
            contract_address: Deployed contract address
            network: Network where contract is deployed
            
        Returns:
            Dict with verification status, explorer_url
        """
        logger.info(f"Verifying contract: {contract_address}")
        return await self.agent.verify_contract(contract_address, network)
    
    async def test(self, contract_code: str) -> Dict[str, Any]:
        """
        Run tests on a contract.
        
        Args:
            contract_code: Solidity source code
            
        Returns:
            Dict with test results, coverage
        """
        logger.info("Running tests")
        # This would call the agent's test functionality
        # For now, return a placeholder
        return {
            "status": "success",
            "message": "Testing functionality not yet implemented in API"
        }
    
    async def workflow(
        self,
        prompt: str,
        network: str = "hyperion",
        test_only: bool = False,
        upload_scope: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run complete workflow (generate → compile → audit → deploy → verify).
        
        Args:
            prompt: Natural language contract description
            network: Target network (default: hyperion)
            test_only: If True, skip deployment
            upload_scope: Optional IPFS upload scope ('team' or 'community')
            
        Returns:
            Complete workflow results
        """
        logger.info(f"Running complete workflow: {prompt}")
        return await self.agent.run_workflow(
            user_prompt=prompt,
            network=network,
            test_only=test_only,
            upload_scope=upload_scope
        )
    
    async def _compile_contract(self, contract_name: str, contract_code: str) -> Dict[str, Any]:
        """Internal compilation helper"""
        return await self.agent._compile_contract(contract_name, contract_code)


# Convenience function for synchronous use
def run_workflow(
    prompt: str,
    network: str = "hyperion",
    test_only: bool = False,
    upload_scope: Optional[str] = None
) -> Dict[str, Any]:
    """
    Synchronous wrapper for workflow execution.
    
    Usage:
        result = run_workflow("Create an ERC20 token")
    """
    api = HyperKitAPI()
    return asyncio.run(api.workflow(prompt, network, test_only, upload_scope))


def generate_contract(prompt: str, context: str = "") -> Dict[str, Any]:
    """
    Synchronous wrapper for contract generation.
    
    Usage:
        result = generate_contract("Create an ERC20 token")
    """
    api = HyperKitAPI()
    return asyncio.run(api.generate(prompt, context))


def compile_contract(contract_code: str, contract_name: str = None) -> Dict[str, Any]:
    """
    Synchronous wrapper for contract compilation.
    
    Usage:
        result = compile_contract(code, "MyToken")
    """
    api = HyperKitAPI()
    return asyncio.run(api.compile(contract_code, contract_name))


def audit_contract(contract_code: str) -> Dict[str, Any]:
    """
    Synchronous wrapper for contract auditing.
    
    Usage:
        result = audit_contract(code)
    """
    api = HyperKitAPI()
    return asyncio.run(api.audit(contract_code))


def deploy_contract(
    contract_code: str,
    network: str = "hyperion",
    contract_name: str = None
) -> Dict[str, Any]:
    """
    Synchronous wrapper for contract deployment.
    
    Usage:
        result = deploy_contract(code, "hyperion", "MyToken")
    """
    api = HyperKitAPI()
    return asyncio.run(api.deploy(contract_code, network, contract_name))

