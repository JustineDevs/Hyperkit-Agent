# HyperKit

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)]
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)]
[![Security: bandit](https://img.shields.io/badge/security-bandit-yellow.svg)](https://github.com/PyCQA/bandit)]

## Overview

**HyperKit** is your go-to SDK for building beautiful onchain applications. Ship in minutes, not weeks. Anyone can build an onchain app in 15 minutes with HyperKit. No blockchain experience required.

### AI Capabilities
- **Smart Contract Generation**: AI-powered creation of Solidity smart contracts using multiple LLM providers
- **Code Validation**: Automated security scanning and code quality checks
- **Multi-Model Support**: Integration with Claude, GPT, Gemini, DeepSeek, and other AI providers
- **Intelligent Analysis**: AI-driven contract optimization and gas efficiency recommendations

## Workflow Commands CLI

| Command | Description |
|---------|-------------|
| `hyperagent generate "Create ERC20 token"` | Generate smart contracts using AI from natural language prompts |
| `hyperagent audit contracts/Token.sol` | Audit smart contracts for security vulnerabilities |
| `hyperagent deploy contracts/Token.sol --network hyperion` | Deploy smart contracts to blockchain networks |
| `hyperagent workflow "Create ERC20 token" --test-only` | Complete end-to-end workflow: Generate → Audit → Deploy → Test |
| `hyperagent interactive` | Launch interactive development shell for real-time contract development |
| `hyperagent status` | Check system status and connectivity |
| `hyperagent test` | Run sample workflows and test functionality |

## Other Commands

| Command | Description |
|---------|-------------|
| `hyperagent scaffold my-project --type defi` | Generate full-stack dApp scaffolds |
| `hyperagent verify 0x742d35... --network hyperion` | Verify deployed contracts on block explorer |
| `hyperagent dashboard` | Launch web-based visual dashboard |

## Features

### 🤖 AI Project Generation
- **Smart Contract Generation**: AI-powered creation of Solidity smart contracts
- **dApp Templates**: Pre-built templates for DeFi protocols, NFT marketplaces, and more
- **Code Validation**: Automated security scanning and code quality checks
- **Multi-Model Support**: Integration with Claude, GPT, Gemini, and other AI providers

### 🧩 HyperKit Modules
- **Modular UI Components**: Drag-and-drop interface for rapid prototyping
- **Theme Customization**: Universal theming system across all components
- **Dynamic Preview**: Real-time preview with one-click copy-paste functionality
- **Component Library**: Extensive library of Web3-specific UI elements

### 🌐 Cross-Chain DeFi Primitives
- **Vault Contracts**: Automated yield farming and liquidity management
- **Swap Contracts**: DEX functionality with cross-chain support
- **Bridge Integration**: Seamless asset migration between Hyperion and Andromeda
- **Governance System**: Built-in voting and proposal mechanisms

### 🛠️ Developer Tools
- **Python SDK**: Comprehensive SDK for backend integration
- **CLI Tools**: Command-line interface for project scaffolding and deployment
- **Visual Dashboard**: Web-based interface for contract management
- **Real-time Monitoring**: Live status tracking and performance metrics

## Quick Start

### Prerequisites
- Python 3.9 or higher
- Node.js 16+ (for frontend components)
- Git
- Hyperion/Andromeda wallet

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/JustineDevs/Hyperkit-Agent.git
   cd hyperkit-agent
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install HyperKit Agent**
   ```bash
   pip install --editable .
   ```

4. **Set up environment variables**
   ```bash
   cp env.example .env
   # Edit .env with your API keys and wallet configuration
   ```

5. **Initialize HyperKit Agent**
   ```bash
   hyperagent status
   ```

6. **Generate your first contract**
   ```bash
   hyperagent generate "Create a simple ERC20 token"
   ```

## Architecture

```
HyperKit/
├── hyperkit-agent/        # Core Python package
│   ├── core/              # Core functionality
│   │   ├── agent/         # AI agent and workflow management
│   │   ├── config/        # Configuration management
│   │   └── llm/          # LLM provider integration
│   ├── services/          # Service modules
│   │   ├── audit/        # Security auditing
│   │   ├── deployment/    # Contract deployment
│   │   ├── generation/    # Contract generation
│   │   └── monitoring/    # Transaction monitoring
│   ├── contracts/         # Smart contract templates
│   │   ├── generated/    # AI-generated contracts
│   │   ├── deployed/     # Deployed contract addresses
│   │   └── templates/    # Contract templates
│   ├── tests/            # Comprehensive test suite
│   │   ├── unit/         # Unit tests
│   │   ├── integration/  # Integration tests
│   │   ├── e2e/         # End-to-end tests
│   │   ├── performance/  # Performance tests
│   │   └── security/    # Security tests
│   └── artifacts/        # Generated artifacts
│       ├── workflows/    # Workflow outputs
│       ├── audits/      # Audit reports
│       └── deployments/  # Deployment information
```

## Documentation

| Resource | Description | Link |
|----------|-------------|------|
| **Getting Started** | Quick start guide and installation | [docs.hyperionkit.xyz](https://docs.hyperionkit.xyz/) |
| **AI Generation** | Smart contract generation guide | [docs.hyperionkit.xyz](https://docs.hyperionkit.xyz/) |
| **CLI Reference** | Complete CLI command reference | [docs.hyperionkit.xyz](https://docs.hyperionkit.xyz/) |
| **API Documentation** | Python SDK and API reference | [docs.hyperionkit.xyz](https://docs.hyperionkit.xyz/) |
| **Examples** | Code examples and tutorials | [docs.hyperionkit.xyz](https://docs.hyperionkit.xyz/) |

## Supported Networks

| Network | Status | Features | Use Cases |
|---------|--------|----------|-----------|
| **Hyperion** | 🔄 Testnet | Native support, optimized | Primary development |
| **Metis** | 🔄 Mainnet | Cross-chain bridging, Optimistic Rollup | Asset migration, DeFi protocols |
| **LazAI** | 🔄 Testnet | AI-optimized blockchain | AI-powered dApps |
| **Ethereum** | ✅ Mainnet | EVM compatibility | Legacy dApp migration |
| **Polygon** | ✅ Mainnet | Low-cost transactions | Mass adoption dApps |
| **Arbitrum** | ✅ Mainnet | Layer 2 scaling | High-performance DeFi |

## Supported AI Providers

| Provider | Status | Features | Use Cases |
|----------|--------|----------|-----------|
| **Claude (Anthropic)** | ✅ Active | Smart contract generation, security analysis | DeFi protocols, complex contracts |
| **GPT-4 (OpenAI)** | ✅ Active | Code completion, documentation | dApp development, testing |
| **Gemini (Google)** | ✅ Active | Multimodal analysis, code review | UI components, visual analysis |
| **DeepSeek** | ✅ Active | Code optimization, gas efficiency | Performance-critical contracts |
| **Qwen (Alibaba)** | ✅ Active | Multi-language support, testing | International dApps |

## Contributing

[![Contributors](https://img.shields.io/github/contributors/JustineDevs/Hyperkit-Agent.svg)](https://github.com/JustineDevs/Hyperkit-Agent/graphs/contributors)
[![Issues](https://img.shields.io/github/issues/JustineDevs/Hyperkit-Agent.svg)](https://github.com/JustineDevs/Hyperkit-Agent/issues)
[![Pull Requests](https://img.shields.io/github/issues-pr/JustineDevs/Hyperkit-Agent.svg)](https://github.com/JustineDevs/Hyperkit-Agent/pulls)

We welcome contributions from the HyperKit community! Please see our [Contributing Guide](CONTRIBUTION.md) for details.

### Quick Start for Contributors

1. **Fork the repository**
   ```bash
   git clone https://github.com/JustineDevs/Hyperkit-Agent.git
   cd hyperkit-agent
   ```

2. **Set up development environment**
   ```bash
   pip install -e .[dev]
   pre-commit install
   ```

3. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```

4. **Make your changes and test**
   ```bash
   pytest
   hyperagent test --contracts
   ```

5. **Create a changeset**
   ```bash
   npm run changeset:add
   ```

6. **Submit a Pull Request**

### Version Management with Changesets

[![Changesets](https://img.shields.io/badge/changesets-enabled-blue.svg)](https://github.com/changesets/changesets)

HyperKit uses [Changesets](https://github.com/changesets/changesets) for version management and changelog generation.

#### Creating Changesets

When making changes, create a changeset to document what changed:

```bash
npm run changeset:add
```

#### Release Process

Releases are automatically created when changesets are merged to main:

1. **Changesets are consumed** and version numbers updated
2. **Changelog entries** are generated automatically
3. **Packages are published** to npm/PyPI
4. **GitHub releases** are created with changelog

## License

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

This project is licensed under the MIT License - see the [LICENSE](LICENSE.md) file for details.

## Roadmap

### Month 1: Foundation & AI Generation
- [x] Project rebranding and documentation
- [x] AI-powered smart contract generation
- [x] HyperKit modular UI system
- [x] Visual dashboard beta
- [x] Python SDK v0.1.0

### Month 2: Expansion & CLI Tools
- [x] CLI tool for project scaffolding
- [x] DeFi primitives development
- [x] Cross-chain bridge integration
- [x] Developer onboarding program
- [x] Partnership activations

### Month 3: Community & Features
- [ ] Vault and swap contracts
- [ ] Governance system beta
- [ ] Community leaderboard
- [ ] Video tutorials and workshops
- [ ] Feature request triage

### Month 4: Security & Governance
- [ ] External security audits
- [ ] Governance voting system
- [ ] Multi-chain integration
- [ ] HyperKit hackathon
- [ ] Advanced documentation

### Month 5: Mainnet Preparation
- [ ] Release candidate delivery
- [ ] Mainnet bridge contracts
- [ ] Public beta launch
- [ ] Grant program launch
- [ ] Partnership expansion

### Month 6: Public Launch
- [ ] HyperKit v1.0 GA
- [ ] Developer feedback system
- [ ] Reference integrations
- [ ] Launch announcement
- [ ] Community spotlight

## Technical Reports

### Integration & Testing Reports
- **[Workflow Behavior Report](hyperkit-agent/REPORTS/WORKFLOW_BEHAVIOR_REPORT.md)**: Complete analysis of the 5-stage workflow system
- **[Testing Results Report](hyperkit-agent/REPORTS/TESTING_RESULTS_REPORT.md)**: Comprehensive testing results and performance metrics
- **[Foundry Integration Report](hyperkit-agent/REPORTS/FOUNDRY_INTEGRATION_REPORT.md)**: Multi-chain deployment integration details
- **[Audit System Enhancement Report](hyperkit-agent/REPORTS/AUDIT_SYSTEM_ENHANCEMENT_REPORT.md)**: Enhanced vulnerability detection and security analysis
- **[Complete Integration Report](hyperkit-agent/REPORTS/INTEGRATION_REPORT.md)**: Full integration overview and production readiness

### Key Features Implemented
- **Interactive Audit Confirmation**: User-friendly security controls for high-severity issues
- **Smart Contract Naming**: Meaningful contract names and organized file structure
- **Command-Based Organization**: Logical artifact organization by command type
- **Foundry Integration**: Multi-chain deployment with Windows, Linux, macOS support
- **Enhanced Audit System**: Comprehensive vulnerability detection for local and deployed contracts
- **Error Handling**: Robust failure recovery and simulation mode
- **Cross-Platform Support**: Full compatibility across operating systems

## Acknowledgments

- Thanks to all contributors who help make HyperKit better
- Special thanks to the Hyperion and Andromeda communities
- Web3 and DeFi developers for inspiration and feedback
- AI and open-source communities for their continuous support
- [Metis Protocol](https://docs.hyperionkit.xyz/) for Optimistic Rollup technology
- [Hyperion Protocol](https://docs.hyperionkit.xyz/) for decentralized spatial blockchain network

---

**Made with ❤️ by the HyperKit Team**

[Website](https://hyperionkit.xyz) • [Documentation](https://docs.hyperionkit.xyz/) • [Discord](https://discord.gg/hyperionkit) • [Twitter](https://twitter.com/hyperionkit)