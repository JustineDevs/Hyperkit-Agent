# Path Placeholder Guidelines

## Overview

All file paths in documentation use generic placeholders to avoid exposing user-specific information.

## Placeholder Format

### Windows Paths

Replace specific user paths with:
- ❌ **Don't use**: `C:\Users\JustineDevs\Downloads\HyperAgent`
- ✅ **Use instead**: `C:\Users\USERNAME\Downloads\HyperAgent`

### Unix/Linux Paths

For cross-platform compatibility:
- ❌ **Don't use**: `/home/justine/HyperAgent`
- ✅ **Use instead**: `~/HyperAgent` or `/path/to/HyperAgent`

### Git Bash/WSL Paths

For Git Bash on Windows:
- ❌ **Don't use**: `/c/Users/JustineDevs/Downloads/HyperAgent`
- ✅ **Use instead**: `/c/Users/USERNAME/Downloads/HyperAgent` or `~/Downloads/HyperAgent`

## Examples

### Documentation Examples

```bash
# ✅ Correct (generic placeholder)
cd C:\Users\USERNAME\Downloads\HyperAgent

# ❌ Incorrect (specific user)
cd C:\Users\JustineDevs\Downloads\HyperAgent
```

### Code Comments

```python
# ✅ Correct
# Path: C:\Users\USERNAME\Downloads\HyperAgent\hyperkit-agent

# ❌ Incorrect  
# Path: C:\Users\JustineDevs\Downloads\HyperAgent\hyperkit-agent
```

## What NOT to Replace

### GitHub URLs

GitHub repository URLs should **NOT** be replaced:
- ✅ Keep: `https://github.com/JustineDevs/Hyperkit-Agent`
- These are actual repository references, not file paths

### Relative Paths

Relative paths are already generic:
- ✅ `./scripts/install.sh`
- ✅ `../hyperkit-agent/scripts/doctor.py`
- ✅ `scripts/ci/run_all.py`

## Files to Review

When adding new documentation, ensure:
1. No hardcoded Windows user paths
2. Use `USERNAME` placeholder for Windows paths
3. Use `~` or relative paths for Unix paths
4. GitHub URLs remain unchanged
5. Relative paths are preferred when possible

## Scripts

Scripts should use relative paths or environment variables:
- ✅ `Path(__file__).parent.parent`
- ✅ `os.path.expanduser("~")`
- ✅ `Path.home() / "Downloads" / "HyperAgent"`
- ❌ Hardcoded `C:\Users\JustineDevs\...`

