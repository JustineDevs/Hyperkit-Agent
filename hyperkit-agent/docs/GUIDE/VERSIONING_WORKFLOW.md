# Canonical Versioning Workflow

**Status:** ✅ **ENFORCED** - This is THE canonical workflow for all version bumps  
**Last Updated:** 2025-11-05  
**Version:** 1.6.0

---

## 🎯 **Overview**

This document defines the **gold-standard, reproducible versioning workflow** for HyperAgent. This workflow ensures:

- ✅ Clean, consolidated reports before versioning
- ✅ Complete capture of all version-related changes
- ✅ Zero uncommitted files after workflow
- ✅ Complete migration to `devlog` branch
- ✅ Professional, audit-ready release state

**🚫 CRITICAL:** This workflow is **ENFORCED**. Manual, ad-hoc versioning is **NOT ALLOWED**.

---

## 📋 **The Three-Step Workflow**

### **Step 1: Consolidate & Clean Reports (merge.py)**

**Command:**
```bash
npm run reports:organize
# OR
python hyperkit-agent/scripts/reports/merge.py
```

**Purpose:**
- Collapse scattered `.md` reports into consolidated files per category
- Remove individual report files after merging
- Clean state before versioning

**Why First?**
If you bump the version *before* cleaning reports, your version tag may reflect soon-to-be-deleted or duplicate report files—confusing your release history and users.

**What It Does:**
1. Scans all `REPORTS/` subdirectories (ACCOMPLISHED, AUDIT, QUALITY, STATUS, etc.)
2. Merges individual `.md` files into consolidated files (e.g., `ACCOMPLISHED.md`)
3. Deletes merged files after consolidation
4. **Auto-commits per category:** `docs(reports): consolidate {category} reports (X merged, Y deleted)`

**Result:**
- ✅ Clean, consolidated reports
- ✅ All changes committed automatically
- ✅ Ready for version bump

---

### **Step 2: Bump Version and Capture All Version-Specific State**

**Command:**
```bash
npm run version:patch
# OR
npm run version:minor
# OR
npm run version:major
```

**Purpose:**
- Bump version in all files
- Update changelog, docs, badges
- Sync version changes to `devlog` branch
- Capture all version-related git changes

**Why Second?**
You want only the *final* report, changelog, and doc state included in the new version—they should match what shipped, not what existed before cleaning.

**What It Does (Automatically):**

1. **Bump Version:**
   - Updates: `VERSION`, `package.json`, `hyperkit-agent/pyproject.toml`
   - **Auto-commits:** `chore: bump version to X.Y.Z`

2. **Cleanup Duplicates:**
   - Runs `cleanup-meta-dupes.js`
   - Removes duplicate meta files (single source of truth)
   - **Auto-commits:** Duplicate removals

3. **Update Changelog:**
   - Runs `update-changelog.js`
   - Generates CHANGELOG.md entry from git commits
   - **Auto-commits:** `chore: update CHANGELOG.md for version X.Y.Z`

4. **Update Documentation:**
   - Runs `update-docs.js`
   - Updates version badges in all documentation
   - Updates version references
   - **Auto-commits:** Per file: `docs: update audit badge in ...`

5. **Sync to Devlog:**
   - Runs `sync-to-devlog.js`
   - Syncs version changes to `devlog` branch
   - **Auto-commits:** `chore(devlog): sync documentation from main branch`
   - **Removes non-essential docs from main** (keeps main minimal)
   - **Auto-commits:** `chore(main): remove docs moved to devlog`

**Result:**
- ✅ All version-related files committed
- ✅ Version changes tracked in git
- ✅ Devlog updated with version changes
- ✅ **Main branch cleaned (non-essential docs removed)**
- ✅ No manual git operations needed

---

### **Step 3: Final Hygiene and Migration to Devlog**

**Command:**
```bash
npm run hygiene
```

**Purpose:**
- Run all maintenance and fix-up scripts
- Stage and commit **all** remaining changes
- Ensure complete migration to `devlog` branch
- Final "every file" insurance policy

**Why Last?**
Catches all churn, drift, or accidental file changes from the above steps (or anything the versioning scripts missed/left "dirty"). Leaves the repo and devlog **100% clean**—ready for PR, tag, or release.

**What It Does (Automatically):**

1. **Run All Workflow Scripts:**
   - `cleanup-meta-dupes.js` (duplicate cleanup) ✅ Required
   - `update-readme-links.js` (README links) ✅ Required
   - `doc_drift_audit.py` (doc audit) ⚠️ Optional
   - `doc_drift_cleanup.py` (doc cleanup) ⚠️ Optional
   - `cli_command_inventory.py` (CLI inventory) ⚠️ Optional
   - `legacy_file_inventory.py` (legacy inventory) ⚠️ Optional
   - `merge.py` (reports consolidation) ⚠️ Optional
   - `update-version-in-docs.js` (version in docs) ⚠️ Optional

2. **Stage All Files:**
   - Pattern-based staging (README, CHANGELOG, etc.)
   - **Full file staging** (catches ALL modified files)
   - Result: **No uncommitted changes missed**

3. **Auto-Commit All Changes:**
   - Single commit: `chore: run workflow scripts, update docs and hygiene`
   - Ensures all script-generated changes are committed

4. **Sync to Devlog:**
   - Switches to `devlog` branch
   - Merges latest from `main`
   - Stages devlog-specific files
   - **Auto-commits:** `chore(devlog): sync documentation from main branch`
   - Returns to `main` branch
   - **Removes non-essential docs from main** (keeps main minimal)
   - **Auto-commits:** `chore(main): remove docs moved to devlog`

**Result:**
- ✅ All files captured and committed
- ✅ **No uncommitted changes remain**
- ✅ Complete migration to devlog
- ✅ **Main branch minimal (only essential docs remain)**
- ✅ Clean working tree

---

## 🚀 **One-Command Workflow (Recommended)**

**Instead of running three commands, use the complete workflow:**

```bash
# Patch version bump (recommended for most releases)
npm run version:complete

# Minor version bump
npm run version:complete:minor

# Major version bump
npm run version:complete:major
```

**What This Does:**
1. ✅ Runs `npm run reports:organize` (Step 1)
2. ✅ Runs `npm run version:patch/minor/major` (Step 2)
3. ✅ Runs `npm run hygiene` (Step 3)

**Result:**
- Complete workflow in one command
- No skipped steps
- Professional, reproducible versioning

---

## ✅ **Verification After Workflow**

After running the complete workflow, verify everything is clean:

```bash
# Check main branch
git status
# Expected: "nothing to commit, working tree clean"

# Check devlog branch
git checkout devlog
git status
# Expected: "nothing to commit, working tree clean"

# Verify sync commits
git log --oneline -5
# Should see: "chore(devlog): sync documentation from main branch"

# Return to main
git checkout main
```

---

## 🚫 **What Could Go Wrong & How to Handle**

### **Working Tree Dirty at Start**

**Problem:** Uncommitted changes before starting workflow

**Solution:**
```bash
# The workflow will abort with clear error message:
# "Working tree has uncommitted changes"
# "Please commit or stash changes before running"

# Fix:
git add .
git commit -m "your changes"
# OR
git stash
# Then re-run workflow
```

### **Any Step Fails**

**Problem:** Script fails mid-workflow

**Solution:**
- The chain breaks (by design)
- Fix the error
- Re-run the complete workflow: `npm run version:complete`
- **Never skip steps** - always run the complete workflow

### **Missing Files**

**Problem:** Script expects file that doesn't exist

**Solution:**
- Most scripts are optional (won't fail workflow)
- Required scripts will fail gracefully with clear error
- Check script logs for specific issue
- Fix missing file or script configuration

---

## 📊 **Workflow Summary**

### **Before Workflow:**
```
REPORTS/
  ├── ACCOMPLISHED/
  │   ├── ACCOMPLISHED.md (consolidated)
  │   ├── FEATURE_X_SUMMARY.md (individual - needs merge)
  │   └── FIX_Y_SUMMARY.md (individual - needs merge)
  └── AUDIT/
      ├── AUDIT.md (consolidated)
      └── AUDIT_RESULT_Z.md (individual - needs merge)

VERSION: 1.5.18
CHANGELOG.md: (last version: 1.4.7)
```

### **After Workflow:**
```
REPORTS/
  ├── ACCOMPLISHED/
  │   └── ACCOMPLISHED.md (consolidated - all merged)
  └── AUDIT/
      └── AUDIT.md (consolidated - all merged)

VERSION: 1.6.0
CHANGELOG.md: (updated with 1.6.0 entry)

Git Status:
  main: ✅ Clean
  devlog: ✅ Clean (synced)
```

---

## 🎯 **Best Practices**

### **DO:**
- ✅ Always use `npm run version:complete` for version bumps
- ✅ Run workflow on clean working tree
- ✅ Verify git status after workflow
- ✅ Test on feature branch before merging to main
- ✅ Review commits before pushing

### **DON'T:**
- ❌ Never skip steps (always run complete workflow)
- ❌ Never manually version files (use automation)
- ❌ Never commit between workflow steps (let automation handle it)
- ❌ Never run workflow with uncommitted changes
- ❌ Never bypass safety checks

---

## 📚 **Related Documentation**

- **Command Flow Guide:** [`COMMAND_FLOW_GUIDE.md`](./COMMAND_FLOW_GUIDE.md)
- **Branch Strategy:** [`BRANCH_STRATEGY.md`](../BRANCH_STRATEGY.md)
- **Contributing Guide:** [`CONTRIBUTING.md`](../../../CONTRIBUTING.md)
- **Versioning Flow:** [`COMMAND_FLOW_VERSIONING.md`](../../REPORTS/COMMAND_FLOW_VERSIONING.md)

---

## 🔄 **Workflow Diagram**

```
┌─────────────────────────────────────────────────────────────┐
│  USER COMMAND: npm run version:complete                    │
└─────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 1: npm run reports:organize                          │
│  ────────────────────────────────────────────────────────  │
│  • merge.py merges individual reports                      │
│  • Auto-commits per category                               │
│  • Clean, consolidated reports                             │
└─────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 2: npm run version:patch                             │
│  ────────────────────────────────────────────────────────  │
│  • Bump version (VERSION, package.json, pyproject.toml)    │
│  • Update CHANGELOG.md                                     │
│  • Update documentation badges                             │
│  • Sync to devlog branch                                   │
│  • Auto-commits all changes                                │
└─────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 3: npm run hygiene                                   │
│  ────────────────────────────────────────────────────────  │
│  • Run all maintenance scripts                             │
│  • Stage ALL modified files                                │
│  • Auto-commit catch-all                                   │
│  • Final sync to devlog                                    │
│  • Clean working tree                                      │
└─────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  RESULT:                                                    │
│  ✅ Clean working tree (main)                              │
│  ✅ Clean working tree (devlog)                            │
│  ✅ All files committed                                    │
│  ✅ Ready for PR/tag/release                               │
└─────────────────────────────────────────────────────────────┘
```

---

**Status:** ✅ **LOCKED IN** - This is THE canonical versioning workflow for HyperAgent.

