# Maintenance Scripts

Scripts for code health checks, drift detection, and repository maintenance.

## Scripts

### Code Health
| Script | Purpose | Arguments |
|--------|---------|-----------|
| `deadweight_scan.py` | Identifies TODO, FIXME, mock, stub patterns | `--output REPORTS/` |
| `cli_command_validation.py` | Validates CLI commands | - |
| `security_scan.py` | Runs security checks | - |
| `repo_health_dashboard.py` | Generates health dashboard | - |

### Documentation Drift
| Script | Purpose | Arguments |
|--------|---------|-----------|
| `doc_drift_audit.py` | Audits documentation for outdated content | `--output REPORTS/` |
| `doc_drift_cleanup.py` | Fixes outdated CLI references | - |
| `orphaned_doc_reference_script.py` | Finds orphaned doc references | - |

### Integration Audits
| Script | Purpose | Arguments |
|--------|---------|-----------|
| `integration_sdk_audit.py` | Audits SDK integration status | - |
| `cleanup_mock_integrations.py` | Removes mock integrations | - |
| `script_hash_validator.py` | Validates script integrity | - |

### CLI Management
| Script | Purpose | Arguments |
|--------|---------|-----------|
| `cli_command_inventory.py` | Creates CLI command inventory | - |
| `cli_command_validation.py` | Validates CLI commands | - |

### TODO Management
| Script | Purpose | Arguments |
|--------|---------|-----------|
| `todo_to_issues_conversion.py` | Converts TODOs to GitHub issues | - |
| `focused_todo_to_issues_conversion.py` | Focused TODO conversion | - |

### Legacy Files
| Script | Purpose | Arguments |
|--------|---------|-----------|
| `legacy_file_inventory.py` | Identifies legacy files | - |
| `cleanup_deadweight.sh` | Removes deadweight code | - |

### Policy Enforcement
| Script | Purpose | Arguments |
|--------|---------|-----------|
| `zero_excuse_culture.py` | Enforces doc update policy | - |

## Usage

### Running All Maintenance Tasks
```bash
python run_all_updates.py  # From parent directory
```

### Code Health Checks
```bash
python deadweight_scan.py
python cli_command_validation.py
python security_scan.py
```

### Documentation Drift
```bash
python doc_drift_audit.py
python doc_drift_cleanup.py
python orphaned_doc_reference_script.py
```

### Integration Audits
```bash
python integration_sdk_audit.py
python cleanup_mock_integrations.py
```

## CI Integration

- `.github/workflows/doc-drift-check.yml` - Documentation drift
- `.github/workflows/deadweight-scan.yml` - Deadweight detection
- `.github/workflows/test-gating-policy.yml` - Test gating

## Frequency

- **Daily**: Deadweight scan, security scan
- **Weekly**: CLI validation, integration audits
- **Monthly**: Full documentation drift audit
- **On PR**: All maintenance checks

## Safe Usage

- Most scripts are read-only and generate reports
- `doc_drift_cleanup.py` modifies markdown files
- `cleanup_deadweight.sh` removes code - review carefully
- `integration_sdk_audit.py` requires GitHub token for issues

## Owner

HyperAgent Maintenance Team
