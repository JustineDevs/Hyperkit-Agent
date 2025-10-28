"""Batch Audit CLI Command"""

import click
import asyncio
import logging
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)


@click.group(name='batch-audit')
def batch_audit_group():
    """Batch audit multiple contracts"""
    pass


@batch_audit_group.command(name='contracts')
@click.option('--files', '-f', multiple=True, help='Contract files to audit')
@click.option('--directory', '-d', help='Directory containing contract files to audit')
@click.option('--output', '-o', default='artifacts/batch-audits', help='Output directory')
@click.option('--format', '-fmt', 
              type=click.Choice(['json', 'markdown', 'html', 'csv', 'pdf', 'excel', 'all']),
              default='json', 
              help='Output format')
@click.option('--batch-name', '-n', help='Name for this batch audit')
def audit_contracts(files: tuple, directory: str, output: str, format: str, batch_name: str):
    """
    Audit multiple contracts in batch.
    
    Examples:
        hyperagent batch-audit contracts -f Contract1.sol -f Contract2.sol
        hyperagent batch-audit contracts -d contracts/ --format all
        hyperagent batch-audit contracts -f *.sol --format excel -n "Q4 Audit"
    """
    try:
        from services.audit.batch_auditor import BatchAuditor
        from services.audit.report_aggregator import ReportAggregator
        from services.audit.exporters import (
            JSONExporter, MarkdownExporter, HTMLExporter, 
            CSVExporter, PDFExporter, ExcelExporter
        )
        
        click.echo("Starting batch audit...")
        
        # Resolve files
        if directory:
            contract_files = _resolve_contract_files((directory,))
        elif files:
            contract_files = _resolve_contract_files(files)
        else:
            click.echo("Error: Must specify either --files or --directory", err=True)
            return
        
        if not contract_files:
            click.echo("No contract files found", err=True)
            return
        
        click.echo(f"Found {len(contract_files)} contracts to audit")
        
        # Initialize batch auditor
        auditor = BatchAuditor()
        
        # Run batch audit
        results = asyncio.run(auditor.audit_batch(contract_files))
        
        # Aggregate results
        aggregator = ReportAggregator()
        report = aggregator.aggregate(results, batch_name=batch_name)
        
        # Create output directory
        output_dir = Path(output)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate output filename
        if batch_name:
            output_base = output_dir / batch_name.replace(' ', '_').lower()
        else:
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_base = output_dir / f"batch_audit_{timestamp}"
        
        # Export in requested format(s)
        exporters = {
            'json': JSONExporter(),
            'markdown': MarkdownExporter(),
            'html': HTMLExporter(),
            'csv': CSVExporter(),
            'pdf': PDFExporter(),
            'excel': ExcelExporter()
        }
        
        if format == 'all':
            click.echo("Exporting in all formats...")
            for fmt_name, exporter in exporters.items():
                output_path = f"{output_base}.{fmt_name}"
                if exporter.export(report, output_path):
                    click.echo(f"  {fmt_name.upper()}: {output_path}")
                else:
                    click.echo(f"  {fmt_name.upper()}: Export failed", err=True)
        else:
            exporter = exporters.get(format)
            if exporter:
                output_path = f"{output_base}.{format}"
                if exporter.export(report, output_path):
                    click.echo(f"Report exported: {output_path}")
                else:
                    click.echo("Export failed", err=True)
            else:
                click.echo(f"Unknown format: {format}", err=True)
        
        # Print summary
        click.echo("\nBatch Audit Summary:")
        click.echo(f"  Total Contracts: {report.get('total_contracts', 0)}")
        click.echo(f"  Successful: {report.get('successful_audits', 0)}")
        click.echo(f"  Failed: {report.get('failed_audits', 0)}")
        click.echo(f"  Total Findings: {report.get('total_findings', 0)}")
        
        findings_by_severity = report.get('findings_by_severity', {})
        if findings_by_severity:
            click.echo("\nFindings by Severity:")
            for severity, count in findings_by_severity.items():
                if count > 0:
                    click.echo(f"  {severity.capitalize()}: {count}")
        
        click.echo("\nBatch audit complete!")
        
    except Exception as e:
        logger.error(f"Batch audit failed: {str(e)}", exc_info=True)
        click.echo(f"Batch audit failed: {str(e)}", err=True)


def _resolve_contract_files(file_patterns: tuple) -> List[Path]:
    """Resolve file patterns to actual contract files"""
    import glob
    
    contract_files = []
    
    for pattern in file_patterns:
        pattern_path = Path(pattern)
        
        # If it's a directory, get all .sol files
        if pattern_path.is_dir():
            contract_files.extend(pattern_path.glob('**/*.sol'))
        # If it's a file, add it
        elif pattern_path.is_file():
            contract_files.append(pattern_path)
        # If it's a glob pattern
        elif '*' in str(pattern):
            contract_files.extend([Path(f) for f in glob.glob(str(pattern))])
        else:
            # Try as file
            if pattern_path.exists():
                contract_files.append(pattern_path)
    
    return list(set(contract_files))  # Remove duplicates


def _get_severity_icon(severity: str) -> str:
    """Get icon for severity level"""
    icons = {
        'critical': '🔴',
        'high': '🟠',
        'medium': '🟡',
        'low': '🔵',
        'informational': 'ℹ️',
        'gas-optimization': '⛽'
    }
    return icons.get(severity, '•')
