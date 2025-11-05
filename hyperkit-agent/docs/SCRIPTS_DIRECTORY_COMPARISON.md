# Scripts Directory Comparison

## Overview

There are **two** script directories in the HyperAgent repository with different purposes:

1. **`./scripts/`** (root level) - Project-level installation/setup
2. **`./hyperkit-agent/scripts/`** - Application-level operational scripts

---

## 📁 `hyperagent ` (Root Level)

**Purpose:** Repository/project installation and setup scripts

**Location:** `C:\Users\USERNAME\Downloads\HyperAgent\scripts\`

### Contents:

| File | Purpose |
|------|---------|
| `install` | **Main installation script** - Sets up the entire HyperKit AI Agent project:<br>- Creates virtual environment<br>- Installs Python dependencies<br>- Sets up directory structure<br>- Installs Foundry<br>- Configures environment |
| `setup.py` | **Python package setup** - Defines the package metadata for `hyperkit-agent`:<br>- Package name, version, author<br>- Entry points (CLI commands)<br>- Dependencies<br>- Package classifiers |
| `README.md` | General documentation about script guidelines and usage patterns |

### When to Use:
- **First-time installation** of the project
- **Setting up development environment** from scratch
- **Package distribution** (`setup.py` for pip install)
- **System-level configuration**

### Example Usage:
```bash
# From root directory
hyperagent install          # Full project installation
hyperagent setup       # Package setup for distribution
```

---

## 📁 `./hyperkit-agent/scripts/` (Application Level)

**Purpose:** Operational scripts for running and maintaining the HyperKit-Agent application

**Location:** `C:\Users\USERNAME\Downloads\HyperAgent\hyperkit-agent\scripts\`

### Contents:

| Directory/File | Purpose | Key Scripts |
|----------------|---------|-------------|
| `doctor.py` / `doctor.sh` | **Preflight & self-healing** - Environment validation and auto-fix | Doctor system for dependency checks |
| `ci/` | **CI/CD automation** - Continuous integration workflows | `run_all.py`, `onboarding_smoke.py`, `e2e_templates.py` |
| `dev/` | **Developer tools** - Local development utilities | `install_cli.py`, `setup_rag_vectors.py` |
| `maintenance/` | **Code health** - Maintenance and cleanup scripts | `deadweight_scan.py`, `doc_drift_audit.py` |
| `emergency/` | **Incident response** - Critical fixes and hotfixes | `emergency_patch.sh` |
| `reports/` | **Report generation** - Generate and merge reports | `merge.py` |
| `release/` | **Release management** - Release and changelog scripts | `update-changelog.js`, `update-docs.js` |
| `dependency_install.sh` | **Dependency installer** - OpenZeppelin and other dependencies | Dependency installation |
| `preflight_version_check.sh` | **Version validation** - Check Foundry/solc versions | Version preflight |

### When to Use:
- **After installation** - Running the application
- **Daily development** - CI checks, maintenance, reports
- **Production operations** - Release management, emergency fixes
- **Environment validation** - Doctor checks before workflows

### Example Usage:
```bash
# From hyperkit-agent directory
hyperagent doctor                    # Preflight checks
hyperagent ci/run_all               # Run CI tests
hyperagent maintenance/deadweight_scan  # Cleanup
hyperagent emergency/emergency_patch  # Critical fix
```

---

## 🔄 Key Differences

| Aspect | `./scripts/` (Root) | `./hyperkit-agent/scripts/` (App) |
|--------|---------------------|-----------------------------------|
| **Purpose** | Project setup & installation | Application operations |
| **Scope** | Entire repository | HyperKit-Agent application only |
| **Frequency** | One-time setup | Regular/daily use |
| **Target Users** | New developers, CI/CD initial setup | Developers, operators, maintainers |
| **Scripts Count** | 3 files | 50+ scripts in organized subdirectories |
| **Entry Point** | `install.sh` | `doctor.py`, various operational scripts |

---

## 📊 Directory Structure

```
HyperAgent/
├── scripts/                          # Root-level (project setup)
│   ├── install.sh                   # Project installation
│   ├── setup.py                      # Package setup
│   └── README.md                     # Guidelines
│
└── hyperkit-agent/
    └── scripts/                      # Application-level (operations)
        ├── doctor.py                 # Preflight system
        ├── doctor.sh                 # Doctor bash script
        ├── dependency_install.sh    # Dependency installer
        ├── preflight_version_check.sh # Version checks
        ├── ci/                       # CI/CD automation
        │   ├── run_all.py
        │   ├── onboarding_smoke.py
        │   └── ...
        ├── dev/                      # Developer tools
        │   ├── install_cli.py
        │   └── ...
        ├── maintenance/              # Maintenance scripts
        │   ├── deadweight_scan.py
        │   └── ...
        ├── emergency/                # Emergency scripts
        │   └── emergency_patch.sh
        ├── reports/                  # Report generation
        ├── release/                  # Release management
        └── README.md                 # Scripts documentation
```

---

## 🚀 Typical Workflow

### 1. First-Time Setup (Use Root `./scripts/`)
```bash
# From repository root
cd C:\Users\USERNAME\Downloads\HyperAgent
hyperagent install          # Install entire project
```

### 2. Daily Development (Use `./hyperkit-agent/scripts/`)
```bash
# From hyperkit-agent directory
cd hyperkit-agent

# Preflight check
hyperagent doctor

# Run CI tests
hyperagent ci/run_all

# Generate reports
hyperagent reports/merge
```

### 3. Production Operations (Use `./hyperkit-agent/scripts/`)
```bash
cd hyperkit-agent

# Release management
cd scripts/release
node update-changelog.js

# Emergency fixes
hyperagent emergency/emergency_patch
```

---

## 💡 Best Practices

1. **Installation**: Use root `hyperagent install` for first-time setup
2. **Preflight**: Always run `hyperkit-agent/scripts/doctor.py` before workflows
3. **CI/CD**: Use `hyperkit-agent/scripts/ci/` for continuous integration
4. **Maintenance**: Use `hyperkit-agent/scripts/maintenance/` for cleanup
5. **Documentation**: Each subdirectory has its own `README.md`

---

## 📝 Summary

- **`./scripts/`** = **Setup scripts** (one-time installation)
- **`./hyperkit-agent/scripts/`** = **Operational scripts** (daily use)

Both directories serve different purposes in the development lifecycle:
- Root scripts **set up** the project
- Application scripts **run and maintain** the project

