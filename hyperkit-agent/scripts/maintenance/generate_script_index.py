"""
Generate Script Index

Parses all scripts in the scripts directory and generates/updates README files
with summaries and usage examples.
"""

import os
import sys
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List


class ScriptIndexGenerator:
    """Generate script index for directory READMEs."""

    def __init__(self, base_dir: Path = None):
        self.base_dir = base_dir or Path("hyperkit-agent")
        self.scripts_dir = self.base_dir / "scripts"

    def scan_script(self, file_path: Path) -> Dict:
        """Scan a script for metadata."""
        metadata = {
            "name": file_path.name,
            "path": str(file_path.relative_to(self.scripts_dir)),
            "type": "Python" if file_path.suffix == ".py" else "Shell",
            "size": file_path.stat().st_size,
            "modified": datetime.fromtimestamp(file_path.stat().st_mtime).strftime("%Y-%m-%d"),
            "description": "",
            "usage": ""
        }

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

                # Extract description from docstring or comments
                if file_path.suffix == ".py":
                    # Look for module docstring
                    docstring_match = re.search(r'"""(.*?)"""', content, re.DOTALL)
                    if docstring_match:
                        metadata["description"] = docstring_match.group(1).strip().split("\n")[0]
                else:
                    # Look for initial comments
                    for line in content.split("\n")[:10]:
                        if line.strip().startswith("#") and not line.strip().startswith("#!"):
                            desc = line.strip().lstrip("#").strip()
                            if desc and not desc.startswith("Color") and not desc.startswith("Configuration"):
                                metadata["description"] = desc
                                break

                # Extract usage examples
                usage_matches = re.findall(r"Usage:?\s*```\s*(.*?)```|Example:?\s*```\s*(.*?)```", content, re.DOTALL)
                if usage_matches:
                    metadata["usage"] = usage_matches[0][0] if usage_matches[0][0] else usage_matches[0][1]

        except Exception as e:
            metadata["description"] = f"Error reading file: {e}"

        return metadata

    def generate_directory_index(self, dir_path: Path) -> str:
        """Generate index for a directory."""
        scripts = []
        
        # Find all Python scripts
        for script in dir_path.rglob("*.py"):
            if "generate_script_index.py" not in str(script):
                scripts.append(self.scan_script(script))

        # Find all shell scripts
        for script in dir_path.rglob("*.sh"):
            scripts.append(self.scan_script(script))

        # Sort by name
        scripts.sort(key=lambda x: x["name"])

        return scripts

    def generate_readme(self, dir_path: Path, scripts: List[Dict]) -> str:
        """Generate README content for a directory."""
        readme_lines = []
        
        # Get directory name
        dir_name = dir_path.name.title()
        readme_lines.append(f"# {dir_name} Scripts\n")

        # Add brief description
        if dir_path.name == "ci":
            readme_lines.append("Scripts for continuous integration, deployment, badge generation, and version management.\n")
        elif dir_path.name == "dev":
            readme_lines.append("Scripts for local development setup, installation, and workflow utilities.\n")
        elif dir_path.name == "maintenance":
            readme_lines.append("Scripts for code health checks, drift detection, and repository maintenance.\n")
        elif dir_path.name == "emergency":
            readme_lines.append("Scripts for critical incident response and hotfix deployment.\n")

        # Create table
        if scripts:
            readme_lines.append("## Scripts\n\n")
            readme_lines.append("| Script | Description | Type | Modified |")
            readme_lines.append("|--------|-------------|------|----------|")
            
            for script in scripts:
                desc = script["description"][:50] + "..." if len(script["description"]) > 50 else script["description"]
                readme_lines.append(f"| `{script['name']}` | {desc} | {script['type']} | {script['modified']} |")

        readme_lines.append("\n")

        # Add auto-generated notice
        readme_lines.append(f"*This file was auto-generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")

        return "\n".join(readme_lines)


def main():
    """Main function to generate script indices."""
    generator = ScriptIndexGenerator()

    # Process each subdirectory
    subdirs = ["ci", "dev", "maintenance", "emergency"]

    for subdir in subdirs:
        dir_path = generator.scripts_dir / subdir
        if dir_path.exists():
            print(f"Generating index for {subdir}/...")
            scripts = generator.generate_directory_index(dir_path)
            
            # Generate README
            readme_content = generator.generate_readme(dir_path, scripts)
            
            # Write README (don't overwrite if exists)
            readme_path = dir_path / "README_GENERATED.md"
            with open(readme_path, "w", encoding="utf-8") as f:
                f.write(readme_content)
            
            print(f"✓ Generated {subdir}/README_GENERATED.md with {len(scripts)} scripts")

    print("\nScript index generation complete!")


if __name__ == "__main__":
    main()
