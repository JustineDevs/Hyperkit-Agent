"""
Workflow Context Manager
Persists state across all pipeline stages for debugging, retries, and recovery.
"""

import json
import logging
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class PipelineStage(Enum):
    """Pipeline stage identifiers"""
    INPUT_PARSING = "input_parsing"
    GENERATION = "generation"
    DEPENDENCY_RESOLUTION = "dependency_resolution"
    COMPILATION = "compilation"
    TESTING = "testing"
    AUDITING = "auditing"
    DEPLOYMENT = "deployment"
    VERIFICATION = "verification"
    OUTPUT = "output"


@dataclass
class StageResult:
    """Result from a single pipeline stage"""
    stage: PipelineStage
    status: str  # 'success', 'error', 'skipped'
    output: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    error_type: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    duration_ms: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowContext:
    """
    Persistent context object that carries state across all pipeline stages.
    Supports multi-step debugging, retries, and detailed error reporting.
    """
    
    # Workflow identification
    workflow_id: str
    user_prompt: str
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    # Stage results (ordered)
    stages: List[StageResult] = field(default_factory=list)
    
    # Contract artifacts
    contract_code: Optional[str] = None
    contract_name: Optional[str] = None
    contract_path: Optional[str] = None
    contract_category: Optional[str] = None
    
    # Dependencies
    detected_dependencies: List[Dict[str, Any]] = field(default_factory=list)
    installed_dependencies: Dict[str, Tuple[bool, str]] = field(default_factory=dict)
    
    # Compilation
    compilation_artifact_path: Optional[str] = None
    compilation_success: bool = False
    
    # Audit results
    audit_results: Optional[Dict[str, Any]] = None
    security_score: Optional[float] = None
    
    # Deployment
    deployment_address: Optional[str] = None
    deployment_tx_hash: Optional[str] = None
    deployment_network: Optional[str] = None
    
    # Verification
    verification_status: Optional[str] = None
    verification_url: Optional[str] = None
    
    # Testing
    test_results: Optional[Dict[str, Any]] = None
    
    # Error tracking
    errors: List[Dict[str, Any]] = field(default_factory=list)
    retry_attempts: Dict[str, int] = field(default_factory=dict)
    
    # Environment
    workspace_dir: Optional[str] = None
    temp_dir: Optional[str] = None
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_stage_result(self, stage: PipelineStage, status: str, output: Dict[str, Any] = None, 
                        error: Optional[str] = None, error_type: Optional[str] = None,
                        duration_ms: Optional[float] = None, metadata: Dict[str, Any] = None):
        """Add a stage result to the context"""
        result = StageResult(
            stage=stage,
            status=status,
            output=output or {},
            error=error,
            error_type=error_type,
            duration_ms=duration_ms,
            metadata=metadata or {}
        )
        self.stages.append(result)
        
        if error:
            self.errors.append({
                "stage": stage.value,
                "error": error,
                "error_type": error_type,
                "timestamp": result.timestamp
            })
    
    def get_last_stage_result(self) -> Optional[StageResult]:
        """Get the most recent stage result"""
        return self.stages[-1] if self.stages else None
    
    def get_stage_result(self, stage: PipelineStage) -> Optional[StageResult]:
        """Get result for a specific stage"""
        for result in reversed(self.stages):
            if result.stage == stage:
                return result
        return None
    
    def has_error(self) -> bool:
        """Check if any stage has failed"""
        return any(stage.status == "error" for stage in self.stages)
    
    def get_last_successful_stage(self) -> Optional[PipelineStage]:
        """Get the last successfully completed stage"""
        for result in reversed(self.stages):
            if result.status == "success":
                return result.stage
        return None
    
    def increment_retry(self, stage: PipelineStage):
        """Increment retry count for a stage"""
        stage_key = stage.value
        self.retry_attempts[stage_key] = self.retry_attempts.get(stage_key, 0) + 1
    
    def get_retry_count(self, stage: PipelineStage) -> int:
        """Get retry count for a stage"""
        return self.retry_attempts.get(stage.value, 0)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary for serialization"""
        data = asdict(self)
        # Convert Enum to string recursively
        def convert_enums(obj):
            if isinstance(obj, PipelineStage):
                return obj.value
            elif isinstance(obj, dict):
                return {k: convert_enums(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_enums(item) for item in obj]
            elif isinstance(obj, Enum):
                return obj.value
            else:
                return obj
        
        return convert_enums(data)
    
    def to_json(self, indent: int = 2) -> str:
        """Serialize context to JSON"""
        return json.dumps(self.to_dict(), indent=indent)
    
    def save_to_file(self, file_path: Path):
        """Save context to JSON file"""
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(self.to_json())
        logger.info(f"💾 Workflow context saved to: {file_path}")
    
    @classmethod
    def from_file(cls, file_path: Path) -> 'WorkflowContext':
        """Load context from JSON file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Convert stage strings back to Enum
        def restore_enums(obj):
            if isinstance(obj, dict):
                if "stage" in obj and isinstance(obj["stage"], str):
                    obj["stage"] = PipelineStage(obj["stage"])
                return {k: restore_enums(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [restore_enums(item) for item in obj]
            else:
                return obj
        
        data = restore_enums(data)
        
        # Reconstruct dataclass
        return cls(**data)
    
    def generate_diagnostic_bundle(self) -> Dict[str, Any]:
        """
        Generate comprehensive diagnostic bundle for troubleshooting.
        Includes input, versions, logs, environment, and dependencies.
        """
        import platform
        import sys
        import subprocess
        
        # Get system info
        system_info = {
            "platform": platform.platform(),
            "python_version": sys.version,
            "architecture": platform.architecture(),
        }
        
        # Get tool versions
        tool_versions = {}
        for tool, cmd in [("forge", ["forge", "--version"]), 
                         ("npm", ["npm", "--version"]),
                         ("node", ["node", "--version"]),
                         ("python", ["python", "--version"])]:
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                tool_versions[tool] = result.stdout.strip() if result.returncode == 0 else "Not found"
            except:
                tool_versions[tool] = "Not found"
        
        return {
            "workflow_id": self.workflow_id,
            "user_prompt": self.user_prompt,
            "created_at": self.created_at,
            "system_info": system_info,
            "tool_versions": tool_versions,
            "workspace_dir": self.workspace_dir,
            "temp_dir": self.temp_dir,
            "stages": [
                {
                    "stage": stage.stage.value if isinstance(stage.stage, Enum) else stage.stage,
                    "status": stage.status,
                    "output": stage.output,
                    "error": stage.error,
                    "error_type": stage.error_type,
                    "timestamp": stage.timestamp,
                    "duration_ms": stage.duration_ms,
                    "metadata": stage.metadata
                }
                for stage in self.stages
            ],
            "errors": self.errors,
            "retry_attempts": self.retry_attempts,
            "detected_dependencies": self.detected_dependencies,
            "installed_dependencies": self.installed_dependencies,
            "contract_info": {
                "name": self.contract_name,
                "path": self.contract_path,
                "category": self.contract_category,
            },
            "compilation": {
                "success": self.compilation_success,
                "artifact_path": self.compilation_artifact_path,
            },
            "audit": self.audit_results,
            "deployment": {
                "address": self.deployment_address,
                "tx_hash": self.deployment_tx_hash,
                "network": self.deployment_network,
            },
            "verification": {
                "status": self.verification_status,
                "url": self.verification_url,
            },
            "metadata": self.metadata,
        }


class ContextManager:
    """
    Manager for workflow contexts.
    Handles persistence, retrieval, and diagnostics.
    """
    
    def __init__(self, workspace_dir: Path):
        """
        Initialize context manager.
        
        Args:
            workspace_dir: Base workspace directory
            
        Raises:
            RuntimeError: If contexts directory cannot be created or accessed
        """
        self.workspace_dir = Path(workspace_dir).resolve()
        self.contexts_dir = self.workspace_dir / ".workflow_contexts"
        
        # Robust directory creation with loud failures
        try:
            self.contexts_dir.mkdir(exist_ok=True, parents=True)
            
            # Validate directory was created and is accessible
            if not self.contexts_dir.exists():
                raise RuntimeError(
                    f"Failed to create contexts directory: {self.contexts_dir}\n"
                    f"Fix: mkdir -p {self.contexts_dir} && chmod +w {self.contexts_dir}"
                )
            
            # Check write permissions
            import os
            if not os.access(self.contexts_dir, os.W_OK):
                raise RuntimeError(
                    f"No write permission for contexts directory: {self.contexts_dir}\n"
                    f"Fix: chmod +w {self.contexts_dir}"
                )
            
            logger.info(f"ContextManager initialized - contexts dir: {self.contexts_dir}")
            
        except (OSError, PermissionError) as e:
            error_msg = (
                f"CRITICAL: Cannot create or access contexts directory: {self.contexts_dir}\n"
                f"Error: {str(e)}\n"
                f"Fix steps:\n"
                f"  1. mkdir -p {self.contexts_dir}\n"
                f"  2. chmod +w {self.contexts_dir}\n"
                f"  3. Check parent directory permissions: {self.contexts_dir.parent}"
            )
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e
    
    def create_context(self, workflow_id: str, user_prompt: str, 
                      workspace_dir: Optional[Path] = None) -> WorkflowContext:
        """Create a new workflow context"""
        context = WorkflowContext(
            workflow_id=workflow_id,
            user_prompt=user_prompt,
            workspace_dir=str(workspace_dir or self.workspace_dir)
        )
        return context
    
    def save_context(self, context: WorkflowContext):
        """Save context to disk"""
        file_path = self.contexts_dir / f"{context.workflow_id}.json"
        context.save_to_file(file_path)
    
    def load_context(self, workflow_id: str) -> Optional[WorkflowContext]:
        """Load context from disk"""
        file_path = self.contexts_dir / f"{workflow_id}.json"
        if file_path.exists():
            return WorkflowContext.from_file(file_path)
        return None
    
    def save_diagnostic_bundle(self, context: WorkflowContext) -> Path:
        """Save diagnostic bundle for a context"""
        bundle = context.generate_diagnostic_bundle()
        file_path = self.contexts_dir / f"{context.workflow_id}_diagnostics.json"
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(bundle, f, indent=2)
        logger.info(f"📋 Diagnostic bundle saved: {file_path}")
        return file_path
    
    def get_context_path(self, workflow_id: str) -> Path:
        """Get path to context file for a workflow"""
        return self.contexts_dir / f"{workflow_id}.json"

