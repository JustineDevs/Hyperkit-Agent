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
| `hyperagent generate "Create a production-ready ERC20 staking contract with 1B token supply, 12% APY rewards, 7-day lock period, and ReentrancyGuard security"` | Generate smart contracts using AI from detailed natural language prompts |
| `hyperagent audit contracts/StakingContract.sol` | Audit smart contracts for security vulnerabilities with comprehensive vulnerability detection |
| `hyperagent audit 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb --network hyperion` | Audit deployed contracts by address with source code fetching and bytecode analysis |
| `hyperagent deploy contracts/StakingContract.sol --network hyperion --constructor-args "1000000000" "12" "7"` | Deploy smart contracts to blockchain networks with constructor arguments |
| `hyperagent workflow "Build a cross-chain ERC20 token bridge for Metis ↔ Hyperion with 0.5% bridge fee, multisig validation, and ECDSA signature verification" --test-only` | Complete end-to-end workflow: Generate → Audit → Deploy → Test |
| `hyperagent verify 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb --network hyperion` | Verify deployed contracts on block explorer with source code verification |
| `hyperagent interactive --address 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb` | Launch interactive development shell for real-time contract interaction and testing |
| `hyperagent status` | Check system status, connectivity, and AI provider availability |
| `hyperagent test` | Run comprehensive test suite including unit, integration, and security tests |

## Security Commands (NEW!) 🔒

| Command | Description |
|---------|-------------|
| `hyperagent check-address-security 0x742d35... --network hyperion` | Check reputation and risk score of blockchain address with multi-factor analysis |
| `hyperagent check-url-phishing https://example.com` | Detect phishing URLs with typosquatting and SSL certificate validation |
| `hyperagent scan-approvals 0xYourWallet --network hyperion` | Scan token approvals and detect unlimited approvals (ERC20/721/1155) |
| `hyperagent analyze-transaction --to 0xContract --from 0xWallet --network hyperion` | Run comprehensive security analysis on transaction with risk scoring |

## Other Commands

| Command | Description |
|---------|-------------|
| `hyperagent scaffold my-defi-protocol --type defi` | Generate full-stack dApp scaffolds with DeFi primitives and UI components |
| `hyperagent verify 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb --network hyperion` | Verify deployed contracts on block explorer with source code verification |
| `hyperagent dashboard` | Launch web-based visual dashboard for contract management and monitoring |
| `hyperagent generate "Create an NFT marketplace with 2.5% platform fee, 5% creator royalties, and bidding system"` | Generate complex smart contracts with specific business logic |
| `hyperagent audit https://hyperion-testnet-explorer.metisdevops.link/token/0x742d35... --network hyperion` | Audit contracts via explorer URLs with automatic address extraction |

## Features

### 🤖 AI Project Generation
- **Smart Contract Generation**: AI-powered creation of Solidity smart contracts
- **dApp Templates**: Pre-built templates for DeFi protocols, NFT marketplaces, and more
- **Code Validation**: Automated security scanning and code quality checks
- **Multi-Model Support**: Integration with Claude, GPT, Gemini, and other AI providers

### 🛡️ Wallet Security Extensions (NEW!)
- **Transaction Simulation Engine**: Pocket Universe-style pre-signature preview (1-3s execution)
- **Address Reputation Database**: GoPlus Security-style risk scoring (100K+ addresses)
- **Phishing Detection Module**: Scam Sniffer-style URL/domain analysis (290K+ domains)
- **Token Approval Management**: Revoke.cash-style unlimited approval warnings
- **ML-Based Risk Scoring**: 95%+ accuracy phishing detection
- **Security Analysis Pipeline**: Multi-layer protection (90% reduction in phishing losses)

**Risk Reduction Metrics**:
- 90% reduction in phishing losses
- 85% reduction in approval exploits
- 75% reduction in MEV/sandwich attacks

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
   hyperagent generate "Create a production-ready ERC20 staking contract with 1B token supply, 12% APY rewards, 7-day lock period, and ReentrancyGuard security"
   ```

## Real-World Examples

### DeFi Staking Protocol
```bash
hyperagent generate "
Create a production-ready ERC20 staking contract with:
- 1 billion token supply
- 12% APY staking rewards distributed over 365 days
- Minimum stake: 1000 tokens
- Lock-in period: 7 days (penalty: 10% if withdrawn early)
- Max stake per user: 1M tokens (anti-whale)
- Reward distribution: Monthly snapshots
- Owner functions: pause staking, adjust APY, withdraw rewards
- Security: ReentrancyGuard, SafeMath, checks-effects-interactions pattern
- Use OpenZeppelin ERC20, Ownable, ReentrancyGuard
- Compatible with Metis mainnet (chain ID: 1088)
"
```

### Cross-Chain Token Bridge
```bash
hyperagent generate "
Build a cross-chain ERC20 token bridge for Metis ↔ Hyperion with:
- Source token: LINK (0x... on Metis mainnet)
- Bridge fee: 0.5% (deducted from amount)
- Max transfer per tx: 1M tokens
- Minimum transfer: 100 tokens
- Validator set: 3 out of 5 validators must sign (multisig)
- Signature verification using ECDSA (OpenZeppelin)
- Nonce tracking to prevent replay attacks
- Events: BridgeInitiated, BridgeClaimed, ValidatorAdded
- Admin functions: addValidator, removeValidator, updateFee
- Metadata: chainId, block timestamp for cross-chain verification
- Deployed on both Metis (1088) and Hyperion (133717)
"
```

### NFT Marketplace
```bash
hyperagent generate "
Build an NFT marketplace contract 'HyperMarket' with:
- Base contract: ERC721 for NFTs
- Listing functions: listNFT(tokenId, price, duration), unlistNFT(tokenId), buyNFT(tokenId)
- Bidding system: placeBid(tokenId, bidAmount), acceptBid(tokenId, bidderAddress)
- Fees: 2.5% platform fee on sales
- Royalties: Creator gets 5% of every sale
- Events: Listed, Sold, BidPlaced, BidAccepted
- Admin: setFeePercentage, withdrawFees, emergencyPause
- Escrow: Funds held in contract until transfer confirmed
- Safety: NonReentrant, checks-effects-interactions
- Compatibility: Metis (1088) and Hyperion (133717)
"
```

## Complete Workflow Example

### 1. Generate a DeFi Protocol
```bash
hyperagent generate "
Create a production-ready ERC20 staking contract with:
- 1 billion token supply
- 12% APY staking rewards distributed over 365 days
- Minimum stake: 1000 tokens
- Lock-in period: 7 days (penalty: 10% if withdrawn early)
- Max stake per user: 1M tokens (anti-whale)
- Security: ReentrancyGuard, SafeMath, checks-effects-interactions pattern
- Use OpenZeppelin ERC20, Ownable, ReentrancyGuard
- Compatible with Metis mainnet (chain ID: 1088)
"
```

### 2. Audit for Security Vulnerabilities
```bash
hyperagent audit contracts/StakingContract.sol
# Output: CRITICAL severity with detailed vulnerability findings
```

### 3. Deploy to Blockchain
```bash
hyperagent deploy contracts/StakingContract.sol \
  --network hyperion \
  --constructor-args "1000000000" "12" "7"
# Output: Contract deployed at 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb
```

### 4. Verify on Explorer
```bash
hyperagent verify 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb --network hyperion
# Output: Contract verified and source code published
```

### 5. Test Interactively
```bash
hyperagent interactive --address 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb
# Interactive shell for testing contract functions
```

### 6. Complete Workflow (All-in-One)
```bash
hyperagent workflow "
Build a cross-chain ERC20 token bridge for Metis ↔ Hyperion with:
- Bridge fee: 0.5% (deducted from amount)
- Validator set: 3 out of 5 validators must sign (multisig)
- Signature verification using ECDSA (OpenZeppelin)
- Nonce tracking to prevent replay attacks
- Events: BridgeInitiated, BridgeClaimed, ValidatorAdded
" --test-only
# Complete: Generate → Audit → Deploy → Test
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
- **[Audit Accuracy Enhancement Report](hyperkit-agent/REPORTS/AUDIT_ACCURACY_ENHANCEMENT_REPORT.md)**: Fixed false positive reporting and confidence tracking
- **[Audit Reliability Enhancement Report](hyperkit-agent/REPORTS/AUDIT_RELIABILITY_ENHANCEMENT_REPORT.md)**: Fixed critical infrastructure gaps and achieved 87.5% accuracy
- **[Complete Integration Report](hyperkit-agent/REPORTS/INTEGRATION_REPORT.md)**: Full integration overview and production readiness

### Key Features Implemented
- **Interactive Audit Confirmation**: User-friendly security controls for high-severity issues
- **Smart Contract Naming**: Meaningful contract names and organized file structure
- **Command-Based Organization**: Logical artifact organization by command type
- **Foundry Integration**: Multi-chain deployment with Windows, Linux, macOS support
- **Enhanced Audit System**: Comprehensive vulnerability detection for local and deployed contracts
- **Audit Accuracy Enhancement**: Honest confidence scoring and false positive reduction
- **Audit Reliability Enhancement**: Multi-tool consensus scoring with 87.5% accuracy benchmark
- **Multi-Source Verification**: Explorer APIs, Sourcify, and bytecode analysis with confidence tracking
- **Human Review Integration**: Automatic escalation for critical findings requiring expert analysis
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