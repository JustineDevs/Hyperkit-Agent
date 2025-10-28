# Parallel Script Runner Report
Generated: 2025-10-28T21:06:31.415117
Duration: 0.00 seconds

## Summary
- Total Workflows: 8
- Successful: 0
- Failed: 8
- Critical Workflows: 4
- Critical Failures: 4
- CI Should Block: YES
- Overall Status: FAIL

## Critical Failures
The following critical workflows failed:

### version_update
**Status**: error
**Error**: Script not found: hyperkit-agent\scripts\update_version_in_docs.py

### doc_drift_audit
**Status**: error
**Error**: Script not found: hyperkit-agent\scripts\doc_drift_audit.py

### deadweight_scan
**Status**: error
**Error**: Script not found: hyperkit-agent\scripts\deadweight_scan.py

### cli_command_validation
**Status**: error
**Error**: Script not found: hyperkit-agent\scripts\cli_command_validation.py

## Detailed Results

### version_update
**Description**: Update version information across all docs
**Status**: error
**Critical**: Yes

**Error**: Script not found: hyperkit-agent\scripts\update_version_in_docs.py

### integration_sdk_audit
**Description**: Audit SDK integrations
**Status**: error
**Critical**: No

**Error**: Script not found: hyperkit-agent\scripts\integration_sdk_audit.py

### cli_command_validation
**Description**: Validate CLI commands
**Status**: error
**Critical**: Yes

**Error**: Script not found: hyperkit-agent\scripts\cli_command_validation.py

### legacy_file_inventory
**Description**: Inventory legacy files
**Status**: error
**Critical**: No

**Error**: Script not found: hyperkit-agent\scripts\legacy_file_inventory.py

### doc_drift_audit
**Description**: Audit documentation for drift
**Status**: error
**Critical**: Yes

**Error**: Script not found: hyperkit-agent\scripts\doc_drift_audit.py

### deadweight_scan
**Description**: Scan for deadweight patterns
**Status**: error
**Critical**: Yes

**Error**: Script not found: hyperkit-agent\scripts\deadweight_scan.py

### audit_badge_system
**Description**: Add audit badges to docs
**Status**: error
**Critical**: No

**Error**: Script not found: hyperkit-agent\scripts\audit_badge_system.py

### todo_to_issues_conversion
**Description**: Convert TODOs to GitHub issues
**Status**: error
**Critical**: No

**Error**: Script not found: hyperkit-agent\scripts\focused_todo_to_issues_conversion.py
