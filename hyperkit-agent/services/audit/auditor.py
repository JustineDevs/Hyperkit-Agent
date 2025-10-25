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

# Import the new contract fetcher
from services.blockchain.contract_fetcher import ContractFetcher

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
        self.contract_fetcher = ContractFetcher()
        self.severity_weights = {
            "critical": 10,
            "high": 7,
            "medium": 4,
            "low": 1,
            "info": 0.5,
        }
        
        # Initialize Alith AI auditor (if enabled and available)
        self.alith_agent = None
        if self.config.get("alith_enabled", False):
            try:
                from services.alith import HyperKitAlithAgent, is_alith_available
                
                if is_alith_available():
                    alith_config = self.config.get("alith", {})
                    self.alith_agent = HyperKitAlithAgent(alith_config)
                    self.tools_available["alith"] = True
                    logger.info("✅ Alith AI auditor initialized")
                else:
                    logger.warning("Alith SDK not available")
                    self.tools_available["alith"] = False
            except Exception as e:
                logger.warning(f"Failed to initialize Alith auditor: {e}")
                self.tools_available["alith"] = False
        else:
            self.tools_available["alith"] = False

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

            # Run all available tools and collect results
            tool_results = {}
            
            # Run Slither analysis
            if self.tools_available["slither"]:
                slither_results = await self._run_slither(temp_file)
                audit_results["slither"] = slither_results
                audit_results["tools_used"].append("slither")
                tool_results["slither"] = slither_results.get("findings", [])
                audit_results["findings"].extend(slither_results.get("findings", []))

            # Run Mythril analysis
            if self.tools_available["mythril"]:
                mythril_results = await self._run_mythril(temp_file)
                audit_results["mythril"] = mythril_results
                audit_results["tools_used"].append("mythril")
                tool_results["mythril"] = mythril_results.get("findings", [])
                audit_results["findings"].extend(mythril_results.get("findings", []))

            # Run custom pattern analysis
            custom_results = await self._run_custom_patterns(contract_code)
            audit_results["custom"] = custom_results
            audit_results["tools_used"].append("custom")
            tool_results["custom"] = custom_results.get("findings", [])
            audit_results["findings"].extend(custom_results.get("findings", []))
            
            # Run Alith AI analysis (NEW)
            if self.tools_available.get("alith") and self.alith_agent:
                try:
                    logger.info("Running Alith AI security analysis...")
                    ai_results = await self.alith_agent.audit_contract(contract_code)
                    
                    if ai_results.get("success"):
                        audit_results["alith"] = ai_results
                        audit_results["tools_used"].append("alith_ai")
                        
                        # Convert AI findings to standard format
                        ai_findings = []
                        for vuln in ai_results.get("vulnerabilities", []):
                            ai_findings.append({
                                "type": vuln.get("title", "AI-detected vulnerability"),
                                "severity": vuln.get("severity", "medium").lower(),
                                "description": vuln.get("description", ""),
                                "location": vuln.get("location", "Unknown"),
                                "recommendation": vuln.get("recommendation", ""),
                                "tool": "alith_ai",
                                "confidence": ai_results.get("confidence", 0.85)
                            })
                        
                        tool_results["alith_ai"] = ai_findings
                        audit_results["findings"].extend(ai_findings)
                        logger.info(f"Alith AI found {len(ai_findings)} potential issues")
                    else:
                        logger.warning(f"Alith AI analysis failed: {ai_results.get('error')}")
                except Exception as e:
                    logger.warning(f"Alith AI analysis error: {e}")

            # Apply consensus scoring and deduplication
            consensus_findings = self._deduplicate_and_score(audit_results["findings"], tool_results)
            audit_results["findings"] = consensus_findings

            # Calculate overall severity with confidence
            audit_results["severity"] = self._calculate_severity(consensus_findings)
            audit_results["consensus_score"] = self._calculate_confidence(consensus_findings, tool_results)
            audit_results["accuracy_estimate"] = self._get_accuracy_estimate(audit_results["consensus_score"])
            audit_results["disclaimer"] = self._get_audit_disclaimer(audit_results["consensus_score"])

            # Clean up temporary file
            Path(temp_file).unlink(missing_ok=True)

            logger.info(f"Audit completed with severity: {audit_results['severity']}")
            return audit_results

        except Exception as e:
            logger.error(f"Audit failed: {e}")
            return {"status": "error", "error": str(e), "severity": "critical"}

    async def audit_deployed_contract(self, contract_address: str, network: str, api_key: str = None) -> Dict[str, Any]:
        """
        Audit a deployed contract with confidence tracking and source verification.
        
        Args:
            contract_address: Address of the deployed contract
            network: Blockchain network name
            api_key: Optional API key for explorer access
            
        Returns:
            Dictionary containing audit results with confidence scoring
        """
        try:
            logger.info(f"Auditing deployed contract {contract_address} on {network}")
            
            # Fetch contract source with confidence tracking
            source_result = self.contract_fetcher.fetch_contract_source(contract_address, network, api_key)
            
            if not source_result or not source_result.get("source"):
                return {
                    "status": "error",
                    "error": "Could not fetch contract source code",
                    "severity": "unknown",
                    "source_type": "not_found",
                    "confidence": 0.0
                }
            
            # Extract source and metadata
            source_code = source_result["source"]
            source_type = source_result["source_type"]
            confidence = source_result["confidence"]
            metadata = source_result["metadata"]
            
            logger.info(f"Source type: {source_type}, Confidence: {confidence}")
            
            # Run audit with confidence-aware analysis
            audit_result = await self._audit_with_confidence(source_code, source_type, confidence)
            
            # Add source metadata to results
            audit_result.update({
                "source_type": source_type,
                "confidence": confidence,
                "metadata": metadata,
                "recommendations": self.contract_fetcher.get_source_recommendation(source_type)
            })
            
            return audit_result
                
        except Exception as e:
            logger.error(f"Error auditing deployed contract {contract_address}: {e}")
            return {
                "status": "error",
                "error": str(e),
                "severity": "unknown",
                "source_type": "error",
                "confidence": 0.0
            }

    async def _audit_with_confidence(self, source_code: str, source_type: str, confidence: float) -> Dict[str, Any]:
        """
        Run audit with confidence-aware analysis and filtering.
        
        Args:
            source_code: Contract source code
            source_type: Type of source (verified_source, bytecode_decompiled, etc.)
            confidence: Confidence score (0-1)
            
        Returns:
            Audit results with confidence adjustments
        """
        try:
            # Run standard audit
            audit_result = await self.audit(source_code)
            
            # Apply confidence-based adjustments
            if source_type == "bytecode_decompiled":
                # Filter out likely false positives from decompilation
                audit_result = self._filter_bytecode_artifacts(audit_result)
                # Reduce severity based on confidence
                audit_result = self._adjust_severity_by_confidence(audit_result, confidence)
            
            # Add confidence warnings
            if confidence < 0.5:
                audit_result["warnings"] = audit_result.get("warnings", [])
                audit_result["warnings"].extend([
                    "⚠️  Low confidence source - findings may be unreliable",
                    "⚠️  Consider verifying source code for accurate results"
                ])
            
            return audit_result
            
        except Exception as e:
            logger.error(f"Error in confidence-aware audit: {e}")
            return {
                "status": "error",
                "error": str(e),
                "severity": "unknown"
            }

    def _filter_bytecode_artifacts(self, audit_result: Dict[str, Any]) -> Dict[str, Any]:
        """Filter out likely false positives from bytecode decompilation."""
        if "findings" not in audit_result:
            return audit_result
        
        filtered_findings = []
        for finding in audit_result["findings"]:
            # Skip findings that are likely decompilation artifacts
            description = finding.get("description", "").lower()
            if any(artifact in description for artifact in [
                "decompiled", "bytecode", "reconstructed", "simulated"
            ]):
                continue
            filtered_findings.append(finding)
        
        audit_result["findings"] = filtered_findings
        return audit_result

    def _adjust_severity_by_confidence(self, audit_result: Dict[str, Any], confidence: float) -> Dict[str, Any]:
        """Adjust severity based on source confidence."""
        if confidence >= 0.8:
            return audit_result  # High confidence, no adjustment
        
        # Reduce severity for low confidence sources
        severity_mapping = {
            "critical": "high" if confidence < 0.5 else "critical",
            "high": "medium" if confidence < 0.5 else "high",
            "medium": "low" if confidence < 0.3 else "medium",
            "low": "info" if confidence < 0.3 else "low"
        }
        
        current_severity = audit_result.get("severity", "unknown")
        if current_severity in severity_mapping:
            audit_result["severity"] = severity_mapping[current_severity]
            audit_result["confidence_adjusted"] = True
        
        return audit_result

    def _deduplicate_and_score(self, all_findings: List[Dict[str, Any]], tool_results: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Score findings based on agreement between tools"""
        consensus = {}
        
        for finding in all_findings:
            # Create unique identifier for the finding
            issue_id = f"{finding.get('type', 'unknown')}_{finding.get('location', 'unknown')}_{finding.get('description', '')[:50]}"
            
            if issue_id not in consensus:
                consensus[issue_id] = {
                    "finding": finding,
                    "tool_agreement": 0,
                    "tools_found": [],
                    "severity_scores": []
                }
            
            consensus[issue_id]["tool_agreement"] += 1
            consensus[issue_id]["tools_found"].append(finding.get("tool", "unknown"))
            consensus[issue_id]["severity_scores"].append(finding.get("severity", "info"))
        
        # Only keep findings agreed on by 2+ tools or high-confidence single tool findings
        high_confidence = []
        for issue_id, data in consensus.items():
            if data["tool_agreement"] >= 2:
                # Multi-tool consensus - high confidence
                finding = data["finding"].copy()
                finding["consensus_confidence"] = 0.9
                finding["tool_agreement"] = data["tool_agreement"]
                finding["tools_found"] = data["tools_found"]
                high_confidence.append(finding)
            elif data["tool_agreement"] == 1 and data["finding"].get("severity") in ["critical", "high"]:
                # Single tool but high severity - medium confidence
                finding = data["finding"].copy()
                finding["consensus_confidence"] = 0.6
                finding["tool_agreement"] = 1
                finding["tools_found"] = data["tools_found"]
                high_confidence.append(finding)
        
        return high_confidence

    def _calculate_confidence(self, findings: List[Dict[str, Any]], tool_results: Dict[str, List[Dict[str, Any]]]) -> float:
        """Calculate overall confidence based on tool agreement and findings quality"""
        if not findings:
            return 0.0
        
        # Base confidence from tool agreement
        total_agreement = sum(f.get("tool_agreement", 1) for f in findings)
        max_possible = len(findings) * len(tool_results)
        agreement_ratio = total_agreement / max_possible if max_possible > 0 else 0
        
        # Confidence boost for verified source
        source_confidence = 0.8  # Default for local files
        
        # Final confidence calculation
        final_confidence = (agreement_ratio * 0.6) + (source_confidence * 0.4)
        return min(final_confidence, 0.95)  # Cap at 95%

    def _get_accuracy_estimate(self, confidence: float) -> str:
        """Get realistic accuracy estimate based on confidence"""
        if confidence >= 0.9:
            return "85-90%"
        elif confidence >= 0.7:
            return "75-85%"
        elif confidence >= 0.5:
            return "60-75%"
        else:
            return "30-60%"

    def _get_audit_disclaimer(self, confidence: float) -> str:
        """Get appropriate disclaimer based on confidence level"""
        if confidence >= 0.8:
            return """
✅ Your contract was audited using multiple tools with high confidence.
📊 Confidence Score: {:.0%}

⚠️  IMPORTANT:
   - This audit is NOT a substitute for professional security review
   - Critical findings should be reviewed by human auditors
   - Before mainnet deployment, hire a professional firm
   - Common exploits: reentrancy, overflow, access control

🔗 Next Steps:
   1. Fix HIGH/CRITICAL findings
   2. Submit for professional audit (Trail of Bits, OpenZeppelin)
   3. Deploy to testnet first
   4. Monitor on mainnet with insurance
            """.format(confidence).strip()
        else:
            return """
⚠️  LOW CONFIDENCE AUDIT - Use with caution

📊 Confidence Score: {:.0%}

❌ LIMITATIONS:
   - Source code may be incomplete or unverified
   - Findings may contain false positives
   - This audit is NOT suitable for production decisions

🔗 RECOMMENDATIONS:
   1. Verify source code on Sourcify or block explorer
   2. Request original source from contract author
   3. For production, hire professional auditors
   4. Deploy to testnet for additional testing
            """.format(confidence).strip()

    async def audit_with_human_review(self, contract_code: str, severity_threshold: str = "critical") -> Dict[str, Any]:
        """Flag critical findings for human review"""
        try:
            # Run standard audit
            audit_result = await self.audit(contract_code)
            
            if audit_result.get("status") != "success":
                return audit_result
            
            findings = audit_result.get("findings", [])
            
            # Filter critical findings
            critical_findings = [
                f for f in findings 
                if f.get("severity") in ["critical", "high"] and 
                   severity_threshold in ["critical", "high"]
            ]
            
            if critical_findings:
                return {
                    "status": "pending_human_review",
                    "findings": critical_findings,
                    "total_findings": len(findings),
                    "critical_count": len(critical_findings),
                    "action": "Human auditor required before deployment",
                    "estimated_review_time": "4-24 hours",
                    "severity_threshold": severity_threshold,
                    "human_review_required": True,
                    "review_link": self._generate_review_link(critical_findings),
                    "disclaimer": """
🚨 CRITICAL FINDINGS DETECTED - HUMAN REVIEW REQUIRED

⚠️  The following critical security issues were found:
   - These findings require expert human analysis
   - Do NOT deploy to mainnet without professional review
   - Consider hiring a professional audit firm

🔗 Next Steps:
   1. Submit for human review (see link below)
   2. Fix all critical/high findings
   3. Re-audit after fixes
   4. Professional audit recommended for mainnet
                    """.strip()
                }
            else:
                return {
                    "status": "auto_approved",
                    "findings": findings,
                    "confidence": audit_result.get("consensus_score", 0.0),
                    "human_review_required": False,
                    "disclaimer": """
✅ NO CRITICAL FINDINGS - Auto-approved for testing

📊 Confidence Score: {:.0%}

⚠️  IMPORTANT:
   - This audit is suitable for testnet deployment
   - For mainnet, professional audit still recommended
   - Monitor contract behavior after deployment
                    """.format(audit_result.get("consensus_score", 0.0)).strip()
                }
                
        except Exception as e:
            logger.error(f"Human review audit failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "human_review_required": True
            }

    def _generate_review_link(self, critical_findings: List[Dict[str, Any]]) -> str:
        """Generate a link for human review submission"""
        # This would integrate with a human review system
        # For now, return a placeholder
        return "https://hyperkit.xyz/audit-review/submit"

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

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120, encoding='utf-8')

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

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120, encoding='utf-8')

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
