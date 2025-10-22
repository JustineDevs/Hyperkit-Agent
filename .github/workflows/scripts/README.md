# 🚀 HyperKit AI Agent - Version Automation Scripts

## Quick Start

### **Update Version (All-in-One)**
```bash
# Default patch
npm run version:update

# Patch version (1.2.0 → 1.2.1)
npm run version:patch 

# Minor version (1.2.0 → 1.3.0)
npm run version:minor

# Major version (1.2.0 → 2.0.0)
npm run version:major 
```

### **What It Does**
- ✅ Updates version in all files (`package.json`, `setup.py`, etc.)
- ✅ Creates changeset entry
- ✅ Updates changelog files
- ✅ Commits changes with git
- ✅ Creates version tag (`v1.2.1`)

## Files Updated

| File | Pattern | Example |
|------|---------|---------|
| `package.json` | `"version": "1.2.0"` | ✅ Updated |
| `hyperkit-agent/package.json` | `"version": "1.2.0"` | ✅ Updated |
| `hyperkit-agent/setup.py` | `version="1.2.0"` | ✅ Updated |
| `hyperkit-agent/services/defi/primitives_generator.py` | `"version": "1.2.0"` | ✅ Updated |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `BUMP_TYPE` | `patch` | Version bump type: `patch`, `minor`, `major` |

## Prerequisites

- ✅ Git repository
- ✅ Python 3.9+
- ✅ Changeset directory (`.changeset/`)
- ✅ Version files exist

## Manual Steps After Running

1. **Review changes:**
   ```bash
   git show HEAD
   ```

2. **Push to remote:**
   ```bash
   git push origin main --tags
   ```

3. **Publish release:**
   ```bash
   npx changeset publish
   ```

## Troubleshooting

| Error | Solution |
|-------|----------|
| `No version found` | Check if version files exist and have valid version numbers |
| `Not in a git repository` | Run from project root directory |
| `Changeset directory not found` | Ensure `.changeset/` directory exists |
| `Git operation failed` | Check git status and resolve any conflicts |

## Examples

### **Patch Release (Bug Fix)**
```bash
python .github/workflows/scripts/version_update.py
# 1.2.0 → 1.2.1
```

### **Minor Release (New Feature)**
```bash
BUMP_TYPE=minor python .github/workflows/scripts/version_update.py
# 1.2.0 → 1.3.0
```

### **Major Release (Breaking Change)**
```bash
BUMP_TYPE=major python .github/workflows/scripts/version_update.py
# 1.2.0 → 2.0.0
```

---

**💡 Pro Tip:** Always test locally before pushing to production!
