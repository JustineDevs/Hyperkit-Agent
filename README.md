<div align="center">

<img src="public/ascii/ascii-art-Hyperagent.png" alt="HyperAgent" width="800">

</div>

<!-- VERSION_PLACEHOLDER -->
**Version**: 1.6.7  
**Last Updated**: 2025-01-25  
**Commit**: Latest
<!-- /VERSION_PLACEHOLDER -->

> **Status Notice**  
> This system is in active development. While IPFS RAG features are production-ready, core deployment features have known limitations. See [HONEST_STATUS_ASSESSMENT.md](https://github.com/JustineDevs/Hyperkit-Agent/blob/devlog/hyperkit-agent/REPORTS/HONEST_STATUS_ASSESSMENT.md) for full details. Use for development and partnerships, not unattended production deployments.

[![Coverage](https://codecov.io/gh/JustineDevs/Hyperkit-Agent/branch/main/graph/badge.svg)](https://codecov.io/gh/JustineDevs/Hyperkit-Agent)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Solidity 0.8.20+](https://img.shields.io/badge/solidity-0.8.20+-lightgrey.svg)](https://soliditylang.org/)
[![Node.js 18+](https://img.shields.io/badge/node-18+-green.svg)](https://nodejs.org/)
[![Contributors](https://img.shields.io/github/contributors/JustineDevs/Hyperkit-Agent)](https://github.com/JustineDevs/Hyperkit-Agent/graphs/contributors)
[![Issues](https://img.shields.io/github/issues/JustineDevs/Hyperkit-Agent)](https://github.com/JustineDevs/Hyperkit-Agent/issues)
[![Pull Requests](https://img.shields.io/github/issues-pr/JustineDevs/Hyperkit-Agent)](https://github.com/JustineDevs/Hyperkit-Agent/pulls)
[![Status](https://img.shields.io/badge/status-active--development-yellow.svg)](https://github.com/JustineDevs/Hyperkit-Agent/blob/devlog/hyperkit-agent/REPORTS/HONEST_STATUS_ASSESSMENT.md)

---

## Overview

HyperAgent is an AI-powered platform that streamlines smart contract development, security auditing, and deployment on Hyperion testnet. By combining Large Language Models (LLMs), Retrieval-Augmented Generation (RAG), and blockchain technology, HyperAgent automates the entire smart contract lifecycle—from natural language prompts to production-ready, audited, and deployed contracts.

### Key Features

- **AI-First Development**: Generate production-ready smart contracts from natural language descriptions
- **Multi-Layer Security**: Comprehensive auditing with Slither, Mythril, and AI analysis with consensus scoring
- **Hyperion Testnet**: Exclusive deployment target with automatic verification on block explorers
- **5-Stage Workflow**: Complete automation from generation through testing
- **Self-Healing System**: Automatic dependency installation, error recovery, and retry logic
- **IPFS RAG Integration**: Template-based generation using IPFS Pinata for best practices
- **Zero-Config Setup**: Minimal manual configuration required

---

## Quick Start

### Prerequisites

| Requirement | Version | Installation |
|-------------|---------|--------------|
| Python | 3.10-3.12 | [python.org](https://python.org/downloads/) |
| Node.js | 18+ | [nodejs.org](https://nodejs.org/) |
| Foundry | Latest | `curl -L https://foundry.paradigm.xyz \| bash && foundryup` |
| Git | Latest | [git-scm.com](https://git-scm.com/) |

### Installation

```bash
# 1. Clone repository
git clone https://github.com/JustineDevs/Hyperkit-Agent.git
cd Hyperkit-Agent/hyperkit-agent

# 2. Install Python dependencies
pip install -e .

# 3. Install Foundry
curl -L https://foundry.paradigm.xyz | bash
foundryup

# 4. Configure environment
cp env.example .env
# Edit .env with your API keys

# 5. Run Doctor preflight check (auto-installs OpenZeppelin)
hyperagent doctor

# 6. Verify installation
hyperagent --help
hyperagent version
hyperagent status
```

### Environment Configuration

Create `.env` file in `hyperkit-agent/` directory:

```env
# AI Provider API Keys (at least one required)
GOOGLE_API_KEY=your_google_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Blockchain Configuration
DEFAULT_PRIVATE_KEY=your_private_key_here
DEFAULT_NETWORK=hyperion

# Network RPC URLs
HYPERION_RPC_URL=https://hyperion-testnet.metisdevops.link

# IPFS Pinata (for RAG templates)
PINATA_API_KEY=your_pinata_api_key
PINATA_SECRET_KEY=your_pinata_secret_key

# Security Settings
ENABLE_AUDIT=true
ENABLE_VERIFICATION=true
LOG_LEVEL=INFO
```

---

## Project Status

| Component | Status | Version | Notes |
|-----------|--------|---------|-------|
| **Core System** | Production Ready | v1.6.7 | All critical systems operational |
| **AI Generation** | Functional | v1.6.7 | Multi-provider support (Google, OpenAI, Anthropic) |
| **Security Auditing** | Functional | v1.6.7 | Multi-source consensus + batch auditing |
| **Deployment Pipeline** | Functional | v1.6.7 | Foundry integration complete |
| **Verification System** | Functional | v1.6.7 | Hyperion explorer integration |
| **Testing Framework** | Functional | v1.6.7 | Comprehensive test coverage |
| **CI/CD Pipeline** | Active | v1.6.7 | Multi-Python version testing |
| **Documentation** | Complete | v1.6.7 | Production-grade documentation |
| **Alith SDK** | Production | v1.6.7 | AI agent for contract generation & auditing |
| **IPFS Pinata RAG** | Production | v1.6.7 | Exclusive RAG backend with 13 templates |

For detailed status assessment, see [HONEST_STATUS_ASSESSMENT.md](https://github.com/JustineDevs/Hyperkit-Agent/blob/devlog/hyperkit-agent/REPORTS/HONEST_STATUS_ASSESSMENT.md).

---

## Network Support

| Network | Chain ID | Status | RPC Endpoint | Explorer |
|---------|----------|--------|--------------|----------|
| **Hyperion Testnet** | 133717 | **EXCLUSIVE** | https://hyperion-testnet.metisdevops.link | [Explorer](https://hyperion-testnet-explorer.metisdevops.link) |

> **Important**: Hyperion is the **EXCLUSIVE** deployment target. All CLI commands are hardcoded to Hyperion testnet. Future network support (LazAI, Metis) is documentation only—see [ROADMAP.md](https://github.com/JustineDevs/Hyperkit-Agent/blob/devlog/hyperkit-agent/docs/ROADMAP.md).

---

## Core Capabilities

### AI Contract Generation

Generate production-ready smart contracts from natural language descriptions:

```bash
# Generate contract from prompt
hyperagent generate contract "Create an ERC20 token with 1M supply"

# Generate with template
hyperagent generate contract --template erc20 --name MyToken

# Complete workflow (generate → audit → deploy → verify → test)
hyperagent workflow run "Create a simple ERC20 token with 1M supply"
```

### Security Auditing

Multi-source security analysis with consensus scoring:

```bash
# Audit single contract
hyperagent audit contract --contract MyToken.sol --output report.json

# Batch audit directory
hyperagent audit batch --directory ./contracts --recursive --output ./reports

# Audit with severity filter
hyperagent audit contract --contract MyToken.sol --severity critical
```

**Security Pipeline:**
- Static analysis (Slither)
- Symbolic execution (Mythril)
- AI pattern recognition (GPT-4/Gemini)
- Consensus-based scoring
- Comprehensive reporting (JSON/Markdown/PDF/Excel)

### Deployment & Verification

Deploy contracts to Hyperion testnet with automatic verification:

```bash
# Deploy contract
hyperagent deploy --contract artifacts/MyToken.sol --args "MyToken" "MTK" 1000000

# Verify deployed contract
hyperagent verify contract 0xYourContractAddress

# Monitor system health
hyperagent monitor system
```

### Self-Healing System

HyperAgent automatically handles dependencies and errors:

- **Dependency Detection**: Parses contracts for imports (Solidity, npm, Python)
- **Auto-Installation**: Installs OpenZeppelin contracts automatically
- **Error Recovery**: Detects and fixes common compilation errors
- **Retry Logic**: Retries failed operations with automatic fixes
- **Doctor System**: Preflight validation with auto-repair

```bash
# Run Doctor preflight check
hyperagent doctor

# Check system status
hyperagent status
```

---

## RAG Template Integration

HyperAgent uses Retrieval-Augmented Generation (RAG) to enhance all CLI commands with real-world templates stored on IPFS via Pinata.

### Available Templates

| Category | Templates | Count |
|----------|-----------|-------|
| **Contracts** | ERC20, ERC721 | 2 |
| **DeFi** | Staking Pool, DAO Governance, DEX, Lending Pool | 4 |
| **NFT** | NFT Collection | 1 |
| **Audit** | Security Checklist, Gas Optimization | 2 |
| **Prompts** | Contract Generation, Style Prompts, Security Prompts | 3 |
| **Deployment** | Hardhat Deploy | 1 |

**Total**: 13 templates, all uploaded and verified on IPFS.

### Using RAG Templates

```bash
# Generate with RAG context (default)
hyperagent generate contract --type ERC20 --name MyToken

# Complete workflow with full RAG context
hyperagent workflow run "create pausable ERC20 token"
```

Templates are automatically fetched from IPFS and cached locally for offline use. See [RAG Template Documentation](https://github.com/JustineDevs/Hyperkit-Agent/blob/devlog/docs/RAG_TEMPLATES/README.md) for details.

---

## CLI Commands

### Generation Commands

| Command | Purpose | Example |
|---------|---------|---------|
| `generate contract` | Generate smart contract from prompt | `hyperagent generate contract "ERC20 token"` |
| `generate test` | Generate test suite | `hyperagent generate test MyContract.sol` |
| `generate docs` | Generate documentation | `hyperagent generate docs MyContract.sol` |

### Audit Commands

| Command | Purpose | Example |
|---------|---------|---------|
| `audit contract` | Audit single contract | `hyperagent audit contract --contract MyToken.sol` |
| `audit batch` | Audit multiple contracts | `hyperagent audit batch --directory ./contracts --recursive` |
| `audit report` | View audit report | `hyperagent audit report --report audit.json` |

### Deployment Commands

| Command | Purpose | Example |
|---------|---------|---------|
| `deploy` | Deploy contract to Hyperion | `hyperagent deploy --contract MyToken.sol` |
| `verify contract` | Verify on explorer | `hyperagent verify contract 0x123...` |
| `monitor system` | System health check | `hyperagent monitor system` |

### Workflow Commands

| Command | Purpose | Example |
|---------|---------|---------|
| `workflow run` | Execute full workflow | `hyperagent workflow run "Create ERC20 token"` |
| `workflow list` | Show available templates | `hyperagent workflow list` |
| `workflow status` | Check workflow status | `hyperagent workflow status <id>` |

### System Commands

| Command | Purpose | Example |
|---------|---------|---------|
| `doctor` | Run preflight validation | `hyperagent doctor` |
| `status` | Check system health | `hyperagent status` |
| `config` | Manage configuration | `hyperagent config list` |
| `version` | Show version information | `hyperagent version` |
| `limitations` | Show known limitations | `hyperagent limitations` |

---

## NPM Scripts

HyperAgent provides comprehensive npm scripts for version management, CLI access, and workflow automation.

### Version Management

```bash
npm run version:current        # Display current version
npm run version:check         # Check version consistency
npm run version:patch         # Bump patch version (auto-commits all changed files)
npm run version:minor         # Bump minor version
npm run version:major         # Bump major version
npm run version:complete      # Complete workflow: reports → version → hygiene
```

### Workflow Hygiene

```bash
npm run hygiene              # Run complete workflow hygiene (auto-handles uncommitted files)
npm run hygiene:dry-run      # Preview changes without modifications
npm run hygiene:push         # Run workflow and push to remote
```

The `hygiene` command automatically:
- Detects and stages uncommitted files
- Runs all formatting and generation scripts
- Syncs documentation between `main` and `devlog` branches
- Generates reports after sync
- Commits all changes automatically

### CLI Access

```bash
npm run hyperagent:status     # Check system status
npm run hyperagent:test       # Run E2E tests
npm run hyperagent:doctor     # Run Doctor preflight
```

### Documentation & Reports

```bash
npm run docs:update          # Update version in all documentation
npm run docs:audit           # Run documentation drift audit
npm run reports:organize     # Consolidate reports into category directories
npm run reports:status       # Generate CLI command inventory
```

See [package.json](./package.json) for complete script reference.

---

## Developer Tools

| Tool | Version | Purpose | Status |
|------|---------|---------|--------|
| **Foundry** | Latest | Solidity compilation and testing | Required |
| **Python** | 3.10-3.12 | Core runtime environment | Required |
| **Node.js** | 18+ | Package management and versioning | Required |
| **Git** | Latest | Version control | Required |
| **OpenZeppelin** | v5.0+ | Smart contract libraries | Auto-installed |
| **Slither** | Latest | Static analysis | Required |
| **Mythril** | Latest | Security analysis | Required |

---

## AI Providers

| Provider | Model | Purpose | API Key Required | Status |
|----------|-------|---------|------------------|--------|
| **Google Gemini** | gemini-pro | Contract generation, analysis | `GOOGLE_API_KEY` | Supported |
| **OpenAI** | gpt-4 | Advanced reasoning, auditing | `OPENAI_API_KEY` | Supported |
| **Anthropic Claude** | claude-3-sonnet | Code review, optimization | `ANTHROPIC_API_KEY` | Supported |
| **Alith SDK** | v1.6.7+ | AI-powered contract generation & auditing | `OPENAI_API_KEY` | Production |
| **IPFS Pinata RAG** | Latest | Template storage & retrieval | `PINATA_API_KEY` | Production |

---

## Security & Compliance

| Aspect | Implementation | Status |
|--------|----------------|--------|
| **Bug Bounty Program** | $50 - $5,000 rewards | Active |
| **Vulnerability Reporting** | 24-48hr response time | [SECURITY.md](./SECURITY.md) |
| **Security Scanning** | Bandit, Safety in CI/CD | Automated |
| **Dependency Auditing** | Automated CVE checks | Active |
| **Code Review** | Required for all PRs | Enforced |
| **Access Control** | Role-based permissions | Implemented |
| **Audit Trail** | All operations logged | Active |
| **Secrets Management** | Environment variables only | Enforced |

---

## Documentation

HyperAgent uses a dual-branch structure for optimal organization:

- **`main` branch**: Code + essential docs (~794 KB)
- **`devlog` branch**: Full documentation (~1.9 MB)

### Quick Links

**Essential Documentation (in main):**
- [Quick Start Guide](./hyperkit-agent/docs/GUIDE/QUICK_START.md)
- [Environment Setup](./hyperkit-agent/docs/GUIDE/ENVIRONMENT_SETUP.md)
- [Contributing Guide](./CONTRIBUTING.md)
- [Security Policy](./SECURITY.md)

**Full Documentation (in devlog):**
- [Implementation Status](https://github.com/JustineDevs/Hyperkit-Agent/blob/devlog/hyperkit-agent/REPORTS/HONEST_STATUS_ASSESSMENT.md)
- [Audit Reports](https://github.com/JustineDevs/Hyperkit-Agent/blob/devlog/hyperkit-agent/REPORTS/AUDIT/AUDIT.md)
- [Developer Guides](https://github.com/JustineDevs/Hyperkit-Agent/tree/devlog/hyperkit-agent/docs/TEAM)
- [Integration Docs](https://github.com/JustineDevs/Hyperkit-Agent/tree/devlog/hyperkit-agent/docs/INTEGRATION)

**Access devlog branch:**
```bash
git fetch origin devlog:devlog && git checkout devlog
# Or clone: git clone -b devlog <repo-url>
```

---

## Example Workflows

### Basic Token Creation

```bash
# Create ERC20 token
hyperagent workflow run "Create a simple ERC20 token with 1M supply"
```

### Advanced DeFi Contract

```bash
# Create staking pool
hyperagent workflow run "Create a staking contract with 10% APY and reward distribution"
```

### NFT Collection

```bash
# Create NFT collection
hyperagent workflow run "Create an ERC721 NFT collection with 10K supply and whitelist minting"
```

### Batch Security Audit

```bash
# Audit entire project
hyperagent audit batch --directory ./contracts --recursive --output ./security-reports --format json
```

---

## Testing

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test suites
pytest tests/test_rag.py          # All RAG tests (consolidated)
pytest tests/test_pinata.py      # All Pinata tests (consolidated)
pytest tests/unit/                # Unit tests
pytest tests/integration/         # Integration tests
pytest tests/e2e/                 # End-to-end tests

# Run with markers
pytest -m integration             # Integration tests only
pytest -m asyncio                 # Async tests only

# With coverage
pytest --cov=hyperkit-agent tests/
```

### Test Organization

- **Consolidated Test Files**: Related tests are organized into single files for better maintainability
- **Test Markers**: Use `@pytest.mark.integration` and `@pytest.mark.asyncio` for test categorization
- **Test Isolation**: Proper fixtures ensure tests don't interfere with each other

---

## Contributing

We welcome contributions from the community. Please see our [Contributing Guide](./CONTRIBUTING.md) for details.

### Quick Contribution Guide

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Make your changes
4. Run tests (`pytest tests/ -v`)
5. Commit your changes (`git commit -m 'Add AmazingFeature'`)
6. Push to the branch (`git push origin feature/AmazingFeature`)
7. Open a Pull Request

### Contribution Areas

- Bug fixes and improvements
- New features and enhancements
- Documentation improvements
- Test coverage expansion
- Security enhancements
- Network integrations

**Important**: All PRs must include documentation updates. See [CONTRIBUTING.md](./CONTRIBUTING.md) for complete guidelines.

---

## Roadmap

### Completed

- Core agent architecture
- Multi-source auditing
- Foundry integration
- Hyperion deployment
- Security extensions
- CI/CD pipeline
- E2E testing
- Documentation
- Batch auditing

### In Progress

- Template library expansion
- Advanced AI features
- Performance optimization

### Planned

- Additional network support (documentation only)
- Community building
- Advanced security features

---

## License

This project is licensed under the **MIT License** - see the [LICENSE.md](./LICENSE.md) file for details.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## Support & Community

- **Documentation**: [GitHub Docs](https://github.com/JustineDevs/Hyperkit-Agent)
- **Issues**: [GitHub Issues](https://github.com/JustineDevs/Hyperkit-Agent/issues)
- **Discord**: [Join Community](https://discord.com/invite/MDh7jY8vWe)
- **Twitter**: [@HyperKit](https://x.com/HyperionKit)
- **Security**: Hyperkitdev@gmail.com (for security issues)
- **Bug Bounty**: See [SECURITY.md](./SECURITY.md)

---

## Acknowledgments

### Technologies

- **Foundry** - Fast, portable, and modular toolkit for Ethereum development
- **OpenZeppelin** - Secure smart contract library
- **Google Gemini** - Advanced AI language model
- **OpenAI GPT-4** - State-of-the-art language understanding
- **Anthropic Claude** - Reliable AI assistant
- **Slither** - Static analysis framework
- **Mythril** - Security analysis tool

### Community

Special thanks to all contributors, security researchers, and community members who help make HyperAgent better every day.

---

<div align="center">

**Star us on GitHub if you find HyperAgent useful!**

[![GitHub stars](https://img.shields.io/github/stars/JustineDevs/Hyperkit-Agent?style=social)](https://github.com/JustineDevs/Hyperkit-Agent/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/JustineDevs/Hyperkit-Agent?style=social)](https://github.com/JustineDevs/Hyperkit-Agent/network/members)
[![GitHub watchers](https://img.shields.io/github/watchers/JustineDevs/Hyperkit-Agent?style=social)](https://github.com/JustineDevs/Hyperkit-Agent/watchers)

**HyperAgent** - Revolutionizing Smart Contract Development with AI

**Last Updated**: 2025-01-25 | **Version**: 1.6.7 | **Status**: Production Ready

</div>
