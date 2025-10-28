"""
PDF Exporter for Audit Reports

Note: Uses reportlab if available, falls back to HTML-to-PDF or text-based PDF
"""

from pathlib import Path
from typing import Dict, Any

from .base_exporter import BaseExporter, logger


class PDFExporter(BaseExporter):
    """Export audit reports as PDF"""
    
    def __init__(self):
        self.reportlab_available = False
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
            from reportlab.lib.styles import getSampleStyleSheet
            self.reportlab_available = True
            self.reportlab_modules = {
                'letter': letter,
                'SimpleDocTemplate': SimpleDocTemplate,
                'Paragraph': Paragraph,
                'Spacer': Spacer,
                'Table': Table,
                'getSampleStyleSheet': getSampleStyleSheet
            }
        except ImportError:
            logger.warning("reportlab not available, using fallback PDF generation")
    
    async def export(self, audit_result: Dict[str, Any], output_file: Path):
        """Export single audit result as PDF"""
        self._ensure_output_dir(output_file)
        
        if self.reportlab_available:
            await self._export_reportlab(audit_result, output_file)
        else:
            await self._export_fallback(audit_result, output_file)
        
        logger.debug(f"Exported PDF to {output_file}")
    
    async def export_batch_summary(self, batch_results: Dict[str, Any], output_file: Path):
        """Export batch summary as PDF"""
        self._ensure_output_dir(output_file)
        
        if self.reportlab_available:
            await self._export_batch_reportlab(batch_results, output_file)
        else:
            await self._export_batch_fallback(batch_results, output_file)
        
        logger.debug(f"Exported batch PDF to {output_file}")
    
    async def _export_reportlab(self, audit_result: Dict[str, Any], output_file: Path):
        """Export using reportlab library"""
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        
        doc = SimpleDocTemplate(str(output_file), pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        contract_name = audit_result.get('contract_name', 'Unknown')
        story.append(Paragraph(f"Audit Report: {contract_name}", styles['Title']))
        story.append(Spacer(1, 12))
        
        # Summary
        severity = audit_result.get('severity', 'unknown').upper()
        story.append(Paragraph(f"Severity: {severity}", styles['Heading2']))
        story.append(Spacer(1, 6))
        
        findings = audit_result.get('findings', [])
        story.append(Paragraph(f"Total Findings: {len(findings)}", styles['Normal']))
        story.append(Spacer(1, 12))
        
        # Findings
        for idx, finding in enumerate(findings, 1):
            story.append(Paragraph(f"{idx}. {finding.get('title', 'Issue')}", styles['Heading3']))
            story.append(Paragraph(f"Severity: {finding.get('severity', 'unknown')}", styles['Normal']))
            story.append(Paragraph(finding.get('description', 'No description'), styles['Normal']))
            story.append(Spacer(1, 6))
        
        doc.build(story)
    
    async def _export_batch_reportlab(self, batch_results: Dict[str, Any], output_file: Path):
        """Export batch summary using reportlab"""
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        
        doc = SimpleDocTemplate(str(output_file), pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        story.append(Paragraph("Batch Audit Summary", styles['Title']))
        story.append(Spacer(1, 12))
        
        summary = batch_results.get('summary', {})
        story.append(Paragraph(f"Total Contracts: {batch_results.get('total_contracts', 0)}", styles['Normal']))
        story.append(Paragraph(f"Risk Score: {summary.get('risk_score', 0)}/100", styles['Heading2']))
        story.append(Spacer(1, 12))
        
        # Recommendations
        recommendations = summary.get('recommendations', [])
        if recommendations:
            story.append(Paragraph("Recommendations:", styles['Heading2']))
            for rec in recommendations:
                story.append(Paragraph(f"• {rec}", styles['Normal']))
            story.append(Spacer(1, 12))
        
        doc.build(story)
    
    async def _export_fallback(self, audit_result: Dict[str, Any], output_file: Path):
        """Fallback: Export as text file with .pdf extension"""
        contract_name = audit_result.get('contract_name', 'Unknown')
        severity = audit_result.get('severity', 'unknown')
        findings = audit_result.get('findings', [])
        
        content = f"AUDIT REPORT: {contract_name}\n"
        content += "=" * 80 + "\n\n"
        content += f"Severity: {severity.upper()}\n"
        content += f"Total Findings: {len(findings)}\n\n"
        
        for idx, finding in enumerate(findings, 1):
            content += f"{idx}. {finding.get('title', 'Issue')}\n"
            content += f"   Severity: {finding.get('severity', 'unknown')}\n"
            content += f"   {finding.get('description', 'No description')}\n\n"
        
        content += "\nNote: Install 'reportlab' for full PDF support\n"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
    
    async def _export_batch_fallback(self, batch_results: Dict[str, Any], output_file: Path):
        """Fallback: Export batch summary as text"""
        summary = batch_results.get('summary', {})
        
        content = "BATCH AUDIT SUMMARY\n"
        content += "=" * 80 + "\n\n"
        content += f"Total Contracts: {batch_results.get('total_contracts', 0)}\n"
        content += f"Successful: {batch_results.get('successful', 0)}\n"
        content += f"Failed: {batch_results.get('failed', 0)}\n"
        content += f"Risk Score: {summary.get('risk_score', 0)}/100\n\n"
        
        recommendations = summary.get('recommendations', [])
        if recommendations:
            content += "Recommendations:\n"
            for rec in recommendations:
                content += f"  - {rec}\n"
        
        content += "\nNote: Install 'reportlab' for full PDF support\n"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)

