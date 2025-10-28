"""CSV Report Exporter for Batch Audit Reports"""

import csv
import logging
from pathlib import Path
from typing import Dict, Any, List
from .base_exporter import BaseExporter

logger = logging.getLogger(__name__)


class CSVExporter(BaseExporter):
    """Export audit reports to CSV format"""
    
    def export(self, report: Dict[str, Any], output_path: str) -> bool:
        """
        Export audit report to CSV format.
        
        Creates two CSV files:
        - {output_path}_summary.csv: High-level summary of all contracts
        - {output_path}_findings.csv: Detailed findings for all contracts
        
        Args:
            report: Audit report dictionary
            output_path: Path for output file (without extension)
            
        Returns:
            bool: True if export successful
        """
        try:
            output_dir = Path(output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Export summary CSV
            summary_path = f"{output_path}_summary.csv"
            self._export_summary(report, summary_path)
            
            # Export detailed findings CSV
            findings_path = f"{output_path}_findings.csv"
            self._export_findings(report, findings_path)
            
            logger.info(f"✅ CSV export successful:")
            logger.info(f"  - Summary: {summary_path}")
            logger.info(f"  - Findings: {findings_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ CSV export failed: {str(e)}")
            return False
    
    def _export_summary(self, report: Dict[str, Any], output_path: str):
        """Export high-level summary"""
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Header
            writer.writerow([
                'Contract', 'Status', 'Critical', 'High', 'Medium', 
                'Low', 'Informational', 'Gas', 'Total Findings', 
                'Risk Level', 'Confidence'
            ])
            
            # Data rows
            for contract_name, contract_data in report.get('contracts', {}).items():
                findings_by_severity = contract_data.get('findings_by_severity', {})
                
                writer.writerow([
                    contract_name,
                    contract_data.get('status', 'unknown'),
                    findings_by_severity.get('critical', 0),
                    findings_by_severity.get('high', 0),
                    findings_by_severity.get('medium', 0),
                    findings_by_severity.get('low', 0),
                    findings_by_severity.get('informational', 0),
                    findings_by_severity.get('gas-optimization', 0),
                    contract_data.get('total_findings', 0),
                    contract_data.get('risk_level', 'unknown'),
                    f"{contract_data.get('confidence_score', 0):.0f}%"
                ])
    
    def _export_findings(self, report: Dict[str, Any], output_path: str):
        """Export detailed findings"""
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Header
            writer.writerow([
                'Contract', 'Severity', 'Title', 'Description', 
                'Location', 'Recommendation', 'Source'
            ])
            
            # Data rows
            for contract_name, contract_data in report.get('contracts', {}).items():
                for finding in contract_data.get('findings', []):
                    writer.writerow([
                        contract_name,
                        finding.get('severity', 'unknown'),
                        finding.get('title', 'No title'),
                        finding.get('description', 'No description')[:200] + '...',  # Truncate for CSV
                        finding.get('location', 'unknown'),
                        finding.get('recommendation', 'No recommendation')[:200] + '...',
                        finding.get('source', 'unknown')
                    ])
