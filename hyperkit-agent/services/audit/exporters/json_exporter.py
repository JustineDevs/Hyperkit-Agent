"""
JSON Exporter for Audit Reports
"""

import json
from pathlib import Path
from typing import Dict, Any

from .base_exporter import BaseExporter, logger


class JSONExporter(BaseExporter):
    """Export audit reports as JSON"""
    
    async def export(self, audit_result: Dict[str, Any], output_file: Path):
        """Export single audit result as JSON"""
        self._ensure_output_dir(output_file)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(audit_result, f, indent=2, default=str)
        
        logger.debug(f"Exported JSON to {output_file}")
    
    async def export_batch_summary(self, batch_results: Dict[str, Any], output_file: Path):
        """Export batch summary as JSON"""
        self._ensure_output_dir(output_file)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(batch_results, f, indent=2, default=str)
        
        logger.debug(f"Exported batch JSON to {output_file}")

