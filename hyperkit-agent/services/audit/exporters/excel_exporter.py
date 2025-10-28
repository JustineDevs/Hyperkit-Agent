"""Excel Report Exporter for Batch Audit Reports"""

import logging
from pathlib import Path
from typing import Dict, Any
from .base_exporter import BaseExporter

logger = logging.getLogger(__name__)


class ExcelExporter(BaseExporter):
    """
    Export audit reports to Excel format.
    
    Note: Requires 'openpyxl' package from requirements-optional.txt
    Falls back to CSV export if openpyxl is not available.
    """
    
    def __init__(self):
        self.openpyxl_available = self._check_openpyxl()
    
    def _check_openpyxl(self) -> bool:
        """Check if openpyxl is installed"""
        try:
            import openpyxl
            return True
        except ImportError:
            logger.warning("⚠️  openpyxl not installed. Excel export will fallback to CSV.")
            logger.warning("   Install with: pip install openpyxl")
            return False
    
    def export(self, report: Dict[str, Any], output_path: str) -> bool:
        """
        Export audit report to Excel format with multiple sheets.
        
        Creates an Excel workbook with sheets:
        - Summary: High-level overview
        - Contracts: Per-contract summary
        - Findings: Detailed findings
        - Statistics: Charts and graphs
        
        Args:
            report: Audit report dictionary
            output_path: Path for output Excel file
            
        Returns:
            bool: True if export successful
        """
        if not self.openpyxl_available:
            return self._fallback_to_csv(report, output_path)
        
        try:
            from openpyxl import Workbook
            from openpyxl.styles import Font, PatternFill, Alignment
            from openpyxl.utils import get_column_letter
            
            output_dir = Path(output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Ensure .xlsx extension
            if not output_path.endswith('.xlsx'):
                output_path = f"{output_path}.xlsx"
            
            wb = Workbook()
            
            # Remove default sheet
            if 'Sheet' in wb.sheetnames:
                wb.remove(wb['Sheet'])
            
            # Create sheets
            self._create_summary_sheet(wb, report)
            self._create_contracts_sheet(wb, report)
            self._create_findings_sheet(wb, report)
            
            # Save workbook
            wb.save(output_path)
            
            logger.info(f"✅ Excel export successful: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Excel export failed: {str(e)}")
            return False
    
    def _create_summary_sheet(self, wb, report: Dict[str, Any]):
        """Create summary sheet"""
        from openpyxl.styles import Font, PatternFill, Alignment
        
        ws = wb.create_sheet("Summary", 0)
        
        # Title
        ws['A1'] = f"Batch Audit Report - {report.get('batch_name', 'Unknown')}"
        ws['A1'].font = Font(size=16, bold=True)
        ws.merge_cells('A1:D1')
        
        # Overall Statistics
        row = 3
        ws[f'A{row}'] = "Total Contracts"
        ws[f'B{row}'] = report.get('total_contracts', 0)
        row += 1
        
        ws[f'A{row}'] = "Successful Audits"
        ws[f'B{row}'] = report.get('successful_audits', 0)
        row += 1
        
        ws[f'A{row}'] = "Failed Audits"
        ws[f'B{row}'] = report.get('failed_audits', 0)
        row += 1
        
        ws[f'A{row}'] = "Total Findings"
        ws[f'B{row}'] = report.get('total_findings', 0)
        row += 2
        
        # Findings by Severity
        ws[f'A{row}'] = "Findings by Severity"
        ws[f'A{row}'].font = Font(bold=True)
        row += 1
        
        findings_by_severity = report.get('findings_by_severity', {})
        for severity, count in findings_by_severity.items():
            ws[f'A{row}'] = severity.capitalize()
            ws[f'B{row}'] = count
            
            # Color code by severity
            if severity == 'critical':
                ws[f'A{row}'].fill = PatternFill(start_color="FF0000", end_color="FF0000", fill_type="solid")
            elif severity == 'high':
                ws[f'A{row}'].fill = PatternFill(start_color="FFA500", end_color="FFA500", fill_type="solid")
            elif severity == 'medium':
                ws[f'A{row}'].fill = PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")
            
            row += 1
        
        # Auto-size columns
        ws.column_dimensions['A'].width = 20
        ws.column_dimensions['B'].width = 15
    
    def _create_contracts_sheet(self, wb, report: Dict[str, Any]):
        """Create contracts summary sheet"""
        from openpyxl.styles import Font
        
        ws = wb.create_sheet("Contracts")
        
        # Header
        headers = ['Contract', 'Status', 'Critical', 'High', 'Medium', 'Low', 
                  'Informational', 'Gas', 'Total', 'Risk Level', 'Confidence']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(1, col)
            cell.value = header
            cell.font = Font(bold=True)
        
        # Data
        row = 2
        for contract_name, contract_data in report.get('contracts', {}).items():
            findings_by_severity = contract_data.get('findings_by_severity', {})
            
            ws.cell(row, 1).value = contract_name
            ws.cell(row, 2).value = contract_data.get('status', 'unknown')
            ws.cell(row, 3).value = findings_by_severity.get('critical', 0)
            ws.cell(row, 4).value = findings_by_severity.get('high', 0)
            ws.cell(row, 5).value = findings_by_severity.get('medium', 0)
            ws.cell(row, 6).value = findings_by_severity.get('low', 0)
            ws.cell(row, 7).value = findings_by_severity.get('informational', 0)
            ws.cell(row, 8).value = findings_by_severity.get('gas-optimization', 0)
            ws.cell(row, 9).value = contract_data.get('total_findings', 0)
            ws.cell(row, 10).value = contract_data.get('risk_level', 'unknown')
            ws.cell(row, 11).value = f"{contract_data.get('confidence_score', 0):.0f}%"
            
            row += 1
        
        # Auto-size columns
        for col in range(1, 12):
            ws.column_dimensions[get_column_letter(col)].width = 15
    
    def _create_findings_sheet(self, wb, report: Dict[str, Any]):
        """Create detailed findings sheet"""
        from openpyxl.styles import Font
        
        ws = wb.create_sheet("Findings")
        
        # Header
        headers = ['Contract', 'Severity', 'Title', 'Description', 'Location', 'Recommendation', 'Source']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(1, col)
            cell.value = header
            cell.font = Font(bold=True)
        
        # Data
        row = 2
        for contract_name, contract_data in report.get('contracts', {}).items():
            for finding in contract_data.get('findings', []):
                ws.cell(row, 1).value = contract_name
                ws.cell(row, 2).value = finding.get('severity', 'unknown')
                ws.cell(row, 3).value = finding.get('title', 'No title')
                ws.cell(row, 4).value = finding.get('description', 'No description')[:500]  # Truncate
                ws.cell(row, 5).value = finding.get('location', 'unknown')
                ws.cell(row, 6).value = finding.get('recommendation', 'No recommendation')[:500]
                ws.cell(row, 7).value = finding.get('source', 'unknown')
                
                row += 1
        
        # Auto-size columns
        for col in [1, 2, 5, 7]:
            ws.column_dimensions[get_column_letter(col)].width = 15
        for col in [3, 4, 6]:
            ws.column_dimensions[get_column_letter(col)].width = 50
    
    def _fallback_to_csv(self, report: Dict[str, Any], output_path: str) -> bool:
        """Fallback to CSV export if openpyxl not available"""
        from .csv_exporter import CSVExporter
        
        csv_exporter = CSVExporter()
        csv_path = output_path.replace('.xlsx', '')
        
        logger.info("🔄 Falling back to CSV export...")
        return csv_exporter.export(report, csv_path)
