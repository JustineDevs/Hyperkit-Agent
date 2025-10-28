#!/usr/bin/env python3
"""
Zero-Excuse Culture Implementation
Every PR with feature/CLI change MUST have doc updates or PR rejected
"""

import os
import json
import subprocess
from pathlib import Path
from typing import List, Dict, Any


class ZeroExcuseCulture:
    """Enforce zero-excuse culture for documentation updates"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.docs_root = project_root / "docs"
        self.hyperkit_docs_root = project_root / "hyperkit-agent" / "docs"
        
    def check_pr_documentation_requirements(self, pr_number: str = None) -> Dict[str, Any]:
        """Check if PR meets documentation requirements"""
        
        # Get changed files in PR
        if pr_number:
            changed_files = self._get_pr_changed_files(pr_number)
        else:
            # For local testing, get staged files
            changed_files = self._get_staged_files()
        
        # Analyze changes
        analysis = {
            "pr_number": pr_number,
            "changed_files": changed_files,
            "requires_doc_update": False,
            "doc_files_to_update": [],
            "missing_docs": [],
            "violations": []
        }
        
        # Check for CLI changes
        cli_changes = self._detect_cli_changes(changed_files)
        if cli_changes:
            analysis["requires_doc_update"] = True
            analysis["violations"].append("CLI changes detected - documentation update required")
            
            # Check if CLI docs are updated
            cli_docs_updated = self._check_cli_docs_updated(changed_files)
            if not cli_docs_updated:
                analysis["missing_docs"].append("CLI command reference not updated")
        
        # Check for feature changes
        feature_changes = self._detect_feature_changes(changed_files)
        if feature_changes:
            analysis["requires_doc_update"] = True
            analysis["violations"].append("Feature changes detected - documentation update required")
            
            # Check if feature docs are updated
            feature_docs_updated = self._check_feature_docs_updated(changed_files)
            if not feature_docs_updated:
                analysis["missing_docs"].append("Feature documentation not updated")
        
        # Check for API changes
        api_changes = self._detect_api_changes(changed_files)
        if api_changes:
            analysis["requires_doc_update"] = True
            analysis["violations"].append("API changes detected - documentation update required")
            
            # Check if API docs are updated
            api_docs_updated = self._check_api_docs_updated(changed_files)
            if not api_docs_updated:
                analysis["missing_docs"].append("API reference not updated")
        
        return analysis
    
    def _get_pr_changed_files(self, pr_number: str) -> List[str]:
        """Get changed files from PR"""
        try:
            result = subprocess.run([
                "gh", "pr", "view", pr_number, "--json", "files"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                pr_data = json.loads(result.stdout)
                return [f["path"] for f in pr_data["files"]]
            else:
                print(f"Error getting PR files: {result.stderr}")
                return []
        except Exception as e:
            print(f"Error running gh command: {e}")
            return []
    
    def _get_staged_files(self) -> List[str]:
        """Get staged files for local testing"""
        try:
            result = subprocess.run([
                "git", "diff", "--cached", "--name-only"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                return result.stdout.strip().split('\n') if result.stdout.strip() else []
            else:
                return []
        except Exception as e:
            print(f"Error getting staged files: {e}")
            return []
    
    def _detect_cli_changes(self, changed_files: List[str]) -> bool:
        """Detect CLI-related changes"""
        cli_patterns = [
            "cli/",
            "commands/",
            "main.py",
            "hyperagent",
            "argparse",
            "click"
        ]
        
        for file_path in changed_files:
            for pattern in cli_patterns:
                if pattern in file_path.lower():
                    return True
        return False
    
    def _detect_feature_changes(self, changed_files: List[str]) -> bool:
        """Detect feature-related changes"""
        feature_patterns = [
            "services/",
            "core/",
            "features/",
            "workflow",
            "audit",
            "deploy",
            "generate"
        ]
        
        for file_path in changed_files:
            for pattern in feature_patterns:
                if pattern in file_path.lower():
                    return True
        return False
    
    def _detect_api_changes(self, changed_files: List[str]) -> bool:
        """Detect API-related changes"""
        api_patterns = [
            "api/",
            "endpoints/",
            "routes/",
            "controllers/",
            "middleware/"
        ]
        
        for file_path in changed_files:
            for pattern in api_patterns:
                if pattern in file_path.lower():
                    return True
        return False
    
    def _check_cli_docs_updated(self, changed_files: List[str]) -> bool:
        """Check if CLI documentation is updated"""
        cli_doc_patterns = [
            "CLI_COMMANDS_REFERENCE.md",
            "cli",
            "commands",
            "hyperagent"
        ]
        
        for file_path in changed_files:
            for pattern in cli_doc_patterns:
                if pattern in file_path.lower() and file_path.endswith('.md'):
                    return True
        return False
    
    def _check_feature_docs_updated(self, changed_files: List[str]) -> bool:
        """Check if feature documentation is updated"""
        feature_doc_patterns = [
            "README.md",
            "GUIDE/",
            "INTEGRATION/",
            "EXECUTION/"
        ]
        
        for file_path in changed_files:
            for pattern in feature_doc_patterns:
                if pattern in file_path and file_path.endswith('.md'):
                    return True
        return False
    
    def _check_api_docs_updated(self, changed_files: List[str]) -> bool:
        """Check if API documentation is updated"""
        api_doc_patterns = [
            "API_REFERENCE.md",
            "api",
            "reference"
        ]
        
        for file_path in changed_files:
            for pattern in api_doc_patterns:
                if pattern in file_path.lower() and file_path.endswith('.md'):
                    return True
        return False
    
    def generate_pr_checklist(self, analysis: Dict[str, Any]) -> str:
        """Generate PR checklist based on analysis"""
        
        checklist = []
        checklist.append("## 📋 Documentation Requirements Checklist")
        checklist.append("")
        
        if analysis["requires_doc_update"]:
            checklist.append("### ❌ Documentation Update Required")
            checklist.append("")
            
            for violation in analysis["violations"]:
                checklist.append(f"- [ ] {violation}")
            
            checklist.append("")
            checklist.append("### 📝 Required Documentation Updates:")
            
            for missing_doc in analysis["missing_docs"]:
                checklist.append(f"- [ ] {missing_doc}")
            
            checklist.append("")
            checklist.append("### 🚨 PR Status: **BLOCKED**")
            checklist.append("This PR cannot be merged until documentation is updated.")
            
        else:
            checklist.append("### ✅ No Documentation Updates Required")
            checklist.append("This PR does not require documentation changes.")
            checklist.append("")
            checklist.append("### 🚨 PR Status: **APPROVED**")
        
        return "\n".join(checklist)
    
    def create_github_action(self) -> str:
        """Create GitHub Action workflow for zero-excuse culture"""
        
        workflow_content = """name: Zero-Excuse Documentation Culture

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  documentation-check:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
      with:
        fetch-depth: 0
    
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.12'
    
    - name: Install dependencies
      run: |
        pip install pyyaml
    
    - name: Run documentation check
      run: |
        python scripts/zero_excuse_culture.py --pr-check
    
    - name: Comment on PR
      if: failure()
      uses: actions/github-script@v7
      with:
        script: |
          const fs = require('fs');
          const checklist = fs.readFileSync('pr_checklist.md', 'utf8');
          
          github.rest.issues.createComment({
            issue_number: context.issue.number,
            owner: context.repo.owner,
            repo: context.repo.repo,
            body: checklist
          });
    
    - name: Fail if documentation required
      if: failure()
      run: |
        echo "::error::PR blocked: Documentation updates required"
        exit 1
"""
        
        return workflow_content


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Zero-Excuse Culture Documentation Checker")
    parser.add_argument("--pr-check", action="store_true", help="Check current PR")
    parser.add_argument("--pr-number", type=str, help="PR number to check")
    parser.add_argument("--create-workflow", action="store_true", help="Create GitHub Action workflow")
    
    args = parser.parse_args()
    
    project_root = Path(__file__).parent.parent.parent
    checker = ZeroExcuseCulture(project_root)
    
    if args.create_workflow:
        workflow_content = checker.create_github_action()
        workflow_path = project_root / ".github" / "workflows" / "zero-excuse-docs.yml"
        workflow_path.parent.mkdir(parents=True, exist_ok=True)
        workflow_path.write_text(workflow_content)
        print(f"GitHub Action workflow created: {workflow_path}")
        return
    
    if args.pr_check or args.pr_number:
        analysis = checker.check_pr_documentation_requirements(args.pr_number)
        
        print("Zero-Excuse Culture Analysis")
        print("=" * 50)
        print(f"PR Number: {analysis['pr_number'] or 'Local'}")
        print(f"Changed Files: {len(analysis['changed_files'])}")
        print(f"Requires Doc Update: {analysis['requires_doc_update']}")
        
        if analysis['violations']:
            print("\nViolations:")
            for violation in analysis['violations']:
                print(f"  - {violation}")
        
        if analysis['missing_docs']:
            print("\nMissing Documentation:")
            for missing in analysis['missing_docs']:
                print(f"  - {missing}")
        
        # Generate checklist
        checklist = checker.generate_pr_checklist(analysis)
        checklist_path = project_root / "pr_checklist.md"
        checklist_path.write_text(checklist)
        print(f"\nPR Checklist saved: {checklist_path}")
        
        # Exit with error if documentation required
        if analysis['requires_doc_update']:
            print("\n❌ PR BLOCKED: Documentation updates required!")
            exit(1)
        else:
            print("\n✅ PR APPROVED: No documentation updates required!")
            exit(0)


if __name__ == "__main__":
    main()
