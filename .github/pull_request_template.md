## Pull Request Checklist

### 📋 Documentation Requirements
- [ ] **CLI Changes**: If this PR modifies CLI commands, I have updated the relevant documentation
- [ ] **API Changes**: If this PR modifies APIs, I have updated the API documentation
- [ ] **New Features**: If this PR adds new features, I have documented them with examples
- [ ] **Breaking Changes**: If this PR contains breaking changes, I have provided migration instructions
- [ ] **Troubleshooting**: If this PR affects user workflows, I have updated troubleshooting guides

### 📚 Documentation Files Updated
Please list all documentation files that were updated in this PR:

- [ ] `README.md`
- [ ] `docs/CLI_COMMANDS_REFERENCE.md`
- [ ] `docs/API_REFERENCE.md`
- [ ] `docs/TROUBLESHOOTING_GUIDE.md`
- [ ] Other: ________________

### 🔍 Implementation Status
- [ ] **Implemented**: All features in this PR are fully functional
- [ ] **Partially Implemented**: Some features work with limitations (explain below)
- [ ] **Not Implemented**: Some features are documented but not functional (explain below)

### 🧪 Testing
- [ ] **Unit Tests**: Added/updated unit tests for new functionality
- [ ] **Integration Tests**: Added/updated integration tests
- [ ] **E2E Tests**: Added/updated end-to-end tests
- [ ] **Documentation Examples**: Tested all code examples in documentation

### 📝 Additional Information
**Description of Changes**:
<!-- Provide a clear description of what this PR changes -->

**Documentation Impact**:
<!-- Describe how this change affects users and what documentation was updated -->

**Breaking Changes**:
<!-- List any breaking changes and migration instructions -->

**Testing Instructions**:
<!-- Provide instructions for reviewers to test the changes -->

### 🚨 Drift Prevention Policy
By submitting this PR, I acknowledge that:
- [ ] I have read and understand the [Drift Prevention Policy](docs/POLICIES/DRIFT_PREVENTION_POLICY.md)
- [ ] I have updated all relevant documentation
- [ ] I have tested all documentation examples
- [ ] I understand that PRs violating this policy will be blocked

### 📋 Reviewer Checklist
**For Documentation Reviewers**:
- [ ] Documentation matches implementation
- [ ] Examples are tested and working
- [ ] All CLI commands are documented
- [ ] Implementation status is accurate
- [ ] Links are valid and up-to-date

**For Code Reviewers**:
- [ ] Code changes are properly implemented
- [ ] Tests cover new functionality
- [ ] No breaking changes without migration docs
- [ ] Performance impact is acceptable

---

**Note**: This PR template is automatically enforced by our drift prevention policy. PRs that don't meet documentation requirements will be blocked.
