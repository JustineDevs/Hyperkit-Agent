# HyperKit AI Agent - Environment Setup Guide v1.2.0

## 🚀 **QUICK START (5 Minutes)**

### **1. Install Dependencies**
```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Foundry (for smart contract compilation)
curl -L https://foundry.paradigm.xyz | bash
foundryup
```

### **2. Configure Environment**
```bash
# Copy environment template
cp env.example .env

# Edit with your API keys
nano .env
```

### **3. Test Installation**
```bash
# Test the agent
python main.py

# Test workflow
hyperagent workflow "Create a simple ERC20 token"
```

---

## 📋 **REQUIRED DEPENDENCIES**

### **1. Foundry Installation (Required for Deployment)**

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

## 🔑 **REQUIRED API KEYS**

### **1. AI Provider API Keys (Required)**

```bash
# Google Gemini (Primary - Free $300 credits)
GOOGLE_API_KEY=your_google_api_key_here

# OpenAI (Secondary - Pay-per-use)
OPENAI_API_KEY=your_openai_api_key_here

# LazAI API (Required for Alith SDK integration)
LAZAI_API_KEY=your_lazai_api_key_here
```

### **2. Optional AI Providers**

```bash
# Anthropic Claude (Optional - Paid service)
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

### **3. IPFS Storage (Pinata)**

```bash
# Pinata IPFS API keys for decentralized storage
PINATA_API_KEY=your_pinata_api_key_here
PINATA_SECRET_KEY=your_pinata_secret_key_here
```

### **4. Blockchain Network RPC URLs**

```bash
# Hyperion Testnet (Primary - Metis)
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

### **5. Wallet Configuration**

```bash
# Your wallet private key (for deployment)
# WARNING: Use test wallets only for development!
PRIVATE_KEY=your_wallet_private_key_here
```

### **6. Obsidian RAG System (MCP Docker)**

```bash
# MCP Docker configuration for advanced Obsidian integration
MCP_ENABLED=true
DOCKER_ENABLED=true
OBSIDIAN_HOST=host.docker.internal
OBSIDIAN_MCP_API_KEY=your_obsidian_mcp_api_key_here
OBSIDIAN_VAULT_PATH=C:/Users/JustineDevs/Downloads/Hyperkit
```

## 🔑 **GETTING API KEYS**

### **Google Gemini API Key (Primary - Required)**
1. Visit [Google AI Studio](https://aistudio.google.com/)
2. Sign up or log in with your Google account
3. Click "Get API Key" in the left sidebar
4. Create a new API key
5. Copy and paste into `.env` file
6. **Free $300 credits included!**

### **OpenAI API Key (Secondary - Optional)**
1. Visit [OpenAI Platform](https://platform.openai.com/)
2. Sign up or log in with your account
3. Go to API Keys section
4. Create a new API key
5. Copy and paste into `.env` file
6. **Pay-per-use pricing**

### **LazAI API Key (Required for Alith SDK)**
1. Visit [LazAI Network](https://lazai.network/)
2. Sign up for an account
3. Go to API Keys section
4. Create a new API key
5. Copy and paste into `.env` file
6. **Required for Alith SDK integration**

### **Pinata IPFS API Keys (Required for Storage)**
1. Visit [Pinata Cloud](https://app.pinata.cloud/)
2. Sign up for a free account
3. Go to API Keys section
4. Create a new API key
5. Copy both API Key and Secret Key
6. **1GB free storage included!**

### **Anthropic Claude API Key (Optional)**
1. Visit [Anthropic Console](https://console.anthropic.com/)
2. Sign up for an account
3. Go to API Keys section
4. Create a new API key
5. Copy and paste into `.env` file
6. **Pay-per-use pricing**

## 🧠 **OBSIDIAN RAG INTEGRATION (MCP Docker)**

### **1. Install Obsidian**
1. Download [Obsidian](https://obsidian.md/) for your platform
2. Install and create a new vault
3. Set vault path in `.env`: `OBSIDIAN_VAULT_PATH=C:/Users/JustineDevs/Downloads/Hyperkit`

### **2. Create Knowledge Base**
1. Create markdown files with smart contract patterns in:
   - `Contracts/` - Smart contract templates
   - `Audits/` - Security checklists and patterns
   - `Templates/` - Deployment templates
   - `Prompts/` - Generation prompts
2. The MCP Docker system will automatically index these files

### **3. MCP Docker Configuration**
The system uses Docker-based MCP (Model Context Protocol) for advanced Obsidian integration:
- **MCP_ENABLED=true** - Enables Docker-based Obsidian access
- **DOCKER_ENABLED=true** - Enables Docker containerization
- **OBSIDIAN_MCP_API_KEY** - Your Obsidian API key (for MCP Docker)
- **OBSIDIAN_HOST=host.docker.internal** - Docker host configuration

**Note**: No Local REST API plugin needed - MCP Docker handles all Obsidian access.

### **4. Start MCP Docker Container**
```bash
# Build and start MCP Docker container
python scripts/setup_mcp_docker.py

# Or manually
docker build -f Dockerfile.mcp -t mcp/obsidian .
docker run -d --name obsidian-mcp -p 27125:27125 mcp/obsidian
```

## 📝 **CONFIGURATION EXAMPLES**

### **Complete .env File Example (v1.2.0)**
```bash
# ============================================================================
# AI/LLM PROVIDER CONFIGURATION
# ============================================================================
GOOGLE_API_KEY=your_google_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
LAZAI_API_KEY=your_lazai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# ============================================================================
# IPFS STORAGE CONFIGURATION (Pinata)
# ============================================================================
PINATA_API_KEY=your_pinata_api_key_here
PINATA_SECRET_KEY=your_pinata_secret_key_here

# ============================================================================
# BLOCKCHAIN NETWORK CONFIGURATION
# ============================================================================
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

# ============================================================================
# WALLET CONFIGURATION
# ============================================================================
PRIVATE_KEY=your_wallet_private_key_here

# ============================================================================
# OBSIDIAN RAG CONFIGURATION (MCP Docker)
# ============================================================================
MCP_ENABLED=true
DOCKER_ENABLED=true
OBSIDIAN_HOST=host.docker.internal
OBSIDIAN_MCP_API_KEY=your_obsidian_mcp_api_key_here
OBSIDIAN_VAULT_PATH=C:/Users/JustineDevs/Downloads/Hyperkit

# ============================================================================
# SECURITY EXTENSIONS (v1.2.0)
# ============================================================================
SECURITY_EXTENSIONS_ENABLED=true
SLITHER_ENABLED=true
MYTHRIL_ENABLED=false
EDB_ENABLED=false

# ============================================================================
# ALITH SDK CONFIGURATION (v1.2.0)
# ============================================================================
ALITH_ENABLED=true
ALITH_MODEL=gpt-4o-mini
ALITH_SETTLEMENT=true
ALITH_INFERENCE_NODE=https://inference.lazai.network
ALITH_PRIVATE_INFERENCE=false

# ============================================================================
# LOGGING AND MONITORING
# ============================================================================
LOG_LEVEL=INFO
ENVIRONMENT=development
DEBUG=false
TEST_MODE=true
```

## 🌐 **NETWORK RPC URLs**

### **Hyperion Testnet (Primary - Metis)**
- **RPC URL**: `https://hyperion-testnet.metisdevops.link`
- **Chain ID**: `133717`
- **Explorer**: `https://hyperion-testnet-explorer.metisdevops.link`
- **Status**: Free, no API key required
- **Gas Price**: 20 gwei

### **Metis Andromeda (Secondary)**
- **RPC URL**: `https://andromeda.metis.io`
- **Chain ID**: `1088`
- **Explorer**: `https://andromeda-explorer.metis.io`
- **Status**: Free, no API key required
- **Gas Price**: 20 gwei

### **LazAI Testnet (Tertiary)**
- **RPC URL**: `https://rpc.lazai.network/testnet`
- **Chain ID**: `9001`
- **Explorer**: `https://testnet-explorer.lazai.network`
- **Status**: Free, no API key required
- **Gas Price**: 1 gwei

## 🛡️ **SECURITY BEST PRACTICES**

1. **Never commit your `.env` file** to version control
2. **Use environment-specific keys** for development vs production
3. **Rotate API keys regularly**
4. **Use read-only keys** when possible
5. **Monitor API usage** to detect unauthorized access
6. **Use test wallets only** for development
7. **Enable security extensions** for production use

## 🚀 **NEW FEATURES (v1.2.0)**

### **Alith SDK Integration**
- **AI-Powered Auditing**: Real AI agent for smart contract analysis
- **On-Chain Inference**: Deploy AI models to blockchain
- **LazAI Network**: Decentralized AI infrastructure
- **Settlement**: Automatic on-chain settlement of AI results

### **Security Extensions**
- **Transaction Simulation**: Simulate transactions before execution
- **Phishing Detection**: Detect malicious contract interactions
- **Address Reputation**: Check address reputation scores
- **Token Approval Management**: Manage token approvals safely
- **ML Risk Scoring**: Machine learning-based risk assessment

### **IPFS Storage Integration**
- **Decentralized Storage**: Store audit reports on IPFS
- **Pinata Integration**: Professional IPFS gateway
- **Content Addressing**: Immutable content addressing
- **Global Distribution**: Fast global content delivery

### **MCP Docker Integration**
- **Advanced Obsidian**: Docker-based Obsidian integration
- **Model Context Protocol**: Standardized AI tool integration
- **Knowledge Base**: Automatic indexing of smart contract patterns
- **RAG System**: Retrieval-augmented generation for better AI responses

## 🔧 **WORKFLOW FEATURES**

### **Interactive Audit Confirmation**
- **Low/Medium Severity**: Proceeds automatically
- **High Severity**: Interactive confirmation required
- **Automation Support**: Use `--allow-insecure` flag for CI/CD

### **Smart Contract Naming**
- `"Create UniswapV2-style DEX"` → `DEX.sol` with `UniswapV2Router02` contract
- `"Create gaming NFT marketplace"` → `NFTMarketplace.sol` with `NftAuctionMarketplace` contract
- `"Create ERC20 staking contract"` → `Staking.sol` with meaningful staking contract name

### **Command-Based Organization**
- `hyperagent workflow` → `artifacts/workflows/`
- `hyperagent generate` → `artifacts/generate/`
- `hyperagent audit` → `artifacts/audit/`
- `hyperagent deploy` → `artifacts/deploy/`
- `hyperagent verify` → `artifacts/verify/`
- `hyperagent test` → `artifacts/test/`

## 🧪 **TESTING YOUR CONFIGURATION**

After setting up your `.env` file, test the configuration:

```bash
# Test the agent
python main.py

# Test workflow with interactive confirmation
hyperagent workflow "Create a simple ERC20 token"

# Test workflow with automation flag
hyperagent workflow "Create a complex DeFi protocol" --allow-insecure

# Test Alith SDK integration
hyperagent audit contract --contract MyToken.sol --use-alith

# Test IPFS storage
hyperagent store report --file audit_report.json

# Test MCP Docker integration
hyperagent rag query "What are common DeFi vulnerabilities?"

# Test specific services
python -m pytest tests/unit/test_core.py -v

# Test CLI interface
hyperagent --help
```

## 🔧 **TROUBLESHOOTING**

### **Common Issues**

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

4. **Alith SDK Issues**
   - Ensure LazAI API key is valid
   - Check if Alith SDK is properly installed
   - Verify network connectivity to LazAI

5. **IPFS Storage Issues**
   - Verify Pinata API keys are correct
   - Check if Pinata account has sufficient quota
   - Ensure network connectivity to Pinata

6. **MCP Docker Issues**
   - Ensure Docker is installed and running
   - Check if MCP container is running
   - Verify Obsidian vault path is correct

### **Getting Help**

- Check the [Issues](https://github.com/JustineDevs/Hyperkit-Agent/issues) page
- Review the [Documentation](https://github.com/JustineDevs/Hyperkit-Agent#readme)
- Contact support: [team@hyperionkit.xyz](mailto:team@hyperionkit.xyz)

---

## 📚 **ADDITIONAL RESOURCES**

### **API Key Sources**
- **Google Gemini**: [Google AI Studio](https://aistudio.google.com/)
- **OpenAI**: [OpenAI Platform](https://platform.openai.com/)
- **LazAI**: [LazAI Network](https://lazai.network/)
- **Pinata**: [Pinata Cloud](https://app.pinata.cloud/)
- **Anthropic**: [Anthropic Console](https://console.anthropic.com/)

### **Network Resources**
- **Hyperion Testnet**: [Metis Devops](https://hyperion-testnet-explorer.metisdevops.link)
- **Metis Andromeda**: [Metis Explorer](https://andromeda-explorer.metis.io)
- **LazAI Testnet**: [LazAI Explorer](https://testnet-explorer.lazai.network)

### **Development Tools**
- **Foundry**: [Foundry Book](https://book.getfoundry.sh/)
- **Obsidian**: [Obsidian Help](https://help.obsidian.md/)
- **Docker**: [Docker Documentation](https://docs.docker.com/)

---

**🎉 You're now ready to use HyperKit AI Agent v1.2.0 with full Alith SDK integration and security extensions!**
