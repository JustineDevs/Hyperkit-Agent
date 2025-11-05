# Command Flow Guide

**Complete guide to using HyperAgent workflow automation commands.**

---

## 📋 Quick Reference

### **Version Management**

**⚠️ CRITICAL:** Always use the complete workflow for version bumps:

```bash
# Complete workflow (RECOMMENDED - all three steps)
npm run version:complete          # Patch version (1.5.15 → 1.5.16)
npm run version:complete:minor    # Minor version (1.5.15 → 1.6.0)
npm run version:complete:major    # Major version (1.5.15 → 2.0.0)
```

**Individual Steps (if needed):**
```bash
npm run version:patch          # Bump patch version only
npm run version:minor          # Bump minor version only
npm run version:major          # Bump major version only
npm run version:update-docs    # Sync version across all documentation
npm run version:check          # Check version consistency
npm run version:current        # Show current version
```

**See:** [`VERSIONING_WORKFLOW.md`](./VERSIONING_WORKFLOW.md) for complete workflow documentation.

### **Workflow Hygiene**
```bash
npm run hygiene:dry-run        # Preview what would be done (safe)
npm run hygiene                # Run complete workflow (commits locally)
npm run hygiene:push           # Run workflow and push to remote
```

---

## 🔄 Detailed Flow Diagrams

### **1. Version Bump Flow**

```bash
npm run version:patch
```

**Execution Flow:**
1. **version-bump.js** (JavaScript)
   - Reads current version from `VERSION` file
   - Calculates new version (patch/minor/major)
   - Updates: `VERSION`, `package.json`, `hyperkit-agent/pyproject.toml`
   - Commits changes (unless `--no-commit` flag)

2. **Post-bump scripts** (automatically called):
   - **update-changelog.js** → Updates `CHANGELOG.md` with git commits
   - **update-docs.js** → Updates version badges in all documentation
   - **sync-to-devlog.js** → Syncs documentation to `devlog` branch

**Result:**
- ✅ Version bumped in all files
- ✅ CHANGELOG.md updated
- ✅ Documentation badges updated
- ✅ Changes synced to devlog branch

---

### **2. Workflow Hygiene Flow**

```bash
npm run hygiene
```

**Execution Flow:**

**STEP 1: Run Workflow Scripts**
- `update-readme-links.js` (JavaScript) ✅ Required
  - Updates README.md links for devlog branch
- `doc_drift_audit.py` (Python) ⚠️ Optional
  - AI-powered documentation drift analysis
- `doc_drift_cleanup.py` (Python) ⚠️ Optional
  - AI-powered documentation cleanup
- `cli_command_inventory.py` (Python) ⚠️ Optional
  - CLI command analysis
- `legacy_file_inventory.py` (Python) ⚠️ Optional
  - Legacy file analysis
- `update-version-in-docs.js` (JavaScript) ⚠️ Optional
  - Syncs version across all documentation

**STEP 2: Stage and Commit on Main**
- Switches to `main` branch (if not already)
- Stages files matching `MAIN_STAGE_PATTERNS`:
  - `README.md`, `CHANGELOG.md`
  - `hyperkit-agent/docs/GUIDE/`
  - `hyperkit-agent/config.yaml`
  - `package.json`, `VERSION`, etc.
- Commits: `"chore: run workflow scripts, update docs and hygiene"`

**STEP 3: Sync to Devlog**
- Calls `sync-to-devlog.js` (JavaScript)
- Switches to `devlog` branch
- Merges latest from `main`
- Stages files matching `DEVLOG_STAGE_PATTERNS`:
  - `hyperkit-agent/REPORTS/`
  - `hyperkit-agent/docs/TEAM/`
  - `hyperkit-agent/docs/EXECUTION/`
  - `hyperkit-agent/docs/INTEGRATION/`
  - `docs/`
- Commits: `"chore(devlog): sync documentation from main"`
- Returns to original branch

**STEP 4: Final Status**
- Shows git status
- Reports any remaining uncommitted changes

**Result:**
- ✅ All workflow scripts executed
- ✅ Changes committed to `main` branch
- ✅ Documentation synced to `devlog` branch
- ✅ Repository is clean and organized

---

### **3. Dry-Run Flow**

```bash
npm run hygiene:dry-run
```

**Same as workflow hygiene, but:**
- ❌ No files are modified
- ❌ No git commits are made
- ❌ No branch switches occur
- ✅ Shows what would be done

**Use this to preview changes before running the actual workflow.**

---

## 💡 Usage Scenarios

### **Scenario 1: After Adding a Feature**

```bash
# 1. Commit your feature
git add .
git commit -m "feat: add new contract generator"

# 2. Bump patch version (automatically handles everything)
npm run version:patch

# This automatically:
# - Bumps version (1.5.15 → 1.5.16)
# - Updates CHANGELOG.md
# - Updates all doc badges
# - Syncs to devlog branch
# - Commits everything

# 3. Push to remote
git push origin main
git push origin devlog
```

### **Scenario 2: Update Documentation**

```bash
# 1. You've updated documentation files
# (e.g., updated README.md, added new docs)

# 2. Run hygiene workflow
npm run hygiene

# This automatically:
# - Updates README links
# - Runs maintenance scripts (optional)
# - Commits changes to main
# - Syncs docs to devlog branch

# 3. Push if needed
git push origin main
git push origin devlog
```

### **Scenario 3: Preview Before Committing**

```bash
# See what would happen without making changes
npm run hygiene:dry-run

# Output shows:
# - Which scripts would run
# - Which files would be staged
# - What commits would be made
# - Which branches would be affected

# Then run for real:
npm run hygiene
```

---

## 🛠️ Tech Stack

**JavaScript** (Node.js):
- All version management scripts
- All workflow automation scripts
- All documentation update scripts
- All branch synchronization scripts

**Python**:
- AI-powered analysis scripts (optional)
- Orchestration script (`sync_workflow.py`)

**Shell**:
- Emergency scripts only

---

## ⚠️ Important Notes

1. **Working Tree Must Be Clean**
   - The workflow checks for uncommitted changes
   - Commit or stash changes before running

2. **Branch Safety**
   - Always returns to original branch
   - Never pushes to remote (unless `--push` flag)
   - Safe to run multiple times

3. **Script Execution**
   - Required scripts: Fail → Workflow stops
   - Optional scripts: Fail → Workflow continues
   - All scripts run sequentially

4. **Path Resolution**
   - All scripts use relative paths from repository root
   - Works on Windows, Mac, and Linux

---

## 📚 Related Documentation

- [`TECH_STACK_POLICY.md`](TECH_STACK_POLICY.md) - Tech stack separation policy
- [`MIGRATION_COMPLETE.md`](MIGRATION_COMPLETE.md) - Migration status
- [`../ci/README.md`](../ci/README.md) - CI/CD scripts documentation
- [`../release/README.md`](../release/README.md) - Release scripts documentation

---

---

## 🛡️ Safety Features

**Enterprise-Grade Safety Implemented:**
- ✅ Automatic branch restoration (even on CTRL+C/interrupt)
- ✅ Working tree validation before operations
- ✅ Required vs optional script distinction
- ✅ Timeout protection (5 minutes per script)
- ✅ Comprehensive error handling and recovery
- ✅ Configuration externalized (`workflow_patterns.json`)

**See:** [`HYGIENE_SAFETY.md`](HYGIENE_SAFETY.md) for complete safety documentation.

---

**Last Updated:** 2025-01-30

