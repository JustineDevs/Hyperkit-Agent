#!/usr/bin/env python3
"""
Legacy File Inventory Script
Identifies and catalogs legacy files that need to be archived or marked as NOT IMPLEMENTED
"""

import os
import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

def scan_for_legacy_references() -> Dict[str, Any]:
    """Scan codebase for legacy references and unimplemented features"""
    
    legacy_patterns = {
        'python_scripts': [
            r'python scripts/',
            r'python main\.py',
            r'\.py --',
            r'python [a-zA-Z_]+\.py'
        ],
        'shell_scripts': [
            r'bash scripts/',
            r'\./scripts/',
            r'\.sh --',
            r'[a-zA-Z_]+\.sh'
        ],
        'unimplemented_commands': [
            r'hyperagent backup_',
            r'hyperagent restore_',
            r'hyperagent emergency_',
            r'hyperagent verify_',
            r'hyperagent notify_',
            r'hyperagent isolate_',
            r'hyperagent archive_',
            r'hyperagent compliance_'
        ],
        'future_tense': [
            r'will be',
            r'will have',
            r'will provide',
            r'will support',
            r'will enable',
            r'will implement',
            r'will create',
            r'will generate'
        ],
        'todo_markers': [
            r'TODO:',
            r'FIXME:',
            r'XXX:',
            r'NOTE:',
            r'HACK:',
            r'BUG:'
        ]
    }
    
    results = {
        'scan_date': datetime.now().isoformat(),
        'legacy_files': [],
        'unimplemented_features': [],
        'future_tense_docs': [],
        'todo_files': [],
        'summary': {}
    }
    
    # Scan all markdown files
    for root, dirs, files in os.walk('.'):
        # Skip certain directories
        if any(skip in root for skip in ['.git', '__pycache__', 'node_modules', '.pytest_cache']):
            continue
            
        for file in files:
            if file.endswith(('.md', '.txt', '.rst')):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        lines = content.split('\n')
                        
                    # Check for legacy patterns
                    for pattern_type, patterns in legacy_patterns.items():
                        for pattern in patterns:
                            matches = re.findall(pattern, content, re.IGNORECASE)
                            if matches:
                                if pattern_type not in results:
                                    results[pattern_type] = []
                                
                                results[pattern_type].append({
                                    'file': file_path,
                                    'pattern': pattern,
                                    'matches': matches,
                                    'lines': [i+1 for i, line in enumerate(lines) if re.search(pattern, line, re.IGNORECASE)]
                                })
                                
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")
    
    # Generate summary
    results['summary'] = {
        'total_files_scanned': len([f for root, dirs, files in os.walk('.') for f in files if f.endswith(('.md', '.txt', '.rst'))]),
        'legacy_references': len(results.get('python_scripts', [])) + len(results.get('shell_scripts', [])),
        'unimplemented_features': len(results.get('unimplemented_commands', [])),
        'future_tense_docs': len(results.get('future_tense', [])),
        'todo_files': len(results.get('todo_markers', []))
    }
    
    return results

def identify_disaster_recovery_files() -> List[Dict[str, Any]]:
    """Identify disaster recovery and emergency response files"""
    
    disaster_files = []
    
    # Known disaster recovery files
    disaster_patterns = [
        'DISASTER_RECOVERY',
        'EMERGENCY_RESPONSE',
        'BACKUP',
        'RESTORE',
        'RECOVERY',
        'INCIDENT',
        'CRISIS'
    ]
    
    for root, dirs, files in os.walk('.'):
        for file in files:
            if any(pattern in file.upper() for pattern in disaster_patterns):
                file_path = os.path.join(root, file)
                disaster_files.append({
                    'file': file_path,
                    'type': 'disaster_recovery',
                    'status': 'needs_review'
                })
    
    return disaster_files

def identify_legacy_scripts() -> List[Dict[str, Any]]:
    """Identify legacy script files"""
    
    legacy_scripts = []
    
    # Look for script directories
    script_dirs = ['scripts', 'bin', 'tools', 'utils']
    
    for script_dir in script_dirs:
        if os.path.exists(script_dir):
            for root, dirs, files in os.walk(script_dir):
                for file in files:
                    if file.endswith(('.py', '.sh', '.bat', '.ps1')):
                        file_path = os.path.join(root, file)
                        legacy_scripts.append({
                            'file': file_path,
                            'type': 'script',
                            'status': 'needs_review'
                        })
    
    return legacy_scripts

def create_archive_recommendations(scan_results: Dict[str, Any]) -> Dict[str, Any]:
    """Create recommendations for archiving or marking files as NOT IMPLEMENTED"""
    
    recommendations = {
        'archive_candidates': [],
        'not_implemented_candidates': [],
        'update_candidates': [],
        'delete_candidates': []
    }
    
    # Files with many legacy references should be archived
    for file_data in scan_results.get('python_scripts', []):
        if len(file_data['matches']) > 5:
            recommendations['archive_candidates'].append({
                'file': file_data['file'],
                'reason': 'Multiple legacy script references',
                'matches': len(file_data['matches'])
            })
    
    # Files with unimplemented commands should be marked NOT IMPLEMENTED
    for file_data in scan_results.get('unimplemented_commands', []):
        recommendations['not_implemented_candidates'].append({
            'file': file_data['file'],
            'reason': 'References unimplemented CLI commands',
            'commands': file_data['matches']
        })
    
    # Files with future tense should be updated
    for file_data in scan_results.get('future_tense', []):
        recommendations['update_candidates'].append({
            'file': file_data['file'],
            'reason': 'Contains future tense language',
            'instances': len(file_data['matches'])
        })
    
    return recommendations

def generate_cleanup_script(recommendations: Dict[str, Any]) -> str:
    """Generate a cleanup script based on recommendations"""
    
    script_content = '''#!/bin/bash
# Legacy File Cleanup Script
# Generated by legacy_file_inventory.py

echo "Starting legacy file cleanup..."

# Create archive directory
mkdir -p ARCHIVE/legacy_files
mkdir -p ARCHIVE/not_implemented

# Archive files with multiple legacy references
'''
    
    for candidate in recommendations['archive_candidates']:
        script_content += f'''
# Archive {candidate['file']} - {candidate['reason']}
if [ -f "{candidate['file']}" ]; then
    echo "Archiving {candidate['file']}..."
    mv "{candidate['file']}" "ARCHIVE/legacy_files/"
    echo "Archived {candidate['file']}"
fi
'''
    
    script_content += '''
# Add NOT IMPLEMENTED banners to files
'''
    
    for candidate in recommendations['not_implemented_candidates']:
        script_content += f'''
# Add NOT IMPLEMENTED banner to {candidate['file']}
if [ -f "{candidate['file']}" ]; then
    echo "Adding NOT IMPLEMENTED banner to {candidate['file']}..."
    # Create backup
    cp "{candidate['file']}" "{candidate['file']}.backup"
    
    # Add banner
    cat > "{candidate['file']}.tmp" << 'EOF'
> **NOT IMPLEMENTED BANNER**  
> This process references scripts or procedures that are not CLI-integrated.  
> These features are documented but not executable via `hyperagent` CLI.  
> See implementation status in `REPORTS/IMPLEMENTATION_STATUS.md`.
> 
> 
> 
EOF
    
    cat "{candidate['file']}" >> "{candidate['file']}.tmp"
    mv "{candidate['file']}.tmp" "{candidate['file']}"
    echo "Added NOT IMPLEMENTED banner to {candidate['file']}"
fi
'''
    
    script_content += '''
echo "Legacy file cleanup completed!"
echo "Review ARCHIVE/ directory for archived files"
echo "Review files with NOT IMPLEMENTED banners"
'''
    
    return script_content

def main():
    """Main function"""
    print("Scanning for legacy files and unimplemented features...")
    
    # Scan for legacy references
    scan_results = scan_for_legacy_references()
    
    # Identify disaster recovery files
    disaster_files = identify_disaster_recovery_files()
    
    # Identify legacy scripts
    legacy_scripts = identify_legacy_scripts()
    
    # Create recommendations
    recommendations = create_archive_recommendations(scan_results)
    
    # Generate cleanup script
    cleanup_script = generate_cleanup_script(recommendations)
    
    # Save results
    results = {
        'scan_results': scan_results,
        'disaster_files': disaster_files,
        'legacy_scripts': legacy_scripts,
        'recommendations': recommendations
    }
    
    # Write JSON report to JSON_DATA directory
    json_path = Path('REPORTS/JSON_DATA/legacy_file_inventory.json')
    json_path.parent.mkdir(parents=True, exist_ok=True)
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    # Write cleanup script
    with open('scripts/cleanup_legacy_files.sh', 'w') as f:
        f.write(cleanup_script)
    
    # Make cleanup script executable
    os.chmod('scripts/cleanup_legacy_files.sh', 0o755)
    
    # Print summary
    print(f"\nLegacy File Inventory Complete!")
    print(f"Files scanned: {scan_results['summary']['total_files_scanned']}")
    print(f"Legacy references found: {scan_results['summary']['legacy_references']}")
    print(f"Unimplemented features: {scan_results['summary']['unimplemented_features']}")
    print(f"Future tense docs: {scan_results['summary']['future_tense_docs']}")
    print(f"TODO files: {scan_results['summary']['todo_files']}")
    print(f"\nArchive candidates: {len(recommendations['archive_candidates'])}")
    print(f"NOT IMPLEMENTED candidates: {len(recommendations['not_implemented_candidates'])}")
    print(f"Update candidates: {len(recommendations['update_candidates'])}")
    
    print(f"\nReports generated:")
    print(f"- {json_path}")
    print(f"- scripts/cleanup_legacy_files.sh")
    
    return 0

if __name__ == "__main__":
    exit(main())
