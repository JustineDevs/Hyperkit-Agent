#!/usr/bin/env python3
"""
Documentation Drift Audit System
Automated quarterly audits to prevent accumulation of outdated guides
"""

import os
import json
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any


class DocDriftAuditor:
    """Audit system for documentation drift detection"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.docs_root = project_root / "docs"
        self.hyperkit_docs_root = project_root / "hyperkit-agent" / "docs"
        self.audit_results = {
            "timestamp": datetime.now().isoformat(),
            "drift_detected": [],
            "outdated_patterns": [],
            "recommendations": []
        }
    
    def audit_future_tense(self) -> List[Dict[str, Any]]:
        """Detect future-tense language in documentation"""
        future_patterns = [
            r"will be",
            r"will have", 
            r"will support",
            r"will provide",
            r"will enable",
            r"will allow",
            r"will include",
            r"will implement",
            r"will add",
            r"will create",
            r"coming soon",
            r"planned for",
            r"roadmap",
            r"upcoming",
            r"TBD",
            r"TODO",
            r"FIXME"
        ]
        
        drift_items = []
        
        for docs_path in [self.docs_root, self.hyperkit_docs_root]:
            if not docs_path.exists():
                continue
                
            for md_file in docs_path.rglob("*.md"):
                content = md_file.read_text(encoding='utf-8', errors='ignore')
                
                for pattern in future_patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        drift_items.append({
                            "file": str(md_file.relative_to(self.project_root)),
                            "line": line_num,
                            "pattern": pattern,
                            "context": content[max(0, match.start()-50):match.end()+50],
                            "severity": "medium"
                        })
        
        return drift_items
    
    def audit_outdated_cli_commands(self) -> List[Dict[str, Any]]:
        """Detect outdated CLI command patterns"""
        outdated_patterns = [
            r"python main\.py",
            r"python cli/main\.py", 
            r"python -m hyperagent",
            r"python scripts/",
            r"main\.py",
            r"cli/main\.py"
        ]
        
        drift_items = []
        
        for docs_path in [self.docs_root, self.hyperkit_docs_root]:
            if not docs_path.exists():
                continue
                
            for md_file in docs_path.rglob("*.md"):
                content = md_file.read_text(encoding='utf-8', errors='ignore')
                
                for pattern in outdated_patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        drift_items.append({
                            "file": str(md_file.relative_to(self.project_root)),
                            "line": line_num,
                            "pattern": pattern,
                            "context": content[max(0, match.start()-50):match.end()+50],
                            "severity": "high",
                            "recommendation": "Replace with 'hyperagent' command"
                        })
        
        return drift_items
    
    def audit_stale_content(self) -> List[Dict[str, Any]]:
        """Detect stale content based on timestamps and patterns"""
        stale_patterns = [
            r"last updated.*202[0-3]",  # Old dates
            r"version.*[0-9]+\.[0-9]+\.[0-9]+",  # Version numbers
            r"status.*development",  # Still in development
            r"status.*beta",  # Beta status
            r"status.*alpha"  # Alpha status
        ]
        
        drift_items = []
        
        for docs_path in [self.docs_root, self.hyperkit_docs_root]:
            if not docs_path.exists():
                continue
                
            for md_file in docs_path.rglob("*.md"):
                # Check file modification time
                file_age = datetime.now() - datetime.fromtimestamp(md_file.stat().st_mtime)
                if file_age > timedelta(days=90):  # Files older than 90 days
                    drift_items.append({
                        "file": str(md_file.relative_to(self.project_root)),
                        "pattern": "stale_file",
                        "age_days": file_age.days,
                        "severity": "low",
                        "recommendation": "Review and update content"
                    })
                
                content = md_file.read_text(encoding='utf-8', errors='ignore')
                
                for pattern in stale_patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        drift_items.append({
                            "file": str(md_file.relative_to(self.project_root)),
                            "line": line_num,
                            "pattern": pattern,
                            "context": content[max(0, match.start()-50):match.end()+50],
                            "severity": "medium",
                            "recommendation": "Update status and version information"
                        })
        
        return drift_items
    
    def audit_broken_links(self) -> List[Dict[str, Any]]:
        """Detect broken internal links"""
        drift_items = []
        
        for docs_path in [self.docs_root, self.hyperkit_docs_root]:
            if not docs_path.exists():
                continue
                
            for md_file in docs_path.rglob("*.md"):
                content = md_file.read_text(encoding='utf-8', errors='ignore')
                
                # Find markdown links
                link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
                matches = re.finditer(link_pattern, content)
                
                for match in matches:
                    link_text = match.group(1)
                    link_path = match.group(2)
                    
                    # Skip external links
                    if link_path.startswith(('http://', 'https://', 'mailto:')):
                        continue
                    
                    # Check if internal link exists
                    if link_path.startswith('./'):
                        target_file = md_file.parent / link_path[2:]
                    elif link_path.startswith('/'):
                        target_file = self.project_root / link_path[1:]
                    else:
                        target_file = md_file.parent / link_path
                    
                    if not target_file.exists():
                        line_num = content[:match.start()].count('\n') + 1
                        drift_items.append({
                            "file": str(md_file.relative_to(self.project_root)),
                            "line": line_num,
                            "pattern": "broken_link",
                            "link_text": link_text,
                            "link_path": link_path,
                            "severity": "high",
                            "recommendation": f"Fix or remove broken link: {link_path}"
                        })
        
        return drift_items
    
    def run_full_audit(self) -> Dict[str, Any]:
        """Run complete documentation drift audit"""
        print("Running Documentation Drift Audit...")
        print("=" * 60)
        
        # Run all audit checks
        self.audit_results["drift_detected"].extend(self.audit_future_tense())
        self.audit_results["drift_detected"].extend(self.audit_outdated_cli_commands())
        self.audit_results["drift_detected"].extend(self.audit_stale_content())
        self.audit_results["drift_detected"].extend(self.audit_broken_links())
        
        # Generate summary
        total_issues = len(self.audit_results["drift_detected"])
        high_severity = len([item for item in self.audit_results["drift_detected"] if item.get("severity") == "high"])
        medium_severity = len([item for item in self.audit_results["drift_detected"] if item.get("severity") == "medium"])
        low_severity = len([item for item in self.audit_results["drift_detected"] if item.get("severity") == "low"])
        
        print(f"Audit Summary:")
        print(f"  Total Issues: {total_issues}")
        print(f"  High Severity: {high_severity}")
        print(f"  Medium Severity: {medium_severity}")
        print(f"  Low Severity: {low_severity}")
        
        # Generate recommendations
        if high_severity > 0:
            self.audit_results["recommendations"].append("High priority: Fix outdated CLI commands and broken links")
        if medium_severity > 0:
            self.audit_results["recommendations"].append("Medium priority: Update future-tense language and stale content")
        if low_severity > 0:
            self.audit_results["recommendations"].append("Low priority: Review old files for updates")
        
        if total_issues == 0:
            self.audit_results["recommendations"].append("No drift detected - documentation is up to date!")
        
        return self.audit_results
    
    def save_audit_report(self, output_path: Path = None):
        """Save audit results to file"""
        if output_path is None:
            output_path = self.project_root / "hyperkit-agent" / "REPORTS" / f"doc_drift_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(self.audit_results, indent=2))
        
        print(f"Audit report saved: {output_path}")
        return output_path


def main():
    """Main entry point for doc drift audit"""
    project_root = Path(__file__).parent.parent.parent
    auditor = DocDriftAuditor(project_root)
    
    # Run audit
    results = auditor.run_full_audit()
    
    # Save report
    report_path = auditor.save_audit_report()
    
    # Print detailed results
    print("\n" + "=" * 60)
    print("Detailed Results:")
    print("=" * 60)
    
    for item in results["drift_detected"]:
        severity_icon = {"high": "[HIGH]", "medium": "[MED]", "low": "[LOW]"}.get(item["severity"], "[?]")
        print(f"{severity_icon} {item['file']}:{item.get('line', 'N/A')} - {item['pattern']}")
        if "recommendation" in item:
            print(f"   -> {item['recommendation']}")
    
    print("\n" + "=" * 60)
    print("Recommendations:")
    print("=" * 60)
    
    for rec in results["recommendations"]:
        print(f"  {rec}")
    
    print("\n" + "=" * 60)
    print("Documentation drift audit completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
