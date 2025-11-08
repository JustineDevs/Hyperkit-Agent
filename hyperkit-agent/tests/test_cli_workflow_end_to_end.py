#!/usr/bin/env python3
"""
Brutal End-to-End CLI Workflow Test
Tests every command and subcommand in the HyperAgent CLI for correctness,
error handling, recursion issues, and proper execution flow.

This is a non-negotiable pre-release test that must pass before any deployment.
"""

import subprocess
import sys
import os
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime

# Set up paths
TEST_DIR = Path(__file__).parent
PROJECT_ROOT = TEST_DIR.parent
HYPERAGENT_CMD = "hyperagent"

# Test results storage
TEST_RESULTS: List[Dict] = []

# Error patterns to detect
ERROR_PATTERNS = [
    r"Traceback \(most recent call last\)",
    r"File \".*\", line \d+",
    r"Exception:",
    r"Error:",
    r"maximum recursion depth exceeded",
    r"RecursionError",
    r"Sentinel\.UNSET",
    r"Context not found for workflow: Sentinel",
    r"AttributeError",
    r"TypeError",
    r"ValueError",
    r"KeyError",
    r"ImportError",
    r"ModuleNotFoundError",
]


def detect_errors(output: str, stderr: str) -> List[str]:
    """
    Detect errors, tracebacks, and exceptions in output.
    
    Returns:
        List of detected error patterns
    """
    detected = []
    combined = f"{output}\n{stderr}"
    
    for pattern in ERROR_PATTERNS:
        if re.search(pattern, combined, re.IGNORECASE | re.MULTILINE):
            detected.append(pattern)
    
    return detected


def run_cli_command(
    args: List[str],
    cwd: Optional[Path] = None,
    env: Optional[Dict] = None,
    description: str = "",
    expect_error: bool = False,
    timeout: int = 60
) -> Tuple[bool, str, str, int, List[str]]:
    """
    Run CLI command and capture all output, errors, and return codes.
    
    Args:
        args: Command arguments (e.g., ["workflow", "list"])
        cwd: Working directory (default: project root)
        env: Environment variables
        description: Test description
        expect_error: Whether error is expected
        timeout: Command timeout in seconds
        
    Returns:
        Tuple of (success, stdout, stderr, returncode, detected_errors)
    """
    if cwd is None:
        cwd = PROJECT_ROOT
    
    # Build command
    command = [HYPERAGENT_CMD] + args
    
    # Prepare environment
    test_env = os.environ.copy()
    if env:
        test_env.update(env)
    
    # Disable interactive prompts for testing
    test_env["HYPERAGENT_NON_INTERACTIVE"] = "1"
    test_env["NO_COLOR"] = "1"  # Disable colors for cleaner output
    
    description = description or " ".join(args)
    
    print(f"\n{'='*80}")
    print(f"TEST: {description}")
    print(f"Command: {' '.join(command)}")
    print(f"{'='*80}")
    
    try:
        proc = subprocess.Popen(
            command,
            cwd=str(cwd),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            env=test_env,
            encoding='utf-8',
            errors='replace'
        )
        
        try:
            stdout, stderr = proc.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            proc.kill()
            stdout, stderr = proc.communicate()
            stderr += "\n[ERROR] Command timed out after {} seconds".format(timeout)
        
        returncode = proc.returncode
        
        # Detect errors in output
        detected_errors = detect_errors(stdout, stderr)
        
        # Determine success
        # Command succeeds if:
        # 1. Return code is 0 (or error was expected)
        # 2. No tracebacks or critical errors detected
        # 3. No recursion errors
        has_critical_errors = any(
            "recursion" in err.lower() or 
            "traceback" in err.lower() or
            "sentinel.unset" in err.lower()
            for err in detected_errors
        )
        
        if expect_error:
            success = returncode != 0 and not has_critical_errors
        else:
            success = returncode == 0 and not has_critical_errors
        
        # Store results
        result = {
            "description": description,
            "command": " ".join(command),
            "success": success,
            "stdout": stdout.strip(),
            "stderr": stderr.strip(),
            "returncode": returncode,
            "detected_errors": detected_errors,
            "has_critical_errors": has_critical_errors,
            "timestamp": datetime.now().isoformat()
        }
        
        TEST_RESULTS.append(result)
        
        # Print summary
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} | Return Code: {returncode}")
        if detected_errors:
            print(f"⚠️  Detected Errors: {', '.join(detected_errors)}")
        if stdout.strip():
            print(f"\nSTDOUT ({len(stdout)} chars):")
            print(stdout[:500] + ("..." if len(stdout) > 500 else ""))
        if stderr.strip():
            print(f"\nSTDERR ({len(stderr)} chars):")
            print(stderr[:500] + ("..." if len(stderr) > 500 else ""))
        
        return success, stdout, stderr, returncode, detected_errors
        
    except Exception as e:
        error_msg = f"Exception running command: {e}"
        print(f"❌ FAIL | {error_msg}")
        result = {
            "description": description,
            "command": " ".join(command),
            "success": False,
            "stdout": "",
            "stderr": error_msg,
            "returncode": -1,
            "detected_errors": [f"TestException: {type(e).__name__}"],
            "has_critical_errors": True,
            "timestamp": datetime.now().isoformat()
        }
        TEST_RESULTS.append(result)
        return False, "", error_msg, -1, [f"TestException: {type(e).__name__}"]


def test_workflow_commands():
    """Test all workflow command group subcommands."""
    print("\n" + "="*80)
    print("WORKFLOW COMMAND GROUP TESTS")
    print("="*80)
    
    # Workflow list - should show RAG templates
    run_cli_command(
        ["workflow", "list"],
        description="Workflow > List RAG Templates"
    )
    
    # Workflow status - should show status or fail gracefully
    run_cli_command(
        ["workflow", "status"],
        description="Workflow > Status (latest)"
    )
    
    # Workflow inspect - should show latest or fail gracefully
    run_cli_command(
        ["workflow", "inspect"],
        description="Workflow > Inspect (latest)"
    )
    
    # Workflow run - test with minimal prompt (may fail if no network/config)
    run_cli_command(
        ["workflow", "run", "Create a test ERC20 token", "--test-only", "--no-audit"],
        description="Workflow > Run (test-only, minimal)",
        timeout=120  # Workflow can take longer
    )


def test_generate_commands():
    """Test all generate command group subcommands."""
    print("\n" + "="*80)
    print("GENERATE COMMAND GROUP TESTS")
    print("="*80)
    
    # Generate templates - should list available templates
    run_cli_command(
        ["generate", "templates"],
        description="Generate > Templates List"
    )
    
    # Generate contract - test with simple prompt
    run_cli_command(
        ["generate", "contract", "Create a simple ERC20 token"],
        description="Generate > Contract (simple prompt)",
        timeout=90
    )


def test_deploy_commands():
    """Test all deploy command group subcommands."""
    print("\n" + "="*80)
    print("DEPLOY COMMAND GROUP TESTS")
    print("="*80)
    
    # Deploy status
    run_cli_command(
        ["deploy", "status"],
        description="Deploy > Status"
    )
    
    # Deploy list
    run_cli_command(
        ["deploy", "list"],
        description="Deploy > List"
    )


def test_audit_commands():
    """Test all audit command group subcommands."""
    print("\n" + "="*80)
    print("AUDIT COMMAND GROUP TESTS")
    print("="*80)
    
    # Audit contract - test with example file if exists
    example_contract = PROJECT_ROOT / "examples" / "SimpleToken.sol"
    if example_contract.exists():
        run_cli_command(
            ["audit", "contract", "--contract", str(example_contract)],
            description="Audit > Contract (example file)",
            timeout=120
        )
    else:
        print(f"⚠️  Skipping audit contract test - example file not found: {example_contract}")
    
    # Audit batch - test with examples directory if exists
    examples_dir = PROJECT_ROOT / "examples" / "contracts"
    if examples_dir.exists():
        run_cli_command(
            ["audit", "batch", "--directory", str(examples_dir)],
            description="Audit > Batch (examples directory)",
            timeout=180
        )
    else:
        print(f"⚠️  Skipping audit batch test - examples directory not found: {examples_dir}")


def test_batch_audit_commands():
    """Test batch-audit command group."""
    print("\n" + "="*80)
    print("BATCH-AUDIT COMMAND GROUP TESTS")
    print("="*80)
    
    examples_dir = PROJECT_ROOT / "examples" / "contracts"
    if examples_dir.exists():
        run_cli_command(
            ["batch-audit", "contracts", "--directory", str(examples_dir)],
            description="Batch-Audit > Contracts (examples directory)",
            timeout=180
        )
    else:
        print(f"⚠️  Skipping batch-audit test - examples directory not found: {examples_dir}")


def test_verify_commands():
    """Test all verify command group subcommands."""
    print("\n" + "="*80)
    print("VERIFY COMMAND GROUP TESTS")
    print("="*80)
    
    # Verify status
    run_cli_command(
        ["verify", "status"],
        description="Verify > Status"
    )
    
    # Verify list
    run_cli_command(
        ["verify", "list"],
        description="Verify > List"
    )


def test_config_commands():
    """Test all config command group subcommands."""
    print("\n" + "="*80)
    print("CONFIG COMMAND GROUP TESTS")
    print("="*80)
    
    # Config list
    run_cli_command(
        ["config", "list"],
        description="Config > List"
    )
    
    # Config show
    run_cli_command(
        ["config", "show"],
        description="Config > Show"
    )


def test_monitor_commands():
    """Test all monitor command group subcommands."""
    print("\n" + "="*80)
    print("MONITOR COMMAND GROUP TESTS")
    print("="*80)
    
    # Monitor health
    run_cli_command(
        ["monitor", "health"],
        description="Monitor > Health"
    )
    
    # Monitor status
    run_cli_command(
        ["monitor", "status"],
        description="Monitor > Status"
    )


def test_docs_commands():
    """Test all docs command group subcommands."""
    print("\n" + "="*80)
    print("DOCS COMMAND GROUP TESTS")
    print("="*80)
    
    # Docs info
    run_cli_command(
        ["docs", "info"],
        description="Docs > Info"
    )


def test_utility_commands():
    """Test all utility commands (not in groups)."""
    print("\n" + "="*80)
    print("UTILITY COMMANDS TESTS")
    print("="*80)
    
    # Status
    run_cli_command(
        ["status"],
        description="Status Check"
    )
    
    # Version
    run_cli_command(
        ["version"],
        description="Version Info"
    )
    
    # Doctor
    run_cli_command(
        ["doctor"],
        description="Doctor Preflight",
        timeout=90
    )
    
    # Test RAG
    run_cli_command(
        ["test-rag"],
        description="Test RAG Connections"
    )
    
    # Limitations
    run_cli_command(
        ["limitations"],
        description="Limitations Info"
    )
    
    # Context (without workflow-id - should list)
    run_cli_command(
        ["context"],
        description="Context > List (no workflow-id)"
    )
    
    # Context (with invalid workflow-id - should fail gracefully)
    run_cli_command(
        ["context", "--workflow-id", "nonexistent-workflow-12345"],
        description="Context > Invalid workflow-id (should fail gracefully)",
        expect_error=True
    )


def test_error_handling():
    """Test error handling and edge cases."""
    print("\n" + "="*80)
    print("ERROR HANDLING & EDGE CASE TESTS")
    print("="*80)
    
    # Invalid command - should show suggestion
    run_cli_command(
        ["invalid-command-that-does-not-exist"],
        description="Invalid Command (should show suggestion)",
        expect_error=True
    )
    
    # Missing required arguments
    run_cli_command(
        ["workflow", "run"],
        description="Workflow Run (missing prompt - should fail gracefully)",
        expect_error=True
    )
    
    # Help command
    run_cli_command(
        ["--help"],
        description="Help Command"
    )


def print_summary():
    """Print comprehensive test summary."""
    print("\n" + "="*80)
    print("CLI WORKFLOW & SUBCOMMAND END-TO-END TEST RESULTS")
    print("="*80)
    print(f"Test Run: {datetime.now().isoformat()}")
    print(f"Total Tests: {len(TEST_RESULTS)}")
    
    # Categorize results
    passed = [t for t in TEST_RESULTS if t["success"]]
    failed = [t for t in TEST_RESULTS if not t["success"]]
    critical_failures = [t for t in TEST_RESULTS if t.get("has_critical_errors", False)]
    
    print(f"\n✅ PASSED: {len(passed)}")
    print(f"❌ FAILED: {len(failed)}")
    print(f"🚨 CRITICAL FAILURES: {len(critical_failures)}")
    
    # Show failed tests
    if failed:
        print("\n" + "="*80)
        print("FAILED TESTS:")
        print("="*80)
        for i, test in enumerate(failed, 1):
            print(f"\n{i}. {test['description']}")
            print(f"   Command: {test['command']}")
            print(f"   Return Code: {test['returncode']}")
            if test.get('detected_errors'):
                print(f"   Detected Errors: {', '.join(test['detected_errors'])}")
            if test['stderr']:
                print(f"   STDERR: {test['stderr'][:200]}...")
    
    # Show critical failures
    if critical_failures:
        print("\n" + "="*80)
        print("🚨 CRITICAL FAILURES (Recursion, Tracebacks, Sentinel Errors):")
        print("="*80)
        for i, test in enumerate(critical_failures, 1):
            print(f"\n{i}. {test['description']}")
            print(f"   Command: {test['command']}")
            print(f"   Return Code: {test['returncode']}")
            print(f"   Detected Errors: {', '.join(test.get('detected_errors', []))}")
            if test['stderr']:
                print(f"   STDERR:\n{test['stderr'][:500]}")
            if test['stdout']:
                # Show relevant parts of stdout
                lines = test['stdout'].split('\n')
                error_lines = [l for l in lines if any(p in l.lower() for p in ['error', 'traceback', 'exception', 'recursion'])]
                if error_lines:
                    print(f"   Relevant STDOUT:\n" + "\n".join(error_lines[:10]))
    
    # Summary statistics
    print("\n" + "="*80)
    print("SUMMARY STATISTICS")
    print("="*80)
    
    error_types = {}
    for test in TEST_RESULTS:
        for error in test.get('detected_errors', []):
            error_types[error] = error_types.get(error, 0) + 1
    
    if error_types:
        print("\nError Type Frequency:")
        for error_type, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True):
            print(f"  {error_type}: {count}")
    
    # Final verdict
    print("\n" + "="*80)
    if len(critical_failures) > 0:
        print("🚨 VERDICT: CRITICAL FAILURES DETECTED - DO NOT DEPLOY")
        print("="*80)
        return False
    elif len(failed) > 0:
        print("⚠️  VERDICT: SOME TESTS FAILED - REVIEW BEFORE DEPLOYMENT")
        print("="*80)
        return False
    else:
        print("✅ VERDICT: ALL TESTS PASSED - READY FOR DEPLOYMENT")
        print("="*80)
        return True


def main():
    """Run all tests."""
    print("="*80)
    print("BRUTAL END-TO-END CLI WORKFLOW TEST SUITE")
    print("="*80)
    print(f"Project Root: {PROJECT_ROOT}")
    print(f"Test Directory: {TEST_DIR}")
    print(f"HyperAgent Command: {HYPERAGENT_CMD}")
    print("="*80)
    
    # Check if hyperagent command is available
    try:
        result = subprocess.run(
            [HYPERAGENT_CMD, "--version"],
            capture_output=True,
            timeout=10
        )
        if result.returncode != 0:
            print(f"⚠️  Warning: '{HYPERAGENT_CMD}' command may not be available")
    except FileNotFoundError:
        print(f"❌ ERROR: '{HYPERAGENT_CMD}' command not found in PATH")
        print("   Make sure HyperAgent is installed: pip install -e .")
        sys.exit(1)
    
    # Run all test suites
    try:
        test_utility_commands()
        test_workflow_commands()
        test_generate_commands()
        test_deploy_commands()
        test_audit_commands()
        test_batch_audit_commands()
        test_verify_commands()
        test_config_commands()
        test_monitor_commands()
        test_docs_commands()
        test_error_handling()
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ Fatal error running tests: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Print summary and exit
    all_passed = print_summary()
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()

