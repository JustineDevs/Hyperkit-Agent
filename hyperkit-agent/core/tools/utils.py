"""
HyperKit AI Agent - Utility Functions
Common utilities and helper functions
"""

import json
import logging
import hashlib
import re
from typing import Dict, Any, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


def validate_solidity_code(code: str) -> Dict[str, Any]:
    """
    Validate Solidity code for basic syntax and structure.

    Args:
        code: Solidity contract code

    Returns:
        Dictionary containing validation results
    """
    validation_result = {"valid": True, "errors": [], "warnings": [], "suggestions": []}

    # Check for SPDX license identifier
    if "SPDX-License-Identifier" not in code:
        validation_result["warnings"].append("Missing SPDX license identifier")

    # Check for pragma directive
    if "pragma solidity" not in code:
        validation_result["errors"].append("Missing pragma solidity directive")

    # Check for contract declaration
    if "contract " not in code:
        validation_result["errors"].append("No contract declaration found")

    # Check for basic security patterns
    if ".call(" in code and "nonReentrant" not in code:
        validation_result["warnings"].append(
            "External calls without reentrancy protection"
        )

    if "tx.origin" in code:
        validation_result["warnings"].append("Use of tx.origin for authorization")

    # Check for events
    if "event " not in code:
        validation_result["suggestions"].append(
            "Consider adding events for important state changes"
        )

    # Check for NatSpec documentation
    if "/**" not in code:
        validation_result["suggestions"].append("Consider adding NatSpec documentation")

    # Determine overall validity
    validation_result["valid"] = len(validation_result["errors"]) == 0

    return validation_result


def extract_contract_info(code: str) -> Dict[str, Any]:
    """
    Extract basic information from Solidity contract code.

    Args:
        code: Solidity contract code

    Returns:
        Dictionary containing contract information
    """
    info = {
        "contract_name": None,
        "inheritance": [],
        "functions": [],
        "events": [],
        "modifiers": [],
        "imports": [],
        "license": None,
        "pragma_version": None,
    }

    # Extract contract name
    contract_match = re.search(r"contract\s+(\w+)", code)
    if contract_match:
        info["contract_name"] = contract_match.group(1)

    # Extract inheritance
    inheritance_match = re.search(r"contract\s+\w+\s+is\s+([^{]+)", code)
    if inheritance_match:
        inheritance_str = inheritance_match.group(1)
        info["inheritance"] = [item.strip() for item in inheritance_str.split(",")]

    # Extract functions
    function_matches = re.findall(r"function\s+(\w+)", code)
    info["functions"] = function_matches

    # Extract events
    event_matches = re.findall(r"event\s+(\w+)", code)
    info["events"] = event_matches

    # Extract modifiers
    modifier_matches = re.findall(r"modifier\s+(\w+)", code)
    info["modifiers"] = modifier_matches

    # Extract imports
    import_matches = re.findall(r'import\s+["\']([^"\']+)["\']', code)
    info["imports"] = import_matches

    # Extract license
    license_match = re.search(r"SPDX-License-Identifier:\s*(\w+)", code)
    if license_match:
        info["license"] = license_match.group(1)

    # Extract pragma version
    pragma_match = re.search(r"pragma\s+solidity\s+([^;]+)", code)
    if pragma_match:
        info["pragma_version"] = pragma_match.group(1)

    return info


def calculate_code_metrics(code: str) -> Dict[str, Any]:
    """
    Calculate various metrics for Solidity code.

    Args:
        code: Solidity contract code

    Returns:
        Dictionary containing code metrics
    """
    lines = code.split("\n")

    metrics = {
        "total_lines": len(lines),
        "code_lines": len(
            [
                line
                for line in lines
                if line.strip() and not line.strip().startswith("//")
            ]
        ),
        "comment_lines": len([line for line in lines if line.strip().startswith("//")]),
        "blank_lines": len([line for line in lines if not line.strip()]),
        "functions_count": len(re.findall(r"function\s+\w+", code)),
        "events_count": len(re.findall(r"event\s+\w+", code)),
        "modifiers_count": len(re.findall(r"modifier\s+\w+", code)),
        "imports_count": len(re.findall(r"import\s+", code)),
        "complexity_score": calculate_complexity(code),
        "gas_estimate": estimate_gas_usage(code),
    }

    return metrics


def calculate_complexity(code: str) -> int:
    """
    Calculate cyclomatic complexity of Solidity code.

    Args:
        code: Solidity contract code

    Returns:
        Complexity score
    """
    complexity_keywords = [
        "if",
        "else",
        "while",
        "for",
        "do",
        "switch",
        "case",
        "catch",
        "&&",
        "||",
    ]

    complexity = 1  # Base complexity

    for keyword in complexity_keywords:
        complexity += len(re.findall(rf"\b{keyword}\b", code))

    return complexity


def estimate_gas_usage(code: str) -> Dict[str, int]:
    """
    Estimate gas usage for contract functions.

    Args:
        code: Solidity contract code

    Returns:
        Dictionary containing gas estimates
    """
    # Simple gas estimation based on code complexity
    base_gas = 21000
    function_count = len(re.findall(r"function\s+\w+", code))
    complexity = calculate_complexity(code)

    return {
        "deployment": base_gas + (function_count * 20000) + (complexity * 1000),
        "average_function": 50000 + (complexity * 5000),
        "complex_function": 100000 + (complexity * 10000),
    }


def generate_contract_hash(code: str) -> str:
    """
    Generate a hash for contract code.

    Args:
        code: Solidity contract code

    Returns:
        SHA-256 hash of the contract
    """
    # Normalize code (remove comments and extra whitespace)
    normalized_code = re.sub(r"//.*$", "", code, flags=re.MULTILINE)
    normalized_code = re.sub(r"/\*.*?\*/", "", normalized_code, flags=re.DOTALL)
    normalized_code = re.sub(r"\s+", " ", normalized_code)

    return hashlib.sha256(normalized_code.encode()).hexdigest()


def format_contract_code(code: str) -> str:
    """
    Format Solidity code for better readability.

    Args:
        code: Solidity contract code

    Returns:
        Formatted contract code
    """
    # Basic formatting (in practice, you'd use a proper formatter like prettier-solidity)
    lines = code.split("\n")
    formatted_lines = []
    indent_level = 0

    for line in lines:
        stripped = line.strip()
        if not stripped:
            formatted_lines.append("")
            continue

        # Decrease indent for closing braces
        if stripped.startswith("}"):
            indent_level = max(0, indent_level - 1)

        # Add indentation
        formatted_line = "    " * indent_level + stripped
        formatted_lines.append(formatted_line)

        # Increase indent for opening braces
        if stripped.endswith("{"):
            indent_level += 1

    return "\n".join(formatted_lines)


def save_contract_to_file(
    code: str, filename: str, directory: str = "./contracts"
) -> str:
    """
    Save contract code to a file.

    Args:
        code: Solidity contract code
        filename: Name of the file
        directory: Directory to save the file

    Returns:
        Path to the saved file
    """
    Path(directory).mkdir(parents=True, exist_ok=True)

    if not filename.endswith(".sol"):
        filename += ".sol"

    file_path = Path(directory) / filename

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(code)

    logger.info(f"Contract saved to {file_path}")
    return str(file_path)


def load_contract_from_file(file_path: str) -> str:
    """
    Load contract code from a file.

    Args:
        file_path: Path to the contract file

    Returns:
        Contract code content
    """
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def create_contract_metadata(
    contract_code: str, deployment_info: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Create metadata for a deployed contract.

    Args:
        contract_code: Solidity contract code
        deployment_info: Deployment information

    Returns:
        Contract metadata
    """
    contract_info = extract_contract_info(contract_code)
    metrics = calculate_code_metrics(contract_code)

    metadata = {
        "contract_info": contract_info,
        "metrics": metrics,
        "deployment": deployment_info,
        "code_hash": generate_contract_hash(contract_code),
        "timestamp": deployment_info.get("timestamp"),
        "network": deployment_info.get("network"),
        "address": deployment_info.get("address"),
        "tx_hash": deployment_info.get("tx_hash"),
    }

    return metadata


def validate_network_config(network: str, config: Dict[str, Any]) -> bool:
    """
    Validate network configuration.

    Args:
        network: Network name
        config: Network configuration

    Returns:
        True if configuration is valid
    """
    required_fields = ["rpc_url", "chain_id", "explorer"]

    if network not in config:
        return False

    network_config = config[network]

    for field in required_fields:
        if field not in network_config:
            logger.error(f"Missing required field '{field}' for network '{network}'")
            return False

    return True


def format_error_message(error: Exception) -> str:
    """
    Format error message for better readability.

    Args:
        error: Exception object

    Returns:
        Formatted error message
    """
    error_type = type(error).__name__
    error_message = str(error)

    return f"{error_type}: {error_message}"


def create_audit_report(audit_results: Dict[str, Any]) -> str:
    """
    Create a formatted audit report.

    Args:
        audit_results: Audit results dictionary

    Returns:
        Formatted audit report
    """
    report = []
    report.append("=" * 60)
    report.append("HYPERKIT AI AGENT - SECURITY AUDIT REPORT")
    report.append("=" * 60)
    report.append("")

    # Summary
    findings = audit_results.get("findings", [])
    severity = audit_results.get("severity", "unknown")

    report.append(f"Overall Severity: {severity.upper()}")
    report.append(f"Total Findings: {len(findings)}")
    report.append("")

    # Findings by severity
    severity_counts = {}
    for finding in findings:
        sev = finding.get("severity", "unknown")
        severity_counts[sev] = severity_counts.get(sev, 0) + 1

    report.append("Findings by Severity:")
    for sev, count in sorted(severity_counts.items(), key=lambda x: x[1], reverse=True):
        report.append(f"  {sev.upper()}: {count}")
    report.append("")

    # Detailed findings
    if findings:
        report.append("Detailed Findings:")
        report.append("-" * 40)

        for i, finding in enumerate(findings, 1):
            report.append(f"{i}. {finding.get('description', 'No description')}")
            report.append(f"   Severity: {finding.get('severity', 'unknown')}")
            report.append(f"   Tool: {finding.get('tool', 'unknown')}")
            if finding.get("pattern"):
                report.append(f"   Pattern: {finding['pattern']}")
            report.append("")

    # Recommendations
    report.append("Recommendations:")
    report.append("-" * 40)

    if severity_counts.get("critical", 0) > 0:
        report.append("• Address critical vulnerabilities immediately")
    if severity_counts.get("high", 0) > 0:
        report.append("• Review and fix high-severity issues")
    if severity_counts.get("medium", 0) > 0:
        report.append("• Consider addressing medium-severity issues")

    report.append("• Implement additional security measures")
    report.append("• Consider external security audit")
    report.append("")
    report.append("=" * 60)

    return "\n".join(report)


# Example usage
if __name__ == "__main__":
    # Example contract code
    sample_contract = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract SimpleToken {
    mapping(address => uint256) public balances;
    
    function deposit() public payable {
        balances[msg.sender] += msg.value;
    }
    
    function withdraw(uint256 amount) public {
        require(balances[msg.sender] >= amount);
        msg.sender.call{value: amount}("");
        balances[msg.sender] -= amount;
    }
}
"""

    # Test validation
    validation = validate_solidity_code(sample_contract)
    print("Validation Results:")
    print(json.dumps(validation, indent=2))

    # Test contract info extraction
    info = extract_contract_info(sample_contract)
    print("\nContract Info:")
    print(json.dumps(info, indent=2))

    # Test metrics
    metrics = calculate_code_metrics(sample_contract)
    print("\nCode Metrics:")
    print(json.dumps(metrics, indent=2))
