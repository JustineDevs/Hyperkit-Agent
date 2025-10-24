# Contributing to HyperKit

Thank you for your interest in contributing to HyperKit! This document provides guidelines for contributing to the project.

## 🤝 How to Contribute

### **Ways to Contribute**
- 🐛 **Bug Reports**: Report issues and bugs
- 💡 **Feature Requests**: Suggest new features
- 📝 **Documentation**: Improve documentation
- 🔧 **Code Contributions**: Submit code changes
- 🧪 **Testing**: Help with testing and QA

### **Getting Started**
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## 📋 Development Guidelines

### **Code Standards**
- Follow PEP 8 for Python code
- Use type hints for function parameters and returns
- Write comprehensive docstrings
- Maintain test coverage above 80%

### **Commit Message Format**
```
type(scope): description

[optional body]

[optional footer]
```

**Types**: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

**Examples**:
- `feat(generation): add smart naming system`
- `fix(deployment): resolve RPC timeout issues`
- `docs(api): update CLI reference`

### **Pull Request Process**
1. Ensure your branch is up to date with main
2. Run all tests: `python -m pytest`
3. Check code style: `python -m flake8`
4. Update documentation if needed
5. Request review from maintainers

## 🧪 Testing

### **Running Tests**
```bash
# Unit tests
python -m pytest tests/unit/

# Integration tests
python -m pytest tests/integration/

# End-to-end tests
python -m pytest tests/e2e/

# All tests
python -m pytest
```

### **Test Coverage**
```bash
# Generate coverage report
python -m pytest --cov=hyperkit-agent --cov-report=html
```

## 📚 Documentation

### **Documentation Types**
- **Public Docs** (`/docs/`): User-facing documentation
- **Developer Docs** (`/hyperkit-agent/docs/`): Technical documentation
- **Code Comments**: Inline code documentation
- **API Docs**: Auto-generated from docstrings

### **Writing Documentation**
- Use clear, concise language
- Include examples and code snippets
- Keep documentation up to date
- Follow the existing style guide

## 🐛 Bug Reports

### **Before Reporting**
1. Check existing issues
2. Ensure you're using the latest version
3. Try to reproduce the issue
4. Gather relevant information

### **Bug Report Template**
```markdown
**Bug Description**
A clear description of the bug.

**Steps to Reproduce**
1. Go to '...'
2. Click on '...'
3. See error

**Expected Behavior**
What you expected to happen.

**Actual Behavior**
What actually happened.

**Environment**
- OS: [e.g., Windows 10]
- Python version: [e.g., 3.9.0]
- HyperKit version: [e.g., 1.0.0]

**Additional Context**
Any other relevant information.
```

## 💡 Feature Requests

### **Feature Request Template**
```markdown
**Feature Description**
A clear description of the feature.

**Use Case**
Why is this feature needed?

**Proposed Solution**
How should this feature work?

**Alternatives**
Other solutions you've considered.

**Additional Context**
Any other relevant information.
```

## 🔒 Security

### **Security Issues**
For security-related issues, please email security@hyperkit.dev instead of creating a public issue.

### **Security Guidelines**
- Never commit secrets or API keys
- Use environment variables for sensitive data
- Follow secure coding practices
- Report vulnerabilities responsibly

## 📞 Community

### **Getting Help**
- 📖 **Documentation**: Check the docs first
- 💬 **Discussions**: Use GitHub Discussions
- 🐛 **Issues**: Create an issue for bugs
- 💡 **Ideas**: Use Discussions for feature ideas

### **Code of Conduct**
We are committed to providing a welcoming and inclusive environment. Please read and follow our [Code of Conduct](./CODE_OF_CONDUCT.md).

## 🏆 Recognition

Contributors will be recognized in:
- CONTRIBUTORS.md file
- Release notes
- Project documentation
- Community acknowledgments

## 📄 License

By contributing to HyperKit, you agree that your contributions will be licensed under the same license as the project.

---

Thank you for contributing to HyperKit! 🚀
