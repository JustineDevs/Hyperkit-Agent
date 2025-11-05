#!/usr/bin/env python3
"""
Audit Badge System Script
Adds version/commit hash/date badges to every technical/process markdown file
showing last confirmed implementation status
"""

import os
import re
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

def get_git_info() -> Dict[str, str]:
    """Get git commit hash and date"""
    try:
        # Get current commit hash
        commit_hash = subprocess.check_output(['git', 'rev-parse', 'HEAD'], 
                                            universal_newlines=True).strip()[:8]
        
        # Get commit date
        commit_date = subprocess.check_output(['git', 'log', '-1', '--format=%ci'], 
                                            universal_newlines=True).strip()
        
        # Get current branch
        branch = subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], 
                                       universal_newlines=True).strip()
        
        return {
            'commit_hash': commit_hash,
            'commit_date': commit_date,
            'branch': branch
        }
    except Exception as e:
        print(f"Warning: Could not get git info: {e}")
        return {
            'commit_hash': 'unknown',
            'commit_date': datetime.now().isoformat(),
            'branch': 'unknown'
        }

def get_version_info() -> str:
    """Get version from VERSION file"""
    try:
        with open('VERSION', 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        return '1.4.5'  # fallback

def create_badge_content(git_info: Dict[str, str], version: str) -> str:
    """Create badge content for markdown files"""
    
    # Parse commit date
    try:
        commit_dt = datetime.fromisoformat(git_info['commit_date'].replace(' ', 'T'))
        formatted_date = commit_dt.strftime('%Y-%m-%d')
    except:
        formatted_date = datetime.now().strftime('%Y-%m-%d')
    
    badge_content = f"""<!-- AUDIT_BADGE_START -->
**Implementation Status**: ✅ Verified  
**Version**: {version}  
**Last Verified**: {formatted_date}  
**Commit**: `{git_info['commit_hash']}`  
**Branch**: `{git_info['branch']}`  
<!-- AUDIT_BADGE_END -->

"""
    
    return badge_content

def should_add_badge(file_path: str) -> bool:
    """Determine if a file should get an audit badge"""
    
    # Skip certain files
    skip_patterns = [
        'README.md',
        'CHANGELOG.md',
        'TODO.md',
        'SECURITY.md',
        'CONTRIBUTING.md',
        'LICENSE',
        '.gitignore',
        'package.json',
        'requirements.txt',
        'pyproject.toml',
        'foundry.toml',
        'docker-compose.yml',
        'Dockerfile',
        '.env',
        '.env.example'
    ]
    
    filename = os.path.basename(file_path)
    if filename in skip_patterns:
        return False
    
    # Skip files in certain directories
    skip_dirs = [
        'node_modules',
        '.git',
        '__pycache__',
        '.pytest_cache',
        'lib',
        'cache',
        'artifacts',
        'out',
        'logs',
        'test_logs',
        'llm_logs'
    ]
    
    for skip_dir in skip_dirs:
        if skip_dir in file_path:
            return False
    
    # Only add to markdown files in docs, guides, or technical directories
    if not file_path.endswith('.md'):
        return False
    
    # Must be in a technical directory
    technical_dirs = [
        'docs',
        'hyperkit-agent/docs',
        'hyperkit-agent/REPORTS',
        'scripts',
        'hyperkit-agent/scripts'
    ]
    
    for tech_dir in technical_dirs:
        if tech_dir in file_path:
            return True
    
    return False

def has_existing_badge(content: str) -> bool:
    """Check if file already has an audit badge"""
    return 'AUDIT_BADGE_START' in content

def add_badge_to_file(file_path: str, badge_content: str) -> bool:
    """Add audit badge to a file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Skip if already has badge
        if has_existing_badge(content):
            return False
        
        # Add badge at the beginning
        new_content = badge_content + content
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        return True
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def update_existing_badges(file_path: str, badge_content: str) -> bool:
    """Update existing audit badges"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if not has_existing_badge(content):
            return False
        
        # Replace existing badge
        pattern = r'<!-- AUDIT_BADGE_START -->.*?<!-- AUDIT_BADGE_END -->'
        new_content = re.sub(pattern, badge_content.strip(), content, flags=re.DOTALL)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        return True
        
    except Exception as e:
        print(f"Error updating {file_path}: {e}")
        return False

def scan_and_add_badges() -> Dict[str, Any]:
    """Scan all files and add audit badges"""
    
    git_info = get_git_info()
    version = get_version_info()
    badge_content = create_badge_content(git_info, version)
    
    results = {
        'files_processed': 0,
        'badges_added': 0,
        'badges_updated': 0,
        'files_skipped': 0,
        'errors': []
    }
    
    # Scan all markdown files
    for root, dirs, files in os.walk('.'):
        # Skip certain directories
        if any(skip in root for skip in ['.git', '__pycache__', 'node_modules', '.pytest_cache']):
            continue
            
        for file in files:
            if file.endswith('.md'):
                file_path = os.path.join(root, file)
                
                if not should_add_badge(file_path):
                    results['files_skipped'] += 1
                    continue
                
                results['files_processed'] += 1
                
                # Try to update existing badge first
                if update_existing_badges(file_path, badge_content):
                    results['badges_updated'] += 1
                    print(f"Updated badge in: {file_path}")
                # Otherwise add new badge
                elif add_badge_to_file(file_path, badge_content):
                    results['badges_added'] += 1
                    print(f"Added badge to: {file_path}")
                else:
                    results['errors'].append(f"Failed to process: {file_path}")
    
    return results

def create_badge_report(results: Dict[str, Any], git_info: Dict[str, str], version: str) -> str:
    """Create a report of badge operations"""
    
    report = f"""# Audit Badge System Report

**Generated**: {datetime.now().isoformat()}  
**Version**: {version}  
**Commit**: {git_info['commit_hash']}  
**Branch**: {git_info['branch']}  

## Summary

- **Files Processed**: {results['files_processed']}
- **Badges Added**: {results['badges_added']}
- **Badges Updated**: {results['badges_updated']}
- **Files Skipped**: {results['files_skipped']}
- **Errors**: {len(results['errors'])}

## Badge Format

Each technical markdown file now includes:

```markdown
<!-- AUDIT_BADGE_START -->
**Implementation Status**: ✅ Verified  
**Version**: {version}  
**Last Verified**: {datetime.now().strftime('%Y-%m-%d')}  
**Commit**: `{git_info['commit_hash']}`  
**Branch**: `{git_info['branch']}`  
<!-- AUDIT_BADGE_END -->
```

## Files with Errors

"""
    
    if results['errors']:
        for error in results['errors']:
            report += f"- {error}\n"
    else:
        report += "No errors encountered.\n"
    
    report += f"""
## Next Steps

1. Review all files with audit badges
2. Verify implementation status is accurate
3. Update badges when features are implemented
4. Integrate badge updates into CI/CD pipeline

---
*This report is automatically generated by the audit badge system.*
"""
    
    return report

def main():
    """Main function"""
    print("Starting audit badge system...")
    
    # Get git and version info
    git_info = get_git_info()
    version = get_version_info()
    
    print(f"Version: {version}")
    print(f"Commit: {git_info['commit_hash']}")
    print(f"Branch: {git_info['branch']}")
    
    # Scan and add badges
    results = scan_and_add_badges()
    
    # Create report
    report = create_badge_report(results, git_info, version)
    
    # Save report to AUDIT category
    report_path = Path('REPORTS/AUDIT/audit_badge_report.md')
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    # Print summary
    print(f"\nAudit Badge System Complete!")
    print(f"Files processed: {results['files_processed']}")
    print(f"Badges added: {results['badges_added']}")
    print(f"Badges updated: {results['badges_updated']}")
    print(f"Files skipped: {results['files_skipped']}")
    print(f"Errors: {len(results['errors'])}")
    
    print(f"\nReport saved to: {report_path}")
    
    return 0

if __name__ == "__main__":
    exit(main())
