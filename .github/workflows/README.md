# GitHub Actions Workflows

Professional CI/CD workflows for HyperKit Agent.

---

## 🎯 **Version Management Workflows**

### **1. Version Automation** (`versioning.yml`)

**Purpose:** Manual version bumping via GitHub Actions UI

**Triggers:**
- `workflow_dispatch` - Manual trigger with inputs

**Inputs:**
- `bump_type`: `patch`, `minor`, or `major` (default: `patch`)
- `auto_push`: Automatically push changes (default: `false`)

**What It Does:**
1. ✅ Runs canonical `version_bump.py` script
2. ✅ Updates documentation versions
3. ✅ Optionally pushes to remote
4. ✅ Optionally creates GitHub release

**Usage:**
- Go to Actions → Version Automation → Run workflow
- Select bump type (patch/minor/major)
- Enable auto_push if you want automatic push/release

**Note:** Prefer using `npm run version:patch` locally for faster feedback.

---

### **2. Version Sync** (`version-sync.yml`)

**Purpose:** Automatic documentation sync when VERSION file changes

**Triggers:**
- `push` to `VERSION` file
- `release` published

**What It Does:**
1. ✅ Detects VERSION file change
2. ✅ Runs `update_version_in_docs.py`
3. ✅ Updates all documentation with new version
4. ✅ Commits and pushes doc updates automatically

**Use Case:** Ensures docs stay in sync when version is bumped manually or via release.

---

## 📋 **Other Workflows**

### **CI/CD** (`ci-cd.yml`)
- Runs tests, linting, security checks on PR/push
- Builds and validates the project

### **Security** (`security.yml`)
- Security scanning and vulnerability checks

### **Tests** (`tests.yml`)
- Automated test suite execution

### **Documentation Drift Check** (`doc-drift-check.yml`)
- Ensures code and documentation stay in sync

### **Drift Prevention Policy** (`drift-prevention-policy.yml`)
- Enforces documentation updates when code changes

### **RAG Registry Sync** (`rag-registry-sync.yml`)
- Syncs RAG templates with IPFS registry

### **Regression Audit** (`regression-audit.yml`)
- Regression testing and audit checks

### **Test Gating Policy** (`test-gating-policy.yml`)
- Test quality gates for PR approval

### **Changeset Check** (`changeset-check.yml`)
- Validates changeset entries

---

## 🔗 **Canonical Version Scripts**

**All workflows use canonical Python scripts from `hyperkit-agent/scripts/ci/`:**

- ✅ `version_bump.py` - Version bumping (patch/minor/major)
- ✅ `update_version_in_docs.py` - Documentation version sync

**Source of Truth:**
- 📁 Root `VERSION` file (single source of truth)
- All files derive from `VERSION`

**Legacy Script (not recommended):**
- ⚠️ `.github/workflows/scripts/version_update.py` - Legacy, kept for backward compatibility

---

## 🚀 **Professional Workflow Best Practices**

1. **Use npm scripts locally** - Faster feedback, same functionality
2. **Use GitHub workflows** - For automated releases, CI/CD integration
3. **Single source of truth** - Always root `VERSION` file
4. **Canonical scripts only** - Use `hyperkit-agent/scripts/ci/` scripts
5. **Consistent Python version** - Use Python 3.12 for new workflows

---

## 📚 **Related Documentation**

- **Scripts README**: `.github/workflows/scripts/README.md`
- **CI Scripts**: `hyperkit-agent/scripts/ci/README.md`
- **Release Scripts**: `hyperkit-agent/scripts/release/README.md`
- **Branch Strategy**: `hyperkit-agent/docs/BRANCH_STRATEGY.md`
- **Git Commit Capabilities**: `.github/workflows/GIT_COMMIT_CAPABILITIES.md`

---

**Last Updated**: 2025-01-29  
**Version**: 1.5.0

