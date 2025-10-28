#!/usr/bin/env python3
"""
Deadweight Scan Script - GitHub-Friendly Version
Scans the codebase for TODO, NotImplemented, pass, stub, warning, or mock patterns
and generates a summary report (under 100MB for GitHub).
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

class DeadweightScanner:
    """Scans for deadweight code patterns that should not exist in production."""
    
    def __init__(self, root_path: str = "."):
        self.root_path = Path(root_path)
        self.patterns = {
            'TODO': r'\bTODO\b',
            'FIXME': r'\bFIXME\b', 
            'XXX': r'\bXXX\b',
            'HACK': r'\bHACK\b',
            'NotImplementedError': r'NotImplementedError',
            'pass': r'^\s*pass\s*$',
            'stub': r'\bstub\b',
            'mock': r'\bmock\b',
            'fake': r'\bfake\b',
            'placeholder': r'\bplaceholder\b',
            'limited.*mode': r'limited.*mode',
            'fallback': r'fallback.*mock',
            'demo': r'\bdemo\b',
            'example': r'\bexample\b',
            'test.*only': r'test.*only',
            'debug.*only': r'debug.*only'
        }
        
        self.exclude_dirs = {
            '__pycache__', '.git', 'node_modules', '.pytest_cache',
            'venv', 'env', '.venv', '.env', 'build', 'dist'
        }
        
        self.exclude_files = {
            'deadweight_scan.py', 'test_', 'conftest.py'
        }
    
    def scan_file(self, file_path: Path) -> Dict[str, Any]:
        """Scan a single file for deadweight patterns."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')
            
            findings = {}
            total_issues = 0
            
            for pattern_name, pattern_regex in self.patterns.items():
                matches = []
                for line_num, line in enumerate(lines, 1):
                    if re.search(pattern_regex, line, re.IGNORECASE):
                        matches.append({
                            'line': line_num,
                            'content': line.strip()[:100]  # Limit content length
                        })
                        total_issues += 1
                
                if matches:
                    findings[pattern_name] = matches
            
            return {
                'file': str(file_path),
                'findings': findings,
                'total_issues': total_issues,
                'patterns': list(findings.keys())
            }
            
        except Exception as e:
            return {
                'file': str(file_path),
                'error': str(e),
                'findings': {},
                'total_issues': 0,
                'patterns': []
            }
    
    def scan_directory(self, directory: Path) -> Dict[str, Any]:
        """Scan entire directory for deadweight patterns."""
        results = {
            'scanned_files': 0,
            'files_with_deadweight': 0,
            'total_findings': 0,
            'pattern_counts': {},
            'critical_files': [],
            'files_with_deadweight_list': []
        }
        
        # Initialize pattern counts
        for pattern in self.patterns.keys():
            results['pattern_counts'][pattern] = 0
        
        # Scan all files
        for file_path in directory.rglob("*"):
            if file_path.is_file():
                # Skip excluded directories
                if any(part in self.exclude_dirs for part in file_path.parts):
                    continue
                
                # Skip excluded files
                if any(excluded in file_path.name for excluded in self.exclude_files):
                    continue
                
                # Only scan text files
                if file_path.suffix not in {'.py', '.md', '.txt', '.yml', '.yaml', '.json', '.sh'}:
                    continue
                
                results['scanned_files'] += 1
                file_results = self.scan_file(file_path)
                
                if file_results['total_issues'] > 0:
                    results['files_with_deadweight'] += 1
                    results['total_findings'] += file_results['total_issues']
                    
                    # Add to files list
                    results['files_with_deadweight_list'].append(file_results)
                    
                    # Update pattern counts
                    for pattern in file_results['patterns']:
                        results['pattern_counts'][pattern] += len(file_results['findings'][pattern])
                    
                    # Mark as critical if high issue count
                    if file_results['total_issues'] >= 10:
                        results['critical_files'].append(file_results)
        
        # Sort critical files by issue count
        results['critical_files'].sort(key=lambda x: x['total_issues'], reverse=True)
        
        return results
    
    def generate_report(self, results: Dict[str, Any]) -> str:
        """Generate a comprehensive deadweight report for IPFS upload."""
        report_lines = []
        report_lines.append("# Deadweight Scan Report - Comprehensive")
        report_lines.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"**Total Files Scanned**: {results['scanned_files']}")
        report_lines.append(f"**Files with Deadweight**: {results['files_with_deadweight']}")
        report_lines.append(f"**Total Findings**: {results['total_findings']}")
        report_lines.append("")
        
        # Summary by pattern
        report_lines.append("## Summary by Pattern")
        report_lines.append("")
        for pattern, count in results['pattern_counts'].items():
            if count > 0:
                report_lines.append(f"- **{pattern}**: {count}")
        report_lines.append("")
        
        # All files with detailed findings
        report_lines.append("## Detailed Findings by File")
        report_lines.append("")
        
        for file_info in results['files_with_deadweight_list']:
            report_lines.append(f"### {file_info['file']}")
            report_lines.append(f"**Total Issues**: {file_info['total_issues']}")
            report_lines.append(f"**Patterns Found**: {', '.join(file_info['patterns'])}")
            report_lines.append("")
            
            # Show all findings for each pattern
            for pattern, matches in file_info['findings'].items():
                report_lines.append(f"#### {pattern} ({len(matches)} occurrences)")
                report_lines.append("")
                
                for match in matches:
                    report_lines.append(f"**Line {match['line']}**:")
                    report_lines.append("```")
                    report_lines.append(match['content'])
                    report_lines.append("```")
                    report_lines.append("")
                
                report_lines.append("---")
                report_lines.append("")
        
        report_lines.append("## Next Steps")
        report_lines.append("1. Run cleanup script: `bash scripts/maintenance/cleanup_deadweight.sh`")
        report_lines.append("2. Review critical files first")
        report_lines.append("3. Test after cleanup")
        report_lines.append("4. This report is stored on IPFS for decentralized access")
        
        return "\n".join(report_lines)
    
    def generate_cleanup_script(self, results: Dict[str, Any]) -> str:
        """Generate a cleanup script to remove deadweight patterns."""
        script_lines = [
            "#!/bin/bash",
            "# Deadweight Cleanup Script",
            "# Generated by deadweight_scan.py",
            "",
            "echo 'Starting deadweight cleanup...'",
            ""
        ]
        
        for file_info in results['files_with_deadweight_list']:
            file_path = file_info['file']
            script_lines.append(f"echo 'Cleaning {file_path}...'")
            
            # For each pattern, create sed commands to remove or comment out
            for pattern, matches in file_info['findings'].items():
                if pattern in ['TODO', 'FIXME', 'XXX', 'HACK']:
                    # Comment out TODO lines
                    for match in matches:
                        line_num = match['line']
                        script_lines.append(f"sed -i '{line_num}s/^/# TODO REMOVE: /' '{file_path}'")
                elif pattern == 'pass':
                    # Replace empty pass statements with raise NotImplementedError
                    for match in matches:
                        line_num = match['line']
                        script_lines.append(f"sed -i '{line_num}s/^\\s*pass\\s*$/    raise NotImplementedError(\"This feature requires implementation\")/' '{file_path}'")
                elif pattern in ['stub', 'mock', 'fake']:
                    # Comment out mock implementations
                    for match in matches:
                        line_num = match['line']
                        script_lines.append(f"sed -i '{line_num}s/^/# MOCK REMOVED: /' '{file_path}'")
            
            script_lines.append("")
        
        script_lines.extend([
            "echo 'Deadweight cleanup completed.'",
            "echo 'Please review changes before committing.'"
        ])
        
        return "\n".join(script_lines)


def main():
    """Main function to run the deadweight scan."""
    scanner = DeadweightScanner()
    
    print("Scanning for deadweight patterns...")
    results = scanner.scan_directory(Path("hyperkit-agent"))
    
    # Generate report
    report = scanner.generate_report(results)
    
    # Save report
    report_path = Path("hyperkit-agent/REPORTS/DEADWEIGHT_SCAN_REPORT.md")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"Report saved to: {report_path}")
    
    # Generate cleanup script
    cleanup_script = scanner.generate_cleanup_script(results)
    
    cleanup_path = Path("hyperkit-agent/scripts/maintenance/cleanup_deadweight.sh")
    cleanup_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(cleanup_path, 'w', encoding='utf-8') as f:
        f.write(cleanup_script)
    
    # Make script executable
    os.chmod(cleanup_path, 0o755)
    
    print(f"Cleanup script saved to: {cleanup_path}")
    
    print("\nSummary:")
    print(f"  Files scanned: {results['scanned_files']}")
    print(f"  Files with deadweight: {results['files_with_deadweight']}")
    print(f"  Total findings: {results['total_findings']}")
    
    if results['critical_files']:
        print(f"  Critical files: {len(results['critical_files'])}")
        print("\nCritical files with deadweight:")
        for critical in results['critical_files'][:5]:
            print(f"    - {critical['file']}")
    
    # Save JSON results (comprehensive for IPFS)
    json_path = Path("hyperkit-agent/REPORTS/JSON_DATA/deadweight_scan_results.json")
    json_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create comprehensive JSON (for IPFS upload)
    comprehensive_results = {
        'scan_date': datetime.now().isoformat(),
        'scanned_files': results['scanned_files'],
        'files_with_deadweight': results['files_with_deadweight'],
        'total_findings': results['total_findings'],
        'pattern_counts': results['pattern_counts'],
        'critical_files_count': len(results['critical_files']),
        'critical_files': [
            {
                'file': f['file'],
                'total_issues': f['total_issues'],
                'patterns': f['patterns'],
                'findings': f['findings']  # Include all findings
            }
            for f in results['critical_files']
        ],
        'all_files_with_deadweight': results['files_with_deadweight_list']  # Include all files
    }
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(comprehensive_results, f, indent=2)
    
    print(f"Comprehensive JSON saved to: {json_path}")


if __name__ == "__main__":
    main()