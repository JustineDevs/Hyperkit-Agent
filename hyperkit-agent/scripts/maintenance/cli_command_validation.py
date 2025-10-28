#!/usr/bin/env python3
"""
CLI Command Validation Script
Verifies all CLI commands work and maps them to actual code coverage
"""

import subprocess
import json
import os
import sys
from pathlib import Path
from datetime import datetime

class CLICommandValidator:
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "commands": {},
            "summary": {
                "total": 0,
                "working": 0,
                "broken": 0,
                "not_implemented": 0
            }
        }
    
    def discover_commands(self):
        """Discover all available CLI commands"""
        try:
            # Get help output to discover commands
            result = subprocess.run(
                ["python", "cli/main.py", "--help"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                print(f"Error discovering commands: {result.stderr}")
                return []
            
            # Parse commands from help output
            commands = []
            lines = result.stdout.split('\n')
            in_commands_section = False
            
            for line in lines:
                if 'Commands:' in line:
                    in_commands_section = True
                    continue
                
                if in_commands_section and line.strip():
                    if line.startswith('  '):
                        cmd = line.strip().split()[0]
                        if cmd and not cmd.startswith('-'):
                            commands.append(cmd)
                    elif not line.startswith(' '):
                        break
            
            return commands
            
        except Exception as e:
            print(f"Error discovering commands: {e}")
            return []
    
    def test_command(self, command, args=None):
        """Test a single CLI command"""
        if args is None:
            args = ["--help"]
        
        cmd_args = ["python", "cli/main.py", command] + args
        
        try:
            result = subprocess.run(
                cmd_args,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            return {
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "success": result.returncode == 0
            }
            
        except subprocess.TimeoutExpired:
            return {
                "returncode": -1,
                "stdout": "",
                "stderr": "Command timed out",
                "success": False
            }
        except Exception as e:
            return {
                "returncode": -1,
                "stdout": "",
                "stderr": str(e),
                "success": False
            }
    
    def validate_command(self, command):
        """Validate a command with multiple test scenarios"""
        print(f"Testing command: {command}")
        
        command_result = {
            "command": command,
            "tests": {},
            "overall_status": "unknown"
        }
        
        # Test 1: Help command
        help_result = self.test_command(command, ["--help"])
        command_result["tests"]["help"] = help_result
        
        # Test 2: Basic execution (if not help)
        if command != "help":
            basic_result = self.test_command(command, [])
            command_result["tests"]["basic"] = basic_result
        
        # Test 3: Command-specific tests
        if command == "generate":
            test_result = self.test_command(command, ["contract", "--type", "ERC20", "--name", "TestToken"])
            command_result["tests"]["generate_contract"] = test_result
        
        elif command == "audit":
            test_result = self.test_command(command, ["contract", "--contract", "test.sol"])
            command_result["tests"]["audit_contract"] = test_result
        
        elif command == "deploy":
            test_result = self.test_command(command, ["--network", "hyperion", "--contract", "test.sol"])
            command_result["tests"]["deploy_contract"] = test_result
        
        elif command == "workflow":
            test_result = self.test_command(command, ["run", "test prompt"])
            command_result["tests"]["workflow_run"] = test_result
        
        # Determine overall status
        all_tests = list(command_result["tests"].values())
        if all(test["success"] for test in all_tests):
            command_result["overall_status"] = "working"
            self.results["summary"]["working"] += 1
        elif any(test["success"] for test in all_tests):
            command_result["overall_status"] = "partial"
            self.results["summary"]["broken"] += 1
        else:
            command_result["overall_status"] = "broken"
            self.results["summary"]["broken"] += 1
        
        return command_result
    
    def check_code_coverage(self, command):
        """Check if command has corresponding test coverage"""
        test_files = [
            f"tests/unit/test_{command}.py",
            f"tests/integration/test_{command}.py",
            f"tests/e2e/test_{command}.py",
            f"tests/test_{command}.py"
        ]
        
        coverage = []
        for test_file in test_files:
            if os.path.exists(test_file):
                coverage.append(test_file)
        
        return coverage
    
    def run_validation(self):
        """Run complete CLI validation"""
        print("Starting CLI command validation...")
        
        # Discover commands
        commands = self.discover_commands()
        print(f"Discovered commands: {commands}")
        
        if not commands:
            print("No commands discovered, using known commands")
            commands = [
                "generate", "deploy", "audit", "batch-audit", 
                "verify", "monitor", "config", "workflow", "status"
            ]
        
        self.results["summary"]["total"] = len(commands)
        
        # Validate each command
        for command in commands:
            command_result = self.validate_command(command)
            command_result["test_coverage"] = self.check_code_coverage(command)
            self.results["commands"][command] = command_result
        
        # Generate report
        self.generate_report()
        
        return self.results
    
    def generate_report(self):
        """Generate validation report"""
        report_content = f"""# CLI Command Validation Report

<!-- VERSION_PLACEHOLDER -->
**Version**: 1.4.5
**Last Updated**: {datetime.now().strftime('%Y-%m-%d')}
**Commit**: unknown
<!-- /VERSION_PLACEHOLDER -->

## Summary

- **Total Commands**: {self.results['summary']['total']}
- **Working**: {self.results['summary']['working']}
- **Broken/Partial**: {self.results['summary']['broken']}
- **Not Implemented**: {self.results['summary']['not_implemented']}

## Command Status

"""
        
        for command, result in self.results["commands"].items():
            status_emoji = {
                "working": "✅",
                "partial": "⚠️",
                "broken": "❌",
                "unknown": "❓"
            }.get(result["overall_status"], "❓")
            
            report_content += f"### {status_emoji} {command}\n"
            report_content += f"- **Status**: {result['overall_status']}\n"
            report_content += f"- **Test Coverage**: {', '.join(result['test_coverage']) if result['test_coverage'] else 'None'}\n"
            
            # Add test results
            for test_name, test_result in result["tests"].items():
                test_status = "✅" if test_result["success"] else "❌"
                report_content += f"- **{test_name}**: {test_status}\n"
            
            report_content += "\n"
        
        # Add recommendations
        report_content += """## Recommendations

### High Priority Fixes
"""
        
        broken_commands = [cmd for cmd, result in self.results["commands"].items() 
                          if result["overall_status"] in ["broken", "partial"]]
        
        if broken_commands:
            for cmd in broken_commands:
                report_content += f"- Fix `{cmd}` command implementation\n"
        else:
            report_content += "- All commands are working correctly\n"
        
        report_content += """
### Test Coverage Improvements
"""
        
        no_coverage = [cmd for cmd, result in self.results["commands"].items() 
                      if not result["test_coverage"]]
        
        if no_coverage:
            for cmd in no_coverage:
                report_content += f"- Add test coverage for `{cmd}` command\n"
        else:
            report_content += "- All commands have test coverage\n"
        
        report_content += """
---
*This report is automatically generated by the CLI validation script.*
"""
        
        # Save report
        with open("REPORTS/CLI_VALIDATION_REPORT.md", "w", encoding="utf-8") as f:
            f.write(report_content)
        
        # Save JSON results
        with open("REPORTS/cli_validation_results.json", "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2)
        
        print(f"Generated CLI validation report")
        print(f"Working: {self.results['summary']['working']}/{self.results['summary']['total']}")

def main():
    """Main function"""
    validator = CLICommandValidator()
    results = validator.run_validation()
    
    # Print summary
    print("\n" + "="*50)
    print("CLI VALIDATION SUMMARY")
    print("="*50)
    print(f"Total Commands: {results['summary']['total']}")
    print(f"Working: {results['summary']['working']}")
    print(f"Broken/Partial: {results['summary']['broken']}")
    print(f"Not Implemented: {results['summary']['not_implemented']}")
    
    # Return exit code based on results
    if results['summary']['broken'] > 0:
        return 1
    return 0

if __name__ == "__main__":
    exit(main())
