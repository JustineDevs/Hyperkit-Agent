<!-- AUDIT_BADGE_START -->
**Implementation Status**: ✅ Verified  
**Version**: 1.4.7  
**Last Verified**: 2025-11-06  
**Commit**: `013af8b`  
**Branch**: `main`  
<!-- AUDIT_BADGE_END -->

# Configuration Guide - v1.4.7

**Version**: 1.5.14  
**Last Updated**: 2025-10-28

---

## 📋 Overview

This guide covers all configuration options for HyperAgent v1.4.7, including the new Alith SDK integration and IPFS Pinata RAG system.

---

## 🔑 Required Configuration

### 1. AI Agent Configuration

#### Alith SDK (Primary AI Agent)
```bash
# Required: OpenAI API key (Alith SDK uses OpenAI)
OPENAI_API_KEY=sk-proj-...your-openai-api-key...

# Required: Enable Alith SDK
ALITH_ENABLED=true
```

**Note**: Alith SDK is the ONLY AI agent. LazAI is network-only (blockchain RPC), NOT an AI service.

#### Fallback LLM Providers (Optional)
```bash
# Google Gemini (fallback)
GOOGLE_API_KEY=your_google_api_key_here

# Anthropic Claude (fallback)
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

### 2. RAG Configuration (Required for Template Retrieval)

#### IPFS Pinata (Exclusive RAG Backend)
```bash
# Required: Pinata API keys (get from https://app.pinata.cloud/)
PINATA_API_KEY=your_pinata_api_key
PINATA_SECRET_KEY=your_pinata_secret_key
```

**Note**: Obsidian/MCP RAG is deprecated. IPFS Pinata is now the exclusive RAG backend.

### 3. Network Configuration - HYPERION-ONLY MODE

**🔴 CRITICAL**: Hyperion is the **EXCLUSIVE** deployment target. All other networks are not supported in code.

#### Hyperion Testnet (EXCLUSIVE)
```bash
HYPERION_RPC_URL=https://hyperion-testnet.metisdevops.link
HYPERION_CHAIN_ID=133717
HYPERION_EXPLORER_URL=https://hyperion-testnet-explorer.metisdevops.link
HYPERION_EXPLORER_API_KEY=your_hyperion_explorer_api_key_here  # Optional
```

**Note**: 
- Hyperion is the only supported network in production code.
- Future network support (LazAI, Metis) is **documentation-only** - see [ROADMAP.md](../ROADMAP.md).
- No multi-network code exists - system will fail clearly if non-Hyperion network is attempted.

### 4. Wallet Configuration

#### Deployment Private Key
```bash
# Required for contract deployment
DEFAULT_PRIVATE_KEY=your_64_hex_character_private_key

# Alternative (legacy support)
PRIVATE_KEY=your_64_hex_character_private_key
```

**⚠️ WARNING**: Use test wallets only for development! Never commit real private keys to version control.

---

## 📁 Configuration Files

### `.env` File
Primary configuration file. Copy from `env.example`:

```bash
cp env.example .env
# Then edit .env with your actual values
```

### `config.yaml` File
YAML configuration for networks and defaults:

```yaml
ai_providers:
  google:
    api_key: 'YOUR_GOOGLE_API_KEY_HERE'
    model: 'gemini-pro'
  openai:
    api_key: 'YOUR_OPENAI_API_KEY_HERE'
    model: 'gpt-4'
  anthropic:
    api_key: 'YOUR_ANTHROPIC_API_KEY_HERE'
    model: 'claude-3-sonnet'

networks:
  hyperion:
    chain_id: 133717
    explorer_url: https://hyperion-testnet-explorer.metisdevops.link
    rpc_url: https://hyperion-testnet.metisdevops.link
    status: testnet
```

---

## 🔍 Configuration Validation

### Automatic Validation
Configuration is automatically validated on startup. Errors will be logged:

```
CRITICAL CONFIGURATION ERRORS DETECTED
================================================================================
[ERROR] DEFAULT_PRIVATE_KEY not configured
  Required for: Contract deployment, transaction signing
  Fix: Add DEFAULT_PRIVATE_KEY=your_private_key_hex to .env

[ERROR] PINATA_API_KEY not configured
  Required: IPFS Pinata RAG requires PINATA_API_KEY and PINATA_SECRET_KEY
  Fix: Get keys from: https://app.pinata.cloud/
```

### Manual Validation
```bash
# Check system status
hyperagent status

# Test configuration
hyperagent config validate
```

### Strict Mode
Enable hard fail on config errors:

```bash
# Set in .env
HYPERKIT_STRICT_CONFIG=true

# System will exit with error if critical config missing
```

---

## 🎯 Configuration Priority

Configuration is loaded in this order (later sources override earlier):

1. **config.yaml** (base configuration)
2. **.env file** (environment variables)
3. **System environment variables** (override everything)

Example:
```bash
# config.yaml has: OPENAI_API_KEY=key1
# .env has: OPENAI_API_KEY=key2
# System env has: OPENAI_API_KEY=key3

# Final value: key3 (system env wins)
```

---

## 🚫 Deprecated Configuration

These configuration keys are **deprecated** and will trigger warnings:

```bash
# Deprecated - Remove these (system will warn if detected):
# LAZAI_API_KEY - Not used for AI agent (LazAI is network-only)
# OBSIDIAN_API_KEY - Obsidian RAG deprecated (use IPFS Pinata)
# OBSIDIAN_MCP_API_KEY - Obsidian MCP deprecated (use IPFS Pinata)
# MCP_ENABLED - MCP/Obsidian deprecated (use IPFS Pinata)
```

**Action**: Remove from `.env` and `config.yaml`. System will work without them.

---

## ✅ Configuration Checklist

- [ ] OpenAI API key set (for Alith SDK)
- [ ] ALITH_ENABLED=true
- [ ] Pinata API keys set (PINATA_API_KEY, PINATA_SECRET_KEY)
- [ ] Default private key set (for deployment)
- [ ] Network chain IDs correct (Hyperion: 133717, LazAI: 9001)
- [ ] Network RPC URLs correct
- [ ] Deprecated keys removed
- [ ] Configuration validated with `hyperagent status`

---

## 📚 Additional Resources

- [Migration Guide](./MIGRATION_GUIDE.md) - Step-by-step migration instructions
- [IPFS RAG Guide](./IPFS_RAG_GUIDE.md) - IPFS Pinata RAG setup
- [env.example](../env.example) - Example configuration file
- [CLI Commands](../CLI_COMMANDS_REFERENCE.md) - All available commands

---

**Questions?** Check `/docs` directory or open an issue on GitHub.

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
