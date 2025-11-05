# Devlog Branch Strategy Implementation

## Overview

HyperAgent implements a **dual-branch structure** to optimize repository size and improve developer experience:

- **`main` branch**: Code + essential documentation (~794 KB)
- **`devlog` branch**: Full documentation (~1.9 MB)
- **`ai` branch**: Production-ready (future)

## Implementation Summary

### Scripts Created

1. **`scripts/ci/update_readme_links.py`**
   - Converts relative links to GitHub URLs for devlog branch
   - Automatically runs during version bumps
   - Ensures links work from main branch

2. **`scripts/ci/sync_to_devlog.py`**
   - Syncs documentation files to devlog branch
   - Automatically runs during version bumps
   - Maintains code synchronization between branches

3. **`scripts/ci/validate_branch_sync.py`**
   - Validates branch sync integrity
   - Checks essential docs are in main
   - Validates README links are correct

4. **`scripts/ci/essential_docs_whitelist.json`**
   - Defines which files stay in main branch
   - Configures sync behavior

### CLI Integration

**New Command**: `hyperagent docs`
- `hyperagent docs open` - Show documentation index
- `hyperagent docs checkout` - Checkout devlog branch locally
- `hyperagent docs info` - Show documentation access guide

### Documentation Updates

1. **README.md**
   - Added branch awareness banner
   - Updated all documentation links to GitHub URLs
   - Added quick access instructions

2. **CONTRIBUTING.md**
   - Added branch strategy section
   - Documented workflow for code vs. documentation changes
   - Added instructions for syncing to devlog

3. **version_bump.py**
   - Integrated automatic link updates
   - Integrated automatic doc sync
   - Added devlog push reminder

## Usage

### For Developers (Code Changes)

```bash
# Work on main branch
git checkout main
git checkout -b feature/my-feature

# Make code changes
# Commit essential docs if needed
git commit -m "feat: add feature"

# Push and create PR to main
git push origin feature/my-feature
```

### For Documentation

```bash
# After PR merged to main, sync docs to devlog
python scripts/ci/sync_to_devlog.py

# Or manually
git checkout devlog
git merge main
git push origin devlog
```

### For Users

```bash
# Clone main (code only)
git clone https://github.com/JustineDevs/Hyperkit-Agent.git

# Clone devlog (full docs)
git clone -b devlog https://github.com/JustineDevs/Hyperkit-Agent.git

# Switch to devlog in existing clone
git fetch origin devlog:devlog
git checkout devlog

# Use CLI helper
hyperagent docs checkout
```

## Automated Workflows

### Version Bump Integration

When running `npm run version:patch|minor|major`:

1. Version files updated
2. README.md links automatically converted to GitHub URLs
3. Documentation automatically synced to devlog branch
4. Reminder to push devlog branch

### Manual Sync

```bash
# Update README links
python scripts/ci/update_readme_links.py

# Sync docs to devlog
python scripts/ci/sync_to_devlog.py

# Validate sync
python scripts/ci/validate_branch_sync.py
```

## Essential Files in Main

The following files **must** remain in main branch:

- `README.md`
- `CHANGELOG.md`
- `LICENSE.md`
- `SECURITY.md`
- `CONTRIBUTING.md`
- `CODE_OF_CONDUCT.md`
- `VERSION`
- `package.json`
- `hyperkit-agent/pyproject.toml`
- `hyperkit-agent/config.yaml`
- `hyperkit-agent/docs/GUIDE/QUICK_START.md`
- `hyperkit-agent/docs/GUIDE/ENVIRONMENT_SETUP.md`
- `hyperkit-agent/env.example`

## Files in Devlog

All other documentation files are in devlog:

- `hyperkit-agent/REPORTS/` (all subdirectories)
- `hyperkit-agent/docs/TEAM/`
- `hyperkit-agent/docs/EXECUTION/`
- `hyperkit-agent/docs/INTEGRATION/`
- `hyperkit-agent/docs/REFERENCE/`
- `docs/` (root-level docs)

## Validation

Run validation to check branch sync:

```bash
python scripts/ci/validate_branch_sync.py
```

This checks:
- Essential docs present in main
- README links are correct
- Devlog branch exists

## Benefits

1. **Faster Clones**: 50-60% smaller for code-focused users
2. **Clear Separation**: Code vs. documentation
3. **Automated Sync**: No manual intervention needed
4. **Link Integrity**: All links work from both branches
5. **CI/CD Ready**: Validation scripts for automation

## Troubleshooting

### Links Broken in Main

Run: `python scripts/ci/update_readme_links.py`

### Docs Not Synced

Run: `python scripts/ci/sync_to_devlog.py`

### Validation Failures

Check:
- All essential files exist in main
- README links point to GitHub URLs for devlog docs
- Devlog branch exists and is up-to-date

## Future Enhancements

- [ ] GitHub Actions CI for automatic validation
- [ ] Automated PR checks for branch compliance
- [ ] Sparse checkout documentation
- [ ] Git subtree for advanced users

