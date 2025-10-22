"""
Smart Contract Auditing and Debugging Service
Integrates multiple security tools for comprehensive contract analysis
"""

import asyncio
import json
import logging
import subprocess
import tempfile
from typing import Dict, Any, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class SmartContractAuditor:
    """
    Comprehensive smart contract auditor using multiple security tools.
    Integrates Slither, Mythril, and custom pattern analysis.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the smart contract auditor.

        Args:
            config: Configuration dictionary for audit tools
        """
        self.config = config or {}
        self.tools_available = self._check_tools_availability()
        self.severity_weights = {
            "critical": 10,
            "high": 7,
            "medium": 4,
            "low": 1,
            "info": 0.5,
        }

        logger.info(
            f"SmartContractAuditor initialized. Available tools: {self.tools_available}"
        )

    def _check_tools_availability(self) -> Dict[str, bool]:
        """Check which security tools are available on the system."""
        tools = {}

        # Check Slither
        try:
            result = subprocess.run(
                ["slither", "--version"], capture_output=True, text=True, timeout=10
            )
            tools["slither"] = result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            tools["slither"] = False

        # Check Mythril
        try:
            result = subprocess.run(
                ["myth", "version"], capture_output=True, text=True, timeout=10
            )
            tools["mythril"] = result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            tools["mythril"] = False

        # Check EDB (Ethereum Debugger)
        try:
            result = subprocess.run(
                ["edb", "--version"], capture_output=True, text=True, timeout=10
            )
            tools["edb"] = result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            tools["edb"] = False

        return tools

    async def audit(self, contract_code: str) -> Dict[str, Any]:
        """
        Perform comprehensive audit of a smart contract.

        Args:
            contract_code: Solidity contract code to audit

        Returns:
            Dictionary containing audit results and severity assessment
        """
        try:
            logger.info("Starting comprehensive contract audit")

            # Create temporary file for contract
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".sol", delete=False
            ) as f:
                f.write(contract_code)
                temp_file = f.name

            audit_results = {
                "timestamp": asyncio.get_event_loop().time(),
                "contract_length": len(contract_code),
                "tools_used": [],
                "findings": [],
                "severity": "unknown",
            }

            # Run Slither analysis
            if self.tools_available["slither"]:
                slither_results = await self._run_slither(temp_file)
                audit_results["slither"] = slither_results
                audit_results["tools_used"].append("slither")
                audit_results["findings"].extend(slither_results.get("findings", []))

            # Run Mythril analysis
            if self.tools_available["mythril"]:
                mythril_results = await self._run_mythril(temp_file)
                audit_results["mythril"] = mythril_results
                audit_results["tools_used"].append("mythril")
                audit_results["findings"].extend(mythril_results.get("findings", []))

            # Run custom pattern analysis
            custom_results = await self._run_custom_patterns(contract_code)
            audit_results["custom"] = custom_results
            audit_results["tools_used"].append("custom")
            audit_results["findings"].extend(custom_results.get("findings", []))

            # Calculate overall severity
            audit_results["severity"] = self._calculate_severity(
                audit_results["findings"]
            )

            # Clean up temporary file
            Path(temp_file).unlink(missing_ok=True)

            logger.info(f"Audit completed with severity: {audit_results['severity']}")
            return audit_results

        except Exception as e:
            logger.error(f"Audit failed: {e}")
            return {"status": "error", "error": str(e), "severity": "critical"}

    async def _run_slither(self, contract_file: str) -> Dict[str, Any]:
        """Run Slither static analysis on the contract."""
        try:
            cmd = ["slither", contract_file, "--json", "-"]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

            if result.returncode == 0:
                try:
                    slither_data = json.loads(result.stdout)
                    findings = []

                    for detector in slither_data.get("results", {}).get(
                        "detectors", []
                    ):
                        finding = {
                            "tool": "slither",
                            "severity": detector.get("impact", "unknown").lower(),
                            "confidence": detector.get("confidence", "unknown").lower(),
                            "description": detector.get("description", ""),
                            "elements": detector.get("elements", []),
                        }
                        findings.append(finding)

                    return {
                        "status": "success",
                        "findings": findings,
                        "raw_output": slither_data,
                    }
                except json.JSONDecodeError:
                    return {
                        "status": "error",
                        "error": "Failed to parse Slither JSON output",
                        "raw_output": result.stdout,
                    }
            else:
                return {
                    "status": "error",
                    "error": f"Slither failed with return code {result.returncode}",
                    "stderr": result.stderr,
                }

        except subprocess.TimeoutExpired:
            return {"status": "error", "error": "Slither analysis timed out"}
        except Exception as e:
            return {"status": "error", "error": f"Slither execution failed: {e}"}

    async def _run_mythril(self, contract_file: str) -> Dict[str, Any]:
        """Run Mythril symbolic execution analysis on the contract."""
        try:
            cmd = [
                "myth",
                "analyze",
                contract_file,
                "--execution-timeout",
                "60",
                "--solver-timeout",
                "30",
                "--max-depth",
                "10",
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

            findings = []

            # Parse Mythril output (simplified parsing)
            if "CRITICAL" in result.stdout:
                findings.append(
                    {
                        "tool": "mythril",
                        "severity": "critical",
                        "description": "Critical vulnerability detected by Mythril",
                        "details": result.stdout,
                    }
                )
            elif "HIGH" in result.stdout:
                findings.append(
                    {
                        "tool": "mythril",
                        "severity": "high",
                        "description": "High severity issue detected by Mythril",
                        "details": result.stdout,
                    }
                )

            return {
                "status": "success",
                "findings": findings,
                "raw_output": result.stdout,
            }

        except subprocess.TimeoutExpired:
            return {"status": "error", "error": "Mythril analysis timed out"}
        except Exception as e:
            return {"status": "error", "error": f"Mythril execution failed: {e}"}

    async def _run_custom_patterns(self, contract_code: str) -> Dict[str, Any]:
        """Run custom security pattern analysis."""
        findings = []

        # Check for common vulnerabilities
        vulnerability_patterns = {
            "reentrancy": {
                "pattern": r"\.call\(|\.transfer\(|\.send\(",
                "severity": "high",
                "description": "Potential reentrancy vulnerability detected",
            },
            "integer_overflow": {
                "pattern": r"(\+|\*|\-|\/)\s*\w+",
                "severity": "medium",
                "description": "Potential integer overflow/underflow",
            },
            "unchecked_call": {
                "pattern": r"\.call\([^)]*\)(?!\s*;)",
                "severity": "medium",
                "description": "Unchecked external call return value",
            },
            "tx_origin": {
                "pattern": r"tx\.origin",
                "severity": "medium",
                "description": "Use of tx.origin for authorization",
            },
            "block_timestamp": {
                "pattern": r"block\.timestamp",
                "severity": "low",
                "description": "Use of block.timestamp for randomness",
            },
        }

        import re

        for vuln_name, vuln_info in vulnerability_patterns.items():
            matches = re.findall(vuln_info["pattern"], contract_code)
            if matches:
                findings.append(
                    {
                        "tool": "custom",
                        "severity": vuln_info["severity"],
                        "description": vuln_info["description"],
                        "pattern": vuln_name,
                        "matches": len(matches),
                    }
                )

        # Check for best practices
        best_practices = {
            "has_nat_spec": {
                "pattern": r"/\*\*.*?\*/",
                "severity": "info",
                "description": "NatSpec documentation found",
            },
            "has_events": {
                "pattern": r"event\s+\w+",
                "severity": "info",
                "description": "Events defined for logging",
            },
            "has_modifiers": {
                "pattern": r"modifier\s+\w+",
                "severity": "info",
                "description": "Custom modifiers defined",
            },
            "uses_openzeppelin": {
                "pattern": r"@openzeppelin",
                "severity": "info",
                "description": "OpenZeppelin libraries imported",
            },
        }

        for practice_name, practice_info in best_practices.items():
            matches = re.findall(practice_info["pattern"], contract_code)
            if matches:
                findings.append(
                    {
                        "tool": "custom",
                        "severity": practice_info["severity"],
                        "description": practice_info["description"],
                        "pattern": practice_name,
                        "matches": len(matches),
                    }
                )

        return {"status": "success", "findings": findings}

    def _calculate_severity(self, findings: List[Dict[str, Any]]) -> str:
        """Calculate overall severity based on findings."""
        if not findings:
            return "low"

        # Calculate weighted severity score
        total_score = 0
        for finding in findings:
            severity = finding.get("severity", "info")
            weight = self.severity_weights.get(severity, 0)
            total_score += weight

        # Determine overall severity
        if total_score >= 20:
            return "critical"
        elif total_score >= 10:
            return "high"
        elif total_score >= 5:
            return "medium"
        else:
            return "low"

    async def debug_transaction(self, tx_hash: str, rpc_url: str) -> Dict[str, Any]:
        """
        Debug a transaction using EDB debugger.

        Args:
            tx_hash: Transaction hash to debug
            rpc_url: RPC URL for the network

        Returns:
            Dictionary containing debug results
        """
        if not self.tools_available["edb"]:
            return {"status": "error", "error": "EDB debugger not available"}

        try:
            cmd = ["edb", "--rpc-urls", rpc_url, "replay", tx_hash]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

            return {
                "status": "success",
                "tx_hash": tx_hash,
                "debug_output": result.stdout,
                "stderr": result.stderr,
            }

        except subprocess.TimeoutExpired:
            return {"status": "error", "error": "Debug session timed out"}
        except Exception as e:
            return {"status": "error", "error": f"Debug failed: {e}"}

    def get_audit_summary(self, audit_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a summary of audit results."""
        findings = audit_results.get("findings", [])

        summary = {
            "total_findings": len(findings),
            "severity_distribution": {},
            "tools_used": audit_results.get("tools_used", []),
            "overall_severity": audit_results.get("severity", "unknown"),
            "recommendations": [],
        }

        # Count findings by severity
        for finding in findings:
            severity = finding.get("severity", "unknown")
            summary["severity_distribution"][severity] = (
                summary["severity_distribution"].get(severity, 0) + 1
            )

        # Generate recommendations based on findings
        if summary["severity_distribution"].get("critical", 0) > 0:
            summary["recommendations"].append(
                "Address critical vulnerabilities immediately"
            )
        if summary["severity_distribution"].get("high", 0) > 0:
            summary["recommendations"].append("Review and fix high-severity issues")
        if summary["severity_distribution"].get("medium", 0) > 0:
            summary["recommendations"].append(
                "Consider addressing medium-severity issues"
            )

        return summary


# Example usage
async def main():
    """Example usage of the SmartContractAuditor."""
    auditor = SmartContractAuditor()

    # Example contract code
    contract_code = """
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

    try:
        audit_results = await auditor.audit(contract_code)
        summary = auditor.get_audit_summary(audit_results)

        print("Audit Results:")
        print(json.dumps(audit_results, indent=2))
        print("\nAudit Summary:")
        print(json.dumps(summary, indent=2))

    except Exception as e:
        print(f"Audit failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
