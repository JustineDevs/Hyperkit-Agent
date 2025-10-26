"""
Robust Prompt Parser for Smart Contract Generation
Extracts token names, symbols, and features from natural language prompts
"""

import re
import logging
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class TokenSpec:
    """Token specification extracted from prompt"""
    name: str
    symbol: str
    decimals: int = 18
    max_supply: Optional[int] = None
    initial_supply: Optional[int] = None


@dataclass
class ContractSpec:
    """Contract specification extracted from prompt"""
    contract_name: str
    token_spec: Optional[TokenSpec] = None
    features: List[str] = None
    parameters: Dict[str, Any] = None


class PromptParser:
    """
    Robust parser for extracting contract specifications from natural language prompts.
    Handles various formats and ensures deterministic output.
    """
    
    def __init__(self):
        self.token_patterns = [
            # Direct token name patterns (more flexible) - ORDER MATTERS!
            r'\b([A-Z][A-Z0-9_]{1,15})\b',  # GAMEX, MYTOKEN (word boundary)
            r"'([A-Z][A-Z0-9_]{1,15})'",  # 'GAMEX', 'MYTOKEN'
            r'"([A-Z][A-Z0-9_]{1,15})"',  # "GAMEX", "MYTOKEN"
            
            # Token with explicit naming
            r'token\s+(?:name|symbol)?\s*[:\-=]\s*["\']?([A-Z][A-Z0-9_]{1,15})["\']?',
            r'symbol\s*[:\-=]\s*["\']?([A-Z][A-Z0-9_]{1,15})["\']?',
            r'name\s*[:\-=]\s*["\']?([A-Z][A-Z0-9_]{1,15})["\']?',
            
            # Contract name patterns
            r'contract\s+([A-Z][a-zA-Z0-9_]{1,20})',
            r'create\s+([A-Z][a-zA-Z0-9_]{1,20})',
            r'build\s+([A-Z][a-zA-Z0-9_]{1,20})',
        ]
        
        self.feature_patterns = {
            'mintable': [r'mint', r'mintable', r'can mint'],
            'burnable': [r'burn', r'burnable', r'can burn'],
            'pausable': [r'pause', r'pausable', r'emergency stop'],
            'governance': [r'governance', r'dao', r'voting', r'proposal'],
            'staking': [r'staking', r'stake', r'rewards'],
            'deflationary': [r'deflationary', r'burn.*%', r'tax'],
            'whale_protection': [r'whale', r'anti.*whale', r'max.*per.*wallet'],
            'vesting': [r'vesting', r'vest', r'lock.*period'],
        }
        
        self.parameter_patterns = {
            'max_supply': r'max.*supply.*?(\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:million|billion|k|m|b)?',
            'initial_supply': r'initial.*supply.*?(\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:million|billion|k|m|b)?',
            'decimals': r'(\d+)\s*decimals?',
            'apy': r'(\d+(?:\.\d+)?)\s*%?\s*apy',
            'fee': r'(\d+(?:\.\d+)?)\s*%?\s*fee',
            'lock_period': r'(\d+)\s*(?:day|week|month|year)s?\s*lock',
        }

    def parse_prompt(self, prompt: str) -> ContractSpec:
        """
        Parse a natural language prompt and extract contract specifications.
        
        Args:
            prompt: Natural language description of the contract
            
        Returns:
            ContractSpec with extracted information
        """
        try:
            # Extract token name/symbol
            token_spec = self._extract_token_spec(prompt)
            
            # Extract contract name
            contract_name = self._extract_contract_name(prompt, token_spec)
            
            # Extract features
            features = self._extract_features(prompt)
            
            # Extract parameters
            parameters = self._extract_parameters(prompt)
            
            logger.info(f"Parsed prompt: contract='{contract_name}', token='{token_spec.name if token_spec else 'None'}'")
            
            return ContractSpec(
                contract_name=contract_name,
                token_spec=token_spec,
                features=features,
                parameters=parameters
            )
            
        except Exception as e:
            logger.error(f"Prompt parsing failed: {e}")
            # Return safe defaults
            return ContractSpec(
                contract_name="GeneratedContract",
                token_spec=TokenSpec(name="GeneratedToken", symbol="GEN"),
                features=[],
                parameters={}
            )

    def _extract_token_spec(self, prompt: str) -> Optional[TokenSpec]:
        """Extract token name and symbol from prompt."""
        token_name = None
        token_symbol = None
        
        # Try to find token name/symbol using patterns
        for pattern in self.token_patterns:
            matches = re.findall(pattern, prompt, re.IGNORECASE)
            if matches:
                # Find the best candidate from all matches
                for match in matches:
                    candidate = match.upper()
                    if self._is_valid_token_symbol(candidate):
                        # Skip common words that aren't tokens
                        if candidate not in ['CREATE', 'BUILD', 'MAKE', 'GENERATE', 'TOKEN', 'CONTRACT', 'WITH', 'SUPPLY', 'BILLION']:
                            if not token_symbol:
                                token_symbol = candidate
                            if not token_name:
                                token_name = candidate
                            break
                if token_symbol:  # Found a valid token, stop looking
                    break
        
        # If no token found, try to extract from context
        if not token_symbol:
            # Look for "create X token" patterns
            create_pattern = r'create\s+([A-Z][a-zA-Z0-9_]{2,15})\s+token'
            matches = re.findall(create_pattern, prompt, re.IGNORECASE)
            if matches:
                token_name = matches[0]
                token_symbol = self._generate_symbol_from_name(token_name)
        
        if not token_symbol:
            return None
            
        # Extract additional token parameters
        decimals = self._extract_decimals(prompt)
        max_supply = self._extract_max_supply(prompt)
        initial_supply = self._extract_initial_supply(prompt)
        
        return TokenSpec(
            name=token_name or token_symbol,
            symbol=token_symbol,
            decimals=decimals,
            max_supply=max_supply,
            initial_supply=initial_supply
        )

    def _extract_contract_name(self, prompt: str, token_spec: Optional[TokenSpec]) -> str:
        """Extract contract name from prompt."""
        # If we have a token spec, use it as base
        if token_spec and token_spec.name:
            # Convert token name to contract name
            name = token_spec.name
            if not name.endswith('Token'):
                name = f"{name}Token"
            return name
        
        # Look for explicit contract names
        contract_patterns = [
            r'contract\s+([A-Z][a-zA-Z0-9_]{2,20})',
            r'create\s+([A-Z][a-zA-Z0-9_]{2,20})',
            r'build\s+([A-Z][a-zA-Z0-9_]{2,20})',
        ]
        
        for pattern in contract_patterns:
            matches = re.findall(pattern, prompt, re.IGNORECASE)
            if matches:
                return matches[0]
        
        # Default fallback
        return "GeneratedContract"

    def _extract_features(self, prompt: str) -> List[str]:
        """Extract contract features from prompt."""
        features = []
        prompt_lower = prompt.lower()
        
        for feature, patterns in self.feature_patterns.items():
            for pattern in patterns:
                if re.search(pattern, prompt_lower):
                    features.append(feature)
                    break
        
        return features

    def _extract_parameters(self, prompt: str) -> Dict[str, Any]:
        """Extract numerical parameters from prompt."""
        parameters = {}
        
        for param_name, pattern in self.parameter_patterns.items():
            matches = re.findall(pattern, prompt, re.IGNORECASE)
            if matches:
                try:
                    value = self._parse_number(matches[0])
                    parameters[param_name] = value
                except ValueError:
                    continue
        
        return parameters

    def _is_valid_token_symbol(self, symbol: str) -> bool:
        """Check if a string is a valid token symbol."""
        if not symbol or len(symbol) < 1 or len(symbol) > 15:
            return False
        
        # Must be uppercase letters and numbers
        if not re.match(r'^[A-Z0-9_]+$', symbol):
            return False
        
        # Must start with a letter
        if not symbol[0].isalpha():
            return False
        
        return True

    def _generate_symbol_from_name(self, name: str) -> str:
        """Generate a token symbol from a name."""
        # Remove common suffixes
        name = re.sub(r'(token|coin|currency)$', '', name, flags=re.IGNORECASE)
        
        # Take first 4 characters, uppercase
        symbol = name[:4].upper()
        
        # Ensure it's valid
        if not self._is_valid_token_symbol(symbol):
            symbol = "TOKEN"
        
        return symbol

    def _extract_decimals(self, prompt: str) -> int:
        """Extract decimals from prompt."""
        pattern = r'(\d+)\s*decimals?'
        matches = re.findall(pattern, prompt, re.IGNORECASE)
        if matches:
            try:
                return int(matches[0])
            except ValueError:
                pass
        return 18  # Default

    def _extract_max_supply(self, prompt: str) -> Optional[int]:
        """Extract max supply from prompt."""
        pattern = r'max.*supply.*?(\d+(?:,\d{3})*(?:\.\d+)?)\s*(million|billion|k|m|b)?'
        matches = re.findall(pattern, prompt, re.IGNORECASE)
        if matches:
            try:
                number, unit = matches[0]
                number = self._parse_number(number)
                multiplier = self._get_unit_multiplier(unit)
                return int(number * multiplier)
            except ValueError:
                pass
        return None

    def _extract_initial_supply(self, prompt: str) -> Optional[int]:
        """Extract initial supply from prompt."""
        pattern = r'initial.*supply.*?(\d+(?:,\d{3})*(?:\.\d+)?)\s*(million|billion|k|m|b)?'
        matches = re.findall(pattern, prompt, re.IGNORECASE)
        if matches:
            try:
                number, unit = matches[0]
                number = self._parse_number(number)
                multiplier = self._get_unit_multiplier(unit)
                return int(number * multiplier)
            except ValueError:
                pass
        return None

    def _parse_number(self, number_str: str) -> float:
        """Parse a number string with commas."""
        return float(number_str.replace(',', ''))

    def _get_unit_multiplier(self, unit: str) -> int:
        """Get multiplier for unit (k, m, b, etc.)."""
        if not unit:
            return 1
        
        unit = unit.lower()
        multipliers = {
            'k': 1000,
            'm': 1000000,
            'million': 1000000,
            'b': 1000000000,
            'billion': 1000000000,
        }
        return multipliers.get(unit, 1)

    def validate_and_fix_contract(self, contract_code: str, spec: ContractSpec) -> str:
        """
        Validate and fix contract code to match the specification.
        
        Args:
            contract_code: Generated contract code
            spec: Contract specification
            
        Returns:
            Fixed contract code
        """
        try:
            # Fix contract name
            if spec.contract_name:
                contract_code = self._fix_contract_name(contract_code, spec.contract_name)
            
            # Fix token name and symbol
            if spec.token_spec:
                contract_code = self._fix_token_spec(contract_code, spec.token_spec)
            
            logger.info(f"Contract validation and fixing completed")
            return contract_code
            
        except Exception as e:
            logger.error(f"Contract validation failed: {e}")
            return contract_code

    def _fix_contract_name(self, contract_code: str, contract_name: str) -> str:
        """Fix contract name in the code."""
        # Find contract declaration
        contract_pattern = r'contract\s+(\w+)'
        match = re.search(contract_pattern, contract_code)
        
        if match:
            old_name = match.group(1)
            # Replace contract name everywhere
            contract_code = contract_code.replace(f'contract {old_name}', f'contract {contract_name}')
            contract_code = contract_code.replace(f'{old_name}()', f'{contract_name}()')
            contract_code = contract_code.replace(f'{old_name}:', f'{contract_name}:')
            contract_code = contract_code.replace(f'@title {old_name}', f'@title {contract_name}')
        
        return contract_code

    def _fix_token_spec(self, contract_code: str, token_spec: TokenSpec) -> str:
        """Fix token name and symbol in the code."""
        # Fix ERC20 constructor calls - be more aggressive
        erc20_pattern = r'ERC20\("([^"]+)",\s*"([^"]+)"\)'
        
        def replace_erc20(match):
            return f'ERC20("{token_spec.name}", "{token_spec.symbol}")'
        
        contract_code = re.sub(erc20_pattern, replace_erc20, contract_code)
        
        # Fix ERC721 constructor calls
        erc721_pattern = r'ERC721\("([^"]+)",\s*"([^"]+)"\)'
        
        def replace_erc721(match):
            return f'ERC721("{token_spec.name}", "{token_spec.symbol}")'
        
        contract_code = re.sub(erc721_pattern, replace_erc721, contract_code)
        
        # Also fix any hardcoded token names in comments
        contract_code = contract_code.replace(f'named {token_spec.name}', f'named {token_spec.name}')
        
        return contract_code


# Example usage
def test_parser():
    """Test the prompt parser with various inputs."""
    parser = PromptParser()
    
    test_prompts = [
        "Create a GAMEX token with 1 billion supply",
        "Build a 'MYTOKEN' ERC20 with minting",
        "Generate a TestToken contract",
        "Create a staking contract for LINK token",
    ]
    
    for prompt in test_prompts:
        print(f"\nPrompt: {prompt}")
        spec = parser.parse_prompt(prompt)
        print(f"Contract: {spec.contract_name}")
        if spec.token_spec:
            print(f"Token: {spec.token_spec.name} ({spec.token_spec.symbol})")
        print(f"Features: {spec.features}")


if __name__ == "__main__":
    test_parser()
