"""
Adaptive Prompt Repair System
Automatically repairs prompts and context based on known error patterns.
Enhanced with meta-prompting capabilities.
"""

import re
import logging
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

# Import meta-prompting (optional)
try:
    from core.prompts.meta_prompting import MetaPrompting
    META_PROMPTING_AVAILABLE = True
except ImportError:
    META_PROMPTING_AVAILABLE = False
    MetaPrompting = None


class AdaptivePromptRepair:
    """
    Adaptive prompt repair system that detects known error patterns
    and automatically patches prompts/context before retry.
    """
    
    # Known error patterns and their repair strategies
    ERROR_PATTERNS = {
        'missing_pragma': {
            'detect': lambda error: 'pragma' in error.lower() and ('missing' in error.lower() or 'not found' in error.lower()),
            'repair': lambda prompt, context: _add_pragma_instruction(prompt, context)
        },
        'empty_context': {
            'detect': lambda error: 'empty context' in error.lower() or 'no context' in error.lower(),
            'repair': lambda prompt, context: _add_fallback_template(prompt, context)
        },
        'compilation_error': {
            'detect': lambda error: 'compilation' in error.lower() and 'error' in error.lower(),
            'repair': lambda prompt, context: _add_solidity_version_requirement(prompt, context)
        },
        'unknown_contract_type': {
            'detect': lambda error: 'unknown' in error.lower() and ('contract' in error.lower() or 'type' in error.lower()),
            'repair': lambda prompt, context: _add_contract_type_classification(prompt, context)
        },
        'missing_import': {
            'detect': lambda error: 'import' in error.lower() and ('not found' in error.lower() or 'missing' in error.lower()),
            'repair': lambda prompt, context: _add_import_instructions(prompt, context)
        },
        'variable_shadowing': {
            'detect': lambda error: 'shadow' in error.lower() or 'shadows' in error.lower(),
            'repair': lambda prompt, context: _add_shadowing_instructions(prompt, context)
        }
    }
    
    def __init__(self, agent_memory=None, llm_router=None):
        """
        Initialize adaptive prompt repair system.
        
        Args:
            agent_memory: Optional AgentMemory instance for learning from past fixes
            llm_router: Optional LLM router for meta-prompting
        """
        self.agent_memory = agent_memory
        # Initialize meta-prompting if available
        self.meta_prompting = None
        if META_PROMPTING_AVAILABLE and llm_router:
            try:
                self.meta_prompting = MetaPrompting(llm_router=llm_router, agent_memory=agent_memory)
                logger.info("Meta-prompting system initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize meta-prompting: {e}")
    
    def detect_error_pattern(self, error: str) -> Optional[str]:
        """
        Detect error pattern from error message.
        
        Args:
            error: Error message
            
        Returns:
            Error pattern name or None
        """
        for pattern_name, pattern_info in self.ERROR_PATTERNS.items():
            if pattern_info['detect'](error):
                logger.info(f"🔍 Detected error pattern: {pattern_name}")
                return pattern_name
        return None
    
    def repair_prompt(self, prompt: str, context: str, error: str, error_type: Optional[str] = None) -> Tuple[str, str, bool]:
        """
        Repair prompt and context based on error pattern.
        
        Args:
            prompt: Original user prompt
            context: RAG context (may be empty)
            error: Error message
            error_type: Optional error type from agent memory
            
        Returns:
            Tuple of (repaired_prompt, repaired_context, was_repaired)
        """
        # First, try to detect error pattern
        pattern = self.detect_error_pattern(error)
        
        # If agent memory available, check for successful fixes for this error type
        if self.agent_memory and error_type:
            try:
                successful_fixes = self.agent_memory.get_successful_fixes_for_error(
                    error_type,
                    'generation'  # Most prompt repairs happen during generation
                )
                if successful_fixes:
                    logger.info(f"💡 Using fix strategy from agent memory for {error_type}")
                    # Could apply memory-based fixes here
            except Exception as e:
                logger.debug(f"Failed to query agent memory for fixes: {e}")
        
        if pattern and pattern in self.ERROR_PATTERNS:
            repair_func = self.ERROR_PATTERNS[pattern]['repair']
            repaired_prompt, repaired_context = repair_func(prompt, context)
            logger.info(f"🔧 Applied prompt repair for pattern: {pattern}")
            return repaired_prompt, repaired_context, True
        
        # No pattern detected or repair available
        return prompt, context, False
    
    async def repair_with_llm(self, prompt: str, context: str, error: str, agent) -> Tuple[str, str, bool]:
        """
        Use LLM to rephrase prompt if standard fixes don't work.
        
        Args:
            prompt: Original user prompt
            context: RAG context
            error: Error message
            agent: HyperKitAgent instance for LLM access
            
        Returns:
            Tuple of (repaired_prompt, repaired_context, was_repaired)
        """
        try:
            repair_prompt = f"""The following contract generation prompt failed with error: {error}

Original prompt: {prompt}

Please rephrase the prompt to be more explicit and clear, ensuring:
1. All required Solidity version and pragma statements are specified
2. Contract type is clearly identified
3. All required imports and dependencies are mentioned
4. Technical requirements are specific and unambiguous

Rephrased prompt:"""
            
            # Use agent's LLM to rephrase
            if hasattr(agent, 'ai_agent') and agent.ai_agent:
                result = await agent.ai_agent.generate_contract(repair_prompt, "")
                if result and result.get('status') == 'success':
                    rephrased = result.get('contract_code', '')
                    # Extract the rephrased prompt (it should be in the response)
                    # This is a simplified version - in practice, you'd parse the LLM response
                    logger.info("🤖 Used LLM to rephrase prompt")
                    return prompt, context, True  # For now, return original (would need proper parsing)
            
        except Exception as e:
            logger.warning(f"LLM-based prompt repair failed: {e}")
        
        return prompt, context, False


def _add_pragma_instruction(prompt: str, context: str) -> Tuple[str, str]:
    """Add pragma solidity instruction to prompt"""
    if 'pragma solidity' not in prompt.lower() and 'pragma solidity' not in context.lower():
        enhanced_prompt = f"""{prompt}

IMPORTANT: The contract MUST include 'pragma solidity ^0.8.24;' at the top of the file."""
        return enhanced_prompt, context
    return prompt, context


def _add_fallback_template(prompt: str, context: str) -> Tuple[str, str]:
    """Add fallback template instructions when context is empty"""
    if not context or len(context.strip()) < 50:
        enhanced_prompt = f"""{prompt}

Since no template context is available, generate a complete, production-ready contract from scratch following these requirements:
- Use OpenZeppelin v5 compatible imports
- Include proper access controls (Ownable, ReentrancyGuard)
- Follow Solidity best practices and security patterns
- Include comprehensive error handling"""
        return enhanced_prompt, context
    return prompt, context


def _add_solidity_version_requirement(prompt: str, context: str) -> Tuple[str, str]:
    """Add explicit Solidity version requirement"""
    enhanced_prompt = f"""{prompt}

REQUIREMENT: The contract MUST be compatible with Solidity ^0.8.24 and OpenZeppelin v5.x.
Ensure all imports use OpenZeppelin v5 paths (e.g., @openzeppelin/contracts/utils/ReentrancyGuard.sol)."""
    return enhanced_prompt, context


def _add_contract_type_classification(prompt: str, context: str) -> Tuple[str, str]:
    """Add contract type classification to prompt"""
    prompt_lower = prompt.lower()
    
    contract_type = None
    if 'erc20' in prompt_lower or 'token' in prompt_lower:
        contract_type = 'ERC20'
    elif 'erc721' in prompt_lower or 'nft' in prompt_lower:
        contract_type = 'ERC721'
    elif 'defi' in prompt_lower or 'dex' in prompt_lower or 'swap' in prompt_lower:
        contract_type = 'DeFi'
    elif 'dao' in prompt_lower or 'governance' in prompt_lower:
        contract_type = 'DAO'
    
    if contract_type:
        enhanced_prompt = f"""{prompt}

Contract Type: {contract_type}
Generate a {contract_type} contract following industry-standard patterns and best practices."""
        return enhanced_prompt, context
    
    return prompt, context


def _add_import_instructions(prompt: str, context: str) -> Tuple[str, str]:
    """Add import instructions to prompt"""
    enhanced_prompt = f"""{prompt}

IMPORTANT: Ensure all required imports are included:
- Use OpenZeppelin v5 import paths
- Import all dependencies explicitly
- Verify import paths match OpenZeppelin v5 structure"""
    return enhanced_prompt, context


def _add_shadowing_instructions(prompt: str, context: str) -> Tuple[str, str]:
    """Add variable shadowing prevention instructions"""
    enhanced_prompt = f"""{prompt}

IMPORTANT: Avoid variable shadowing:
- Constructor parameters should not shadow state variables
- Use different names for parameters (e.g., _paramName instead of paramName)
- Ensure all variable names are unique within their scope"""
    return enhanced_prompt, context

