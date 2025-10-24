"""
Smart contract testing and interaction service.
"""

import json
import logging
import asyncio
from typing import Dict, Any, List, Optional
from pathlib import Path

from .web3_interaction import Web3Interaction

logger = logging.getLogger(__name__)

class ContractTester:
    """
    Main contract testing service that handles contract interaction,
    function testing, and validation.
    """
    
    def __init__(self, rpc_url: str, contract_address: str, abi: Optional[List[Dict]] = None):
        self.rpc_url = rpc_url
        self.contract_address = contract_address
        self.abi = abi or []
        self.web3_interaction = Web3Interaction(rpc_url)
        
    async def run_tests(self, source_code: str) -> Dict[str, Any]:
        """
        Run comprehensive tests on the deployed contract.
        
        Args:
            source_code: The Solidity source code for analysis
            
        Returns:
            Dict with test results
        """
        try:
            logger.info(f"Starting contract tests for {self.contract_address}")
            
            test_results = {
                "contract_address": self.contract_address,
                "rpc_url": self.rpc_url,
                "tests_passed": 0,
                "tests_failed": 0,
                "test_details": []
            }
            
            # Test 1: Contract parsing and validation
            parsing_result = await self._test_contract_parsing(source_code)
            test_results["test_details"].append(parsing_result)
            if parsing_result["status"] == "passed":
                test_results["tests_passed"] += 1
            else:
                test_results["tests_failed"] += 1
            
            # Test 2: Syntax validation
            syntax_result = await self._test_syntax_validation(source_code)
            test_results["test_details"].append(syntax_result)
            if syntax_result["status"] == "passed":
                test_results["tests_passed"] += 1
            else:
                test_results["tests_failed"] += 1
            
            # Test 3: Contract interaction
            interaction_result = await self._test_contract_interaction()
            test_results["test_details"].append(interaction_result)
            if interaction_result["status"] == "passed":
                test_results["tests_passed"] += 1
            else:
                test_results["tests_failed"] += 1
            
            # Test 4: Function detection
            function_result = await self._test_function_detection(source_code)
            test_results["test_details"].append(function_result)
            if function_result["status"] == "passed":
                test_results["tests_passed"] += 1
            else:
                test_results["tests_failed"] += 1
            
            # Overall status
            test_results["overall_status"] = "passed" if test_results["tests_failed"] == 0 else "failed"
            
            logger.info(f"Contract tests completed: {test_results['tests_passed']} passed, {test_results['tests_failed']} failed")
            return test_results
            
        except Exception as e:
            logger.error(f"Contract testing failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "contract_address": self.contract_address
            }
    
    async def _test_contract_parsing(self, source_code: str) -> Dict[str, Any]:
        """Test contract parsing and structure analysis."""
        try:
            # Basic contract structure analysis
            lines = source_code.split('\n')
            contract_lines = [line for line in lines if 'contract ' in line]
            function_lines = [line for line in lines if 'function ' in line]
            event_lines = [line for line in lines if 'event ' in line]
            
            return {
                "test_name": "contract_parsing",
                "status": "passed",
                "details": {
                    "total_lines": len(lines),
                    "contracts_found": len(contract_lines),
                    "functions_found": len(function_lines),
                    "events_found": len(event_lines),
                    "contract_names": [line.split('contract ')[1].split(' ')[0] for line in contract_lines]
                }
            }
        except Exception as e:
            return {
                "test_name": "contract_parsing",
                "status": "failed",
                "error": str(e)
            }
    
    async def _test_syntax_validation(self, source_code: str) -> Dict[str, Any]:
        """Test Solidity syntax validation."""
        try:
            # Basic syntax checks
            syntax_checks = {
                "has_pragma": "pragma solidity" in source_code,
                "has_contract": "contract " in source_code,
                "has_braces": source_code.count('{') == source_code.count('}'),
                "has_semicolons": source_code.count(';') > 0,
                "valid_structure": True
            }
            
            all_passed = all(syntax_checks.values())
            
            return {
                "test_name": "syntax_validation",
                "status": "passed" if all_passed else "failed",
                "details": syntax_checks
            }
        except Exception as e:
            return {
                "test_name": "syntax_validation",
                "status": "failed",
                "error": str(e)
            }
    
    async def _test_contract_interaction(self) -> Dict[str, Any]:
        """Test basic contract interaction."""
        try:
            # Test contract connection
            is_connected = await self.web3_interaction.is_contract_deployed(self.contract_address)
            
            if is_connected:
                # Try to get contract code
                contract_code = await self.web3_interaction.get_contract_code(self.contract_address)
                
                return {
                    "test_name": "contract_interaction",
                    "status": "passed",
                    "details": {
                        "contract_deployed": True,
                        "has_code": len(contract_code) > 0,
                        "code_length": len(contract_code)
                    }
                }
            else:
                return {
                    "test_name": "contract_interaction",
                    "status": "failed",
                    "details": {
                        "contract_deployed": False,
                        "error": "Contract not found or not deployed"
                    }
                }
        except Exception as e:
            return {
                "test_name": "contract_interaction",
                "status": "failed",
                "error": str(e)
            }
    
    async def _test_function_detection(self, source_code: str) -> Dict[str, Any]:
        """Test function detection and analysis."""
        try:
            # Extract function signatures
            functions = []
            lines = source_code.split('\n')
            
            for i, line in enumerate(lines):
                if 'function ' in line and '{' in line:
                    # Extract function name
                    func_line = line.strip()
                    if 'function ' in func_line:
                        func_name = func_line.split('function ')[1].split('(')[0].strip()
                        functions.append({
                            "name": func_name,
                            "line": i + 1,
                            "signature": func_line
                        })
            
            return {
                "test_name": "function_detection",
                "status": "passed",
                "details": {
                    "functions_found": len(functions),
                    "function_list": [f["name"] for f in functions],
                    "functions": functions
                }
            }
        except Exception as e:
            return {
                "test_name": "function_detection",
                "status": "failed",
                "error": str(e)
            }
    
    async def test_specific_function(
        self, 
        function_name: str, 
        parameters: List[Any] = None
    ) -> Dict[str, Any]:
        """
        Test a specific contract function.
        
        Args:
            function_name: Name of the function to test
            parameters: Function parameters
            
        Returns:
            Dict with function test result
        """
        try:
            result = await self.web3_interaction.call_contract_function(
                contract_address=self.contract_address,
                function_name=function_name,
                parameters=parameters or []
            )
            
            return {
                "function_name": function_name,
                "status": "success",
                "result": result
            }
        except Exception as e:
            return {
                "function_name": function_name,
                "status": "failed",
                "error": str(e)
            }
