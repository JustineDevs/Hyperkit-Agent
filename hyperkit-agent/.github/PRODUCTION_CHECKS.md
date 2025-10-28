# Production CI/CD Checks

## Hard Failures Enforced

### 1. Dependency Validation
- All core dependencies must install successfully
- Critical SDKs must be importable (Web3, Alith, AI providers)
- **NO continue-on-error** for production dependencies

### 2. Mock Mode Detection
- Scans codebase for `MOCK_MODE = True` in production code
- **Fails CI** if mock mode detected outside tests
- Ensures production deployments use real services

### 3. Syntax Errors
- Flake8 checks for critical syntax errors (E9, F63, F7, F82)
- **Fails CI** on any syntax errors
- Prevents broken code from reaching production

### 4. Test Coverage
- Pytest must pass all tests
- No tolerance for test failures in main branch
- **Fails CI** if any test fails

### 5. Security Checks
- Bandit security scanner runs on all code
- Safety checks for vulnerable dependencies
- Reports generated for review

## What Changed (P4 Implementation)

### Before
- Optional dependencies failed silently
- Mock mode not detected
- Linting issues only warned
- Tests could be skipped

### After
- **Hard fail** on missing core dependencies
- **Hard fail** on mock mode in production
- **Hard fail** on syntax errors
- **Hard fail** on test failures
- Security scans always run

## How to Test Locally

```bash
# Run all checks locally before pushing
cd hyperkit-agent

# Install dependencies (must succeed)
pip install -r requirements.txt

# Validate production code
grep -r "MOCK_MODE.*=.*True" . --include="*.py" | grep -v test
# Should return nothing

# Run tests (must pass)
pytest tests/ -v

# Check syntax (must pass)
flake8 core/ services/ --count --select=E9,F63,F7,F82

# Security scan
bandit -r core/ services/
```

## Emergency Override

If CI/CD is blocking a critical hotfix due to these checks:

1. **DO NOT** disable the checks
2. **FIX** the underlying issue
3. If absolutely necessary, create a separate hotfix branch with minimal changes
4. Get explicit approval from lead developer

## Monitoring

All CI/CD runs are logged and can be reviewed at:
- GitHub Actions: https://github.com/YOUR_REPO/actions
- Codecov: For test coverage trends
- Security reports: In artifacts for each run

---

**Last Updated**: 2025-10-28  
**Status**: ✅ Production Ready  
**Owner**: DevOps Team

