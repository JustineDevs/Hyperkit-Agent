"""
Self-Healing Workflow Orchestrator
Orchestrates the complete pipeline with dependency management, context tracking, and auto-recovery.
"""

import asyncio
import logging
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

# Defensive check: Ensure PipelineStage is properly imported at module level
if not hasattr(PipelineStage, "GENERATION"):
    raise ImportError("PipelineStage not properly imported at module level - check imports")
from core.workflow.error_handler import SelfHealingErrorHandler, handle_error_with_retry
from core.workflow.environment_manager import EnvironmentManager
from services.dependencies.dependency_manager import DependencyManager

logger = logging.getLogger(__name__)


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
        self.error_handler = SelfHealingErrorHandler()
        self.dep_manager = DependencyManager(self.workspace_dir)
        self.env_manager: Optional[EnvironmentManager] = None
        
        logger.info("WorkflowOrchestrator initialized with self-healing capabilities")
    
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
        if resume_from_diagnostic:
            logger.info(f"🔄 Resuming workflow from diagnostic bundle: {resume_from_diagnostic}")
            try:
                diagnostic_path = Path(resume_from_diagnostic)
                if not diagnostic_path.exists():
                    logger.error(f"Diagnostic bundle not found: {resume_from_diagnostic}")
                    return {
                        "status": "error",
                        "error": f"Diagnostic bundle not found: {resume_from_diagnostic}",
                        "suggestions": ["Verify the diagnostic bundle path is correct"]
                    }
                
                # Load diagnostic bundle
                with open(diagnostic_path, 'r') as f:
                    diagnostic_data = json.load(f)
                
                # Extract workflow_id and recreate context
                workflow_id = diagnostic_data.get('workflow_id', str(uuid.uuid4())[:8])
                context = self.context_manager.create_context(workflow_id, diagnostic_data.get('user_prompt', user_prompt), self.workspace_dir)
                
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
            workflow_id = str(uuid.uuid4())[:8]
            context = self.context_manager.create_context(workflow_id, user_prompt, self.workspace_dir)
        
        # Create isolated environment
        self.env_manager = EnvironmentManager(self.workspace_dir, workflow_id)
        temp_dir = self.env_manager.create_isolated_environment()
        context.temp_dir = str(temp_dir)
        context.metadata["temp_dir"] = str(temp_dir)
        
        logger.info(f"🚀 Starting self-healing workflow: {workflow_id}")
        logger.info(f"📝 User prompt: {user_prompt}")
        logger.info(f"📁 Isolated environment: {temp_dir}")
        
        had_errors = False
        
        # Determine resume point if resuming from diagnostic bundle
        last_successful_stage = context.get_last_successful_stage() if resume_from_diagnostic else None
        
        try:
            # Resume from last successful stage if resuming from diagnostic bundle
            if resume_from_diagnostic and last_successful_stage:
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
            
            # Stage 0: Preflight checks (skip if resuming past generation)
            if not resume_from_diagnostic or not last_successful_stage or last_successful_stage.value == 'input_parsing':
                await self._stage_preflight(context)
            
            # Stage 1: Input parsing & RAG context (skip if resuming past this)
            if not resume_from_diagnostic or not last_successful_stage or last_successful_stage.value == 'input_parsing':
                await self._stage_input_parsing(context, user_prompt, rag_scope)
            
            # Stage 2: Contract generation (skip if resuming past this)
            if not resume_from_diagnostic or not last_successful_stage or last_successful_stage.value in ['generation', 'input_parsing']:
                await self._stage_generation(context, user_prompt, rag_scope)
            
            # Stage 3: Dependency resolution (skip if resuming past this)
            if not resume_from_diagnostic or not last_successful_stage or last_successful_stage.value in ['dependency_resolution', 'generation', 'input_parsing']:
                await self._stage_dependency_resolution(context)
            
            # Stage 4: Compilation (skip if resuming past this)
            if not resume_from_diagnostic or not last_successful_stage or last_successful_stage.value in ['compilation', 'dependency_resolution', 'generation', 'input_parsing']:
                await self._stage_compilation(context)
            
            # Stage 5: Testing (skip if resuming past this)
            if not test_only:
                if not resume_from_diagnostic or not last_successful_stage or last_successful_stage.value in ['testing', 'compilation', 'dependency_resolution', 'generation', 'input_parsing']:
                    await self._stage_testing(context)
            
            # Stage 6: Auditing (skip if resuming past this)
            if not resume_from_diagnostic or not last_successful_stage or last_successful_stage.value in ['auditing', 'testing', 'compilation', 'dependency_resolution', 'generation', 'input_parsing']:
                await self._stage_auditing(context)
            
            # Stage 7: Deployment (skip if resuming past this)
            deployment_success = False
            if not test_only:
                if not resume_from_diagnostic or not last_successful_stage or last_successful_stage.value in ['deployment', 'auditing', 'testing', 'compilation', 'dependency_resolution', 'generation', 'input_parsing']:
                    try:
                        await self._stage_deployment(context, network, allow_insecure)
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
                if not resume_from_diagnostic or not last_successful_stage or last_successful_stage.value in ['verification', 'deployment', 'auditing', 'testing', 'compilation', 'dependency_resolution', 'generation', 'input_parsing']:
                    try:
                        await self._stage_verification(context, network)
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
                    
                    logger.info(f"📚 Retrieved RAG context: {len(rag_context)} characters")
                    if template_info:
                        logger.info(f"📦 Template matched: {template_info.get('cid', 'N/A')}")
                except Exception as rag_error:
                    logger.warning(f"⚠️ RAG context retrieval failed: {rag_error}")
                    # Continue without RAG - it's helpful but not required
                    rag_context = ""
            else:
                logger.warning("⚠️ RAG system not available - proceeding without template context")
                logger.info("💡 Tip: Configure PINATA_API_KEY and PINATA_SECRET_KEY for template retrieval")
            
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
        """Stage 2: Contract generation"""
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
                
                generation_result = await self.agent.generate_contract(user_prompt, rag_context)
                
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
                if attempt < max_retries:
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
            fix_success, fix_msg = await handle_error_with_retry(
                self.error_handler, e, fix_context, max_retries=2
            )
            
            if not fix_success:
                duration = (time.time() - stage_start) * 1000
                context.add_stage_result(
                    PipelineStage.DEPENDENCY_RESOLUTION,
                    "error",
                    error=str(e),
                    duration_ms=duration
                )
                raise
            
            # Retry dependency resolution after fix
            logger.info("Retrying dependency resolution after auto-fix...")
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
        
        # 2. Fix constructor parameter shadowing of functions
        # Find all public/external function names in the contract
        # Pattern matches: function name(...) public/external [view/pure/payable] [returns (...)]
        function_pattern = r'function\s+(\w+)\s*\([^)]*\)\s+(?:public|external)'
        function_names = set(re.findall(function_pattern, fixed))
        
        # Log found function names for debugging
        logger.info(f"Sanitizer: Checking for shadowing issues...")
        if function_names:
            logger.info(f"Sanitizer: Found functions that may shadow: {', '.join(function_names)}")
        else:
            logger.info("Sanitizer: No public/external functions found to check for shadowing")
        
        if function_names:
            # Find constructor and its parameters
            constructor_pattern = r'constructor\s*\(([^)]+)\)'
            constructor_match = re.search(constructor_pattern, fixed)
            
            if constructor_match:
                params_original = constructor_match.group(1)
                params = params_original
                modified = False
                replaced_names = {}
                
                # Check each parameter for shadowing
                for func_name in function_names:
                    # Match parameter with this name: type paramName or type memory paramName
                    # Simpler pattern: match any type followed by the parameter name
                    # Look for the parameter name as a standalone word in the params string
                    param_pattern = rf'\b(\w+(?:\s+memory)?)\s+\b({func_name})\b'
                    param_match = re.search(param_pattern, params)
                    if param_match:
                        # Rename parameter to _paramName to avoid shadowing
                        new_name = f'_{func_name}'
                        # Replace the exact match in params list
                        old_param_decl = param_match.group(0)
                        new_param_decl = f'{param_match.group(1)} {new_name}'
                        params = params.replace(old_param_decl, new_param_decl)
                        replaced_names[func_name] = new_name
                        modified = True
                        logger.info(f"Sanitizer: Will rename constructor parameter '{func_name}' to '{new_name}'")
                
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
                context.deployment_address = deployment_result.get("contract_address")
                context.deployment_tx_hash = deployment_result.get("tx_hash")
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



