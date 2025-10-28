"""
Batch Audit System with Multi-Format Export

Handles batch auditing of multiple contracts with:
- Per-contract error handling
- Report aggregation
- Multi-format export (JSON, HTML, Markdown, CSV, PDF, Excel)
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

from .auditor import SmartContractAuditor
from .report_aggregator import ReportAggregator
from .exporters import (
    JSONExporter,
    HTMLExporter,
    MarkdownExporter,
    CSVExporter,
    PDFExporter,
    ExcelExporter
)

logger = logging.getLogger(__name__)


class BatchAuditor:
    """
    Batch audit multiple contracts with comprehensive error handling
    and multi-format export capabilities.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize batch auditor.
        
        Args:
            config: Configuration for auditing and export
        """
        self.config = config or {}
        self.auditor = SmartContractAuditor(config)
        self.aggregator = ReportAggregator()
        
        # Initialize exporters
        self.exporters = {
            'json': JSONExporter(),
            'html': HTMLExporter(),
            'markdown': MarkdownExporter(),
            'csv': CSVExporter(),
            'pdf': PDFExporter(),
            'excel': ExcelExporter()
        }
        
        logger.info("BatchAuditor initialized with all export formats")
    
    async def audit_batch(
        self,
        contracts: List[Dict[str, str]],
        export_formats: List[str] = ['json', 'html'],
        output_dir: Optional[str] = None,
        aggregate: bool = True
    ) -> Dict[str, Any]:
        """
        Audit multiple contracts with error handling and export.
        
        Args:
            contracts: List of dicts with 'name' and 'code' or 'path'
            export_formats: List of export formats (json, html, markdown, csv, pdf, excel)
            output_dir: Directory for output files
            aggregate: Whether to create aggregated summary report
            
        Returns:
            Batch audit results with success/failure counts
        """
        logger.info(f"Starting batch audit of {len(contracts)} contracts")
        
        # Setup output directory
        if output_dir is None:
            output_dir = Path('artifacts/audits') / datetime.now().strftime('%Y%m%d_%H%M%S')
        else:
            output_dir = Path(output_dir)
        
        output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Output directory: {output_dir}")
        
        # Audit results storage
        results = {
            'timestamp': datetime.now().isoformat(),
            'total_contracts': len(contracts),
            'successful': 0,
            'failed': 0,
            'contracts': [],
            'failures': [],
            'summary': {}
        }
        
        # Process each contract with error handling
        for idx, contract_info in enumerate(contracts, 1):
            contract_name = contract_info.get('name', f'contract_{idx}')
            logger.info(f"[{idx}/{len(contracts)}] Auditing: {contract_name}")
            
            try:
                # Load contract code
                if 'code' in contract_info:
                    contract_code = contract_info['code']
                elif 'path' in contract_info:
                    contract_path = Path(contract_info['path'])
                    if not contract_path.exists():
                        raise FileNotFoundError(f"Contract file not found: {contract_path}")
                    contract_code = contract_path.read_text(encoding='utf-8')
                else:
                    raise ValueError(f"Contract must have 'code' or 'path': {contract_name}")
                
                # Run audit
                audit_result = await self.auditor.audit(contract_code)
                
                # Add metadata
                audit_result['contract_name'] = contract_name
                audit_result['success'] = True
                audit_result['error'] = None
                
                results['contracts'].append(audit_result)
                results['successful'] += 1
                
                # Export individual contract report
                await self._export_contract_report(
                    audit_result,
                    contract_name,
                    export_formats,
                    output_dir
                )
                
                logger.info(f"✓ {contract_name}: {audit_result.get('severity', 'unknown')} severity")
                
            except Exception as e:
                logger.error(f"✗ {contract_name}: {str(e)}")
                
                # Record failure but continue
                failure_record = {
                    'contract_name': contract_name,
                    'success': False,
                    'error': str(e),
                    'error_type': type(e).__name__
                }
                
                results['contracts'].append(failure_record)
                results['failures'].append(failure_record)
                results['failed'] += 1
        
        # Generate aggregated summary
        if aggregate and results['successful'] > 0:
            logger.info("Generating aggregated summary report")
            results['summary'] = self.aggregator.aggregate(
                [c for c in results['contracts'] if c.get('success', False)]
            )
            
            # Export aggregated report
            await self._export_aggregated_report(
                results,
                export_formats,
                output_dir
            )
        
        # Save batch results JSON
        batch_results_file = output_dir / 'batch_results.json'
        with open(batch_results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"Batch audit complete: {results['successful']} succeeded, {results['failed']} failed")
        logger.info(f"Results saved to: {output_dir}")
        
        return results
    
    async def _export_contract_report(
        self,
        audit_result: Dict[str, Any],
        contract_name: str,
        formats: List[str],
        output_dir: Path
    ):
        """Export individual contract audit report in multiple formats"""
        # Create subdirectory for this contract
        contract_dir = output_dir / 'contracts' / contract_name
        contract_dir.mkdir(parents=True, exist_ok=True)
        
        for format_name in formats:
            if format_name not in self.exporters:
                logger.warning(f"Unknown export format: {format_name}")
                continue
            
            try:
                exporter = self.exporters[format_name]
                output_file = contract_dir / f"{contract_name}.{format_name}"
                
                await exporter.export(audit_result, output_file)
                logger.debug(f"Exported {contract_name} to {format_name}")
                
            except Exception as e:
                logger.error(f"Failed to export {contract_name} as {format_name}: {e}")
    
    async def _export_aggregated_report(
        self,
        batch_results: Dict[str, Any],
        formats: List[str],
        output_dir: Path
    ):
        """Export aggregated batch audit report"""
        summary_dir = output_dir / 'summary'
        summary_dir.mkdir(parents=True, exist_ok=True)
        
        for format_name in formats:
            if format_name not in self.exporters:
                continue
            
            try:
                exporter = self.exporters[format_name]
                output_file = summary_dir / f"batch_summary.{format_name}"
                
                await exporter.export_batch_summary(batch_results, output_file)
                logger.debug(f"Exported batch summary as {format_name}")
                
            except Exception as e:
                logger.error(f"Failed to export batch summary as {format_name}: {e}")
    
    async def audit_directory(
        self,
        directory: str,
        pattern: str = '*.sol',
        **kwargs
    ) -> Dict[str, Any]:
        """
        Audit all contracts in a directory.
        
        Args:
            directory: Directory containing contracts
            pattern: File pattern to match (default: *.sol)
            **kwargs: Additional arguments for audit_batch
            
        Returns:
            Batch audit results
        """
        dir_path = Path(directory)
        if not dir_path.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")
        
        # Find all matching contracts
        contract_files = list(dir_path.rglob(pattern))
        logger.info(f"Found {len(contract_files)} contracts in {directory}")
        
        if not contract_files:
            raise ValueError(f"No contracts found matching pattern: {pattern}")
        
        # Prepare contract list
        contracts = [
            {
                'name': file.stem,
                'path': str(file)
            }
            for file in contract_files
        ]
        
        return await self.audit_batch(contracts, **kwargs)

