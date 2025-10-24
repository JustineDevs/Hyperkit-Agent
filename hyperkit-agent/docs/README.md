# Developer Documentation (Internal)

This directory is for contributors and maintainers of `hyperkit-agent`.

## 📚 Key Files

- **[DEVELOPER_GUIDE.md](./DEVELOPER_GUIDE.md)** → Engineering instructions, SDK & architecture
- **[CLI_REFERENCE.md](./CLI_REFERENCE.md)** → Reference for CLI commands
- **[API_REFERENCE.md](./API_REFERENCE.md)** → Python/Node SDK info
- **[TESTING_GUIDE.md](./TESTING_GUIDE.md)** → Unit & integration tests
- **[TROUBLESHOOTING.md](./TROUBLESHOOTING.md)** → Common issues and solutions
- **[ARCHITECTURE.md](./ARCHITECTURE.md)** → System architecture and design
- **[SECURITY.md](./SECURITY.md)** → Security guidelines and best practices

## 🏗️ Architecture Overview

### **Core Components**
- **`core/`** - Core agent logic and configuration
- **`services/`** - Service modules (generation, audit, deployment, etc.)
- **`cli/`** - Command-line interface
- **`utils/`** - Utility functions and helpers

### **Service Modules**
- **`generation/`** - Smart contract generation
- **`audit/`** - Security auditing
- **`deployment/`** - Contract deployment
- **`verification/`** - Contract verification
- **`testing/`** - Contract testing
- **`monitoring/`** - Transaction monitoring

## 🚀 Quick Start for Developers

### **Setup Development Environment**
```bash
# Clone repository
git clone https://github.com/JustineDevs/HyperAgent.git
cd HyperAgent

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Setup development environment
./scripts/setup-dev.sh
```

### **Running Tests**
```bash
# Unit tests
python -m pytest tests/unit/

# Integration tests
python -m pytest tests/integration/

# All tests
python -m pytest
```

### **Code Quality**
```bash
# Linting
python -m flake8 hyperkit-agent/
python -m pylint hyperkit-agent/

# Type checking
python -m mypy hyperkit-agent/

# Formatting
python -m black hyperkit-agent/
```

## 📖 Documentation Navigation

- **Public Docs** ([../../docs/](../../docs/)) → User-facing documentation
- **Developer Docs** (this directory) → Technical implementation
- **Source Code** ([../](../)) → Main codebase

## 🔗 External Resources

- **GitHub Repository**: [HyperAgent](https://github.com/JustineDevs/HyperAgent)
- **Issue Tracker**: [Issues](https://github.com/JustineDevs/HyperAgent/issues)
- **Discussions**: [Discussions](https://github.com/JustineDevs/HyperAgent/discussions)
- **Contributing Guide**: [../../docs/CONTRIBUTING.md](../../docs/CONTRIBUTING.md)
