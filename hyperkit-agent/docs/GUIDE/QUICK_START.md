# HyperKit Agent - Quick Start

## 🚀 Installation

### One Command to Install Everything
```bash
npm run install:root
```

That's it! This installs **all packages** including `alith>=0.12.0` automatically.

## 📦 Alternative Installation Methods

### Basic Installation
```bash
cd hyperkit-agent
pip install -e .
```

### Development Installation (Recommended for Developers)
```bash
npm run install:dev
```

### Full Installation (Dev + Security Tools)
```bash
npm run install:all
```

## ✅ Verify Installation

```bash
# Check if it works
npm run hyperagent:help

# Check version
npm run hyperagent:version

# Check status
npm run hyperagent:status
```

## 🎯 Most Used Commands

### Running the Agent
```bash
npm run hyperagent              # Run the CLI
npm run hyperagent:help         # Show all commands
npm run hyperagent:generate     # Generate contracts
npm run hyperagent:audit        # Audit contracts
npm run hyperagent:deploy       # Deploy contracts
```

### Testing
```bash
npm run test                     # Run all tests
npm run test:units              # Unit tests only
npm run test:coverage           # Test with coverage
```

### Code Quality
```bash
npm run lint                     # Check code quality
npm run format                   # Format code
npm run type-check              # Type checking
```

## 📚 Documentation

- [Installation Guide](./INSTALLATION_GUIDE.md) - Complete installation instructions
- [Changes Summary](./CHANGES_SUMMARY.md) - What was fixed
- [Main README](./hyperkit-agent/README.md) - Full documentation
- [Troubleshooting](./hyperkit-agent/docs/TROUBLESHOOTING_GUIDE.md) - Fix common issues

## ⚡ Quick Reference

```bash
# Installation
npm run install:root             # Install from root
npm run install:dev              # Install with dev tools
npm run install:all              # Install with everything

# Testing
npm run test                     # All tests
npm run test:units               # Unit tests
npm run test:integration         # Integration tests

# Code Quality
npm run lint                     # Lint
npm run format                   # Format
npm run security                 # Security scan

# Version Management
npm run version:show             # Show version
npm run version:patch           # Bump patch
npm run version:minor           # Bump minor

# CLI Commands
npm run hyperagent               # Main CLI
npm run hyperagent:help          # Help
npm run hyperagent:version       # Version
npm run hyperagent:status        # Status
```

## 🎉 That's It!

You now have HyperKit Agent installed with all dependencies including `alith>=0.12.0`.

**No need to run `pip install alith>=0.12.0` separately!**

Everything is automatically installed when you run `npm run install:root`.

