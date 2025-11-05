# Installation Summary - Complete Dependency Overview

**Last Updated**: 2025-10-31  
**Version**: 1.5.14

## Quick Reference

### What `pip install -e .` Installs

When you run `pip install -e .` from the `hyperkit-agent` directory, **ALL Python packages** from `pyproject.toml` are installed:

#### Core Dependencies (Always Installed)
- ✅ **Alith SDK** (>=0.12.0) - AI agent framework for Web3
- ✅ **Web3 Libraries**: web3, eth-account, eth-utils, eth-keys, eth-typing
- ✅ **AI Providers**: OpenAI, Anthropic, Google Generative AI
- ✅ **IPFS Client**: ipfshttpclient (for RAG template storage)
- ✅ **Configuration**: pyyaml, jsonschema, python-dotenv
- ✅ **HTTP Libraries**: requests, httpx, aiohttp
- ✅ **Logging**: structlog, python-json-logger, loguru
- ✅ **Utilities**: click, rich, pydantic, tenacity, ratelimit, cachetools
- ✅ **Vector DB**: chromadb (for local vector storage)
- ✅ **Reporting**: reportlab, openpyxl (for PDF/Excel export)

#### Optional Extras
- `[dev]`: pytest, black, flake8, mypy, isort, pre-commit, bandit, safety
- `[security]`: slither-analyzer, mythril, bandit, safety
- `[docs]`: sphinx, sphinx-rtd-theme

### What Does NOT Get Installed by `pip install -e .`

| Component | Installation Method | Notes |
|-----------|---------------------|-------|
| **Foundry** | System installation | ⚠️ Required before workflows: `curl -L https://foundry.paradigm.xyz \| bash && foundryup` |
| **OpenZeppelin Contracts** | Auto-installed by agent | ✅ First workflow run or `hyperagent doctor` (creates `lib/` directory) |
| **Scripts** | Included in repo | ✅ Available after cloning (no installation needed) |
| **lib/ directory** | Auto-created | ✅ When OpenZeppelin is installed |
| **foundry.toml** | Included in repo | ✅ Configuration file (no installation needed) |

## Complete Installation Steps

```bash
# 1. Clone repository
git clone https://github.com/JustineDevs/Hyperkit-Agent.git
cd Hyperkit-Agent

# 2. Install Python dependencies (from hyperkit-agent directory)
cd hyperkit-agent
pip install -e .
# This installs ALL packages from pyproject.toml:
# - alith>=0.12.0, web3, OpenAI, Anthropic, Google AI, etc.
# - All utility libraries, IPFS client, vector DB, reporting tools
# No need to run 'pip install alith>=0.12.0' separately!

# 3. Install Foundry (system-level requirement)
curl -L https://foundry.paradigm.xyz | bash
foundryup
# Foundry is required for Solidity compilation
# Cannot be installed via pip - it's a system-level tool

# 4. Run Doctor to validate and auto-install OpenZeppelin
hyperagent doctor
# Doctor will:
# - Check all required tools (forge, python, node, npm)
# - Validate OpenZeppelin installation
# - Auto-install OpenZeppelin if missing (creates lib/ directory)
# - Fix Foundry/solc version mismatches
# - Clean git submodule issues

# 5. Verify installation
hyperagent status
hyperagent version
```

## Key Points

1. **`pip install -e .` installs ALL Python packages** - No need for separate `pip install alith` or `pip install -r requirements.txt`
2. **Foundry must be installed separately** - System-level tool, not a Python package
3. **OpenZeppelin auto-installs** - Agent handles this during first workflow or via Doctor
4. **Scripts are included** - No installation needed, already in repository
5. **lib/ directory auto-created** - When OpenZeppelin installs

## Troubleshooting

### "alith not found"
**Solution**: Make sure you ran `pip install -e .` from the `hyperkit-agent` directory:
```bash
cd hyperkit-agent
pip install -e .
```

### "OpenZeppelin not found"
**Solution**: Run Doctor to auto-install:
```bash
hyperagent doctor
```

### "forge not found"
**Solution**: Install Foundry (system-level):
```bash
curl -L https://foundry.paradigm.xyz | bash
foundryup
```

## Verification Checklist

After installation, verify everything is ready:

```bash
# Check Python packages
python -c "import alith; print('✅ Alith SDK installed')"
python -c "import web3; print('✅ Web3 installed')"
python -c "import openai; print('✅ OpenAI installed')"

# Check Foundry
forge --version

# Check Doctor
hyperagent doctor

# Check system status
hyperagent status
```

---

**For detailed installation instructions, see:**
- [Installation Guide](../../docs/INSTALLATION_GUIDE.md)
- [Environment Setup Guide](GUIDE/ENVIRONMENT_SETUP.md)
- [Quick Start Guide](GUIDE/QUICK_START.md)

