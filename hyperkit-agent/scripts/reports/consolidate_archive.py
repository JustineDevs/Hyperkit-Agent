#!/usr/bin/env python3
"""Consolidate archive files"""
from pathlib import Path
from datetime import datetime

def consolidate_archive_files():
    """Consolidate all archive files into FIXES_ARCHIVE.md"""
    reports_root = Path(__file__).parent
    archive_dir = reports_root / 'archive'
    output_file = archive_dir / 'FIXES_ARCHIVE.md'
    
    fixes_dir = archive_dir / 'fixes'
    old_reports_dir = archive_dir / 'old-reports'
    
    content = []
    content.append("# Archive - Fixes and Historical Reports\n")
    content.append("**Purpose**: Consolidated archive of all historical fixes and old reports\n")
    content.append("**Consolidated**: 2025-10-29\n")
    content.append("**Status**: Archived - Historical Reference Only\n")
    content.append("\n---\n")
    content.append("\n## Table of Contents\n\n")
    
    # Fixes section
    if fixes_dir.exists():
        content.append("1. [Fixes Archive](#fixes-archive)\n")
        fixes_files = sorted(fixes_dir.glob('*.md'))
        for i, f in enumerate(fixes_files, 2):
            title = f.name.replace('.md', '').replace('_', ' ').title()
            anchor = title.lower().replace(' ', '-')
            content.append(f"   {i}. [{title}](#{anchor})\n")
    
    # Old reports section
    if old_reports_dir.exists():
        content.append(f"{len(fixes_files) + 1}. [Old Reports Archive](#old-reports-archive)\n")
        old_files = sorted(old_reports_dir.glob('*.md'))
        start_num = len(fixes_files) + 2
        for i, f in enumerate(old_files, start_num):
            title = f.name.replace('.md', '').replace('_', ' ').title()
            anchor = title.lower().replace(' ', '-')
            content.append(f"   {i}. [{title}](#{anchor})\n")
    
    content.append("\n---\n\n")
    
    # Fixes content
    if fixes_dir.exists():
        content.append("## Fixes Archive\n\n")
        for md_file in sorted(fixes_dir.glob('*.md')):
            title = md_file.name.replace('.md', '').replace('_', ' ').title()
            content.append(f"\n### {title}\n\n")
            content.append(f"*From: `{md_file.name}`*\n\n")
            content.append("---\n\n")
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    file_content = f.read()
                    # Remove frontmatter
                    file_content = file_content.replace('---\n', '', 1)
                    if file_content.startswith('---'):
                        file_content = file_content.split('---\n', 2)[-1]
                    content.append(file_content)
                    content.append("\n\n---\n\n")
            except Exception as e:
                content.append(f"*Error reading file: {e}*\n\n")
    
    # Old reports content
    if old_reports_dir.exists():
        content.append("## Old Reports Archive\n\n")
        for md_file in sorted(old_reports_dir.glob('*.md')):
            title = md_file.name.replace('.md', '').replace('_', ' ').title()
            content.append(f"\n### {title}\n\n")
            content.append(f"*From: `{md_file.name}`*\n\n")
            content.append("---\n\n")
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    file_content = f.read()
                    # Remove frontmatter
                    file_content = file_content.replace('---\n', '', 1)
                    if file_content.startswith('---'):
                        file_content = file_content.split('---\n', 2)[-1]
                    content.append(file_content)
                    content.append("\n\n---\n\n")
            except Exception as e:
                content.append(f"*Error reading file: {e}*\n\n")
    
    content.append("\n\n---\n\n")
    content.append("**Note**: This is a historical archive. Refer to current consolidated reports in parent directories for up-to-date information.\n\n")
    content.append("**Archive Status**: Complete historical reference only\n")
    content.append("**Last Updated**: 2025-10-29\n")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(''.join(content))
    
    print(f"[SUCCESS] Created {output_file}")

if __name__ == "__main__":
    consolidate_archive_files()

