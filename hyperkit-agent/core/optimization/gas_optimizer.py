"""
Gas Optimization Service
Provides gas optimization recommendations and utilities for smart contracts
"""

import re
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class GasOptimization:
    """Gas optimization recommendation"""

    type: str
    description: str
    impact: str  # 'high', 'medium', 'low'
    savings: str  # Estimated gas savings
    code_snippet: str
    recommendation: str


class GasOptimizer:
    """
    Gas optimization analyzer and recommender for Solidity contracts
    """

    def __init__(self):
        self.optimizations = []
        self.patterns = self._initialize_patterns()

    def _initialize_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Initialize gas optimization patterns"""
        return {
            "storage_optimization": {
                "pack_structs": {
                    "pattern": r"struct\s+\w+\s*\{[^}]*\}",
                    "description": "Pack struct variables to use fewer storage slots",
                    "impact": "high",
                    "savings": "2000-5000 gas per struct",
                },
                "use_uint256": {
                    "pattern": r"uint(8|16|32|64|128)\s+",
                    "description": "Use uint256 instead of smaller uint types for storage",
                    "impact": "medium",
                    "savings": "2000 gas per variable",
                },
                "pack_variables": {
                    "pattern": r"(uint256|uint128|uint64|uint32|uint16|uint8)\s+\w+;",
                    "description": "Pack multiple small variables in single storage slot",
                    "impact": "high",
                    "savings": "2000 gas per packed slot",
                },
            },
            "memory_optimization": {
                "use_calldata": {
                    "pattern": r"function\s+\w+\([^)]*memory\s+[^)]*\)",
                    "description": "Use calldata instead of memory for read-only parameters",
                    "impact": "medium",
                    "savings": "100-500 gas per parameter",
                },
                "avoid_memory_copy": {
                    "pattern": r"string\s+memory\s+\w+",
                    "description": "Use calldata for string parameters when possible",
                    "impact": "low",
                    "savings": "50-200 gas per string",
                },
            },
            "loop_optimization": {
                "cache_array_length": {
                    "pattern": r"for\s*\([^;]*;\s*\w+\.length[^;]*;",
                    "description": "Cache array length in loop condition",
                    "impact": "medium",
                    "savings": "100-300 gas per iteration",
                },
                "unchecked_arithmetic": {
                    "pattern": r"for\s*\([^;]*;\s*\w+\s*\+\+\s*[^;]*;",
                    "description": "Use unchecked arithmetic for loop counters",
                    "impact": "low",
                    "savings": "20-50 gas per iteration",
                },
            },
            "function_optimization": {
                "external_functions": {
                    "pattern": r"function\s+\w+\([^)]*\)\s+public\s+",
                    "description": "Use external instead of public for functions not called internally",
                    "impact": "medium",
                    "savings": "100-200 gas per call",
                },
                "view_pure_functions": {
                    "pattern": r"function\s+\w+\([^)]*\)\s+public\s+(?!view|pure)",
                    "description": "Add view or pure modifiers when appropriate",
                    "impact": "low",
                    "savings": "50-100 gas per call",
                },
            },
            "string_optimization": {
                "use_bytes32": {
                    "pattern": r"string\s+(public\s+)?\w+",
                    "description": "Use bytes32 instead of string for short fixed-length data",
                    "impact": "high",
                    "savings": "2000-5000 gas per variable",
                },
                "avoid_string_concat": {
                    "pattern": r"string\.concat\(",
                    "description": "Use assembly for string concatenation when possible",
                    "impact": "medium",
                    "savings": "500-1000 gas per concatenation",
                },
            },
            "event_optimization": {
                "indexed_parameters": {
                    "pattern": r"event\s+\w+\([^)]*\)",
                    "description": "Use indexed parameters for frequently filtered events",
                    "impact": "low",
                    "savings": "100-300 gas per event",
                }
            },
        }

    def analyze_contract(self, contract_code: str) -> List[GasOptimization]:
        """
        Analyze contract for gas optimization opportunities

        Args:
            contract_code: Solidity contract code

        Returns:
            List of gas optimization recommendations
        """
        logger.info("Starting gas optimization analysis")

        optimizations = []

        for category, patterns in self.patterns.items():
            for pattern_name, pattern_info in patterns.items():
                matches = re.finditer(
                    pattern_info["pattern"], contract_code, re.MULTILINE | re.DOTALL
                )

                for match in matches:
                    optimization = GasOptimization(
                        type=f"{category}_{pattern_name}",
                        description=pattern_info["description"],
                        impact=pattern_info["impact"],
                        savings=pattern_info["savings"],
                        code_snippet=match.group(0),
                        recommendation=self._generate_recommendation(
                            category, pattern_name, match.group(0)
                        ),
                    )
                    optimizations.append(optimization)

        # Add custom optimizations
        custom_optimizations = self._analyze_custom_patterns(contract_code)
        optimizations.extend(custom_optimizations)

        logger.info(f"Found {len(optimizations)} gas optimization opportunities")
        return optimizations

    def _analyze_custom_patterns(self, contract_code: str) -> List[GasOptimization]:
        """Analyze custom gas optimization patterns"""
        optimizations = []

        # Check for expensive operations
        expensive_patterns = [
            {
                "pattern": r"\.transfer\(",
                "description": "Use call instead of transfer for gas efficiency",
                "impact": "high",
                "savings": "2300 gas per transfer",
            },
            {
                "pattern": r"\.send\(",
                "description": "Use call instead of send for gas efficiency",
                "impact": "high",
                "savings": "2300 gas per send",
            },
            {
                "pattern": r'require\s*\(\s*[^,]+,\s*"[^"]*"\s*\)',
                "description": "Use custom errors instead of require with strings",
                "impact": "medium",
                "savings": "1000-2000 gas per require",
            },
            {
                "pattern": r"keccak256\s*\(\s*abi\.encodePacked\s*\(",
                "description": "Use abi.encode instead of abi.encodePacked for security",
                "impact": "low",
                "savings": "100-300 gas per hash",
            },
        ]

        for pattern_info in expensive_patterns:
            matches = re.finditer(pattern_info["pattern"], contract_code)
            for match in matches:
                optimization = GasOptimization(
                    type=f"custom_{pattern_info['pattern'].replace('\\', '').replace('(', '').replace(')', '')}",
                    description=pattern_info["description"],
                    impact=pattern_info["impact"],
                    savings=pattern_info["savings"],
                    code_snippet=match.group(0),
                    recommendation=self._generate_custom_recommendation(
                        pattern_info, match.group(0)
                    ),
                )
                optimizations.append(optimization)

        return optimizations

    def _generate_recommendation(
        self, category: str, pattern_name: str, code_snippet: str
    ) -> str:
        """Generate specific recommendation for a pattern"""
        recommendations = {
            "pack_structs": f"Pack struct variables in the following order: uint256, uint128, uint64, uint32, uint16, uint8, bool, address. Current code: {code_snippet}",
            "use_uint256": f"Consider using uint256 instead of smaller uint types for storage variables. Current code: {code_snippet}",
            "pack_variables": f"Pack multiple small variables in a single storage slot. Current code: {code_snippet}",
            "use_calldata": f"Use calldata instead of memory for read-only parameters. Current code: {code_snippet}",
            "cache_array_length": f"Cache array length before the loop. Current code: {code_snippet}",
            "unchecked_arithmetic": f"Use unchecked arithmetic for loop counters. Current code: {code_snippet}",
            "external_functions": f"Use external instead of public for functions not called internally. Current code: {code_snippet}",
            "use_bytes32": f"Use bytes32 instead of string for short fixed-length data. Current code: {code_snippet}",
            "indexed_parameters": f"Add indexed keyword to frequently filtered event parameters. Current code: {code_snippet}",
        }

        return recommendations.get(pattern_name, f"Consider optimizing: {code_snippet}")

    def _generate_custom_recommendation(
        self, pattern_info: Dict[str, Any], code_snippet: str
    ) -> str:
        """Generate custom recommendation"""
        if "transfer" in pattern_info["pattern"]:
            return f"Replace {code_snippet} with: (bool success, ) = recipient.call{{value: amount}}(''); require(success, 'Transfer failed');"
        elif "send" in pattern_info["pattern"]:
            return f"Replace {code_snippet} with: (bool success, ) = recipient.call{{value: amount}}(''); require(success, 'Send failed');"
        elif "require" in pattern_info["pattern"]:
            return f"Define custom error and use: if (!condition) revert CustomError(); instead of {code_snippet}"
        elif "keccak256" in pattern_info["pattern"]:
            return f"Use abi.encode instead of abi.encodePacked for better security: {code_snippet.replace('abi.encodePacked', 'abi.encode')}"

        return f"Consider optimizing: {code_snippet}"

    def generate_optimized_code(
        self, contract_code: str, optimizations: List[GasOptimization]
    ) -> str:
        """
        Generate optimized version of the contract

        Args:
            contract_code: Original contract code
            optimizations: List of optimizations to apply

        Returns:
            Optimized contract code
        """
        optimized_code = contract_code

        # Apply high-impact optimizations first
        high_impact_optimizations = [
            opt for opt in optimizations if opt.impact == "high"
        ]

        for optimization in high_impact_optimizations:
            optimized_code = self._apply_optimization(optimized_code, optimization)

        return optimized_code

    def _apply_optimization(self, code: str, optimization: GasOptimization) -> str:
        """Apply a specific optimization to the code"""
        if "pack_structs" in optimization.type:
            return self._optimize_struct_packing(code)
        elif "use_calldata" in optimization.type:
            return self._optimize_calldata_usage(code)
        elif "cache_array_length" in optimization.type:
            return self._optimize_loop_length_caching(code)
        elif "external_functions" in optimization.type:
            return self._optimize_function_visibility(code)

        return code

    def _optimize_struct_packing(self, code: str) -> str:
        """Optimize struct packing"""
        # This is a simplified example - in practice, you'd need more sophisticated analysis
        return code

    def _optimize_calldata_usage(self, code: str) -> str:
        """Optimize calldata usage"""
        # Replace memory with calldata for read-only parameters
        code = re.sub(r"(\w+)\s+memory\s+(\w+)(?=\s*[,\)])", r"\1 calldata \2", code)
        return code

    def _optimize_loop_length_caching(self, code: str) -> str:
        """Optimize loop length caching"""
        # This would require more sophisticated AST analysis
        return code

    def _optimize_function_visibility(self, code: str) -> str:
        """Optimize function visibility"""
        # Replace public with external where appropriate
        # This is a simplified example
        return code

    def estimate_gas_savings(
        self, optimizations: List[GasOptimization]
    ) -> Dict[str, Any]:
        """
        Estimate total gas savings from optimizations

        Args:
            optimizations: List of optimizations

        Returns:
            Dictionary with gas savings estimates
        """
        total_savings = 0
        savings_by_impact = {"high": 0, "medium": 0, "low": 0}

        for optimization in optimizations:
            # Extract numeric value from savings string
            savings_match = re.search(r"(\d+)", optimization.savings)
            if savings_match:
                savings = int(savings_match.group(1))
                total_savings += savings
                savings_by_impact[optimization.impact] += savings

        return {
            "total_savings": total_savings,
            "savings_by_impact": savings_by_impact,
            "optimization_count": len(optimizations),
            "high_impact_count": len(
                [opt for opt in optimizations if opt.impact == "high"]
            ),
            "medium_impact_count": len(
                [opt for opt in optimizations if opt.impact == "medium"]
            ),
            "low_impact_count": len(
                [opt for opt in optimizations if opt.impact == "low"]
            ),
        }

    def generate_report(self, optimizations: List[GasOptimization]) -> str:
        """
        Generate a gas optimization report

        Args:
            optimizations: List of optimizations

        Returns:
            Formatted report string
        """
        if not optimizations:
            return "No gas optimization opportunities found."

        report = "# Gas Optimization Report\n\n"

        # Summary
        savings_estimate = self.estimate_gas_savings(optimizations)
        report += f"## Summary\n"
        report += (
            f"- Total optimizations found: {savings_estimate['optimization_count']}\n"
        )
        report += f"- Estimated gas savings: {savings_estimate['total_savings']} gas\n"
        report += f"- High impact: {savings_estimate['high_impact_count']}\n"
        report += f"- Medium impact: {savings_estimate['medium_impact_count']}\n"
        report += f"- Low impact: {savings_estimate['low_impact_count']}\n\n"

        # Group by impact
        for impact in ["high", "medium", "low"]:
            impact_optimizations = [
                opt for opt in optimizations if opt.impact == impact
            ]
            if impact_optimizations:
                report += f"## {impact.title()} Impact Optimizations\n\n"

                for i, optimization in enumerate(impact_optimizations, 1):
                    report += f"### {i}. {optimization.description}\n"
                    report += f"**Type:** {optimization.type}\n"
                    report += f"**Savings:** {optimization.savings}\n"
                    report += (
                        f"**Code:**\n```solidity\n{optimization.code_snippet}\n```\n"
                    )
                    report += f"**Recommendation:** {optimization.recommendation}\n\n"

        return report
