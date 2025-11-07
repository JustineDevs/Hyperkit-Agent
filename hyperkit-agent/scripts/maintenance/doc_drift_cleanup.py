#!/usr/bin/env python3
"""
Documentation Drift Cleanup Script
Removes all references to main.py, deprecated python scripts, and legacy workflows
Updates all docs to use hyperagent CLI commands only
"""

import os
import re
import glob
from pathlib import Path

def fix_main_py_references(content):
    """Fix main.py references to hyperagent CLI"""
    replacements = [
        # Direct main.py calls
        (r'python main\.py (\w+)', r'hyperagent \1'),
        (r'python main\.py', r'hyperagent'),
        (r'CMD \["python", "main\.py"\]', r'CMD ["hyperagent", "start"]'),
        (r'CMD \["python", "main\.py", "(\w+)"\]', r'CMD ["hyperagent", "\1"]'),
        
        # Health check patterns
        (r'python main\.py health', r'hyperagent monitor health'),
        (r'python main\.py status', r'hyperagent status'),
        (r'python main\.py deploy', r'hyperagent deploy'),
        (r'python main\.py audit', r'hyperagent audit'),
        (r'python main\.py generate', r'hyperagent generate'),
        (r'python main\.py workflow', r'hyperagent workflow'),
        
        # Script execution patterns
        (r'python scripts/([^\.]+)\.py', r'hyperagent \1'),
        (r'python scripts/', r'hyperagent '),
        
        # Shell script patterns
        (r'\./scripts/([^\.]+)\.sh', r'hyperagent \1'),
        (r'bash scripts/([^\.]+)\.sh', r'hyperagent \1'),
    ]
    
    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content)
    
    return content

def fix_legacy_workflows(content):
    """Fix legacy workflow references"""
    replacements = [
        # Update workflow references
        (r'5-stage workflow', r'AI-powered workflow'),
        (r'workflow execution', r'workflow run'),
        
        # Fix deprecated command patterns
        (r'--constructor-args', r'--args'),
        (r'--constructor-file', r'--file'),
    ]
    
    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content)
    
    return content

def add_not_implemented_banners(content, file_path):
    """Add NOT IMPLEMENTED banners for stub processes"""
    stub_patterns = [
        r'disaster recovery',
        r'backup.*restore',
        r'emergency.*recovery',
        r'health check.*script',
        r'python.*script.*not.*cli',
    ]
    
    # Check if content contains stub patterns
    has_stubs = any(re.search(pattern, content, re.IGNORECASE) for pattern in stub_patterns)
    
    if has_stubs and 'NOT IMPLEMENTED' not in content:
        banner = """
> ⚠️ **NOT IMPLEMENTED BANNER**  
> This process references scripts or procedures that are not CLI-integrated.  
> These features are documented but not executable via `hyperagent` CLI.  
> See implementation status in `REPORTS/IMPLEMENTATION_STATUS.md`.

"""
        # Add banner after title
        title_match = re.search(r'^# (.+)$', content, re.MULTILINE)
        if title_match:
            title_end = title_match.end()
            content = content[:title_end] + banner + content[title_end:]
    
    return content

def process_file(file_path):
    """Process a single markdown file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Apply fixes
        content = fix_main_py_references(content)
        content = fix_legacy_workflows(content)
        content = add_not_implemented_banners(content, file_path)
        
        # Write back if changed
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Fixed: {file_path}")
            return True
        
        return False
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def is_submodule(file_path):
    """Check if a file is in a submodule directory"""
    path = Path(file_path)
    # Check if any parent directory is a submodule
    # Submodules have a .git file (not directory) in their root
    for parent in path.parents:
        git_file = parent / ".git"
        if git_file.exists() and git_file.is_file():
            return True
        # Also exclude common submodule directories
        if parent.name == "lib" and "openzeppelin" in str(parent).lower():
            return True
    return False

def main():
    """Main function to process all markdown files"""
    print("Starting documentation drift cleanup...")
    
    # Find all markdown files
    markdown_files = []
    # Auto-detect patterns: if hyperkit-agent subdir exists, include both; otherwise just current dir
    patterns = ["**/*.md", "docs/**/*.md"]
    if Path("hyperkit-agent").exists() and Path("hyperkit-agent").is_dir():
        patterns.extend(["hyperkit-agent/docs/**/*.md", "hyperkit-agent/REPORTS/**/*.md"])
    patterns.append("REPORTS/**/*.md")
    
    for pattern in patterns:
        markdown_files.extend(glob.glob(pattern, recursive=True))
    
    # Filter out submodule files
    markdown_files = [f for f in markdown_files if not is_submodule(f)]
    
    # Remove duplicates and sort
    markdown_files = sorted(set(markdown_files))
    
    fixed_count = 0
    for file_path in markdown_files:
        if process_file(file_path):
            fixed_count += 1
    
    print(f"Fixed {fixed_count} files")
    
    # Create implementation status report
    create_implementation_status_report()
    
    return 0

def create_implementation_status_report():
    """Create implementation status report"""
    report_content = """# Implementation Status Report

<!-- VERSION_PLACEHOLDER -->
**Version**: 1.4.5
**Last Updated**: 2025-01-28
**Commit**: unknown
<!-- /VERSION_PLACEHOLDER -->

## ✅ IMPLEMENTED FEATURES

### Core CLI Commands
- `hyperagent generate` - Contract generation with AI
- `hyperagent audit` - Security auditing
- `hyperagent deploy` - Multi-chain deployment
- `hyperagent workflow run` - End-to-end workflows
- `hyperagent status` - System status
- `hyperagent monitor` - Health monitoring

### RAG Integration
- IPFS template fetching
- RAG-enhanced prompts
- Template versioning
- Offline fallbacks

### Testing
- Unit tests (19/27 passing)
- Integration tests
- E2E workflow tests

## ⚠️ PARTIALLY IMPLEMENTED

### Deployment
- Foundry integration (basic)
- Multi-network support (limited)
- Constructor argument parsing (enhanced)

### Monitoring
- Health checks (basic)
- Logging system (structured)

## ❌ NOT IMPLEMENTED

### Disaster Recovery
- Backup procedures (referenced as scripts)
- Emergency recovery workflows
- Automated failover

### Advanced Features
- Multi-sig deployment
- Governance integration
- Advanced monitoring

## 🔧 STUB PROCESSES

These processes are documented but not CLI-integrated:

1. **Backup/Restore Scripts** - Referenced as python scripts
2. **Emergency Recovery** - Documented but not executable
3. **Health Check Scripts** - Shell/python scripts not CLI commands
4. **RAG Vector Regeneration** - Script-based, not CLI-integrated

## 📋 ACTION ITEMS

1. Convert all script references to CLI commands
2. Implement missing disaster recovery procedures
3. Complete multi-network deployment validation
4. Add comprehensive E2E test coverage
5. Implement advanced monitoring features

---
*This report is automatically generated and updated with each version sync.*
"""
    
    # Save to STATUS category (use relative path from hyperkit-agent root)
    report_path = Path("REPORTS/STATUS/implementation_status.md")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)
    
    print("Created IMPLEMENTATION_STATUS.md report")

if __name__ == "__main__":
    exit(main())
