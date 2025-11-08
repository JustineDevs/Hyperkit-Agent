# CI/CD Scripts

Scripts for continuous integration, deployment, badge generation, and version management.

## Scripts

| Script | Purpose | Arguments | Frequency |
|--------|---------|-----------|-----------|
| `sync_workflow.py` | Branch+workflow hygiene with auto uncommitted file handling | `[--dry-run] [--push]` | On commit/push |
| `run_all_updates.py` | Orchestrates all repo maintenance workflows in parallel | - | CI/CD on push |
| `audit_badge_system.py` | Adds audit badges to markdown files | `--output REPORTS/` | CI/CD badges |
| `docs_version_badge_system.py` | Injects version badges into core docs | - | On release |
| `command_badge_generator.py` | Generates SVG badges for CLI commands | - | On new commands |
| `update_version_in_docs.py` | Updates version across all docs | - | Version release |
| `version_bump.py` | Handles semantic versioning | `[patch|minor|major]` | On release |
| `prepare_rag_templates.py` | Prepares RAG templates for upload | - | Before upload |
| `upload_rag_templates_to_ipfs.py` | Uploads RAG templates to IPFS | - | After prepare |
| `cleanup_legacy_files_fixed.sh` | Legacy file cleanup (legacy) | - | One-time |

## Workflow Hygiene (`sync_workflow.py`)

The hygiene workflow script automatically handles uncommitted files to prevent data loss and ensure clean working trees.

### Features:
- **Auto-detection**: Detects untracked, modified, and staged files before workflow run
- **Auto-staging**: Automatically stages uncommitted files to prevent data loss
- **Auto-commit**: Commits workflow-generated files automatically
- **Final validation**: Ensures no uncommitted files remain after workflow completion

### Usage:
```bash
# Run hygiene workflow (auto-handles uncommitted files)
npm run hygiene

# Dry run (preview changes)
npm run hygiene:dry-run

# Push changes to remote
npm run hygiene:push
```

### Uncommitted File Handling:
1. **Pre-flight check**: Detects uncommitted files before workflow starts
2. **Auto-staging**: Automatically stages detected files
3. **Workflow execution**: Runs all workflow scripts
4. **Auto-commit**: Commits generated files automatically
5. **Final validation**: Ensures clean working tree after completion

## Usage

### Version Management
```bash
python version_bump.py minor  # Bump minor version
python update_version_in_docs.py  # Sync version across docs
```

### Badge Generation
```bash
python audit_badge_system.py
python docs_version_badge_system.py
python command_badge_generator.py
```

### CI/CD Orchestration
```bash
python run_all_updates.py  # Runs all workflows in parallel
```

### RAG Template Management
```bash
python prepare_rag_templates.py
python upload_rag_templates_to_ipfs.py
```

## CI Integration

These scripts are integrated into GitHub Actions workflows:
- `.github/workflows/version-sync.yml` - Version management
- `.github/workflows/doc-drift-check.yml` - Badge updates
- `.github/workflows/rag-registry-sync.yml` - RAG template sync

## Safe Usage

- Run `run_all_updates.py` in CI only
- Badge scripts update markdown files - review changes
- Version scripts modify global version files
- RAG scripts require Pinata API keys configured

## Owner

HyperAgent CI/CD Team
