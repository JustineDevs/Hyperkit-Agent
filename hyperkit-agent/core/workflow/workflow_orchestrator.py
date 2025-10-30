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

from core.workflow.context_manager import (
    ContextManager, WorkflowContext, PipelineStage, StageResult
)
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
        rag_scope: str = 'official-only'  # 'official-only' or 'opt-in-community'
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
        try:
            # Stage 0: Preflight checks
            await self._stage_preflight(context)
            
            # Stage 1: Input parsing & RAG context
            await self._stage_input_parsing(context, user_prompt, rag_scope)
            
            # Stage 2: Contract generation
            await self._stage_generation(context, user_prompt, rag_scope)
            
            # Stage 3: Dependency resolution
            await self._stage_dependency_resolution(context)
            
            # Stage 4: Compilation
            await self._stage_compilation(context)
            
            # Stage 5: Testing (optional)
            if not test_only:
                await self._stage_testing(context)
            
            # Stage 6: Auditing
            await self._stage_auditing(context)
            
            # Stage 7: Deployment
            if not test_only:
                await self._stage_deployment(context, network, allow_insecure)
            
            # Stage 8: Verification
            if not test_only and auto_verification and context.deployment_address:
                await self._stage_verification(context, network)
            
            # Stage 9: Output & diagnostics
            result = await self._stage_output(context, upload_scope)
            
            # Save context
            self.context_manager.save_context(context)
            
            # Auto-upload artifacts to Pinata if upload_scope is specified
            if upload_scope and upload_scope in ['team', 'community'] and not context.has_error():
                await self._auto_upload_artifacts(context, upload_scope)
            
            # Clean up environment on success
            if self.env_manager:
                self.env_manager.cleanup(preserve_on_error=False, had_errors=False)
            
            logger.info(f"✅ Workflow completed successfully: {workflow_id}")
            return result
            
        except Exception as e:
            had_errors = True
            # Save context even on failure for debugging
            context.add_stage_result(
                PipelineStage.OUTPUT,
                "error",
                error=str(e),
                error_type="workflow_exception"
            )
            self.context_manager.save_context(context)
            
            # Generate diagnostic bundle
            diagnostic_path = self.context_manager.save_diagnostic_bundle(context)
            
            # Preserve environment for debugging
            if self.env_manager:
                self.env_manager.preserve_for_debugging()
                self.env_manager.cleanup(preserve_on_error=True, had_errors=True)
            
            logger.error(f"❌ Workflow failed: {e}")
            logger.info(f"📋 Diagnostic bundle saved: {diagnostic_path}")
            logger.info(f"📁 Temp environment preserved: {self.env_manager.temp_dir if self.env_manager else 'N/A'}")
            
            return {
                "status": "error",
                "error": str(e),
                "workflow_id": workflow_id,
                "diagnostic_bundle": str(diagnostic_path),
                "temp_dir": str(self.env_manager.temp_dir) if self.env_manager else None,
                "context": context.to_dict()
            }
    
    async def _stage_preflight(self, context: WorkflowContext):
        """Stage 0: Preflight checks"""
        stage_start = time.time()
        logger.info("🔍 Stage 0: Preflight Checks")
        
        try:
            checks = self.dep_manager.preflight_check()
            
            # Required tools (workflow will fail if missing)
            required_tools = ["forge", "python"]
            missing_required = [tool for tool in required_tools if not checks.get(tool, False)]
            
            # Optional tools (warnings only)
            optional_tools = ["npm", "node", "pip"]
            missing_optional = [tool for tool in optional_tools if not checks.get(tool, False)]
            
            if missing_required:
                error_msg = f"Missing required tools: {', '.join(missing_required)}. Please install these system tools."
                context.add_stage_result(
                    PipelineStage.INPUT_PARSING,
                    "error",
                    error=error_msg,
                    error_type="missing_required_tools"
                )
                raise RuntimeError(error_msg)
            
            # Log warnings for optional tools
            if missing_optional:
                logger.warning(f"⚠️ Optional tools not found: {', '.join(missing_optional)}. These are only needed if contracts use npm/Node.js dependencies.")
            
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
        """Stage 1: Input parsing & RAG context retrieval"""
        stage_start = time.time()
        logger.info("📥 Stage 1: Input Parsing & Context Retrieval")
        
        try:
            # Get RAG context if available
            rag_context = ""
            if hasattr(self.agent, 'rag') and self.agent.rag:
                try:
                    rag_context = await self.agent.rag.retrieve(user_prompt, rag_scope=rag_scope)
                    logger.info(f"Retrieved RAG context with scope: {rag_scope}")
                except Exception as e:
                    logger.warning(f"RAG retrieval failed: {e}")
                    rag_context = ""
            
            # Store RAG context for reuse in generation stage
            context.metadata['rag_context'] = rag_context
            context.metadata['rag_scope'] = rag_scope
            
            duration = (time.time() - stage_start) * 1000
            context.add_stage_result(
                PipelineStage.INPUT_PARSING,
                "success",
                output={"rag_context_length": len(rag_context), "rag_scope": rag_scope, "rag_context": rag_context},
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
            raise
    
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
        """Stage 5: Testing (placeholder)"""
        stage_start = time.time()
        logger.info("🧪 Stage 5: Testing")
        
        # Placeholder for test execution
        duration = (time.time() - stage_start) * 1000
        context.add_stage_result(
            PipelineStage.TESTING,
            "skipped",
            output={"note": "Testing stage not yet implemented"},
            duration_ms=duration
        )
    
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
                context.security_score = audit_result.get("security_score")
                
                duration = (time.time() - stage_start) * 1000
                context.add_stage_result(
                    PipelineStage.AUDITING,
                    "success",
                    output=audit_result,
                    duration_ms=duration
                )
                logger.info("✅ Audit completed")
                return audit_result
            else:
                raise Exception(audit_result.get("error", "Audit failed"))
                
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
        
        # 1. Remove any _beforeTokenTransfer override block entirely (broad match)
        patterns = [
            r"function\s+_beforeTokenTransfer\s*\([^)]*\)\s*[^\{]*\{[\s\S]*?\}",
        ]
        for pat in patterns:
            if re.search(pat, fixed, re.MULTILINE | re.DOTALL):
                fixed = re.sub(pat, "", fixed, flags=re.MULTILINE | re.DOTALL)
        
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
            
            if deployment_result.get("status") in ["success", "deployed"]:
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
                return deployment_result
            else:
                raise Exception(deployment_result.get("error", "Deployment failed"))
                
        except Exception as e:
            duration = (time.time() - stage_start) * 1000
            context.add_stage_result(
                PipelineStage.DEPLOYMENT,
                "error",
                error=str(e),
                duration_ms=duration
            )
            raise
    
    async def _stage_verification(self, context: WorkflowContext, network: str):
        """Stage 8: Verification"""
        stage_start = time.time()
        logger.info("✔️ Stage 8: Verification")
        
        try:
            if not context.deployment_address:
                raise ValueError("No deployment address for verification")
            
            verification_result = await self.agent.verify_contract(
                context.deployment_address,
                network
            )
            
            context.verification_status = verification_result.get("status")
            context.verification_url = verification_result.get("explorer_url")
            
            duration = (time.time() - stage_start) * 1000
            context.add_stage_result(
                PipelineStage.VERIFICATION,
                "success",
                output=verification_result,
                duration_ms=duration
            )
            logger.info("✅ Verification completed")
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
    
    async def _stage_output(self, context: WorkflowContext, upload_scope: Optional[str] = None) -> Dict[str, Any]:
        """Stage 9: Output & diagnostics"""
        stage_start = time.time()
        logger.info("📊 Stage 9: Output & Diagnostics")
        
        # Generate final result
        result = {
            "status": "success" if not context.has_error() else "error",
            "workflow_id": context.workflow_id,
            "contract_name": context.contract_name,
            "contract_path": context.contract_path,
            "compilation": {
                "success": context.compilation_success,
                "artifact_path": context.compilation_artifact_path
            },
            "audit": context.audit_results,
            "deployment": {
                "address": context.deployment_address,
                "tx_hash": context.deployment_tx_hash,
                "network": context.deployment_network
            },
            "verification": {
                "status": context.verification_status,
                "url": context.verification_url
            },
            "stages": [
                {
                    "stage": stage.stage.value,
                    "status": stage.status,
                    "duration_ms": stage.duration_ms
                }
                for stage in context.stages
            ]
        }
        
        # Save diagnostic bundle if there were errors
        if context.has_error():
            diagnostic_path = self.context_manager.save_diagnostic_bundle(context)
            result["diagnostic_bundle"] = str(diagnostic_path)
        
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

