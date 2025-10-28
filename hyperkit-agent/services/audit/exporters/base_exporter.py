"""
Base Exporter Class

Defines interface for all audit report exporters.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class BaseExporter(ABC):
    """Base class for all audit report exporters"""
    
    @abstractmethod
    async def export(self, audit_result: Dict[str, Any], output_file: Path):
        """
        Export individual contract audit result.
        
        Args:
            audit_result: Single contract audit result
            output_file: Path to output file
        """
        pass
    
    @abstractmethod
    async def export_batch_summary(self, batch_results: Dict[str, Any], output_file: Path):
        """
        Export batch audit summary.
        
        Args:
            batch_results: Batch audit results with summary
            output_file: Path to output file
        """
        pass
    
    def _ensure_output_dir(self, output_file: Path):
        """Ensure output directory exists"""
        output_file.parent.mkdir(parents=True, exist_ok=True)

