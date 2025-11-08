"""
Event/Action Audit Trail System
Comprehensive logging of all workflow events for debugging and regression analysis.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class AuditEventType(Enum):
    """Types of events to audit"""
    PROMPT_RECEIVED = "prompt_received"
    RAG_CONTEXT_RETRIEVED = "rag_context_retrieved"
    RAG_CONTEXT_EMPTY = "rag_context_empty"
    MODEL_SELECTED = "model_selected"
    GENERATION_ATTEMPTED = "generation_attempted"
    GENERATION_SUCCESS = "generation_success"
    GENERATION_FAILED = "generation_failed"
    COMPILATION_ATTEMPTED = "compilation_attempted"
    COMPILATION_SUCCESS = "compilation_success"
    COMPILATION_FAILED = "compilation_failed"
    ERROR_OCCURRED = "error_occurred"
    AUTO_FIX_ATTEMPTED = "auto_fix_attempted"
    AUTO_FIX_SUCCESS = "auto_fix_success"
    AUTO_FIX_FAILED = "auto_fix_failed"
    RETRY_TRIGGERED = "retry_triggered"
    ESCALATION_TRIGGERED = "escalation_triggered"
    DEPLOYMENT_ATTEMPTED = "deployment_attempted"
    DEPLOYMENT_SUCCESS = "deployment_success"
    DEPLOYMENT_FAILED = "deployment_failed"
    WORKFLOW_COMPLETED = "workflow_completed"
    WORKFLOW_FAILED = "workflow_failed"


class AuditTrail:
    """
    Comprehensive audit trail system for tracking all workflow events.
    """
    
    def __init__(self, workspace_dir: Path):
        """
        Initialize audit trail system.
        
        Args:
            workspace_dir: Base workspace directory
        """
        self.workspace_dir = Path(workspace_dir)
        self.logs_dir = self.workspace_dir / "logs"
        self.audit_log_file = self.logs_dir / "audit_trail.jsonl"
        
        # Ensure logs directory exists
        self.logs_dir.mkdir(parents=True, exist_ok=True)
    
    def log_event(
        self,
        event_type: AuditEventType,
        workflow_id: str,
        stage: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Log an event to the audit trail.
        
        Args:
            event_type: Type of event
            workflow_id: Workflow identifier
            stage: Optional stage name
            details: Optional event details
            error: Optional error message
            metadata: Optional additional metadata
        """
        try:
            event = {
                "timestamp": datetime.utcnow().isoformat(),
                "event_type": event_type.value,
                "workflow_id": workflow_id,
                "stage": stage,
                "details": details or {},
                "error": error,
                "metadata": metadata or {}
            }
            
            # Write to JSONL file (one JSON object per line)
            with open(self.audit_log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(event) + '\n')
            
            logger.debug(f"Audit event logged: {event_type.value} for workflow {workflow_id}")
            
        except Exception as e:
            logger.warning(f"Failed to log audit event: {e}")
    
    def query_events(
        self,
        workflow_id: Optional[str] = None,
        event_type: Optional[AuditEventType] = None,
        stage: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Query audit trail events.
        
        Args:
            workflow_id: Filter by workflow ID
            event_type: Filter by event type
            stage: Filter by stage
            limit: Maximum number of results
            
        Returns:
            List of matching events
        """
        if not self.audit_log_file.exists():
            return []
        
        results = []
        try:
            with open(self.audit_log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        event = json.loads(line)
                        
                        # Apply filters
                        if workflow_id and event.get('workflow_id') != workflow_id:
                            continue
                        if event_type and event.get('event_type') != event_type.value:
                            continue
                        if stage and event.get('stage') != stage:
                            continue
                        
                        results.append(event)
                        if len(results) >= limit:
                            break
                    except json.JSONDecodeError:
                        continue
            
            # Return most recent first
            return list(reversed(results))
            
        except Exception as e:
            logger.warning(f"Failed to query audit trail: {e}")
            return []
    
    def get_statistics(self, workflow_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get statistics about events.
        
        Args:
            workflow_id: Optional workflow ID to filter
            
        Returns:
            Dictionary with statistics
        """
        events = self.query_events(workflow_id=workflow_id, limit=1000)
        
        if not events:
            return {
                "total_events": 0,
                "event_counts": {},
                "error_count": 0,
                "success_count": 0
            }
        
        event_counts = {}
        error_count = 0
        success_count = 0
        
        for event in events:
            event_type = event.get('event_type', 'unknown')
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
            
            if 'error' in event_type or 'failed' in event_type:
                error_count += 1
            elif 'success' in event_type:
                success_count += 1
        
        return {
            "total_events": len(events),
            "event_counts": event_counts,
            "error_count": error_count,
            "success_count": success_count,
            "success_rate": success_count / (success_count + error_count) if (success_count + error_count) > 0 else 0.0
        }

