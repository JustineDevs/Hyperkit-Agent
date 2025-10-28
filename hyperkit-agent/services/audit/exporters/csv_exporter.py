"""
CSV Exporter for Audit Reports
"""

import csv
from pathlib import Path
from typing import Dict, Any

from .base_exporter import BaseExporter, logger


class CSVExporter(BaseExporter):
    """Export audit reports as CSV"""
    
    async def export(self, audit_result: Dict[str, Any], output_file: Path):
        """Export single audit result as CSV"""
        self._ensure_output_dir(output_file)
        
        findings = audit_result.get('findings', [])
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Header
            writer.writerow(['#', 'Title', 'Severity', 'Type', 'Description', 'Location', 'Recommendation'])
            
            # Findings
            for idx, finding in enumerate(findings, 1):
                writer.writerow([
                    idx,
                    finding.get('title', ''),
                    finding.get('severity', ''),
                    finding.get('type', ''),
                    finding.get('description', ''),
                    finding.get('location', ''),
                    finding.get('recommendation', '')
                ])
        
        logger.debug(f"Exported CSV to {output_file}")
    
    async def export_batch_summary(self, batch_results: Dict[str, Any], output_file: Path):
        """Export batch summary as CSV"""
        self._ensure_output_dir(output_file)
        
        contracts = batch_results.get('contracts', [])
        summary = batch_results.get('summary', {})
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Summary header
            writer.writerow(['Batch Audit Summary'])
            writer.writerow(['Total Contracts', batch_results.get('total_contracts', 0)])
            writer.writerow(['Successful', batch_results.get('successful', 0)])
            writer.writerow(['Failed', batch_results.get('failed', 0)])
            writer.writerow(['Risk Score', summary.get('risk_score', 0)])
            writer.writerow([])
            
            # Contract results header
            writer.writerow(['Contract Name', 'Severity', 'Findings Count', 'Status'])
            
            # Contract results
            for contract in contracts:
                name = contract.get('contract_name', 'Unknown')
                if contract.get('success'):
                    severity = contract.get('severity', 'unknown')
                    findings_count = len(contract.get('findings', []))
                    writer.writerow([name, severity.upper(), findings_count, 'Success'])
                else:
                    error = contract.get('error', 'Unknown error')
                    writer.writerow([name, 'N/A', 'N/A', f'Failed: {error}'])
        
        logger.debug(f"Exported batch CSV to {output_file}")

