# HyperAgent Configuration Files

All linters, type checkers, and test settings are stored here for standardization.

## 📁 Configuration Files

### **Code Quality**
- **`.flake8`** - Flake8 linting configuration
- **`.pylintrc`** - Pylint configuration
- **`mypy.ini`** - MyPy type checking configuration
- **`black.toml`** - Black code formatting configuration

### **Testing**
- **`pytest.ini`** - Pytest configuration
- **`coverage.ini`** - Coverage reporting configuration
- **`tox.ini`** - Tox testing configuration

### **Development**
- **`pre-commit.yaml`** - Pre-commit hooks configuration
- **`pyproject.toml`** - Python project configuration
- **`setup.cfg`** - Setuptools configuration

## 🔧 Configuration Details

### **Flake8 (.flake8)**
```ini
[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude = 
    .git,
    __pycache__,
    .venv,
    venv,
    .pytest_cache
```

### **Pylint (.pylintrc)**
```ini
[MASTER]
load-plugins = pylint.extensions.docparams
disable = C0330

[MESSAGES CONTROL]
disable = missing-docstring

[FORMAT]
max-line-length = 88
```

### **MyPy (mypy.ini)**
```ini
[mypy]
python_version = 3.9
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
```

### **Black (black.toml)**
```toml
[tool.black]
line-length = 88
target-version = ['py39']
include = '\.pyi?$'
extend-exclude = '''
/(
  \.git
  | \.mypy_cache
  | \.tox
  | \.venv
  | _build
  | buck-out
  | build
  | dist
)/
'''
```

### **Pytest (pytest.ini)**
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --strict-markers
    --strict-config
    --verbose
    --tb=short
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    performance: Performance tests
    security: Security tests
```

## 🚀 Usage

### **Running Linters**
```bash
# Flake8
flake8 hyperkit-agent/

# Pylint
pylint hyperkit-agent/

# MyPy
mypy hyperkit-agent/

# Black
black hyperkit-agent/
```

### **Running Tests**
```bash
# All tests
pytest

# Specific test categories
pytest -m unit
pytest -m integration
pytest -m e2e

# With coverage
pytest --cov=hyperkit-agent --cov-report=html
```

### **Pre-commit Hooks**
```bash
# Install pre-commit
pre-commit install

# Run manually
pre-commit run --all-files
```

## 📊 Code Quality Metrics

### **Target Metrics**
- **Test Coverage**: >80%
- **Linting Score**: 10/10
- **Type Coverage**: >90%
- **Documentation**: >95%

### **Quality Gates**
- All tests must pass
- No linting errors
- Type checking must pass
- Coverage threshold met
- Documentation complete

## 🔄 Maintenance

### **Regular Updates**
- Update linter configurations monthly
- Review and update test configurations quarterly
- Update type checking rules as needed
- Keep documentation current

### **Configuration Validation**
```bash
# Validate all configurations
python -m flake8 --version
python -m pylint --version
python -m mypy --version
python -m black --version
python -m pytest --version
```

## 📝 Best Practices

### **Code Style**
- Follow PEP 8 guidelines
- Use type hints for all functions
- Write comprehensive docstrings
- Keep functions small and focused

### **Testing**
- Write tests for all new functionality
- Use descriptive test names
- Include both positive and negative tests
- Maintain high test coverage

### **Documentation**
- Document all public APIs
- Include usage examples
- Keep documentation up to date
- Use consistent formatting

## 🔧 Customization

### **Project-Specific Settings**
- Adjust line length limits as needed
- Configure ignore patterns for project structure
- Set appropriate test markers
- Customize coverage thresholds

### **Team Standards**
- Agree on coding standards
- Use consistent configuration across team
- Regular code review process
- Continuous integration checks

## 📞 Support

### **Configuration Issues**
- Check file syntax and format
- Verify tool versions
- Review error messages
- Consult tool documentation

### **Customization Help**
- Review existing configurations
- Test changes incrementally
- Document any customizations
- Share improvements with team
