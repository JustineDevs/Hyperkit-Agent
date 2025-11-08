"""
Self-Healing Workflow Orchestrator
Orchestrates the complete pipeline with dependency management, context tracking, and auto-recovery.
"""

import asyncio
import logging
import os
import time
import uuid
import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

# CRITICAL: PipelineStage MUST be imported at module level only - never locally
# This enum is used throughout the orchestrator and must always be in module scope
from core.workflow.context_manager import (
    ContextManager, WorkflowContext, PipelineStage, StageResult
)
from core.workflow.workflow_state import (
    WorkflowState, LoopStep, AgentReasoning, ActionPlan, ActionResult, ToolInvocation
)
from core.workflow.state_persistence import StatePersistence

# Defensive check: Ensure PipelineStage is properly imported at module level
if not hasattr(PipelineStage, "GENERATION"):
    raise ImportError("PipelineStage not properly imported at module level - check imports")
from core.workflow.error_handler import SelfHealingErrorHandler, handle_error_with_retry
from core.workflow.environment_manager import EnvironmentManager
from services.dependencies.dependency_manager import DependencyManager

logger = logging.getLogger(__name__)

# Optional import for agent memory (Phase 3 feature)
try:
    from core.workflow.agent_memory import AgentMemory
    AGENT_MEMORY_AVAILABLE = True
except ImportError:
    AGENT_MEMORY_AVAILABLE = False
    logger.debug("Agent memory system not available")

# Optional import for adaptive prompt repair (Phase 3 feature)
try:
    from core.workflow.adaptive_prompt_repair import AdaptivePromptRepair
    ADAPTIVE_REPAIR_AVAILABLE = True
except ImportError:
    ADAPTIVE_REPAIR_AVAILABLE = False
    logger.debug("Adaptive prompt repair not available")

# Optional import for guardrails (Phase 3 feature)
try:
    from core.workflow.guardrails import Guardrails
    GUARDRAILS_AVAILABLE = True
except ImportError:
    GUARDRAILS_AVAILABLE = False
    logger.debug("Guardrails system not available")

# Optional import for audit trail (Phase 3 feature)
try:
    from core.workflow.audit_trail import AuditTrail, AuditEventType
    AUDIT_TRAIL_AVAILABLE = True
except ImportError:
    AUDIT_TRAIL_AVAILABLE = False
    logger.debug("Audit trail system not available")


class WorkflowOrchestrator:
    """
    Self-healing workflow orchestrator that manages the complete pipeline.
    Handles dependency resolution, context persistence, error recovery, and auto-fixes.
    """
    
    def __init__(self, agent, workspace_dir: Path):
        """
        Initialize workflow orchestrator.
        
        Args:
            agent: HyperKitAgent instance
            workspace_dir: Base workspace directory
        """
        self.agent = agent
        self.workspace_dir = Path(workspace_dir)
        
        # Initialize managers
        self.context_manager = ContextManager(self.workspace_dir)
        self.state_persistence = StatePersistence(self.workspace_dir)
        self.error_handler = SelfHealingErrorHandler()
        self.dep_manager = DependencyManager(self.workspace_dir)
        self.env_manager: Optional[EnvironmentManager] = None
        
        # Initialize tool registry (Phase 2)
        from core.tools.registry import ToolRegistry, ToolExecutor
        from core.tools.agent_tools import create_agent_tools
        self.tool_registry = ToolRegistry()
        self.tool_executor = ToolExecutor(self.tool_registry)
        
        # Register agent tools
        try:
            agent_tools = create_agent_tools(agent)
            for tool in agent_tools:
                self.tool_registry.register(tool)
            logger.info(f"Registered {len(agent_tools)} agent tools")
        except Exception as e:
            logger.warning(f"Failed to register agent tools: {e}")
        
        # Initialize agent memory system (Phase 3 feature)
        self.agent_memory: Optional[AgentMemory] = None
        if AGENT_MEMORY_AVAILABLE:
            try:
                self.agent_memory = AgentMemory(self.workspace_dir)
                logger.info("Agent memory system initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize agent memory: {e}")
        
        # Initialize adaptive prompt repair system (Phase 3 feature)
        self.prompt_repair: Optional[AdaptivePromptRepair] = None
        if ADAPTIVE_REPAIR_AVAILABLE:
            try:
                # Get LLM router from agent for meta-prompting
                llm_router = getattr(agent, 'llm_router', None) if hasattr(agent, 'llm_router') else None
                self.prompt_repair = AdaptivePromptRepair(agent_memory=self.agent_memory, llm_router=llm_router)
                logger.info("Adaptive prompt repair system initialized with meta-prompting")
            except Exception as e:
                logger.warning(f"Failed to initialize adaptive prompt repair: {e}")
        
        # Initialize guardrails system (Phase 3 feature)
        self.guardrails: Optional[Guardrails] = None
        if GUARDRAILS_AVAILABLE:
            try:
                # Load config for guardrails
                from core.config.loader import get_config
                config = get_config().to_dict()
                guardrails_config = config.get('guardrails', {})
                self.guardrails = Guardrails(self.workspace_dir, guardrails_config)
                logger.info("Guardrails system initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize guardrails: {e}")
        
        # Initialize audit trail system (Phase 3 feature)
        self.audit_trail: Optional[AuditTrail] = None
        if AUDIT_TRAIL_AVAILABLE:
            try:
                self.audit_trail = AuditTrail(self.workspace_dir)
                logger.info("Audit trail system initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize audit trail: {e}")
        
        logger.info("WorkflowOrchestrator initialized with self-healing capabilities")
    
    async def _read_workflow_state(self, context: WorkflowContext) -> WorkflowState:
        """
        READ step: Load workflow state, context, and RAG results.
        
        Args:
            context: Current workflow context
            
        Returns:
            WorkflowState with current state loaded
        """
        workflow_state = self.state_persistence.load_state(context.workflow_id)
        if not workflow_state:
            # Create new state if not found
            workflow_state = WorkflowState(
                workflow_id=context.workflow_id,
                user_goal=context.user_prompt,
                current_step=LoopStep.READ
            )
        
        # Update context snapshot from WorkflowContext
        workflow_state.update_context_snapshot({
            "last_successful_stage": context.get_last_successful_stage().value if context.get_last_successful_stage() else None,
            "has_errors": context.has_error(),
            "retry_counts": context.retry_attempts,
            "error_count": len(context.error_history)
        })
        
        workflow_state.add_reasoning(
            step=LoopStep.READ,
            reasoning=f"Reading workflow state for {context.workflow_id}. Last successful stage: {context.get_last_successful_stage().value if context.get_last_successful_stage() else 'none'}",
            plan=["Load state", "Load context", "Load RAG context"],
            confidence=1.0
        )
        
        self.state_persistence.save_state(workflow_state)
        self.state_persistence.append_log_entry(
            workflow_state,
            "read",
            f"Loaded workflow state. Current step: {workflow_state.current_step.value}"
        )
        
        return workflow_state
    
    async def _plan_next_action(self, state: WorkflowState, context: WorkflowContext, 
                               stage: PipelineStage) -> ActionPlan:
        """
        PLAN step: Agent reasons about next actions.
        
        Args:
            state: Current workflow state
            context: Current workflow context
            stage: Pipeline stage to plan for
            
        Returns:
            ActionPlan for next action
        """
        # Determine tool based on stage
        stage_to_tool = {
            PipelineStage.INPUT_PARSING: "query_ipfs_rag",
            PipelineStage.GENERATION: "generate_contract",
            PipelineStage.DEPENDENCY_RESOLUTION: "analyze_dependencies",
            PipelineStage.COMPILATION: "run_linter",  # Compilation is handled by Foundry
            PipelineStage.TESTING: "run_tests",
            PipelineStage.AUDITING: "audit_contract",
            PipelineStage.DEPLOYMENT: "deploy_contract",
            PipelineStage.VERIFICATION: "verify_contract"
        }
        
        tool_name = stage_to_tool.get(stage, "unknown")
        
        # Build reasoning
        reasoning = f"Planning {stage.value} stage. Tool: {tool_name}"
        if state.error_history:
            last_error = state.error_history[-1]
            reasoning += f". Previous error in {last_error.get('stage', 'unknown')}: {last_error.get('error', 'unknown')[:100]}"
        
        # Create action plan
        action_plan = ActionPlan(
            step=LoopStep.PLAN,
            tool_name=tool_name,
            parameters={"stage": stage.value},
            reasoning=reasoning,
            expected_outcome=f"Successfully complete {stage.value} stage"
        )
        
        state.add_reasoning(
            step=LoopStep.PLAN,
            reasoning=reasoning,
            plan=[f"Execute {tool_name} for {stage.value}"],
            constraints={"stage": stage.value, "retry_count": state.retry_counts.get(stage.value, 0)},
            confidence=0.9 if state.retry_counts.get(stage.value, 0) == 0 else 0.7
        )
        
        state.set_next_action(action_plan)
        state.current_stage = stage.value
        self.state_persistence.save_state(state)
        self.state_persistence.append_log_entry(
            state,
            "plan",
            reasoning,
            {"tool": tool_name, "stage": stage.value}
        )
        
        return action_plan
    
    async def _execute_action(self, action_plan: ActionPlan, state: WorkflowState, 
                            context: WorkflowContext) -> ActionResult:
        """
        ACT step: Execute selected tool(s).
        
        Args:
            action_plan: Planned action to execute
            state: Current workflow state
            context: Current workflow context
            
        Returns:
            ActionResult with execution results
        """
        import time
        start_time = time.time()
        
        state.current_step = LoopStep.ACT
        self.state_persistence.save_state(state)
        
        try:
            # Get parameters from context metadata or action plan
            user_prompt = context.user_prompt
            rag_scope = context.metadata.get('rag_scope', 'official-only')
            network = context.metadata.get('network', 'hyperion')
            allow_insecure = context.metadata.get('allow_insecure', False)
            
            # Map tool names to actual stage methods with proper parameters
            tool_to_stage_method = {
                "query_ipfs_rag": lambda: self._stage_input_parsing(context, user_prompt, rag_scope),
                "generate_contract": lambda: self._stage_generation(context, user_prompt, rag_scope),
                "analyze_dependencies": lambda: self._stage_dependency_resolution(context),
                "run_linter": lambda: self._stage_compilation(context),
                "run_tests": lambda: self._stage_testing(context),
                "audit_contract": lambda: self._stage_auditing(context),
                "deploy_contract": lambda: self._stage_deployment(context, network, allow_insecure),
                "verify_contract": lambda: self._stage_verification(context, network)
            }
            
            # Execute the stage method
            if action_plan.tool_name in tool_to_stage_method:
                await tool_to_stage_method[action_plan.tool_name]()
                duration_ms = (time.time() - start_time) * 1000
                
                # Get the last stage result
                last_result = context.get_last_stage_result()
                success = last_result.status == "success" if last_result else False
                
                # Record tool invocation
                invocation = state.add_tool_invocation(
                    tool_name=action_plan.tool_name,
                    parameters=action_plan.parameters,
                    result={"status": last_result.status, "output": last_result.output} if last_result else None,
                    error=last_result.error if last_result and last_result.error else None,
                    duration_ms=duration_ms
                )
                
                result = ActionResult(
                    success=success,
                    output=last_result.output if last_result else {},
                    error=last_result.error if last_result else None,
                    error_type=last_result.error_type if last_result else None,
                    tool_invocation=invocation,
                    duration_ms=duration_ms
                )
            else:
                # Unknown tool
                result = ActionResult(
                    success=False,
                    error=f"Unknown tool: {action_plan.tool_name}",
                    error_type="UnknownToolError"
                )
            
            self.state_persistence.append_log_entry(
                state,
                "act",
                f"Executed {action_plan.tool_name}",
                {"success": result.success, "duration_ms": result.duration_ms}
            )
            
            return result
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            error_msg = str(e)
            
            state.add_tool_invocation(
                tool_name=action_plan.tool_name,
                parameters=action_plan.parameters,
                error=error_msg,
                duration_ms=duration_ms
            )
            
            state.record_error(error_msg, type(e).__name__, state.current_stage)
            
            result = ActionResult(
                success=False,
                error=error_msg,
                error_type=type(e).__name__,
                duration_ms=duration_ms
            )
            
            self.state_persistence.append_log_entry(
                state,
                "act_error",
                f"Failed to execute {action_plan.tool_name}: {error_msg}",
                {"error_type": type(e).__name__}
            )
            
            return result
    
    async def _update_workflow_state(self, state: WorkflowState, action_result: ActionResult, 
                                    context: WorkflowContext) -> WorkflowState:
        """
        UPDATE step: Persist results to workflow_state and markdown log.
        
        Args:
            state: Current workflow state
            action_result: Result from action execution
            context: Current workflow context
            
        Returns:
            Updated WorkflowState
        """
        state.current_step = LoopStep.UPDATE
        
        # Update context snapshot
        state.update_context_snapshot({
            "last_action": state.tool_invocations[-1].tool_name if state.tool_invocations else None,
            "last_action_success": action_result.success,
            "last_stage": context.get_last_stage_result().stage.value if context.get_last_stage_result() else None,
            "has_errors": context.has_error()
        })
        
        # Clear next action if completed
        if action_result.success:
            state.next_action = None
        else:
            # Plan retry or escalation
            if state.retry_counts.get(state.current_stage or "unknown", 0) < 3:
                # Will retry - keep action plan
                pass
            else:
                # Max retries exceeded - clear action
                state.next_action = None
                state.has_error = True
        
        # Save state and log
        self.state_persistence.save_state(state)
        self.state_persistence.save_full_log(state)
        
        self.state_persistence.append_log_entry(
            state,
            "update",
            f"Updated workflow state. Action success: {action_result.success}",
            {"step": state.current_step.value, "stage": state.current_stage}
        )
        
        return state
    
    async def _autonomous_loop(self, context: WorkflowContext, stage: PipelineStage) -> bool:
        """
        Execute autonomous read/plan/act/update loop for a stage.
        
        Args:
            context: Workflow context
            stage: Pipeline stage to execute
            
        Returns:
            True if stage completed successfully, False otherwise
        """
        # READ: Load workflow state
        state = await self._read_workflow_state(context)
        
        # PLAN: Determine next action
        action_plan = await self._plan_next_action(state, context, stage)
        
        # ACT: Execute action
        action_result = await self._execute_action(action_plan, state, context)
        
        # UPDATE: Persist results
        await self._update_workflow_state(state, action_result, context)
        
        return action_result.success
    
    async def run_complete_workflow(
        self,
        user_prompt: str,
        network: str = "hyperion",
        auto_verification: bool = True,
        test_only: bool = False,
        allow_insecure: bool = False,
        upload_scope: Optional[str] = None,  # 'team' or 'community'
        rag_scope: str = 'official-only',  # 'official-only' or 'opt-in-community'
        resume_from_diagnostic: Optional[str] = None  # Path to diagnostic bundle for recovery
    ) -> Dict[str, Any]:
        """
        Execute complete self-healing workflow with all automation.
        
        Pipeline stages:
        1. Preflight checks & setup
        2. Input parsing & context retrieval
        3. Contract generation
        4. Dependency resolution & installation
        5. Compilation
        6. Testing (optional)
        7. Auditing
        8. Deployment (if not test-only)
        9. Verification (if deployed)
        10. Output & diagnostics
        
        Args:
            user_prompt: User's natural language request
            network: Target blockchain network
            auto_verification: Whether to auto-verify contract
            test_only: Test mode (no deployment)
            allow_insecure: Allow deployment despite audit issues
            
        Returns:
            Complete workflow results with diagnostics
        """
        # Check if resuming from diagnostic bundle
        # Filter out None, empty strings, and Click Sentinel objects
        resume_path_str = None
        if resume_from_diagnostic and isinstance(resume_from_diagnostic, (str, os.PathLike)):
            # Convert to string if it's a PathLike object
            resume_path_str = str(resume_from_diagnostic)
            if resume_path_str and resume_path_str.strip():
                logger.info(f"🔄 Resuming workflow from diagnostic bundle: {resume_path_str}")
                try:
                    diagnostic_path = Path(resume_path_str)
                    if not diagnostic_path.exists():
                        logger.error(f"Diagnostic bundle not found: {resume_path_str}")
                        return {
                            "status": "error",
                            "error": f"Diagnostic bundle not found: {resume_path_str}",
                            "suggestions": ["Verify the diagnostic bundle path is correct"]
                        }
                    
                    # Load diagnostic bundle
                    with open(diagnostic_path, 'r') as f:
                        diagnostic_data = json.load(f)
                    
                    # Extract workflow_id and recreate context
                    workflow_id = diagnostic_data.get('workflow_id', str(uuid.uuid4())[:8])
                    context = self.context_manager.create_context(workflow_id, diagnostic_data.get('user_prompt', user_prompt), self.workspace_dir)
                    
                    # Load or create workflow state
                    workflow_state = self.state_persistence.load_state(workflow_id)
                    if not workflow_state:
                        workflow_state = WorkflowState(
                            workflow_id=workflow_id,
                            user_goal=diagnostic_data.get('user_prompt', user_prompt),
                            current_step=LoopStep.READ
                        )
                    
                    # Restore context state from diagnostic bundle
                    if 'stages' in diagnostic_data:
                        context.stages = []
                        for stage_data in diagnostic_data['stages']:
                            # PipelineStage and StageResult are available from module-level import (line 16)
                            # Do NOT re-import - this creates local scope that shadows module-level import
                            stage_result = StageResult(
                                stage=PipelineStage(stage_data['stage']),
                                status=stage_data['status'],
                                output=stage_data.get('output', {}),
                                error=stage_data.get('error'),
                                error_type=stage_data.get('error_type'),
                                timestamp=stage_data.get('timestamp', datetime.utcnow().isoformat()),
                                duration_ms=stage_data.get('duration_ms')
                            )
                            context.stages.append(stage_result)
                    
                    # Restore contract info if available
                    if 'contract_info' in diagnostic_data:
                        contract_info = diagnostic_data['contract_info']
                        context.contract_name = contract_info.get('name')
                        context.contract_path = contract_info.get('path')
                        context.contract_category = contract_info.get('category')
                    
                    # Restore compilation info
                    if 'compilation' in diagnostic_data:
                        context.compilation_success = diagnostic_data['compilation'].get('success', False)
                        context.compilation_artifact_path = diagnostic_data['compilation'].get('artifact_path')
                    
                    # Restore deployment info
                    if 'deployment' in diagnostic_data:
                        deployment_info = diagnostic_data['deployment']
                        context.deployment_address = deployment_info.get('address')
                        context.deployment_tx_hash = deployment_info.get('tx_hash')
                        context.deployment_network = deployment_info.get('network')
                    
                    logger.info(f"✅ Loaded diagnostic bundle - resuming from stage: {context.get_last_successful_stage()}")
                    
                except Exception as e:
                    logger.error(f"Failed to load diagnostic bundle: {e}")
                    return {
                        "status": "error",
                        "error": f"Failed to load diagnostic bundle: {str(e)}",
                        "suggestions": ["Check diagnostic bundle format", "Verify bundle is valid JSON"]
                    }
            else:
                # resume_path_str is empty or invalid - treat as None
                resume_path_str = None
        
        # If not resuming, create new workflow context and state
        if not resume_path_str:
            workflow_id = str(uuid.uuid4())[:8]
            context = self.context_manager.create_context(workflow_id, user_prompt, self.workspace_dir)
            
            # Create workflow state for autonomous loop
            workflow_state = WorkflowState(
                workflow_id=workflow_id,
                user_goal=user_prompt,
                current_step=LoopStep.READ
            )
            self.state_persistence.save_state(workflow_state)
            
            # Log prompt received (Phase 3 feature)
            if self.audit_trail:
                self.audit_trail.log_event(
                    AuditEventType.PROMPT_RECEIVED,
                    workflow_id,
                    details={"prompt_length": len(user_prompt), "rag_scope": rag_scope}
                )
        else:
            # Load existing workflow state if resuming
            workflow_state = self.state_persistence.load_state(context.workflow_id)
            if not workflow_state:
                # Create new state if not found
                workflow_state = WorkflowState(
                    workflow_id=context.workflow_id,
                    user_goal=user_prompt,
                    current_step=LoopStep.READ
                )
        
        # Ensure workflow_id is available
        workflow_id = context.workflow_id
        
        # Create isolated environment
        self.env_manager = EnvironmentManager(self.workspace_dir, workflow_id)
        temp_dir = self.env_manager.create_isolated_environment()
        context.temp_dir = str(temp_dir)
        context.metadata["temp_dir"] = str(temp_dir)
        
        # Update workflow state with environment info
        workflow_state.update_context_snapshot({
            "temp_dir": str(temp_dir),
            "workspace_dir": str(self.workspace_dir)
        })
        self.state_persistence.save_state(workflow_state)
        
        logger.info(f"🚀 Starting self-healing workflow: {workflow_id}")
        logger.info(f"📝 User prompt: {user_prompt}")
        logger.info(f"📁 Isolated environment: {temp_dir}")
        
        had_errors = False
        
        # Determine resume point if resuming from diagnostic bundle
        last_successful_stage = context.get_last_successful_stage() if resume_path_str else None
        
        try:
            # Resume from last successful stage if resuming from diagnostic bundle
            if resume_path_str and last_successful_stage:
                logger.info(f"🔄 Resuming workflow from stage: {last_successful_stage.value}")
                
                # Skip stages that already succeeded
                if last_successful_stage.value in ['input_parsing', 'generation']:
                    logger.info("Skipping preflight, input parsing, and generation (already completed)")
                elif last_successful_stage.value == 'dependency_resolution':
                    logger.info("Skipping preflight through dependency resolution (already completed)")
                elif last_successful_stage.value == 'compilation':
                    logger.info("Skipping preflight through compilation (already completed)")
                elif last_successful_stage.value == 'testing':
                    logger.info("Skipping preflight through testing (already completed)")
                elif last_successful_stage.value == 'auditing':
                    logger.info("Skipping preflight through auditing (already completed)")
                elif last_successful_stage.value == 'deployment':
                    logger.info("Skipping preflight through deployment (already completed)")
            
            # Store metadata for autonomous loop
            context.metadata['network'] = network
            context.metadata['rag_scope'] = rag_scope
            context.metadata['allow_insecure'] = allow_insecure
            
            # Stage 0: Preflight checks (skip if resuming past generation)
            if not resume_path_str or not last_successful_stage or last_successful_stage.value == 'input_parsing':
                await self._stage_preflight(context)
            
            # Stage 1: Input parsing & RAG context (skip if resuming past this)
            if not resume_path_str or not last_successful_stage or last_successful_stage.value == 'input_parsing':
                await self._autonomous_loop(context, PipelineStage.INPUT_PARSING)
            
            # Stage 2: Contract generation (skip if resuming past this)
            if not resume_path_str or not last_successful_stage or last_successful_stage.value in ['generation', 'input_parsing']:
                await self._autonomous_loop(context, PipelineStage.GENERATION)
            
            # Stage 3: Dependency resolution (skip if resuming past this)
            if not resume_path_str or not last_successful_stage or last_successful_stage.value in ['dependency_resolution', 'generation', 'input_parsing']:
                await self._autonomous_loop(context, PipelineStage.DEPENDENCY_RESOLUTION)
            
            # Stage 4: Compilation (skip if resuming past this)
            if not resume_path_str or not last_successful_stage or last_successful_stage.value in ['compilation', 'dependency_resolution', 'generation', 'input_parsing']:
                await self._autonomous_loop(context, PipelineStage.COMPILATION)
            
            # Stage 5: Testing (skip if resuming past this)
            if not test_only:
                if not resume_path_str or not last_successful_stage or last_successful_stage.value in ['testing', 'compilation', 'dependency_resolution', 'generation', 'input_parsing']:
                    await self._autonomous_loop(context, PipelineStage.TESTING)
            
            # Stage 6: Auditing (skip if resuming past this)
            if not resume_path_str or not last_successful_stage or last_successful_stage.value in ['auditing', 'testing', 'compilation', 'dependency_resolution', 'generation', 'input_parsing']:
                await self._autonomous_loop(context, PipelineStage.AUDITING)
            
            # Stage 7: Deployment (skip if resuming past this)
            deployment_success = False
            if not test_only:
                if not resume_path_str or not last_successful_stage or last_successful_stage.value in ['deployment', 'auditing', 'testing', 'compilation', 'dependency_resolution', 'generation', 'input_parsing']:
                    try:
                        await self._autonomous_loop(context, PipelineStage.DEPLOYMENT)
                        # Check if deployment actually succeeded
                        if context.deployment_address:
                            deployment_success = True
                    except Exception as deploy_error:
                        # Deployment failed - log but don't crash workflow
                        logger.error(f"❌ Deployment stage failed: {deploy_error}")
                        logger.info("💡 Workflow continuing - deployment failure is logged in context")
                        # Deployment stage result already added in _stage_deployment
                        deployment_success = False
            
            # Stage 8: Verification & Artifact Storage (only if deployment succeeded)
            if not test_only and auto_verification and deployment_success and context.deployment_address:
                if not resume_path_str or not last_successful_stage or last_successful_stage.value in ['verification', 'deployment', 'auditing', 'testing', 'compilation', 'dependency_resolution', 'generation', 'input_parsing']:
                    try:
                        await self._autonomous_loop(context, PipelineStage.VERIFICATION)
                    except Exception as verify_error:
                        # Verification failed - log but don't crash workflow
                        logger.warning(f"⚠️ Verification stage failed: {verify_error}")
                        logger.info("💡 Workflow continuing - verification failure is logged")
                        # Verification stage result already added in _stage_verification
            elif not test_only and auto_verification and not deployment_success:
                # Skip verification if deployment failed
                logger.info("⏭️ Skipping verification - deployment did not succeed")
                context.add_stage_result(
                    PipelineStage.VERIFICATION,
                    "skipped",
                    output={"reason": "Deployment failed - no contract address to verify"},
                    duration_ms=0
                )
            
            # Stage 9: Output & diagnostics (always runs)
            result = await self._stage_output(context, upload_scope)
            
            # Add workflow_id to result for CLI monitoring (Phase 5)
            result['workflow_id'] = context.workflow_id
            
            # Mark workflow state as complete
            final_state = self.state_persistence.load_state(context.workflow_id)
            if final_state:
                final_state.mark_complete()
                self.state_persistence.save_state(final_state)
                self.state_persistence.save_full_log(final_state)
            
            # Save workflow to agent memory for learning (Phase 3 feature)
            if self.agent_memory:
                try:
                    diagnostic_bundle = context.generate_diagnostic_bundle()
                    self.agent_memory.add_workflow(diagnostic_bundle)
                    logger.debug("Workflow saved to agent memory")
                except Exception as mem_error:
                    logger.warning(f"Failed to save workflow to agent memory: {mem_error}")
            
            # Determine final workflow status based on critical stages
            # Critical: generation, compilation (these must succeed)
            # Non-critical: deployment, verification (can fail but workflow completes)
            critical_stages = [PipelineStage.GENERATION, PipelineStage.COMPILATION]
            critical_failures = [
                s for s in context.stages 
                if s.stage in critical_stages and s.status == "error"
            ]
            
            if critical_failures:
                # Critical stage failed - workflow status is error
                result["status"] = "error"
                result["critical_failure"] = True
                result["failed_stages"] = [s.stage.value for s in critical_failures]
                logger.error("❌ Workflow failed due to critical stage failure")
                
                # Log workflow failure (Phase 3 feature)
                if self.audit_trail:
                    self.audit_trail.log_event(
                        AuditEventType.WORKFLOW_FAILED,
                        context.workflow_id,
                        error="Critical stage failure",
                        details={"failed_stages": [s.stage.value for s in critical_failures]}
                    )
            elif context.has_error():
                # Non-critical errors (deployment/verification) - workflow completed with warnings
                result["status"] = "completed_with_errors"
                result["critical_failure"] = False
                logger.warning("⚠️ Workflow completed with non-critical errors (deployment/verification)")
            else:
                # All stages succeeded
                result["status"] = "success"
                result["critical_failure"] = False
                logger.info("✅ Workflow completed successfully")
                
                # Log workflow completion (Phase 3 feature)
                if self.audit_trail:
                    self.audit_trail.log_event(
                        AuditEventType.WORKFLOW_COMPLETED,
                        context.workflow_id,
                        details={"status": "success", "stages_completed": len([s for s in context.stages if s.status == "success"])}
                    )
            
            # Save context (always save, even on failure)
            self.context_manager.save_context(context)
            
            # Auto-upload artifacts to Pinata if upload_scope is specified (only if no critical errors)
            if upload_scope and upload_scope in ['team', 'community'] and not critical_failures:
                try:
                    await self._auto_upload_artifacts(context, upload_scope)
                except Exception as upload_error:
                    logger.warning(f"⚠️ Artifact upload failed: {upload_error}")
                    # Non-fatal - continue
            
            # Clean up environment (preserve on critical errors, cleanup on success/warnings)
            if self.env_manager:
                had_errors = critical_failures or context.has_error()
                self.env_manager.cleanup(preserve_on_error=bool(critical_failures), had_errors=had_errors)
            
            logger.info(f"📊 Workflow completed: {result['status']} (workflow_id: {workflow_id})")
            return result
            
        except Exception as e:
            # CRITICAL: PipelineStage is already imported at module level (line 16)
            # Do NOT re-import - re-importing creates local scope that conflicts with module-level import
            had_errors = True
            diagnostic_path = None
            
            # Only save context if it exists (might not exist if exception occurs very early)
            if 'context' in locals() and context is not None:
                try:
                    # PipelineStage is available from module-level import (no re-import needed)
                    context.add_stage_result(
                        PipelineStage.OUTPUT,
                        "error",
                        error=str(e),
                        error_type="workflow_exception"
                    )
                    self.context_manager.save_context(context)
                    
                    # Generate diagnostic bundle
                    try:
                        diagnostic_path = self.context_manager.save_diagnostic_bundle(context)
                    except Exception as diag_error:
                        logger.error(f"Failed to save diagnostic bundle: {diag_error}")
                        diagnostic_path = None
                except Exception as context_error:
                    logger.error(f"Failed to save context on workflow error: {context_error}")
            else:
                logger.warning("⚠️ No context available for error handling - exception occurred very early")
            
            # Preserve environment for debugging
            if self.env_manager:
                try:
                    self.env_manager.preserve_for_debugging()
                    self.env_manager.cleanup(preserve_on_error=True, had_errors=True)
                except Exception as env_error:
                    logger.error(f"Failed to cleanup environment: {env_error}")
            
            logger.error(f"❌ Workflow failed: {e}")
            if diagnostic_path:
                logger.info(f"📋 Diagnostic bundle saved: {diagnostic_path}")
            if self.env_manager and hasattr(self.env_manager, 'temp_dir') and self.env_manager.temp_dir:
                logger.info(f"📁 Temp environment preserved: {self.env_manager.temp_dir}")
            
            # Build error result safely
            error_result = {
                "status": "error",
                "error": str(e),
                "workflow_id": workflow_id if 'workflow_id' in locals() else "unknown"
            }
            
            if diagnostic_path:
                error_result["diagnostic_bundle"] = str(diagnostic_path)
            
            if self.env_manager and hasattr(self.env_manager, 'temp_dir') and self.env_manager.temp_dir:
                error_result["temp_dir"] = str(self.env_manager.temp_dir)
            
            if 'context' in locals() and context is not None:
                try:
                    error_result["context"] = context.to_dict() if hasattr(context, 'to_dict') else str(context)
                except Exception:
                    error_result["context"] = f"Context available but serialization failed (workflow_id: {context.workflow_id if hasattr(context, 'workflow_id') else 'unknown'})"
            
            error_result["suggestions"] = [
                "Review diagnostic bundle for detailed error information" if diagnostic_path else "Exception occurred too early - no diagnostic bundle available",
                "Check error messages above for actionable fixes",
                f"Review workflow context if available"
            ]
            
            return error_result
    
    async def _stage_preflight(self, context: WorkflowContext):
        """Stage 0: Preflight checks (hardened validation)"""
        stage_start = time.time()
        logger.info("🔍 Stage 0: Preflight Checks (Doctor)")
        
        try:
            # Run comprehensive doctor/preflight checks (hardened validation)
            try:
                import sys
                scripts_path = Path(__file__).parent.parent.parent / "scripts"
                if str(scripts_path) not in sys.path:
                    sys.path.insert(0, str(scripts_path))
                
                from doctor import doctor as run_doctor
                doctor_workspace = Path(__file__).parent.parent.parent
                logger.info("🔬 Running Doctor preflight checks...")
                doctor_result = run_doctor(workspace_dir=doctor_workspace, auto_fix=True)
                if not doctor_result:
                    logger.warning("⚠️  Doctor preflight found issues, but continuing with workflow")
                else:
                    logger.info("✅ Doctor preflight checks passed")
            except ImportError as e:
                logger.debug(f"Doctor script not available ({e}), using basic preflight")
            except Exception as e:
                logger.warning(f"⚠️  Doctor preflight error: {e}, falling back to basic checks")
            
            checks = self.dep_manager.preflight_check()
            
            # Required tools (workflow will fail if missing) - per ideal workflow
            required_tools = ["forge", "python"]
            missing_required = [tool for tool in required_tools if not checks.get(tool, False)]
            
            # Optional tools (warnings only)
            optional_tools = ["npm", "node", "pip"]
            missing_optional = [tool for tool in optional_tools if not checks.get(tool, False)]
            
            # Check Foundry version (per ideal workflow preflight requirements)
            forge_version_check = checks.get("forge_version", {})
            if forge_version_check:
                current_version = forge_version_check.get("version", "unknown")
                is_nightly = forge_version_check.get("is_nightly", False)
                
                # Enforce strict mode if enabled
                import os
                strict_mode = os.getenv("HYPERAGENT_STRICT_FORGE", "0").lower() in ("1", "true", "yes")
                if strict_mode and is_nightly:
                    error_msg = (
                        f"Foundry nightly build detected in strict mode. "
                        f"Current: {current_version}. "
                        f"Please install stable version: foundryup"
                    )
                    context.add_stage_result(
                        PipelineStage.INPUT_PARSING,
                        "error",
                        error=error_msg,
                        error_type="foundry_version_mismatch"
                    )
                    raise RuntimeError(error_msg)
                elif is_nightly:
                    logger.warning(f"⚠️ Foundry nightly build detected: {current_version} (may have unpredictable behavior)")
            
            if missing_required:
                error_msg = (
                    f"Missing required tools: {', '.join(missing_required)}. "
                    f"Please install these system tools.\n"
                    f"  - Forge: Install Foundry (foundryup)\n"
                    f"  - Python: Install Python 3.8+"
                )
                context.add_stage_result(
                    PipelineStage.INPUT_PARSING,
                    "error",
                    error=error_msg,
                    error_type="missing_required_tools"
                )
                raise RuntimeError(error_msg)
            
            # Log warnings for optional tools with actionable messages
            if missing_optional:
                logger.warning(f"⚠️ Optional tools not found: {', '.join(missing_optional)}. These are only needed if contracts use npm/Node.js dependencies.")
                logger.info("💡 To install: npm (install Node.js), pip (comes with Python)")
            
            duration = (time.time() - stage_start) * 1000
            context.add_stage_result(
                PipelineStage.INPUT_PARSING,
                "success",
                output={
                    "tools": checks,
                    "required": {tool: checks.get(tool, False) for tool in required_tools},
                    "optional": {tool: checks.get(tool, False) for tool in optional_tools},
                    "warnings": missing_optional if missing_optional else None
                },
                duration_ms=duration
            )
            logger.info("✅ Preflight checks passed")
            
        except Exception as e:
            duration = (time.time() - stage_start) * 1000
            context.add_stage_result(
                PipelineStage.INPUT_PARSING,
                "error",
                error=str(e),
                duration_ms=duration
            )
            raise
    
    async def _stage_input_parsing(self, context: WorkflowContext, user_prompt: str, rag_scope: str = 'official-only'):
        """Stage 1: Input parsing & RAG context (per ideal workflow: Template & Context Fetch)"""
        stage_start = time.time()
        logger.info("📥 Stage 1: Input Parsing & Context Retrieval")
        
        try:
            # Per ideal workflow: Load closest matching template from IPFS/Pinata
            rag_context = ""
            template_info = None
            
            if hasattr(self.agent, 'rag') and self.agent.rag:
                try:
                    # Retrieve RAG context from IPFS/Pinata (per ideal workflow)
                    rag_context = await self.agent.rag.retrieve(user_prompt, rag_scope=rag_scope)
                    
                    # Try to identify which template was matched
                    if hasattr(self.agent.rag, 'last_retrieved_cid'):
                        template_info = {
                            "cid": getattr(self.agent.rag, 'last_retrieved_cid', None),
                            "source": "ipfs_pinata",
                            "scope": rag_scope
                        }
                    
                    if rag_context:
                        logger.info(f"📚 RAG context retrieved: {len(rag_context)} characters")
                        if template_info:
                            logger.info(f"📦 Template matched: {template_info.get('cid', 'N/A')} (scope: {rag_scope})")
                        else:
                            logger.info(f"📚 RAG context retrieved from IPFS (no specific template matched)")
                        
                        # Log RAG context retrieved (Phase 3 feature)
                        if self.audit_trail:
                            self.audit_trail.log_event(
                                AuditEventType.RAG_CONTEXT_RETRIEVED,
                                context.workflow_id,
                                stage=PipelineStage.INPUT_PARSING.value,
                                details={"context_length": len(rag_context), "template_cid": template_info.get('cid') if template_info else None}
                            )
                    else:
                        logger.info("ℹ️  No RAG context found - generating from scratch (new prompt pattern)")
                        logger.info("💡 This is normal for novel contract types not in template library")
                        
                        # Log RAG context empty (Phase 3 feature)
                        if self.audit_trail:
                            self.audit_trail.log_event(
                                AuditEventType.RAG_CONTEXT_EMPTY,
                                context.workflow_id,
                                stage=PipelineStage.INPUT_PARSING.value,
                                details={"reason": "No matching template found"}
                            )
                except Exception as rag_error:
                    logger.warning(f"⚠️ RAG context retrieval failed: {rag_error}")
                    # Continue without RAG - it's helpful but not required
                    rag_context = ""
                    logger.info("ℹ️  Continuing without RAG context - contract generation will proceed from scratch")
            else:
                logger.warning("⚠️ RAG system not available - proceeding without template context")
                logger.info("💡 Tip: Configure PINATA_API_KEY and PINATA_SECRET_KEY for template retrieval")
                logger.info("ℹ️  Generating contract from scratch without template context")
            
            # Store RAG context for reuse in generation stage
            context.metadata['rag_context'] = rag_context
            context.metadata['rag_scope'] = rag_scope
            if template_info:
                context.metadata['template_info'] = template_info
            
            duration = (time.time() - stage_start) * 1000
            context.add_stage_result(
                PipelineStage.INPUT_PARSING,
                "success",
                output={
                    "rag_context_length": len(rag_context),
                    "rag_scope": rag_scope,
                    "template_info": template_info,
                    "template_loaded": bool(rag_context)
                },
                duration_ms=duration
            )
            
            return rag_context
            
        except Exception as e:
            duration = (time.time() - stage_start) * 1000
            context.add_stage_result(
                PipelineStage.INPUT_PARSING,
                "error",
                error=str(e),
                duration_ms=duration
            )
            # Don't raise - RAG context is helpful but not required
            logger.warning(f"⚠️ RAG context retrieval failed: {e}")
            logger.info("💡 Continuing without RAG context - contract generation will proceed")
    
    async def _stage_generation(self, context: WorkflowContext, user_prompt: str, rag_scope: str = 'official-only'):
        """Stage 2: Contract generation with context-rich prompts"""
        from core.prompts.system_prompt import build_contract_generation_prompt
        stage_start = time.time()
        logger.info("🎨 Stage 2: Contract Generation")
        
        max_retries = 2
        
        for attempt in range(max_retries + 1):
            try:
                # Get RAG context (reuse from input parsing stage if available in metadata)
                rag_context = ""
                if hasattr(self.agent, 'rag') and self.agent.rag:
                    # Check if RAG context was already retrieved in input parsing stage
                    input_parsing_stage = next(
                        (s for s in context.stages if s.stage == PipelineStage.INPUT_PARSING),
                        None
                    )
                    
                    if input_parsing_stage and input_parsing_stage.output.get('rag_context'):
                        # Reuse cached RAG context
                        rag_context = input_parsing_stage.output.get('rag_context', '')
                        logger.debug("Reusing RAG context from input parsing stage")
                    else:
                        # Fetch fresh RAG context
                        try:
                            rag_context = await self.agent.rag.retrieve(user_prompt, rag_scope=rag_scope)
                        except Exception as e:
                            logger.debug(f"RAG retrieval in generation stage failed: {e}")
                            pass
                
                # Build context-rich prompt (Phase 3)
                workflow_state = self.state_persistence.load_state(context.workflow_id)
                enhanced_prompt = build_contract_generation_prompt(
                    user_goal=user_prompt,
                    rag_context=rag_context if isinstance(rag_context, str) else "",
                    workflow_state=workflow_state.to_dict() if workflow_state else None,
                    error_history=context.error_history[-5:] if context.error_history else None,  # Last 5 errors
                    constraints={
                        "network": context.metadata.get('network', 'hyperion'),
                        "standards": ["ERC20", "OpenZeppelin v5"],
                        "gas_optimization": True,
                        "security_level": "high"
                    }
                )
                
                # Log generation attempt (Phase 3 feature)
                if self.audit_trail:
                    self.audit_trail.log_event(
                        AuditEventType.GENERATION_ATTEMPTED,
                        context.workflow_id,
                        stage=PipelineStage.GENERATION.value,
                        details={"attempt": attempt + 1, "has_rag_context": bool(rag_context), "enhanced_prompt": True}
                    )
                
                # Use enhanced prompt for generation
                generation_result = await self.agent.generate_contract(enhanced_prompt, rag_context)
                
                # Track model/provider info for diagnostic bundles
                model_provider = generation_result.get('provider_used', 'unknown')
                generation_method = generation_result.get('method', 'unknown')
                context.metadata['model_provider'] = model_provider
                context.metadata['generation_method'] = generation_method
                
                # Log model selection (Phase 3 feature)
                if self.audit_trail:
                    self.audit_trail.log_event(
                        AuditEventType.MODEL_SELECTED,
                        context.workflow_id,
                        stage=PipelineStage.GENERATION.value,
                        details={"provider": model_provider, "method": generation_method}
                    )
                
                if generation_result["status"] == "success":
                    context.contract_code = generation_result["contract_code"]
                    context.contract_name = generation_result.get("contract_name")
                    context.contract_path = generation_result.get("path")
                    context.contract_category = generation_result.get("category")
                    
                    # Ensure contract_name is not None - extract from code if needed
                    if not context.contract_name and context.contract_code:
                        from core.tools.utils import extract_contract_info
                        contract_info = extract_contract_info(context.contract_code)
                        context.contract_name = contract_info.get("contract_name", "Contract")
                        logger.warning(f"Contract name was None, extracted: {context.contract_name}")
                    
                    if not context.contract_name:
                        raise ValueError("Could not determine contract name from generated code")
                    
                    duration = (time.time() - stage_start) * 1000
                    context.add_stage_result(
                        PipelineStage.GENERATION,
                        "success",
                        output=generation_result,
                        duration_ms=duration,
                        metadata={"attempt": attempt + 1}
                    )
                    logger.info("✅ Contract generated successfully")
                    
                    # Log generation success (Phase 3 feature)
                    if self.audit_trail:
                        self.audit_trail.log_event(
                            AuditEventType.GENERATION_SUCCESS,
                            context.workflow_id,
                            stage=PipelineStage.GENERATION.value,
                            details={"contract_name": context.contract_name, "contract_size": len(context.contract_code) if context.contract_code else 0}
                        )
                    
                    # Self-healing onboarding: Store successful novel prompts as templates (Phase 3 feature)
                    if hasattr(self.agent, 'rag') and self.agent.rag:
                        # Check if this was a novel prompt (no RAG context found)
                        rag_context_used = bool(context.metadata.get('rag_context'))
                        if not rag_context_used and context.contract_code:
                            try:
                                template_cid = await self.agent.rag.suggest_and_store_new_pattern(
                                    user_prompt,
                                    context.contract_code,
                                    success=True,
                                    metadata={
                                        'contract_type': context.contract_category or 'Custom',
                                        'contract_name': context.contract_name,
                                        'workflow_id': context.workflow_id
                                    }
                                )
                                if template_cid:
                                    logger.info(f"💡 Auto-stored novel prompt as template (CID: {template_cid})")
                                    context.metadata['template_auto_stored'] = True
                                    context.metadata['template_cid'] = template_cid
                            except Exception as store_error:
                                logger.debug(f"Failed to auto-store template: {store_error}")
                    
                    # Sanitize generated contract code to avoid known compiler issues
                    try:
                        sanitized = self._sanitize_contract_code(context.contract_code)
                        if sanitized != context.contract_code:
                            context.contract_code = sanitized
                            logger.info("🔧 Applied post-generation sanitizer to contract code")
                            # CRITICAL: Write sanitized code back to contracts/ directory
                            from pathlib import Path
                            foundry_project_dir = Path(__file__).parent.parent.parent
                            foundry_contracts_dir = foundry_project_dir / "contracts"
                            foundry_contract_file = foundry_contracts_dir / f"{context.contract_name}.sol"
                            try:
                                foundry_contract_file.write_text(sanitized, encoding="utf-8")
                                logger.info(f"✅ Updated contracts/ file with sanitized code: {foundry_contract_file}")
                            except Exception as write_err:
                                logger.warning(f"⚠️ Could not update contracts/ file: {write_err}")
                    except Exception as _:
                        # Non-fatal if sanitizer fails
                        pass

                    return generation_result
                else:
                    raise Exception(generation_result.get("error", "Generation failed"))
                    
            except Exception as e:
                # Log generation failure (Phase 3 feature)
                if self.audit_trail:
                    self.audit_trail.log_event(
                        AuditEventType.GENERATION_FAILED,
                        context.workflow_id,
                        stage=PipelineStage.GENERATION.value,
                        error=str(e),
                        details={"attempt": attempt + 1}
                    )
                
                if attempt < max_retries:
                    # Try adaptive prompt repair before retry (Phase 3 feature)
                    if self.prompt_repair:
                        try:
                            error_str = str(e)
                            repaired_prompt, repaired_context, was_repaired = self.prompt_repair.repair_prompt(
                                user_prompt, rag_context, error_str
                            )
                            if was_repaired:
                                logger.info("🔧 Applied adaptive prompt repair")
                                user_prompt = repaired_prompt
                                rag_context = repaired_context
                                # Update RAG context in metadata
                                context.metadata['rag_context'] = rag_context
                                context.metadata['prompt_repaired'] = True
                                context.metadata['repair_pattern'] = self.prompt_repair.detect_error_pattern(error_str)
                                
                                # Log auto-fix attempt (Phase 3 feature)
                                if self.audit_trail:
                                    self.audit_trail.log_event(
                                        AuditEventType.AUTO_FIX_ATTEMPTED,
                                        context.workflow_id,
                                        stage=PipelineStage.GENERATION.value,
                                        details={"fix_type": "prompt_repair", "pattern": context.metadata.get('repair_pattern')}
                                    )
                        except Exception as repair_error:
                            logger.debug(f"Adaptive prompt repair failed: {repair_error}")
                    
                    # Log retry triggered (Phase 3 feature)
                    if self.audit_trail:
                        self.audit_trail.log_event(
                            AuditEventType.RETRY_TRIGGERED,
                            context.workflow_id,
                            stage=PipelineStage.GENERATION.value,
                            details={"retry_count": attempt + 1, "max_retries": max_retries}
                        )
                    
                    context.increment_retry(PipelineStage.GENERATION)
                    logger.warning(f"⚠️ Generation attempt {attempt + 1} failed, retrying...")
                    await asyncio.sleep(1)  # Brief delay before retry
                    continue
                else:
                    duration = (time.time() - stage_start) * 1000
                    context.add_stage_result(
                        PipelineStage.GENERATION,
                        "error",
                        error=str(e),
                        duration_ms=duration,
                        metadata={"attempts": attempt + 1}
                    )
                    raise
    
    async def _stage_dependency_resolution(self, context: WorkflowContext):
        """Stage 3: Dependency detection and installation"""
        stage_start = time.time()
        logger.info("📦 Stage 3: Dependency Resolution")
        
        try:
            if not context.contract_code:
                raise ValueError("No contract code available for dependency detection")
            
            # Detect dependencies
            logger.info(f"Analyzing contract code for dependencies...")
            deps = self.dep_manager.detect_dependencies(
                context.contract_code,
                context.contract_path or "contract.sol"
            )
            
            context.detected_dependencies = [
                {
                    "name": dep.name,
                    "source_type": dep.source_type,
                    "install_path": str(dep.install_path) if dep.install_path else None
                }
                for dep in deps
            ]
            
            logger.info(f"📦 Detected {len(deps)} dependencies: {[d.name for d in deps]}")
            
            if deps:
                # Install all dependencies
                logger.info(f"Installing {len(deps)} dependencies...")
                install_results = await self.dep_manager.install_all_dependencies(deps)
                context.installed_dependencies = {
                    name: (success, message)
                    for name, (success, message) in install_results.items()
                }
                
                # Log installation results
                for name, (success, message) in install_results.items():
                    if success:
                        logger.info(f"✅ Installed {name}: {message}")
                    else:
                        logger.error(f"❌ Failed to install {name}: {message}")
                
                failed = [name for name, (success, _) in install_results.items() if not success]
                if failed:
                    error_msg = f"Failed to install dependencies: {', '.join(failed)}"
                    logger.error(f"❌ {error_msg}")
                    raise RuntimeError(error_msg)
                
                # Update remappings after successful installation
                for dep in deps:
                    if dep.install_path and dep.install_path.exists():
                        try:
                            self.dep_manager._update_remappings(dep.name, dep.install_path)
                            logger.debug(f"Updated remappings for {dep.name}")
                        except Exception as e:
                            logger.warning(f"Failed to update remappings for {dep.name}: {e}")
            else:
                logger.info("📦 No dependencies detected")
                context.installed_dependencies = {}
            
            duration = (time.time() - stage_start) * 1000
            context.add_stage_result(
                PipelineStage.DEPENDENCY_RESOLUTION,
                "success",
                output={
                    "detected": len(deps),
                    "installed": sum(1 for s, _ in context.installed_dependencies.values() if s),
                    "dependencies": [d.name for d in deps]
                },
                duration_ms=duration
            )
            logger.info("✅ Dependencies resolved")
            
        except Exception as e:
            logger.error(f"❌ Dependency resolution failed: {e}")
            logger.exception(e)  # Log full traceback
            
            # Try auto-fix
            fix_context = {
                "workspace_dir": self.workspace_dir,
                "contract_code": context.contract_code
            }
            # Query agent memory for similar errors and successful fixes (Phase 3 feature)
            if self.agent_memory:
                try:
                    error_type = type(e).__name__
                    similar_errors = self.agent_memory.query_similar_errors(
                        error_type, 
                        PipelineStage.DEPENDENCY_RESOLUTION.value,
                        limit=3
                    )
                    if similar_errors:
                        successful_fixes = self.agent_memory.get_successful_fixes_for_error(
                            error_type,
                            PipelineStage.DEPENDENCY_RESOLUTION.value
                        )
                        if successful_fixes:
                            logger.info(f"💡 Found {len(successful_fixes)} successful fixes for similar error in agent memory")
                            # Could use these fixes to inform the error handler
                except Exception as mem_error:
                    logger.debug(f"Failed to query agent memory: {mem_error}")
            
            fix_success, fix_msg = await handle_error_with_retry(
                self.error_handler, e, fix_context, max_retries=2
            )
            
            # Record fix attempt in error history
            context.record_fix_attempt(PipelineStage.DEPENDENCY_RESOLUTION, fix_success, fix_msg or "")
            
            if not fix_success:
                duration = (time.time() - stage_start) * 1000
                context.add_stage_result(
                    PipelineStage.DEPENDENCY_RESOLUTION,
                    "error",
                    error=str(e),
                    duration_ms=duration
                )
                raise
            
            # BULLETPROOF RECURSION GUARD: Increment FIRST, then check
            # This ensures atomic increment-and-check to prevent infinite recursion
            MAX_RETRIES = 3
            retry_count = context.increment_and_get_retry_count(PipelineStage.DEPENDENCY_RESOLUTION)
            
            # Log every increment + recursion attempt for debugging
            import traceback
            stack_info = ''.join(traceback.format_stack()[-3:-1])  # Last 2 stack frames
            logger.debug(f"🔄 Dependency resolution retry attempt {retry_count}/{MAX_RETRIES}\nStack trace:\n{stack_info}")
            
            # Strict check: if incremented count exceeds MAX_RETRIES, refuse to recurse
            if retry_count > MAX_RETRIES:
                logger.error(f"❌ Dependency resolution failed after {MAX_RETRIES} retries (attempt {retry_count} exceeded limit)")
                # Save diagnostic bundle for debugging
                diagnostic_path = None
                try:
                    diagnostic_path = self.context_manager.save_diagnostic_bundle(context)
                    logger.error(f"Diagnostic bundle saved: {diagnostic_path}")
                except Exception as diag_error:
                    logger.warning(f"Failed to save diagnostic bundle: {diag_error}")
                
                # Escalate using guardrails (Phase 3 feature)
                if self.guardrails:
                    try:
                        context_dict = context.generate_diagnostic_bundle()
                        self.guardrails.escalate(
                            PipelineStage.DEPENDENCY_RESOLUTION.value,
                            str(e),
                            context_dict,
                            diagnostic_path
                        )
                        
                        # Log escalation (Phase 3 feature)
                        if self.audit_trail:
                            self.audit_trail.log_event(
                                AuditEventType.ESCALATION_TRIGGERED,
                                context.workflow_id,
                                stage=PipelineStage.DEPENDENCY_RESOLUTION.value,
                                error=str(e),
                                details={"retry_count": retry_count, "max_retries": MAX_RETRIES, "exceeded": True}
                            )
                    except Exception as guard_error:
                        logger.debug(f"Guardrails escalation failed: {guard_error}")
                
                duration = (time.time() - stage_start) * 1000
                context.add_stage_result(
                    PipelineStage.DEPENDENCY_RESOLUTION,
                    "error",
                    error=f"Dependency resolution failed after {MAX_RETRIES} retries (attempt {retry_count} exceeded limit)",
                    error_type="max_retries_exceeded",
                    duration_ms=duration
                )
                
                # Store user-friendly error info in context
                if self.guardrails:
                    friendly_error = self.guardrails.get_user_friendly_error(
                        PipelineStage.DEPENDENCY_RESOLUTION.value,
                        str(e),
                        "max_retries_exceeded"
                    )
                    context.metadata['friendly_error'] = friendly_error
                
                raise RuntimeError(f"Dependency resolution failed after {MAX_RETRIES} retries (attempt {retry_count} exceeded limit). See diagnostic bundle for details.")
            
            # Safe to retry: retry_count is now incremented and <= MAX_RETRIES
            logger.info(f"🔄 Retrying dependency resolution after auto-fix... (attempt {retry_count}/{MAX_RETRIES})")
            await self._stage_dependency_resolution(context)
    
    async def _stage_compilation(self, context: WorkflowContext):
        """Stage 4: Compilation with auto-recovery"""
        stage_start = time.time()
        logger.info("🔨 Stage 4: Compilation")
        
        max_retries = 3
        
        for attempt in range(max_retries + 1):
            try:
                if not context.contract_code or not context.contract_name:
                    raise ValueError("Contract code or name missing")
                
                compilation_result = await self.agent._compile_contract(
                    context.contract_name,
                    context.contract_code
                )
                
                if compilation_result.get("success"):
                    context.compilation_success = True
                    context.compilation_artifact_path = compilation_result.get("artifact_path")
                    
                    duration = (time.time() - stage_start) * 1000
                    context.add_stage_result(
                        PipelineStage.COMPILATION,
                        "success",
                        output=compilation_result,
                        duration_ms=duration,
                        metadata={"attempt": attempt + 1}
                    )
                    logger.info("✅ Compilation successful")
                    return compilation_result
                else:
                    error_msg = compilation_result.get("error", "Compilation failed")
                    raise Exception(error_msg)
                    
            except Exception as e:
                if attempt < max_retries:
                    # Try auto-fix
                    fix_context = {
                        "workspace_dir": self.workspace_dir,
                        "contract_code": context.contract_code,
                        "contract_name": context.contract_name
                    }
                    
                    fix_success, fix_msg = await handle_error_with_retry(
                        self.error_handler, e, fix_context, max_retries=1
                    )
                    
                    if fix_success:
                        # Update contract code if it was fixed
                        if "contract_code" in fix_context:
                            context.contract_code = fix_context["contract_code"]
                            logger.info("✅ Contract code updated after auto-fix")
                            # CRITICAL: Write fixed code back to contracts/ directory
                            from pathlib import Path
                            foundry_project_dir = Path(__file__).parent.parent.parent
                            foundry_contracts_dir = foundry_project_dir / "contracts"
                            foundry_contract_file = foundry_contracts_dir / f"{context.contract_name}.sol"
                            try:
                                foundry_contract_file.write_text(fix_context["contract_code"], encoding="utf-8")
                                logger.info(f"✅ Updated contracts/ file with fixed code: {foundry_contract_file}")
                                # Clear Foundry cache before retry
                                import subprocess
                                subprocess.run(
                                    ["forge", "clean"],
                                    cwd=foundry_project_dir,
                                    capture_output=True,
                                    timeout=30
                                )
                                logger.info("🧹 Cleared Foundry cache before retry")
                            except Exception as write_err:
                                logger.warning(f"⚠️ Could not update contracts/ file: {write_err}")
                        context.increment_retry(PipelineStage.COMPILATION)
                        logger.info(f"🔧 Auto-fixed compilation error, retrying...")
                        await asyncio.sleep(1)
                        continue
                    else:
                        context.increment_retry(PipelineStage.COMPILATION)
                        logger.warning(f"⚠️ Compilation attempt {attempt + 1} failed, retrying...")
                        await asyncio.sleep(1)
                        continue
                else:
                    duration = (time.time() - stage_start) * 1000
                    context.add_stage_result(
                        PipelineStage.COMPILATION,
                        "error",
                        error=str(e),
                        duration_ms=duration,
                        metadata={"attempts": attempt + 1}
                    )
                    raise
    
    async def _stage_testing(self, context: WorkflowContext):
        """Stage 5: Testing - Execute e2e and edge-case tests per ideal workflow"""
        stage_start = time.time()
        logger.info("🧪 Stage 5: Testing")
        
        try:
            if not context.contract_name or not context.compilation_success:
                logger.warning("⚠️ Skipping tests: contract not compiled successfully")
                duration = (time.time() - stage_start) * 1000
                context.add_stage_result(
                    PipelineStage.TESTING,
                    "skipped",
                    output={"reason": "Contract not compiled"},
                    duration_ms=duration
                )
                return
            
            # Run Foundry tests if test file exists
            import subprocess
            from pathlib import Path
            
            foundry_project_dir = Path(__file__).parent.parent.parent
            test_file = foundry_project_dir / "test" / f"{context.contract_name}.t.sol"
            
            test_results = {
                "foundry_tests_run": False,
                "tests_passed": False,
                "test_count": 0,
                "test_output": None
            }
            
            # Check if test file exists
            if test_file.exists():
                logger.info(f"📝 Found test file: {test_file.name}")
                try:
                    # Run forge test for this specific contract
                    # Note: Foundry runs all tests by default, but we can filter
                    test_cmd = ["forge", "test", "--match-contract", context.contract_name, "-vv"]
                    result = subprocess.run(
                        test_cmd,
                        cwd=foundry_project_dir,
                        capture_output=True,
                        text=True,
                        timeout=120
                    )
                    
                    test_results["foundry_tests_run"] = True
                    test_results["test_output"] = result.stdout + result.stderr
                    test_results["tests_passed"] = result.returncode == 0
                    
                    if result.returncode == 0:
                        logger.info("✅ All tests passed")
                    else:
                        logger.warning(f"⚠️ Some tests failed (exit code: {result.returncode})")
                        # Extract test count from output if possible
                        if "test result:" in result.stdout:
                            test_results["test_count"] = result.stdout.count("test result:")
                    
                except subprocess.TimeoutExpired:
                    logger.warning("⚠️ Test execution timed out after 120 seconds")
                    test_results["test_output"] = "Test execution timed out"
                except Exception as e:
                    logger.warning(f"⚠️ Test execution failed: {e}")
                    test_results["test_output"] = str(e)
            else:
                logger.info("ℹ️ No test file found - generating basic sanity test recommendations")
                test_results["note"] = "No test file found. Consider adding tests for: mint/burn/approve (tokens), batch mint (NFTs)"
            
            # Perform basic sanity checks even without formal tests
            sanity_checks = {
                "contract_compiled": context.compilation_success,
                "contract_has_code": bool(context.contract_code),
                "deployment_ready": context.compilation_success and context.audit_results
            }
            test_results["sanity_checks"] = sanity_checks
            
            duration = (time.time() - stage_start) * 1000
            status = "success" if (test_results.get("tests_passed") or not test_results.get("foundry_tests_run")) else "warning"
            context.add_stage_result(
                PipelineStage.TESTING,
                status,
                output=test_results,
                duration_ms=duration
            )
            
            # Flag test failures (but don't block workflow - tests are informative)
            if test_results.get("foundry_tests_run") and not test_results.get("tests_passed"):
                logger.warning("⚠️ Test failures detected - review test output before deployment")
            
        except Exception as e:
            duration = (time.time() - stage_start) * 1000
            context.add_stage_result(
                PipelineStage.TESTING,
                "error",
                error=str(e),
                duration_ms=duration
            )
            # Don't raise - test failures are informative, not blocking
            logger.warning(f"⚠️ Testing stage error: {e}")
    
    async def _stage_auditing(self, context: WorkflowContext):
        """Stage 6: Auditing"""
        stage_start = time.time()
        logger.info("🔒 Stage 6: Auditing")
        
        try:
            if not context.contract_code:
                raise ValueError("No contract code for auditing")
            
            audit_result = await self.agent.audit_contract(context.contract_code)
            
            if audit_result["status"] == "success":
                context.audit_results = audit_result
                context.security_score = audit_result.get("security_score", 0)
                
                # Per ideal workflow: Add audit badge/flag if critical errors found
                severity = audit_result.get("severity", "low")
                vulnerability_count = len(audit_result.get("results", {}).get("vulnerabilities", []))
                critical_issues = [v for v in audit_result.get("results", {}).get("vulnerabilities", []) 
                                  if v.get("severity", "").lower() in ["critical", "high"]]
                
                audit_summary = {
                    "severity": severity,
                    "security_score": context.security_score,
                    "vulnerability_count": vulnerability_count,
                    "critical_issues_count": len(critical_issues),
                    "audit_passed": len(critical_issues) == 0,
                    "recommendations": audit_result.get("results", {}).get("recommendations", [])
                }
                
                if len(critical_issues) > 0:
                    logger.warning(f"🔒 Audit found {len(critical_issues)} critical/high severity issues")
                    logger.warning("⚠️ Deployment should be reviewed before proceeding")
                    audit_summary["blocking_issues"] = critical_issues
                else:
                    logger.info("✅ Audit passed: No critical security issues detected")
                
                duration = (time.time() - stage_start) * 1000
                context.add_stage_result(
                    PipelineStage.AUDITING,
                    "success",
                    output={**audit_result, "summary": audit_summary},
                    duration_ms=duration
                )
                logger.info(f"✅ Audit completed (Security Score: {context.security_score}/100)")
                return audit_result
            else:
                error_msg = audit_result.get("error", "Audit failed")
                # Provide actionable error message per ideal workflow
                raise Exception(
                    f"{error_msg}\n"
                    f"💡 Recovery suggestions:\n"
                    f"   1. Check if Slither/Mythril tools are installed\n"
                    f"   2. Verify contract code is valid Solidity\n"
                    f"   3. Review static analysis tool configuration"
                )
                
        except Exception as e:
            duration = (time.time() - stage_start) * 1000
            context.add_stage_result(
                PipelineStage.AUDITING,
                "error",
                error=str(e),
                duration_ms=duration
            )
            raise

    def _sanitize_contract_code(self, code: str) -> str:
        """Apply quick fixes to common generation issues before compilation.

        - Remove invalid _beforeTokenTransfer overrides for ERC20 when signature/parents mismatch
        - Fix constructor parameter shadowing of public/external functions
        """
        if not code:
            return code
        import re
        fixed = code
        
        # 0. Ensure pragma solidity matches OpenZeppelin v5 requirements (^0.8.24)
        pragma_match = re.search(r'pragma solidity\s+([^;]+);', fixed)
        if pragma_match:
            pragma_spec = pragma_match.group(1).strip()
            # Check if it's compatible with 0.8.24+
            if '^0.8.' in pragma_spec:
                version_match = re.search(r'0\.8\.(\d+)', pragma_spec)
                if version_match:
                    minor_version = int(version_match.group(1))
                    if minor_version < 24:
                        # Update to 0.8.24 minimum for OZ v5 compatibility
                        fixed = re.sub(
                            r'pragma solidity\s+[^;]+;',
                            'pragma solidity ^0.8.24;',
                            fixed,
                            count=1
                        )
                        logger.info("🔧 Updated pragma solidity to ^0.8.24 for OpenZeppelin v5 compatibility")
            elif '0.8.' in pragma_spec and not pragma_spec.startswith('^0.8.24'):
                # If no caret or too old, update it
                fixed = re.sub(
                    r'pragma solidity\s+[^;]+;',
                    'pragma solidity ^0.8.24;',
                    fixed,
                    count=1
                )
                logger.info("🔧 Updated pragma solidity to ^0.8.24 for OpenZeppelin v5 compatibility")
        
        # 0.3. PROACTIVELY fix OpenZeppelin v5 Ownable constructor requirement
        # OpenZeppelin v5 Ownable REQUIRES constructor(address initialOwner) or Ownable(msg.sender) in constructor
        if 'is Ownable' in fixed or 'Ownable' in fixed:
            # Check if contract inherits Ownable
            ownable_inheritance = re.search(r'contract\s+\w+\s+is\s+[^{]*Ownable', fixed)
            if ownable_inheritance:
                # Check if constructor exists
                constructor_match = re.search(r'constructor\s*\(([^)]*)\)\s*([^{]*)\{', fixed)
                if constructor_match:
                    constructor_params = constructor_match.group(1).strip()
                    constructor_calls = constructor_match.group(2).strip()
                    
                    # Check if Ownable constructor is NOT already called
                    if 'Ownable(' not in constructor_calls:
                        # Add Ownable(msg.sender) to constructor calls
                        # Pattern: constructor(...) ERC20(...) { -> constructor(...) ERC20(...) Ownable(msg.sender) {
                        fixed = re.sub(
                            r'(constructor\s*\([^)]*\)\s*)([^{]*?)(\{)',
                            lambda m: m.group(1) + m.group(2).rstrip() + ' Ownable(msg.sender) ' + m.group(3),
                            fixed,
                            count=1
                        )
                        logger.info("🔧 Added Ownable(msg.sender) to constructor for OpenZeppelin v5 compatibility")
                    elif 'Ownable(' in constructor_calls and 'msg.sender' not in constructor_calls and 'initialOwner' not in constructor_calls:
                        # Ownable() with no args - needs fixing
                        fixed = re.sub(
                            r'Ownable\(\)',
                            'Ownable(msg.sender)',
                            fixed,
                            count=1
                        )
                        logger.info("🔧 Fixed Ownable() to Ownable(msg.sender) for OpenZeppelin v5 compatibility")
                else:
                    # No constructor exists - need to add one with Ownable(msg.sender)
                    # Find the contract declaration and add constructor after it
                    contract_match = re.search(r'(contract\s+\w+\s+is\s+[^{]*\{)', fixed)
                    if contract_match:
                        # Build constructor calls based on what the contract inherits
                        constructor_calls = []
                        if 'Ownable' in contract_match.group(1):
                            constructor_calls.append('Ownable(msg.sender)')
                        if 'ReentrancyGuard' in contract_match.group(1):
                            constructor_calls.append('ReentrancyGuard()')
                        
                        if constructor_calls:
                            # Add constructor after the opening brace
                            constructor_str = ' ' + ' '.join(constructor_calls) + ' '
                            fixed = re.sub(
                                r'(contract\s+\w+\s+is\s+[^{]*\{)',
                                lambda m: m.group(1) + f'\n    constructor(){constructor_str}{{}}',
                                fixed,
                                count=1
                            )
                            logger.info(f"🔧 Added constructor() {constructor_str.strip()} for OpenZeppelin v5 compatibility")
        
        # 0.3.5. PROACTIVELY fix OpenZeppelin v5 import path changes (security -> utils)
        # OpenZeppelin v5 moved Pausable and ReentrancyGuard from security/ to utils/
        oz_v5_path_fixes = {
            "@openzeppelin/contracts/security/Pausable.sol": "@openzeppelin/contracts/utils/Pausable.sol",
            "@openzeppelin/contracts/security/ReentrancyGuard.sol": "@openzeppelin/contracts/utils/ReentrancyGuard.sol",
            "@openzeppelin/contracts/utils/security/Pausable.sol": "@openzeppelin/contracts/utils/Pausable.sol",
        }
        for old_path, new_path in oz_v5_path_fixes.items():
            if old_path in fixed:
                fixed = fixed.replace(old_path, new_path)
                logger.info(f"🔧 Fixed OpenZeppelin v5 import path: {old_path} -> {new_path}")
        
        # 0.4. PROACTIVELY fix 'implements' keyword (Java/TypeScript pattern, invalid in Solidity)
        # Solidity uses 'is' for both contract extension and interface inheritance - NEVER 'implements'
        if 'implements' in fixed:
            # Replace: contract X implements IInterface -> contract X is IInterface
            fixed = re.sub(
                r'contract\s+([A-Za-z0-9_]+)\s+implements\s+',
                r'contract \1 is ',
                fixed
            )
            logger.info("🔧 Fixed 'implements' keyword to 'is' (Solidity syntax correction)")
        
        # 0.4.5. PROACTIVELY remove SafeMath (deprecated in Solidity 0.8+)
        # Solidity 0.8+ has built-in checked arithmetic, SafeMath is no longer needed
        if 'SafeMath' in fixed or 'using SafeMath' in fixed:
            logger.info("🔧 Proactively removing deprecated SafeMath usage...")
            # Remove import
            fixed = re.sub(r"import\s+['\"]@openzeppelin/contracts/utils/math/SafeMath\.sol['\"];?\s*\n?", "", fixed, flags=re.IGNORECASE | re.MULTILINE)
            # Remove using statement
            fixed = re.sub(r"using\s+SafeMath\s+for\s+uint256;?\s*\n?", "", fixed, flags=re.IGNORECASE | re.MULTILINE)
            # Replace .add() with +, .sub() with -, .mul() with *, .div() with /
            fixed = re.sub(r'(\w+)\.add\(([^)]+)\)', r'(\1 + \2)', fixed)
            fixed = re.sub(r'(\w+)\.sub\(([^)]+)\)', r'(\1 - \2)', fixed)
            fixed = re.sub(r'(\w+)\.mul\(([^)]+)\)', r'(\1 * \2)', fixed)
            fixed = re.sub(r'(\w+)\.div\(([^)]+)\)', r'(\1 / \2)', fixed)
            logger.info("✅ Proactively removed SafeMath - using native checked arithmetic")
        
        # 0.5. PROACTIVELY remove Counters.sol (deprecated in OZ v5) before compilation
        # This prevents the error from happening in the first place
        if 'Counters.sol' in fixed or 'using Counters' in fixed or 'Counters.Counter' in fixed:
            logger.info("🔧 Proactively removing deprecated Counters.sol usage...")
            # Remove import
            fixed = re.sub(r"import\s+['\"]@openzeppelin/contracts/utils/Counters\.sol['\"];?\s*\n?", "", fixed, flags=re.IGNORECASE | re.MULTILINE)
            # Remove using statement
            fixed = re.sub(r"using\s+Counters\s+for\s+Counters\.Counter;?\s*\n?", "", fixed, flags=re.IGNORECASE | re.MULTILINE)
            # Replace Counters.Counter declarations
            fixed = re.sub(r"Counters\.Counter\s+(private|internal|public)?\s*(\w+);", r"uint256 \1 \2;", fixed, flags=re.IGNORECASE)
            fixed = re.sub(r"Counters\.Counter\s+(\w+);", r"uint256 private \1;", fixed, flags=re.IGNORECASE)
            # Replace method calls
            fixed = re.sub(r"(\w+TokenIdCounter|\w+Counter)\.current\(\)", r"\1", fixed)
            fixed = re.sub(r"(\w+TokenIdCounter|\w+Counter)\.increment\(\)", r"\1++", fixed)
            logger.info("✅ Proactively removed Counters.sol - using manual counter instead")
        
        # 1. Remove any _beforeTokenTransfer override block entirely (improved regex)
        # Handles multiline signatures, comments, and nested braces
        patterns = [
            r"function\s+_beforeTokenTransfer\s*\([^)]*\)\s*internal[\s\S]*?override[\s\S]*?\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}",
            r"function\s+_beforeTokenTransfer\s*\([^)]*\)\s*internal\s+virtual\s+override[\s\S]*?\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}",
            r"function\s+_beforeTokenTransfer\s*\([^)]*\)\s*internal[\s\S]*?\{[\s\S]*?\}",
        ]
        for pat in patterns:
            if re.search(pat, fixed, re.MULTILINE | re.DOTALL):
                fixed = re.sub(pat, "", fixed, flags=re.MULTILINE | re.DOTALL)
                logger.info("🔧 Removed _beforeTokenTransfer override function")
        
        # 2. Fix constructor parameter shadowing of state variables and functions
        # First, find all state variables - Solidity syntax: type [visibility] [immutable/constant] name;
        # Pattern 1: uint256 private immutable _cap; or uint256 _cap;
        simple_state_var_pattern = r'(?:uint256|uint8|uint16|uint32|uint64|uint128|int256|int8|int16|int32|int64|int128|bool|address|string|bytes\d*|mapping)\s+(?:private|internal|public)?\s*(?:immutable|constant)?\s*(_?\w+)\s*;'
        state_vars = set(re.findall(simple_state_var_pattern, fixed))
        # Pattern 2: private uint256 _cap; (less common but possible)
        alt_state_var_pattern = r'(?:private|internal|public)\s+(?:uint256|uint8|uint16|uint32|uint64|uint128|int256|int8|int16|int32|int64|int128|bool|address|string|bytes\d*|mapping)\s+(?:immutable|constant)?\s*(_?\w+)\s*;'
        alt_state_vars = set(re.findall(alt_state_var_pattern, fixed))
        state_vars.update(alt_state_vars)
        
        # Find all public/external function names in the contract
        # Pattern matches: function name(...) public/external [view/pure/payable] [returns (...)]
        function_pattern = r'function\s+(\w+)\s*\([^)]*\)\s+(?:public|external)'
        function_names = set(re.findall(function_pattern, fixed))
        
        # Combine state variables and function names to check for shadowing
        all_names_to_check = state_vars.union(function_names)
        
        # Log found names for debugging
        logger.info(f"Sanitizer: Checking for shadowing issues...")
        if state_vars:
            logger.info(f"Sanitizer: Found state variables: {', '.join(state_vars)}")
        if function_names:
            logger.info(f"Sanitizer: Found functions that may shadow: {', '.join(function_names)}")
        
        if all_names_to_check:
            # Find constructor and its parameters
            constructor_pattern = r'constructor\s*\(([^)]+)\)'
            constructor_match = re.search(constructor_pattern, fixed)
            
            if constructor_match:
                params_original = constructor_match.group(1)
                params = params_original
                modified = False
                replaced_names = {}
                
                # Check each name (state variable or function) for shadowing
                for name_to_check in all_names_to_check:
                    # Remove leading underscore if present for matching
                    name_without_underscore = name_to_check.lstrip('_')
                    # Match parameter with this name: type paramName or type memory paramName
                    # Look for the parameter name as a standalone word in the params string
                    # Match both with and without underscore prefix
                    param_pattern = rf'\b(\w+(?:\s+memory)?)\s+\b(_?{re.escape(name_without_underscore)})\b'
                    param_match = re.search(param_pattern, params)
                    if param_match:
                        # Rename parameter to _paramName to avoid shadowing (if not already prefixed)
                        param_name = param_match.group(2)
                        if param_name.startswith('_'):
                            new_name = param_name  # Already prefixed, but might still shadow
                        else:
                            new_name = f'_{param_name}'
                        # Replace the exact match in params list
                        old_param_decl = param_match.group(0)
                        new_param_decl = f'{param_match.group(1)} {new_name}'
                        params = params.replace(old_param_decl, new_param_decl)
                        replaced_names[param_name] = new_name
                        modified = True
                        logger.info(f"Sanitizer: Will rename constructor parameter '{param_name}' to '{new_name}' to avoid shadowing state variable/function")
                
                # Update constructor signature if parameters were modified
                if modified:
                    # Replace the entire constructor signature
                    old_constructor_sig = f'constructor({params_original})'
                    new_constructor_sig = f'constructor({params})'
                    fixed = fixed.replace(old_constructor_sig, new_constructor_sig)
                    logger.info(f"Updated constructor signature")
                    
                    # Replace all references to the old parameter names in constructor body
                    # Find constructor body more reliably
                    constructor_body_match = re.search(
                        r'constructor\s*\([^)]+\)[^\{]*\{([^\}]*\{[^\}]*\}[^\}]*|[^\}]*)\}',
                        fixed,
                        re.DOTALL
                    )
                    if constructor_body_match:
                        constructor_body = constructor_body_match.group(1)
                        updated_body = constructor_body
                        for old_name, new_name in replaced_names.items():
                            # Replace standalone references to the parameter (not part of other identifiers)
                            # Use word boundaries to avoid partial matches
                            updated_body = re.sub(
                                rf'\b{old_name}\b',
                                new_name,
                                updated_body
                            )
                        fixed = fixed.replace(constructor_body, updated_body)
                        logger.info(f"Updated constructor body with renamed parameters")
        
        return fixed
    
    async def _stage_deployment(self, context: WorkflowContext, network: str, allow_insecure: bool):
        """Stage 7: Deployment"""
        stage_start = time.time()
        logger.info("🚀 Stage 7: Deployment")
        
        try:
            if not context.contract_code or not context.contract_name:
                raise ValueError("Contract code or name missing")
            
            # Check audit results
            audit_severity = None
            if context.audit_results:
                audit_severity = context.audit_results.get("severity", "low")
            
            if audit_severity == "high" and not allow_insecure:
                context.add_stage_result(
                    PipelineStage.DEPLOYMENT,
                    "skipped",
                    output={"reason": "High severity audit issues"},
                    duration_ms=(time.time() - stage_start) * 1000
                )
                return {"status": "skipped", "reason": "High severity audit"}
            
            deployment_result = await self.agent.deploy_contract(
                context.contract_code,
                network,
                context.contract_name
            )
            
            # Check deployment result status
            deployment_status = deployment_result.get("status", "unknown")
            
            if deployment_status in ["success", "deployed"]:
                # Handle both "address" and "contract_address" keys for compatibility
                context.deployment_address = (
                    deployment_result.get("address") or 
                    deployment_result.get("contract_address")
                )
                # Handle both "tx_hash" and "transaction_hash" keys for compatibility
                context.deployment_tx_hash = (
                    deployment_result.get("tx_hash") or 
                    deployment_result.get("transaction_hash")
                )
                context.deployment_network = network
                
                duration = (time.time() - stage_start) * 1000
                context.add_stage_result(
                    PipelineStage.DEPLOYMENT,
                    "success",
                    output=deployment_result,
                    duration_ms=duration
                )
                logger.info("✅ Deployment successful")
                logger.info(f"   Contract Address: {context.deployment_address}")
                logger.info(f"   Transaction Hash: {context.deployment_tx_hash}")
                return deployment_result
            else:
                # Deployment failed - provide detailed error information
                error_msg = deployment_result.get("error", "Deployment failed")
                error_details = deployment_result.get("error_details", {})
                suggestions = deployment_result.get("suggestions", [])
                
                duration = (time.time() - stage_start) * 1000
                context.add_stage_result(
                    PipelineStage.DEPLOYMENT,
                    "error",
                    error=error_msg,
                    error_type=error_details.get("error_type", "deployment_failure"),
                    duration_ms=duration,
                    output={
                        "error": error_msg,
                        "error_details": error_details,
                        "suggestions": suggestions
                    }
                )
                
                # Log detailed failure information
                logger.error(f"❌ Deployment failed: {error_msg}")
                if error_details:
                    logger.error(f"   Error Type: {error_details.get('error_type', 'Unknown')}")
                    logger.error(f"   Contract: {error_details.get('contract_name', 'Unknown')}")
                    if error_details.get('rpc_url'):
                        logger.error(f"   RPC URL: {error_details.get('rpc_url')}")
                
                if suggestions:
                    logger.info("💡 Recovery suggestions:")
                    for suggestion in suggestions:
                        logger.info(f"   • {suggestion}")
                
                # Don't raise - allow workflow to continue and complete with error status
                logger.info("⚠️ Deployment stage failed - workflow will continue to output stage")
                return deployment_result
                
        except Exception as e:
            duration = (time.time() - stage_start) * 1000
            error_type = type(e).__name__
            
            context.add_stage_result(
                PipelineStage.DEPLOYMENT,
                "error",
                error=str(e),
                error_type=error_type,
                duration_ms=duration,
                output={
                    "error": str(e),
                    "error_type": error_type,
                    "suggestions": [
                        "Check network connectivity",
                        "Verify RPC endpoint is accessible",
                        "Check account balance for gas fees",
                        "Review contract code for compilation issues"
                    ]
                }
            )
            
            # Log detailed exception information
            logger.error(f"❌ Deployment exception: {error_type}: {str(e)}")
            logger.info("💡 Recovery suggestions:")
            logger.info("   • Check network connectivity and RPC endpoint")
            logger.info("   • Verify account has sufficient balance for gas")
            logger.info("   • Review contract compilation artifacts")
            logger.info("   • Check diagnostic bundle for detailed error trace")
            
            # Don't raise - allow workflow to complete gracefully
            logger.info("⚠️ Deployment stage exception - workflow will continue to output stage")
            return {
                "status": "error",
                "error": str(e),
                "error_type": error_type,
                "stage": "deployment"
            }
    
    async def _stage_verification(self, context: WorkflowContext, network: str):
        """Stage 8: Verification & Artifact Storage per ideal workflow"""
        stage_start = time.time()
        logger.info("✔️ Stage 8: Verification & Artifact Storage")
        
        try:
            if not context.deployment_address:
                raise ValueError("No deployment address for verification")
            
            # Step 1: Verify on block explorer (per ideal workflow)
            verification_result = await self.agent.verify_contract(
                context.deployment_address,
                context.contract_code,
                network
            )
            
            context.verification_status = verification_result.get("status")
            context.verification_url = verification_result.get("explorer_url")
            
            # Step 2: Prepare artifacts for IPFS storage (even if upload_scope not set)
            # Store artifact metadata in context for potential upload
            artifacts_metadata = {
                "contract": {
                    "address": context.deployment_address,
                    "name": context.contract_name,
                    "code": context.contract_code,
                    "abi": verification_result.get("abi"),  # If available from verification
                },
                "deployment": {
                    "tx_hash": context.deployment_tx_hash,
                    "network": network,
                    "timestamp": context.created_at
                },
                "explorer_url": verification_result.get("explorer_url"),
                "verification_status": verification_result.get("status")
            }
            
            # Step 3: Generate artifact paths for local storage (robust path handling)
            from pathlib import Path
            from core.config.paths import PathManager
            
            try:
                # Use PathManager for robust path resolution
                path_manager = PathManager(command_type="verify")
                artifacts_dir = path_manager.get_artifacts_dir() / "deploy" / network
                artifacts_dir.mkdir(parents=True, exist_ok=True)
                
                # Validate artifacts directory was created
                if not artifacts_dir.exists():
                    raise OSError(f"Failed to create artifacts directory: {artifacts_dir}")
                
                logger.debug(f"Artifacts directory: {artifacts_dir}")
                
                # Save ABI if available
                abi_path = None
                if verification_result.get("abi"):
                    abi_file = artifacts_dir / f"{context.contract_name}.abi.json"
                    try:
                        import json
                        abi_file.write_text(json.dumps(verification_result["abi"], indent=2), encoding="utf-8")
                        artifacts_metadata["abi_path"] = str(abi_file.resolve())  # Use absolute path
                        abi_path = str(abi_file.resolve())
                        logger.info(f"💾 Saved ABI to: {abi_file}")
                    except (OSError, IOError) as e:
                        logger.error(f"❌ Failed to save ABI file: {e}")
                        # Continue without ABI path - non-critical
                
                # Save deployment metadata
                metadata_file = artifacts_dir / f"{context.contract_name}.metadata.json"
                try:
                    import json
                    metadata_file.write_text(json.dumps(artifacts_metadata, indent=2), encoding="utf-8")
                    context.metadata["metadata_path"] = str(metadata_file.resolve())  # Use absolute path
                    if abi_path:
                        context.metadata["abi_path"] = abi_path
                    context.metadata["artifacts_stored"] = True
                    logger.info(f"💾 Saved deployment metadata to: {metadata_file}")
                except (OSError, IOError) as e:
                    logger.error(f"❌ Failed to save metadata file: {e}")
                    # Mark as stored with warning
                    context.metadata["artifacts_stored"] = False
                    context.metadata["artifact_storage_error"] = str(e)
                    
            except Exception as e:
                logger.error(f"❌ Artifact path handling failed: {e}")
                # Continue without artifact storage - non-critical for verification
                context.metadata["artifacts_stored"] = False
                context.metadata["artifact_storage_error"] = str(e)
            
            duration = (time.time() - stage_start) * 1000
            context.add_stage_result(
                PipelineStage.VERIFICATION,
                "success",
                output={
                    **verification_result,
                    "artifacts_stored": True,
                    "artifact_paths": {
                        "abi": abi_path,
                        "metadata": str(metadata_file)
                    }
                },
                duration_ms=duration
            )
            logger.info("✅ Verification completed and artifacts stored")
            return verification_result
            
        except Exception as e:
            duration = (time.time() - stage_start) * 1000
            context.add_stage_result(
                PipelineStage.VERIFICATION,
                "error",
                error=str(e),
                duration_ms=duration
            )
            # Don't raise - verification failure is non-fatal
            logger.warning(f"⚠️ Verification failed: {e}")
            # Provide actionable error message per ideal workflow
            logger.info("💡 Recovery suggestions:")
            logger.info("   1. Check block explorer API availability")
            logger.info("   2. Verify network RPC endpoint is accessible")
            logger.info("   3. Manually verify contract on explorer if needed")
    
    async def _stage_output(self, context: WorkflowContext, upload_scope: Optional[str] = None) -> Dict[str, Any]:
        """Stage 9: Output & diagnostics"""
        stage_start = time.time()
        logger.info("📊 Stage 9: Output & Diagnostics")
        
        # CRITICAL: PipelineStage is available from module-level import (line 16)
        # No local imports or re-definitions allowed - always use module-level enum
        # Defensive check already done at module load (line 23-24)
        
        # Generate final result per ideal workflow (comprehensive output)
        # Note: Status will be overridden by caller based on critical vs non-critical failures
        result = {
            "status": "success",  # Will be set by caller
            "workflow_id": context.workflow_id,
            "contract_name": context.contract_name,
            "contract_path": context.contract_path,
            "generation": {
                "status": next(
                    (s.status for s in context.stages if s.stage == PipelineStage.GENERATION),
                    "unknown"
                ),
                "contract_name": context.contract_name,
                "contract_path": context.contract_path
            },
            "compilation": {
                "success": context.compilation_success,
                "artifact_path": context.compilation_artifact_path
            },
            "testing": {
                "status": next(
                    (s.status for s in context.stages if s.stage == PipelineStage.TESTING),
                    "skipped"
                ),
                "results": next(
                    (s.output for s in context.stages if s.stage == PipelineStage.TESTING),
                    None
                )
            },
            "audit": context.audit_results,
            "deployment": {
                "address": context.deployment_address,
                "tx_hash": context.deployment_tx_hash,
                "network": context.deployment_network,
                "status": next(
                    (s.status for s in context.stages if s.stage == PipelineStage.DEPLOYMENT),
                    "skipped"
                ),
                "explorer_url": f"https://explorer.{context.deployment_network}.io/address/{context.deployment_address}" if context.deployment_address else None,
                "error": next(
                    (s.error for s in context.stages if s.stage == PipelineStage.DEPLOYMENT and s.error),
                    None
                ),
                "error_details": next(
                    (s.output.get("error_details") for s in context.stages if s.stage == PipelineStage.DEPLOYMENT and s.output and s.output.get("error_details")),
                    None
                ),
                "suggestions": next(
                    (s.output.get("suggestions", []) for s in context.stages if s.stage == PipelineStage.DEPLOYMENT and s.output and s.output.get("suggestions")),
                    []
                )
            },
            "verification": {
                "status": context.verification_status or next(
                    (s.status for s in context.stages if s.stage == PipelineStage.VERIFICATION),
                    "skipped"
                ),
                "url": context.verification_url,
                "artifacts_stored": context.metadata.get("artifacts_stored", False),
                "error": next(
                    (s.error for s in context.stages if s.stage == PipelineStage.VERIFICATION and s.error),
                    None
                )
            },
            "artifacts": {
                "ipfs_uploads": context.metadata.get("ipfs_uploads", []),
                "upload_scope": context.metadata.get("upload_scope"),
                "local_paths": {
                    "contract": context.contract_path,
                    "abi": context.metadata.get("abi_path"),
                    "metadata": context.metadata.get("metadata_path")
                }
            },
            "stages": [
                {
                    "stage": stage.stage.value,
                    "status": stage.status,
                    "duration_ms": stage.duration_ms,
                    "error": stage.error if stage.error else None
                }
                for stage in context.stages
            ],
            "diagnostics": {
                "has_errors": context.has_error(),
                "error_count": len([s for s in context.stages if s.status == "error"]),
                "warning_count": len([s for s in context.stages if s.status == "warning"])
            }
        }
        
        # Save diagnostic bundle if there were errors (per ideal workflow: fail-loud with diagnostics)
        if context.has_error():
            diagnostic_path = self.context_manager.save_diagnostic_bundle(context)
            result["diagnostic_bundle"] = str(diagnostic_path)
            result["error_recovery"] = {
                "diagnostic_bundle": str(diagnostic_path),
                "next_steps": [
                    "Review diagnostic bundle for detailed error information",
                    "Check error messages above for actionable fixes",
                    "Review workflow context at: " + str(self.context_manager.get_context_path(context.workflow_id))
                ]
            }
        
        duration = (time.time() - stage_start) * 1000
        context.add_stage_result(
            PipelineStage.OUTPUT,
            "success",
            output=result,
            duration_ms=duration
        )
        
        return result
    
    async def _auto_upload_artifacts(self, context: WorkflowContext, upload_scope: str):
        """Auto-upload workflow artifacts to Pinata IPFS"""
        try:
            import os
            from services.storage.dual_scope_pinata import PinataScopeClient, UploadScope
            
            # Get Pinata config
            pinata_config = {
                'team_api_key': os.getenv('PINATA_TEAM_API_KEY') or os.getenv('PINATA_API_KEY'),
                'team_api_secret': os.getenv('PINATA_TEAM_SECRET_KEY') or os.getenv('PINATA_SECRET_KEY'),
                'community_api_key': os.getenv('PINATA_COMMUNITY_API_KEY') or os.getenv('PINATA_API_KEY'),
                'community_api_secret': os.getenv('PINATA_COMMUNITY_SECRET_KEY') or os.getenv('PINATA_SECRET_KEY'),
                'registry_dir': self.workspace_dir / "data" / "ipfs_registries"
            }
            
            # Initialize Pinata client
            pinata_client = PinataScopeClient(pinata_config)
            
            scope = UploadScope.TEAM if upload_scope == 'team' else UploadScope.COMMUNITY
            
            # Initialize moderation and analytics for Community uploads
            moderation = None
            analytics = None
            if scope == UploadScope.COMMUNITY:
                try:
                    from services.security.community_moderation import CommunityModeration
                    from services.analytics.community_analytics import CommunityAnalytics
                    moderation = CommunityModeration()
                    analytics = CommunityAnalytics()
                except ImportError:
                    logger.debug("Moderation/analytics modules not available")
            
            # Generate workflow signature
            workflow_signature = f"{context.workflow_id}-{context.created_at}"
            
            uploads = []
            
            # Upload contract code
            if context.contract_code:
                try:
                    # Scan content for Community uploads
                    scan_result = None
                    if scope == UploadScope.COMMUNITY and moderation:
                        scan_result = moderation.scan_content(context.contract_code, 'contract')
                        if not scan_result.get('safe'):
                            logger.warning(f"⚠️ Content flagged during scan: {scan_result.get('flags')}")
                            # Still upload but mark as flagged
                    
                    upload_result = await pinata_client.upload_artifact(
                        content=context.contract_code,
                        artifact_type='contract',
                        scope=scope,
                        metadata={
                            'description': f"Contract: {context.contract_name}",
                            'tags': ['contract', context.contract_category or 'smart-contract'],
                            'keyvalues': {
                                'contract_name': context.contract_name or 'unknown',
                                'compilation_success': str(context.compilation_success),
                                'audit_severity': context.audit_results.get('severity', 'unknown') if context.audit_results else 'unknown',
                                'flagged': str(not scan_result.get('safe') if scan_result else False),
                                'risk_score': str(scan_result.get('risk_score', 0.0) if scan_result else 0.0),
                                'quality_score': str(scan_result.get('quality_score', 0.5) if scan_result else 0.5)
                            }
                        },
                        workflow_signature=workflow_signature
                    )
                    uploads.append({'type': 'contract', 'cid': upload_result['cid']})
                    logger.info(f"✅ Uploaded contract to IPFS ({scope.value}): {upload_result['cid']}")
                    
                    # Record analytics
                    if analytics and scope == UploadScope.COMMUNITY:
                        artifact_id = upload_result.get('artifact_id')
                        analytics.record_upload(
                            artifact_id,
                            'contract',
                            user_id=None,  # Could extract from context if available
                            metadata={'compilation_success': context.compilation_success}
                        )
                        # Calculate quality score
                        quality_score = analytics.calculate_quality_score(artifact_id, {
                            'compilation_success': context.compilation_success,
                            'audit_severity': context.audit_results.get('severity', 'unknown') if context.audit_results else 'unknown',
                            'timestamp': upload_result.get('registry_entry', {}).get('timestamp')
                        })
                        logger.info(f"Quality score: {quality_score:.2f}")
                        
                except Exception as e:
                    logger.warning(f"⚠️ Failed to upload contract: {e}")
            
            # Upload user prompt
            if context.user_prompt:
                try:
                    upload_result = await pinata_client.upload_artifact(
                        content=context.user_prompt,
                        artifact_type='prompt',
                        scope=scope,
                        metadata={
                            'description': f"User prompt for workflow {context.workflow_id}",
                            'tags': ['prompt', 'workflow'],
                            'keyvalues': {
                                'workflow_id': context.workflow_id
                            }
                        },
                        workflow_signature=workflow_signature
                    )
                    uploads.append({'type': 'prompt', 'cid': upload_result['cid']})
                    logger.info(f"✅ Uploaded prompt to IPFS ({scope.value}): {upload_result['cid']}")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to upload prompt: {e}")
            
            # Upload workflow metadata
            workflow_metadata = {
                'workflow_id': context.workflow_id,
                'contract_name': context.contract_name,
                'compilation_success': context.compilation_success,
                'deployment_address': context.deployment_address,
                'deployment_tx_hash': context.deployment_tx_hash,
                'audit_results': context.audit_results,
                'stages_count': len(context.stages)
            }
            
            try:
                upload_result = await pinata_client.upload_artifact(
                    content=json.dumps(workflow_metadata, indent=2),
                    artifact_type='workflow',
                    scope=scope,
                    metadata={
                        'description': f"Workflow metadata for {context.workflow_id}",
                        'tags': ['workflow', 'metadata'],
                        'keyvalues': {
                            'workflow_id': context.workflow_id,
                            'status': 'success' if not context.has_error() else 'error'
                        }
                    },
                    workflow_signature=workflow_signature
                )
                uploads.append({'type': 'workflow', 'cid': upload_result['cid']})
                logger.info(f"✅ Uploaded workflow metadata to IPFS ({scope.value}): {upload_result['cid']}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to upload workflow metadata: {e}")
            
            # Store upload results in context metadata
            context.metadata['ipfs_uploads'] = uploads
            context.metadata['upload_scope'] = upload_scope
            
            logger.info(f"📤 Auto-upload complete: {len(uploads)} artifacts uploaded to {scope.value} scope")
            
        except ImportError:
            logger.debug("Pinata client not available - skipping auto-upload")
        except Exception as e:
            logger.warning(f"⚠️ Auto-upload failed: {e}")



