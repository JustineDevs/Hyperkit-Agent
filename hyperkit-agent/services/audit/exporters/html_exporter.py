"""
HTML Exporter for Audit Reports
"""

from pathlib import Path
from typing import Dict, Any
from datetime import datetime

from .base_exporter import BaseExporter, logger


class HTMLExporter(BaseExporter):
    """Export audit reports as HTML"""
    
    async def export(self, audit_result: Dict[str, Any], output_file: Path):
        """Export single audit result as HTML"""
        self._ensure_output_dir(output_file)
        
        html_content = self._generate_contract_html(audit_result)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.debug(f"Exported HTML to {output_file}")
    
    async def export_batch_summary(self, batch_results: Dict[str, Any], output_file: Path):
        """Export batch summary as HTML"""
        self._ensure_output_dir(output_file)
        
        html_content = self._generate_batch_html(batch_results)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.debug(f"Exported batch HTML to {output_file}")
    
    def _generate_contract_html(self, result: Dict[str, Any]) -> str:
        """Generate HTML content for single contract"""
        contract_name = result.get('contract_name', 'Unknown')
        severity = result.get('severity', 'unknown').upper()
        timestamp = result.get('timestamp', datetime.now().isoformat())
        findings = result.get('findings', [])
        
        severity_color = {
            'CRITICAL': '#dc3545',
            'HIGH': '#fd7e14',
            'MEDIUM': '#ffc107',
            'LOW': '#17a2b8',
            'INFO': '#6c757d',
            'SAFE': '#28a745',
            'UNKNOWN': '#6c757d'
        }.get(severity, '#6c757d')
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Audit Report: {contract_name}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; margin: 40px; background: #f8f9fa; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; border-bottom: 3px solid {severity_color}; padding-bottom: 10px; }}
        .meta {{ color: #666; margin: 20px 0; }}
        .meta-item {{ display: inline-block; margin-right: 20px; }}
        .severity {{ display: inline-block; padding: 5px 15px; background: {severity_color}; color: white; border-radius: 4px; font-weight: bold; }}
        .summary {{ background: #f8f9fa; padding: 20px; border-radius: 4px; margin: 20px 0; }}
        .finding {{ border-left: 4px solid #dee2e6; padding: 15px; margin: 15px 0; background: #f8f9fa; }}
        .finding.critical {{ border-left-color: #dc3545; }}
        .finding.high {{ border-left-color: #fd7e14; }}
        .finding.medium {{ border-left-color: #ffc107; }}
        .finding.low {{ border-left-color: #17a2b8; }}
        .finding h3 {{ margin-top: 0; color: #333; }}
        .finding-meta {{ color: #666; font-size: 0.9em; margin: 10px 0; }}
        .recommendation {{ background: #d4edda; border-left: 4px solid #28a745; padding: 10px; margin-top: 10px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Smart Contract Audit Report: {contract_name}</h1>
        <div class="meta">
            <div class="meta-item"><strong>Audit Date:</strong> {timestamp}</div>
            <div class="meta-item"><strong>Severity:</strong> <span class="severity">{severity}</span></div>
            <div class="meta-item"><strong>Tools:</strong> {', '.join(result.get('tools_used', []))}</div>
        </div>
        
        <div class="summary">
            <h2>Summary</h2>
            <p><strong>Total Findings:</strong> {len(findings)}</p>
"""
        
        # Add severity breakdown
        severity_counts = {}
        for finding in findings:
            sev = finding.get('severity', 'unknown')
            severity_counts[sev] = severity_counts.get(sev, 0) + 1
        
        for sev, count in sorted(severity_counts.items()):
            html += f"            <p><strong>{sev.title()}:</strong> {count}</p>\n"
        
        html += """        </div>
        
        <h2>Findings</h2>
"""
        
        # Add findings
        if findings:
            for idx, finding in enumerate(findings, 1):
                sev_class = finding.get('severity', 'info').lower()
                html += f"""        <div class="finding {sev_class}">
            <h3>{idx}. {finding.get('title', 'Issue')}</h3>
            <div class="finding-meta">
                <strong>Severity:</strong> {finding.get('severity', 'unknown').title()} | 
                <strong>Type:</strong> {finding.get('type', 'unknown')}
            </div>
            <p><strong>Description:</strong> {finding.get('description', 'No description')}</p>
"""
                
                if 'location' in finding:
                    html += f"            <p><strong>Location:</strong> {finding['location']}</p>\n"
                
                if 'recommendation' in finding:
                    html += f"""            <div class="recommendation">
                <strong>Recommendation:</strong> {finding['recommendation']}
            </div>
"""
                
                html += "        </div>\n"
        else:
            html += "        <p>No findings detected.</p>\n"
        
        html += """    </div>
</body>
</html>"""
        
        return html
    
    def _generate_batch_html(self, batch_results: Dict[str, Any]) -> str:
        """Generate HTML content for batch summary"""
        timestamp = batch_results.get('timestamp', datetime.now().isoformat())
        summary = batch_results.get('summary', {})
        risk_score = summary.get('risk_score', 0)
        
        # Determine risk color
        if risk_score >= 70:
            risk_color = '#dc3545'
        elif risk_score >= 40:
            risk_color = '#ffc107'
        else:
            risk_color = '#28a745'
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Batch Audit Summary</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; margin: 40px; background: #f8f9fa; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; border-bottom: 3px solid {risk_color}; padding-bottom: 10px; }}
        .summary-box {{ background: #f8f9fa; padding: 20px; border-radius: 4px; margin: 20px 0; }}
        .risk-score {{ font-size: 3em; font-weight: bold; color: {risk_color}; text-align: center; margin: 20px 0; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }}
        .stat {{ background: white; padding: 15px; border-radius: 4px; border: 1px solid #dee2e6; }}
        .stat-value {{ font-size: 2em; font-weight: bold; color: #333; }}
        .stat-label {{ color: #666; font-size: 0.9em; }}
        .contract-list {{ margin: 20px 0; }}
        .contract-item {{ padding: 10px; margin: 5px 0; background: #f8f9fa; border-radius: 4px; }}
        .recommendation {{ background: #d1ecf1; border-left: 4px solid #0c5460; padding: 10px; margin: 10px 0; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #dee2e6; }}
        th {{ background: #f8f9fa; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Batch Audit Summary Report</h1>
        <div class="summary-box">
            <p><strong>Audit Date:</strong> {timestamp}</p>
            <p><strong>Total Contracts:</strong> {batch_results.get('total_contracts', 0)}</p>
            <p><strong>Successful Audits:</strong> {batch_results.get('successful', 0)}</p>
            <p><strong>Failed Audits:</strong> {batch_results.get('failed', 0)}</p>
        </div>
        
        <div class="risk-score">
            Risk Score: {risk_score}/100
        </div>
"""
        
        if summary:
            html += """        <div class="stats">
"""
            html += f"""            <div class="stat">
                <div class="stat-value">{summary.get('total_findings', 0)}</div>
                <div class="stat-label">Total Findings</div>
            </div>
            <div class="stat">
                <div class="stat-value">{summary.get('avg_findings_per_contract', 0)}</div>
                <div class="stat-label">Avg Findings/Contract</div>
            </div>
"""
            
            # Risk distribution
            risk_dist = summary.get('risk_distribution', {})
            for severity in ['critical', 'high', 'medium', 'low']:
                count = risk_dist.get(severity, 0)
                html += f"""            <div class="stat">
                <div class="stat-value">{count}</div>
                <div class="stat-label">{severity.title()} Issues</div>
            </div>
"""
            
            html += """        </div>
"""
            
            # Recommendations
            recommendations = summary.get('recommendations', [])
            if recommendations:
                html += """        <h2>Recommendations</h2>
"""
                for rec in recommendations:
                    html += f"""        <div class="recommendation">{rec}</div>
"""
            
            # Top issues
            top_issues = summary.get('top_issues', [])
            if top_issues:
                html += """        <h2>Top Issues</h2>
        <table>
            <tr><th>Issue Type</th><th>Occurrences</th></tr>
"""
                for issue in top_issues[:10]:
                    html += f"""            <tr><td>{issue['type']}</td><td>{issue['count']}</td></tr>
"""
                html += """        </table>
"""
        
        # Contract results
        html += """        <h2>Individual Contract Results</h2>
        <div class="contract-list">
"""
        
        contracts = batch_results.get('contracts', [])
        for contract in contracts:
            if contract.get('success'):
                name = contract.get('contract_name', 'Unknown')
                severity = contract.get('severity', 'unknown')
                findings_count = len(contract.get('findings', []))
                html += f"""            <div class="contract-item">
                <strong>{name}</strong>: {severity.upper()} ({findings_count} findings)
            </div>
"""
        
        html += """        </div>
    </div>
</body>
</html>"""
        
        return html

