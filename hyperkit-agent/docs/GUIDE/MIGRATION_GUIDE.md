<!-- AUDIT_BADGE_START -->
**Implementation Status**: ✅ Verified  
**Version**: 1.4.8  
**Last Verified**: 2025-11-05  
**Commit**: `3649147`  
**Branch**: `main`  
<!-- AUDIT_BADGE_END -->

# Migration Guide - System Refactor v1.5.0

**Version**: 1.5.14  
**Date**: 2025-10-28  
**Status**: Production Ready

---

## 🚨 Breaking Changes Overview

This guide helps you migrate from the previous system architecture to v1.5.0, which includes major changes to AI agent integration and RAG backend.

### What Changed

| Component | Before | After |
|-----------|--------|-------|
| **AI Agent** | LazAI AI agent (with API key) | Alith SDK only (uses OpenAI key) |
| **RAG Backend** | Obsidian/MCP + IPFS Pinata | IPFS Pinata exclusive |
| **Network Chain IDs** | Hyperion: 1001, LazAI: 8888 | Hyperion: 133717, LazAI: 9001 |
| **Mock Fallbacks** | Enabled | Disabled (hard fail) |

---

## 📋 Migration Steps

### 1. Update Environment Variables

#### Remove Deprecated Keys
```bash
# Remove these (if present):
# LAZAI_API_KEY=...
# OBSIDIAN_API_KEY=...
# OBSIDIAN_MCP_API_KEY=...
# MCP_ENABLED=...
```

#### Add Required Keys for Alith SDK
```bash
# Add OpenAI API key (Alith SDK requires it):
OPENAI_API_KEY=sk-...your-openai-api-key...

# Enable Alith SDK:
ALITH_ENABLED=true
```

#### Update IPFS Pinata Configuration
```bash
# Ensure Pinata keys are set (required for RAG):
PINATA_API_KEY=your_pinata_api_key
PINATA_SECRET_KEY=your_pinata_secret_key

# Get keys from: https://app.pinata.cloud/
```

#### Update Network Chain IDs - HYPERION-ONLY
```bash
# Update Hyperion chain ID:
HYPERION_CHAIN_ID=133717  # Changed from 1001

# Note: LazAI and Metis network configs removed - Hyperion-only mode
# Future network support documented in ROADMAP.md only
```

### 2. Update Configuration Files

#### `config.yaml`
```yaml
networks:
  hyperion:
    chain_id: 133717  # Updated from 1001
    rpc_url: https://hyperion-testnet.metisdevops.link
    explorer_url: https://hyperion-testnet-explorer.metisdevops.link
    default: true
    # ... rest of config
  
  # Note: LazAI and Metis network configs removed - Hyperion-only mode
  # Future network support documented in ROADMAP.md only
```

### 3. Code Changes (If Custom Code)

#### AI Agent Usage
**Before:**
```python
from services.core.ai_agent import HyperKitAIAgent

# Used LAZAI_API_KEY
agent = HyperKitAIAgent()  # Required LAZAI_API_KEY
```

**After:**
```python
from services.core.ai_agent import HyperKitAIAgent

# Uses OPENAI_API_KEY + ALITH_ENABLED
agent = HyperKitAIAgent()  # Requires OPENAI_API_KEY + ALITH_ENABLED=true
```

#### RAG Usage
**Before:**
```python
# DEPRECATED: Obsidian RAG removed - use IPFS Pinata instead
# IPFS Pinata RAG is now exclusive - no Obsidian/MCP support
```

**After:**
```python
# Only IPFS Pinata RAG
from services.rag.ipfs_rag import get_ipfs_rag
rag = get_ipfs_rag(config)  # Requires PINATA_API_KEY + PINATA_SECRET_KEY
```

### 4. Network Configuration

#### LazAI Network (Network Only)
```yaml
# LazAI is now ONLY a blockchain network (RPC endpoint)
# NOT an AI agent service
networks:
  lazai:
    chain_id: 9001
    rpc_url: https://rpc.lazai.network/testnet
    explorer_url: https://testnet-explorer.lazai.network
    # Note: No AI agent functionality
```

---

## 🔍 Verification Steps

### 1. Test Configuration
```bash
# Check system status
hyperagent status

# Should show:
# - Alith SDK: configured (if OPENAI_API_KEY set)
# - IPFS Pinata: configured (if PINATA_API_KEY set)
# - Networks: configured correctly
```

### 2. Test RAG Connection
```bash
# Test IPFS Pinata RAG
hyperagent test-rag

# Should show:
# - Pinata Enabled: ✅
# - CID Registry: ✅
# - Overall Status: ✅ PASSED
```

### 3. Test AI Agent
```bash
# Try generating a contract
hyperagent generate "Simple ERC20 token"

# Should use Alith SDK if configured, or fallback LLM
```

### 4. Test Network Configuration
```bash
# Deploy to Hyperion (should use chain ID 133717)
hyperagent deploy contract MyToken.sol --network hyperion

# Should connect to correct network without errors
```

---

## ⚠️ Common Issues & Solutions

### Issue 1: "Alith SDK not configured"
**Symptom**: Warnings about Alith SDK not available

**Solution**:
```bash
# Set OpenAI API key (required for Alith SDK)
export OPENAI_API_KEY=sk-...your-key...

# Enable Alith SDK
export ALITH_ENABLED=true

# Restart the application
```

### Issue 2: "IPFS Pinata not configured"
**Symptom**: RAG operations fail with Pinata errors

**Solution**:
```bash
# Get Pinata API keys from https://app.pinata.cloud/
export PINATA_API_KEY=your_pinata_api_key
export PINATA_SECRET_KEY=your_pinata_secret_key

# Test connection
hyperagent test-rag
```

### Issue 3: "Network not supported"
**Symptom**: Deployment fails with "Network not supported"

**Solution**:
```bash
# Check network name is correct
# Supported: hyperion, lazai, metis
hyperagent deploy contract MyToken.sol --network hyperion

# Check chain ID in config.yaml matches:
# - hyperion: 133717
# - lazai: 9001
# - metis: 1088
```

### Issue 4: MCP/Obsidian Deprecation Warning
**Symptom**: Warning about MCP_ENABLED detected

**Solution**:
```bash
# Remove from .env:
# MCP_ENABLED=... (remove this line)

# System will work without it (uses IPFS Pinata instead)
```

### Issue 5: Wrong Chain ID
**Symptom**: Network connection fails or wrong network

**Solution**:
```bash
# Update chain IDs in config.yaml and .env:
# Hyperion: 133717 (was 1001)
# LazAI: 9001 (was 8888)

# Restart application
```

---

## 📚 Additional Resources

### Getting API Keys
1. **OpenAI API Key** (for Alith SDK):
   - Sign up: https://platform.openai.com/
   - Get key: https://platform.openai.com/api-keys
   - Cost: Pay-per-use

2. **Pinata API Keys** (for IPFS RAG):
   - Sign up: https://app.pinata.cloud/
   - Get keys: Account Settings → API Keys
   - Free tier available

### Documentation
- [IPFS RAG Guide](./IPFS_RAG_GUIDE.md)
- [Configuration Guide](./CONFIGURATION_GUIDE.md)
- [CLI Commands Reference](../CLI_COMMANDS_REFERENCE.md)

### Support
- GitHub Issues: https://github.com/JustineDevs/Hyperkit-Agent/issues
- Documentation: `/docs` directory

---

## ✅ Migration Checklist

- [ ] Removed deprecated environment variables (LAZAI_API_KEY for AI, Obsidian keys)
- [ ] Added OPENAI_API_KEY for Alith SDK
- [ ] Added PINATA_API_KEY and PINATA_SECRET_KEY for RAG
- [ ] Set ALITH_ENABLED=true
- [ ] Updated chain IDs in config.yaml (Hyperion: 133717, LazAI: 9001)
- [ ] Updated chain IDs in .env (if used)
- [ ] Tested configuration with `hyperagent status`
- [ ] Tested RAG with `hyperagent test-rag`
- [ ] Tested AI agent with `hyperagent generate`
- [ ] Tested network deployment
- [ ] Removed any custom code using Obsidian/MCP
- [ ] Updated any custom code using LazAI AI agent

---

**Status**: ✅ Ready for Production  
**Need Help?**: Open an issue on GitHub or check `/docs` directory

---

## 🔗 **Connect With Us**

- 🌐 **Website**: [Hyperionkit.xyz](http://hyperionkit.xyz/)
- 📚 **Documentation**: [GitHub Docs](https://github.com/Hyperionkit/Hyperkit-Agent)
- 💬 **Discord**: [Join Community](https://discord.com/invite/MDh7jY8vWe)
- 🐦 **Twitter**: [@HyperKit](https://x.com/HyperionKit)
- 📧 **Contact**: [Hyperkitdev@gmail.com](mailto:Hyperkitdev@gmail.com) (for security issues)
- 💰 **Bug Bounty**: See [SECURITY.md](../../../SECURITY.md)

**Last Updated**: 2025-01-29  
**Version**: 1.5.14

