<!-- AUDIT_BADGE_START -->
**Implementation Status**: ✅ Verified  
**Version**: 1.4.6  
**Last Verified**: 2025-10-28  
**Commit**: `6f63afe4`  
**Branch**: `main`  
<!-- AUDIT_BADGE_END -->

# Production Mode Documentation

## Overview

HyperAgent operates in two distinct modes: **Production Mode** and **Safe Mode**. This document explains the differences, requirements, and how to ensure your system is running in the correct mode.

## 🔄 Mode Comparison

| Feature | 🟢 Production Mode | 🔴 Safe Mode |
|---------|-------------------|--------------|
| **Contract Generation** | Real AI-powered generation | Blocked with clear error |
| **Contract Auditing** | Real security analysis | Blocked with clear error |
| **Contract Deployment** | Actual blockchain deployment | Blocked with clear error |
| **Contract Verification** | Real explorer verification | Blocked with clear error |
| **Error Handling** | Clear, actionable error messages | Clear, actionable error messages |
| **Mock Fallbacks** | None - fails loud | None - fails loud |

## 🟢 Production Mode Requirements

### Critical Dependencies

All of the following must be available and functional:

#### 1. **Alith SDK**
```bash
pip install alith>=0.12.0
```
- **Purpose**: Real AI agent for contract generation and auditing
- **Test**: Must have `Agent` and `Web3Tools` classes
- **Failure**: System will not generate or audit contracts

#### 2. **Foundry**
```bash
curl -L https://foundry.paradigm.xyz | bash
foundryup
```
- **Purpose**: Smart contract compilation and deployment
- **Test**: `forge --version` must work
- **Failure**: System will not deploy contracts

#### 3. **Web3 Connection**
```bash
export HYPERION_RPC_URL="https://hyperion-testnet.metisdevops.link"
```
- **Purpose**: Blockchain connectivity
- **Test**: Must connect to Hyperion testnet
- **Failure**: System will not interact with blockchain

#### 4. **AI Providers**
At least one of the following must be configured:
```bash
export OPENAI_API_KEY="your_openai_key"
export GOOGLE_API_KEY="your_google_key"
export ANTHROPIC_API_KEY="your_anthropic_key"
```
- **Purpose**: AI-powered contract generation
- **Test**: Must have valid API key
- **Failure**: System will not generate contracts

#### 5. **Private Key**
```bash
export DEFAULT_PRIVATE_KEY="your_private_key"
```
- **Purpose**: Transaction signing and deployment
- **Test**: Must be valid Ethereum private key
- **Failure**: System will not deploy contracts

#### 6. **Hyperion RPC**
```bash
export HYPERION_RPC_URL="https://hyperion-testnet.metisdevops.link"
```
- **Purpose**: Hyperion testnet connectivity
- **Test**: Must contain "hyperion-testnet.metisdevops.link"
- **Failure**: System will not connect to correct network

## 🔍 Checking Your Mode

### Health Check Command
```bash
hyperagent health
```

**Production Mode Output:**
```
🟢 PRODUCTION MODE ENABLED
All critical dependencies are available and functional.
System is ready for production operations.
```

**Safe Mode Output:**
```
🔴 SAFE MODE ONLY
Critical dependencies are missing. System will run in safe mode.

CRITICAL FAILURES:
  ❌ alith_sdk: Alith package found but missing required classes (Agent, Web3Tools)
  ❌ web3_connection: HYPERION_RPC_URL not set in environment

NEXT STEPS:
1. Install missing dependencies
2. Configure required environment variables
3. Run: hyperagent status --validate
4. Test with: hyperagent workflow run 'test' --network hyperion
```

## 🚨 Error Messages

### Production Mode Required Errors

When attempting operations in Safe Mode, you'll see:

```
🚨 PRODUCTION MODE REQUIRED FOR: Contract Generation

The system is currently running in SAFE MODE due to missing critical dependencies.

CRITICAL FAILURES:
❌ alith_sdk: Alith package found but missing required classes (Agent, Web3Tools)

To enable production mode:
1. Install missing dependencies
2. Configure required environment variables
3. Run: hyperagent status --validate

SYSTEM WILL NOT PERFORM: Contract Generation
```

## 🔧 Enabling Production Mode

### Step 1: Install Dependencies
```bash
# Install Alith SDK
pip install alith>=0.12.0

# Install Foundry
curl -L https://foundry.paradigm.xyz | bash
foundryup
```

### Step 2: Configure Environment
Create a `.env` file:
```bash
# Required for Production Mode
DEFAULT_PRIVATE_KEY="your_private_key_here"
HYPERION_RPC_URL="https://hyperion-testnet.metisdevops.link"

# AI Provider (at least one required)
OPENAI_API_KEY="your_openai_key_here"
GOOGLE_API_KEY="your_google_key_here"
ANTHROPIC_API_KEY="your_anthropic_key_here"
```

### Step 3: Verify Production Mode
```bash
hyperagent health
```

### Step 4: Test Production Operations
```bash
hyperagent workflow run "Create a simple ERC20 token" --network hyperion
```

## 🛡️ Safety Features

### No Silent Fallbacks
- **Before**: System would silently fall back to mock implementations
- **After**: System fails loud and clear when dependencies are missing

### Clear Error Messages
- **Before**: Generic "deployment failed" messages
- **After**: Specific error messages with actionable steps

### Real-time Validation
- **Before**: Cached validation results
- **After**: Always checks current system state

## 🔍 Troubleshooting

### Common Issues

#### 1. "Alith package found but missing required classes"
**Cause**: Mock `alith` package installed instead of real SDK
**Solution**: 
```bash
pip uninstall alith
pip install alith>=0.12.0
```

#### 2. "HYPERION_RPC_URL not set in environment"
**Cause**: Environment variable not configured
**Solution**:
```bash
export HYPERION_RPC_URL="https://hyperion-testnet.metisdevops.link"
```

#### 3. "No AI provider API keys configured"
**Cause**: No AI provider API keys set
**Solution**:
```bash
export OPENAI_API_KEY="your_key_here"
# OR
export GOOGLE_API_KEY="your_key_here"
# OR
export ANTHROPIC_API_KEY="your_key_here"
```

#### 4. "Foundry not found"
**Cause**: Foundry not installed or not in PATH
**Solution**:
```bash
curl -L https://foundry.paradigm.xyz | bash
foundryup
```

### Debug Commands

```bash
# Check system health
hyperagent health

# Test specific components
python -c "from core.validation.production_validator import validate_production_mode; print(validate_production_mode())"

# Check environment variables
env | grep -E "(DEFAULT_PRIVATE_KEY|HYPERION_RPC_URL|.*API_KEY)"
```

## 📋 Production Mode Checklist

Before using HyperAgent in production:

- [ ] Alith SDK installed and functional
- [ ] Foundry installed and in PATH
- [ ] Hyperion RPC URL configured
- [ ] At least one AI provider API key set
- [ ] Private key configured
- [ ] `hyperagent health` shows "🟢 PRODUCTION MODE ENABLED"
- [ ] Test workflow runs successfully
- [ ] Contract deployment works
- [ ] Contract verification works

## 🎯 Best Practices

1. **Always check mode first**: Run `hyperagent health` before operations
2. **Fix dependencies immediately**: Don't ignore Safe Mode warnings
3. **Test after changes**: Verify Production Mode after dependency updates
4. **Monitor logs**: Watch for production mode validation messages
5. **Use environment files**: Keep sensitive keys in `.env` files

## 🔗 Related Documentation

- [Technical Documentation](TECHNICAL_DOCUMENTATION.md) - System architecture and implementation details
- [API Reference](API_REFERENCE.md) - Complete API documentation
- [Integration Guide](INTEGRATOR_GUIDE.md) - Integration patterns and best practices
- [Security Setup](SECURITY_SETUP.md) - Security configuration
- [Emergency Response](EMERGENCY_RESPONSE.md) - Incident response procedures
- [Known Issues](EXECUTION/KNOWN_ISSUES.md) - Current known issues
- [External Monitoring](EXTERNAL_MONITORING.md) - Monitoring setup guide
