# HyperKit Agent - Installation Guide

## Quick Start

Install HyperKit Agent with all Python dependencies (including `alith>=0.12.0`) in one command. OpenZeppelin contracts and other Solidity dependencies are auto-installed by the agent.

### Option 1: From Root Directory (Recommended)
```bash
npm run install:root
```

### Option 2: Direct pip Installation
```bash
cd hyperkit-agent
pip install -e .
```

### Option 3: Install with Development Dependencies
```bash
npm run install:dev
# Or directly:
cd hyperkit-agent && pip install -e ".[dev]"
```

### Option 4: Install All Extras (Dev + Security)
```bash
npm run install:all
# Or directly:
cd hyperkit-agent && pip install -e ".[dev,security]"
```

## What Gets Installed

### Python Dependencies (via `pip install -e .`)

When you run `pip install -e .` from the `hyperkit-agent` directory, **all Python packages listed in `pyproject.toml` are automatically installed**, including:

- ✅ `alith>=0.12.0` (AI agent framework for Web3)
- ✅ All Web3 dependencies (web3, eth-account, eth-utils, eth-keys, eth-typing)
- ✅ All LLM providers (OpenAI, Anthropic, Google Generative AI)
- ✅ All core dependencies (click, rich, pydantic, python-dotenv, etc.)
- ✅ All utility libraries (ipfshttpclient, pyyaml, jsonschema, requests, httpx, aiohttp, etc.)
- ✅ Logging and monitoring (structlog, python-json-logger, loguru)
- ✅ Testing tools (if using `[dev]` extras: pytest, black, flake8, mypy, etc.)
- ✅ Security tools (if using `[security]` extras: slither-analyzer, mythril, bandit, safety)

**You do NOT need to run `pip install alith>=0.12.0` separately.**

### Non-Python Dependencies (Auto-Handled by Agent)

The following are **NOT** installed via `pip install -e .` but are automatically handled by the agent system:

#### Foundry & Solidity Tooling
- **Foundry**: Must be installed separately (system-level requirement)
  ```bash
  curl -L https://foundry.paradigm.xyz | bash
  foundryup
  ```
- **Foundry configuration**: `foundry.toml` is included in the repository
- **Solidity compiler**: Auto-installed/managed by Foundry

#### OpenZeppelin Contracts
- **Installation**: Automatically installed during first workflow run
- **Location**: `lib/openzeppelin-contracts/` (created automatically)
- **Method**: Uses `forge install` or direct `git clone` as fallback
- **Verification**: Doctor system validates installation

#### Scripts & Utilities
- **Doctor scripts**: `scripts/doctor.py` and `scripts/doctor.sh` (included in repo)
- **Dependency installer**: `scripts/dependency_install.sh` (included in repo)
- **CI/CD scripts**: `scripts/ci/` directory (included in repo)
- **All scripts**: Available immediately after cloning repository

#### Directory Structure
- **lib/**: Created automatically when OpenZeppelin is installed
- **contracts/**: Included in repository
- **artifacts/**: Created automatically during workflow run
- **logs/**: Created automatically during runtime

### Summary: What Requires Manual Installation?

| Component | Installation Method | Notes |
|-----------|---------------------|-------|
| **Python packages** | `pip install -e .` | ✅ All from pyproject.toml |
| **Foundry** | System installation | ⚠️ Required before workflows |
| **OpenZeppelin** | Auto-installed by agent | ✅ First workflow run or `hyperagent doctor` |
| **Scripts** | Included in repo | ✅ Available after clone |
| **lib/ directory** | Auto-created | ✅ When OpenZeppelin installs |

### Complete Installation Flow

```bash
# 1. Install Python dependencies
cd hyperkit-agent
pip install -e .

# 2. Install Foundry (system-level, one-time)
curl -L https://foundry.paradigm.xyz | bash
foundryup

# 3. Run Doctor to validate and auto-install OpenZeppelin
hyperagent doctor
# Or let it install automatically on first workflow run

# 4. Verify everything is ready
hyperagent status
```

## Available npm Scripts

### Installation Commands
- `npm run install:root` - Basic installation from root
- `npm run install:dev` - Install with development dependencies
- `npm run install:all` - Install with dev and security tools
- `npm run install:prod` - Production installation

### Testing Commands
- `npm run test` - Run all tests
- `npm run test:coverage` - Run tests with coverage
- `npm run test:units` - Run unit tests only
- `npm run test:integration` - Run integration tests
- `npm run test:e2e` - Run end-to-end tests

### Code Quality
- `npm run lint` - Run flake8 linter
- `npm run format` - Format code with black
- `npm run format:check` - Check code formatting
- `npm run type-check` - Run mypy type checking
- `npm run security` - Run security analysis
- `npm run security:contracts` - Run contract security analysis

### CLI Commands
- `npm run hyperagent` - Run the CLI
- `npm run hyperagent:help` - Show CLI help
- `npm run hyperagent:status` - Show system status
- `npm run hyperagent:version` - Show version

### Documentation
- `npm run docs:build` - Build documentation
- `npm run docs:serve` - Serve documentation locally

### Version Management
- `npm run version:current` - Show current version
- `npm run version:patch` - Bump patch version
- `npm run version:minor` - Bump minor version
- `npm run version:major` - Bump major version

### Workflow Hygiene ⭐
- `npm run hygiene` - Run complete workflow hygiene (docs, reports, branch sync)
- `npm run hygiene:dry-run` - Preview what would be done
- `npm run hygiene:push` - Run workflow and push to remote

## Project Structure

```
HyperAgent/
├── package.json          # NPM scripts and project metadata
├── VERSION              # Version file
├── hyperkit-agent/      # Main Python package
│   ├── pyproject.toml  # Python dependencies (including alith)
│   ├── core/           # Core functionality
│   ├── services/       # Service modules
│   ├── cli/           # CLI interface
│   ├── tests/         # Test suite
│   └── scripts/       # Utility scripts
└── docs/              # Documentation
```

## Doctor Preflight System

Before running your first workflow, it's recommended to run the **Doctor** preflight system to validate your environment:

```bash
# Run Doctor check (auto-fixes common issues)
hyperagent doctor

# Or run manually with auto-fix
cd hyperkit-agent
hyperagent doctor

# Report only (no fixes)
hyperagent doctor --no-fix
```

**What Doctor Checks:**
- ✅ Required tools (forge, python, node, npm)
- ✅ OpenZeppelin installation and version compatibility
- ✅ Foundry configuration (solc version)
- ✅ Git submodule issues (auto-fixes broken entries)

**Auto-Fix Capabilities:**
- Installs missing OpenZeppelin contracts
- Fixes version mismatches in `foundry.toml`
- Cleans broken git submodule entries
- Removes submodule entries from `.gitignore` (wrong location)

See [`hyperkit-agent/docs/GUIDE/DOCTOR_PREFLIGHT.md`](../hyperkit-agent/docs/GUIDE/DOCTOR_PREFLIGHT.md) for detailed documentation.

---

## Troubleshooting

### Issue: "alith not found"
**Solution**: Make sure you're installing from the `hyperkit-agent` directory:
```bash
cd hyperkit-agent
pip install -e .
```

### Issue: "Permission denied"
**Solution**: Use the `--user` flag:
```bash
pip install -e . --user
```

### Issue: "Package conflicts"
**Solution**: Create a fresh virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e .
```

### Issue: "Missing dependencies"
**Solution**: Use the `install:all` command to install all extras:
```bash
npm run install:all
```

### Issue: "OpenZeppelin not found" or "git submodule errors"
**Solution**: Run the Doctor system to auto-fix:
```bash
hyperagent doctor
# Or manually:
cd hyperkit-agent
hyperagent doctor
```

The Doctor system will:
- Detect missing OpenZeppelin contracts
- Auto-install via `forge install` or direct `git clone`
- Fix broken git submodule references
- Clean up `.gitignore` entries if needed

## Development Setup

For development with all tools:

```bash
# Clone the repository
git clone https://github.com/JustineDevs/Hyperkit-Agent.git
cd Hyperkit-Agent

# Install with all development tools
npm run install:all

# Run tests to verify installation
npm run test

# Check the CLI
npm run hyperagent:help
```

## Production Setup

For production deployment:

```bash
# Install production dependencies only
npm run install:prod

# Build the package
npm run build

# Run the CLI
npm run hyperagent
```

## Complete Dependency Overview

### What `pip install -e .` Installs

The `pip install -e .` command installs **only Python packages** from `hyperkit-agent/pyproject.toml`:

#### Core Python Dependencies (Always Installed)
- **Web3 & Blockchain**: web3, eth-account, eth-utils, eth-keys, eth-typing
- **AI/LLM**: OpenAI, Anthropic, Google Generative AI
- **Alith SDK**: alith>=0.12.0 (AI agent framework for Web3)
- **IPFS**: ipfshttpclient (for RAG template storage)
- **Configuration**: pyyaml, jsonschema, python-dotenv
- **HTTP**: requests, httpx, aiohttp
- **Logging**: structlog, python-json-logger, loguru
- **Utilities**: click, rich, pydantic, tenacity, ratelimit, cachetools
- **Vector DB**: chromadb (for local vector storage)
- **Reporting**: reportlab, openpyxl (for PDF/Excel export)

### Optional Extras
- `dev`: Testing and development tools (pytest, black, flake8, mypy, etc.)
- `security`: Security analysis tools (slither, mythril, bandit, safety)
- `docs`: Documentation tools (sphinx, sphinx-rtd-theme)

## Important Notes

### What `pip install -e .` Does
- ✅ Installs **ALL Python packages** from `pyproject.toml` (alith, web3, OpenAI, Anthropic, Google AI, etc.)
- ✅ Installs CLI command (`hyperagent`) globally or in virtual environment
- ❌ **Does NOT install**: Foundry (system-level tool), OpenZeppelin contracts (auto-installed by agent), scripts (included in repo)

### What Gets Auto-Installed by Agent
- ✅ **OpenZeppelin contracts**: Auto-installed during first workflow run or via `hyperagent doctor` (creates `lib/openzeppelin-contracts/`)
- ✅ **lib/ directory**: Auto-created when OpenZeppelin is installed
- ✅ **npm packages**: Auto-installed if contracts use Node.js dependencies

### What Requires Manual Installation
- ⚠️ **Foundry**: Must install separately via `curl -L https://foundry.paradigm.xyz | bash && foundryup`
- ⚠️ **Python**: Must be Python 3.10-3.12 (system-level requirement)
- ⚠️ **Node.js**: Must be Node.js 18+ (system-level requirement)
- ⚠️ **Git**: Must be installed (system-level requirement)

### What's Already Included
- ✅ **All scripts**: `scripts/doctor.py`, `scripts/dependency_install.sh`, `scripts/ci/`, etc. (included in repository)
- ✅ **Foundry config**: `foundry.toml` (included in repository)
- ✅ **Contract templates**: `contracts/` directory (included in repository)

## Support

For issues or questions:
- Check the [Troubleshooting Guide](hyperkit-agent/docs/TROUBLESHOOTING_GUIDE.md)
- Review the [README](hyperkit-agent/README.md)
- Open an issue on [GitHub](https://github.com/JustineDevs/Hyperkit-Agent/issues)

