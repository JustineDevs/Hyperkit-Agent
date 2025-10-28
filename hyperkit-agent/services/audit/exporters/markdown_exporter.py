"""
Markdown Exporter for Audit Reports
"""

from pathlib import Path
from typing import Dict, Any
from datetime import datetime

from .base_exporter import BaseExporter, logger


class MarkdownExporter(BaseExporter):
    """Export audit reports as Markdown"""
    
    async def export(self, audit_result: Dict[str, Any], output_file: Path):
        """Export single audit result as Markdown"""
        self._ensure_output_dir(output_file)
        
        md_content = self._generate_contract_markdown(audit_result)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        logger.debug(f"Exported Markdown to {output_file}")
    
    async def export_batch_summary(self, batch_results: Dict[str, Any], output_file: Path):
        """Export batch summary as Markdown"""
        self._ensure_output_dir(output_file)
        
        md_content = self._generate_batch_markdown(batch_results)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        logger.debug(f"Exported batch Markdown to {output_file}")
    
    def _generate_contract_markdown(self, result: Dict[str, Any]) -> str:
        """Generate Markdown content for single contract"""
        contract_name = result.get('contract_name', 'Unknown')
        severity = result.get('severity', 'unknown').upper()
        timestamp = result.get('timestamp', datetime.now().isoformat())
        
        md = f"# Smart Contract Audit Report: {contract_name}\n\n"
        md += f"**Audit Date**: {timestamp}\n"
        md += f"**Severity**: {severity}\n"
        md += f"**Tools Used**: {', '.join(result.get('tools_used', []))}\n\n"
        
        # Summary
        md += "## Summary\n\n"
        findings = result.get('findings', [])
        md += f"- **Total Findings**: {len(findings)}\n"
        
        severity_counts = {}
        for finding in findings:
            sev = finding.get('severity', 'unknown')
            severity_counts[sev] = severity_counts.get(sev, 0) + 1
        
        for sev, count in sorted(severity_counts.items()):
            md += f"- **{sev.title()}**: {count}\n"
        
        # Findings
        if findings:
            md += "\n## Findings\n\n"
            for idx, finding in enumerate(findings, 1):
                md += f"### {idx}. {finding.get('title', 'Issue')}\n\n"
                md += f"**Severity**: {finding.get('severity', 'unknown').title()}\n"
                md += f"**Type**: {finding.get('type', 'unknown')}\n\n"
                md += f"**Description**:\n{finding.get('description', 'No description')}\n\n"
                
                if 'location' in finding:
                    md += f"**Location**: {finding['location']}\n\n"
                
                if 'recommendation' in finding:
                    md += f"**Recommendation**: {finding['recommendation']}\n\n"
                
                md += "---\n\n"
        
        return md
    
    def _generate_batch_markdown(self, batch_results: Dict[str, Any]) -> str:
        """Generate Markdown content for batch summary"""
        timestamp = batch_results.get('timestamp', datetime.now().isoformat())
        summary = batch_results.get('summary', {})
        
        md = "# Batch Audit Summary Report\n\n"
        md += f"**Audit Date**: {timestamp}\n"
        md += f"**Total Contracts**: {batch_results.get('total_contracts', 0)}\n"
        md += f"**Successful Audits**: {batch_results.get('successful', 0)}\n"
        md += f"**Failed Audits**: {batch_results.get('failed', 0)}\n\n"
        
        # Summary stats
        if summary:
            md += "## Summary Statistics\n\n"
            md += f"- **Total Findings**: {summary.get('total_findings', 0)}\n"
            md += f"- **Average Findings Per Contract**: {summary.get('avg_findings_per_contract', 0)}\n"
            md += f"- **Risk Score**: {summary.get('risk_score', 0)}/100\n\n"
            
            # Risk distribution
            risk_dist = summary.get('risk_distribution', {})
            md += "### Risk Distribution\n\n"
            for severity, count in risk_dist.items():
                md += f"- **{severity.title()}**: {count} contracts\n"
            
            # Top issues
            top_issues = summary.get('top_issues', [])
            if top_issues:
                md += "\n### Top Issues\n\n"
                for issue in top_issues[:5]:
                    md += f"- **{issue['type']}**: {issue['count']} occurrences\n"
            
            # Recommendations
            recommendations = summary.get('recommendations', [])
            if recommendations:
                md += "\n## Recommendations\n\n"
                for rec in recommendations:
                    md += f"- {rec}\n"
            
            # Summary text
            summary_text = summary.get('summary_text', '')
            if summary_text:
                md += f"\n## Overall Assessment\n\n{summary_text}\n"
        
        # Individual contract results
        md += "\n## Individual Contract Results\n\n"
        contracts = batch_results.get('contracts', [])
        for contract in contracts:
            if contract.get('success'):
                name = contract.get('contract_name', 'Unknown')
                severity = contract.get('severity', 'unknown')
                findings_count = len(contract.get('findings', []))
                md += f"- **{name}**: {severity.upper()} ({findings_count} findings)\n"
        
        # Failures
        failures = batch_results.get('failures', [])
        if failures:
            md += "\n## Failed Audits\n\n"
            for failure in failures:
                name = failure.get('contract_name', 'Unknown')
                error = failure.get('error', 'Unknown error')
                md += f"- **{name}**: {error}\n"
        
        return md

