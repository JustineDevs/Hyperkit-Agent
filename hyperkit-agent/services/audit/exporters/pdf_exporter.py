"""PDF Report Exporter for Batch Audit Reports"""

import logging
from pathlib import Path
from typing import Dict, Any
from .base_exporter import BaseExporter

logger = logging.getLogger(__name__)


class PDFExporter(BaseExporter):
    """
    Export audit reports to PDF format.
    
    Note: Requires 'reportlab' package from requirements-optional.txt
    Falls back to HTML export if reportlab is not available.
    """
    
    def __init__(self):
        self.reportlab_available = self._check_reportlab()
    
    def _check_reportlab(self) -> bool:
        """Check if reportlab is installed"""
        try:
            import reportlab
            return True
        except ImportError:
            logger.warning("⚠️  reportlab not installed. PDF export will fallback to HTML.")
            logger.warning("   Install with: pip install reportlab")
            return False
    
    def export(self, report: Dict[str, Any], output_path: str) -> bool:
        """
        Export audit report to PDF format.
        
        Args:
            report: Audit report dictionary
            output_path: Path for output PDF file
            
        Returns:
            bool: True if export successful
        """
        if not self.reportlab_available:
            return self._fallback_to_html(report, output_path)
        
        try:
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib import colors
            
            output_dir = Path(output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Ensure .pdf extension
            if not output_path.endswith('.pdf'):
                output_path = f"{output_path}.pdf"
            
            # Create PDF
            doc = SimpleDocTemplate(output_path, pagesize=letter)
            story = []
            styles = getSampleStyleSheet()
            
            # Title
            title = Paragraph(f"<b>Batch Audit Report - {report.get('batch_name', 'Unknown')}</b>", 
                            styles['Title'])
            story.append(title)
            story.append(Spacer(1, 0.2*inch))
            
            # Summary
            summary_text = f"""
            <b>Summary</b><br/>
            Total Contracts: {report.get('total_contracts', 0)}<br/>
            Successful: {report.get('successful_audits', 0)}<br/>
            Failed: {report.get('failed_audits', 0)}<br/>
            Total Findings: {report.get('total_findings', 0)}<br/>
            Critical: {report.get('findings_by_severity', {}).get('critical', 0)}<br/>
            High: {report.get('findings_by_severity', {}).get('high', 0)}<br/>
            Medium: {report.get('findings_by_severity', {}).get('medium', 0)}<br/>
            Low: {report.get('findings_by_severity', {}).get('low', 0)}
            """
            story.append(Paragraph(summary_text, styles['Normal']))
            story.append(Spacer(1, 0.3*inch))
            
            # Contract Details
            for contract_name, contract_data in report.get('contracts', {}).items():
                contract_title = Paragraph(f"<b>{contract_name}</b>", styles['Heading2'])
                story.append(contract_title)
                
                findings_count = contract_data.get('total_findings', 0)
                contract_summary = Paragraph(
                    f"Status: {contract_data.get('status', 'unknown')} | "
                    f"Findings: {findings_count} | "
                    f"Risk: {contract_data.get('risk_level', 'unknown')}",
                    styles['Normal']
                )
                story.append(contract_summary)
                story.append(Spacer(1, 0.1*inch))
                
                # Top findings
                if findings_count > 0:
                    findings = contract_data.get('findings', [])[:5]  # Top 5
                    for finding in findings:
                        finding_text = f"""
                        <b>[{finding.get('severity', 'unknown').upper()}]</b> {finding.get('title', 'No title')}<br/>
                        {finding.get('description', 'No description')[:200]}...
                        """
                        story.append(Paragraph(finding_text, styles['Normal']))
                        story.append(Spacer(1, 0.05*inch))
                
                story.append(Spacer(1, 0.2*inch))
            
            # Build PDF
            doc.build(story)
            
            logger.info(f"✅ PDF export successful: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ PDF export failed: {str(e)}")
            return False
    
    def _fallback_to_html(self, report: Dict[str, Any], output_path: str) -> bool:
        """Fallback to HTML export if reportlab not available"""
        from .html_exporter import HTMLExporter
        
        html_exporter = HTMLExporter()
        html_path = output_path.replace('.pdf', '.html')
        
        logger.info("🔄 Falling back to HTML export...")
        return html_exporter.export(report, html_path)
