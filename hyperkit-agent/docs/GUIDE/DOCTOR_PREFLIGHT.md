# HyperKit-Agent Doctor: Production-Grade Preflight System

## Overview

The **Doctor** system implements style hardened dependency validation and self-healing patterns to ensure reliable, error-proof agent operation in any environment.

## Key Features

### 1. **Hardened & Version-Locked Dependencies**
- ✅ All core dependencies (OpenZeppelin, solc/forge, node, etc) are version-checked
- ✅ No "latest" anywhere—explicit version requirements with actionable errors
- ✅ Automated install with fallback steps

### 2. **Proactive Dependency Validation**
- ✅ Scans for all required library files at exact import paths
- ✅ Validates exact compiler version support
- ✅ Checks all tools present in env/PATH
- ✅ Auto-repair script runs if any missing

### 3. **Legacy Compatibility Layer**
- ✅ Detects OpenZeppelin version drift
- ✅ Handles Counters.sol deprecation (OZ v5)
- ✅ Transparently falls back to correct compatible repo/commit
- ✅ Template rewriting for compatibility

### 4. **Fail-Loud, Suggest-Fix Error Handling**
- ✅ Every failure tells user:
  - What failed
  - What version/dependency caused it
  - Precise copy-paste commands for auto-fix
- ✅ No silent catch-alls—root cause always surfaced

## Usage

### Standalone Script

```bash
# Run doctor before workflow
python scripts/doctor.py

# Or use bash script
bash scripts/doctor.sh

# Disable auto-fix (report only)
python scripts/doctor.py --no-fix
```

### Integration in Workflow

The doctor automatically runs as part of `_stage_preflight()` in the workflow orchestrator. You can also run it manually:

```python
from scripts.doctor import doctor
from pathlib import Path

# Run doctor with auto-fix
success = doctor(workspace_dir=Path("hyperkit-agent"), auto_fix=True)
```

## What Doctor Checks

### Step 1: Required Tools
- ✅ `forge` - Foundry compiler
- ✅ `python` - Python 3.8+
- ✅ `node` - Node.js (optional)
- ✅ `npm` - npm (optional)

### Step 2: OpenZeppelin Installation
- ✅ Checks if `lib/openzeppelin-contracts` exists
- ✅ Verifies `ERC20.sol` is present
- ✅ Detects OpenZeppelin version (v4 vs v5)
- ✅ Checks for `Counters.sol` (deprecated in v5)
- ✅ Auto-installs correct version if missing

### Step 3: Foundry Configuration
- ✅ Validates `foundry.toml` exists
- ✅ Checks `solc` version matches requirements (0.8.24)
- ✅ Auto-updates if mismatch detected

### Step 4: Git Submodule Issues
- ✅ Checks for broken `.gitmodules` entries
- ✅ Removes submodule entries from `.gitignore` (wrong location)
- ✅ Cleans `.git/config` submodule references

## Auto-Fix Capabilities

The doctor automatically fixes:
1. **Missing OpenZeppelin**: Installs via `forge install` or direct `git clone`
2. **Wrong OZ Version**: Reinstalls compatible version (v4.9.5 for Counters.sol)
3. **Solc Version Mismatch**: Updates `foundry.toml` to correct version
4. **Git Submodule Issues**: Removes broken entries from `.gitmodules` and `.gitignore`
5. **Broken Dependencies**: Cleans and reinstalls with correct versions

## Error Messages & Recovery

Every error includes:

1. **What Failed**: Clear description of the issue
2. **Why It Failed**: Root cause explanation
3. **How to Fix**: Actionable commands or steps

Example:
```
❌ OpenZeppelin contracts not found
💡 Recovery: Run: forge install OpenZeppelin/openzeppelin-contracts
   Or: bash scripts/dependency_install.sh
```

## CI/CD Integration

### GitHub Actions

```yaml
- name: Run Agent Doctor
  run: |
    cd hyperkit-agent
    python scripts/doctor.py
```

### Pre-Commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-commit

cd hyperkit-agent
python scripts/doctor.py --no-fix
if [ $? -ne 0 ]; then
  echo "❌ Doctor preflight failed. Please fix issues before committing."
  exit 1
fi
```

## Comparison: Typical Agent

| Feature | HyperKit-Agent Doctor | Typical Agent |
|---------|----------------------|---------------|
| Dependency Pinning | ✅ Always, version-locked | ❌ Often dynamic |
| Preflight/Doctor | ✅ Fail-fast, actionable | ❌ Usually missing |
| Legacy Compatibility | ✅ Auto-detection & fallback | ❌ Manual patching |
| Error Handling | ✅ Fail-loud, suggest-fix | ❌ Masks/loops errors |
| Install Automation | ✅ Robust & repeatable | ❌ Semi-manual |
| CI Coverage | ✅ Full workflow tests | ❌ Spotty |

## Best Practices

1. **Run Doctor Before Every Workflow**
   - Automatically runs in `_stage_preflight()`
   - Can run manually for validation

2. **Version Lock Everything**
   - Pin OpenZeppelin versions in dependency manifest
   - Pin Solidity compiler version in `foundry.toml`
   - Document expected tool versions

3. **Fail Early, Fix Loudly**
   - Never mask errors
   - Always provide actionable fixes
   - Auto-fix when possible, report when manual

4. **Test in CI**
   - Run doctor in CI pipeline
   - Validate all dependency checks
   - Ensure auto-fix works correctly

## Troubleshooting

### Issue: Doctor reports missing tools

**Solution:**
```bash
# Install Foundry
curl -L https://foundry.paradigm.xyz | bash
foundryup

# Install Python
# Download from: https://www.python.org/downloads/

# Install Node.js
# Download from: https://nodejs.org/
```

### Issue: OpenZeppelin installation fails

**Solution:**
```bash
# Clean and reinstall
rm -rf lib/openzeppelin-contracts
forge install OpenZeppelin/openzeppelin-contracts

# Or use direct clone
git clone https://github.com/OpenZeppelin/openzeppelin-contracts.git lib/openzeppelin-contracts
```

### Issue: Counters.sol not found

**Solution:**
- This is **expected** in OpenZeppelin v5 (Counters.sol is deprecated)
- Doctor will auto-remove Counters.sol usage in generated contracts
- Or install OZ v4.9.5: `forge install OpenZeppelin/openzeppelin-contracts@v4.9.5`

## Related Files

- `scripts/doctor.py` - Python doctor implementation
- `scripts/doctor.sh` - Bash doctor script
- `scripts/dependency_install.sh` - Dependency installer
- `services/dependencies/dependency_manager.py` - Dependency manager with auto-fix
- `core/workflow/workflow_orchestrator.py` - Workflow with integrated doctor

## Summary

The Doctor system ensures **zero-excuse, production-grade onboarding** by:
- ✅ Validating all dependencies before workflow execution
- ✅ Auto-fixing common issues (OZ installation, version mismatches)
- ✅ Providing actionable error messages when manual fixes are needed
- ✅ Enforcing version consistency across all tools and libraries