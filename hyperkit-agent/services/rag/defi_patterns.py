"""
DeFi Pattern Knowledge Base for Enhanced RAG
Contains specialized DeFi patterns, security best practices, and common implementations
"""

from typing import Dict, List, Any
import json

class DeFiPatterns:
    """DeFi pattern knowledge base for enhanced RAG context"""
    
    def __init__(self):
        self.patterns = self._load_defi_patterns()
    
    def _load_defi_patterns(self) -> Dict[str, Any]:
        """Load DeFi patterns and best practices"""
        return {
            "erc20_patterns": {
                "basic_erc20": {
                    "description": "Basic ERC20 token implementation with standard functions",
                    "security_notes": [
                        "Use OpenZeppelin's ERC20 contract as base",
                        "Implement proper access controls",
                        "Use SafeMath for arithmetic operations (Solidity 0.8+)",
                        "Include pause functionality for emergency stops"
                    ],
                    "common_functions": [
                        "transfer(address to, uint256 amount)",
                        "approve(address spender, uint256 amount)",
                        "transferFrom(address from, address to, uint256 amount)",
                        "mint(address to, uint256 amount) - owner only",
                        "burn(uint256 amount) - user can burn own tokens"
                    ]
                },
                "advanced_erc20": {
                    "description": "Advanced ERC20 with additional features",
                    "features": [
                        "Minting and burning capabilities",
                        "Pausable functionality",
                        "Access control with roles",
                        "Snapshot functionality for governance",
                        "Vesting schedules"
                    ],
                    "security_considerations": [
                        "Implement reentrancy guards",
                        "Use checks-effects-interactions pattern",
                        "Validate all inputs",
                        "Implement proper event logging"
                    ]
                }
            },
            "defi_protocols": {
                "amm": {
                    "description": "Automated Market Maker (AMM) patterns",
                    "common_implementations": [
                        "Constant Product Market Maker (x * y = k)",
                        "StableSwap for stablecoin pairs",
                        "Weighted pools with different token weights"
                    ],
                    "security_patterns": [
                        "Reentrancy protection on all external calls",
                        "Slippage protection",
                        "Deadline validation",
                        "Liquidity lock mechanisms"
                    ]
                },
                "lending": {
                    "description": "Lending protocol patterns",
                    "core_functions": [
                        "supply(address asset, uint256 amount)",
                        "borrow(address asset, uint256 amount)",
                        "repay(address asset, uint256 amount)",
                        "withdraw(address asset, uint256 amount)"
                    ],
                    "risk_management": [
                        "Collateral factor validation",
                        "Liquidation thresholds",
                        "Interest rate models",
                        "Health factor calculations"
                    ]
                },
                "staking": {
                    "description": "Staking and yield farming patterns",
                    "features": [
                        "Deposit and withdrawal functions",
                        "Reward calculation and distribution",
                        "Lock period mechanisms",
                        "Compound interest calculations"
                    ],
                    "security_considerations": [
                        "Prevent double-spending",
                        "Secure reward distribution",
                        "Time-based access controls",
                        "Emergency withdrawal mechanisms"
                    ]
                }
            },
            "security_patterns": {
                "access_control": {
                    "description": "Access control patterns for DeFi protocols",
                    "implementations": [
                        "Ownable pattern for single owner",
                        "Role-based access control (RBAC)",
                        "Multi-signature requirements",
                        "Time-locked operations"
                    ],
                    "best_practices": [
                        "Use OpenZeppelin's AccessControl",
                        "Implement role hierarchies",
                        "Regular access reviews",
                        "Emergency pause functionality"
                    ]
                },
                "reentrancy_protection": {
                    "description": "Reentrancy attack prevention",
                    "patterns": [
                        "Checks-Effects-Interactions pattern",
                        "ReentrancyGuard modifier",
                        "State variable updates before external calls",
                        "Pull payment pattern for withdrawals"
                    ]
                },
                "integer_overflow": {
                    "description": "Integer overflow/underflow protection",
                    "solutions": [
                        "Use SafeMath library (Solidity < 0.8)",
                        "Solidity 0.8+ built-in overflow protection",
                        "Explicit bounds checking",
                        "Use uint256 for large calculations"
                    ]
                }
            },
            "gas_optimization": {
                "description": "Gas optimization techniques",
                "techniques": [
                    "Pack structs efficiently",
                    "Use events instead of storage for logs",
                    "Batch operations when possible",
                    "Use assembly for critical functions",
                    "Optimize loop operations"
                ],
                "common_patterns": [
                    "Use immutable for constants",
                    "Cache storage reads",
                    "Use calldata instead of memory when possible",
                    "Minimize external calls"
                ]
            },
            "testing_patterns": {
                "description": "Testing patterns for DeFi contracts",
                "test_categories": [
                    "Unit tests for individual functions",
                    "Integration tests for protocol interactions",
                    "Fuzz testing for edge cases",
                    "Formal verification for critical functions"
                ],
                "common_test_scenarios": [
                    "Normal operation flows",
                    "Edge cases and boundary conditions",
                    "Attack scenarios and mitigations",
                    "Upgrade and migration testing"
                ]
            }
        }
    
    def get_patterns_for_query(self, query: str) -> str:
        """Get relevant DeFi patterns for a given query"""
        query_lower = query.lower()
        relevant_patterns = []
        
        # Match query to pattern categories
        if any(keyword in query_lower for keyword in ['erc20', 'token', 'fungible']):
            relevant_patterns.append(self._format_pattern("ERC20 Patterns", self.patterns["erc20_patterns"]))
        
        if any(keyword in query_lower for keyword in ['amm', 'swap', 'liquidity', 'pool']):
            relevant_patterns.append(self._format_pattern("AMM Patterns", self.patterns["defi_protocols"]["amm"]))
        
        if any(keyword in query_lower for keyword in ['lending', 'borrow', 'supply', 'collateral']):
            relevant_patterns.append(self._format_pattern("Lending Patterns", self.patterns["defi_protocols"]["lending"]))
        
        if any(keyword in query_lower for keyword in ['staking', 'yield', 'farm', 'reward']):
            relevant_patterns.append(self._format_pattern("Staking Patterns", self.patterns["defi_protocols"]["staking"]))
        
        if any(keyword in query_lower for keyword in ['security', 'safe', 'audit', 'vulnerability']):
            relevant_patterns.append(self._format_pattern("Security Patterns", self.patterns["security_patterns"]))
        
        if any(keyword in query_lower for keyword in ['gas', 'optimize', 'efficient', 'cost']):
            relevant_patterns.append(self._format_pattern("Gas Optimization", self.patterns["gas_optimization"]))
        
        if any(keyword in query_lower for keyword in ['test', 'testing', 'verify', 'validation']):
            relevant_patterns.append(self._format_pattern("Testing Patterns", self.patterns["testing_patterns"]))
        
        return "\n\n".join(relevant_patterns) if relevant_patterns else ""
    
    def _format_pattern(self, title: str, pattern_data: Dict[str, Any]) -> str:
        """Format pattern data for RAG context"""
        formatted = f"# {title}\n\n"
        
        if isinstance(pattern_data, dict):
            for key, value in pattern_data.items():
                if isinstance(value, list):
                    formatted += f"**{key.replace('_', ' ').title()}:**\n"
                    for item in value:
                        formatted += f"- {item}\n"
                    formatted += "\n"
                elif isinstance(value, str):
                    formatted += f"**{key.replace('_', ' ').title()}:** {value}\n\n"
                elif isinstance(value, dict):
                    formatted += f"**{key.replace('_', ' ').title()}:**\n"
                    for sub_key, sub_value in value.items():
                        if isinstance(sub_value, list):
                            formatted += f"  - {sub_key.replace('_', ' ').title()}: {', '.join(sub_value)}\n"
                        else:
                            formatted += f"  - {sub_key.replace('_', ' ').title()}: {sub_value}\n"
                    formatted += "\n"
        
        return formatted
    
    def get_all_patterns(self) -> str:
        """Get all DeFi patterns for comprehensive context"""
        all_patterns = []
        for category, patterns in self.patterns.items():
            all_patterns.append(self._format_pattern(category.replace('_', ' ').title(), patterns))
        return "\n\n".join(all_patterns)

# Global instance for easy access
defi_patterns = DeFiPatterns()

