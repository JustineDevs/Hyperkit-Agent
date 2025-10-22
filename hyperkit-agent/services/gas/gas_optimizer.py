"""
Gas Optimization Service for HyperKit AI Agent

This module provides comprehensive gas optimization analysis and recommendations
for Solidity smart contracts.
"""

import re
import json
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class GasOptimizer:
    """Advanced gas optimization analyzer for Solidity contracts."""
    
    def __init__(self):
        self.optimization_patterns = {
            'storage_optimization': {
                'pack_structs': r'struct\s+\w+\s*\{[^}]*\}',
                'optimize_arrays': r'(\w+)\[\d*\]\s+(public|private|internal)',
                'use_immutable': r'(\w+)\s+(public|private|internal)\s+constant',
                'pack_variables': r'(\w+)\s+(public|private|internal)\s+(\w+);'
            },
            'function_optimization': {
                'avoid_storage_reads': r'storage\s+\w+',
                'use_calldata': r'memory\s+\w+\[\]',
                'optimize_loops': r'for\s*\([^)]*\)\s*\{',
                'avoid_redundant_calls': r'(\w+)\([^)]*\)\s*;.*\1\([^)]*\)\s*;'
            },
            'memory_optimization': {
                'use_bytes32': r'string\s+(\w+)',
                'optimize_strings': r'string\s+(public|private|internal)',
                'use_fixed_arrays': r'(\w+)\[\]\s+(public|private|internal)'
            }
        }
        
        self.gas_costs = {
            'storage_slot': 20000,
            'storage_read': 200,
            'storage_write': 20000,
            'memory_allocation': 3,
            'calldata_read': 3,
            'function_call': 21,
            'sstore': 20000,
            'sload': 200,
            'mstore': 3,
            'mload': 3
        }
    
    def analyze_contract(self, contract_path: str) -> Dict[str, Any]:
        """
        Analyze a Solidity contract for gas optimization opportunities.
        
        Args:
            contract_path: Path to the Solidity contract file
            
        Returns:
            Dictionary containing optimization analysis results
        """
        try:
            with open(contract_path, 'r', encoding='utf-8') as f:
                contract_code = f.read()
            
            analysis = {
                'contract_path': contract_path,
                'optimization_opportunities': [],
                'gas_estimates': {},
                'recommendations': [],
                'score': 0
            }
            
            # Analyze storage optimization
            storage_analysis = self._analyze_storage_optimization(contract_code)
            analysis['optimization_opportunities'].extend(storage_analysis)
            
            # Analyze function optimization
            function_analysis = self._analyze_function_optimization(contract_code)
            analysis['optimization_opportunities'].extend(function_analysis)
            
            # Analyze memory optimization
            memory_analysis = self._analyze_memory_optimization(contract_code)
            analysis['optimization_opportunities'].extend(memory_analysis)
            
            # Generate recommendations
            analysis['recommendations'] = self._generate_recommendations(analysis['optimization_opportunities'])
            
            # Calculate optimization score
            analysis['score'] = self._calculate_optimization_score(analysis['optimization_opportunities'])
            
            # Estimate gas savings
            analysis['gas_estimates'] = self._estimate_gas_savings(analysis['optimization_opportunities'])
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing contract {contract_path}: {e}")
            return {
                'contract_path': contract_path,
                'error': str(e),
                'optimization_opportunities': [],
                'recommendations': [],
                'score': 0
            }
    
    def _analyze_storage_optimization(self, code: str) -> List[Dict[str, Any]]:
        """Analyze storage optimization opportunities."""
        opportunities = []
        
        # Check for struct packing opportunities
        struct_matches = re.finditer(self.optimization_patterns['storage_optimization']['pack_structs'], code, re.MULTILINE)
        for match in struct_matches:
            struct_code = match.group(0)
            if self._has_packing_opportunity(struct_code):
                opportunities.append({
                    'type': 'storage_packing',
                    'severity': 'high',
                    'description': 'Struct can be packed to save storage slots',
                    'location': match.span(),
                    'suggestion': 'Reorder struct fields to pack into fewer storage slots',
                    'gas_savings': 20000  # One storage slot
                })
        
        # Check for immutable variable opportunities
        immutable_matches = re.finditer(self.optimization_patterns['storage_optimization']['use_immutable'], code)
        for match in immutable_matches:
            opportunities.append({
                'type': 'immutable_variable',
                'severity': 'medium',
                'description': 'Variable can be made immutable',
                'location': match.span(),
                'suggestion': 'Use immutable keyword for variables set only once',
                'gas_savings': 20000
            })
        
        return opportunities
    
    def _analyze_function_optimization(self, code: str) -> List[Dict[str, Any]]:
        """Analyze function optimization opportunities."""
        opportunities = []
        
        # Check for calldata usage
        calldata_matches = re.finditer(self.optimization_patterns['function_optimization']['use_calldata'], code)
        for match in calldata_matches:
            opportunities.append({
                'type': 'calldata_usage',
                'severity': 'medium',
                'description': 'Use calldata instead of memory for read-only arrays',
                'location': match.span(),
                'suggestion': 'Replace memory with calldata for function parameters',
                'gas_savings': 1000
            })
        
        # Check for redundant function calls
        redundant_matches = re.finditer(self.optimization_patterns['function_optimization']['avoid_redundant_calls'], code, re.DOTALL)
        for match in redundant_matches:
            opportunities.append({
                'type': 'redundant_calls',
                'severity': 'low',
                'description': 'Potential redundant function calls detected',
                'location': match.span(),
                'suggestion': 'Cache function results to avoid redundant calls',
                'gas_savings': 500
            })
        
        return opportunities
    
    def _analyze_memory_optimization(self, code: str) -> List[Dict[str, Any]]:
        """Analyze memory optimization opportunities."""
        opportunities = []
        
        # Check for string optimization
        string_matches = re.finditer(self.optimization_patterns['memory_optimization']['use_bytes32'], code)
        for match in string_matches:
            opportunities.append({
                'type': 'string_optimization',
                'severity': 'medium',
                'description': 'Consider using bytes32 instead of string for short values',
                'location': match.span(),
                'suggestion': 'Use bytes32 for strings shorter than 32 characters',
                'gas_savings': 2000
            })
        
        return opportunities
    
    def _has_packing_opportunity(self, struct_code: str) -> bool:
        """Check if a struct has packing opportunities."""
        # Simple heuristic: check if struct has multiple small types that could be packed
        small_types = ['uint8', 'uint16', 'uint32', 'bool', 'address']
        type_count = sum(1 for t in small_types if t in struct_code)
        return type_count > 1
    
    def _generate_recommendations(self, opportunities: List[Dict[str, Any]]) -> List[str]:
        """Generate optimization recommendations based on opportunities."""
        recommendations = []
        
        high_priority = [op for op in opportunities if op['severity'] == 'high']
        medium_priority = [op for op in opportunities if op['severity'] == 'medium']
        low_priority = [op for op in opportunities if op['severity'] == 'low']
        
        if high_priority:
            recommendations.append(f"🚨 HIGH PRIORITY: {len(high_priority)} critical optimizations found")
            for op in high_priority:
                recommendations.append(f"  • {op['description']}: {op['suggestion']}")
        
        if medium_priority:
            recommendations.append(f"⚠️  MEDIUM PRIORITY: {len(medium_priority)} optimizations found")
            for op in medium_priority:
                recommendations.append(f"  • {op['description']}: {op['suggestion']}")
        
        if low_priority:
            recommendations.append(f"💡 LOW PRIORITY: {len(low_priority)} minor optimizations found")
            for op in low_priority:
                recommendations.append(f"  • {op['description']}: {op['suggestion']}")
        
        return recommendations
    
    def _calculate_optimization_score(self, opportunities: List[Dict[str, Any]]) -> int:
        """Calculate optimization score (0-100)."""
        if not opportunities:
            return 100
        
        high_count = len([op for op in opportunities if op['severity'] == 'high'])
        medium_count = len([op for op in opportunities if op['severity'] == 'medium'])
        low_count = len([op for op in opportunities if op['severity'] == 'low'])
        
        # Penalty system: high=10, medium=5, low=2
        penalty = (high_count * 10) + (medium_count * 5) + (low_count * 2)
        score = max(0, 100 - penalty)
        
        return score
    
    def _estimate_gas_savings(self, opportunities: List[Dict[str, Any]]) -> Dict[str, int]:
        """Estimate total gas savings from optimizations."""
        total_savings = sum(op.get('gas_savings', 0) for op in opportunities)
        
        return {
            'total_estimated_savings': total_savings,
            'deployment_savings': sum(op.get('gas_savings', 0) for op in opportunities if op['type'] == 'storage_packing'),
            'execution_savings': sum(op.get('gas_savings', 0) for op in opportunities if op['type'] != 'storage_packing'),
            'optimization_count': len(opportunities)
        }
    
    def generate_optimization_report(self, analysis: Dict[str, Any]) -> str:
        """Generate a human-readable optimization report."""
        report = []
        report.append("=" * 60)
        report.append("🔧 GAS OPTIMIZATION ANALYSIS REPORT")
        report.append("=" * 60)
        report.append(f"📁 Contract: {analysis['contract_path']}")
        report.append(f"📊 Optimization Score: {analysis['score']}/100")
        report.append("")
        
        # Gas estimates
        if 'gas_estimates' in analysis:
            gas_info = analysis['gas_estimates']
            report.append("⛽ GAS SAVINGS ESTIMATE:")
            report.append(f"  • Total Estimated Savings: {gas_info.get('total_estimated_savings', 0):,} gas")
            report.append(f"  • Deployment Savings: {gas_info.get('deployment_savings', 0):,} gas")
            report.append(f"  • Execution Savings: {gas_info.get('execution_savings', 0):,} gas")
            report.append(f"  • Optimization Opportunities: {gas_info.get('optimization_count', 0)}")
            report.append("")
        
        # Recommendations
        if analysis['recommendations']:
            report.append("🎯 OPTIMIZATION RECOMMENDATIONS:")
            for rec in analysis['recommendations']:
                report.append(f"  {rec}")
            report.append("")
        
        # Detailed opportunities
        if analysis['optimization_opportunities']:
            report.append("📋 DETAILED OPPORTUNITIES:")
            for i, op in enumerate(analysis['optimization_opportunities'], 1):
                report.append(f"  {i}. [{op['severity'].upper()}] {op['description']}")
                report.append(f"     💡 Suggestion: {op['suggestion']}")
                report.append(f"     ⛽ Gas Savings: {op.get('gas_savings', 0):,} gas")
                report.append("")
        
        report.append("=" * 60)
        return "\n".join(report)
    
    def export_report_json(self, analysis: Dict[str, Any], output_path: str) -> bool:
        """Export analysis results to JSON file."""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(analysis, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Error exporting report to {output_path}: {e}")
            return False
    
    def batch_analyze_contracts(self, contract_directory: str) -> Dict[str, Any]:
        """Analyze multiple contracts in a directory."""
        contract_dir = Path(contract_directory)
        if not contract_dir.exists():
            return {'error': f'Directory {contract_directory} does not exist'}
        
        results = {
            'directory': contract_directory,
            'contracts_analyzed': 0,
            'total_opportunities': 0,
            'average_score': 0,
            'contracts': []
        }
        
        total_score = 0
        total_opportunities = 0
        
        for contract_file in contract_dir.glob("*.sol"):
            analysis = self.analyze_contract(str(contract_file))
            results['contracts'].append(analysis)
            results['contracts_analyzed'] += 1
            
            if 'score' in analysis:
                total_score += analysis['score']
            
            if 'optimization_opportunities' in analysis:
                total_opportunities += len(analysis['optimization_opportunities'])
        
        if results['contracts_analyzed'] > 0:
            results['average_score'] = total_score / results['contracts_analyzed']
            results['total_opportunities'] = total_opportunities
        
        return results


def main():
    """Test the gas optimizer."""
    optimizer = GasOptimizer()
    
    # Test with a sample contract
    test_contract = """
    pragma solidity ^0.8.0;
    
    contract TestContract {
        uint256 public value1;
        uint256 public value2;
        bool public flag;
        address public owner;
        
        struct User {
            uint256 id;
            string name;
            bool active;
        }
        
        mapping(address => User) public users;
        
        function setValues(uint256 _value1, uint256 _value2) public {
            value1 = _value1;
            value2 = _value2;
        }
        
        function getUserData(address user) public view returns (string memory) {
            return users[user].name;
        }
    }
    """
    
    # Write test contract
    with open("test_contract.sol", "w") as f:
        f.write(test_contract)
    
    # Analyze contract
    analysis = optimizer.analyze_contract("test_contract.sol")
    print(optimizer.generate_optimization_report(analysis))
    
    # Clean up
    Path("test_contract.sol").unlink()


if __name__ == "__main__":
    main()