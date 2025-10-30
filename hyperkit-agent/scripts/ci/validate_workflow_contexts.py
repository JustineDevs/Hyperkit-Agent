#!/usr/bin/env python3
"""
CI Validation Script for Workflow Contexts and Artifacts

Validates that every workflow run creates proper contexts and diagnostic bundles.
Run this in CI to ensure no silent failures or missing artifacts.
"""

import json
import sys
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class WorkflowContextValidator:
    """Validate workflow context creation and completeness"""
    
    def __init__(self, workspace_dir: Path):
        self.workspace_dir = Path(workspace_dir)
        self.contexts_dir = self.workspace_dir / ".workflow_contexts"
        self.temp_envs_dir = self.workspace_dir / ".temp_envs"
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def validate_all(self) -> Dict[str, Any]:
        """Run all validation checks"""
        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "workspace": str(self.workspace_dir),
            "checks": {},
            "errors": [],
            "warnings": [],
            "passed": False
        }
        
        # Check 1: Directories exist
        results["checks"]["directories_exist"] = self._check_directories_exist()
        
        # Check 2: Context files are valid JSON
        results["checks"]["context_files_valid"] = self._check_context_files_valid()
        
        # Check 3: Diagnostic bundles exist and are complete
        results["checks"]["diagnostic_bundles_complete"] = self._check_diagnostic_bundles()
        
        # Check 4: No empty contexts
        results["checks"]["no_empty_contexts"] = self._check_no_empty_contexts()
        
        # Check 5: Temp environments cleaned up on success
        results["checks"]["temp_envs_cleanup"] = self._check_temp_envs_cleanup()
        
        # Aggregate results
        all_passed = all(
            check.get("passed", False) 
            for check in results["checks"].values()
        )
        
        results["passed"] = all_passed
        results["errors"] = self.errors
        results["warnings"] = self.warnings
        
        return results
    
    def _check_directories_exist(self) -> Dict[str, Any]:
        """Check that required directories exist"""
        check_result = {
            "name": "directories_exist",
            "passed": False,
            "details": {}
        }
        
        # Check contexts directory
        contexts_exists = self.contexts_dir.exists()
        check_result["details"]["contexts_dir"] = {
            "exists": contexts_exists,
            "path": str(self.contexts_dir)
        }
        
        if not contexts_exists:
            self.errors.append(f"Contexts directory missing: {self.contexts_dir}")
            check_result["details"]["contexts_dir"]["error"] = "Directory does not exist"
        
        # Check temp_envs directory (may not exist if no workflows run yet)
        temp_envs_exists = self.temp_envs_dir.exists()
        check_result["details"]["temp_envs_dir"] = {
            "exists": temp_envs_exists,
            "path": str(self.temp_envs_dir)
        }
        
        if not temp_envs_exists:
            self.warnings.append(f"Temp environments directory missing: {self.temp_envs_dir} (may be normal if no workflows run)")
        
        check_result["passed"] = contexts_exists  # contexts_dir is required
        
        return check_result
    
    def _check_context_files_valid(self) -> Dict[str, Any]:
        """Check that all context files are valid JSON"""
        check_result = {
            "name": "context_files_valid",
            "passed": False,
            "details": {"valid": 0, "invalid": 0, "errors": []}
        }
        
        if not self.contexts_dir.exists():
            check_result["error"] = "Contexts directory does not exist"
            return check_result
        
        context_files = list(self.contexts_dir.glob("*.json"))
        
        for context_file in context_files:
            try:
                with open(context_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Basic validation
                required_fields = ["workflow_id", "user_prompt"]
                missing_fields = [f for f in required_fields if f not in data]
                
                if missing_fields:
                    error_msg = f"{context_file.name}: Missing required fields: {missing_fields}"
                    check_result["details"]["errors"].append(error_msg)
                    self.errors.append(error_msg)
                    check_result["details"]["invalid"] += 1
                else:
                    check_result["details"]["valid"] += 1
                    
            except json.JSONDecodeError as e:
                error_msg = f"{context_file.name}: Invalid JSON - {e}"
                check_result["details"]["errors"].append(error_msg)
                self.errors.append(error_msg)
                check_result["details"]["invalid"] += 1
            except Exception as e:
                error_msg = f"{context_file.name}: Error reading file - {e}"
                check_result["details"]["errors"].append(error_msg)
                self.errors.append(error_msg)
                check_result["details"]["invalid"] += 1
        
        check_result["passed"] = check_result["details"]["invalid"] == 0
        
        return check_result
    
    def _check_diagnostic_bundles(self) -> Dict[str, Any]:
        """Check that diagnostic bundles exist and are complete"""
        check_result = {
            "name": "diagnostic_bundles_complete",
            "passed": False,
            "details": {"complete": 0, "incomplete": 0, "missing": 0, "errors": []}
        }
        
        if not self.contexts_dir.exists():
            check_result["error"] = "Contexts directory does not exist"
            return check_result
        
        # Find all context files (non-diagnostic)
        context_files = [
            f for f in self.contexts_dir.glob("*.json")
            if not f.name.endswith("_diagnostics.json")
        ]
        
        required_bundle_fields = [
            "workflow_id",
            "user_prompt",
            "system_info",
            "tool_versions",
            "stages",
            "errors"
        ]
        
        for context_file in context_files:
            workflow_id = context_file.stem
            diagnostic_file = self.contexts_dir / f"{workflow_id}_diagnostics.json"
            
            if not diagnostic_file.exists():
                error_msg = f"Missing diagnostic bundle for workflow {workflow_id}"
                check_result["details"]["errors"].append(error_msg)
                check_result["details"]["missing"] += 1
                self.warnings.append(error_msg)
                continue
            
            try:
                with open(diagnostic_file, 'r', encoding='utf-8') as f:
                    bundle = json.load(f)
                
                missing_fields = [f for f in required_bundle_fields if f not in bundle]
                
                if missing_fields:
                    error_msg = f"{diagnostic_file.name}: Missing fields: {missing_fields}"
                    check_result["details"]["errors"].append(error_msg)
                    check_result["details"]["incomplete"] += 1
                    self.warnings.append(error_msg)
                else:
                    check_result["details"]["complete"] += 1
                    
            except Exception as e:
                error_msg = f"{diagnostic_file.name}: Error reading bundle - {e}"
                check_result["details"]["errors"].append(error_msg)
                check_result["details"]["incomplete"] += 1
                self.errors.append(error_msg)
        
        check_result["passed"] = (
            check_result["details"]["missing"] == 0 and 
            check_result["details"]["incomplete"] == 0
        )
        
        return check_result
    
    def _check_no_empty_contexts(self) -> Dict[str, Any]:
        """Check that no context files are empty or have no stage results"""
        check_result = {
            "name": "no_empty_contexts",
            "passed": False,
            "details": {"non_empty": 0, "empty": 0, "errors": []}
        }
        
        if not self.contexts_dir.exists():
            check_result["error"] = "Contexts directory does not exist"
            return check_result
        
        context_files = list(self.contexts_dir.glob("*.json"))
        context_files = [f for f in context_files if not f.name.endswith("_diagnostics.json")]
        
        for context_file in context_files:
            try:
                with open(context_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Check if file is essentially empty
                if not data or len(data) < 3:
                    error_msg = f"{context_file.name}: Context file is empty or minimal"
                    check_result["details"]["errors"].append(error_msg)
                    check_result["details"]["empty"] += 1
                    self.errors.append(error_msg)
                    continue
                
                # Check if stages exist and have content
                stages = data.get("stages", [])
                if not stages:
                    error_msg = f"{context_file.name}: No stage results recorded"
                    check_result["details"]["errors"].append(error_msg)
                    check_result["details"]["empty"] += 1
                    self.warnings.append(error_msg)
                else:
                    check_result["details"]["non_empty"] += 1
                    
            except Exception as e:
                error_msg = f"{context_file.name}: Error checking - {e}"
                check_result["details"]["errors"].append(error_msg)
                check_result["details"]["empty"] += 1
                self.errors.append(error_msg)
        
        check_result["passed"] = check_result["details"]["empty"] == 0
        
        return check_result
    
    def _check_temp_envs_cleanup(self) -> Dict[str, Any]:
        """Check that temp environments are cleaned up after successful workflows"""
        check_result = {
            "name": "temp_envs_cleanup",
            "passed": False,
            "details": {"total": 0, "preserved": 0, "cleaned": 0}
        }
        
        if not self.temp_envs_dir.exists():
            check_result["passed"] = True  # No temp dirs = no cleanup needed
            check_result["details"]["message"] = "No temp environments directory (no workflows run)"
            return check_result
        
        temp_dirs = [d for d in self.temp_envs_dir.iterdir() if d.is_dir()]
        check_result["details"]["total"] = len(temp_dirs)
        
        for temp_dir in temp_dirs:
            # Check for preserve marker
            preserve_marker = temp_dir / ".preserve_for_debug"
            if preserve_marker.exists():
                check_result["details"]["preserved"] += 1
                # This is OK - preserved for debugging
            else:
                check_result["details"]["cleaned"] += 1
        
        # If there are preserved dirs, that's OK (they're for debugging)
        # But if there are many, it might indicate cleanup isn't working
        if check_result["details"]["preserved"] > 10:
            self.warnings.append(
                f"Many preserved temp environments ({check_result['details']['preserved']}) - "
                "consider cleanup or investigating preserved dirs"
            )
        
        check_result["passed"] = True  # This is informational, not a failure
        
        return check_result


def main():
    """Main entry point"""
    # Get workspace directory (default to hyperkit-agent/)
    if len(sys.argv) > 1:
        workspace_dir = Path(sys.argv[1])
    else:
        # Default: assume script is in hyperkit-agent/scripts/ci/
        script_dir = Path(__file__).resolve().parent
        workspace_dir = script_dir.parent.parent.parent
    
    validator = WorkflowContextValidator(workspace_dir)
    results = validator.validate_all()
    
    # Print results
    print("\n" + "="*60)
    print("Workflow Context Validation Results")
    print("="*60)
    
    print(f"\nWorkspace: {results['workspace']}")
    print(f"Timestamp: {results['timestamp']}")
    
    print("\nCheck Results:")
    for check_name, check_result in results["checks"].items():
        status = "✅ PASS" if check_result.get("passed", False) else "❌ FAIL"
        print(f"  {status}: {check_name}")
        
        if "details" in check_result:
            details = check_result["details"]
            if isinstance(details, dict) and "errors" in details and details["errors"]:
                for error in details["errors"][:3]:  # Show first 3 errors
                    print(f"    - {error}")
    
    if results["errors"]:
        print("\nErrors:")
        for error in results["errors"]:
            print(f"  ❌ {error}")
    
    if results["warnings"]:
        print("\nWarnings:")
        for warning in results["warnings"]:
            print(f"  ⚠️  {warning}")
    
    print("\n" + "="*60)
    print(f"Overall Status: {'✅ PASSED' if results['passed'] else '❌ FAILED'}")
    print("="*60)
    
    # Save results to file
    results_file = workspace_dir / "test_logs" / "ci_validation_results.json"
    results_file.parent.mkdir(parents=True, exist_ok=True)
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to: {results_file}")
    
    # Exit with error code if validation failed
    sys.exit(0 if results["passed"] else 1)


if __name__ == "__main__":
    main()

