# Contributing to HyperKit AI Agent

Thank you for your interest in contributing to HyperKit! This document provides guidelines and instructions for contributing.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Code Standards](#code-standards)
- [Testing Requirements](#testing-requirements)
- [Pull Request Process](#pull-request-process)
- [Security Guidelines](#security-guidelines)

## 🤝 Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on what's best for the community
- Show empathy towards other community members

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+ (for versioning scripts)
- Foundry (for Solidity development)
- Git

### Setup

```bash
# Clone the repository
git clone https://github.com/JustineDevs/Hyperkit-Agent.git
cd Hyperkit-Agent/hyperkit-agent

# Install dependencies
pip install -e .[dev]

# Install Foundry (if not already installed)
curl -L https://foundry.paradigm.xyz | bash
foundryup

# Install OpenZeppelin contracts
forge install OpenZeppelin/openzeppelin-contracts

# Run tests to verify setup
pytest tests/ -v
forge test
```

## 🔄 Development Workflow

### Branch Strategy

- `main` - Production-ready code
- `develop` - Integration branch for features
- `feature/*` - New features
- `fix/*` - Bug fixes
- `docs/*` - Documentation updates

### Making Changes

1. **Fork the repository**
2. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes**
4. **Write/update tests**
5. **Run the full test suite**:
   ```bash
   pytest tests/ -v --cov
   forge test
   ```
6. **Commit your changes**:
   ```bash
   git commit -m "feat: add awesome feature"
   ```
7. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```
8. **Create a Pull Request**

## 📝 Code Standards

### Python Code Style

- Follow PEP 8
- Use Black for formatting: `black hyperkit-agent/`
- Use isort for imports: `isort hyperkit-agent/`
- Use type hints
- Maximum line length: 120 characters

### Solidity Code Style

- Follow Solidity style guide
- Use Solidity 0.8.20+
- Include NatSpec comments
- Use named imports from OpenZeppelin
- Run `forge fmt` before committing

### Naming Conventions

- **Python**: `snake_case` for functions/variables, `PascalCase` for classes
- **Solidity**: `PascalCase` for contracts, `camelCase` for functions
- **Files**: `kebab-case` for file names

### Documentation

- Document all public APIs
- Include docstrings for all functions/classes
- Update README.md if adding new features
- Add examples for complex functionality

## 🧪 Testing Requirements

### Required Tests

All contributions must include:

1. **Unit Tests**: Test individual functions/methods
2. **Integration Tests**: Test component interactions
3. **Security Tests**: For security-sensitive code
4. **Contract Tests**: For Solidity changes

### Test Coverage

- Minimum 80% code coverage for Python
- All critical paths must be tested
- Include edge cases and error conditions

### Running Tests

```bash
# Run Python tests
pytest tests/ -v --cov=hyperkit-agent

# Run Solidity tests
cd hyperkit-agent && forge test -vvv

# Run specific test file
pytest tests/test_specific.py -v

# Run with debugging
pytest tests/ -v -s
```

## 🔀 Pull Request Process

### Before Submitting

- [ ] All tests pass
- [ ] Code is formatted (black, isort)
- [ ] No linter errors (flake8)
- [ ] Documentation is updated
- [ ] Commit messages follow convention
- [ ] No merge conflicts with main

### PR Title Format

Use conventional commits:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `test:` - Test additions/changes
- `refactor:` - Code refactoring
- `chore:` - Maintenance tasks

Example: `feat: add batch audit functionality`

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
Describe testing performed

## Checklist
- [ ] Tests pass
- [ ] Code formatted
- [ ] Documentation updated
- [ ] No security issues
```

### Review Process

1. Automated checks must pass (CI/CD)
2. At least one maintainer approval required
3. No unresolved conversations
4. All requested changes addressed

## 🔒 Security Guidelines

### Security Best Practices

- Never commit secrets or API keys
- Use environment variables for sensitive data
- Follow principle of least privilege
- Validate all user inputs
- Use parameterized queries
- Keep dependencies updated

### Reporting Security Issues

**DO NOT** open a public issue for security vulnerabilities.

Instead, email: security@hyperkit.dev

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

### Security Testing

Run security scans before submitting:

```bash
# Python security scan
bandit -r hyperkit-agent/

# Dependency check
safety check

# Solidity security analysis
cd hyperkit-agent && slither .
```

## 📦 Adding Dependencies

### Python Dependencies

1. Add to `pyproject.toml` under `dependencies`
2. Pin version ranges appropriately
3. Test with `pip install -e .`
4. Update `requirements.txt`
5. Document why the dependency is needed

### Solidity Dependencies

1. Use `forge install` for libraries
2. Update `foundry.toml` remappings
3. Document in README
4. Ensure compatibility with existing contracts

## 🐛 Bug Reports

### Before Reporting

- Check existing issues
- Verify it's reproducible
- Test on latest version

### Bug Report Template

```markdown
**Describe the bug**
Clear description

**To Reproduce**
Steps to reproduce:
1. Step 1
2. Step 2
3. Expected vs actual

**Environment**
- OS: [e.g., Ubuntu 22.04]
- Python: [e.g., 3.11]
- Version: [e.g., 4.1.11]

**Additional context**
Any other relevant information
```

## 💡 Feature Requests

### Feature Request Template

```markdown
**Problem Statement**
What problem does this solve?

**Proposed Solution**
How should it work?

**Alternatives Considered**
Other approaches you've thought about

**Additional Context**
Mockups, examples, etc.
```

## 📊 Performance Guidelines

- Profile code for bottlenecks
- Optimize critical paths
- Document performance considerations
- Include benchmarks for performance changes

## 🎓 Learning Resources

- [Solidity Documentation](https://docs.soliditylang.org/)
- [Web3.py Documentation](https://web3py.readthedocs.io/)
- [OpenZeppelin Contracts](https://docs.openzeppelin.com/contracts/)
- [Foundry Book](https://book.getfoundry.sh/)

## 📞 Getting Help

- GitHub Discussions for questions
- Discord for real-time chat
- Documentation for guides

## 🏆 Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md
- Credited in release notes
- Recognized in project documentation

## 📜 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to HyperKit! 🚀

