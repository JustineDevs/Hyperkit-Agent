#!/usr/bin/env python3
"""
Orphaned Doc Reference Script
Validates that all system commands referenced in docs exist in CLI or are flagged DEPRECATED.
Ensures documentation accuracy and prevents broken references.
"""

import os
import re
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Any, Set, Tuple
from datetime import datetime

class OrphanedDocReferenceValidator:
    """Validates CLI command references in documentation."""
    
    def __init__(self, root_path: str = "."):
        self.root_path = Path(root_path)
        self.cli_commands = set()
        self.doc_references = []
        self.orphaned_references = []
        self.deprecated_commands = set()
        
        # Patterns to match CLI command references
        self.command_patterns = [
            r'`hyperagent\s+([a-zA-Z0-9\-_]+)`',  # `hyperagent command`
            r'hyperagent\s+([a-zA-Z0-9\-_]+)',    # hyperagent command
            r'`([a-zA-Z0-9\-_]+)`',               # `command` (in CLI context)
            r'npm run ([a-zA-Z0-9\-_:]+)',       # npm run command
            r'`npm run ([a-zA-Z0-9\-_:]+)`',     # `npm run command`
        ]
        
        # Commands that should be flagged as deprecated
        self.known_deprecated = {
            'main.py', 'python main.py', 'python scripts/',
            'obsidian', 'lazai', 'mock', 'demo'
        }
    
    def discover_cli_commands(self) -> Set[str]:
        """Discover all available CLI commands."""
        commands = set()
        
        try:
            # Get help output from main CLI
            result = subprocess.run(
                [sys.executable, 'hyperkit-agent/cli/main.py', '--help'],
                cwd=self.root_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                help_output = result.stdout
                
                # Extract commands from help output
                command_lines = re.findall(r'^\s*([a-zA-Z0-9\-_]+)\s+', help_output, re.MULTILINE)
                commands.update(command_lines)
                
                # Extract subcommands
                subcommand_lines = re.findall(r'^\s*([a-zA-Z0-9\-_]+)\s+', help_output, re.MULTILINE)
                commands.update(subcommand_lines)
        
        except Exception as e:
            print(f"Warning: Could not discover CLI commands: {e}")
        
        # Also check command files directly
        cli_commands_dir = self.root_path / "hyperkit-agent/cli/commands"
        if cli_commands_dir.exists():
            for cmd_file in cli_commands_dir.glob("*.py"):
                if not cmd_file.name.startswith("__"):
                    command_name = cmd_file.stem.replace("_", "-")
                    commands.add(command_name)
        
        # Add npm commands from package.json
        package_json_path = self.root_path / "package.json"
        if package_json_path.exists():
            try:
                with open(package_json_path, 'r', encoding='utf-8') as f:
                    package_data = json.load(f)
                    scripts = package_data.get('scripts', {})
                    for script_name in scripts.keys():
                        commands.add(f"npm run {script_name}")
            except Exception as e:
                print(f"Warning: Could not read package.json: {e}")
        
        self.cli_commands = commands
        return commands
    
    def scan_documentation(self) -> List[Dict[str, Any]]:
        """Scan all documentation files for CLI command references."""
        references = []
        
        # Scan markdown files
        for md_file in self.root_path.rglob("*.md"):
            if self._should_scan_file(md_file):
                file_references = self._scan_file_for_commands(md_file)
                references.extend(file_references)
        
        # Scan other documentation files
        for ext in ['.rst', '.txt', '.yml', '.yaml']:
            for doc_file in self.root_path.rglob(f"*{ext}"):
                if self._should_scan_file(doc_file):
                    file_references = self._scan_file_for_commands(doc_file)
                    references.extend(file_references)
        
        self.doc_references = references
        return references
    
    def _should_scan_file(self, file_path: Path) -> bool:
        """Determine if a file should be scanned."""
        # Skip certain directories
        skip_dirs = {'__pycache__', '.git', 'node_modules', '.pytest_cache', 'venv', 'env'}
        if any(skip_dir in str(file_path) for skip_dir in skip_dirs):
            return False
        
        # Skip certain file patterns
        skip_patterns = {'test_', 'conftest.py', 'setup.py', 'requirements'}
        if any(file_path.name.startswith(pattern) for pattern in skip_patterns):
            return False
        
        return True
    
    def _scan_file_for_commands(self, file_path: Path) -> List[Dict[str, Any]]:
        """Scan a single file for CLI command references."""
        references = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')
        except Exception:
            return references
        
        for line_num, line in enumerate(lines, 1):
            for pattern in self.command_patterns:
                matches = re.finditer(pattern, line, re.IGNORECASE)
                for match in matches:
                    command = match.group(1)
                    references.append({
                        'file': str(file_path),
                        'line': line_num,
                        'command': command,
                        'context': line.strip(),
                        'pattern': pattern
                    })
        
        return references
    
    def validate_references(self) -> Dict[str, Any]:
        """Validate all found references against available CLI commands."""
        orphaned = []
        valid = []
        deprecated = []
        
        for ref in self.doc_references:
            command = ref['command']
            
            if command in self.known_deprecated:
                deprecated.append(ref)
            elif command in self.cli_commands:
                valid.append(ref)
            else:
                # Check if it's a partial match or subcommand
                is_valid = False
                for cli_cmd in self.cli_commands:
                    if command in cli_cmd or cli_cmd in command:
                        is_valid = True
                        break
                
                if is_valid:
                    valid.append(ref)
                else:
                    orphaned.append(ref)
        
        self.orphaned_references = orphaned
        
        return {
            'total_references': len(self.doc_references),
            'valid_references': len(valid),
            'orphaned_references': len(orphaned),
            'deprecated_references': len(deprecated),
            'available_commands': len(self.cli_commands),
            'orphaned_details': orphaned,
            'deprecated_details': deprecated
        }
    
    def generate_report(self, validation_results: Dict[str, Any]) -> str:
        """Generate a comprehensive validation report."""
        report_lines = [
            "# Orphaned Doc Reference Validation Report",
            f"Generated: {datetime.now().isoformat()}",
            "",
            "## Summary",
            f"- Total References Found: {validation_results['total_references']}",
            f"- Valid References: {validation_results['valid_references']}",
            f"- Orphaned References: {validation_results['orphaned_references']}",
            f"- Deprecated References: {validation_results['deprecated_references']}",
            f"- Available CLI Commands: {validation_results['available_commands']}",
            ""
        ]
        
        if validation_results['orphaned_references'] > 0:
            report_lines.extend([
                "## Orphaned References",
                "These commands are referenced in documentation but don't exist in the CLI:",
                ""
            ])
            
            for ref in validation_results['orphaned_details']:
                report_lines.extend([
                    f"### {ref['command']}",
                    f"**File**: {ref['file']}",
                    f"**Line**: {ref['line']}",
                    f"**Context**: `{ref['context']}`",
                    ""
                ])
        
        if validation_results['deprecated_references'] > 0:
            report_lines.extend([
                "## Deprecated References",
                "These commands are flagged as deprecated and should be updated:",
                ""
            ])
            
            for ref in validation_results['deprecated_details']:
                report_lines.extend([
                    f"### {ref['command']}",
                    f"**File**: {ref['file']}",
                    f"**Line**: {ref['line']}",
                    f"**Context**: `{ref['context']}`",
                    ""
                ])
        
        report_lines.extend([
            "## Available CLI Commands",
            "All currently available CLI commands:",
            ""
        ])
        
        for cmd in sorted(self.cli_commands):
            report_lines.append(f"- `{cmd}`")
        
        report_lines.extend([
            "",
            "## Recommendations",
            ""
        ])
        
        if validation_results['orphaned_references'] > 0:
            report_lines.extend([
                "1. **Fix Orphaned References**: Update documentation to use valid CLI commands",
                "2. **Remove Deprecated Commands**: Replace deprecated command references",
                "3. **Add Missing Commands**: Implement missing commands or remove references",
                ""
            ])
        else:
            report_lines.extend([
                "✅ All command references are valid!",
                ""
            ])
        
        return "\n".join(report_lines)
    
    def generate_cleanup_script(self, validation_results: Dict[str, Any]) -> str:
        """Generate a script to fix orphaned references."""
        script_lines = [
            "#!/bin/bash",
            "# Orphaned Reference Cleanup Script",
            "# Generated by orphaned_doc_reference_script.py",
            "",
            "echo 'Starting orphaned reference cleanup...'",
            ""
        ]
        
        # Group orphaned references by file
        files_to_fix = {}
        for ref in validation_results['orphaned_details']:
            file_path = ref['file']
            if file_path not in files_to_fix:
                files_to_fix[file_path] = []
            files_to_fix[file_path].append(ref)
        
        for file_path, refs in files_to_fix.items():
            script_lines.append(f"echo 'Fixing {file_path}...'")
            
            for ref in refs:
                line_num = ref['line']
                command = ref['command']
                # Suggest replacement (this would need manual review)
                script_lines.append(f"# Line {line_num}: Replace '{command}' with valid command")
                script_lines.append(f"# sed -i '{line_num}s/{command}/VALID_COMMAND/' '{file_path}'")
            
            script_lines.append("")
        
        script_lines.extend([
            "echo 'Orphaned reference cleanup completed.'",
            "echo 'Please review changes before committing.'"
        ])
        
        return "\n".join(script_lines)


def main():
    """Main function to run orphaned reference validation."""
    validator = OrphanedDocReferenceValidator()
    
    print("Orphaned Doc Reference Validator")
    print("=" * 40)
    
    # Discover CLI commands
    print("Discovering CLI commands...")
    commands = validator.discover_cli_commands()
    print(f"Found {len(commands)} CLI commands")
    
    # Scan documentation
    print("Scanning documentation...")
    references = validator.scan_documentation()
    print(f"Found {len(references)} command references")
    
    # Validate references
    print("Validating references...")
    results = validator.validate_references()
    
    # Generate report
    report = validator.generate_report(results)
    
    # Save MD report to QUALITY category
    report_path = Path("REPORTS/QUALITY/orphaned_doc_reference_report.md")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"Report saved to: {report_path}")
    
    # Generate cleanup script
    cleanup_script = validator.generate_cleanup_script(results)
    
    cleanup_path = Path("scripts/cleanup_orphaned_references.sh")
    cleanup_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(cleanup_path, 'w', encoding='utf-8') as f:
        f.write(cleanup_script)
    
    # Make script executable
    os.chmod(cleanup_path, 0o755)
    
    print(f"Cleanup script saved to: {cleanup_path}")
    
    # Print summary
    print("\nSummary:")
    print(f"  Total references: {results['total_references']}")
    print(f"  Valid references: {results['valid_references']}")
    print(f"  Orphaned references: {results['orphaned_references']}")
    print(f"  Deprecated references: {results['deprecated_references']}")
    
    if results['orphaned_references'] > 0:
        print(f"\nOrphaned references found:")
        for ref in results['orphaned_details'][:5]:  # Show first 5
            print(f"  - {ref['command']} in {ref['file']}:{ref['line']}")
        if len(results['orphaned_details']) > 5:
            print(f"  ... and {len(results['orphaned_details']) - 5} more")
    
    # Save JSON results to JSON_DATA directory
    json_path = Path("REPORTS/JSON_DATA/orphaned_doc_reference_results.json")
    json_path.parent.mkdir(parents=True, exist_ok=True)
    
    full_results = {
        "validation_results": results,
        "cli_commands": list(commands),
        "doc_references": references,
        "timestamp": datetime.now().isoformat()
    }
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(full_results, f, indent=2)
    
    print(f"JSON results saved to: {json_path}")


if __name__ == "__main__":
    main()
