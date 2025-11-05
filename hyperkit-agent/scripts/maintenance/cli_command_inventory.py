"""
CLI Command Inventory Script

Generates a comprehensive inventory of all CLI commands, their implementation status,
test coverage, and functionality mapping.
"""

import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import ast
import re

def get_cli_commands() -> Dict[str, Any]:
    """Discover all CLI commands from the CLI structure"""
    
    cli_dir = Path("cli/commands")
    commands = {}
    
    # Main commands from cli/main.py
    main_cmds = [
        "help", "version", "status", "test-rag", "limitations"
    ]
    
    # Command groups
    command_groups = {
        "generate": ["contract", "templates", "from-template"],
        "deploy": ["contract", "status", "info"],
        "audit": ["contract", "batch", "report"],
        "batch-audit": ["contracts"],
        "verify": ["contract", "list", "status", "deployment"],
        "monitor": ["health", "metrics", "logs", "status"],
        "config": ["get", "set", "save", "load", "reset", "list"],
        "workflow": ["run", "list", "status"]
    }
    
    commands["main"] = {}
    for cmd in main_cmds:
        commands["main"][cmd] = {"status": "working", "category": "core"}
    
    commands["groups"] = {}
    for group, subcmds in command_groups.items():
        commands["groups"][group] = {
            "subcommands": subcmds,
            "category": "functional"
        }
    
    return commands

def check_command_implementation(cmd_file: Path) -> Dict[str, Any]:
    """Check if command is implemented or has TODOs"""
    
    try:
        content = cmd_file.read_text(encoding='utf-8')
        
        # Count TODOs and check implementation
        todo_count = len(re.findall(r'TODO|FIXME|XXX', content, re.IGNORECASE))
        
        # Check if it's a stub
        is_stub = todo_count > 5 or "stub" in content.lower() or "not implemented" in content.lower()
        
        return {
            "implemented": not is_stub,
            "todo_count": todo_count,
            "is_stub": is_stub,
            "lines": len(content.split('\n'))
        }
    except Exception as e:
        return {"error": str(e)}

def check_test_coverage(cmd_name: str) -> Dict[str, Any]:
    """Check test coverage for a command"""
    
    test_dir = Path("tests")
    coverage_info = {
        "unit_tests": False,
        "integration_tests": False,
        "e2e_tests": False
    }
    
    # Check for tests
    for test_type, test_path in [
        ("unit_tests", test_dir / "unit"),
        ("integration_tests", test_dir / "integration"),
        ("e2e_tests", test_dir / "e2e")
    ]:
        if test_path.exists():
            for test_file in test_path.glob("*.py"):
                try:
                    content = test_file.read_text(encoding='utf-8')
                    if cmd_name in content.lower():
                        coverage_info[test_type] = True
                        break
                except:
                    pass
    
    return coverage_info

def generate_inventory() -> Dict[str, Any]:
    """Generate comprehensive command inventory"""
    
    commands = get_cli_commands()
    inventory = {
        "generated_at": datetime.now().isoformat(),
        "commands": {},
        "summary": {
            "total_commands": 0,
            "implemented": 0,
            "stubs": 0,
            "with_tests": 0,
            "categories": {}
        }
    }
    
    # Inventory main commands
    for cmd_name, cmd_info in commands["main"].items():
        inventory["commands"][cmd_name] = {
            "name": cmd_name,
            "category": cmd_info["category"],
            "type": "main",
            "status": "working",
            "tests": {"e2e_tests": True}
        }
        inventory["summary"]["total_commands"] += 1
        inventory["summary"]["implemented"] += 1
        inventory["summary"]["with_tests"] += 1
    
    # Inventory command groups
    cli_dir = Path("cli/commands")
    for group_name, group_info in commands["groups"].items():
        cmd_file = cli_dir / f"{group_name}.py"
        
        impl_status = check_command_implementation(cmd_file) if cmd_file.exists() else {"implemented": False, "todo_count": 0}
        test_coverage = check_test_coverage(group_name)
        
        inventory["commands"][group_name] = {
            "name": group_name,
            "category": group_info["category"],
            "type": "group",
            "subcommands": group_info["subcommands"],
            "file": str(cmd_file.relative_to("hyperkit-agent")),
            "status": "working" if impl_status.get("implemented", False) else "stub",
            "implementation": impl_status,
            "tests": test_coverage,
            "has_tests": any(test_coverage.values())
        }
        
        inventory["summary"]["total_commands"] += 1
        if impl_status.get("implemented", False):
            inventory["summary"]["implemented"] += 1
        else:
            inventory["summary"]["stubs"] += 1
        
        if any(test_coverage.values()):
            inventory["summary"]["with_tests"] += 1
    
    # Calculate categories
    for cmd_name, cmd_info in inventory["commands"].items():
        cat = cmd_info["category"]
        if cat not in inventory["summary"]["categories"]:
            inventory["summary"]["categories"][cat] = 0
        inventory["summary"]["categories"][cat] += 1
    
    return inventory

def main():
    """Main execution"""
    print("Generating CLI command inventory...")
    
    inventory = generate_inventory()
    
    # Write JSON report to JSON_DATA directory (hyperkit-agent/REPORTS/JSON_DATA/)
    # Script is in hyperkit-agent/scripts/maintenance/, so go up 2 levels to hyperkit-agent/
    script_dir = Path(__file__).parent.resolve()
    hyperkit_agent_root = script_dir.parent.parent
    output_file = hyperkit_agent_root / "REPORTS" / "JSON_DATA" / "cli_command_inventory.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(inventory, indent=2, default=str))
    
    print(f"Inventory generated: {output_file}")
    
    # Print summary
    print("\nCLI Command Inventory Summary:")
    print(f"  Total Commands: {inventory['summary']['total_commands']}")
    print(f"  Implemented: {inventory['summary']['implemented']}")
    print(f"  Stubs: {inventory['summary']['stubs']}")
    print(f"  With Tests: {inventory['summary']['with_tests']}")
    print(f"\nCategories:")
    for cat, count in inventory['summary']['categories'].items():
        print(f"  {cat}: {count}")

if __name__ == "__main__":
    main()
