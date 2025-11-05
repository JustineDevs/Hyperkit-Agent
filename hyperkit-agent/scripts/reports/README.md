# Reports Consolidation Scripts

Scripts for consolidating and organizing markdown reports in the REPORTS/ directory.

## Scripts

### `merge.py` ⭐ **UNIFIED SCRIPT** ⭐
**Unified script that merges individual markdown files into consolidated files and removes merged files.**

**Usage:**
```bash
# Dry run (preview changes)
hyperagent reports/merge --dry-run

# Process all directories
hyperagent reports/merge

# Process single directory
hyperagent reports/merge --directory ACCOMPLISHED
```

**What it does:**
1. Scans all REPORTS subdirectories
2. Finds the consolidated file for each directory (e.g., `ACCOMPLISHED.md`)
3. Merges all other `*.md` files into the consolidated file
4. Removes the merged files after merging
5. Skips files that are already merged (detects duplicates)

**Features:**
- ✅ Automatic duplicate detection (checks for `*From: `filename`*` pattern)
- ✅ Dry-run mode for safety
- ✅ Single directory processing
- ✅ All directories processing
- ✅ Proper section headers and formatting
- ✅ Preserves existing consolidated content

**Example:**
```
ACCOMPLISHED/
  ├── ACCOMPLISHED.md (consolidated file - exists)
  ├── AUDIT_COMPLETION_SUMMARY.md (new - will merge)
  ├── AUDIT_FIXES_APPLIED.md (new - will merge)
  
After merge.py:
  └── ACCOMPLISHED.md (updated with all content, individual files deleted)
```

---

### `consolidate_reports.py` (Legacy)
Original consolidation script. Superseded by `merge.py`.

**Note**: Use `merge.py` instead for ongoing file merging.

---

### `consolidate_archive.py` (Legacy)
Archive consolidation helper. Functionality integrated into `merge.py`.

---

### `delete_obsolete_files.py` (Legacy)
File deletion helper. Functionality integrated into `merge.py` (automatic deletion after merge).

---

## Quick Reference

### Merge Individual Files into Consolidated Files
```bash
# Dry run to see what would happen
hyperagent reports/merge --dry-run

# Actually merge and delete files
hyperagent reports/merge

# Process specific directory
hyperagent reports/merge --directory ACCOMPLISHED
```

---

**Status**: ✅ `merge.py` is the unified script - consolidates merge, archive, and delete operations

