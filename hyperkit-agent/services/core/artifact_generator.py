"""
Artifact Generation Service
Comprehensive artifact generation for HyperKit Agent
"""

import os
import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from core.config.manager import config

class HyperKitArtifactGenerator:
    """
    Comprehensive artifact generation service
    Handles generation of contracts, reports, documentation, and other artifacts
    """
    
    def __init__(self):
        self.config = config
        self.artifacts_dir = Path("artifacts")
        self.artifacts_dir.mkdir(exist_ok=True)
        
        # Create subdirectories for different artifact types
        self.contracts_dir = self.artifacts_dir / "contracts"
        self.reports_dir = self.artifacts_dir / "reports"
        self.docs_dir = self.artifacts_dir / "docs"
        self.templates_dir = self.artifacts_dir / "templates"
        self.tests_dir = self.artifacts_dir / "tests"
        
        # Ensure all directories exist
        for directory in [self.contracts_dir, self.reports_dir, self.docs_dir, 
                         self.templates_dir, self.tests_dir]:
            directory.mkdir(exist_ok=True)
    
    async def generate_contract_artifact(self, contract_code: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Generate complete contract artifact with all related files"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            contract_name = metadata.get('name', 'Contract')
            safe_name = self._sanitize_filename(contract_name)
            
            # Create contract directory
            contract_dir = self.contracts_dir / f"{safe_name}_{timestamp}"
            contract_dir.mkdir(exist_ok=True)
            
            # Generate main contract file
            contract_file = contract_dir / f"{safe_name}.sol"
            with open(contract_file, 'w', encoding='utf-8') as f:
                f.write(contract_code)
            
            # Generate ABI file
            abi_file = contract_dir / f"{safe_name}.json"
            abi_data = self._extract_abi(contract_code)
            with open(abi_file, 'w', encoding='utf-8') as f:
                json.dump(abi_data, f, indent=2)
            
            # Generate metadata file
            metadata_file = contract_dir / "metadata.json"
            metadata_data = {
                "name": contract_name,
                "timestamp": timestamp,
                "type": "smart_contract",
                "language": "solidity",
                "version": metadata.get('version', '1.0.0'),
                "description": metadata.get('description', ''),
                "features": metadata.get('features', []),
                "security_level": metadata.get('security_level', 'medium'),
                "gas_optimized": metadata.get('gas_optimized', False),
                "files": {
                    "contract": f"{safe_name}.sol",
                    "abi": f"{safe_name}.json",
                    "metadata": "metadata.json"
                }
            }
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata_data, f, indent=2)
            
            # Generate test file
            test_file = contract_dir / f"test_{safe_name}.js"
            test_code = self._generate_test_code(contract_name, safe_name)
            with open(test_file, 'w', encoding='utf-8') as f:
                f.write(test_code)
            
            # Generate deployment script
            deploy_file = contract_dir / f"deploy_{safe_name}.js"
            deploy_code = self._generate_deployment_script(contract_name, safe_name)
            with open(deploy_file, 'w', encoding='utf-8') as f:
                f.write(deploy_code)
            
            return {
                "status": "success",
                "artifact_id": f"{safe_name}_{timestamp}",
                "directory": str(contract_dir),
                "files": {
                    "contract": str(contract_file),
                    "abi": str(abi_file),
                    "metadata": str(metadata_file),
                    "test": str(test_file),
                    "deploy": str(deploy_file)
                },
                "metadata": metadata_data
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "message": "Failed to generate contract artifact"
            }
    
    async def generate_audit_report_artifact(self, audit_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive audit report artifact"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            contract_address = audit_data.get('contract_address', 'unknown')
            safe_address = self._sanitize_filename(contract_address)
            
            # Create report directory
            report_dir = self.reports_dir / f"audit_{safe_address}_{timestamp}"
            report_dir.mkdir(exist_ok=True)
            
            # Generate main report file
            report_file = report_dir / "audit_report.md"
            report_content = self._generate_audit_report_markdown(audit_data)
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            # Generate JSON report
            json_file = report_dir / "audit_report.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(audit_data, f, indent=2)
            
            # Generate executive summary
            summary_file = report_dir / "executive_summary.md"
            summary_content = self._generate_executive_summary(audit_data)
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write(summary_content)
            
            # Generate recommendations file
            recommendations_file = report_dir / "recommendations.md"
            recommendations_content = self._generate_recommendations(audit_data)
            with open(recommendations_file, 'w', encoding='utf-8') as f:
                f.write(recommendations_content)
            
            return {
                "status": "success",
                "artifact_id": f"audit_{safe_address}_{timestamp}",
                "directory": str(report_dir),
                "files": {
                    "report": str(report_file),
                    "json": str(json_file),
                    "summary": str(summary_file),
                    "recommendations": str(recommendations_file)
                },
                "metadata": {
                    "type": "audit_report",
                    "timestamp": timestamp,
                    "contract_address": contract_address,
                    "security_score": audit_data.get('security_score', 0)
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "message": "Failed to generate audit report artifact"
            }
    
    async def generate_documentation_artifact(self, doc_type: str, content: Dict[str, Any]) -> Dict[str, Any]:
        """Generate documentation artifacts"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Create documentation directory
            doc_dir = self.docs_dir / f"{doc_type}_{timestamp}"
            doc_dir.mkdir(exist_ok=True)
            
            # Generate main documentation file
            doc_file = doc_dir / f"{doc_type}.md"
            doc_content = self._generate_documentation_markdown(doc_type, content)
            with open(doc_file, 'w', encoding='utf-8') as f:
                f.write(doc_content)
            
            # Generate JSON metadata
            metadata_file = doc_dir / "metadata.json"
            metadata = {
                "type": doc_type,
                "timestamp": timestamp,
                "version": content.get('version', '1.0.0'),
                "title": content.get('title', doc_type.title()),
                "description": content.get('description', ''),
                "sections": content.get('sections', [])
            }
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
            
            return {
                "status": "success",
                "artifact_id": f"{doc_type}_{timestamp}",
                "directory": str(doc_dir),
                "files": {
                    "documentation": str(doc_file),
                    "metadata": str(metadata_file)
                },
                "metadata": metadata
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "message": "Failed to generate documentation artifact"
            }
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe file system usage"""
        import re
        # Remove or replace invalid characters
        safe_name = re.sub(r'[<>:"/\\|?*]', '_', filename)
        safe_name = re.sub(r'\s+', '_', safe_name)
        return safe_name[:50]  # Limit length
    
    def _extract_abi(self, contract_code: str) -> Dict[str, Any]:
        """Extract ABI from contract code (simplified)"""
        # This is a simplified ABI extraction
        # In production, use proper Solidity compilation
        return {
            "contractName": "GeneratedContract",
            "abi": [
                {
                    "type": "constructor",
                    "inputs": [],
                    "stateMutability": "nonpayable"
                }
            ],
            "bytecode": "0x",
            "deployedBytecode": "0x"
        }
    
    def _generate_test_code(self, contract_name: str, safe_name: str) -> str:
        """Generate test code for contract"""
        return f"""// Test file for {contract_name}
const {contract_name} = artifacts.require("{contract_name}");

contract("{contract_name}Test", (accounts) => {{
    let {safe_name};
    const owner = accounts[0];
    const user1 = accounts[1];
    const user2 = accounts[2];

    beforeEach(async () => {{
        {safe_name} = await {contract_name}.new({{ from: owner }});
    }});

    it("should deploy successfully", async () => {{
        assert.ok({safe_name}.address);
    }});

    it("should have correct owner", async () => {{
        const contractOwner = await {safe_name}.owner();
        assert.equal(contractOwner, owner);
    }});

    // Add more tests as needed
}});
"""
    
    def _generate_deployment_script(self, contract_name: str, safe_name: str) -> str:
        """Generate deployment script for contract"""
        return f"""// Deployment script for {contract_name}
const {contract_name} = artifacts.require("{contract_name}");

module.exports = async function (deployer, network, accounts) {{
    const owner = accounts[0];
    
    console.log("Deploying {contract_name}...");
    
    await deployer.deploy({contract_name}, {{
        from: owner,
        gas: 3000000
    }});
    
    const {safe_name} = await {contract_name}.deployed();
    console.log("{contract_name} deployed at:", {safe_name}.address);
    
    // Add any post-deployment setup here
}};
"""
    
    def _generate_audit_report_markdown(self, audit_data: Dict[str, Any]) -> str:
        """Generate markdown audit report"""
        vulnerabilities = audit_data.get('vulnerabilities', [])
        warnings = audit_data.get('warnings', [])
        recommendations = audit_data.get('recommendations', [])
        security_score = audit_data.get('security_score', 0)
        
        report = f"""# Security Audit Report

## Executive Summary

**Contract Address**: {audit_data.get('contract_address', 'N/A')}
**Audit Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Security Score**: {security_score}/100
**Status**: {'✅ PASSED' if security_score >= 80 else '⚠️ NEEDS ATTENTION' if security_score >= 60 else '❌ FAILED'}

## Vulnerabilities Found

"""
        
        if vulnerabilities:
            for i, vuln in enumerate(vulnerabilities, 1):
                report += f"### {i}. {vuln.get('title', 'Unknown Vulnerability')}\n"
                report += f"**Severity**: {vuln.get('severity', 'Unknown')}\n"
                report += f"**Description**: {vuln.get('description', 'No description available')}\n"
                report += f"**Recommendation**: {vuln.get('recommendation', 'No recommendation available')}\n\n"
        else:
            report += "No critical vulnerabilities found.\n\n"
        
        if warnings:
            report += "## Warnings\n\n"
            for i, warning in enumerate(warnings, 1):
                report += f"{i}. {warning}\n"
            report += "\n"
        
        if recommendations:
            report += "## Recommendations\n\n"
            for i, rec in enumerate(recommendations, 1):
                report += f"{i}. {rec}\n"
        
        return report
    
    def _generate_executive_summary(self, audit_data: Dict[str, Any]) -> str:
        """Generate executive summary"""
        security_score = audit_data.get('security_score', 0)
        vulnerabilities = audit_data.get('vulnerabilities', [])
        
        return f"""# Executive Summary

## Security Assessment

**Overall Security Score**: {security_score}/100

**Risk Level**: {'LOW' if security_score >= 80 else 'MEDIUM' if security_score >= 60 else 'HIGH'}

**Critical Issues**: {len([v for v in vulnerabilities if v.get('severity') == 'CRITICAL'])}

**High Issues**: {len([v for v in vulnerabilities if v.get('severity') == 'HIGH'])}

**Medium Issues**: {len([v for v in vulnerabilities if v.get('severity') == 'MEDIUM'])}

**Low Issues**: {len([v for v in vulnerabilities if v.get('severity') == 'LOW'])}

## Recommendation

{'✅ Contract is ready for deployment' if security_score >= 80 else '⚠️ Address issues before deployment' if security_score >= 60 else '❌ Do not deploy until critical issues are resolved'}
"""
    
    def _generate_recommendations(self, audit_data: Dict[str, Any]) -> str:
        """Generate recommendations section"""
        recommendations = audit_data.get('recommendations', [])
        
        if not recommendations:
            return "# Recommendations\n\nNo specific recommendations at this time.\n"
        
        content = "# Recommendations\n\n"
        for i, rec in enumerate(recommendations, 1):
            content += f"## {i}. {rec.get('title', f'Recommendation {i}')}\n\n"
            content += f"{rec.get('description', rec)}\n\n"
            if rec.get('priority'):
                content += f"**Priority**: {rec['priority']}\n\n"
        
        return content
    
    def _generate_documentation_markdown(self, doc_type: str, content: Dict[str, Any]) -> str:
        """Generate documentation markdown"""
        title = content.get('title', doc_type.title())
        description = content.get('description', '')
        sections = content.get('sections', [])
        
        doc = f"# {title}\n\n"
        if description:
            doc += f"{description}\n\n"
        
        for section in sections:
            doc += f"## {section.get('title', 'Section')}\n\n"
            doc += f"{section.get('content', '')}\n\n"
        
        return doc
    
    async def list_artifacts(self, artifact_type: str = None) -> Dict[str, Any]:
        """List all generated artifacts"""
        try:
            artifacts = []
            
            if artifact_type == "contracts" or artifact_type is None:
                for contract_dir in self.contracts_dir.iterdir():
                    if contract_dir.is_dir():
                        metadata_file = contract_dir / "metadata.json"
                        if metadata_file.exists():
                            with open(metadata_file, 'r') as f:
                                metadata = json.load(f)
                            artifacts.append({
                                "type": "contract",
                                "id": contract_dir.name,
                                "directory": str(contract_dir),
                                "metadata": metadata
                            })
            
            if artifact_type == "reports" or artifact_type is None:
                for report_dir in self.reports_dir.iterdir():
                    if report_dir.is_dir():
                        artifacts.append({
                            "type": "report",
                            "id": report_dir.name,
                            "directory": str(report_dir)
                        })
            
            if artifact_type == "docs" or artifact_type is None:
                for doc_dir in self.docs_dir.iterdir():
                    if doc_dir.is_dir():
                        artifacts.append({
                            "type": "documentation",
                            "id": doc_dir.name,
                            "directory": str(doc_dir)
                        })
            
            return {
                "status": "success",
                "artifacts": artifacts,
                "total": len(artifacts),
                "filter": artifact_type
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "message": "Failed to list artifacts"
            }
    
    async def cleanup_artifacts(self, older_than_days: int = 30) -> Dict[str, Any]:
        """Clean up old artifacts"""
        try:
            import time
            current_time = time.time()
            cutoff_time = current_time - (older_than_days * 24 * 60 * 60)
            
            cleaned = 0
            for directory in [self.contracts_dir, self.reports_dir, self.docs_dir]:
                for item in directory.iterdir():
                    if item.is_dir() and item.stat().st_mtime < cutoff_time:
                        import shutil
                        shutil.rmtree(item)
                        cleaned += 1
            
            return {
                "status": "success",
                "cleaned_artifacts": cleaned,
                "older_than_days": older_than_days
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "message": "Failed to cleanup artifacts"
            }
