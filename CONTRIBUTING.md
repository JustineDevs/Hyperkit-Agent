# Contributing to HyperAgent

Thank you for contributing to HyperAgent! This document provides guidelines and expectations for contributors.

---

## 🎯 Core Contribution Principles

### Zero-Excuse Culture for Documentation

**CRITICAL**: Every feature or CLI change MUST include documentation updates in the same PR.

#### Documentation Requirements:
- ✅ **Required**: Update relevant docs when adding new features
- ✅ **Required**: Update CLI reference when adding new commands/flags
- ✅ **Required**: Update examples when changing behavior
- ✅ **Required**: Update API docs when changing interfaces
- ❌ **Failure Policy**: PRs without matching doc updates will be REJECTED

#### PR Review Checklist:

**Before submitting a PR, ensure:**

1. **Documentation Updated** ✅
   - [ ] Updated relevant documentation files
   - [ ] Updated CLI command reference
   - [ ] Updated examples and usage guides
   - [ ] No reference to old/deprecated features

2. **Code Quality** ✅
   - [ ] Code follows project style guide
   - [ ] All tests passing
   - [ ] No linting errors
   - [ ] Proper error handling

3. **Tests** ✅
   - [ ] Unit tests added for new features
   - [ ] Integration tests updated
   - [ ] E2E tests updated if workflow affected
   - [ ] Test coverage maintained/increased

4. **Status Updates** ✅
   - [ ] Updated HONEST_STATUS_ASSESSMENT.md if changing capabilities
   - [ ] Updated IMPLEMENTATION_PROGRESS if major feature
   - [ ] Marked todos as completed

---

## 📝 Documentation Standards

### File Organization

- **docs/** (root): User-facing, high-level documentation
- **hyperkit-agent/docs/**: Internal technical documentation
- **hyperkit-agent/Docs/**: Team/execution/internal guides
- **hyperkit-agent/REPORTS/**: Current status, audits, progress reports

### Naming Conventions

- Use kebab-case for all documentation files
- Use descriptive names that indicate purpose
- No random suffixes, timestamps, or dates
- Exception: ACCOMPLISHED/ uses date suffixes for historical tracking

### Documentation Types

**Real**: Documented feature that works as described  
**Partial**: Feature works but has known limitations (must document them)  
**Stub**: Must be marked as such or removed

---

## 🚫 What NOT to Do

❌ **Don't create documentation for planned features** (use GitHub Issues instead)  
❌ **Don't use "coming soon" or "planned" language**  
❌ **Don't leave TODOs in production code** (convert to Issues or implement)  
❌ **Don't commit stub/placeholder documentation**  
❌ **Don't create duplicate status reports**  
❌ **Don't use future-tense for present-tense capabilities**  

✅ **Do document what actually works**  
✅ **Do document known limitations honestly**  
✅ **Do delete outdated documentation**  
✅ **Do update docs in same commit as code changes**  

---

## 🔄 Development Workflow

### Before Starting

1. Check current todos in `hyperkit-agent/TODO.md`
2. Read HONEST_STATUS_ASSESSMENT.md for current limitations
3. Review existing documentation before adding new docs

### Making Changes

1. **Create feature branch** from `main`
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make code changes** with tests

3. **Update documentation** in the SAME commit:
   ```bash
   # Edit code
   git add src/new_feature.py
   git add tests/test_new_feature.py
   
   # Update docs in same commit
   git add docs/new_feature_guide.md
   git commit -m "feat: add new feature with docs"
   ```

4. **Run tests and linting**:
   ```bash
   pytest tests/
   flake8 src/
   ```

5. **Push and create PR**:
   ```bash
   git push origin feature/your-feature-name
   # Create PR on GitHub
   ```

### PR Approval Criteria

**Will be approved if:**
- ✅ All tests passing
- ✅ Documentation updated
- ✅ No linting errors
- ✅ Follows contribution guidelines

**Will be rejected if:**
- ❌ Documentation not updated
- ❌ Tests not passing
- ❌ Linting errors present
- ❌ Stub/placeholder code in production

---

## 📊 Status & Progress Reporting

### Updating Status Documents

**When to update**:
- Adding new feature → Update HONEST_STATUS_ASSESSMENT.md
- Fixing bug → Update KNOWN_LIMITATIONS.md
- Major progress → Update IMPLEMENTATION_PROGRESS
- Completion → Update appropriate TODO

**Location of status docs**:
- `hyperkit-agent/REPORTS/HONEST_STATUS_ASSESSMENT.md`
- `hyperkit-agent/REPORTS/IMPLEMENTATION_PROGRESS_*.md`
- `hyperkit-agent/docs/EXECUTION/KNOWN_LIMITATIONS.md`

---

## 🧪 Testing Requirements

### Test Coverage

- **Unit Tests**: Required for all new functions/modules
- **Integration Tests**: Required for new features affecting workflows
- **E2E Tests**: Required for new CLI commands or major features

### Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test suite
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/

# With coverage
pytest --cov=hyperkit-agent tests/
```

---

## 📋 Code Review Process

### For Contributors

1. Submit PR with all requirements met
2. Wait for review feedback
3. Address review comments
4. Resubmit if needed

### For Reviewers

1. Check documentation updated
2. Check tests added
3. Check code quality
4. Check status documents updated
5. Approve or request changes

---

## 🎯 Issue Tracking

**Use GitHub Issues for**:
- Feature requests
- Bug reports
- Planned improvements
- Questions/discussions

**Link Issues in**:
- PR descriptions
- Commit messages
- Status updates

---

## 🔧 Setup for Contributors

### Local Development

```bash
# Clone repository
git clone https://github.com/JustineDevs/Hyperkit-Agent.git
cd Hyperkit-Agent

# Install dependencies
cd hyperkit-agent
pip install -r requirements.txt  # All dependencies (includes Alith SDK and IPFS features)

# Run tests
pytest tests/

# Run linting
flake8 hyperkit-agent/
```

### Environment Setup

1. Copy `hyperkit-agent/env.example` to `hyperkit-agent/.env`
2. Add API keys (OpenAI, Anthropic, Google)
3. Configure network settings

---

## 📞 Getting Help

- **Documentation**: See `docs/` and `hyperkit-agent/docs/`
- **Issues**: Open GitHub issue
- **Questions**: Check KNOWN_LIMITATIONS.md or HONEST_STATUS_ASSESSMENT.md
- **Contributing**: This file

---

## ✅ Summary: What Makes a Good Contribution

**Good PR**:
- ✅ Feature works as described
- ✅ Tests added and passing
- ✅ Documentation updated
- ✅ Status documents updated
- ✅ No stub/TODO code
- ✅ Honest about limitations

**Bad PR**:
- ❌ Feature incomplete but documented as complete
- ❌ Tests missing
- ❌ Documentation outdated
- ❌ Stub code in production
- ❌ Misleading status claims

---

**Remember**: HyperAgent values honesty over hype. Document what works, mark what doesn't, and keep it real.

**Last Updated**: 2025-10-28  
**Maintained By**: HyperAgent Core Team
