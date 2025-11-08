"""
Workflow State Management
Tracks autonomous agent loop state (read/plan/act/update) with reasoning and tool invocations.
"""

import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, List
from pathlib import Path

logger = logging.getLogger(__name__)


class LoopStep(Enum):
    """Autonomous loop step identifiers"""
    READ = "read"
    PLAN = "plan"
    ACT = "act"
    UPDATE = "update"
    COMPLETE = "complete"
    ERROR = "error"


@dataclass
class AgentReasoning:
    """Agent's reasoning and planning for next actions"""
    step: LoopStep
    reasoning: str  # Why this action was chosen
    plan: List[str]  # Planned sequence of actions
    constraints: Dict[str, Any] = field(default_factory=dict)  # Constraints to consider
    confidence: float = 1.0  # Confidence in plan (0.0-1.0)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class ToolInvocation:
    """Record of a tool invocation"""
    tool_name: str
    parameters: Dict[str, Any]
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    duration_ms: Optional[float] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class ActionPlan:
    """Plan for next action(s)"""
    step: LoopStep
    tool_name: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    reasoning: str = ""
    expected_outcome: str = ""
    fallback_plan: Optional['ActionPlan'] = None


@dataclass
class ActionResult:
    """Result of an action execution"""
    success: bool
    output: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    error_type: Optional[str] = None
    tool_invocation: Optional[ToolInvocation] = None
    duration_ms: Optional[float] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class WorkflowState:
    """
    Autonomous workflow state tracking read/plan/act/update cycle.
    Persists agent reasoning, tool invocations, and next planned actions.
    """
    
    # Workflow identification
    workflow_id: str
    user_goal: str
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    # Current loop state
    current_step: LoopStep = LoopStep.READ
    current_stage: Optional[str] = None  # Pipeline stage (e.g., "generation", "auditing")
    
    # Agent reasoning history
    reasoning_history: List[AgentReasoning] = field(default_factory=list)
    current_reasoning: Optional[AgentReasoning] = None
    
    # Tool invocations
    tool_invocations: List[ToolInvocation] = field(default_factory=list)
    
    # Next planned actions
    next_action: Optional[ActionPlan] = None
    action_queue: List[ActionPlan] = field(default_factory=list)
    
    # Context and state
    context_snapshot: Dict[str, Any] = field(default_factory=dict)  # Current context state
    rag_context: Optional[str] = None
    error_history: List[Dict[str, Any]] = field(default_factory=list)
    retry_counts: Dict[str, int] = field(default_factory=dict)
    
    # Workflow status
    is_complete: bool = False
    has_error: bool = False
    error_message: Optional[str] = None
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_reasoning(self, step: LoopStep, reasoning: str, plan: List[str], 
                     constraints: Dict[str, Any] = None, confidence: float = 1.0):
        """Add agent reasoning for a step"""
        reasoning_obj = AgentReasoning(
            step=step,
            reasoning=reasoning,
            plan=plan,
            constraints=constraints or {},
            confidence=confidence
        )
        self.reasoning_history.append(reasoning_obj)
        self.current_reasoning = reasoning_obj
        self.current_step = step
        self.updated_at = datetime.utcnow().isoformat()
    
    def add_tool_invocation(self, tool_name: str, parameters: Dict[str, Any],
                           result: Optional[Dict[str, Any]] = None,
                           error: Optional[str] = None,
                           duration_ms: Optional[float] = None):
        """Record a tool invocation"""
        invocation = ToolInvocation(
            tool_name=tool_name,
            parameters=parameters,
            result=result,
            error=error,
            duration_ms=duration_ms
        )
        self.tool_invocations.append(invocation)
        self.updated_at = datetime.utcnow().isoformat()
        return invocation
    
    def set_next_action(self, action_plan: ActionPlan):
        """Set the next planned action"""
        self.next_action = action_plan
        self.updated_at = datetime.utcnow().isoformat()
    
    def queue_action(self, action_plan: ActionPlan):
        """Add action to queue"""
        self.action_queue.append(action_plan)
        self.updated_at = datetime.utcnow().isoformat()
    
    def get_next_action(self) -> Optional[ActionPlan]:
        """Get and remove next action (from next_action or queue)"""
        if self.next_action:
            action = self.next_action
            self.next_action = None
            self.updated_at = datetime.utcnow().isoformat()
            return action
        elif self.action_queue:
            action = self.action_queue.pop(0)
            self.updated_at = datetime.utcnow().isoformat()
            return action
        return None
    
    def update_context_snapshot(self, snapshot: Dict[str, Any]):
        """Update context snapshot"""
        self.context_snapshot.update(snapshot)
        self.updated_at = datetime.utcnow().isoformat()
    
    def record_error(self, error: str, error_type: str, stage: Optional[str] = None):
        """Record an error"""
        error_entry = {
            "error": error,
            "error_type": error_type,
            "stage": stage or self.current_stage,
            "step": self.current_step.value,
            "timestamp": datetime.utcnow().isoformat(),
            "retry_count": self.retry_counts.get(stage or "unknown", 0)
        }
        self.error_history.append(error_entry)
        if len(self.error_history) > 50:
            self.error_history.pop(0)  # Keep last 50 errors
        self.has_error = True
        self.error_message = error
        self.updated_at = datetime.utcnow().isoformat()
    
    def increment_retry(self, stage: str):
        """Increment retry count for a stage"""
        self.retry_counts[stage] = self.retry_counts.get(stage, 0) + 1
        self.updated_at = datetime.utcnow().isoformat()
    
    def mark_complete(self):
        """Mark workflow as complete"""
        self.is_complete = True
        self.current_step = LoopStep.COMPLETE
        self.updated_at = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        # Convert Enums to strings
        def convert_enums(obj):
            if isinstance(obj, LoopStep):
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
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkflowState':
        """Create WorkflowState from dictionary"""
        # Convert string enums back to Enum objects
        def restore_enums(obj):
            if isinstance(obj, dict):
                if "step" in obj and isinstance(obj["step"], str):
                    try:
                        obj["step"] = LoopStep(obj["step"])
                    except ValueError:
                        pass
                if "current_step" in obj and isinstance(obj["current_step"], str):
                    try:
                        obj["current_step"] = LoopStep(obj["current_step"])
                    except ValueError:
                        pass
                return {k: restore_enums(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [restore_enums(item) for item in obj]
            else:
                return obj
        
        data = restore_enums(data)
        return cls(**data)

