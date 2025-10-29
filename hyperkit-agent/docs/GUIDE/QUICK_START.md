# Quick Start Guide - v1.5.0

**Version**: 1.5.4  
**Last Updated**: 2025-10-28

---

## 🚀 Get Started in 5 Minutes

### Step 1: Install Dependencies

```bash
# Install Python dependencies
cd hyperkit-agent
pip install -r requirements.txt  # Includes Alith SDK and IPFS features

# Install Foundry (for contract compilation)
curl -L https://foundry.paradigm.xyz | bash
foundryup
```

### Step 2: Configure Environment

```bash
# Copy example environment file
cp env.example .env

# Edit .env with your API keys:
# - OPENAI_API_KEY (required for Alith SDK)
# - PINATA_API_KEY & PINATA_SECRET_KEY (required for RAG)
# - DEFAULT_PRIVATE_KEY (required for deployment)
```

### Step 3: Verify Configuration

```bash
# Check system status
hyperagent status

# Test RAG connection
hyperagent test-rag
```

### Step 4: Generate Your First Contract

```bash
# Generate a simple ERC20 token
hyperagent generate "Create an ERC20 token named MyToken with symbol MTK and 1 million initial supply"

# Or run full workflow
hyperagent workflow run "Create a secure voting contract"
```

---

## 📋 Essential Commands

### Contract Generation
```bash
# Generate contract from natural language
hyperagent generate "Your contract description"

# Use RAG templates for better context
hyperagent generate "Your description" --use-rag
```

### Contract Auditing
```bash
# Audit a contract file
hyperagent audit contract MyToken.sol

# Batch audit directory
hyperagent batch-audit --directory contracts/
```

### Deployment
```bash
# Deploy to Hyperion testnet (exclusive deployment target)
hyperagent deploy contract MyToken.sol
# Note: --network flag is deprecated/hidden - Hyperion is hardcoded

# Deploy with constructor arguments
hyperagent deploy contract MyToken.sol --constructor-args '["MyToken", "MTK", 1000000]'
```

### Full Workflow
```bash
# Run complete 5-stage workflow
hyperagent workflow run "Your contract description"

# Options:
# --network hyperion (default)
# --test-only (skip deployment)
# --allow-insecure (proceed despite high severity)
```

---

## 🔧 Configuration Quick Reference

### Required Keys

```bash
# AI Agent (Alith SDK)
OPENAI_API_KEY=sk-...          # Required for Alith SDK
ALITH_ENABLED=true              # Enable Alith SDK

# RAG System (IPFS Pinata)
PINATA_API_KEY=...              # Required for RAG
PINATA_SECRET_KEY=...           # Required for RAG

# Deployment
DEFAULT_PRIVATE_KEY=...         # Required for deployment
```

### Network Configuration

```bash
# Hyperion Testnet (default)
HYPERION_CHAIN_ID=133717
HYPERION_RPC_URL=https://hyperion-testnet.metisdevops.link

# LazAI Testnet (network only)
LAZAI_CHAIN_ID=9001
LAZAI_RPC_URL=https://rpc.lazai.network/testnet
```

---

## ⚠️ Important Notes

### AI Agent
- **Alith SDK** is the ONLY AI agent (uses OpenAI API key)
- **LazAI** is network-only (blockchain RPC), NOT an AI agent
- If Alith SDK not configured, system uses fallback LLM

### RAG System
- **IPFS Pinata** is the exclusive RAG backend
- **Obsidian/MCP RAG** is deprecated
- RAG requires PINATA_API_KEY and PINATA_SECRET_KEY

### Network Chain IDs
- Hyperion: **133717** (updated from 1001)
- LazAI: **9001** (updated from 8888)
- Metis: **1088** (unchanged)

---

## 🆘 Troubleshooting

### "Alith SDK not configured"
→ Set `OPENAI_API_KEY` and `ALITH_ENABLED=true`

### "IPFS Pinata not configured"
→ Set `PINATA_API_KEY` and `PINATA_SECRET_KEY`

### "Network not supported"
→ Check network name (hyperion, lazai, metis) and chain ID in config

### "MCP_ENABLED detected"
→ Remove `MCP_ENABLED` from `.env` (deprecated)

---

## 📚 Next Steps

- [Migration Guide](./MIGRATION_GUIDE.md) - Migrate from older versions
- [Configuration Guide](./CONFIGURATION_GUIDE.md) - Detailed config options
- [IPFS RAG Guide](./IPFS_RAG_GUIDE.md) - RAG template setup
- [CLI Commands](../CLI_COMMANDS_REFERENCE.md) - All available commands

---

**Ready to go?** Run `hyperagent status` to verify your setup!

---

## 🔗 **Connect With Us**

- 🌐 **Website**: [Hyperionkit.xyz](http://hyperionkit.xyz/)
- 📚 **Documentation**: [GitHub Docs](https://github.com/Hyperionkit/Hyperkit-Agent)
- 💬 **Discord**: [Join Community](https://discord.com/invite/MDh7jY8vWe)
- 🐦 **Twitter**: [@HyperKit](https://x.com/HyperionKit)
- 📧 **Contact**: [Hyperkitdev@gmail.com](mailto:Hyperkitdev@gmail.com) (for security issues)
- 💰 **Bug Bounty**: See [SECURITY.md](../../../SECURITY.md)

**Last Updated**: 2025-01-29  
**Version**: 1.5.4
