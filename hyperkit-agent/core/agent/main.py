"""
HyperKit AI Agent - Core Implementation
Combines smart contract generation, auditing, and deployment capabilities
"""

import asyncio
import json
import logging
import subprocess
from typing import Dict, Any, Optional
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HyperKitAgent:
    """
    Main HyperKit AI Agent that orchestrates smart contract generation,
    auditing, debugging, and deployment workflows.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the HyperKit Agent with configuration."""
        self.config = config or {}
        
        # Initialize free LLM router
        from core.llm.router import HybridLLMRouter
        self.llm_router = HybridLLMRouter()
        
        # Initialize Obsidian RAG
        from services.rag.obsidian_rag import ObsidianRAG
        vault_path = self.config.get('OBSIDIAN_VAULT_PATH', '~/hyperkit-kb')
        self.rag = ObsidianRAG(vault_path=vault_path)
        
        # Initialize mock Alith client
        from core.tools.alith_mock import AlithClient
        self.alith = AlithClient()
        
        # Register available tools
        self.tools = {
            'generate': self.generate_contract,
            'audit': self.audit_contract,
            'deploy': self.deploy_contract,
            'debug': self.debug_contract,
            'analyze': self.analyze_contract
        }
        
        logger.info("HyperKit Agent initialized successfully")
    
    async def generate_contract(self, prompt: str, context: str = "") -> Dict[str, Any]:
        """
        Generate a smart contract based on natural language prompt using free LLM models.
        
        Args:
            prompt: Natural language description of the contract
            context: Additional context from RAG system
            
        Returns:
            Dictionary containing generated contract code and metadata
        """
        try:
            # Retrieve context from Obsidian vault
            rag_context = ""
            if self.rag:
                rag_context = self.rag.retrieve(prompt)
            
            # Combine all context
            full_context = f"{context}\n\n{rag_context}".strip()
            
            # Create enhanced prompt with context
            enhanced_prompt = self._create_contract_generation_prompt(prompt, full_context)
            
            # Use free LLM router for code generation
            contract_code = self.llm_router.route(enhanced_prompt, task_type='code', prefer_local=True)
            
            # Post-process the generated code
            contract_code = self._post_process_contract(contract_code)
            
            return {
                'status': 'success',
                'contract_code': contract_code,
                'prompt': prompt,
                'context_used': full_context,
                'provider_used': 'free_llm_router'
            }
        except Exception as e:
            logger.error(f"Contract generation failed: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'prompt': prompt
            }
    
    async def audit_contract(self, contract_code: str) -> Dict[str, Any]:
        """
        Audit a smart contract using multiple security tools.
        
        Args:
            contract_code: Solidity contract code to audit
            
        Returns:
            Dictionary containing audit results and severity level
        """
        try:
            # Import audit service
            from services.audit.auditor import SmartContractAuditor
            
            auditor = SmartContractAuditor()
            audit_results = await auditor.audit(contract_code)
            
            return {
                'status': 'success',
                'results': audit_results,
                'severity': audit_results.get('severity', 'unknown')
            }
        except Exception as e:
            logger.error(f"Contract audit failed: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'severity': 'critical'
            }
    
    async def deploy_contract(self, contract_code: str, network: str = 'hyperion') -> Dict[str, Any]:
        """
        Deploy a smart contract to the specified network.
        
        Args:
            contract_code: Solidity contract code to deploy
            network: Target network for deployment
            
        Returns:
            Dictionary containing deployment details
        """
        try:
            # Import deployment service
            from services.deployment.deployer import MultiChainDeployer
            
            deployer = MultiChainDeployer()
            deployment_result = await deployer.deploy(contract_code, network)
            
            return {
                'status': 'success',
                'deployment': deployment_result,
                'network': network
            }
        except Exception as e:
            logger.error(f"Contract deployment failed: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'network': network
            }
    
    async def debug_contract(self, tx_hash: str, rpc_url: str) -> Dict[str, Any]:
        """
        Debug a transaction using EDB debugger.
        
        Args:
            tx_hash: Transaction hash to debug
            rpc_url: RPC URL for the network
            
        Returns:
            Dictionary containing debug results
        """
        try:
            # Integration with EDB debugger
            cmd = f"edb --rpc-urls {rpc_url} replay {tx_hash}"
            result = subprocess.run(cmd.split(), capture_output=True, text=True)
            
            return {
                'status': 'success',
                'debug_output': result.stdout,
                'tx_hash': tx_hash,
                'rpc_url': rpc_url
            }
        except Exception as e:
            logger.error(f"Contract debugging failed: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'tx_hash': tx_hash
            }
    
    async def analyze_contract(self, contract_code: str) -> Dict[str, Any]:
        """
        Perform comprehensive analysis of a smart contract.
        
        Args:
            contract_code: Solidity contract code to analyze
            
        Returns:
            Dictionary containing analysis results
        """
        try:
            # Perform static analysis
            analysis_results = {
                'gas_estimation': self._estimate_gas(contract_code),
                'complexity_score': self._calculate_complexity(contract_code),
                'security_patterns': self._check_security_patterns(contract_code),
                'best_practices': self._check_best_practices(contract_code)
            }
            
            return {
                'status': 'success',
                'analysis': analysis_results
            }
        except Exception as e:
            logger.error(f"Contract analysis failed: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    async def run_workflow(self, user_prompt: str) -> Dict[str, Any]:
        """
        Execute the complete workflow: generate -> audit -> deploy.
        
        Args:
            user_prompt: User's natural language request
            
        Returns:
            Dictionary containing workflow results
        """
        try:
            logger.info(f"Starting workflow for prompt: {user_prompt}")
            
            # Step 1: RAG-enhanced context retrieval
            context = ""
            if self.rag:
                context = self.rag.retrieve(user_prompt)
            
            # Step 2: Generate contract
            generation_result = await self.generate_contract(user_prompt, context)
            if generation_result['status'] != 'success':
                return generation_result
            
            contract_code = generation_result['contract_code']
            
            # Step 3: Audit contract
            audit_result = await self.audit_contract(contract_code)
            if audit_result['status'] != 'success':
                return audit_result
            
            # Step 4: Deploy if audit passes
            if audit_result['severity'] in ['low', 'medium']:
                deployment_result = await self.deploy_contract(contract_code)
                
                # Log audit results with deployment
                if self.alith and deployment_result['status'] == 'success':
                    self.alith.log_audit(
                        deployment_result['deployment']['address'],
                        audit_result['results']
                    )
                
                return {
                    'status': 'success',
                    'workflow': 'complete',
                    'generation': generation_result,
                    'audit': audit_result,
                    'deployment': deployment_result
                }
            else:
                return {
                    'status': 'audit_failed',
                    'workflow': 'stopped_at_audit',
                    'generation': generation_result,
                    'audit': audit_result,
                    'reason': f"Audit severity too high: {audit_result['severity']}"
                }
                
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'workflow': 'failed'
            }
    
    def _estimate_gas(self, contract_code: str) -> Dict[str, int]:
        """Estimate gas usage for contract functions."""
        # Placeholder for gas estimation logic
        return {
            'deployment': 1000000,
            'average_function': 50000,
            'complex_function': 200000
        }
    
    def _calculate_complexity(self, contract_code: str) -> int:
        """Calculate cyclomatic complexity of the contract."""
        # Placeholder for complexity calculation
        return len(contract_code.split('\n')) // 10
    
    def _check_security_patterns(self, contract_code: str) -> Dict[str, bool]:
        """Check for common security patterns."""
        return {
            'has_reentrancy_guard': 'ReentrancyGuard' in contract_code,
            'has_access_control': 'onlyOwner' in contract_code or 'onlyRole' in contract_code,
            'has_pausable': 'Pausable' in contract_code,
            'uses_safe_math': 'SafeMath' in contract_code or 'unchecked' not in contract_code
        }
    
    def _check_best_practices(self, contract_code: str) -> Dict[str, bool]:
        """Check for Solidity best practices."""
        return {
            'has_nat_spec': '/**' in contract_code and '*/' in contract_code,
            'has_events': 'event ' in contract_code,
            'has_modifiers': 'modifier ' in contract_code,
            'uses_openzeppelin': 'import "@openzeppelin' in contract_code
        }
    
    def _select_ai_provider(self) -> tuple[str, str]:
        """
        Select the best available AI provider based on configured API keys.
        
        Returns:
            Tuple of (provider_name, api_key)
        """
        # Priority order for AI providers
        providers = [
            ('openai', 'OPENAI_API_KEY'),
            ('deepseek', 'DEEPSEEK_API_KEY'),
            ('xai', 'XAI_API_KEY'),
            ('gpt-oss', 'GPT_OSS_API_KEY'),
            ('anthropic', 'ANTHROPIC_API_KEY'),
            ('google', 'GOOGLE_API_KEY'),
            ('dashscope', 'DASHSCOPE_API_KEY')
        ]
        
        for provider, key_name in providers:
            api_key = self.config.get(key_name)
            if api_key and api_key != f'your_{key_name.lower()}_here':
                logger.info(f"Selected AI provider: {provider}")
                return provider, api_key
        
        # Fallback to OpenAI with a placeholder
        logger.warning("No valid API keys found, using OpenAI with placeholder")
        return 'openai', 'placeholder-key'
    
    def _create_contract_generation_prompt(self, user_prompt: str, context: str = "") -> str:
        """Create enhanced prompt for contract generation."""
        base_prompt = f"""
You are an expert Solidity smart contract developer. Generate a secure, production-ready smart contract based on the user's request.

User Request: {user_prompt}

Additional Context:
{context}

Requirements:
1. Use Solidity ^0.8.0
2. Follow security best practices
3. Include proper access controls
4. Add events for important actions
5. Include NatSpec documentation
6. Use OpenZeppelin contracts when appropriate
7. Implement proper error handling
8. Add reentrancy guards where needed

Generate only the Solidity contract code, no explanations or markdown formatting.
"""
        return base_prompt.strip()
    
    def _post_process_contract(self, contract_code: str) -> str:
        """Post-process generated contract code."""
        # Remove markdown formatting if present
        if contract_code.startswith('```solidity'):
            contract_code = contract_code.replace('```solidity', '').replace('```', '')
        
        if contract_code.startswith('```'):
            contract_code = contract_code.replace('```', '')
        
        # Clean up extra whitespace
        contract_code = contract_code.strip()
        
        return contract_code


# Example usage and testing
async def main():
    """Example usage of the HyperKit Agent."""
    config = {
        'openai_api_key': 'your-api-key-here',
        'networks': {
            'hyperion': 'https://hyperion-testnet.metisdevops.link',
            'polygon': 'https://polygon-rpc.com'
        }
    }
    
    agent = HyperKitAgent(config)
    
    # Test workflow
    prompt = "Create a simple ERC20 token contract with minting functionality"
    result = await agent.run_workflow(prompt)
    
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
