"""
Smart contract naming based on prompt analysis
"""

import re
from typing import Tuple
import logging

logger = logging.getLogger(__name__)

class ContractNamer:
    """Generate meaningful contract names from prompts"""
    
    # Keyword mappings
    KEYWORDS_MAP = {
        # Token types
        'erc20': 'Token',
        'erc721': 'NFT',
        'erc1155': 'MultiToken',
        'token': 'Token',
        'staking': 'Staking',
        'vault': 'Vault',
        'pool': 'Pool',
        'swap': 'Swap',
        'dex': 'DEX',
        'amm': 'AMM',
        
        # Features
        'gaming': 'Gaming',
        'game': 'Game',
        'p2e': 'P2E',
        'bridge': 'Bridge',
        'dao': 'DAO',
        'governance': 'Governance',
        'presale': 'Presale',
        'ico': 'ICO',
        'nft': 'NFT',
        'marketplace': 'Marketplace',
        'yield': 'Yield',
        'farm': 'Farm',
        'liquidity': 'Liquidity',
        'lp': 'LiquidityPool',
        
        # Mechanics
        'burn': 'Burn',
        'mint': 'Mint',
        'reward': 'Reward',
        'incentive': 'Incentive',
        'lock': 'Lock',
        'vesting': 'Vesting',
        'escrow': 'Escrow',
        'multisig': 'MultiSig',
    }
    
    def extract_contract_name(self, prompt: str) -> Tuple[str, str]:
        """
        Extract contract name and category from prompt
        
        Returns:
            Tuple[contract_name, category]
        """
        # FIRST: Look for explicitly quoted names (e.g., 'HyperMarket', "NFTMarket")
        quoted_names = re.findall(r"['\"]([A-Z][a-zA-Z0-9_]+)['\"]", prompt)
        if quoted_names:
            contract_name = quoted_names[0]  # Use first quoted name
            category = self._infer_category(prompt)
            return contract_name, category
        
        # SECOND: Look for contract name patterns like "contract 'Name'" or "contract Name"
        explicit_patterns = [
            r"contract\s+['\"]?([A-Z][a-zA-Z0-9_]+)['\"]?",
            r"build.*['\"]?([A-Z][a-zA-Z0-9_]+)['\"]?",
            r"create.*['\"]?([A-Z][a-zA-Z0-9_]+)['\"]?",
            r"name\s*[:=]\s*['\"]?([A-Z][a-zA-Z0-9_]+)['\"]?",
        ]
        
        for pattern in explicit_patterns:
            match = re.search(pattern, prompt, re.IGNORECASE)
            if match:
                contract_name = match.group(1)
                category = self._infer_category(prompt)
                return contract_name, category
        
        # Lowercase for matching
        prompt_lower = prompt.lower()
        
        # Priority keywords (checked third)
        priority_keywords = [
            'gaming token', 'play-to-earn', 'p2e token',
            'nft marketplace', 'nft contract',
            'dex', 'amm', 'liquidity pool',
            'staking', 'yield farm',
            'presale', 'ico',
            'dao', 'governance',
            'token bridge', 'cross-chain',
        ]
        
        # Check priority keywords
        for keyword in priority_keywords:
            if keyword in prompt_lower:
                # Extract tokens from the keyword
                tokens = [self.KEYWORDS_MAP.get(word, word.capitalize()) 
                         for word in keyword.split() 
                         if word in self.KEYWORDS_MAP]
                if tokens:
                    contract_name = ''.join(tokens)
                    return contract_name, keyword
        
        # Extract tokens mentioned in prompt
        found_keywords = []
        for keyword, mapped_name in self.KEYWORDS_MAP.items():
            if keyword in prompt_lower:
                found_keywords.append(mapped_name)
        
        if found_keywords:
            # Remove duplicates while preserving order
            unique_keywords = []
            for kw in found_keywords:
                if kw not in unique_keywords:
                    unique_keywords.append(kw)
            
            contract_name = ''.join(unique_keywords[:3])  # Max 3 keywords
            category = ' + '.join(unique_keywords)
            return contract_name, category
        
        # Fallback: extract tokens from prompt (capitalized words)
        tokens = re.findall(r'\b([A-Z][a-z]+)\b', prompt)
        if tokens:
            contract_name = ''.join(tokens[:3])
            return contract_name, ' '.join(tokens[:2])
        
        # Last resort: use timestamp-based name
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"Contract_{timestamp}", "generated"
    
    def _infer_category(self, prompt: str) -> str:
        """Infer category from prompt content"""
        prompt_lower = prompt.lower()
        
        if any(word in prompt_lower for word in ['nft', 'erc721', 'erc1155', 'marketplace']):
            return "nft"
        elif any(word in prompt_lower for word in ['gaming', 'game', 'p2e', 'play-to-earn']):
            return "gaming"
        elif any(word in prompt_lower for word in ['dao', 'governance', 'voting']):
            return "governance"
        elif any(word in prompt_lower for word in ['bridge', 'cross-chain', 'multichain']):
            return "bridge"
        elif any(word in prompt_lower for word in ['dex', 'amm', 'swap', 'liquidity', 'pool']):
            return "defi"
        elif any(word in prompt_lower for word in ['staking', 'yield', 'farm', 'vault']):
            return "defi"
        elif any(word in prompt_lower for word in ['presale', 'ico', 'ido']):
            return "launchpad"
        elif any(word in prompt_lower for word in ['erc20', 'token']):
            return "tokens"
        else:
            return "other"
    
    def generate_filename(self, prompt: str) -> str:
        """
        Generate full filename with extension
        
        Example:
            "Create gaming token" → "GamingToken.sol"
        """
        contract_name, category = self.extract_contract_name(prompt)
        
        # Sanitize: remove special chars
        safe_name = re.sub(r'[^A-Za-z0-9_]', '', contract_name)
        
        # Ensure CamelCase
        if safe_name:
            safe_name = safe_name[0].upper() + safe_name[1:]
        else:
            safe_name = "Contract"
        
        return f"{safe_name}.sol"
    
    def get_category(self, prompt: str) -> str:
        """
        Get contract category for directory organization
        
        Returns:
            Category like: "tokens", "defi", "nft", "governance"
        """
        return self._infer_category(prompt)
    
    def _infer_category_from_code(self, code: str) -> str:
        """Infer category from contract code content"""
        code_lower = code.lower()
        
        # Check for NFT patterns
        if any(pattern in code_lower for pattern in ['erc721', 'erc1155', 'nft', 'marketplace', 'nonfungible']):
            return "nft"
        # Check for gaming patterns
        elif any(pattern in code_lower for pattern in ['gaming', 'game', 'p2e', 'play', 'player']):
            return "gaming"
        # Check for governance patterns
        elif any(pattern in code_lower for pattern in ['dao', 'governance', 'voting', 'proposal']):
            return "governance"
        # Check for bridge patterns
        elif any(pattern in code_lower for pattern in ['bridge', 'crosschain', 'multichain', 'chain']):
            return "bridge"
        # Check for DeFi patterns
        elif any(pattern in code_lower for pattern in ['dex', 'amm', 'swap', 'liquidity', 'pool', 'staking', 'yield', 'farm', 'vault']):
            return "defi"
        # Check for launchpad patterns
        elif any(pattern in code_lower for pattern in ['presale', 'ico', 'ido', 'launchpad']):
            return "launchpad"
        # Check for token patterns (but not other categories)
        elif any(pattern in code_lower for pattern in ['erc20', 'token', 'mint', 'burn']):
            return "tokens"
        else:
            return "other"