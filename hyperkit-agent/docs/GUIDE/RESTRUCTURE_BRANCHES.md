# Branch Restructuring Plan

## Goal
- **main**: Code + minimal essential docs only
- **devlog**: Documentation files (.md) only

## Steps

### Step 1: Clean Main Branch
Remove all non-essential docs from main:
- `hyperkit-agent/REPORTS/` (entire directory)
- `hyperkit-agent/docs/TEAM/`
- `hyperkit-agent/docs/EXECUTION/`
- `hyperkit-agent/docs/INTEGRATION/`
- `hyperkit-agent/docs/REFERENCE/`
- `docs/` (root level)
- Any other non-essential .md files

### Step 2: Clean Devlog Branch
Remove all code files from devlog, keep only:
- All .md files
- Essential scripts for doc management:
  - `scripts/ci/sync_to_devlog.py`
  - `scripts/ci/update_readme_links.py`
  - `scripts/ci/validate_branch_sync.py`
  - `scripts/ci/essential_docs_whitelist.json`
  - `scripts/utils/branch_awareness.py`
- Essential config files:
  - `package.json`
  - `VERSION`
  - `hyperkit-agent/pyproject.toml`
  - `hyperkit-agent/config.yaml`

## Commands

```bash
# 1. Clean main branch
git checkout main
git rm -r hyperkit-agent/REPORTS/
git rm -r hyperkit-agent/docs/TEAM/
git rm -r hyperkit-agent/docs/EXECUTION/
git rm -r hyperkit-agent/docs/INTEGRATION/
git rm -r hyperkit-agent/docs/REFERENCE/
git rm -r docs/ 2>/dev/null || true
git commit -m "chore: remove non-essential docs from main branch"

# 2. Clean devlog branch
git checkout devlog
# Remove all code directories
git rm -r hyperkit-agent/core/
git rm -r hyperkit-agent/services/
git rm -r hyperkit-agent/cli/
git rm -r hyperkit-agent/contracts/
git rm -r hyperkit-agent/tests/
# Remove most scripts (keep doc management ones)
find hyperkit-agent/scripts -type f ! -name "*.md" ! -path "*/ci/sync_to_devlog.py" ! -path "*/ci/update_readme_links.py" ! -path "*/ci/validate_branch_sync.py" ! -path "*/ci/essential_docs_whitelist.json" ! -path "*/utils/branch_awareness.py" -exec git rm {} \;
git commit -m "chore: remove code files from devlog, keep only documentation"
```

