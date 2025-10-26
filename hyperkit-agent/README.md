# 🚀 HyperKit AI Agent

> **AI-Powered Smart Contract Development, Security Auditing, and Multi-Chain Deployment Platform**

[![Tests](https://github.com/JustineDevs/Hyperkit-Agent/actions/workflows/test.yml/badge.svg)](https://github.com/JustineDevs/Hyperkit-Agent/actions)
[![Coverage](https://codecov.io/gh/JustineDevs/Hyperkit-Agent/branch/main/graph/badge.svg)](https://codecov.io/gh/JustineDevs/Hyperkit-Agent)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Solidity 0.8.20+](https://img.shields.io/badge/solidity-0.8.20+-lightgrey.svg)](https://soliditylang.org/)

## 📋 Table of Contents

- [What is HyperKit?](#-what-is-hyperkit)
- [Key Features](#-key-features)
- [Quick Start](#-quick-start)
- [Supported Networks](#-supported-networks)
- [Usage Examples](#-usage-examples)
- [Architecture](#-architecture)
- [Development](#-development)
- [Contributing](#-contributing)
- [Security](#-security)
- [License](#-license)

## 🎯 What is HyperKit?

HyperKit is an AI-powered platform for smart contract development, security auditing, and multi-chain deployment. It combines Large Language Models (LLMs), Retrieval-Augmented Generation (RAG), and blockchain technology to streamline the entire smart contract lifecycle.

### **Why HyperKit?**

- **AI-Powered Generation**: Create production-ready smart contracts from natural language
- **Multi-Source Auditing**: Comprehensive security analysis with consensus scoring
- **One-Command Deployment**: Deploy to multiple chains with a single command
- **Auto-Verification**: Automatic contract verification on block explorers
- **Built-in Testing**: Integrated testing framework with Foundry

## ✨ Key Features

### 🤖 **AI-Powered Smart Contract Generation**
- Natural language to Solidity conversion
- Template-based generation (ERC20, ERC721, DeFi, DAO)
- Best practices and security patterns built-in

### 🔍 **Multi-Source Security Auditing**
- Integration with Slither, Mythril, and custom analyzers
- Confidence scoring and consensus-based reporting
- Detailed vulnerability analysis with remediation suggestions
- **Batch auditing** for multiple contracts with recursive directory scanning
- Report generation in JSON and Markdown formats

### 🌐 **Multi-Chain Deployment**
- **Primary Networks**: Hyperion (Testnet), LazAI (Testnet), Metis (Mainnet)
- Foundry-based compilation and deployment
- Gas optimization and transaction monitoring
- Optimized for AI-powered blockchain deployment

### ✅ **Automatic Verification**
- Blockscout and Etherscan integration
- Source code verification
- Contract metadata publishing

### 🧪 **Integrated Testing**
- Unit, integration, and end-to-end testing
- Foundry test suite
- Coverage reporting

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+ (for versioning)
- Foundry (for Solidity compilation)
- Git

### Installation

```bash
# Clone the repository
git clone https://github.com/JustineDevs/Hyperkit-Agent.git
cd Hyperkit-Agent/hyperkit-agent

# Install dependencies
pip install -e .

# Install Foundry
curl -L https://foundry.paradigm.xyz | bash
foundryup

# Install OpenZeppelin contracts
forge install OpenZeppelin/openzeppelin-contracts

# Set up environment
cp env.example .env
# Edit .env with your configuration
```

### Configuration

Create a `.env` file with your configuration:

```env
# AI Provider API Keys
GOOGLE_API_KEY=your_google_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Blockchain Configuration
DEFAULT_PRIVATE_KEY=your_private_key_here
HYPERION_RPC_URL=https://hyperion-testnet.metisdevops.link
```

### Verify Installation

```bash
# Test the CLI
hyperagent --help

# Run tests
pytest tests/ -v

# Build contracts
forge build
```

## 🌍 Supported Networks

HyperKit AI Agent focuses on three primary networks optimized for AI-powered smart contract deployment:

| Network | Chain ID | Status | Explorer |
|---------|----------|--------|----------|
| **Hyperion Testnet** | 1001 | 🚧 Testnet (Mainnet Coming Soon) | [Explorer](https://hyperion-testnet-explorer.metisdevops.link) |
| **LazAI Testnet** | 8888 | 🚧 Testnet (Mainnet Coming Soon) | [Explorer](https://lazai-explorer.example.com) |
| **Metis Mainnet** | 1088 | ✅ Mainnet | [Explorer](https://andromeda-explorer.metis.io) |

> **Note**: Hyperion and LazAI are currently in testnet phase. Mainnet launches are coming soon!

## 📚 Usage Examples

### Generate and Deploy a Token

```bash
# Generate, audit, and deploy a gaming token
hyperagent workflow run "Create a gaming token" --network hyperion

# Output: Contract address, transaction hash, gas used
```

### Audit an Existing Contract

```bash
# Audit a single contract file
hyperagent audit contract --contract MyToken.sol

# Audit a contract address from blockchain
hyperagent audit contract --address 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb --network hyperion

# Batch audit all contracts in a directory
hyperagent audit batch --directory ./contracts --recursive

# Batch audit from a file list
hyperagent audit batch --file contracts.txt --output ./audit-reports

# View audit report
hyperagent audit report --report audit-reports/MyToken_audit.json
```

### Deploy a Custom Contract

```bash
# Deploy a contract
hyperagent deploy --contract MyToken.sol --network hyperion

# Verify after deployment
hyperagent verify contract 0xYourContractAddress --network hyperion
```

### Monitor Deployments

```bash
# Check system health
hyperagent monitor health

# View metrics
hyperagent monitor metrics

# Watch logs
hyperagent monitor logs --follow
```

## 🏗️ Architecture

```
HyperKit AI Agent
├── AI Layer (LLM + RAG)
│   ├── Contract Generation
│   ├── Security Analysis
│   └── Code Optimization
├── Blockchain Layer
│   ├── Multi-Chain Support
│   ├── Transaction Management
│   └── Smart Contract Interaction
├── Security Layer
│   ├── Static Analysis (Slither, Mythril)
│   ├── Dynamic Testing
│   └── Consensus Scoring
└── Storage Layer
    ├── Vector Database (RAG)
    ├── Artifact Management
    └── Audit Reports
```

### **5-Stage Workflow**

1. **Generate**: AI-powered contract creation
2. **Audit**: Multi-source security analysis
3. **Deploy**: Foundry-based deployment
4. **Verify**: Auto-verification on explorers
5. **Test**: Comprehensive testing suite

## 🛠️ Development

### Project Structure

```
hyperkit-agent/
├── cli/                # Command-line interface
├── core/               # Core functionality
│   ├── agent/          # AI agent logic
│   ├── config/         # Configuration management
│   └── tools/          # Utility tools
├── services/           # Service implementations
│   ├── audit/          # Security auditing
│   ├── deployment/     # Contract deployment
│   ├── generation/     # Contract generation
│   └── verification/   # Contract verification
├── tests/              # Test suite
│   ├── unit/           # Unit tests
│   ├── integration/    # Integration tests
│   └── security/       # Security tests
├── docs/               # Documentation
└── artifacts/          # Generated contracts and reports
```

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=hyperkit-agent --cov-report=html

# Run Solidity tests
forge test -vvv

# Run specific test
pytest tests/test_audit.py::test_contract_audit -v
```

### Code Quality

```bash
# Format code
black hyperkit-agent/
isort hyperkit-agent/

# Lint
flake8 hyperkit-agent/ --max-line-length=120

# Type checking
mypy hyperkit-agent/

# Security scan
bandit -r hyperkit-agent/
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Quick Contribution Workflow

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests
5. Run tests and linters
6. Commit your changes (`git commit -m 'feat: add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## 🔒 Security

Security is our top priority. We follow industry best practices:

- **Code Audits**: Regular security audits
- **Dependency Scanning**: Automated vulnerability detection
- **Secure Defaults**: Secure configuration out of the box
- **Bug Bounty**: Rewards for responsible disclosure

### Reporting Security Issues

**DO NOT** open a public issue for security vulnerabilities.

Email: security@hyperkit.dev

See [SECURITY.md](SECURITY.md) for details.

## 📊 Current Status

### **Production Ready** ✅
- Multi-chain deployment
- Security auditing
- Contract verification
- CLI interface

### **In Development** 🚧
- Batch operations
- Advanced analytics
- Multi-signature support
- Governance tools

### **Known Limitations** ⚠️
- Deployment requires pre-compiled artifacts (run `forge build`)
- Some AI features require valid API keys
- Limited to EVM-compatible chains

See `hyperagent limitations` for detailed status.

## 📖 Documentation

- [Architecture Overview](docs/README.md)
- [API Reference](docs/API_REFERENCE.md)
- [Developer Guide](docs/DEVELOPER_GUIDE.md)
- [Security Best Practices](docs/SECURITY_BEST_PRACTICES.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)

## 📜 License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.

## 🙏 Acknowledgments

- [OpenZeppelin](https://openzeppelin.com/) for secure smart contract libraries
- [Foundry](https://getfoundry.sh/) for blazing fast Solidity toolkit
- [Alith SDK](https://alith.ai/) for AI agent framework
- [Metis](https://metis.io/) for Hyperion testnet support

## 📞 Support

- **Documentation**: [docs/](docs/)
- **Discord**: [Join our community](https://discord.gg/hyperkit)
- **GitHub Issues**: [Report bugs](https://github.com/JustineDevs/Hyperkit-Agent/issues)
- **Email**: support@hyperkit.dev

## 🗺️ Roadmap

See [ROADMAP.md](docs/ROADMAP.md) for planned features and milestones.

---

**Built with ❤️ by the HyperKit Team**

⭐ Star us on GitHub if you find HyperKit useful!
