# HyperKit Agent - Installation Guide

## Quick Start

Install HyperKit Agent with all dependencies (including `alith>=0.12.0`) in one command:

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

When you run `pip install -e .` from the `hyperkit-agent` directory, **all packages listed in `pyproject.toml` are automatically installed**, including:

- ✅ `alith>=0.12.0` (AI agent framework for Web3)
- ✅ All Web3 dependencies (web3, eth-account, etc.)
- ✅ All LLM providers (OpenAI, Anthropic, Google)
- ✅ All core dependencies
- ✅ Configuration and utilities

**You do NOT need to run `pip install alith>=0.12.0` separately.**

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
- `npm run version:show` - Show current version
- `npm run version:patch` - Bump patch version
- `npm run version:minor` - Bump minor version
- `npm run version:major` - Bump major version

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

## Dependencies Included

The package includes all dependencies from `hyperkit-agent/pyproject.toml`:

### Core Dependencies (Always Installed)
- **Web3 & Blockchain**: web3, eth-account, eth-utils, eth-keys, eth-typing
- **AI/LLM**: OpenAI, Anthropic, Google Generative AI
- **Alith SDK**: alith>=0.12.0 (AI agent framework for Web3)
- **Configuration**: pyyaml, jsonschema, python-dotenv
- **HTTP**: requests, httpx, aiohttp
- **Logging**: structlog, python-json-logger, loguru
- **Utilities**: click, rich, pydantic, tenacity, ratelimit, cachetools

### Optional Extras
- `dev`: Testing and development tools (pytest, black, flake8, mypy, etc.)
- `security`: Security analysis tools (slither, mythril, bandit, safety)
- `docs`: Documentation tools (sphinx, sphinx-rtd-theme)

## Notes

- All commands now properly navigate to the `hyperkit-agent` directory
- The `pip install -e .` command from `hyperkit-agent` includes all packages
- No need to install `alith` separately - it's already in `pyproject.toml`
- The package.json scripts have been updated to reference correct paths
- Version management scripts work from the root directory

## Support

For issues or questions:
- Check the [Troubleshooting Guide](hyperkit-agent/docs/TROUBLESHOOTING_GUIDE.md)
- Review the [README](hyperkit-agent/README.md)
- Open an issue on [GitHub](https://github.com/JustineDevs/Hyperkit-Agent/issues)

