# Parallel Script Runner Report
Generated: 2025-10-28T20:28:19.121359
Duration: 29.25 seconds

## Summary
- Total Workflows: 8
- Successful: 3
- Failed: 5
- Critical Workflows: 4
- Critical Failures: 1
- CI Should Block: YES
- Overall Status: FAIL

## Critical Failures
The following critical workflows failed:

### cli_command_validation
**Status**: error
**Error**: Unknown error

## Detailed Results

### doc_drift_audit
**Description**: Audit documentation for drift
**Status**: success
**Critical**: Yes

**Output**:
```
Running Documentation Drift Audit...
============================================================
Audit Summary:
  Total Issues: 255
  High Severity: 94
  Medium Severity: 161
  Low Severity: 0
Audit report saved: C:\Users\JustineDevs\Downloads\HyperAgent\hyperkit-agent\REPORTS\doc_drift_audit_20251028_202750.json

============================================================
Detailed Results:
============================================================
[MED] docs\GOVERNANCE.md:114 - roadmap
[MED...
```

### integration_sdk_audit
**Description**: Audit SDK integrations
**Status**: error
**Critical**: No

**Error**: Unknown error

**Output**:
```
Starting Integration SDK Audit...

```

### cli_command_validation
**Description**: Validate CLI commands
**Status**: error
**Critical**: Yes

**Error**: Unknown error

**Output**:
```
Starting CLI command validation...
Error discovering commands: python: can't open file 'C:\\Users\\JustineDevs\\Downloads\\HyperAgent\\cli\\main.py': [Errno 2] No such file or directory

Discovered commands: []
No commands discovered, using known commands
Testing command: generate
Testing command: deploy
Testing command: audit
Testing command: batch-audit
Testing command: verify
Testing command: monitor
Testing command: config
Testing command: workflow
Testing command: status

```

### audit_badge_system
**Description**: Add audit badges to docs
**Status**: error
**Critical**: No

**Error**: Unknown error

**Output**:
```
Starting audit badge system...
Version: 1.4.6
Commit: d5465090
Branch: main
Updated badge in: .\docs\DIRECTORY_STRUCTURE.md
Updated badge in: .\docs\GOVERNANCE.md
Updated badge in: .\docs\PRODUCTION_DEPLOYMENT_GUIDE.md
Updated badge in: .\docs\realworld-prompts-for-hyperkit.md
Updated badge in: .\docs\ROADMAP.md
Updated badge in: .\docs\VERSION_MANAGEMENT.md
Updated badge in: .\docs\legal\PRIVACY.md
Updated badge in: .\docs\legal\TERMS.md
Updated badge in: .\docs\RAG_TEMPLATES\UPLOAD_PROCESS.md
...
```

### version_update
**Description**: Update version information across all docs
**Status**: success
**Critical**: Yes

**Output**:
```
Updating version to 1.4.6 (commit: d546509, date: %Y->- (HEAD -> main, origin/main))
Updated: hyperkit-agent/REPORTS\DEADWEIGHT_SCAN_REPORT.md
Updated 1 files

```

### todo_to_issues_conversion
**Description**: Convert TODOs to GitHub issues
**Status**: error
**Critical**: No

**Error**: Unknown error

**Output**:
```
Scanning our codebase for TODO/TBD/FIXME items...
Found 434 TODO items in our codebase

```

### legacy_file_inventory
**Description**: Inventory legacy files
**Status**: error
**Critical**: No

**Error**: Unknown error

**Output**:
```
Scanning for legacy files and unimplemented features...

```

### deadweight_scan
**Description**: Scan for deadweight patterns
**Status**: success
**Critical**: Yes

**Output**:
```
Scanning for deadweight patterns...
Report saved to: hyperkit-agent\REPORTS\DEADWEIGHT_SCAN_REPORT.md
Cleanup script saved to: hyperkit-agent\scripts\cleanup_deadweight.sh

Summary:
  Files scanned: 402
  Files with deadweight: 191
  Total findings: 245086
JSON results saved to: hyperkit-agent\REPORTS\JSON_DATA\deadweight_scan_results.json

```
