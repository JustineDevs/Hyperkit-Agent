"""
Intent Router for HyperKit AI Agent
Classifies user requests and routes to appropriate tools and workflows
"""

import re
from typing import Dict, List, Tuple
from enum import Enum

class IntentType(Enum):
    SIMPLE_CONTRACT = "simple_contract"
    AUDIT_ONLY = "audit_only"
    DEBUG_TRANSACTION = "debug_transaction"

class IntentRouter:
    """Routes user intents to appropriate agent tools and workflows"""
    
    def __init__(self):
        self.intent_patterns = {
            IntentType.SIMPLE_CONTRACT: [
                r"erc20.*token",
                r"erc721.*nft",
                r"erc1155.*nft",
                r"simple.*contract",
                r"basic.*token",
                r"mint.*token",
                r"burn.*token",
                r"transfer.*token",
                r"create.*contract",
                r"generate.*contract",
                r"smart.*contract"
            ],
            IntentType.AUDIT_ONLY: [
                r"audit.*contract",
                r"security.*check",
                r"vulnerability.*scan",
                r"review.*code",
                r"check.*security",
                r"analyze.*contract"
            ],
            IntentType.DEBUG_TRANSACTION: [
                r"debug.*transaction",
                r"replay.*tx",
                r"step.*through",
                r"inspect.*variables",
                r"debug.*contract"
            ]
        }
        
        self.smart_contract_indicators = [
            "token", "nft", "contract", "mint", "burn", "transfer",
            "simple", "basic", "erc20", "erc721", "erc1155", "defi",
            "governance", "dao", "staking", "lending", "swap"
        ]

    def classify_intent(self, user_prompt: str) -> Tuple[IntentType, Dict[str, any]]:
        """
        Classify user intent and extract relevant parameters
        
        Args:
            user_prompt: User's natural language request
            
        Returns:
            Tuple of (IntentType, parameters_dict)
        """
        prompt_lower = user_prompt.lower()
        
        # Check for specific intent patterns
        for intent_type, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, prompt_lower):
                    return self._extract_parameters(intent_type, user_prompt)
        
        # Default to smart contract generation (no fallback - always returns intent)
        # This ensures all prompts are processed as contract generation requests
        return self._extract_parameters(IntentType.SIMPLE_CONTRACT, user_prompt)

    def _extract_parameters(self, intent_type: IntentType, prompt: str) -> Tuple[IntentType, Dict[str, any]]:
        """Extract relevant parameters based on intent type"""
        parameters = {
            "original_prompt": prompt,
            "requires_deployment": intent_type != IntentType.AUDIT_ONLY,
            "requires_debugging": intent_type == IntentType.DEBUG_TRANSACTION,
            "contract_type": self._detect_contract_type(prompt)
        }
        
        return intent_type, parameters

    def _detect_contract_type(self, prompt: str) -> str:
        """Detect the type of smart contract from prompt"""
        prompt_lower = prompt.lower()
        
        if "erc20" in prompt_lower or "token" in prompt_lower:
            return "ERC20"
        elif "erc721" in prompt_lower or "nft" in prompt_lower:
            return "ERC721"
        elif "erc1155" in prompt_lower:
            return "ERC1155"
        elif "defi" in prompt_lower or "dex" in prompt_lower or "swap" in prompt_lower:
            return "DeFi"
        elif "governance" in prompt_lower or "dao" in prompt_lower:
            return "Governance"
        elif "staking" in prompt_lower or "yield" in prompt_lower:
            return "Staking"
        elif "lending" in prompt_lower or "borrow" in prompt_lower:
            return "Lending"
        else:
            return "Generic"

    def get_workflow_tools(self, intent_type: IntentType) -> List[str]:
        """Get required tools for specific intent type"""
        tool_mapping = {
            IntentType.SIMPLE_CONTRACT: ["generate_contract", "audit_contract", "deploy_contract"],
            IntentType.AUDIT_ONLY: ["audit_contract"],
            IntentType.DEBUG_TRANSACTION: ["debug_transaction", "replay_tx"]
        }
        
        return tool_mapping.get(intent_type, ["generate_contract", "audit_contract"])

    def get_workflow_steps(self, intent_type: IntentType) -> List[str]:
        """Get workflow steps for specific intent type"""
        step_mapping = {
            IntentType.SIMPLE_CONTRACT: [
                "1. Generate smart contract code",
                "2. Run security audit",
                "3. Deploy to blockchain",
                "4. Log audit results onchain",
                "5. Return contract address and audit summary"
            ],
            IntentType.AUDIT_ONLY: [
                "1. Analyze contract code",
                "2. Run security audit",
                "3. Log audit results onchain",
                "4. Return audit report"
            ],
            IntentType.DEBUG_TRANSACTION: [
                "1. Load transaction data",
                "2. Step through execution",
                "3. Inspect variables and state",
                "4. Return debug information"
            ]
        }
        
        return step_mapping.get(intent_type, ["1. Process request", "2. Return result"])
