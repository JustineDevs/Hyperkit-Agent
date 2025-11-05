# Devlog Branch Strategy - Script Updates

## Overview

This document lists all scripts that have been updated or should be aware of the devlog branch strategy.

## Updated Scripts

### 1. Core Branch Management Scripts ✅

- **`scripts/ci/update_readme_links.py`** - Converts relative links to GitHub URLs
- **`scripts/ci/sync_to_devlog.py`** - Syncs documentation to devlog branch
- **`scripts/ci/validate_branch_sync.py`** - Validates branch sync integrity
- **`scripts/ci/version_bump.py`** - Integrated with link update and doc sync
- **`scripts/ci/essential_docs_whitelist.json`** - Configuration for sync

### 2. Branch Awareness Utilities ✅

- **`scripts/utils/branch_awareness.py`** - NEW: Helper functions for branch detection

### 3. Updated Scripts with Branch Awareness ✅

- **`scripts/ci/update_honest_status.py`** - Added branch awareness warnings

## Scripts That Write to Devlog-Only Directories

These scripts write to directories that only exist in devlog branch. They work fine with relative paths, but files written from main will be synced to devlog on next sync:

### REPORTS/ Directory

- `scripts/maintenance/doc_drift_audit.py` - Writes to `REPORTS/JSON_DATA/`
- `scripts/maintenance/legacy_file_inventory.py` - Writes to `REPORTS/JSON_DATA/`
- `scripts/maintenance/orphaned_doc_reference_script.py` - Writes to `REPORTS/QUALITY/` and `REPORTS/JSON_DATA/`
- `scripts/maintenance/script_hash_validator.py` - Writes to `REPORTS/JSON_DATA/`
- `scripts/maintenance/lint_all_scripts.py` - Writes to `REPORTS/QUALITY/`
- `scripts/ci/run_all_updates.py` - Writes to `REPORTS/SCRIPTS/` and category subdirectories
- `scripts/reports/merge.py` - Processes `REPORTS/` directories
- `scripts/reports/consolidate_reports.py` - Processes `REPORTS/` directories
- `scripts/reports/consolidate_archive.py` - Processes `REPORTS/` directories

### Documentation Directories

- `scripts/ci/update_version_in_docs.py` - Updates version in `docs/**/*.md` and `REPORTS/**/*.md`
- `scripts/ci/update_honest_status.py` - Updates `docs/HONEST_STATUS.md` (if exists)
- `scripts/release/update-docs.js` - Updates various doc files

## Behavior

### Writing from Main Branch

When scripts write to devlog-only directories from main branch:
- ✅ Files are created successfully (relative paths work)
- ✅ Files will be synced to devlog on next `sync_to_devlog.py` run
- ⚠️ Files won't exist in main branch after sync (they're moved to devlog)

### Writing from Devlog Branch

When scripts write to devlog-only directories from devlog branch:
- ✅ Files are created and remain in devlog
- ✅ Files are available in devlog branch
- ✅ No sync needed

## Best Practices

### For Script Developers

1. **Use Relative Paths**: Always use relative paths, not absolute paths
2. **Add Branch Awareness**: Import `branch_awareness` utilities if needed
3. **Document Behavior**: Add comments explaining devlog-only directory usage
4. **Handle Gracefully**: Scripts should work in both branches

### For Script Users

1. **Run from Appropriate Branch**:
   - For reports/documentation: Use `devlog` branch
   - For code/essential docs: Use `main` branch
2. **Check Branch**: Use `git branch` to verify current branch
3. **Sync After Changes**: Run `sync_to_devlog.py` if you made changes from main

## Helper Functions

### Using Branch Awareness Utilities

```python
from scripts.utils.branch_awareness import (
    get_current_branch,
    is_devlog_branch,
    is_main_branch,
    check_devlog_dir_access,
    suggest_branch_for_operation
)

# Check current branch
branch = get_current_branch()
if branch == "main":
    print("Running on main branch")

# Check if writing to devlog-only directory
output_path = Path("REPORTS/test.md")
is_devlog_only, warning = check_devlog_dir_access(output_path, warn=True)
if is_devlog_only and not is_devlog_branch():
    print("Warning: Writing to devlog-only directory from main")
```

## Migration Notes

### Scripts That Don't Need Updates

Most scripts work fine as-is because:
- They use relative paths
- They work with files that exist in the current branch
- They don't need to know about branches

### Scripts That May Need Updates (Future)

If you want to add branch awareness to more scripts:
1. Import `branch_awareness` utilities
2. Add warnings when writing to devlog-only directories from main
3. Document expected branch in script comments

## Testing

### Test from Main Branch

```bash
git checkout main
python scripts/maintenance/doc_drift_audit.py
# Should work, but will warn about devlog-only directory
```

### Test from Devlog Branch

```bash
git checkout devlog
python scripts/maintenance/doc_drift_audit.py
# Should work without warnings
```

## Summary

✅ **Core branch management scripts**: Fully implemented  
✅ **Branch awareness utilities**: Created and available  
✅ **Key scripts updated**: `update_honest_status.py`  
✅ **Documentation**: Updated and comprehensive  

⚠️ **Most scripts work as-is**: No changes needed (relative paths work fine)  
📝 **Optional enhancements**: Add branch awareness to more scripts if desired

