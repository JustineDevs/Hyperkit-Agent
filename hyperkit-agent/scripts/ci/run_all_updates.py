#!/usr/bin/env python3
"""
Parallel Script Runner
Executes all key repo maintenance workflows in parallel using ThreadPoolExecutor.
Ensures no step is incomplete - if docs, tests, and registry don't all pass in sync, CI blocks.
"""

import asyncio
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Any, Tuple
import json
from datetime import datetime

class ParallelScriptRunner:
    """Runs multiple repo maintenance workflows in parallel with validation."""
    
    def __init__(self, root_path: str = None):
        # Auto-detect root path: if not provided, go up from scripts/ci/ to hyperkit-agent root
        if root_path is None:
            # Script is in hyperkit-agent/scripts/ci/, so go up 2 levels to get to hyperkit-agent root
            script_dir = Path(__file__).parent
            self.root_path = script_dir.parent.parent  # hyperkit-agent/
        else:
            self.root_path = Path(root_path)
        self.results = {}
        self.errors = []
        self.start_time = None
        
        # Define all maintenance workflows with their category directories
        self.workflows = {
            "version_update": {
                "script": "scripts/ci/update_version_in_docs.py",
                "description": "Update version information across all docs",
                "critical": True,
                "timeout": 30,
                "category": "STATUS",
                "output_file": "version_update_report.md"
            },
            "doc_drift_audit": {
                "script": "scripts/maintenance/doc_drift_audit.py",
                "description": "Audit documentation for drift",
                "critical": True,
                "timeout": 60,
                "category": "QUALITY",
                "output_file": "doc_drift_audit_report.md"
            },
            "deadweight_scan": {
                "script": "scripts/maintenance/deadweight_scan.py",
                "description": "Scan for deadweight patterns",
                "critical": True,
                "timeout": 120,
                "category": "QUALITY",
                "output_file": "deadweight_scan_report.md"
            },
            "cli_command_validation": {
                "script": "scripts/maintenance/cli_command_validation.py",
                "description": "Validate CLI commands",
                "critical": True,
                "timeout": 45,
                "category": "QUALITY",
                "output_file": "cli_command_validation_report.md"
            },
            "integration_sdk_audit": {
                "script": "scripts/maintenance/integration_sdk_audit.py",
                "description": "Audit SDK integrations",
                "critical": False,
                "timeout": 30,
                "category": "integration",
                "output_file": "integration_sdk_audit_report.md"
            },
            "legacy_file_inventory": {
                "script": "scripts/maintenance/legacy_file_inventory.py",
                "description": "Inventory legacy files",
                "critical": False,
                "timeout": 60,
                "category": "INFRASTRUCTURE",
                "output_file": "legacy_file_inventory_report.md"
            },
            "audit_badge_system": {
                "script": "scripts/ci/audit_badge_system.py",
                "description": "Add audit badges to docs",
                "critical": False,
                "timeout": 45,
                "category": "AUDIT",
                "output_file": "audit_badge_system_report.md"
            },
            "todo_to_issues_conversion": {
                "script": "scripts/maintenance/focused_todo_to_issues_conversion.py",
                "description": "Convert TODOs to GitHub issues",
                "critical": False,
                "timeout": 90,
                "category": "TODO",
                "output_file": "todo_to_issues_conversion_report.md"
            }
        }
    
    def run_script(self, workflow_name: str, workflow_config: Dict[str, Any]) -> Dict[str, Any]:
        """Run a single script and return results."""
        script_path = self.root_path / workflow_config["script"]
        
        if not script_path.exists():
            return {
                "status": "error",
                "error": f"Script not found: {script_path}",
                "workflow": workflow_name
            }
        
        try:
            # Run the script
            result = subprocess.run(
                [sys.executable, str(script_path)],
                cwd=self.root_path,
                capture_output=True,
                text=True,
                timeout=workflow_config["timeout"]
            )
            
            return {
                "status": "success" if result.returncode == 0 else "error",
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "workflow": workflow_name,
                "duration": workflow_config.get("duration", 0)
            }
            
        except subprocess.TimeoutExpired:
            return {
                "status": "timeout",
                "error": f"Script timed out after {workflow_config['timeout']} seconds",
                "workflow": workflow_name
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "workflow": workflow_name
            }
    
    def run_parallel(self, max_workers: int = 4) -> Dict[str, Any]:
        """Run all workflows in parallel."""
        self.start_time = time.time()
        print(f"Starting parallel execution of {len(self.workflows)} workflows...")
        print(f"Max workers: {max_workers}")
        print()
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all workflows
            future_to_workflow = {
                executor.submit(self.run_script, name, config): name
                for name, config in self.workflows.items()
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_workflow):
                workflow_name = future_to_workflow[future]
                try:
                    result = future.result()
                    self.results[workflow_name] = result
                    
                    # Print status
                    status_icon = "PASS" if result["status"] == "success" else "FAIL"
                    print(f"{status_icon} {workflow_name}: {result['status']}")
                    
                    if result["status"] != "success":
                        print(f"   Error: {result.get('error', 'Unknown error')}")
                    
                except Exception as e:
                    self.results[workflow_name] = {
                        "status": "error",
                        "error": str(e),
                        "workflow": workflow_name
                    }
                    print(f"FAIL {workflow_name}: Exception - {e}")
        
        duration = time.time() - self.start_time
        print(f"\nParallel execution completed in {duration:.2f} seconds")
        
        return self.analyze_results()
    
    def analyze_results(self) -> Dict[str, Any]:
        """Analyze results and determine if CI should block."""
        total_workflows = len(self.workflows)
        successful_workflows = sum(1 for r in self.results.values() if r["status"] == "success")
        failed_workflows = total_workflows - successful_workflows
        
        critical_workflows = [name for name, config in self.workflows.items() if config["critical"]]
        critical_failures = [
            name for name in critical_workflows 
            if self.results.get(name, {}).get("status") != "success"
        ]
        
        analysis = {
            "total_workflows": total_workflows,
            "successful_workflows": successful_workflows,
            "failed_workflows": failed_workflows,
            "critical_workflows": len(critical_workflows),
            "critical_failures": len(critical_failures),
            "critical_failure_names": critical_failures,
            "ci_should_block": len(critical_failures) > 0,
            "overall_status": "PASS" if critical_failures == 0 else "FAIL",
            "duration": time.time() - self.start_time if self.start_time else 0
        }
        
        return analysis
    
    def generate_report(self, analysis: Dict[str, Any]) -> str:
        """Generate a comprehensive report."""
        report_lines = [
            "# Parallel Script Runner Report",
            f"Generated: {datetime.now().isoformat()}",
            f"Duration: {analysis['duration']:.2f} seconds",
            "",
            "## Summary",
            f"- Total Workflows: {analysis['total_workflows']}",
            f"- Successful: {analysis['successful_workflows']}",
            f"- Failed: {analysis['failed_workflows']}",
            f"- Critical Workflows: {analysis['critical_workflows']}",
            f"- Critical Failures: {analysis['critical_failures']}",
            f"- CI Should Block: {'YES' if analysis['ci_should_block'] else 'NO'}",
            f"- Overall Status: {analysis['overall_status']}",
            ""
        ]
        
        if analysis['critical_failures'] > 0:
            report_lines.extend([
                "## Critical Failures",
                "The following critical workflows failed:",
                ""
            ])
            for failure_name in analysis['critical_failure_names']:
                result = self.results[failure_name]
                report_lines.extend([
                    f"### {failure_name}",
                    f"**Status**: {result['status']}",
                    f"**Error**: {result.get('error', 'Unknown error')}",
                    ""
                ])
        
        report_lines.extend([
            "## Detailed Results",
            ""
        ])
        
        for workflow_name, result in self.results.items():
            workflow_config = self.workflows[workflow_name]
            report_lines.extend([
                f"### {workflow_name}",
                f"**Description**: {workflow_config['description']}",
                f"**Status**: {result['status']}",
                f"**Critical**: {'Yes' if workflow_config['critical'] else 'No'}",
                ""
            ])
            
            if result['status'] != 'success':
                report_lines.extend([
                    f"**Error**: {result.get('error', 'Unknown error')}",
                    ""
                ])
            
            if result.get('stdout'):
                report_lines.extend([
                    "**Output**:",
                    "```",
                    result['stdout'][:500] + ("..." if len(result['stdout']) > 500 else ""),
                    "```",
                    ""
                ])
        
        return "\n".join(report_lines)
    
    def save_results(self, analysis: Dict[str, Any]):
        """Save results to files in their respective category directories.
        
        Organization:
        - All JSON files → REPORTS/JSON_DATA/
        - All MD files → REPORTS/{category}/
        """
        # Ensure JSON_DATA directory exists
        json_data_dir = self.root_path / "REPORTS" / "JSON_DATA"
        json_data_dir.mkdir(parents=True, exist_ok=True)
        
        # Save overall parallel runner JSON results in REPORTS/JSON_DATA/
        json_path = json_data_dir / "parallel_runner_results.json"
        
        full_results = {
            "analysis": analysis,
            "workflow_results": self.results,
            "workflow_configs": self.workflows,
            "timestamp": datetime.now().isoformat()
        }
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(full_results, f, indent=2)
        
        # Generate and save overall parallel runner report in REPORTS/SCRIPTS/
        report = self.generate_report(analysis)
        report_path = self.root_path / "REPORTS/SCRIPTS/PARALLEL_RUNNER_REPORT.md"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"Overall results saved to: {json_path}")
        print(f"Overall report saved to: {report_path}")
        
        # Save individual workflow results
        for workflow_name, workflow_config in self.workflows.items():
            if workflow_name in self.results:
                result = self.results[workflow_name]
                category = workflow_config.get("category", "SCRIPTS")
                output_file = workflow_config.get("output_file", f"{workflow_name}_report.md")
                
                # Determine category directory path for MD files
                category_dir = self.root_path / "REPORTS" / category
                category_dir.mkdir(parents=True, exist_ok=True)
                
                # Save individual workflow report (MD) to category directory
                workflow_report_path = category_dir / output_file
                
                # Generate workflow-specific report content
                workflow_report = self._generate_workflow_report(workflow_name, workflow_config, result)
                
                # Append to existing file or create new one
                mode = 'a' if workflow_report_path.exists() else 'w'
                with open(workflow_report_path, mode, encoding='utf-8') as f:
                    if mode == 'a':
                        f.write(f"\n\n---\n\n## Update: {datetime.now().isoformat()}\n\n")
                    f.write(workflow_report)
                
                # Save JSON data for this workflow to JSON_DATA directory
                json_data_path = json_data_dir / f"{workflow_name}_results.json"
                workflow_json = {
                    "workflow": workflow_name,
                    "config": workflow_config,
                    "result": result,
                    "timestamp": datetime.now().isoformat()
                }
                
                # Update existing JSON or create new
                if json_data_path.exists():
                    try:
                        with open(json_data_path, 'r', encoding='utf-8') as f:
                            existing_data = json.load(f)
                        # If it's a list, append; if dict, update
                        if isinstance(existing_data, list):
                            existing_data.append(workflow_json)
                            workflow_json = existing_data
                        else:
                            # Convert to list format
                            workflow_json = [existing_data, workflow_json]
                    except (json.JSONDecodeError, ValueError):
                        # If corrupted, overwrite
                        workflow_json = [workflow_json]
                else:
                    workflow_json = [workflow_json]
                
                with open(json_data_path, 'w', encoding='utf-8') as f:
                    json.dump(workflow_json, f, indent=2)
                
                print(f"  ✅ {workflow_name} → MD: {category_dir}/{output_file}, JSON: {json_data_path.name}")
    
    def _generate_workflow_report(self, workflow_name: str, workflow_config: Dict[str, Any], result: Dict[str, Any]) -> str:
        """Generate a report for an individual workflow."""
        status_icon = "✅" if result.get("status") == "success" else "❌"
        status_color = "success" if result.get("status") == "success" else "error"
        
        report_lines = [
            f"# {workflow_config.get('description', workflow_name)}",
            f"",
            f"**Status**: {status_icon} {result.get('status', 'unknown').upper()}",
            f"**Workflow**: `{workflow_name}`",
            f"**Critical**: {'Yes' if workflow_config.get('critical', False) else 'No'}",
            f"**Timestamp**: {datetime.now().isoformat()}",
            f""
        ]
        
        if result.get("error"):
            report_lines.extend([
                f"## Error",
                f"```",
                f"{result['error']}",
                f"```",
                f""
            ])
        
        if result.get("stdout"):
            report_lines.extend([
                f"## Output",
                f"```",
                f"{result['stdout'][:1000]}",  # Limit output size
                f"```",
                f""
            ])
        
        if result.get("stderr"):
            report_lines.extend([
                f"## Errors",
                f"```",
                f"{result['stderr'][:1000]}",  # Limit error output
                f"```",
                f""
            ])
        
        if result.get("duration"):
            report_lines.append(f"**Duration**: {result['duration']}s")
        
        return "\n".join(report_lines)


def main():
    """Main function to run parallel script execution."""
    runner = ParallelScriptRunner()
    
    print("Parallel Script Runner - CTO Audit Implementation")
    print("=" * 50)
    
    # Run workflows in parallel
    analysis = runner.run_parallel(max_workers=4)
    
    # Save results
    runner.save_results(analysis)
    
    # Print final status
    print("\n" + "=" * 50)
    print("FINAL STATUS")
    print("=" * 50)
    print(f"Overall Status: {analysis['overall_status']}")
    print(f"Critical Failures: {analysis['critical_failures']}")
    print(f"CI Should Block: {'YES' if analysis['ci_should_block'] else 'NO'}")
    
    if analysis['critical_failures'] > 0:
        print("\nCritical failures:")
        for failure_name in analysis['critical_failure_names']:
            print(f"  - {failure_name}")
    
    # Exit with appropriate code
    if analysis['ci_should_block']:
        print("\nCI BLOCKED - Critical workflows failed")
        sys.exit(1)
    else:
        print("\nCI PASSED - All critical workflows successful")
        sys.exit(0)


if __name__ == "__main__":
    main()
