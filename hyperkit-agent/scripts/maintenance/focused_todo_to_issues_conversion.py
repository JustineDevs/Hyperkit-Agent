#!/usr/bin/env python3
"""
Focused TODO to Issues Conversion Script
Scans only our actual codebase for TODO/TBD sections and converts them into GitHub issues
Excludes external libraries and generated files
"""

import os
import re
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

def get_git_info() -> Dict[str, str]:
    """Get git commit hash and date"""
    try:
        commit_hash = subprocess.check_output(['git', 'rev-parse', 'HEAD'], 
                                            universal_newlines=True).strip()[:8]
        branch = subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], 
                                       universal_newlines=True).strip()
        return {
            'commit_hash': commit_hash,
            'branch': branch
        }
    except Exception as e:
        print(f"Warning: Could not get git info: {e}")
        return {
            'commit_hash': 'unknown',
            'branch': 'unknown'
        }

def should_scan_file(file_path: str) -> bool:
    """Determine if a file should be scanned for TODOs"""
    
    # Skip certain directories
    skip_dirs = [
        '.git', '__pycache__', 'node_modules', '.pytest_cache', 
        'lib', 'cache', 'artifacts', 'out', 'logs', 'test_logs', 
        'llm_logs', '.benchmarks', 'hyperkit_agent.egg-info'
    ]
    
    for skip_dir in skip_dirs:
        if skip_dir in file_path:
            return False
    
    # Skip certain file types
    skip_extensions = ['.pyc', '.pyo', '.so', '.dll', '.exe', '.lock']
    if any(file_path.endswith(ext) for ext in skip_extensions):
        return False
    
    # Skip certain files
    skip_files = [
        'package-lock.json', 'yarn.lock', 'poetry.lock',
        'requirements.txt',
        'foundry.lock', 'foundry.toml'
    ]
    
    filename = os.path.basename(file_path)
    if filename in skip_files:
        return False
    
    # Only scan our actual codebase files
    allowed_extensions = ['.py', '.md', '.js', '.ts', '.sol', '.yaml', '.yml', '.json', '.txt']
    if not any(file_path.endswith(ext) for ext in allowed_extensions):
        return False
    
    # Must be in our project directories
    project_dirs = [
        'hyperkit-agent/cli',
        'hyperkit-agent/services',
        'hyperkit-agent/core',
        'hyperkit-agent/scripts',
        'hyperkit-agent/tests',
        'hyperkit-agent/docs',
        'docs',
        'scripts'
    ]
    
    for project_dir in project_dirs:
        if project_dir in file_path:
            return True
    
    return False

def scan_for_todos() -> List[Dict[str, Any]]:
    """Scan codebase for TODO/TBD/FIXME markers in our actual code"""
    
    todo_patterns = [
        r'TODO:?\s*(.+)',
        r'TBD:?\s*(.+)',
        r'FIXME:?\s*(.+)',
        r'XXX:?\s*(.+)',
        r'HACK:?\s*(.+)',
        r'BUG:?\s*(.+)',
        r'NOTE:?\s*(.+)',
        r'REVIEW:?\s*(.+)'
    ]
    
    todos = []
    
    # Scan all files
    for root, dirs, files in os.walk('.'):
        # Skip certain directories
        if any(skip in root for skip in ['.git', '__pycache__', 'node_modules', '.pytest_cache', 'lib']):
            continue
            
        for file in files:
            file_path = os.path.join(root, file)
            
            if not should_scan_file(file_path):
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    lines = content.split('\n')
                    
                # Check for TODO patterns
                for line_num, line in enumerate(lines, 1):
                    for pattern in todo_patterns:
                        matches = re.findall(pattern, line, re.IGNORECASE)
                        if matches:
                            todo_text = matches[0].strip()
                            if todo_text and len(todo_text) > 3:  # Only meaningful TODOs
                                todos.append({
                                    'file': file_path,
                                    'line': line_num,
                                    'text': todo_text,
                                    'type': pattern.split(':')[0].upper(),
                                    'context': _get_context(lines, line_num),
                                    'priority': _determine_priority(todo_text, file_path),
                                    'labels': _determine_labels(todo_text, file_path)
                                })
                                
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
    
    return todos

def _get_context(lines: List[str], line_num: int, context_size: int = 3) -> str:
    """Get context around a TODO line"""
    start = max(0, line_num - context_size - 1)
    end = min(len(lines), line_num + context_size)
    
    context_lines = []
    for i in range(start, end):
        prefix = ">>> " if i == line_num - 1 else "    "
        context_lines.append(f"{prefix}{i+1:4d}: {lines[i]}")
    
    return '\n'.join(context_lines)

def _determine_priority(todo_text: str, file_path: str) -> str:
    """Determine priority based on TODO content and file location"""
    
    # High priority keywords
    high_priority_keywords = [
        'critical', 'urgent', 'security', 'bug', 'fix', 'error', 'crash',
        'production', 'deploy', 'release', 'hotfix', 'emergency'
    ]
    
    # Medium priority keywords
    medium_priority_keywords = [
        'important', 'feature', 'enhancement', 'improvement', 'optimization',
        'performance', 'refactor', 'cleanup', 'documentation'
    ]
    
    # Low priority keywords
    low_priority_keywords = [
        'nice to have', 'future', 'later', 'optional', 'enhancement',
        'cosmetic', 'minor', 'low priority'
    ]
    
    todo_lower = todo_text.lower()
    
    # Check for priority keywords
    for keyword in high_priority_keywords:
        if keyword in todo_lower:
            return 'high'
    
    for keyword in medium_priority_keywords:
        if keyword in todo_lower:
            return 'medium'
    
    for keyword in low_priority_keywords:
        if keyword in todo_lower:
            return 'low'
    
    # Default priority based on file location
    if any(path in file_path for path in ['cli/', 'core/', 'services/']):
        return 'medium'
    elif any(path in file_path for path in ['docs/', 'tests/']):
        return 'low'
    else:
        return 'medium'

def _determine_labels(todo_text: str, file_path: str) -> List[str]:
    """Determine labels based on TODO content and file location"""
    
    labels = []
    
    # Type-based labels
    if 'security' in todo_text.lower():
        labels.append('security')
    if 'bug' in todo_text.lower() or 'fix' in todo_text.lower():
        labels.append('bug')
    if 'feature' in todo_text.lower() or 'enhancement' in todo_text.lower():
        labels.append('enhancement')
    if 'documentation' in todo_text.lower() or 'doc' in todo_text.lower():
        labels.append('documentation')
    if 'test' in todo_text.lower():
        labels.append('testing')
    if 'performance' in todo_text.lower():
        labels.append('performance')
    
    # File-based labels
    if 'cli/' in file_path:
        labels.append('cli')
    elif 'docs/' in file_path:
        labels.append('documentation')
    elif 'tests/' in file_path:
        labels.append('testing')
    elif 'services/' in file_path:
        labels.append('backend')
    elif 'core/' in file_path:
        labels.append('core')
    elif file_path.endswith('.sol'):
        labels.append('smart-contracts')
    elif file_path.endswith('.md'):
        labels.append('documentation')
    
    # Priority labels
    priority = _determine_priority(todo_text, file_path)
    labels.append(f'priority:{priority}')
    
    # Default labels
    labels.extend(['todo', 'maintenance'])
    
    return list(set(labels))  # Remove duplicates

def group_todos_by_category(todos: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Group TODOs by category for better organization"""
    
    categories = {
        'cli_commands': [],
        'documentation': [],
        'testing': [],
        'security': [],
        'performance': [],
        'features': [],
        'bug_fixes': [],
        'refactoring': [],
        'other': []
    }
    
    for todo in todos:
        labels = todo['labels']
        
        if 'cli' in labels:
            categories['cli_commands'].append(todo)
        elif 'documentation' in labels:
            categories['documentation'].append(todo)
        elif 'testing' in labels:
            categories['testing'].append(todo)
        elif 'security' in labels:
            categories['security'].append(todo)
        elif 'performance' in labels:
            categories['performance'].append(todo)
        elif 'enhancement' in labels:
            categories['features'].append(todo)
        elif 'bug' in labels:
            categories['bug_fixes'].append(todo)
        elif 'refactor' in todo['text'].lower():
            categories['refactoring'].append(todo)
        else:
            categories['other'].append(todo)
    
    return categories

def create_github_issue_template(todo: Dict[str, Any], git_info: Dict[str, str]) -> Dict[str, Any]:
    """Create GitHub issue template from TODO"""
    
    # Determine issue title
    title = f"[{todo['type']}] {todo['text'][:80]}"
    if len(todo['text']) > 80:
        title += "..."
    
    # Create issue body
    body = f"""## {todo['type']} Item

**Description**: {todo['text']}

**File**: `{todo['file']}`  
**Line**: {todo['line']}  
**Priority**: {todo['priority']}  

### Context
```text
{todo['context']}
```

### Acceptance Criteria
- [ ] TODO item has been addressed
- [ ] Code has been tested
- [ ] Documentation updated (if applicable)
- [ ] No regressions introduced

### Additional Notes
- **Discovered**: {datetime.now().strftime('%Y-%m-%d')}
- **Commit**: `{git_info['commit_hash']}`
- **Branch**: `{git_info['branch']}`

---
*This issue was automatically created from a TODO comment in the codebase.*
"""
    
    return {
        'title': title,
        'body': body,
        'labels': todo['labels']
    }

def generate_issue_summary(categories: Dict[str, List[Dict[str, Any]]]) -> str:
    """Generate summary of all TODOs found"""
    
    total_todos = sum(len(todos) for todos in categories.values())
    
    summary = f"""# Focused TODO to GitHub Issues Conversion Report

**Generated**: {datetime.now().isoformat()}  
**Total TODOs Found**: {total_todos}

## Summary by Category

"""
    
    for category, todos in categories.items():
        if todos:
            summary += f"### {category.replace('_', ' ').title()} ({len(todos)} items)\n"
            for todo in todos[:5]:  # Show first 5
                summary += f"- **{todo['file']}:{todo['line']}** - {todo['text'][:100]}\n"
            if len(todos) > 5:
                summary += f"- ... and {len(todos) - 5} more\n"
            summary += "\n"
    
    summary += """## Next Steps

1. Review all generated issues
2. Prioritize based on business impact
3. Assign to appropriate team members
4. Create milestones for related issues
5. Track progress in project management tool

## Issue Templates Generated

Each TODO has been converted to a GitHub issue with:
- Descriptive title
- Full context and file location
- Priority and labels
- Acceptance criteria
- Additional metadata

---
*This report is automatically generated by the focused TODO to GitHub Issues conversion script.*
"""
    
    return summary

def main():
    """Main function"""
    print("Scanning our codebase for TODO/TBD/FIXME items...")
    
    # Get git info
    git_info = get_git_info()
    
    # Scan for TODOs
    todos = scan_for_todos()
    
    if not todos:
        print("No TODO items found in our codebase!")
        return 0
    
    print(f"Found {len(todos)} TODO items in our codebase")
    
    # Group by category
    categories = group_todos_by_category(todos)
    
    # Generate issue templates
    issue_templates = []
    for todo in todos:
        issue_template = create_github_issue_template(todo, git_info)
        issue_templates.append({
            'todo': todo,
            'issue_template': issue_template
        })
    
    # Save results
    results = {
        'scan_date': datetime.now().isoformat(),
        'git_info': git_info,
        'total_todos': len(todos),
        'categories': categories,
        'issue_templates': issue_templates
    }
    
    # Write JSON report to JSON_DATA directory
    json_path = Path('REPORTS/JSON_DATA/focused_todo_to_issues_conversion.json')
    json_path.parent.mkdir(parents=True, exist_ok=True)
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    # Generate summary report - save to TODO category
    summary = generate_issue_summary(categories)
    report_path = Path('REPORTS/TODO/focused_todo_to_issues_summary.md')
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(summary)
    
    # Print summary
    print(f"\nFocused TODO to GitHub Issues Conversion Complete!")
    print(f"Total TODOs found: {len(todos)}")
    
    for category, todos_in_category in categories.items():
        if todos_in_category:
            print(f"- {category.replace('_', ' ').title()}: {len(todos_in_category)}")
    
    print(f"\nReports generated:")
    print(f"- {json_path}")
    print(f"- {report_path}")
    
    print(f"\nNext steps:")
    print(f"1. Review the generated issue templates")
    print(f"2. Create GitHub issues using the templates")
    print(f"3. Assign appropriate labels and priorities")
    print(f"4. Track progress in your project management tool")
    
    return 0

if __name__ == "__main__":
    exit(main())
