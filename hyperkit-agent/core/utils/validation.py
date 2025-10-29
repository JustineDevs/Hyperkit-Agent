"""
Validation Utilities
Provides comprehensive input validation and sanitization
"""

import re
import os
from typing import Any, Dict, List, Optional, Union, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ValidationResult:
    """Validation result container"""

    def __init__(
        self, is_valid: bool, errors: List[str] = None, warnings: List[str] = None
    ):
        self.is_valid = is_valid
        self.errors = errors or []
        self.warnings = warnings or []

    def add_error(self, error: str):
        """Add an error message"""
        self.errors.append(error)
        self.is_valid = False

    def add_warning(self, warning: str):
        """Add a warning message"""
        self.warnings.append(warning)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "is_valid": self.is_valid,
            "errors": self.errors,
            "warnings": self.warnings,
        }


class Validator:
    """Comprehensive validation utility"""

    def __init__(self):
        self.patterns = self._initialize_patterns()

    def _initialize_patterns(self) -> Dict[str, str]:
        """Initialize validation patterns"""
        return {
            "ethereum_address": r"^0x[a-fA-F0-9]{40}$",
            "private_key": r"^[a-fA-F0-9]{64}$",
            "tx_hash": r"^0x[a-fA-F0-9]{64}$",
            "block_number": r"^\d+$",
            "gas_limit": r"^\d+$",
            "gas_price": r"^\d+$",
            "wei_amount": r"^\d+$",
            "ether_amount": r"^\d+(\.\d+)?$",
            "contract_name": r"^[a-zA-Z][a-zA-Z0-9_]*$",
            "function_name": r"^[a-zA-Z][a-zA-Z0-9_]*$",
            "variable_name": r"^[a-zA-Z][a-zA-Z0-9_]*$",
            "pragma_version": r"^pragma solidity\s+[\^>=<]?[\d\.]+;?$",
            "import_statement": r'^import\s+["\'].*["\'];?$',
            "api_key": r"^[a-zA-Z0-9_-]{20,}$",
            "rpc_url": r"^https?://[^\s/$.?#].[^\s]*$",
            "file_path": r"^[a-zA-Z0-9_/\\\.-]+$",
            "network_name": r"^[a-zA-Z][a-zA-Z0-9_-]*$",
        }

    def validate_ethereum_address(self, address: str) -> ValidationResult:
        """Validate Ethereum address format"""
        result = ValidationResult(True)

        if not address:
            result.add_error("Address cannot be empty")
            return result

        if not re.match(self.patterns["ethereum_address"], address):
            result.add_error("Invalid Ethereum address format")

        # Check if address is all zeros
        if address == "0x" + "0" * 40:
            result.add_warning("Address is all zeros (null address)")

        return result

    def validate_private_key(self, private_key: str) -> ValidationResult:
        """Validate private key format"""
        result = ValidationResult(True)

        if not private_key:
            result.add_error("Private key cannot be empty")
            return result

        # Remove 0x prefix if present
        if private_key.startswith("0x"):
            private_key = private_key[2:]

        if not re.match(self.patterns["private_key"], private_key):
            result.add_error("Invalid private key format (must be 64 hex characters)")

        if len(private_key) != 64:
            result.add_error("Private key must be exactly 64 characters")

        return result

    def validate_tx_hash(self, tx_hash: str) -> ValidationResult:
        """Validate transaction hash format"""
        result = ValidationResult(True)

        if not tx_hash:
            result.add_error("Transaction hash cannot be empty")
            return result

        if not re.match(self.patterns["tx_hash"], tx_hash):
            result.add_error("Invalid transaction hash format")

        return result

    def validate_gas_settings(
        self, gas_limit: Union[str, int], gas_price: Union[str, int]
    ) -> ValidationResult:
        """Validate gas limit and price"""
        result = ValidationResult(True)

        # Validate gas limit
        if isinstance(gas_limit, str):
            if not re.match(self.patterns["gas_limit"], gas_limit):
                result.add_error("Invalid gas limit format")
            else:
                gas_limit = int(gas_limit)

        if isinstance(gas_limit, int):
            if gas_limit < 21000:
                result.add_error("Gas limit too low (minimum 21000)")
            elif gas_limit > 30000000:
                result.add_warning("Gas limit very high (maximum recommended 30000000)")

        # Validate gas price
        if isinstance(gas_price, str):
            if not re.match(self.patterns["gas_price"], gas_price):
                result.add_error("Invalid gas price format")
            else:
                gas_price = int(gas_price)

        if isinstance(gas_price, int):
            if gas_price < 1:
                result.add_error("Gas price too low (minimum 1 wei)")
            elif gas_price > 1000000000000:  # 1000 gwei
                result.add_warning("Gas price very high")

        return result

    def validate_contract_code(self, contract_code: str) -> ValidationResult:
        """Validate Solidity contract code"""
        result = ValidationResult(True)

        if not contract_code:
            result.add_error("Contract code cannot be empty")
            return result

        # Check for required pragma statement
        if "pragma solidity" not in contract_code:
            result.add_error("Contract must include pragma solidity statement")

        # Check for basic contract structure
        if "contract" not in contract_code:
            result.add_error("Contract code must contain at least one contract")

        # Check for common issues
        if "selfdestruct" in contract_code:
            result.add_warning("Contract contains selfdestruct - use with caution")

        if "delegatecall" in contract_code:
            result.add_warning(
                "Contract contains delegatecall - ensure proper validation"
            )

        if "assembly" in contract_code:
            result.add_warning("Contract contains assembly code - review carefully")

        # Check for proper license identifier
        if "SPDX-License-Identifier" not in contract_code:
            result.add_warning("Contract should include SPDX license identifier")

        return result

    def validate_network_config(self, network: str, rpc_url: str) -> ValidationResult:
        """Validate network configuration"""
        result = ValidationResult(True)

        # Validate network name
        if not re.match(self.patterns["network_name"], network):
            result.add_error("Invalid network name format")

        # Validate RPC URL
        if not re.match(self.patterns["rpc_url"], rpc_url):
            result.add_error("Invalid RPC URL format")

        # Check for common network names
        valid_networks = [
            "mainnet",
            "polygon",
            "arbitrum",
            "hyperion",
            "testnet",
            "goerli",
            "sepolia",
        ]
        if network.lower() not in valid_networks:
            result.add_warning(f"Unknown network: {network}")

        return result

    def validate_api_key(self, api_key: str, provider: str) -> ValidationResult:
        """Validate API key format"""
        result = ValidationResult(True)

        if not api_key:
            result.add_error(f"{provider} API key cannot be empty")
            return result

        if api_key == f"your_{provider.lower()}_api_key_here":
            result.add_error(
                f"Please replace placeholder with actual {provider} API key"
            )
            return result

        if not re.match(self.patterns["api_key"], api_key):
            result.add_error(f"Invalid {provider} API key format")

        # Provider-specific validation
        if provider.lower() == "openai" and not api_key.startswith("sk-"):
            result.add_warning("OpenAI API key should start with 'sk-'")

        if provider.lower() == "google" and not api_key.startswith("AIza"):
            result.add_warning("Google API key should start with 'AIza'")

        return result

    def validate_file_path(
        self, file_path: str, must_exist: bool = False
    ) -> ValidationResult:
        """Validate file path"""
        result = ValidationResult(True)

        if not file_path:
            result.add_error("File path cannot be empty")
            return result

        if not re.match(self.patterns["file_path"], file_path):
            result.add_error("Invalid file path format")

        if must_exist and not os.path.exists(file_path):
            result.add_error(f"File does not exist: {file_path}")

        return result

    def validate_constructor_args(
        self, args: List[Any], abi: List[Dict]
    ) -> ValidationResult:
        """Validate constructor arguments against ABI"""
        result = ValidationResult(True)

        if not abi:
            result.add_warning("No ABI provided for constructor validation")
            return result

        # Find constructor in ABI
        constructor = None
        for item in abi:
            if item.get("type") == "constructor":
                constructor = item
                break

        if not constructor:
            if args:
                result.add_warning(
                    "Constructor arguments provided but no constructor in ABI"
                )
            return result

        constructor_inputs = constructor.get("inputs", [])

        if len(args) != len(constructor_inputs):
            result.add_error(
                f"Expected {len(constructor_inputs)} constructor arguments, got {len(args)}"
            )
            return result

        # Validate each argument
        for i, (arg, input_spec) in enumerate(zip(args, constructor_inputs)):
            expected_type = input_spec.get("type", "")
            if not self._validate_solidity_type(arg, expected_type):
                result.add_error(
                    f"Argument {i} type mismatch: expected {expected_type}"
                )

        return result

    def _validate_solidity_type(self, value: Any, solidity_type: str) -> bool:
        """Validate value against Solidity type"""
        if solidity_type.startswith("uint"):
            return isinstance(value, int) and value >= 0
        elif solidity_type.startswith("int"):
            return isinstance(value, int)
        elif solidity_type == "bool":
            return isinstance(value, bool)
        elif solidity_type == "address":
            return (
                isinstance(value, str)
                and self.validate_ethereum_address(value).is_valid
            )
        elif solidity_type.startswith("bytes"):
            return isinstance(value, (str, bytes))
        elif solidity_type == "string":
            return isinstance(value, str)
        else:
            return True  # Unknown type, assume valid

    def validate_prompt(self, prompt: str) -> ValidationResult:
        """Validate user prompt for contract generation"""
        result = ValidationResult(True)

        if not prompt:
            result.add_error("Prompt cannot be empty")
            return result

        if len(prompt) < 10:
            result.add_warning("Prompt is very short - consider providing more details")

        if len(prompt) > 10000:
            result.add_warning("Prompt is very long - consider shortening it")

        # Check for potentially problematic content
        if any(
            word in prompt.lower()
            for word in ["hack", "exploit", "vulnerability", "backdoor"]
        ):
            result.add_warning("Prompt contains potentially sensitive keywords")

        return result

    def validate_contract_name(self, name: str) -> ValidationResult:
        """Validate contract name"""
        result = ValidationResult(True)

        if not name:
            result.add_error("Contract name cannot be empty")
            return result

        if not re.match(self.patterns["contract_name"], name):
            result.add_error(
                "Invalid contract name format (must start with letter, contain only letters, numbers, and underscores)"
            )

        if len(name) > 50:
            result.add_warning("Contract name is very long")

        return result

    def sanitize_input(self, input_str: str, max_length: int = 10000) -> str:
        """Sanitize user input"""
        if not input_str:
            return ""

        # Remove null bytes and control characters
        sanitized = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", input_str)

        # Limit length with user alert
        original_length = len(sanitized)
        if original_length > max_length:
            sanitized = sanitized[:max_length]
            truncated_amount = original_length - max_length
            logger.error(f"CRITICAL: Input truncated from {original_length} to {max_length} characters ({truncated_amount} chars lost)")
            logger.error(f"This truncation may cause contract generation to fail or miss critical features")
            logger.error(f"Please split your prompt or increase the max_length parameter")
            # Raise warning that will be caught by error handler
            raise ValueError(f"Input truncated: {original_length} chars → {max_length} chars ({truncated_amount} chars lost). This may cause failures.")

        return sanitized.strip()

    def validate_environment_config(self, config: Dict[str, Any]) -> ValidationResult:
        """Validate environment configuration"""
        result = ValidationResult(True)

        # Check required API keys
        required_keys = ["GOOGLE_API_KEY"]
        for key in required_keys:
            if not config.get(key):
                result.add_error(f"Required environment variable {key} is not set")

        # Validate API keys
        if config.get("GOOGLE_API_KEY"):
            api_result = self.validate_api_key(config["GOOGLE_API_KEY"], "google")
            if not api_result.is_valid:
                result.errors.extend(api_result.errors)
                result.is_valid = False

        # Validate network URLs
        network_keys = [
            "HYPERION_RPC_URL",
            "METIS_RPC_URL",
            "LAZAI_RPC_URL",
        ]
        for key in network_keys:
            if config.get(key):
                if not re.match(self.patterns["rpc_url"], config[key]):
                    result.add_error(f"Invalid RPC URL format for {key}")

        return result

    def validate_deployment_config(self, config: Dict[str, Any]) -> ValidationResult:
        """Validate deployment configuration"""
        result = ValidationResult(True)

        # Check required fields
        if not config.get("network"):
            result.add_error("Network must be specified for deployment")

        if not config.get("private_key"):
            result.add_error("Private key must be provided for deployment")

        # Validate network
        if config.get("network"):
            network_result = self.validate_network_config(
                config["network"], config.get("rpc_url", "")
            )
            if not network_result.is_valid:
                result.errors.extend(network_result.errors)
                result.is_valid = False

        # Validate private key
        if config.get("private_key"):
            pk_result = self.validate_private_key(config["private_key"])
            if not pk_result.is_valid:
                result.errors.extend(pk_result.errors)
                result.is_valid = False

        return result
