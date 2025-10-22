#!/usr/bin/env python3
"""
HyperKit Agent Security Scanner
Automated security scanning script to detect hardcoded secrets and sensitive data.
Follows .cursor/rules security best practices.
"""

import os
import re
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class SecurityIssue:
    """Represents a security issue found during scanning."""
    file_path: str
    line_number: int
    issue_type: str
    severity: str
    description: str
    pattern_matched: str
    suggested_fix: str

class SecurityScanner:
    """Comprehensive security scanner for detecting hardcoded secrets."""
    
    def __init__(self, root_path: str = "."):
        self.root_path = Path(root_path)
        self.issues: List[SecurityIssue] = []
        
        # Define security patterns following .cursor/rules
        self.patterns = {
            "google_api_key": {
                "pattern": r'AIzaSy[A-Za-z0-9_-]{35}',
                "severity": "CRITICAL",
                "description": "Google API Key detected",
                "suggested_fix": "Use environment variable: GOOGLE_API_KEY"
            },
            "openai_api_key": {
                "pattern": r'sk-[A-Za-z0-9]{48}',
                "severity": "CRITICAL", 
                "description": "OpenAI API Key detected",
                "suggested_fix": "Use environment variable: OPENAI_API_KEY"
            },
            "private_key": {
                "pattern": r'0x[a-fA-F0-9]{64}',
                "severity": "CRITICAL",
                "description": "Private key detected",
                "suggested_fix": "Use environment variable: PRIVATE_KEY"
            },
            "jwt_secret": {
                "pattern": r'(?i)(jwt[_-]?secret|jwts|jwt_secret)\s*[:=]\s*["\']?[A-Za-z0-9+/]{40,}={0,2}["\']?',
                "severity": "HIGH",
                "description": "JWT secret detected",
                "suggested_fix": "Use environment variable: JWT_SECRET"
            },
            "database_password": {
                "pattern": r'(?i)(password|pwd)\s*[:=]\s*["\']?[A-Za-z0-9!@#$%^&*()_+\-=\[\]{}|;:,.<>?]{8,}["\']?',
                "severity": "HIGH",
                "description": "Database password detected",
                "suggested_fix": "Use environment variable: DB_PASSWORD"
            },
            "api_key_generic": {
                "pattern": r'(?i)(api[_-]?key|apikey)\s*[:=]\s*["\']?[A-Za-z0-9_-]{20,}["\']?',
                "severity": "MEDIUM",
                "description": "Generic API key detected",
                "suggested_fix": "Use environment variable"
            },
            "secret_key": {
                "pattern": r'(?i)(secret[_-]?key|secretkey)\s*[:=]\s*["\']?[A-Za-z0-9_-]{20,}["\']?',
                "severity": "HIGH",
                "description": "Secret key detected",
                "suggested_fix": "Use environment variable"
            },
            "access_token": {
                "pattern": r'(?i)(access[_-]?token|accesstoken)\s*[:=]\s*["\']?[A-Za-z0-9_-]{20,}["\']?',
                "severity": "HIGH",
                "description": "Access token detected",
                "suggested_fix": "Use environment variable"
            }
        }
        
        # Files to exclude from scanning
        self.exclude_patterns = [
            r'\.git/',
            r'node_modules/',
            r'__pycache__/',
            r'\.pytest_cache/',
            r'\.venv/',
            r'venv/',
            r'\.env\.example',
            r'\.gitignore',
            r'README\.md',
            r'CHANGELOG\.md',
            r'LICENSE',
            r'\.cursor/',
            r'\.vscode/',
            r'\.idea/',
            r'dist/',
            r'build/',
            r'coverage/',
            r'\.coverage',
            r'htmlcov/',
            r'\.tox/',
            r'\.mypy_cache/',
            r'\.ruff_cache/',
            r'\.changeset/',
            r'\.github/workflows/',
            r'contracts/agent_generate/',
            r'REPORTS/',
            r'security_report\.md',
            r'security_report\.json'
        ]
        
        # File extensions to scan
        self.scan_extensions = {
            '.py', '.js', '.ts', '.jsx', '.tsx', '.json', '.yaml', '.yml',
            '.toml', '.ini', '.cfg', '.conf', '.md', '.txt', '.sh', '.bat',
            '.ps1', '.dockerfile', '.env', '.sol', '.go', '.rs', '.java',
            '.cpp', '.c', '.h', '.hpp', '.cs', '.php', '.rb', '.swift'
        }

    def should_scan_file(self, file_path: Path) -> bool:
        """Determine if a file should be scanned based on exclusion patterns."""
        file_str = str(file_path)
        
        # Check file extension
        if file_path.suffix.lower() not in self.scan_extensions:
            return False
            
        # Check exclusion patterns - use pathlib for better matching
        for pattern in self.exclude_patterns:
            if re.search(pattern, file_str, re.IGNORECASE):
                return False
        
        # Additional check for node_modules in any part of the path
        if 'node_modules' in file_str:
            return False
                
        return True

    def scan_file(self, file_path: Path) -> List[SecurityIssue]:
        """Scan a single file for security issues."""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                
            for line_num, line in enumerate(lines, 1):
                for issue_type, config in self.patterns.items():
                    pattern = config['pattern']
                    matches = re.finditer(pattern, line, re.IGNORECASE)
                    
                    for match in matches:
                        # Skip if it's in a comment or documentation
                        if self._is_in_comment_or_doc(line, match.start()):
                            continue
                            
                        issue = SecurityIssue(
                            file_path=str(file_path.relative_to(self.root_path)),
                            line_number=line_num,
                            issue_type=issue_type,
                            severity=config['severity'],
                            description=config['description'],
                            pattern_matched=match.group(),
                            suggested_fix=config['suggested_fix']
                        )
                        issues.append(issue)
                        
        except Exception as e:
            logger.warning(f"Error scanning {file_path}: {e}")
            
        return issues

    def _is_in_comment_or_doc(self, line: str, position: int) -> bool:
        """Check if the match position is within a comment or documentation."""
        # Check for Python comments
        if '#' in line and line.find('#') < position:
            return True
            
        # Check for JavaScript/TypeScript comments
        if '//' in line and line.find('//') < position:
            return True
            
        # Check for multi-line comment start
        if '/*' in line and line.find('/*') < position:
            return True
            
        # Check for documentation markers
        if any(marker in line[:position] for marker in ['"""', "'''", '<!--']):
            return True
            
        # Check for markdown documentation
        if line.strip().startswith('#'):
            return True
            
        # Check for example/documentation patterns
        if any(pattern in line.lower() for pattern in ['example', 'template', 'placeholder', 'your_', 'your-']):
            return True
            
        return False

    def scan_directory(self) -> List[SecurityIssue]:
        """Scan entire directory for security issues."""
        logger.info(f"Starting security scan of {self.root_path}")
        
        all_issues = []
        files_scanned = 0
        
        for file_path in self.root_path.rglob('*'):
            if file_path.is_file() and self.should_scan_file(file_path):
                issues = self.scan_file(file_path)
                all_issues.extend(issues)
                files_scanned += 1
                
                if issues:
                    logger.warning(f"Found {len(issues)} issues in {file_path}")
        
        logger.info(f"Scanned {files_scanned} files")
        self.issues = all_issues
        return all_issues

    def generate_report(self, output_file: Optional[str] = None) -> str:
        """Generate a comprehensive security report."""
        if not self.issues:
            return "✅ No security issues found!"
        
        # Group issues by severity
        critical_issues = [i for i in self.issues if i.severity == "CRITICAL"]
        high_issues = [i for i in self.issues if i.severity == "HIGH"]
        medium_issues = [i for i in self.issues if i.severity == "MEDIUM"]
        
        report = []
        report.append("# 🔒 Security Scan Report")
        report.append(f"**Scan Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"**Total Issues:** {len(self.issues)}")
        report.append("")
        
        # Summary
        report.append("## 📊 Summary")
        report.append(f"- 🚨 **Critical:** {len(critical_issues)}")
        report.append(f"- ⚠️ **High:** {len(high_issues)}")
        report.append(f"- ℹ️ **Medium:** {len(medium_issues)}")
        report.append("")
        
        # Critical Issues
        if critical_issues:
            report.append("## 🚨 Critical Issues")
            for issue in critical_issues:
                report.append(f"### {issue.file_path}:{issue.line_number}")
                report.append(f"- **Type:** {issue.issue_type}")
                report.append(f"- **Description:** {issue.description}")
                report.append(f"- **Pattern:** `{issue.pattern_matched}`")
                report.append(f"- **Fix:** {issue.suggested_fix}")
                report.append("")
        
        # High Issues
        if high_issues:
            report.append("## ⚠️ High Priority Issues")
            for issue in high_issues:
                report.append(f"### {issue.file_path}:{issue.line_number}")
                report.append(f"- **Type:** {issue.issue_type}")
                report.append(f"- **Description:** {issue.description}")
                report.append(f"- **Pattern:** `{issue.pattern_matched}`")
                report.append(f"- **Fix:** {issue.suggested_fix}")
                report.append("")
        
        # Medium Issues
        if medium_issues:
            report.append("## ℹ️ Medium Priority Issues")
            for issue in medium_issues:
                report.append(f"### {issue.file_path}:{issue.line_number}")
                report.append(f"- **Type:** {issue.issue_type}")
                report.append(f"- **Description:** {issue.description}")
                report.append(f"- **Pattern:** `{issue.pattern_matched}`")
                report.append(f"- **Fix:** {issue.suggested_fix}")
                report.append("")
        
        # Recommendations
        report.append("## 🛡️ Security Recommendations")
        report.append("1. **Never commit API keys or secrets to version control**")
        report.append("2. **Use environment variables for all sensitive data**")
        report.append("3. **Implement proper secret management**")
        report.append("4. **Regular security scans**")
        report.append("5. **Use .gitignore to exclude sensitive files**")
        report.append("")
        
        report_text = "\n".join(report)
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report_text)
            logger.info(f"Security report saved to {output_file}")
        
        return report_text

    def generate_json_report(self, output_file: str) -> None:
        """Generate JSON report for programmatic processing."""
        report_data = {
            "scan_date": datetime.now().isoformat(),
            "total_issues": len(self.issues),
            "issues_by_severity": {
                "CRITICAL": len([i for i in self.issues if i.severity == "CRITICAL"]),
                "HIGH": len([i for i in self.issues if i.severity == "HIGH"]),
                "MEDIUM": len([i for i in self.issues if i.severity == "MEDIUM"])
            },
            "issues": [
                {
                    "file_path": issue.file_path,
                    "line_number": issue.line_number,
                    "issue_type": issue.issue_type,
                    "severity": issue.severity,
                    "description": issue.description,
                    "pattern_matched": issue.pattern_matched,
                    "suggested_fix": issue.suggested_fix
                }
                for issue in self.issues
            ]
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2)
        
        logger.info(f"JSON report saved to {output_file}")

def main():
    """Main function for CLI usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="HyperKit Agent Security Scanner")
    parser.add_argument("--path", "-p", default=".", help="Path to scan (default: current directory)")
    parser.add_argument("--output", "-o", help="Output file for report")
    parser.add_argument("--json", "-j", help="Output JSON report file")
    parser.add_argument("--quiet", "-q", action="store_true", help="Quiet mode")
    
    args = parser.parse_args()
    
    if args.quiet:
        logging.getLogger().setLevel(logging.WARNING)
    
    scanner = SecurityScanner(args.path)
    issues = scanner.scan_directory()
    
    if issues:
        print(f"🚨 Found {len(issues)} security issues!")
        report = scanner.generate_report(args.output)
        print(report)
        
        if args.json:
            scanner.generate_json_report(args.json)
        
        sys.exit(1)  # Exit with error code if issues found
    else:
        print("✅ No security issues found!")
        sys.exit(0)

if __name__ == "__main__":
    main()
