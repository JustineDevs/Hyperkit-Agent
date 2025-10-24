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

    async def audit_deployed_contract(self, contract_address: str, rpc_url: str) -> Dict[str, Any]:
        """
        Audit a deployed contract by fetching its source code and analyzing it.
        
        Args:
            contract_address: Address of the deployed contract
            rpc_url: RPC URL for the blockchain network
            
        Returns:
            Dictionary containing audit results
        """
        try:
            logger.info(f"Auditing deployed contract: {contract_address}")
            
            # Try to fetch source code from explorer
            source_code = await self._fetch_contract_source(contract_address, rpc_url)
            
            if source_code:
                # Audit the fetched source code
                return await self.audit(source_code)
            else:
                # If no source code available, perform bytecode analysis
                return await self._audit_bytecode(contract_address, rpc_url)
                
        except Exception as e:
            logger.error(f"Deployed contract audit failed: {e}")
            return {"status": "error", "error": str(e), "severity": "critical"}

    async def _fetch_contract_source(self, contract_address: str, rpc_url: str) -> Optional[str]:
        """Fetch contract source code from blockchain explorer."""
        try:
            # This would integrate with explorer APIs to fetch verified source code
            # For now, return None to indicate no source code available
            return None
        except Exception as e:
            logger.warning(f"Failed to fetch source code: {e}")
            return None

    async def _audit_bytecode(self, contract_address: str, rpc_url: str) -> Dict[str, Any]:
        """Perform bytecode analysis when source code is not available."""
        try:
            # Basic bytecode analysis for common vulnerabilities
            findings = []
            
            # Add basic findings for deployed contracts without source
            findings.append({
                "tool": "bytecode_analysis",
                "severity": "medium",
                "description": "Contract source code not available for analysis",
                "confidence": "medium"
            })
            
            return {
                "status": "success",
                "findings": findings,
                "severity": "medium",
                "message": "Limited analysis due to unavailable source code"
            }
            
        except Exception as e:
            logger.error(f"Bytecode analysis failed: {e}")
            return {"status": "error", "error": str(e), "severity": "critical"}

    async def _run_slither(self, contract_file: str) -> Dict[str, Any]:
        """Run Slither static analysis on the contract."""
        try:
            # Use more comprehensive Slither options
            cmd = [
                "slither", 
                contract_file, 
                "--json", "-",
                "--disable-color",
                "--print-json-summary"
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

            findings = []
            
            # Parse both stdout and stderr for findings
            output = result.stdout + result.stderr
            
            # Look for specific vulnerability patterns in output
            vulnerability_patterns = {
                "reentrancy": {
                    "patterns": ["reentrancy", "Reentrancy", "REENTRANCY"],
                    "severity": "high",
                    "description": "Reentrancy vulnerability detected"
                },
                "integer_overflow": {
                    "patterns": ["integer-overflow", "IntegerOverflow", "INTEGER_OVERFLOW"],
                    "severity": "medium", 
                    "description": "Integer overflow/underflow vulnerability"
                },
                "unchecked_call": {
                    "patterns": ["unchecked-transfer", "UncheckedTransfer", "UNCHECKED_TRANSFER"],
                    "severity": "medium",
                    "description": "Unchecked external call return value"
                },
                "tx_origin": {
                    "patterns": ["tx-origin", "TxOrigin", "TX_ORIGIN"],
                    "severity": "medium",
                    "description": "Use of tx.origin for authorization"
                },
                "block_timestamp": {
                    "patterns": ["timestamp", "Timestamp", "TIMESTAMP"],
                    "severity": "low",
                    "description": "Use of block.timestamp for randomness"
                },
                "suicidal": {
                    "patterns": ["suicidal", "Suicidal", "SUICIDAL"],
                    "severity": "critical",
                    "description": "Suicidal contract vulnerability"
                },
                "delegatecall": {
                    "patterns": ["delegatecall", "DelegateCall", "DELEGATECALL"],
                    "severity": "high",
                    "description": "Unsafe delegatecall usage"
                }
            }

            for vuln_name, vuln_info in vulnerability_patterns.items():
                for pattern in vuln_info["patterns"]:
                    if pattern in output:
                        findings.append({
                            "tool": "slither",
                            "severity": vuln_info["severity"],
                            "confidence": "high",
                            "description": vuln_info["description"],
                            "pattern": vuln_name,
                            "details": f"Found pattern: {pattern}"
                        })
                        break  # Only add once per vulnerability type

            # Also try to parse JSON if available
            try:
                slither_data = json.loads(result.stdout)
                for detector in slither_data.get("results", {}).get("detectors", []):
                    finding = {
                        "tool": "slither",
                        "severity": detector.get("impact", "unknown").lower(),
                        "confidence": detector.get("confidence", "unknown").lower(),
                        "description": detector.get("description", ""),
                        "elements": detector.get("elements", []),
                    }
                    findings.append(finding)
            except json.JSONDecodeError:
                pass  # Continue with pattern-based detection

            return {
                "status": "success",
                "findings": findings,
                "raw_output": output,
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

        # Enhanced vulnerability patterns with more comprehensive detection
        vulnerability_patterns = {
            "reentrancy": {
                "patterns": [
                    r"\.call\s*\(",
                    r"\.transfer\s*\(",
                    r"\.send\s*\(",
                    r"external\s+.*\s+payable",
                    r"function\s+\w+.*external.*payable"
                ],
                "severity": "high",
                "description": "Potential reentrancy vulnerability detected",
            },
            "integer_overflow": {
                "patterns": [
                    r"(\+|\*|\-|\/)\s*\w+",
                    r"uint\d*\s*\+\s*uint\d*",
                    r"uint\d*\s*\*\s*uint\d*",
                    r"uint\d*\s*-\s*uint\d*"
                ],
                "severity": "medium",
                "description": "Potential integer overflow/underflow",
            },
            "unchecked_call": {
                "patterns": [
                    r"\.call\([^)]*\)(?!\s*;)",
                    r"\.transfer\([^)]*\)(?!\s*;)",
                    r"\.send\([^)]*\)(?!\s*;)",
                    r"external\s+.*\s+call"
                ],
                "severity": "medium",
                "description": "Unchecked external call return value",
            },
            "tx_origin": {
                "patterns": [
                    r"tx\.origin",
                    r"require\s*\(\s*tx\.origin",
                    r"if\s*\(\s*tx\.origin"
                ],
                "severity": "medium",
                "description": "Use of tx.origin for authorization",
            },
            "block_timestamp": {
                "patterns": [
                    r"block\.timestamp",
                    r"now\s*[+\-*/]",
                    r"block\.timestamp\s*[+\-*/]"
                ],
                "severity": "low",
                "description": "Use of block.timestamp for randomness",
            },
            "suicidal": {
                "patterns": [
                    r"selfdestruct\s*\(",
                    r"suicide\s*\(",
                    r"\.kill\s*\(",
                    r"function\s+.*suicide"
                ],
                "severity": "critical",
                "description": "Suicidal contract vulnerability",
            },
            "delegatecall": {
                "patterns": [
                    r"\.delegatecall\s*\(",
                    r"assembly\s*\{.*delegatecall",
                    r"function\s+.*delegatecall"
                ],
                "severity": "high",
                "description": "Unsafe delegatecall usage",
            },
            "uninitialized_storage": {
                "patterns": [
                    r"mapping\s*\(\s*address\s*=>\s*uint256\s*\)\s+\w+;",
                    r"struct\s+\w+\s*\{[^}]*\}\s*\w+;"
                ],
                "severity": "medium",
                "description": "Uninitialized storage variables",
            },
            "unprotected_ether": {
                "patterns": [
                    r"function\s+\w+.*payable.*\{[^}]*\w+\.transfer",
                    r"function\s+\w+.*payable.*\{[^}]*\w+\.send",
                    r"function\s+\w+.*payable.*\{[^}]*\w+\.call"
                ],
                "severity": "high",
                "description": "Unprotected ether withdrawal",
            },
            "front_running": {
                "patterns": [
                    r"block\.timestamp\s*[+\-]\s*\d+",
                    r"block\.number\s*[+\-]\s*\d+",
                    r"now\s*[+\-]\s*\d+"
                ],
                "severity": "medium",
                "description": "Potential front-running vulnerability",
            },
            "gas_limit": {
                "patterns": [
                    r"for\s*\([^)]*\)\s*\{[^}]*\w+\.transfer",
                    r"for\s*\([^)]*\)\s*\{[^}]*\w+\.send",
                    r"for\s*\([^)]*\)\s*\{[^}]*\w+\.call"
                ],
                "severity": "medium",
                "description": "Potential gas limit vulnerability",
            }
        }

        import re

        for vuln_name, vuln_info in vulnerability_patterns.items():
            total_matches = 0
            matched_patterns = []
            
            for pattern in vuln_info["patterns"]:
                matches = re.findall(pattern, contract_code, re.IGNORECASE | re.MULTILINE)
                if matches:
                    total_matches += len(matches)
                    matched_patterns.append(pattern)
            
            if total_matches > 0:
                findings.append(
                    {
                        "tool": "custom",
                        "severity": vuln_info["severity"],
                        "description": vuln_info["description"],
                        "pattern": vuln_name,
                        "matches": total_matches,
                        "matched_patterns": matched_patterns,
                        "confidence": "high" if total_matches > 1 else "medium"
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

        # Calculate weighted severity score with confidence weighting
        total_score = 0
        critical_count = 0
        high_count = 0
        medium_count = 0
        
        for finding in findings:
            severity = finding.get("severity", "info")
            confidence = finding.get("confidence", "medium")
            matches = finding.get("matches", 1)
            
            # Base weight from severity
            base_weight = self.severity_weights.get(severity, 0)
            
            # Confidence multiplier
            confidence_multiplier = {
                "high": 1.5,
                "medium": 1.0,
                "low": 0.5
            }.get(confidence, 1.0)
            
            # Match count multiplier (more matches = higher score)
            match_multiplier = min(matches * 0.5, 3.0)  # Cap at 3x
            
            # Calculate final weight
            final_weight = base_weight * confidence_multiplier * match_multiplier
            total_score += final_weight
            
            # Count by severity for additional logic
            if severity == "critical":
                critical_count += 1
            elif severity == "high":
                high_count += 1
            elif severity == "medium":
                medium_count += 1

        # Enhanced severity determination
        if critical_count > 0 or total_score >= 25:
            return "critical"
        elif high_count >= 2 or total_score >= 15:
            return "high"
        elif high_count >= 1 or medium_count >= 3 or total_score >= 8:
            return "medium"
        elif total_score >= 3:
            return "low"
        else:
            return "info"

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
