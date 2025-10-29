# Contributor Guide - Fixing Known Bugs

**Date**: 2025-01-29  
**Purpose**: Guide for contributors fixing the critical bugs identified in the CTO audit

---

## P0 Bugs (Fix First)

### 1. Deploy Command Constructor Bug

**Location**: `services/deployment/foundry_deployer.py` (line ~298)

**Issue**: Constructor arguments generated from ABI may not match the actual contract constructor signature, causing deployment failures.

**Symptoms**:
- Deployment fails with "constructor arguments mismatch" error
- ABI shows different types than what's actually in contract code
- Auto-generated args don't match manual args

**Root Cause**:
The `foundry_deployer.py` generates constructor arguments from ABI (lines 243-295), but:
1. ABI might be generated incorrectly by Foundry
2. Type conversion between ABI types and actual Solidity types
3. Array/tuple handling may not match contract expectations

**Fix Strategy**:
1. Validate generated args against contract source code (not just ABI)
2. Use `ConstructorArgumentParser` to extract from source code as fallback
3. Better error messages showing expected vs actual args
4. Log both ABI and source-code-extracted params for comparison

**Files to Modify**:
- `services/deployment/foundry_deployer.py` (constructor arg generation)
- `services/deployment/constructor_parser.py` (source code parsing)
- `services/deployment/deployer.py` (validation layer)

---

### 2. Workflow Silent Failure Bug

**Location**: `cli/commands/workflow.py` (line ~155-162) + `core/agent/main.py` (line ~867)

**Issue**: Workflow may show success even when deployment fails silently.

**Symptoms**:
- Workflow returns `status: "success"` but deployment actually failed
- No error message shown to user
- Deployment stage appears to pass

**Root Cause**:
Looking at `main.py` line 867-881, the workflow DOES check for deployment failure. But:
1. The deploy_contract may return wrong status
2. Error handling may swallow exceptions
3. Result dict may not be properly checked

**Fix Strategy**:
1. Ensure `deploy_contract` always returns proper status dict
2. Add explicit validation that deployment succeeded before marking workflow success
3. Improve error propagation from deployer → agent → workflow CLI
4. Add logging at each stage to trace failures

**Files to Modify**:
- `core/agent/main.py` (run_workflow method, deploy_contract return handling)
- `cli/commands/workflow.py` (_display_success_results method)
- `services/deployment/deployer.py` (ensure proper error return format)

---

## Testing Fixes

### Test Deploy Fix

```bash
# Create a simple ERC20 contract
echo "contract TestToken { constructor(string memory name, string memory symbol, uint256 initialSupply) {} }" > test.sol

# Try to deploy (should work after fix)
python -m cli.main deploy contract test.sol

# Should not fail with constructor mismatch
```

### Test Workflow Fix

```bash
# Run workflow (should fail loudly if deployment fails)
python -m cli.main workflow run "create ERC20 token"

# Check that error is shown and workflow exits with code 1
```

---

## Debugging Tips

### Enable Verbose Logging

```bash
python -m cli.main --verbose deploy contract MyToken.sol
```

### Check Deployment Result Structure

Add logging in `core/agent/main.py` after line 626:
```python
logger.debug(f"Deployer result: {result}")
logger.debug(f"Success: {result.get('success')}")
logger.debug(f"Error: {result.get('error')}")
```

### Compare ABI vs Source Code Constructor

In `foundry_deployer.py`, log both:
- ABI constructor params (from artifact)
- Source code constructor params (from ConstructorArgumentParser)

---

## Success Criteria

After fixes:
1. ✅ Deployment with auto-generated args works for simple contracts
2. ✅ Deployment failures show clear error messages (not silent)
3. ✅ Workflow fails loudly when deployment fails
4. ✅ Constructor arg validation catches mismatches before deployment attempt
5. ✅ Tests pass for both success and failure cases

---

**Priority**: Fix P0 bugs before claiming "Production Ready" again.

