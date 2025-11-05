<!-- AUDIT_BADGE_START -->
**Implementation Status**: ✅ Verified  
**Version**: 1.5.14  
**Last Verified**: 2025-10-28  
**Commit**: `d5465090`  
**Branch**: `main`  
<!-- AUDIT_BADGE_END -->

# HyperKit Agent Troubleshooting Guide

**Last Updated**: 2025-10-28  
**Version**: 1.0  

---

## Table of Contents

1. [Quick Diagnostics](#quick-diagnostics)
2. [Common Issues & Solutions](#common-issues--solutions)
3. [Error Code Reference](#error-code-reference)
4. [Dependency Issues](#dependency-issues)
5. [Deployment Errors](#deployment-errors)
6. [Audit Failures](#audit-failures)
7. [Template Generation Issues](#template-generation-issues)
8. [Performance Problems](#performance-problems)
9. [Getting Help](#getting-help)

---

## Quick Diagnostics

Run these commands to quickly diagnose issues:

```bash
# Check Python version (requires 3.10+)
python --version

# Verify installation
cd hyperkit-agent
pip list | grep -E "web3|openai|anthropic|alith"

# Run diagnostic script
hyperagent diagnose

# Check CI/CD status
git status
git log --oneline -5
```

### System Requirements Checklist

- [ ] Python 3.10, 3.11, or 3.12
- [ ] Git installed
- [ ] pip updated (`pip install --upgrade pip`)
- [ ] Virtual environment activated (recommended)
- [ ] Environment variables set (see `env.example`)

---

## Common Issues & Solutions

### 1. Installation Fails

**Symptom**: `pip install -r requirements.txt` fails

**Common Causes**:
- Python version incompatibility
- Missing system dependencies
- Network issues

**Solutions**:

```bash
# Check Python version
python --version  # Must be 3.10+

# Upgrade pip
python -m pip install --upgrade pip setuptools wheel

# Install with verbose output
pip install -r requirements.txt -v

# Try without cache
pip install -r requirements.txt --no-cache-dir
```

**Screenshot Location**: `docs/images/installation_error.png` (TODO: Add screenshot showing typical pip error)

---

### 2. ModuleNotFoundError

**Symptom**: `ModuleNotFoundError: No module named 'web3'` (or other module)

**Cause**: Dependencies not installed or wrong Python environment

**Solution**:

```bash
# Verify you're in correct directory
pwd  # Should end in /hyperkit-agent

# Activate virtual environment (if using one)
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate      # Windows

# Reinstall dependencies
pip install -r requirements.txt

# Verify installation
python -c "import web3; print(web3.__version__)"
```

---

### 3. Deployment Constructor/ABI Mismatch

**Symptom**: `Constructor validation failed: Expected 3 arguments, got 2`

**Cause**: Missing or incorrect constructor arguments

**Solutions**:

```bash
# Option 1: Let system auto-detect (may fail for complex contracts)
hyperagent deploy contract MyToken.sol

# Option 2: Provide arguments explicitly
hyperagent deploy contract MyToken.sol --args '["0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb", 1000000, "MyToken"]'

# Option 3: Use JSON file (recommended for complex args)
cat > args.json << EOF
{
  "owner": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
  "supply": 1000000,
  "name": "MyToken"
}
EOF

hyperagent deploy contract MyToken.sol --file args.json
```

**Error Message Example**:
```
❌ Constructor validation failed: Expected 3 arguments, got 2

Expected: address owner, uint256 supply, string name
Provided: ["0x123...", 1000]

Suggestions:
- The constructor expects 3 arguments but 2 were provided
- Check the contract constructor signature
- Ensure all required parameters are provided

Examples:
CLI: hyperagent deploy contract MyToken.sol --args '["0x742d...", 1000000, "My Token"]'
```

**Screenshot Location**: `docs/images/constructor_error.png` (TODO: Add screenshot)

---

### 4. Foundry Not Found

**Symptom**: `Foundry is required for deployment but is not installed`

**Cause**: Foundry (forge) not installed on system

**Solution**:

```bash
# Install Foundry
curl -L https://foundry.paradigm.xyz | bash
foundryup

# Verify installation
forge --version

# Alternative: Use Foundry Docker image
docker pull ghcr.io/foundry-rs/foundry:latest
```

**Video Tutorial**: "Installing Foundry for HyperKit" (TODO: Create 3-minute video)

---

### 5. Batch Audit Fails

**Symptom**: Batch audit stops after first error

**Cause**: Old version or incorrect command

**Solution**:

```bash
# Use new batch audit system (P2 implementation)
hyperagent batch-audit directory contracts/ --format html --format pdf

# Individual contract failures won't stop batch
# Check output for:
#   Total contracts: 10
#   Successful: 8
#   Failed: 2
```

**Screenshot Location**: `docs/images/batch_audit_success.png` (TODO: Add screenshot)

---

### 6. Template Generation Fails

**Symptom**: `Missing required variables: token_name, token_symbol`

**Cause**: Required template variables not provided

**Solution**:

```bash
# List available templates
hyperagent template list

# Show required variables
hyperagent template show ERC20

# Generate with all required variables
hyperagent template generate ERC20 MyToken.sol \
  -v token_name=MyToken \
  -v token_symbol=MTK \
  -v initial_supply=1000000 \
  -v decimals=18 \
  -v mintable=true \
  -v burnable=false \
  -v pausable=false
```

---

### 7. CI/CD Pipeline Fails

**Symptom**: GitHub Actions shows red X

**Common Causes & Solutions**:

#### a) Mock Mode Detected
```
❌ MOCK_MODE detected in production code!
```
**Fix**: Remove `MOCK_MODE = True` from non-test files

#### b) Dependency Installation Fails
```
ERROR: No matching distribution found for packagename
```
**Fix**: Check `requirements.txt` for typos or version conflicts

#### c) Syntax Errors
```
F821 undefined name 'variable_name'
```
**Fix**: Run `flake8` locally and fix errors before pushing

#### d) Test Failures
```
FAILED tests/test_something.py::test_function
```
**Fix**: Run tests locally: `pytest tests/ -v`

**Screenshot Location**: `docs/images/cicd_failure.png` (TODO: Add screenshots for each type)

---

### 8. Performance Issues

**Symptom**: Slow contract generation or audit

**Optimization Steps**:

```bash
# Clear cache
rm -rf hyperkit-agent/cache/*
rm -rf hyperkit-agent/__pycache__/*

# Update to latest version
git pull origin main
pip install -r requirements.txt --upgrade

# Use faster export formats
hyperagent batch-audit directory contracts/ --format json  # Fastest

# Disable optional features
hyperagent audit contract.sol --no-mythril  # Skip Mythril (slow)
```

---

## Error Code Reference

| Code | Meaning | Solution |
|------|---------|----------|
| E001 | Dependency missing | Run `pip install -r requirements.txt` |
| E002 | Foundry not found | Install Foundry: `curl -L https://foundry.paradigm.xyz \| bash` |
| E003 | Invalid contract syntax | Check Solidity syntax |
| E004 | Network unreachable | Check RPC URL and internet connection |
| E005 | Insufficient funds | Fund deployer address |
| E006 | Constructor validation failed | Provide correct arguments |
| E007 | Template not found | Run `hyperagent template list` |
| E008 | Mock mode detected | Remove MOCK_MODE from production code |

---

## Dependency Issues

### ipfshttpclient Not Available

**Symptom**: IPFS features disabled

**Impact**: Cannot upload/fetch vector stores from IPFS

**Solution**: IPFS is optional. System works without it.

```bash
# Try to install (may fail on some Python versions)
pip install -r requirements.txt

# Alternative: Use Pinata API (no package needed)
export PINATA_API_KEY=your_key
export PINATA_SECRET_KEY=your_secret
```

### Alith SDK Issues

**Symptom**: Cannot import Alith Agent

**Solution**:

```bash
# Upgrade Alith
pip install --upgrade alith

# Verify version
python -c "import alith; print(alith.__version__)"
```

---

## Getting Help

### 1. Check Existing Documentation
- README.md - Project overview
- docs/ - Comprehensive guides
- hyperkit-agent/REPORTS/ - Status reports

### 2. Search Issues
https://github.com/YOUR_REPO/issues

### 3. Create New Issue
Include:
- Error message (full output)
- Python version (`python --version`)
- OS information
- Steps to reproduce
- Expected vs actual behavior

### 4. Community Support
- Discord: [Link]
- Telegram: [Link]
- Email: support@hyperkit.ai

---

## Preventive Measures

### Before Deployment
```bash
# Run full test suite
pytest tests/ -v

# Check code quality
flake8 core/ services/

# Verify dependencies
pip check

# Test on testnet first
hyperagent deploy contract.sol --network hyperion-testnet
```

### Regular Maintenance
```bash
# Update dependencies monthly
pip install -r requirements.txt --upgrade

# Clear old logs
find logs/ -name "*.log" -mtime +30 -delete

# Update Foundry
foundryup
```

---

## Video Tutorial Index

**TODO**: Create and link video tutorials for:

1. **Installation & Setup** (5 min)
   - Installing Python 3.10+
   - Setting up virtual environment
   - Installing dependencies
   - Configuring environment variables

2. **First Deployment** (3 min)
   - Creating a simple contract
   - Deploying to testnet
   - Verifying deployment
   - Troubleshooting common errors

3. **Using Templates** (4 min)
   - Browsing template library
   - Generating ERC20 token
   - Customizing variables
   - Deploying generated contract

4. **Batch Auditing** (5 min)
   - Running batch audit
   - Interpreting results
   - Exporting reports
   - Acting on findings

5. **CI/CD Setup** (6 min)
   - GitHub Actions configuration
   - Understanding checks
   - Fixing common failures
   - Deployment workflows

---

**Status**: ✅ Comprehensive troubleshooting guide complete  
**Next**: Add screenshots and video tutorials (in progress)  
**Maintainer**: Development Team

