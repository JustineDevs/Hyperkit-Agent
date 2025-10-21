# Contributing to HyperKit

Thank you for your interest in contributing to HyperKit! This document provides guidelines and information for contributors to our Web3 development platform.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Contributing Process](#contributing-process)
- [Code Style and Standards](#code-style-and-standards)
- [Testing Guidelines](#testing-guidelines)
- [Documentation](#documentation)
- [Issue Reporting](#issue-reporting)
- [Pull Request Process](#pull-request-process)
- [Release Process](#release-process)

## Code of Conduct

This project adheres to a code of conduct that we expect all contributors to follow. Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md).

## Getting Started

### Prerequisites

- Python 3.9 or higher
- Git
- Node.js 16+ (for frontend development)
- Docker (optional, for containerized development)
- Hyperion/Andromeda wallet (for testing)
- Solidity knowledge (for smart contract contributions)

### Development Setup

1. **Fork the repository**
   ```bash
   git clone https://github.com/hyperionkit/hyperkit.git
   cd hyperkit
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install HyperKit**
   ```bash
   pip install -e .[dev]
   pip install -r requirements-dev.txt
   ```

4. **Set up environment variables**
   ```bash
   cp env.example .env
   # Edit .env with your API keys and wallet configuration
   ```

5. **Initialize HyperKit**
   ```bash
   hyperkit init --network hyperion-testnet
   ```

6. **Run tests**
   ```bash
   pytest tests/
   hyperkit test --contracts
   ```

## Contributing Process

### 1. Choose an Issue

- Look for issues labeled `good first issue`, `help wanted`, or `hyperkit`
- Check our milestone roadmap for priority features
- Comment on the issue to indicate you're working on it
- If you want to work on something not in the issues, please create one first

### 2. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/issue-number-description
```

### 3. Make Changes

- Follow our coding standards
- Write tests for new functionality
- Update documentation as needed
- Ensure all tests pass

### 4. Commit Changes

```bash
git add .
git commit -m "feat: add new HyperKit AI generation feature"
```

Use conventional commit messages:
- `feat:` for new features (AI generation, modules, contracts)
- `fix:` for bug fixes
- `docs:` for documentation changes
- `style:` for formatting changes
- `refactor:` for code refactoring
- `test:` for test changes
- `chore:` for maintenance tasks
- `contract:` for smart contract changes
- `module:` for HyperKit module changes
- `ai:` for AI generation improvements

### 5. Push and Create PR

```bash
git push origin feature/your-feature-name
```

Then create a pull request using our [PR template](.github/PULL-REQUEST-TEMPLATE.md).

## Code Style and Standards

### Python Code

- Follow PEP 8 style guide
- Use type hints where appropriate
- Maximum line length: 88 characters (Black formatter)
- Use `black` for code formatting
- Use `isort` for import sorting
- Use `flake8` for linting
- Use `mypy` for type checking

### JavaScript/TypeScript Code

- Use Prettier for formatting
- Use ESLint for linting
- Follow Airbnb style guide
- Use TypeScript for new code

### Configuration Files

- Use YAML for configuration files
- Follow consistent indentation (2 spaces)
- Use meaningful names and comments

## Testing Guidelines

### Test Structure

```
tests/
├── unit/           # Unit tests
├── integration/    # Integration tests
├── e2e/           # End-to-end tests
├── contracts/     # Smart contract tests
├── modules/       # HyperKit module tests
├── ai/            # AI generation tests
└── fixtures/      # Test data and fixtures
```

### Writing Tests

- Write tests for all new functionality
- Aim for at least 80% code coverage
- Use descriptive test names
- Test both success and failure cases
- Mock external dependencies

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=hyperkit

# Run specific test file
pytest tests/unit/test_ai_generation.py

# Run smart contract tests
pytest tests/contracts/

# Run HyperKit module tests
pytest tests/modules/

# Run AI generation tests
pytest tests/ai/

# Run integration tests
pytest tests/integration/

# Run e2e tests
pytest tests/e2e/

# Run contract tests with HyperKit CLI
hyperkit test --contracts --network hyperion-testnet
```

## Documentation

### Code Documentation

- Use docstrings for all public functions and classes
- Follow Google docstring format
- Include type hints in docstrings
- Document complex algorithms and business logic

### API Documentation

- Update API documentation for new endpoints
- Include request/response examples
- Document error codes and responses

### User Documentation

- Update README.md for significant changes
- Add examples for new features
- Update installation and setup instructions

## Issue Reporting

### Bug Reports

Use our [bug report template](.github/ISSUE_TEMPLATE/bug_report.yml) and include:

- Clear description of the issue
- Steps to reproduce
- Expected vs actual behavior
- Environment details
- Screenshots or logs if applicable

### Feature Requests

- Describe the feature clearly
- Explain the use case and benefits
- Provide examples if possible
- Consider implementation complexity

## Pull Request Process

### Before Submitting

- [ ] Code follows style guidelines
- [ ] All tests pass
- [ ] Documentation is updated
- [ ] No merge conflicts
- [ ] Commit messages follow conventional format

### PR Requirements

- [ ] Descriptive title and description
- [ ] Link to related issues
- [ ] Screenshots for UI changes
- [ ] Breaking changes documented
- [ ] Migration guide if needed

### Review Process

- All PRs require at least one review
- Address review comments promptly
- Keep PRs focused and reasonably sized
- Respond to CI/CD failures quickly

## Release Process

### Version Numbering

We follow [Semantic Versioning](https://semver.org/):
- `MAJOR.MINOR.PATCH`
- `MAJOR`: Breaking changes
- `MINOR`: New features (backward compatible)
- `PATCH`: Bug fixes (backward compatible)

### Release Checklist

- [ ] All tests passing
- [ ] Documentation updated
- [ ] Changelog updated
- [ ] Version bumped
- [ ] Release notes prepared
- [ ] Security scan completed

## Development Tools

### Pre-commit Hooks

Install pre-commit hooks:

```bash
pip install pre-commit
pre-commit install
```

### IDE Configuration

We provide configuration for:
- VS Code (`.vscode/settings.json`)
- PyCharm (`.idea/`)
- Vim/Neovim (`.vimrc`)

### Docker Development

```bash
# Build development image
docker build -t hypeagent-dev .

# Run development container
docker run -it --rm hypeagent-dev

# Run tests in container
docker run --rm hypeagent-dev pytest
```

## Getting Help

- Check existing [issues](https://github.com/hyperionkit/hyperkit/issues)
- Join our [Discord community](https://discord.gg/hyperionkit)
- Read the [documentation](https://hyperkit.readthedocs.io/)
- Contact maintainers: [maintainers@hyperionkit.xyz](mailto:maintainers@hyperionkit.xyz)
- Check our [milestone roadmap](docs/milestone.md) for current priorities

## Recognition

Contributors will be recognized in:
- CONTRIBUTORS.md file
- Release notes
- Project documentation
- Community highlights

Thank you for contributing to HyperKit! 🚀

## HyperKit Community

Join our growing community of Web3 developers:

- **Discord**: [discord.gg/hyperionkit](https://discord.gg/hyperionkit)
- **Twitter**: [@hyperionkit](https://twitter.com/hyperionkit)
- **YouTube**: [@hyperionkit](https://youtube.com/@hyperionkit)
- **Website**: [hyperionkit.xyz](https://hyperionkit.xyz)

## Milestone Contributions

We're actively working towards our 6-month milestone goals. Check out our [milestone roadmap](docs/milestone.md) to see how you can contribute to:

- Month 1: AI Generation & HyperKit Modules
- Month 2: Python SDK & CLI Tools
- Month 3: DeFi Primitives & Community Features
- Month 4: Security & Governance
- Month 5: Mainnet Preparation
- Month 6: Public Launch

Your contributions help us build the future of Web3 development! 🌟
