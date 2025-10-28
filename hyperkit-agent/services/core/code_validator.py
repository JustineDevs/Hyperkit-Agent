"""
Code Validation and Security Scanning Service
Comprehensive validation and security analysis for AI-generated code
"""

import re
import ast
import subprocess
import tempfile
import os
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from .logging_system import logger, LogCategory, log_info, log_error, log_warning

class CodeValidator:
    """
    Comprehensive code validation and security scanning service
    Validates AI-generated code for security, quality, and compliance
    """
    
    def __init__(self):
        self.security_patterns = self._load_security_patterns()
        self.quality_rules = self._load_quality_rules()
        self.solidity_patterns = self._load_solidity_patterns()
        
    def _load_security_patterns(self) -> Dict[str, List[str]]:
        """Load security vulnerability patterns"""
        return {
            "reentrancy": [
                r"\.call\s*\(",
                r"\.send\s*\(",
                r"\.transfer\s*\(",
                r"external\s+.*\s+payable",
                r"msg\.sender\.call\s*\("
            ],
            "integer_overflow": [
                r"\+.*\+",
                r"\*.*\*",
                r"uint.*\+.*uint",
                r"int.*\+.*int"
            ],
            "timestamp_dependency": [
                r"block\.timestamp",
                r"now\s*[<>=]",
                r"block\.timestamp\s*[<>=]"
            ],
            "tx_origin": [
                r"tx\.origin",
                r"require\s*\(\s*tx\.origin"
            ],
            "unchecked_call": [
                r"\.call\s*\([^)]*\)\s*;",
                r"\.send\s*\([^)]*\)\s*;",
                r"\.transfer\s*\([^)]*\)\s*;"
            ],
            "uninitialized_storage": [
                r"mapping\s*\(\s*[^)]*\)\s+[a-zA-Z_][a-zA-Z0-9_]*\s*;",
                r"struct\s+[a-zA-Z_][a-zA-Z0-9_]*\s*{[^}]*}\s*[a-zA-Z_][a-zA-Z0-9_]*\s*;"
            ],
            "suicidal": [
                r"selfdestruct\s*\(",
                r"suicide\s*\("
            ],
            "gas_limit": [
                r"for\s*\([^)]*\)\s*{[^}]*}",
                r"while\s*\([^)]*\)\s*{[^}]*}",
                r"\.length\s*[<>=]"
            ]
        }
    
    def _load_quality_rules(self) -> Dict[str, List[str]]:
        """Load code quality rules"""
        return {
            "naming_conventions": [
                r"function\s+[a-z][a-zA-Z0-9_]*\s*\(",
                r"contract\s+[A-Z][a-zA-Z0-9_]*",
                r"variable\s+[a-z][a-zA-Z0-9_]*"
            ],
            "documentation": [
                r"\/\*\*.*\*\/",
                r"\/\/.*NOTE"
            ],
            "error_handling": [
                r"require\s*\(",
                r"assert\s*\(",
                r"revert\s*\(",
                r"if\s*\([^)]*\)\s*revert"
            ],
            "gas_optimization": [
                r"uint256\s+[a-zA-Z_][a-zA-Z0-9_]*",
                r"mapping\s*\(\s*[^)]*\)\s+[a-zA-Z_][a-zA-Z0-9_]*",
                r"struct\s+[a-zA-Z_][a-zA-Z0-9_]*"
            ]
        }
    
    def _load_solidity_patterns(self) -> Dict[str, List[str]]:
        """Load Solidity-specific patterns"""
        return {
            "pragma": [
                r"pragma\s+solidity\s+[^;]+;",
                r"pragma\s+experimental\s+[^;]+;"
            ],
            "imports": [
                r"import\s+[\"'][^\"']+[\"'];",
                r"import\s+{[^}]+}\s+from\s+[\"'][^\"']+[\"'];"
            ],
            "contract_structure": [
                r"contract\s+[A-Z][a-zA-Z0-9_]*\s*{",
                r"interface\s+[A-Z][a-zA-Z0-9_]*\s*{",
                r"library\s+[A-Z][a-zA-Z0-9_]*\s*{"
            ],
            "function_declarations": [
                r"function\s+[a-zA-Z_][a-zA-Z0-9_]*\s*\(",
                r"modifier\s+[a-zA-Z_][a-zA-Z0-9_]*\s*\(",
                r"event\s+[A-Z][a-zA-Z0-9_]*\s*\("
            ]
        }
    
    async def validate_code(self, code: str, language: str = "solidity") -> Dict[str, Any]:
        """Comprehensive code validation"""
        try:
            log_info(LogCategory.SECURITY, f"Starting code validation for {language}")
            
            validation_result = {
                "status": "success",
                "language": language,
                "security_issues": [],
                "quality_issues": [],
                "compliance_issues": [],
                "recommendations": [],
                "score": 100
            }
            
            # Security validation
            security_result = await self._validate_security(code, language)
            validation_result["security_issues"] = security_result["issues"]
            validation_result["score"] -= security_result["penalty"]
            
            # Quality validation
            quality_result = await self._validate_quality(code, language)
            validation_result["quality_issues"] = quality_result["issues"]
            validation_result["score"] -= quality_result["penalty"]
            
            # Compliance validation
            compliance_result = await self._validate_compliance(code, language)
            validation_result["compliance_issues"] = compliance_result["issues"]
            validation_result["score"] -= compliance_result["penalty"]
            
            # Generate recommendations
            validation_result["recommendations"] = self._generate_recommendations(validation_result)
            
            # Ensure score doesn't go below 0
            validation_result["score"] = max(0, validation_result["score"])
            
            log_info(LogCategory.SECURITY, f"Code validation completed. Score: {validation_result['score']}")
            return validation_result
            
        except Exception as e:
            log_error(LogCategory.SECURITY, "Code validation failed", e)
            return {
                "status": "error",
                "error": str(e),
                "message": "Code validation failed"
            }
    
    async def _validate_security(self, code: str, language: str) -> Dict[str, Any]:
        """Validate code for security vulnerabilities"""
        issues = []
        penalty = 0
        
        if language.lower() == "solidity":
            for vuln_type, patterns in self.security_patterns.items():
                for pattern in patterns:
                    matches = re.finditer(pattern, code, re.IGNORECASE | re.MULTILINE)
                    for match in matches:
                        line_num = code[:match.start()].count('\n') + 1
                        severity = self._get_severity(vuln_type)
                        
                        issue = {
                            "type": vuln_type,
                            "severity": severity,
                            "line": line_num,
                            "code": match.group().strip(),
                            "description": self._get_vulnerability_description(vuln_type),
                            "recommendation": self._get_vulnerability_recommendation(vuln_type)
                        }
                        issues.append(issue)
                        
                        # Calculate penalty based on severity
                        if severity == "CRITICAL":
                            penalty += 20
                        elif severity == "HIGH":
                            penalty += 15
                        elif severity == "MEDIUM":
                            penalty += 10
                        elif severity == "LOW":
                            penalty += 5
        
        return {"issues": issues, "penalty": penalty}
    
    async def _validate_quality(self, code: str, language: str) -> Dict[str, Any]:
        """Validate code quality"""
        issues = []
        penalty = 0
        
        if language.lower() == "solidity":
            # Check for proper documentation
            if not re.search(r"\/\*\*.*\*\/", code):
                issues.append({
                    "type": "missing_documentation",
                    "severity": "MEDIUM",
                    "description": "Contract lacks proper documentation",
                    "recommendation": "Add NatSpec documentation for all public functions"
                })
                penalty += 5
            
            # Check for error handling
            if not re.search(r"require\s*\(|assert\s*\(|revert\s*\(", code):
                issues.append({
                    "type": "insufficient_error_handling",
                    "severity": "HIGH",
                    "description": "Contract lacks proper error handling",
                    "recommendation": "Add require/assert statements for input validation"
                })
                penalty += 10
            
            # Check for gas optimization opportunities
            if re.search(r"for\s*\([^)]*\)\s*{[^}]*}", code):
                issues.append({
                    "type": "gas_optimization",
                    "severity": "LOW",
                    "description": "Consider gas optimization for loops",
                    "recommendation": "Use assembly or optimize loop operations"
                })
                penalty += 2
        
        return {"issues": issues, "penalty": penalty}
    
    async def _validate_compliance(self, code: str, language: str) -> Dict[str, Any]:
        """Validate code compliance with standards"""
        issues = []
        penalty = 0
        
        if language.lower() == "solidity":
            # Check for SPDX license identifier
            if not re.search(r"SPDX-License-Identifier", code):
                issues.append({
                    "type": "missing_license",
                    "severity": "LOW",
                    "description": "Missing SPDX license identifier",
                    "recommendation": "Add SPDX-License-Identifier comment at the top"
                })
                penalty += 2
            
            # Check for pragma version
            if not re.search(r"pragma\s+solidity", code):
                issues.append({
                    "type": "missing_pragma",
                    "severity": "HIGH",
                    "description": "Missing pragma solidity version",
                    "recommendation": "Add pragma solidity version declaration"
                })
                penalty += 10
            
            # Check for proper contract structure
            if not re.search(r"contract\s+[A-Z]", code):
                issues.append({
                    "type": "invalid_contract_structure",
                    "severity": "HIGH",
                    "description": "Invalid contract declaration",
                    "recommendation": "Use proper contract naming convention (PascalCase)"
                })
                penalty += 15
        
        return {"issues": issues, "penalty": penalty}
    
    def _get_severity(self, vuln_type: str) -> str:
        """Get severity level for vulnerability type"""
        severity_map = {
            "reentrancy": "CRITICAL",
            "integer_overflow": "HIGH",
            "timestamp_dependency": "MEDIUM",
            "tx_origin": "HIGH",
            "unchecked_call": "HIGH",
            "uninitialized_storage": "MEDIUM",
            "suicidal": "CRITICAL",
            "gas_limit": "LOW"
        }
        return severity_map.get(vuln_type, "MEDIUM")
    
    def _get_vulnerability_description(self, vuln_type: str) -> str:
        """Get description for vulnerability type"""
        descriptions = {
            "reentrancy": "Potential reentrancy vulnerability detected",
            "integer_overflow": "Potential integer overflow/underflow",
            "timestamp_dependency": "Dependency on block.timestamp may be manipulated",
            "tx_origin": "Use of tx.origin instead of msg.sender",
            "unchecked_call": "Unchecked external call without proper validation",
            "uninitialized_storage": "Uninitialized storage variable",
            "suicidal": "Self-destruct function detected",
            "gas_limit": "Potential gas limit issues in loops"
        }
        return descriptions.get(vuln_type, "Security issue detected")
    
    def _get_vulnerability_recommendation(self, vuln_type: str) -> str:
        """Get recommendation for vulnerability type"""
        recommendations = {
            "reentrancy": "Use checks-effects-interactions pattern and reentrancy guards",
            "integer_overflow": "Use SafeMath library or Solidity 0.8+ built-in checks",
            "timestamp_dependency": "Avoid using block.timestamp for critical logic",
            "tx_origin": "Use msg.sender instead of tx.origin for authentication",
            "unchecked_call": "Check return values of external calls",
            "uninitialized_storage": "Initialize all storage variables",
            "suicidal": "Remove or restrict self-destruct functionality",
            "gas_limit": "Optimize loops or use pagination"
        }
        return recommendations.get(vuln_type, "Review and fix the security issue")
    
    def _generate_recommendations(self, validation_result: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on validation results"""
        recommendations = []
        
        # Security recommendations
        if validation_result["security_issues"]:
            recommendations.append("Address all security vulnerabilities before deployment")
            
            critical_issues = [issue for issue in validation_result["security_issues"] 
                             if issue["severity"] == "CRITICAL"]
            if critical_issues:
                recommendations.append("CRITICAL: Fix all critical security issues immediately")
        
        # Quality recommendations
        if validation_result["quality_issues"]:
            recommendations.append("Improve code quality and documentation")
        
        # Compliance recommendations
        if validation_result["compliance_issues"]:
            recommendations.append("Ensure compliance with Solidity standards")
        
        # General recommendations
        if validation_result["score"] < 80:
            recommendations.append("Overall code quality needs improvement")
        elif validation_result["score"] < 60:
            recommendations.append("Code requires significant improvements before deployment")
        
        return recommendations
    
    async def scan_with_slither(self, code: str) -> Dict[str, Any]:
        """Scan code using Slither static analysis"""
        try:
            log_info(LogCategory.SECURITY, "Starting Slither security scan")
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.sol', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            try:
                # Run Slither
                result = subprocess.run(
                    ['slither', temp_file, '--json', '-'],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0:
                    # Parse Slither output
                    slither_results = json.loads(result.stdout) if result.stdout else {}
                    
                    return {
                        "status": "success",
                        "tool": "slither",
                        "results": slither_results,
                        "vulnerabilities": slither_results.get("results", {}).get("detectors", [])
                    }
                else:
                    log_warning(LogCategory.SECURITY, f"Slither scan failed: {result.stderr}")
                    return {
                        "status": "error",
                        "tool": "slither",
                        "error": result.stderr,
                        "message": "Slither scan failed"
                    }
                    
            finally:
                # Clean up temporary file
                os.unlink(temp_file)
                
        except subprocess.TimeoutExpired:
            log_error(LogCategory.SECURITY, "Slither scan timed out")
            return {
                "status": "error",
                "tool": "slither",
                "error": "Scan timed out",
                "message": "Slither scan timed out"
            }
        except Exception as e:
            log_error(LogCategory.SECURITY, "Slither scan failed", e)
            return {
                "status": "error",
                "tool": "slither",
                "error": str(e),
                "message": "Slither scan failed"
            }
    
    async def comprehensive_scan(self, code: str, language: str = "solidity") -> Dict[str, Any]:
        """Perform comprehensive security and quality scan"""
        try:
            log_info(LogCategory.SECURITY, f"Starting comprehensive scan for {language}")
            
            # Basic validation
            validation_result = await self.validate_code(code, language)
            
            # Slither scan (if available)
            slither_result = None
            try:
                slither_result = await self.scan_with_slither(code)
            except Exception as e:
                log_warning(LogCategory.SECURITY, f"Slither not available: {e}")
            
            # Combine results
            comprehensive_result = {
                "status": "success",
                "language": language,
                "validation": validation_result,
                "slither_scan": slither_result,
                "overall_score": validation_result.get("score", 0),
                "recommendations": validation_result.get("recommendations", [])
            }
            
            # Add Slither vulnerabilities if available
            if slither_result and slither_result.get("status") == "success":
                slither_vulns = slither_result.get("vulnerabilities", [])
                comprehensive_result["slither_vulnerabilities"] = slither_vulns
                
                # Update overall score based on Slither results
                if slither_vulns:
                    slither_penalty = len(slither_vulns) * 5  # 5 points per vulnerability
                    comprehensive_result["overall_score"] = max(0, 
                        comprehensive_result["overall_score"] - slither_penalty)
            
            log_info(LogCategory.SECURITY, f"Comprehensive scan completed. Score: {comprehensive_result['overall_score']}")
            return comprehensive_result
            
        except Exception as e:
            log_error(LogCategory.SECURITY, "Comprehensive scan failed", e)
            return {
                "status": "error",
                "error": str(e),
                "message": "Comprehensive scan failed"
            }
