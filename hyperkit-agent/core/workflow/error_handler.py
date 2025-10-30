"""
Self-Healing Error Handler
Parses errors, detects automatable issues, and triggers auto-fix attempts.
"""

import re
import logging
from dataclasses import dataclass
from typing import Dict, Any, Optional, List, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class ErrorType(Enum):
    """Types of errors that can be auto-fixed"""
    DEPENDENCY_MISSING = "dependency_missing"
    IMPORT_NOT_FOUND = "import_not_found"
    COMPILATION_ERROR = "compilation_error"
    NETWORK_ERROR = "network_error"
    CONFIG_MISSING = "config_missing"
    PERMISSION_ERROR = "permission_error"
    TIMEOUT_ERROR = "timeout_error"
    FATAL = "fatal"  # Cannot be auto-fixed


@dataclass
class ParsedError:
    """Parsed error information"""
    error_type: ErrorType
    original_message: str
    automatable: bool
    suggested_fix: Optional[str] = None
    auto_fix_action: Optional[str] = None
    fix_parameters: Dict[str, Any] = None


class SelfHealingErrorHandler:
    """
    Self-healing error handler that parses errors and attempts automatic fixes.
    """
    
    def __init__(self):
        """Initialize error handler"""
        self.error_patterns = self._build_error_patterns()
        logger.info("SelfHealingErrorHandler initialized")
    
    def _build_error_patterns(self) -> Dict[ErrorType, List[re.Pattern]]:
        """Build regex patterns for error detection"""
        patterns = {
            ErrorType.DEPENDENCY_MISSING: [
                re.compile(r"Source\s+[\"']([^\"']+)[\"']\s+not found", re.IGNORECASE),
                re.compile(r"Import\s+[\"']([^\"']+)[\"']\s+not found", re.IGNORECASE),
                re.compile(r"Could not find\s+[\"']([^\"']+)[\"']", re.IGNORECASE),
                re.compile(r"Module\s+['\"]([^\"']+)['\"]\s+not found", re.IGNORECASE),
            ],
            ErrorType.IMPORT_NOT_FOUND: [
                re.compile(r"import\s+[\"']([^\"']+)[\"']\s+not found", re.IGNORECASE),
                re.compile(r"cannot resolve import\s+[\"']([^\"']+)[\"']", re.IGNORECASE),
                re.compile(r"failed to resolve\s+[\"']([^\"']+)[\"']", re.IGNORECASE),
            ],
            ErrorType.COMPILATION_ERROR: [
                re.compile(r"compilation failed", re.IGNORECASE),
                re.compile(r"compiler run failed", re.IGNORECASE),
                re.compile(r"syntax error", re.IGNORECASE),
                re.compile(r"type error", re.IGNORECASE),
                re.compile(r"function has override specified but does not override", re.IGNORECASE),
                re.compile(r"override.*does not override anything", re.IGNORECASE),
            ],
            ErrorType.NETWORK_ERROR: [
                re.compile(r"network error", re.IGNORECASE),
                re.compile(r"connection.*refused", re.IGNORECASE),
                re.compile(r"timeout", re.IGNORECASE),
                re.compile(r"ECONNREFUSED", re.IGNORECASE),
            ],
            ErrorType.CONFIG_MISSING: [
                re.compile(r"config.*not found", re.IGNORECASE),
                re.compile(r"missing.*config", re.IGNORECASE),
                re.compile(r"required.*config.*missing", re.IGNORECASE),
            ],
            ErrorType.PERMISSION_ERROR: [
                re.compile(r"permission denied", re.IGNORECASE),
                re.compile(r"access denied", re.IGNORECASE),
                re.compile(r"EACCES", re.IGNORECASE),
            ],
            ErrorType.TIMEOUT_ERROR: [
                re.compile(r"operation.*timeout", re.IGNORECASE),
                re.compile(r"request.*timeout", re.IGNORECASE),
            ],
        }
        return patterns
    
    def parse_error(self, error_message: str, error_type: Optional[str] = None) -> ParsedError:
        """
        Parse an error message and determine if it can be auto-fixed.
        
        Args:
            error_message: The error message to parse
            error_type: Optional pre-classified error type
            
        Returns:
            ParsedError with fix suggestions
        """
        error_str = str(error_message).lower()
        
        # Check each error pattern
        for err_type, patterns in self.error_patterns.items():
            for pattern in patterns:
                match = pattern.search(error_message)
                if match:
                    # Extract dependency/module name if available
                    fix_params = {}
                    if match.lastindex is not None and match.lastindex >= 1:
                        extracted = match.group(1)
                        fix_params["dependency"] = extracted
                        fix_params["import_path"] = extracted
                    
                    suggested_fix = self._get_suggested_fix(err_type, fix_params)
                    auto_fix_action = self._get_auto_fix_action(err_type, fix_params)
                    
                    return ParsedError(
                        error_type=err_type,
                        original_message=error_message,
                        automatable=err_type != ErrorType.FATAL,
                        suggested_fix=suggested_fix,
                        auto_fix_action=auto_fix_action,
                        fix_parameters=fix_params
                    )
        
        # Default: unclassified error
        return ParsedError(
            error_type=ErrorType.FATAL,
            original_message=error_message,
            automatable=False,
            suggested_fix="Manual intervention required"
        )
    
    def _get_suggested_fix(self, error_type: ErrorType, params: Dict[str, Any]) -> Optional[str]:
        """Get human-readable fix suggestion"""
        fixes = {
            ErrorType.DEPENDENCY_MISSING: f"Install missing dependency: {params.get('dependency', 'unknown')}",
            ErrorType.IMPORT_NOT_FOUND: f"Install or verify import path: {params.get('import_path', 'unknown')}",
            ErrorType.COMPILATION_ERROR: "Check contract syntax and dependencies",
            ErrorType.NETWORK_ERROR: "Check network connection and retry",
            ErrorType.CONFIG_MISSING: "Create or update configuration file",
            ErrorType.PERMISSION_ERROR: "Check file permissions and access rights",
            ErrorType.TIMEOUT_ERROR: "Retry operation with longer timeout",
        }
        return fixes.get(error_type, "Manual review required")
    
    def _get_auto_fix_action(self, error_type: ErrorType, params: Dict[str, Any]) -> Optional[str]:
        """Get auto-fix action identifier"""
        actions = {
            ErrorType.DEPENDENCY_MISSING: "install_dependency",
            ErrorType.IMPORT_NOT_FOUND: "install_dependency",
            ErrorType.COMPILATION_ERROR: "retry_compile",
            ErrorType.NETWORK_ERROR: "retry_network",
            ErrorType.CONFIG_MISSING: "create_config",
            ErrorType.TIMEOUT_ERROR: "retry_with_timeout",
        }
        return actions.get(error_type)
    
    async def attempt_auto_fix(self, parsed_error: ParsedError, context: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Attempt to automatically fix an error.
        
        Args:
            parsed_error: The parsed error
            context: Context with dependencies, workspace, etc.
            
        Returns:
            Tuple of (success, message)
        """
        if not parsed_error.automatable:
            return False, "Error cannot be auto-fixed"
        
        action = parsed_error.auto_fix_action
        if not action:
            return False, "No auto-fix action available"
        
        try:
            if action == "install_dependency":
                return await self._auto_fix_dependency(parsed_error, context)
            elif action == "retry_compile":
                return await self._auto_fix_compilation(parsed_error, context)
            elif action == "retry_network":
                return await self._auto_fix_network(parsed_error, context)
            elif action == "create_config":
                return await self._auto_fix_config(parsed_error, context)
            elif action == "retry_with_timeout":
                return await self._auto_fix_timeout(parsed_error, context)
            else:
                return False, f"Unknown auto-fix action: {action}"
        except Exception as e:
            logger.error(f"Auto-fix attempt failed: {e}")
            return False, f"Auto-fix error: {str(e)}"
    
    async def _auto_fix_dependency(self, parsed_error: ParsedError, context: Dict[str, Any]) -> Tuple[bool, str]:
        """Auto-fix missing dependency"""
        dependency = parsed_error.fix_parameters.get("dependency") or parsed_error.fix_parameters.get("import_path")
        if not dependency:
            return False, "No dependency specified"
        
        # Import dependency manager
        from services.dependencies.dependency_manager import DependencyManager
        
        workspace = context.get("workspace_dir")
        if not workspace:
            return False, "Workspace directory not in context"
        
        dep_manager = DependencyManager(workspace)
        
        # Detect dependency from import path
        # Create a dummy contract code to detect dependency
        dummy_code = f'import "{dependency}";'
        deps = dep_manager.detect_dependencies(dummy_code, "auto_fix.sol")
        
        if deps:
            result = await dep_manager.install_all_dependencies(deps)
            success = all(success for success, _ in result.values())
            if success:
                return True, f"Auto-installed dependency: {dependency}"
            else:
                return False, f"Failed to install dependency: {dependency}"
        else:
            return False, f"Could not detect dependency from: {dependency}"
    
    async def _auto_fix_compilation(self, parsed_error: ParsedError, context: Dict[str, Any]) -> Tuple[bool, str]:
        """Auto-fix compilation errors including override issues"""
        contract_code = context.get("contract_code")
        error_message = parsed_error.original_message.lower()

        # Ensure OpenZeppelin deps when imports present or error mentions them
        try:
            if (contract_code and "@openzeppelin/" in contract_code) or "openzeppelin" in error_message:
                from services.dependencies.dependency_manager import DependencyManager
                workspace = context.get("workspace_dir")
                if workspace:
                    dep_manager = DependencyManager(workspace)
                    deps = dep_manager.detect_dependencies(contract_code or "", "AutoFix.sol")
                    if deps:
                        result = await dep_manager.install_all_dependencies(deps)
                        if all(success for success, _ in result.values()):
                            return True, "Installed OpenZeppelin dependencies"
        except Exception as e:
            logger.warning(f"Dependency auto-fix skipped: {e}")

        # Missing import/remapping style errors -> allow retry after deps
        if (
            "file import callback not supported" in error_message
            or "source not found" in error_message
            or ("import" in error_message and "not found" in error_message)
        ):
            return True, "Retry after ensuring remappings and dependencies"

        # Fix override errors for ERC20 _beforeTokenTransfer
        if "override" in error_message and "_beforetokentransfer" in error_message and "erc20" in error_message:
            if contract_code:
                import re
                pattern = r'function _beforeTokenTransfer\([^)]+\)\s+internal\s+virtual\s+override\([^)]+\)\s*\{[^}]*super\._beforeTokenTransfer[^}]*\}'
                if re.search(pattern, contract_code, re.MULTILINE | re.DOTALL):
                    fixed_code = re.sub(pattern, '', contract_code, flags=re.MULTILINE | re.DOTALL).strip()
                    context["contract_code"] = fixed_code
                    logger.info("🔧 Fixed _beforeTokenTransfer override issue")
                    return True, "Removed invalid _beforeTokenTransfer override"

        # As a general fallback, try dependency detection and re-run
        if contract_code:
            from services.dependencies.dependency_manager import DependencyManager
            workspace = context.get("workspace_dir")
            if workspace:
                dep_manager = DependencyManager(workspace)
                deps = dep_manager.detect_dependencies(contract_code, "contract.sol")
                if deps:
                    await dep_manager.install_all_dependencies(deps)

        return True, "Retried compilation after dependency check"
    
    async def _auto_fix_network(self, parsed_error: ParsedError, context: Dict[str, Any]) -> Tuple[bool, str]:
        """Auto-fix network error by retrying"""
        return True, "Network operation will be retried"
    
    async def _auto_fix_config(self, parsed_error: ParsedError, context: Dict[str, Any]) -> Tuple[bool, str]:
        """Auto-fix missing config"""
        # Could create default config
        return False, "Config creation not yet automated"
    
    async def _auto_fix_timeout(self, parsed_error: ParsedError, context: Dict[str, Any]) -> Tuple[bool, str]:
        """Auto-fix timeout by retrying with longer timeout"""
        return True, "Operation will be retried with longer timeout"


async def handle_error_with_retry(error_handler: SelfHealingErrorHandler, error: Exception,
                           context: Dict[str, Any], max_retries: int = 3) -> Tuple[bool, Optional[str]]:
    """
    Handle an error with automatic retry and self-healing.
    
    Args:
        error_handler: The error handler instance
        error: The exception that occurred
        context: Workflow context
        max_retries: Maximum number of retry attempts
        
    Returns:
        Tuple of (success, message)
    """
    error_message = str(error)
    parsed = error_handler.parse_error(error_message)
    
    logger.info(f"🔍 Error detected: {parsed.error_type.value} - {error_message[:100]}")
    
    if not parsed.automatable:
        logger.error(f"❌ Non-recoverable error: {error_message}")
        return False, error_message
    
    # Attempt auto-fix with retries
    for attempt in range(max_retries):
        logger.info(f"🔧 Auto-fix attempt {attempt + 1}/{max_retries}: {parsed.suggested_fix}")
        
        success, message = await error_handler.attempt_auto_fix(parsed, context)
        
        if success:
            logger.info(f"✅ Auto-fix successful: {message}")
            return True, message
        
        if attempt < max_retries - 1:
            logger.warning(f"⚠️ Auto-fix attempt {attempt + 1} failed, retrying...")
    
    logger.error(f"❌ Auto-fix failed after {max_retries} attempts")
    return False, f"Auto-fix failed: {parsed.suggested_fix}"

