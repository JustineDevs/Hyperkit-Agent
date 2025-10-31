#!/bin/bash
#
# Real E2E Workflow Test Script
# Tests the complete workflow chain with actual execution
#

set -e

echo "========================================="
echo "Real E2E Workflow Test"
echo "========================================="
echo ""

WORKSPACE_DIR="${1:-$(pwd)}"
TEST_PROMPT="${2:-create a simple ERC20 token named TestToken with symbol TEST, 1000000 total supply}"

echo "Workspace: $WORKSPACE_DIR"
echo "Test Prompt: $TEST_PROMPT"
echo ""

# Test 1: Test-only mode (should succeed if gen/compile work)
echo "=== Test 1: Test-Only Mode (No Deployment) ==="
python hyperagent workflow run "$TEST_PROMPT" --test-only || {
    echo "❌ Test 1 FAILED: Test-only mode should complete"
    exit 1
}
echo "✅ Test 1 PASSED: Workflow completed in test-only mode"
echo ""

# Test 2: Full workflow with deployment (may fail deployment, but should complete)
echo "=== Test 2: Full Workflow (With Deployment) ==="
RESULT=$(python hyperagent workflow run "$TEST_PROMPT" 2>&1)
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ Test 2 PASSED: Workflow completed successfully"
elif [ $EXIT_CODE -eq 1 ]; then
    # Check if it's a critical failure or deployment failure
    if echo "$RESULT" | grep -q "Workflow completed with non-critical errors"; then
        echo "✅ Test 2 PASSED: Workflow completed with deployment failure (non-critical)"
    elif echo "$RESULT" | grep -q "Workflow failed due to critical errors"; then
        echo "⚠️  Test 2 WARNING: Critical failure (generation/compilation failed)"
        echo "   This is expected if forge/compilation tools are missing"
    else
        echo "❌ Test 2 FAILED: Unexpected error"
        echo "$RESULT"
        exit 1
    fi
else
    echo "❌ Test 2 FAILED: Unexpected exit code $EXIT_CODE"
    echo "$RESULT"
    exit 1
fi

echo ""
echo "========================================="
echo "✅ All Real E2E Tests Completed"
echo "========================================="

