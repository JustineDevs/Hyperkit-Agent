# Environment Setup Guide

## Required API Keys

To use the HyperKit AI Agent, you'll need to configure the following API keys in your `.env` file:

### 1. AI Provider API Keys (Cloud-Based Only)

```bash
# Google Gemini (Primary Provider - Free $300 credits)
GOOGLE_API_KEY=your_google_api_key_here

# OpenAI (Secondary Provider - Optional)
OPENAI_API_KEY=your_openai_api_key_here
```

### 2. Disabled Providers (Not Used)

```bash
# These providers are not used in this version
# ANTHROPIC_API_KEY=your_anthropic_api_key_here
# DASHSCOPE_API_KEY=your_dashscope_api_key_here
# DEEPSEEK_API_KEY=your_deepseek_api_key_here
# XAI_API_KEY=your_xai_api_key_here
# Local models (GPT-OSS, LM Studio) - Removed for cloud-based architecture
```

### 3. Blockchain Network RPC URLs

```bash
# Hyperion Testnet (Primary - Focus Network)
HYPERION_RPC_URL=https://hyperion-testnet.metisdevops.link
HYPERION_CHAIN_ID=133717
HYPERION_EXPLORER_URL=https://hyperion-testnet-explorer.metisdevops.link

# Other Networks (Temporarily Disabled - Focus on Hyperion)
# POLYGON_RPC_URL=https://polygon-rpc.com
# ARBITRUM_RPC_URL=https://arb1.arbitrum.io/rpc
# ETHEREUM_RPC_URL=https://mainnet.infura.io/v3/YOUR_INFURA_PROJECT_ID
```

### 4. RAG System Configuration (Simple MCP)

```bash
# Simple MCP Integration (Direct Obsidian API)
MCP_ENABLED=true
OBSIDIAN_API_KEY=your_obsidian_api_key_here
OBSIDIAN_API_URL=http://localhost:27124
```

### 5. Wallet Configuration

```bash
# Your wallet private key (for deployment)
DEFAULT_PRIVATE_KEY=your_wallet_private_key_here
```

## Getting API Keys

### Google Gemini API Key (Primary - Required)
1. Visit [Google AI Studio](https://aistudio.google.com/)
2. Sign up or log in with your Google account
3. Click "Get API Key" in the left sidebar
4. Create a new API key
5. Copy and paste into `.env` file
6. **Free $300 credits included!**

### OpenAI API Key (Secondary - Optional)
1. Visit [OpenAI Platform](https://platform.openai.com/)
2. Sign up or log in with your account
3. Go to API Keys section
4. Create a new API key
5. Copy and paste into `.env` file
6. **Pay-per-use pricing**

### Cloud-Based Architecture
The HyperKit Agent uses **cloud-based AI providers only** (Google Gemini + OpenAI) for all AI-powered contract generation. No local models or GPT-OSS setup required.

## Obsidian Integration Setup (MCP Docker Only)

### 1. Install Obsidian
1. Download [Obsidian](https://obsidian.md/) for your platform
2. Install and create a new vault
3. No vault path configuration needed - MCP Docker handles this automatically

### 2. Create Knowledge Base
1. Create markdown files with smart contract patterns in:
   - `Contracts/` - Smart contract templates
   - `Audits/` - Security checklists and patterns
   - `Templates/` - Deployment templates
   - `Prompts/` - Generation prompts
2. The MCP Docker system will automatically index these files

### 3. MCP Docker Configuration
The system uses Docker-based MCP (Model Context Protocol) for advanced Obsidian integration:
- **MCP_ENABLED=true** - Enables Docker-based Obsidian access
- **DOCKER_ENABLED=true** - Enables Docker containerization
- **OBSIDIAN_MCP_API_KEY** - Your Obsidian API key (for MCP Docker)
- **OBSIDIAN_HOST=host.docker.internal** - Docker host configuration

**Note**: No Local REST API plugin needed - MCP Docker handles all Obsidian access.

## Configuration Examples

### Complete .env File Example
```bash
# AI Provider API Keys (Cloud-Based)
GOOGLE_API_KEY=your_google_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# MCP Configuration
MCP_ENABLED=true
MCP_CONFIG_PATH=mcp_config.json
OBSIDIAN_MCP_API_KEY=your_obsidian_api_key_here

# Docker Configuration
DOCKER_ENABLED=true
OBSIDIAN_HOST=host.docker.internal

# LangChain Configuration
LANGSMITH_TRACING=true
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
LANGSMITH_API_KEY=your_langsmith_api_key_here
LANGSMITH_PROJECT=your_project_name

# Blockchain Configuration (Hyperion Focus)
DEFAULT_NETWORK=hyperion
HYPERION_RPC_URL=https://hyperion-testnet.metisdevops.link
HYPERION_CHAIN_ID=133717
HYPERION_EXPLORER_URL=https://hyperion-testnet-explorer.metisdevops.link

# Wallet Configuration
DEFAULT_PRIVATE_KEY=your_wallet_private_key_here

# Security Tools
SLITHER_ENABLED=true
MYTHRIL_ENABLED=true
EDB_ENABLED=true

# Logging
LOG_LEVEL=INFO
```

## Network RPC URLs

### Hyperion Testnet (Primary Focus)
- **RPC URL**: `https://hyperion-testnet.metisdevops.link`
- **Chain ID**: `133717`
- **Explorer**: `https://hyperion-testnet-explorer.metisdevops.link`
- **Status**: Free, no API key required

### Other Networks (Temporarily Disabled)
- **Polygon**: `https://polygon-rpc.com` (commented out)
- **Arbitrum**: `https://arb1.arbitrum.io/rpc` (commented out)
- **Ethereum**: Use Infura, Alchemy, or QuickNode (commented out)

## Security Best Practices

1. **Never commit your `.env` file** to version control
2. **Use environment-specific keys** for development vs production
3. **Rotate API keys regularly**
4. **Use read-only keys** when possible
5. **Monitor API usage** to detect unauthorized access

## Testing Your Configuration

After setting up your `.env` file, test the configuration:

```bash
# Test the agent
python main.py

# Test specific services
python -m pytest tests/unit/test_core.py -v

# Test CLI interface
python cli.py --help
```

## Troubleshooting

### Common Issues

1. **API Key Not Working**
   - Verify the key is correct and active
   - Check if you have sufficient credits/quota
   - Ensure the key has the right permissions

2. **RPC Connection Failed**
   - Verify the RPC URL is correct
   - Check if the network is accessible
   - Try a different RPC provider

3. **Wallet Issues**
   - Ensure the private key is valid
   - Check if the wallet has sufficient funds
   - Verify the network matches your wallet

### Getting Help

- Check the [Issues](https://github.com/JustineDevs/Hyperkit-Agent/issues) page
- Review the [Documentation](https://github.com/JustineDevs/Hyperkit-Agent#readme)
- Contact support: [team@hyperionkit.xyz](mailto:team@hyperionkit.xyz)
