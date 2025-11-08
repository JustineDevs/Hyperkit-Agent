"""
Workflow State Persistence
Handles YAML serialization for structured state and Markdown journaling for human-readable logs.
"""

import logging
import yaml
from pathlib import Path
from typing import Optional
from datetime import datetime
from core.workflow.workflow_state import WorkflowState, LoopStep

logger = logging.getLogger(__name__)


class StatePersistence:
    """Handles persistence of workflow state in YAML and Markdown formats"""
    
    def __init__(self, workspace_dir: Path):
        """
        Initialize state persistence.
        
        Args:
            workspace_dir: Base workspace directory
        """
        self.workspace_dir = Path(workspace_dir)
        self.states_dir = self.workspace_dir / ".workflow_states"
        self.states_dir.mkdir(exist_ok=True, parents=True)
        logger.info(f"StatePersistence initialized - states dir: {self.states_dir}")
    
    def save_state(self, state: WorkflowState) -> Path:
        """
        Save workflow state to YAML file.
        
        Args:
            state: WorkflowState to save
            
        Returns:
            Path to saved YAML file
        """
        workflow_dir = self.states_dir / state.workflow_id
        workflow_dir.mkdir(exist_ok=True, parents=True)
        
        yaml_path = workflow_dir / "workflow_state.yaml"
        
        # Convert to dict and save as YAML
        state_dict = state.to_dict()
        with open(yaml_path, 'w', encoding='utf-8') as f:
            yaml.dump(state_dict, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        
        logger.debug(f"💾 Workflow state saved to: {yaml_path}")
        return yaml_path
    
    def load_state(self, workflow_id: str) -> Optional[WorkflowState]:
        """
        Load workflow state from YAML file.
        
        Args:
            workflow_id: Workflow ID to load
            
        Returns:
            WorkflowState if found, None otherwise
        """
        # Validate workflow_id - ensure it's a string and not a Sentinel
        from cli.utils.sentinel_validator import validate_string_param
        workflow_id = validate_string_param(workflow_id, "workflow_id")
        if workflow_id is None:
            return None
        
        yaml_path = self.states_dir / workflow_id / "workflow_state.yaml"
        
        if not yaml_path.exists():
            return None
        
        try:
            with open(yaml_path, 'r', encoding='utf-8') as f:
                state_dict = yaml.safe_load(f)
            
            if not state_dict:
                return None
            
            return WorkflowState.from_dict(state_dict)
        except Exception as e:
            logger.error(f"Failed to load workflow state: {e}")
            return None
    
    def append_log_entry(self, state: WorkflowState, entry_type: str, 
                        content: str, metadata: dict = None):
        """
        Append entry to Markdown log file.
        
        Args:
            state: WorkflowState
            entry_type: Type of log entry (reasoning, tool_invocation, error, etc.)
            content: Log content
            metadata: Additional metadata
        """
        workflow_dir = self.states_dir / state.workflow_id
        workflow_dir.mkdir(exist_ok=True, parents=True)
        
        log_path = workflow_dir / "workflow_log.md"
        
        # Create or append to log file
        timestamp = datetime.utcnow().isoformat()
        
        log_entry = f"""
## {entry_type.title()} - {timestamp}

{content}

"""
        
        if metadata:
            log_entry += "**Metadata:**\n"
            for key, value in metadata.items():
                log_entry += f"- {key}: {value}\n"
            log_entry += "\n"
        
        # Append to file
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(log_entry)
    
    def generate_full_log(self, state: WorkflowState) -> str:
        """
        Generate full Markdown log from workflow state.
        
        Args:
            state: WorkflowState to generate log for
            
        Returns:
            Complete Markdown log content
        """
        log_lines = [
            f"# Workflow Log: {state.workflow_id}",
            "",
            f"**Created:** {state.created_at}",
            f"**Last Updated:** {state.updated_at}",
            f"**Status:** {'Complete' if state.is_complete else 'In Progress'}",
            f"**Current Step:** {state.current_step.value}",
            "",
            f"## User Goal",
            "",
            f"{state.user_goal}",
            "",
        ]
        
        # Add reasoning history
        if state.reasoning_history:
            log_lines.append("## Agent Reasoning History")
            log_lines.append("")
            for reasoning in state.reasoning_history:
                log_lines.append(f"### {reasoning.step.value.title()} - {reasoning.timestamp}")
                log_lines.append("")
                log_lines.append(f"**Reasoning:** {reasoning.reasoning}")
                log_lines.append("")
                if reasoning.plan:
                    log_lines.append("**Plan:**")
                    for action in reasoning.plan:
                        log_lines.append(f"- {action}")
                    log_lines.append("")
                if reasoning.constraints:
                    log_lines.append("**Constraints:**")
                    for key, value in reasoning.constraints.items():
                        log_lines.append(f"- {key}: {value}")
                    log_lines.append("")
                log_lines.append(f"**Confidence:** {reasoning.confidence:.2f}")
                log_lines.append("")
        
        # Add tool invocations
        if state.tool_invocations:
            log_lines.append("## Tool Invocations")
            log_lines.append("")
            for invocation in state.tool_invocations:
                log_lines.append(f"### {invocation.tool_name} - {invocation.timestamp}")
                log_lines.append("")
                log_lines.append("**Parameters:**")
                log_lines.append("```yaml")
                log_lines.append(yaml.dump(invocation.parameters, default_flow_style=False))
                log_lines.append("```")
                log_lines.append("")
                if invocation.result:
                    log_lines.append("**Result:**")
                    log_lines.append("```yaml")
                    log_lines.append(yaml.dump(invocation.result, default_flow_style=False))
                    log_lines.append("```")
                    log_lines.append("")
                if invocation.error:
                    log_lines.append(f"**Error:** {invocation.error}")
                    log_lines.append("")
                if invocation.duration_ms:
                    log_lines.append(f"**Duration:** {invocation.duration_ms:.2f}ms")
                    log_lines.append("")
        
        # Add error history
        if state.error_history:
            log_lines.append("## Error History")
            log_lines.append("")
            for error in state.error_history[-10:]:  # Last 10 errors
                log_lines.append(f"### {error.get('timestamp', 'Unknown')}")
                log_lines.append("")
                log_lines.append(f"**Error:** {error.get('error', 'Unknown')}")
                log_lines.append(f"**Type:** {error.get('error_type', 'Unknown')}")
                log_lines.append(f"**Stage:** {error.get('stage', 'Unknown')}")
                log_lines.append(f"**Retry Count:** {error.get('retry_count', 0)}")
                log_lines.append("")
        
        # Add next action if planned
        if state.next_action:
            log_lines.append("## Next Planned Action")
            log_lines.append("")
            log_lines.append(f"**Tool:** {state.next_action.tool_name or 'None'}")
            log_lines.append(f"**Step:** {state.next_action.step.value}")
            log_lines.append(f"**Reasoning:** {state.next_action.reasoning}")
            log_lines.append("")
        
        return "\n".join(log_lines)
    
    def save_full_log(self, state: WorkflowState) -> Path:
        """
        Save complete Markdown log to file.
        
        Args:
            state: WorkflowState to generate log for
            
        Returns:
            Path to saved Markdown log file
        """
        workflow_dir = self.states_dir / state.workflow_id
        workflow_dir.mkdir(exist_ok=True, parents=True)
        
        log_path = workflow_dir / "workflow_log.md"
        log_content = self.generate_full_log(state)
        
        with open(log_path, 'w', encoding='utf-8') as f:
            f.write(log_content)
        
        logger.debug(f"📝 Workflow log saved to: {log_path}")
        return log_path
    
    def get_state_path(self, workflow_id: str) -> Path:
        """Get path to state YAML file"""
        # Validate workflow_id using centralized utility
        from cli.utils.sentinel_validator import validate_string_param
        validated_id = validate_string_param(workflow_id, "workflow_id")
        if validated_id is None:
            raise ValueError("Invalid workflow_id: cannot be None or Sentinel")
        return self.states_dir / validated_id / "workflow_state.yaml"
    
    def get_log_path(self, workflow_id: str) -> Path:
        """Get path to log Markdown file"""
        # Validate workflow_id using centralized utility
        from cli.utils.sentinel_validator import validate_string_param
        validated_id = validate_string_param(workflow_id, "workflow_id")
        if validated_id is None:
            raise ValueError("Invalid workflow_id: cannot be None or Sentinel")
        return self.states_dir / validated_id / "workflow_log.md"

