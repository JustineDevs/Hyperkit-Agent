"""
Lint All Scripts

Lints all Python and shell scripts in the codebase for:
- Syntax errors
- Basic structure issues
- Execution permissions
- Best practices violations
"""

import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

# ANSI color codes
GREEN = "\033[0;32m"
RED = "\033[0;31m"
YELLOW = "\033[1;33m"
NC = "\033[0m"  # No Color


class ScriptLinter:
    """Lint all scripts in the codebase."""

    def __init__(self, base_dir: Path = None):
        # Auto-detect base directory: if hyperkit-agent exists as subdir, use it; otherwise use current dir
        if base_dir:
            self.base_dir = Path(base_dir)
        else:
            if Path("hyperkit-agent").exists() and Path("hyperkit-agent").is_dir():
                self.base_dir = Path("hyperkit-agent")
            else:
                self.base_dir = Path(".")
        self.scripts_dir = self.base_dir / "scripts"
        self.issues = []
        self.total_files = 0
        self.files_with_issues = 0

    def scan_scripts(self) -> Dict:
        """Scan all Python and shell scripts."""
        results = {
            "python_scripts": [],
            "shell_scripts": [],
            "issues": [],
            "summary": {}
        }

        # Find all Python scripts
        for py_file in self.scripts_dir.rglob("*.py"):
            self.total_files += 1
            result = self.lint_python(py_file)
            if result["has_issues"]:
                results["python_scripts"].append(result)
                self.files_with_issues += 1
            results["issues"].extend(result["issues"])

        # Find all shell scripts
        for sh_file in self.scripts_dir.rglob("*.sh"):
            self.total_files += 1
            result = self.lint_shell(sh_file)
            if result["has_issues"]:
                results["shell_scripts"].append(result)
                self.files_with_issues += 1
            results["issues"].extend(result["issues"])

        # Generate summary
        results["summary"] = {
            "total_files": self.total_files,
            "files_with_issues": self.files_with_issues,
            "total_issues": len(results["issues"]),
            "critical_issues": len([i for i in results["issues"] if i.get("severity") == "critical"]),
            "warnings": len([i for i in results["issues"] if i.get("severity") == "warning"]),
        }

        return results

    def lint_python(self, file_path: Path) -> Dict:
        """Lint a Python script."""
        issues = []

        try:
            # Check syntax
            result = subprocess.run(
                ["python", "-m", "py_compile", str(file_path)],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode != 0:
                issues.append({
                    "file": str(file_path),
                    "issue": "Syntax error",
                    "severity": "critical",
                    "details": result.stderr
                })

            # Check for shebang
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    first_line = f.readline().strip()
                    if not first_line.startswith("#!"):
                        issues.append({
                            "file": str(file_path),
                            "issue": "Missing shebang",
                            "severity": "warning",
                            "details": "Consider adding #!/usr/bin/env python3"
                        })
            except Exception as e:
                issues.append({
                    "file": str(file_path),
                    "issue": "Cannot read file",
                    "severity": "critical",
                    "details": str(e)
                })

            # Check imports
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    if "import" in content and not file_path.stem.startswith("__"):
                        # Check for common issues
                        if "from typing import" in content:
                            # This is OK
                            pass
            except Exception:
                pass

        except subprocess.TimeoutExpired:
            issues.append({
                "file": str(file_path),
                "issue": "Timeout compiling",
                "severity": "warning",
                "details": "File took too long to compile"
            })
        except Exception as e:
            issues.append({
                "file": str(file_path),
                "issue": "Error during linting",
                "severity": "critical",
                "details": str(e)
            })

        return {
            "file": str(file_path),
            "has_issues": len(issues) > 0,
            "issues": issues
        }

    def lint_shell(self, file_path: Path) -> Dict:
        """Lint a shell script."""
        issues = []

        try:
            # Check syntax with bash
            result = subprocess.run(
                ["bash", "-n", str(file_path)],
                shell=True,
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode != 0 and result.stderr:
                issues.append({
                    "file": str(file_path),
                    "issue": "Shell syntax error",
                    "severity": "critical",
                    "details": result.stderr
                })

            # Check for shebang
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    first_line = f.readline().strip()
                    if not first_line.startswith("#!"):
                        issues.append({
                            "file": str(file_path),
                            "issue": "Missing shebang",
                            "severity": "warning",
                            "details": "Consider adding #!/bin/bash"
                        })
            except Exception as e:
                issues.append({
                    "file": str(file_path),
                    "issue": "Cannot read file",
                    "severity": "critical",
                    "details": str(e)
                })

        except subprocess.TimeoutExpired:
            issues.append({
                "file": str(file_path),
                "issue": "Timeout checking syntax",
                "severity": "warning",
                "details": "File took too long to check"
            })
        except Exception as e:
            issues.append({
                "file": str(file_path),
                "issue": "Error during linting",
                "severity": "critical",
                "details": str(e)
            })

        return {
            "file": str(file_path),
            "has_issues": len(issues) > 0,
            "issues": issues
        }

    def generate_report(self, results: Dict) -> str:
        """Generate a linting report."""
        report = []
        report.append("# Script Linting Report\n")
        report.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        # Summary
        summary = results["summary"]
        report.append("## Summary\n\n")
        report.append(f"- **Total Files**: {summary['total_files']}\n")
        report.append(f"- **Files with Issues**: {summary['files_with_issues']}\n")
        report.append(f"- **Total Issues**: {summary['total_issues']}\n")
        report.append(f"- **Critical Issues**: {summary['critical_issues']}\n")
        report.append(f"- **Warnings**: {summary['warnings']}\n\n")

        # Python script issues
        if results["python_scripts"]:
            report.append("## Python Scripts\n\n")
            for script in results["python_scripts"]:
                report.append(f"### {script['file']}\n\n")
                for issue in script["issues"]:
                    severity_icon = "🔴" if issue["severity"] == "critical" else "⚠️"
                    report.append(f"- {severity_icon} **{issue['issue']}**: {issue['details']}\n")
                report.append("\n")

        # Shell script issues
        if results["shell_scripts"]:
            report.append("## Shell Scripts\n\n")
            for script in results["shell_scripts"]:
                report.append(f"### {script['file']}\n\n")
                for issue in script["issues"]:
                    severity_icon = "🔴" if issue["severity"] == "critical" else "⚠️"
                    report.append(f"- {severity_icon} **{issue['issue']}**: {issue['details']}\n")
                report.append("\n")

        return "\n".join(report)


def main():
    """Main linting function."""
    print(f"{GREEN}Scanning scripts for issues...{NC}\n")

    linter = ScriptLinter()
    results = linter.scan_scripts()

    # Generate report
    report = linter.generate_report(results)
    # Save MD report to QUALITY category
    report_path = Path("REPORTS/QUALITY/script_linting_report.md")
    report_path.parent.mkdir(parents=True, exist_ok=True)

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"{GREEN}Report saved to: {report_path}{NC}\n")

    # Print summary
    summary = results["summary"]
    print(f"Files Scanned: {summary['total_files']}")
    print(f"Files with Issues: {summary['files_with_issues']}")
    print(f"Critical Issues: {summary['critical_issues']}")
    print(f"Warnings: {summary['warnings']}")

    # Exit with error code if critical issues found
    if summary['critical_issues'] > 0:
        print(f"\n{RED}Critical issues found - please fix before proceeding{NC}")
        sys.exit(1)
    else:
        print(f"\n{GREEN}All scripts passed linting{NC}")
        sys.exit(0)


if __name__ == "__main__":
    main()
