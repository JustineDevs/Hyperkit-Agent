# Git Add & Commit Capabilities - Complete Inventory

**Date**: 2025-01-29  
**Status**: ✅ Complete

---

## ✅ **Commands with Git Add & Commit**

### **1. Version Bumping (Python)**

#### `npm run version:patch` / `npm run version:minor` / `npm run version:major`
- **Script**: `hyperkit-agent/scripts/ci/version_bump.py`
- **Git Operations**:
  - ✅ `git add` (VERSION, package.json, pyproject.toml)
  - ✅ `git commit` (message: `"chore(release): bump version to X.Y.Z (patch/minor/major)"`)
  - ✅ `git tag` (creates `vX.Y.Z` tag)
- **Auto-commit**: ✅ **ALWAYS ENABLED** (no disable option)
- **Files**: VERSION, package.json, pyproject.toml

---

### **2. Documentation Updates (JavaScript)**

#### `node hyperkit-agent/scripts/release/update-docs.js`
- **Git Operations**:
  - ✅ `git add` (each updated doc file individually)
  - ✅ `git commit` (per file: `"docs: update audit badge in <file>"`)
- **Auto-commit**: ✅ **YES** (default)
- **Disable**: ✅ Use `--no-commit` flag
- **Files**: README.md, docs/**/*.md files with badges/versions

---

### **3. Changelog Updates (JavaScript)**

#### `node hyperkit-agent/scripts/release/update-changelog.js`
- **Usage**: `node hyperkit-agent/scripts/release/update-changelog.js [version] [--no-commit]`
- **Git Operations**:
  - ✅ `git add` (CHANGELOG.md)
  - ✅ `git commit` (message: `"chore: update CHANGELOG.md for version X.Y.Z"`)
- **Auto-commit**: ✅ **YES** (default)
- **Disable**: ✅ Use `--no-commit` flag
- **Files**: CHANGELOG.md

---

### **4. Reports Consolidation (JavaScript)**

#### `node hyperkit-agent/scripts/release/consolidate-reports.js`
- **Usage**: `node hyperkit-agent/scripts/release/consolidate-reports.js [--no-commit]`
- **Git Operations**:
  - ✅ `git add` (consolidated report files)
  - ✅ `git commit` (message: `"docs: update consolidated reports"`)
- **Auto-commit**: ✅ **YES** (default)
- **Disable**: ✅ Use `--no-commit` flag
- **Files**: Modified consolidated report files in REPORTS/

---

### **5. Production Pruning (JavaScript)**

#### `node hyperkit-agent/scripts/release/prune-markdown-for-prod.js`
- **Usage**: 
  ```bash
  # Dry run first (recommended)
  node hyperkit-agent/scripts/release/prune-markdown-for-prod.js --dry-run
  
  # Actually remove files
  node hyperkit-agent/scripts/release/prune-markdown-for-prod.js [--no-commit]
  ```
- **Git Operations**:
  - ✅ `git rm` (removed files)
  - ✅ `git add` (if needed)
  - ✅ `git commit` (message: `"chore: prune N development-only files for production"`)
- **Auto-commit**: ✅ **YES** (default)
- **Disable**: ✅ Use `--no-commit` flag
- **Files**: File deletions (via `git rm`)

---

### **6. Legacy CI/CD Script (Not Recommended)**

#### `python .github/workflows/scripts/version_update.py`
- **Usage**: `BUMP_TYPE=patch python .github/workflows/scripts/version_update.py`
- **Git Operations**:
  - ✅ `git add -A` (all changes)
  - ✅ `git commit` (message: `"chore(release): bump version to X.Y.Z"`)
  - ✅ `git tag` (creates `vX.Y.Z` tag)
- **Auto-commit**: ✅ **ALWAYS ENABLED** (no disable option)
- **Status**: ⚠️ **LEGACY** - Use `version_bump.py` instead

---

### **7. Emergency Patch Script**

#### `hyperkit-agent/scripts/emergency/emergency_patch.sh`
- **Git Operations**:
  - ✅ `git add .` (all changes)
  - ✅ `git commit` (message: `"SECURITY PATCH: <CVE_ID> - <DESCRIPTION>"`)
- **Auto-commit**: ✅ **ALWAYS ENABLED** (by design for security)
- **Purpose**: Emergency security patches

---

## ❌ **Commands WITHOUT Git Commit**

### **Documentation Version Sync (Python)**

#### `npm run version:update-docs`
- **Script**: `hyperkit-agent/scripts/ci/update_version_in_docs.py`
- **Git Operations**: ❌ **NO COMMIT** (only updates files)
- **Note**: You must manually commit changes:
  ```bash
  npm run version:update-docs
  git add docs/ README.md
  git commit -m "docs: sync version in documentation"
  ```

### **Reports Merging (Python)**

#### `python hyperkit-agent/scripts/reports/merge.py`
- **Git Operations**: ❌ **NO COMMIT** (only merges and deletes files)
- **Note**: You must manually commit changes:
  ```bash
  python hyperkit-agent/scripts/reports/merge.py
  git add REPORTS/
  git commit -m "docs: merge individual reports into consolidated files"
  ```

---

## 📊 **Quick Reference Table**

| Command/Script | Git Add | Git Commit | Git Tag | Auto-commit | Disable Flag |
|----------------|---------|------------|---------|-------------|--------------|
| `npm run version:patch/minor/major` | ✅ | ✅ | ✅ | ✅ Always | ❌ No |
| `node update-docs.js` | ✅ | ✅ | ❌ | ✅ Default | ✅ `--no-commit` |
| `node update-changelog.js` | ✅ | ✅ | ❌ | ✅ Default | ✅ `--no-commit` |
| `node consolidate-reports.js` | ✅ | ✅ | ❌ | ✅ Default | ✅ `--no-commit` |
| `node prune-markdown-for-prod.js` | ✅ | ✅ | ❌ | ✅ Default | ✅ `--no-commit` |
| `npm run version:update-docs` | ❌ | ❌ | ❌ | ❌ No | N/A |
| `python merge.py` (reports) | ❌ | ❌ | ❌ | ❌ No | N/A |
| `.github/workflows/scripts/version_update.py` | ✅ | ✅ | ✅ | ✅ Always | ❌ No |
| `emergency_patch.sh` | ✅ | ✅ | ❌ | ✅ Always | ❌ No |

---

## 🎯 **Usage Examples**

### **Version Bump (Auto-commits)**
```bash
npm run version:patch   # ✅ Auto-commits + tags
```

### **Documentation Updates**

**Option 1: JavaScript script (auto-commits)**
```bash
node hyperkit-agent/scripts/release/update-docs.js
```

**Option 2: Python script (manual commit)**
```bash
npm run version:update-docs
git add docs/ README.md
git commit -m "docs: sync version in documentation"
```

### **Changelog (Auto-commits)**
```bash
node hyperkit-agent/scripts/release/update-changelog.js
```

### **Reports Consolidation (Auto-commits)**
```bash
node hyperkit-agent/scripts/release/consolidate-reports.js
```

### **Reports Merging (Manual commit)**
```bash
python hyperkit-agent/scripts/reports/merge.py
git add REPORTS/
git commit -m "docs: merge individual reports into consolidated files"
```

### **Production Pruning (Auto-commits)**
```bash
# Always dry-run first!
node hyperkit-agent/scripts/release/prune-markdown-for-prod.js --dry-run
node hyperkit-agent/scripts/release/prune-markdown-for-prod.js
```

---

## 🔧 **Disable Auto-Commit**

JavaScript release scripts support `--no-commit`:

```bash
node hyperkit-agent/scripts/release/update-docs.js --no-commit
node hyperkit-agent/scripts/release/update-changelog.js --no-commit
node hyperkit-agent/scripts/release/consolidate-reports.js --no-commit
node hyperkit-agent/scripts/release/prune-markdown-for-prod.js --no-commit
```

**Note**: Python scripts (`version_bump.py`, `emergency_patch.sh`) do NOT have a disable option - they always commit (by design).

---

## 🚨 **Important Notes**

1. **`npm run version:update-docs`** (Python) → ❌ **NO COMMIT** - Manual commit required
2. **`python merge.py`** (reports) → ❌ **NO COMMIT** - Manual commit required
3. **`npm run version:patch/minor/major`** (Python) → ✅ **ALWAYS COMMITS** - No disable option
4. **JavaScript release scripts** → ✅ **AUTO-COMMIT** with `--no-commit` option
5. **Emergency patch script** → ✅ **ALWAYS COMMITS** - By design for security

---

**Generated**: 2025-01-29  
**Status**: ✅ Complete Inventory
