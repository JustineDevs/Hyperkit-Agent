# Environment Setup Guide

## Required Dependencies

### 1. Foundry Installation (Required for Deployment)

The HyperKit AI Agent uses Foundry for smart contract compilation and deployment. You must install Foundry before using the agent.

#### Windows Installation

**Option 1: Automatic Installation (Recommended)**
```bash
# Run the installation script
curl -L https://foundry.paradigm.xyz | bash

# Restart your terminal, then run:
foundryup
```

**Option 2: Manual Installation**
1. Download Foundry from [GitHub Releases](https://github.com/foundry-rs/foundry/releases)
2. Extract to `C:\Program Files\Foundry\`
3. Add `C:\Program Files\Foundry\bin` to your PATH
4. Restart terminal and verify: `forge --version`

#### Linux/macOS Installation
```bash
# Install Foundry
curl -L https://foundry.paradigm.xyz | bash

# Restart terminal, then run:
foundryup

# Verify installation
forge --version
```

#### Verify Foundry Installation
```bash
# Check if Foundry is installed
forge --version
# Should output: forge 1.4.3-nightly (or similar)

# Check if forge is in PATH
which forge
# Should output: /home/user/.foundry/bin/forge (Linux/Mac) or C:\Program Files\Foundry\bin\forge.exe (Windows)
```

**Note**: If Foundry is not installed, the agent will run in simulation mode (no actual deployment).

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
# Hyperion Testnet (Primary)
HYPERION_RPC_URL=https://hyperion-testnet.metisdevops.link
HYPERION_CHAIN_ID=133717
HYPERION_EXPLORER_URL=https://hyperion-testnet-explorer.metisdevops.link

# Metis Andromeda (Secondary)
METIS_RPC_URL=https://andromeda.metis.io
METIS_CHAIN_ID=1088
METIS_EXPLORER_URL=https://andromeda-explorer.metis.io

# LazAI Testnet (Tertiary)
LAZAI_RPC_URL=https://rpc.lazai.network/testnet
LAZAI_CHAIN_ID=9001
LAZAI_EXPLORER_URL=https://testnet-explorer.lazai.network
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

# Blockchain Configuration (Hyperion/Metis/LazAI Focus)
DEFAULT_NETWORK=hyperion
HYPERION_RPC_URL=https://hyperion-testnet.metisdevops.link
HYPERION_CHAIN_ID=133717
HYPERION_EXPLORER_URL=https://hyperion-testnet-explorer.metisdevops.link

METIS_RPC_URL=https://andromeda.metis.io
METIS_CHAIN_ID=1088
METIS_EXPLORER_URL=https://andromeda-explorer.metis.io

LAZAI_RPC_URL=https://rpc.lazai.network/testnet
LAZAI_CHAIN_ID=9001
LAZAI_EXPLORER_URL=https://testnet-explorer.lazai.network

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

### Hyperion Testnet (Primary)
- **RPC URL**: `https://hyperion-testnet.metisdevops.link`
- **Chain ID**: `133717`
- **Explorer**: `https://hyperion-testnet-explorer.metisdevops.link`
- **Status**: Free, no API key required

### Metis Andromeda (Secondary)
- **RPC URL**: `https://andromeda.metis.io`
- **Chain ID**: `1088`
- **Explorer**: `https://andromeda-explorer.metis.io`
- **Status**: Free, no API key required

### LazAI Testnet (Tertiary)
- **RPC URL**: `https://rpc.lazai.network/testnet`
- **Chain ID**: `9001`
- **Explorer**: `https://testnet-explorer.lazai.network`
- **Status**: Free, no API key required

## Security Best Practices

1. **Never commit your `.env` file** to version control
2. **Use environment-specific keys** for development vs production
3. **Rotate API keys regularly**
4. **Use read-only keys** when possible
5. **Monitor API usage** to detect unauthorized access

## Workflow Features

### Interactive Audit Confirmation

The HyperKit AI Agent includes intelligent audit confirmation for high-severity security issues:

- **Low/Medium Severity**: Proceeds automatically
- **High Severity**: Interactive confirmation required
- **Automation Support**: Use `--allow-insecure` flag for CI/CD

### Smart Contract Naming

The agent generates meaningful contract names based on functionality:
- `"Create UniswapV2-style DEX"` → `DEX.sol` with `UniswapV2Router02` contract
- `"Create gaming NFT marketplace"` → `NFTMarketplace.sol` with `NftAuctionMarketplace` contract
- `"Create ERC20 staking contract"` → `Staking.sol` with meaningful staking contract name

### Command-Based Organization

Artifacts are organized by command type:
- `hyperagent workflow` → `artifacts/workflows/`
- `hyperagent generate` → `artifacts/generate/`
- `hyperagent audit` → `artifacts/audit/`
- `hyperagent deploy` → `artifacts/deploy/`
- `hyperagent verify` → `artifacts/verify/`
- `hyperagent test` → `artifacts/test/`

## Testing Your Configuration

After setting up your `.env` file, test the configuration:

```bash
# Test the agent
python main.py

# Test workflow with interactive confirmation
hyperagent workflow "Create a simple ERC20 token"

# Test workflow with automation flag
hyperagent workflow "Create a complex DeFi protocol" --allow-insecure

# Test specific services
python -m pytest tests/unit/test_core.py -v

# Test CLI interface
hyperagent --help
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
