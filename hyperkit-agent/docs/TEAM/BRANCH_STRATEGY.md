# Git Branching Strategy & Production Release Workflow

**HyperKit-Agent Branch Policy**

---

## Branch Model

### `main` Branch
- **Purpose**: Development and testing
- **Contents**: All test/debug/enhancement work
- **Workflow**: 
  - Feature branches merge here first
  - All CI/CD workflows run on `main`
  - Integration tests, audits, and development reports
  - Can contain progress reports, TODOs, and development-only documentation

### `master` Branch
- **Purpose**: Production-ready code only
- **Contents**: 
  - ✅ Only proven, reviewed, fully tested code
  - ✅ Up-to-date professional documentation
  - ✅ Production-grade artifacts
  - ✅ Clean, consolidated reports (AUDIT.md, QUALITY.md, etc.)
  - ❌ NO development-only files
  - ❌ NO progress/milestone/TODO markdown files
  - ❌ NO sharded or duplicate documentation

**Policy**: 
- `main` → `master` merges require PR with full validation
- Automatically pruned for production (development noise removed)
- Ready for FDA/SEC-style audit reviews

---

## Production Release Workflow

### Step 1: Create Release Branch

```bash
git checkout main
git pull
git checkout -b release/vX.Y.Z
```

### Step 2: Run Release Preparation Scripts

```bash
# Bump version (patch/minor/major)
npm run version:patch   # or :minor or :major

# Update all files with new version
npm run version:update

# Update documentation
npm run docs:update

# Consolidate and organize reports
npm run reports:organize

# Prune development-only files
npm run docs:prune-for-prod
```

**Or use the all-in-one command:**
```bash
npm run release:prepare
```

### Step 3: Validate Release Candidate

All checks must pass:
- ✅ All tests passing (`npm test`)
- ✅ Linting passes (`npm run lint`)
- ✅ Type checking passes (`npm run type-check`)
- ✅ Security scan passes (`npm run security`)
- ✅ Consolidated reports exist and are up-to-date
- ✅ No development-only markdown files present

### Step 4: Create PR to master

```bash
git add .
git commit -m "chore: prepare release vX.Y.Z"
git push origin release/vX.Y.Z
```

Then create a Pull Request:
- **Base**: `master`
- **Head**: `release/vX.Y.Z`
- **Title**: `🚀 Production Release vX.Y.Z`

### Step 5: CI/CD Validation

GitHub Actions automatically:
1. Runs all tests
2. Validates consolidated reports exist
3. Checks for development-only files
4. Blocks merge if development files are detected
5. Creates release branch and PR if validation passes

### Step 6: Merge to master

After PR approval:
- Merge `release/vX.Y.Z` → `master`
- Master should only contain:
  - Core professional guides
  - Clean navigation (README.md)
  - Updated CHANGELOG.md
  - Consolidated reports (AUDIT.md, QUALITY.md, etc.)
  - Production-ready documentation

---

## NPM Scripts Reference

### Version Management

```bash
npm run version:patch    # Bump patch version (1.2.3 → 1.2.4)
npm run version:minor    # Bump minor version (1.2.3 → 1.3.0)
npm run version:major    # Bump major version (1.2.3 → 2.0.0)
npm run version:update  # Update version + CHANGELOG
```

**Updates:**
- `package.json`
- `pyproject.toml`
- `VERSION` file
- Documentation badges
- README.md version references

### Documentation & Reports

```bash
npm run changelog:update    # Update CHANGELOG.md from git commits
npm run docs:update         # Update doc badges and version refs
npm run reports:organize    # Consolidate REPORTS/ markdown files
npm run docs:prune-for-prod # Remove dev-only files for production
```

### Complete Release Preparation

```bash
npm run release:prepare
```

Runs all steps in sequence:
1. Version bump
2. Changelog update
3. Documentation update
4. Reports consolidation
5. Production file pruning

---

## Automated Scripts

### `scripts/release/update-version-all.js`

Updates version across all files:
- `package.json`
- `pyproject.toml`
- `VERSION` file (creates if missing)
- README.md badges
- Documentation version references

**Usage:**
```bash
node scripts/release/update-version-all.js <major|minor|patch>
```

### `scripts/release/update-changelog.js`

Automatically generates CHANGELOG.md entries:
- Parses git commits since last tag
- Categorizes commits (features, fixes, docs, etc.)
- Formats changelog entry
- Inserts into CHANGELOG.md

**Usage:**
```bash
node scripts/release/update-changelog.js [version]
```

### `scripts/release/update-docs.js`

Updates documentation:
- Audit badges with current version/commit/date
- Version references in docs
- README.md badges

**Usage:**
```bash
node scripts/release/update-docs.js
```

### `scripts/release/consolidate-reports.js`

Organizes REPORTS/ directory:
- Runs Python consolidation script if available
- Verifies all consolidated files exist
- Ensures reports are properly organized

**Usage:**
```bash
node scripts/release/consolidate-reports.js
```

### `scripts/release/prune-markdown-for-prod.js`

Removes development-only files:
- Dated accomplishment files
- Individual progress/TODO files
- Sharded report files (keeps consolidated only)
- Development-only JSON data

**Usage:**
```bash
# Dry run (safe, shows what would be removed)
node scripts/release/prune-markdown-for-prod.js --dry-run

# Actually remove files
node scripts/release/prune-markdown-for-prod.js
```

---

## CI/CD Integration

### GitHub Actions Workflow

Location: `.github/workflows/production-release.yml`

**Triggers:**
- Push to `main` (package.json/pyproject.toml changes)
- Manual workflow dispatch

**Validation Steps:**
1. ✅ All tests pass
2. ✅ Linting and type checking pass
3. ✅ Security scan passes
4. ✅ Consolidated reports verified
5. ✅ No development-only files detected

**If validation passes:**
- Creates `release/vX.Y.Z` branch
- Opens PR to `master`
- Tags release candidate

**If validation fails:**
- Blocks merge
- Reports which checks failed
- Requires manual fix

---

## Production File Policy

### Files to KEEP in master

✅ **Core Documentation:**
- `README.md`
- `CHANGELOG.md`
- `CONTRIBUTING.md`
- `SECURITY.md`
- `CODE_OF_CONDUCT.md`
- `LICENSE`

✅ **Consolidated Reports:**
- `REPORTS/AUDIT/AUDIT.md`
- `REPORTS/QUALITY/QUALITY.md`
- `REPORTS/STATUS/STATUS.md`
- `REPORTS/ACCOMPLISHED/ACCOMPLISHED.md`
- `REPORTS/TODO/TODO_TRACKER.md`
- `REPORTS/SECURITY/SECURITY.md`
- `REPORTS/COMPLIANCE/COMPLIANCE.md`
- `REPORTS/INFRASTRUCTURE/INFRASTRUCTURE.md`
- `REPORTS/INTEGRATION/INTEGRATION.md`
- `REPORTS/IPFS_RAG/IPFS.md`
- `REPORTS/api-audits/API_AUDITS.md`
- `REPORTS/archive/FIXES_ARCHIVE.md`

✅ **Essential Guides:**
- `docs/README.md`
- `docs/GUIDE/*.md` (user guides)
- `docs/API_REFERENCE.md`
- `docs/PRODUCTION_DEPLOYMENT_GUIDE.md`

### Files to REMOVE from master

❌ **Development-Only:**
- Dated accomplishment files (`*_2025-10-27.md`)
- Individual progress files (`*_PROGRESS_*.md`)
- TODO implementation files (`TODO_IMPLEMENTATION_*.md`)
- Milestone reports (superseded by consolidated files)

❌ **Sharded Reports:**
- Individual IPFS reports (keep `IPFS.md` only)
- Individual audit files (keep `AUDIT.md` only)
- Individual quality files (keep `QUALITY.md` only)

❌ **Temporary Data:**
- JSON files with TODO/issue conversions
- Legacy file inventories
- Consolidation scripts (after use)

---

## CTO-Grade Policy Enforcement

### "Never Fudge" Rules

1. **Never merge to master without pruning development files**
   - CI/CD automatically blocks if dev files detected
   - Manual merge requires running `npm run docs:prune-for-prod`

2. **Every production release must include doc merge/prune**
   - `npm run release:prepare` ensures this happens
   - CI/CD validates no dev files remain

3. **Master must be "FDA/SEC ready"**
   - Only truth, only what matters
   - No progress reports, no milestones
   - Clean, professional, audit-ready

4. **Automate everything**
   - One command: `npm run release:prepare`
   - CI/CD handles validation
   - No manual cleanup needed

---

## Troubleshooting

### "Development files detected" error

```bash
# Check what would be removed
npm run docs:prune-for-prod -- --dry-run

# Remove development-only files
npm run docs:prune-for-prod

# Verify clean
npm run docs:prune-for-prod -- --dry-run
```

### Version mismatch

If version is inconsistent across files:
```bash
npm run version:update
git diff  # Review changes
```

### Reports not consolidated

```bash
npm run reports:organize
# Verify consolidated files exist
ls REPORTS/*/*.md | grep -E "(AUDIT|QUALITY|STATUS)\.md"
```

---

## Quick Reference

```bash
# Full release preparation
npm run release:prepare

# Individual steps
npm run version:patch
npm run changelog:update
npm run docs:update
npm run reports:organize
npm run docs:prune-for-prod

# Validation
npm test
npm run lint
npm run type-check
npm run security
```

---

**Last Updated**: 2025-01-29  
**Status**: ✅ Active  
**Enforced By**: CI/CD + Automation Scripts  
**Policy**: Zero-tolerance for dev files in master

