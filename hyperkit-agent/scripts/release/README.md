# Release Automation Scripts

Production release automation scripts for HyperKit-Agent.

## ⚠️ Professional Versioning Workflow

**All versioning is now handled by canonical Python scripts:**

- **Version Bumping**: `hyperkit-agent/scripts/ci/version_bump.py`
- **Doc Sync**: `hyperkit-agent/scripts/ci/update_version_in_docs.py`
- **Source of Truth**: Root `VERSION` file

**JavaScript version script removed** - consolidated to Python for single-source-of-truth workflow.

### `version-bump.js`
Handles semantic versioning with automatic uncommitted file detection and handling.

**Usage:**
```bash
node hyperkit-agent/scripts/release/version-bump.js [patch|minor|major] [--no-commit] [--skip-remote-check] [--skip-uncommitted-check]
```

**Options:**
- `[patch|minor|major]`: Version bump type (required)
- `--no-commit`: Disable auto-commit (default: enabled)
- `--skip-remote-check`: Skip remote version validation
- `--skip-uncommitted-check`: Skip uncommitted file detection

**Features:**
- Detects uncommitted files before version bump
- Auto-stages uncommitted files
- Updates VERSION, package.json, and pyproject.toml
- Commits version files + uncommitted files together
- Final validation ensures clean working tree

**Uncommitted File Handling:**
1. Pre-bump check detects uncommitted files
2. Auto-stages detected files
3. Commits version files + uncommitted files together
4. Post-bump validation ensures clean working tree

**Git Integration:**
- Automatically commits version files and uncommitted files
- Use `--no-commit` to review changes before committing
- Use `--skip-uncommitted-check` to disable auto-staging

### `update-changelog.js`
Automatically generates CHANGELOG.md entries from git commits.

**Usage:**
```bash
node scripts/release/update-changelog.js [version] [--no-commit]
```

**Options:**
- `[version]`: Optional version number (default: from package.json)
- `--no-commit`: Disable auto-commit (default: enabled)

**Features:**
- Parses commits since last tag
- Categorizes (features, fixes, docs, etc.)
- Formats changelog entry
- Inserts into CHANGELOG.md

**Git Integration:**
- Automatically commits CHANGELOG.md changes
- Use `--no-commit` to review changes before committing

### `update-docs.js`
Updates documentation badges and version references.

**Usage:**
```bash
node scripts/release/update-docs.js [--no-commit]
```

**Options:**
- `--no-commit`: Disable auto-commit (default: enabled)

**Updates:**
- Audit badges (version, commit, date)
- Version references in docs
- README.md badges

**Git Integration:**
- Automatically commits each updated documentation file individually
- Use `--no-commit` to review changes before committing

### `consolidate-reports.js`
Organizes and verifies consolidated reports.

**Usage:**
```bash
node scripts/release/consolidate-reports.js [--no-commit]
```

**Options:**
- `--no-commit`: Disable auto-commit (default: enabled)

**Verifies:**
- All consolidated report files exist
- Reports are properly organized
- Python consolidation script compatibility

**Git Integration:**
- Automatically commits modified consolidated report files
- Use `--no-commit` to review changes before committing

### `prune-markdown-for-prod.js`
Removes development-only markdown files before production release.

**Usage:**
```bash
# Dry run (safe)
node scripts/release/prune-markdown-for-prod.js --dry-run

# Actually remove files
node scripts/release/prune-markdown-for-prod.js [--no-commit]
```

**Options:**
- `--dry-run` or `-n`: Preview files to be removed without deleting
- `--no-commit`: Disable auto-commit (default: enabled)

**Removes:**
- Dated accomplishment files
- Individual progress/TODO files
- Sharded report files (keeps consolidated only)
- Development-only JSON data

**Git Integration:**
- Automatically commits file deletions using `git rm`
- Use `--no-commit` to review deletions before committing

## Git Integration

All scripts now have automatic git commit capabilities:

**Default Behavior:**
- ✅ Auto-commit is **ENABLED** by default
- Each updated/deleted file is committed individually with descriptive messages
- Commits use conventional commit format (e.g., `chore:`, `docs:`)

**Disable Auto-Commit:**
- Use `--no-commit` flag with any script to review changes first
- Scripts will still update files but skip git operations
- Manual commit instructions shown when auto-commit is disabled

**Example Workflow:**
```bash
# Auto-commit enabled (default)
node scripts/release/update-version-all.js patch
# → Each file committed automatically

# Review changes first
node scripts/release/update-version-all.js patch --no-commit
# → Files updated, manual commit needed
```

## Quick Reference

Use npm scripts for convenience:

```bash
# Version Management
npm run version:patch    # Bump patch version (1.4.8 → 1.4.9)
npm run version:minor    # Bump minor version (1.4.8 → 1.5.0)
npm run version:major    # Bump major version (1.4.8 → 2.0.0)
npm run version:update  # Bump patch + update CHANGELOG.md

# Documentation & Reports
npm run changelog:update      # Update CHANGELOG.md from git commits
npm run docs:update           # Update doc badges and version refs
npm run reports:organize      # Consolidate REPORTS/ markdown files
npm run docs:prune-for-prod   # Remove dev-only files (dry-run first!)

# Complete Release Preparation (All-in-one)
npm run release:prepare  # Runs: version:update + docs:update + reports:organize + docs:prune-for-prod
```

See [BRANCH_STRATEGY.md](../../docs/BRANCH_STRATEGY.md) for complete workflow.

