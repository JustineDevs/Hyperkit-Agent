"""
Enhanced Error Messages for Deployment

Provides detailed, actionable error messages with examples and diagnostics.
Part of P1 Deploy Fix - Step 3: User-Friendly Error Reporting
"""

from typing import Dict, List, Any, Optional


class DeploymentErrorMessages:
    """Generate user-friendly error messages with examples and suggestions"""
    
    @staticmethod
    def constructor_validation_failed(
        error: str,
        provided_args: List[Any],
        expected_params: List[Dict[str, str]],
        contract_name: str = "Contract"
    ) -> Dict[str, Any]:
        """
        Generate detailed error message for constructor validation failure.
        
        Args:
            error: The validation error message
            provided_args: Arguments that were provided
            expected_params: Expected constructor parameters
            contract_name: Name of the contract
            
        Returns:
            Detailed error dictionary with suggestions and examples
        """
        # Build parameter signature
        param_signature = ", ".join([
            f"{p['type']} {p['name']}" for p in expected_params
        ])
        
        # Generate examples based on parameter types
        examples = DeploymentErrorMessages._generate_constructor_examples(
            expected_params, 
            contract_name
        )
        
        # Provide specific suggestions based on error type
        suggestions = DeploymentErrorMessages._analyze_validation_error(
            error,
            provided_args,
            expected_params
        )
        
        return {
            "success": False,
            "error": f"Constructor validation failed: {error}",
            "contract_name": contract_name,
            "provided_args": provided_args,
            "expected_signature": param_signature,
            "expected_params": expected_params,
            "suggestions": suggestions,
            "examples": examples,
            "help": "Run 'hyperagent deploy --help' for more information"
        }
    
    @staticmethod
    def _generate_constructor_examples(
        params: List[Dict[str, str]],
        contract_name: str
    ) -> Dict[str, str]:
        """Generate usage examples based on constructor parameters"""
        
        # Generate example values
        example_values = []
        for param in params:
            param_type = param['type']
            param_name = param['name']
            
            if 'address' in param_type:
                example_values.append('"0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"')
            elif 'uint' in param_type:
                if 'supply' in param_name.lower() or 'amount' in param_name.lower():
                    example_values.append('1000000000000000000000000')  # 1M tokens with 18 decimals
                else:
                    example_values.append('100')
            elif 'int' in param_type:
                example_values.append('0')
            elif param_type == 'string':
                if 'name' in param_name.lower():
                    example_values.append('"My Token"')
                elif 'symbol' in param_name.lower():
                    example_values.append('"MTK"')
                else:
                    example_values.append('"example"')
            elif param_type == 'bool':
                example_values.append('true')
            elif '[]' in param_type:  # Array types
                base_type = param_type.replace('[]', '')
                if 'address' in base_type:
                    example_values.append('["0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb", "0x123..."]')
                else:
                    example_values.append('[1, 2, 3]')
            elif 'bytes' in param_type:
                example_values.append('"0x"')
            else:
                example_values.append('""')
        
        # Build example commands
        cli_array = f'[{", ".join(example_values)}]'
        
        examples = {
            "cli_inline": f"hyperagent deploy contract {contract_name}.sol --constructor-args '{cli_array}'",
            "cli_file": f"hyperagent deploy contract {contract_name}.sol --constructor-file args.json",
        }
        
        # Generate JSON file examples
        json_array = {
            "description": "Array format (positional)",
            "content": f"[\n  {',\n  '.join(example_values)}\n]"
        }
        
        json_named = {
            "description": "Named format (recommended)",
            "content": "{\n" + ",\n".join([
                f'  "{param["name"]}": {example_values[i]}'
                for i, param in enumerate(params)
            ]) + "\n}"
        }
        
        examples["json_array_format"] = json_array
        examples["json_named_format"] = json_named
        
        return examples
    
    @staticmethod
    def _analyze_validation_error(
        error: str,
        provided_args: List[Any],
        expected_params: List[Dict[str, str]]
    ) -> List[str]:
        """Provide specific suggestions based on error type"""
        
        suggestions = []
        error_lower = error.lower()
        
        # Argument count mismatch
        if "expected" in error_lower and "got" in error_lower:
            suggestions.extend([
                f"The constructor expects {len(expected_params)} arguments but {len(provided_args)} were provided",
                "Check the contract constructor signature",
                "Ensure all required parameters are provided",
            ])
        
        # Type mismatch
        if "type" in error_lower or "mismatch" in error_lower:
            suggestions.extend([
                "Verify that argument types match the constructor signature:",
            ])
            for param in expected_params:
                suggestions.append(f"  • {param['name']}: {param['type']}")
            suggestions.extend([
                "",
                "Common type fixes:",
                "  • Addresses must start with '0x' and be 40 hex characters",
                "  • Numbers should not have quotes (use 1000, not \"1000\")",
                "  • Strings must have quotes (use \"MyToken\", not MyToken)",
                "  • Arrays use bracket notation: [item1, item2, item3]",
            ])
        
        # Address format issues
        if any('address' == p['type'] for p in expected_params):
            if any(isinstance(arg, str) and not arg.startswith('0x') for arg in provided_args):
                suggestions.extend([
                    "",
                    "⚠️  Address Format Issue:",
                    "  • All addresses must start with '0x'",
                    "  • Valid: '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb'",
                    "  • Invalid: '742d35Cc6634C0532925a3b844Bc9e7595f0bEb'",
                ])
        
        # Array issues
        if any('[]' in p['type'] for p in expected_params):
            suggestions.extend([
                "",
                "📦 Array Arguments:",
                "  • Dynamic arrays: address[] → [\"0x123...\", \"0x456...\"]",
                "  • Fixed arrays: uint256[3] → [100, 200, 300]",
                "  • Empty arrays are valid: []",
            ])
        
        # General suggestions
        suggestions.extend([
            "",
            "💡 Tips:",
            "  • Use --constructor-file for complex arguments",
            "  • Test with small values first",
            "  • Check contract documentation for expected formats",
        ])
        
        return suggestions
    
    @staticmethod
    def file_load_failed(
        file_path: str,
        error: Exception,
        expected_params: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """Generate error message for file loading failures"""
        
        error_type = type(error).__name__
        suggestions = []
        
        if "FileNotFoundError" in error_type:
            suggestions = [
                f"The file '{file_path}' does not exist",
                "Check the file path is correct",
                "Use absolute path or path relative to current directory",
                f"Example: --constructor-file ./config/args.json",
            ]
        
        elif "JSONDecodeError" in error_type:
            suggestions = [
                f"The file '{file_path}' contains invalid JSON",
                "Common JSON errors:",
                "  • Missing closing brackets ] or }",
                "  • Trailing commas",
                "  • Unquoted strings",
                "  • Single quotes instead of double quotes",
                "",
                "Valid JSON examples:",
                '  Array: ["0x123...", 1000000]',
                '  Object: {"owner": "0x123...", "supply": 1000000}',
            ]
        
        else:
            suggestions = [
                f"Failed to load constructor arguments: {error}",
                "Verify the file is readable",
                "Check file permissions",
                "Ensure JSON format is correct",
            ]
        
        if expected_params:
            suggestions.append("")
            suggestions.append("Expected constructor parameters:")
            for param in expected_params:
                suggestions.append(f"  • {param['name']}: {param['type']}")
        
        return {
            "success": False,
            "error": f"Failed to load constructor args from file: {error}",
            "file_path": file_path,
            "error_type": error_type,
            "suggestions": suggestions,
            "help": "See documentation for JSON file format examples"
        }
    
    @staticmethod
    def foundry_not_available() -> Dict[str, Any]:
        """Generate error message when Foundry is not installed"""
        
        return {
            "success": False,
            "error": "Foundry is required for deployment but is not installed or not available",
            "required_tool": "Foundry",
            "installation_steps": [
                "1. Run: curl -L https://foundry.paradigm.xyz | bash",
                "2. Run: foundryup",
                "3. Verify: forge --version",
            ],
            "documentation": "https://book.getfoundry.sh/getting-started/installation",
            "alternative": "Use the web UI or API for deployment without Foundry",
            "suggestions": [
                "Install Foundry for command-line deployments",
                "Or use the HyperKit web interface",
                "Or use the REST API for programmatic deployments",
            ]
        }
    
    @staticmethod
    def deployment_failed(
        error: str,
        contract_name: str,
        chain_id: int,
        transaction_hash: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate error message for deployment failures"""
        
        suggestions = []
        error_lower = error.lower()
        
        # Gas-related errors
        if "gas" in error_lower or "out of gas" in error_lower:
            suggestions.extend([
                "⛽ Gas Issue Detected:",
                "  • Contract may be too complex",
                "  • Increase gas limit",
                "  • Check constructor logic for loops",
                "  • Verify RPC endpoint supports the required gas",
            ])
        
        # Insufficient funds
        if "insufficient" in error_lower or "balance" in error_lower:
            suggestions.extend([
                "💰 Insufficient Balance:",
                "  • Deployer account needs more native tokens",
                "  • Check account balance on the blockchain",
                "  • Fund the deployer address",
            ])
        
        # RPC errors
        if "rpc" in error_lower or "connection" in error_lower or "timeout" in error_lower:
            suggestions.extend([
                "🌐 RPC Connection Issue:",
                "  • Verify RPC endpoint is online",
                "  • Check network connection",
                "  • Try a different RPC endpoint",
                "  • Check if the chain ID matches the RPC",
            ])
        
        # Revert errors
        if "revert" in error_lower:
            suggestions.extend([
                "🔄 Contract Reverted:",
                "  • Constructor requirements not met",
                "  • Check constructor logic and require statements",
                "  • Verify all constructor arguments are valid",
                "  • Check for access control issues",
            ])
        
        # General suggestions
        if not suggestions:
            suggestions = [
                "Check deployment logs for details",
                "Verify contract compiles successfully",
                "Test deployment on testnet first",
                "Review contract constructor logic",
            ]
        
        result = {
            "success": False,
            "error": f"Deployment failed: {error}",
            "contract_name": contract_name,
            "chain_id": chain_id,
            "suggestions": suggestions,
        }
        
        if transaction_hash:
            result["transaction_hash"] = transaction_hash
            result["explorer_note"] = "Check block explorer for transaction details"
        
        return result

