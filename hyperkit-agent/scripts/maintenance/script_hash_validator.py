"""
Script Hash Validation System

Implements script marker system with hashes for versioning and validation.
Each script file includes a SCRIPT_MARKER with name, version, and hash.
"""

import hashlib
import re
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

class ScriptMarker:
    """Script marker system for versioning and validation"""
    
    MARKER_PATTERN = re.compile(
        r'# SCRIPT_MARKER:\s*name=(?P<name>[^,]+),\s*version=(?P<version>[^,]+),\s*hash=(?P<hash>[^,\n]+)'
    )
    
    @staticmethod
    def generate_hash(content: str) -> str:
        """Generate SHA-256 hash of script content"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]
    
    @staticmethod
    def add_marker(file_path: Path, name: str, version: str):
        """Add script marker to a file"""
        content = file_path.read_text(encoding='utf-8')
        
        # Check if marker already exists
        existing = ScriptMarker.get_marker(content)
        if existing:
            print(f"Script already has marker: {existing}")
            return
        
        # Generate hash
        hash_value = ScriptMarker.generate_hash(content)
        
        # Create marker
        marker = f"# SCRIPT_MARKER: name={name}, version={version}, hash={hash_value}\n\n"
        
        # Add marker at the top
        new_content = marker + content
        
        file_path.write_text(new_content, encoding='utf-8')
        print(f"Added marker to {file_path}: name={name}, version={version}, hash={hash_value}")
    
    @staticmethod
    def get_marker(content: str) -> Optional[Dict[str, str]]:
        """Extract script marker from content"""
        match = ScriptMarker.MARKER_PATTERN.search(content)
        if match:
            return match.groupdict()
        return None
    
    @staticmethod
    def validate(file_path: Path) -> Dict[str, Any]:
        """Validate a script file"""
        try:
            content = file_path.read_text(encoding='utf-8')
            marker = ScriptMarker.get_marker(content)
            
            if not marker:
                return {
                    "valid": False,
                    "error": "No marker found",
                    "file": str(file_path)
                }
            
            # Remove marker for hash calculation
            content_without_marker = ScriptMarker.MARKER_PATTERN.sub('', content, count=1)
            expected_hash = ScriptMarker.generate_hash(content_without_marker)
            actual_hash = marker['hash']
            
            return {
                "valid": expected_hash == actual_hash,
                "expected_hash": expected_hash,
                "actual_hash": actual_hash,
                "name": marker['name'],
                "version": marker['version'],
                "file": str(file_path)
            }
        except Exception as e:
            return {
                "valid": False,
                "error": str(e),
                "file": str(file_path)
            }
    
    @staticmethod
    def scan_directory(directory: Path) -> Dict[str, Any]:
        """Scan directory for script files and validate"""
        results = {
            "scanned_at": datetime.now().isoformat(),
            "total_files": 0,
            "valid_files": 0,
            "invalid_files": 0,
            "files_without_markers": 0,
            "details": []
        }
        
        for py_file in directory.rglob("*.py"):
            # Skip __pycache__ and virtual environments
            if '__pycache__' in str(py_file) or 'venv' in str(py_file) or '.pyc' in str(py_file):
                continue
            
            results["total_files"] += 1
            validation = ScriptMarker.validate(py_file)
            
            results["details"].append(validation)
            
            if validation.get("valid"):
                results["valid_files"] += 1
            elif "error" in validation and "No marker found" in validation["error"]:
                results["files_without_markers"] += 1
            else:
                results["invalid_files"] += 1
        
        return results

def main():
    """Main execution"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python script_hash_validator.py scan <directory>")
        print("  python script_hash_validator.py add <file> <name> <version>")
        print("  python script_hash_validator.py validate <file>")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "scan":
        if len(sys.argv) < 3:
            directory = Path("hyperkit-agent")
        else:
            directory = Path(sys.argv[2])
        
        print(f"Scanning directory: {directory}")
        results = ScriptMarker.scan_directory(directory)
        
        # Save results
        output_file = Path("hyperkit-agent/REPORTS/script_hash_validation.json")
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(json.dumps(results, indent=2))
        
        print(f"\nScan Results:")
        print(f"  Total files: {results['total_files']}")
        print(f"  Valid files: {results['valid_files']}")
        print(f"  Invalid files: {results['invalid_files']}")
        print(f"  Files without markers: {results['files_without_markers']}")
        print(f"\nResults saved to {output_file}")
    
    elif command == "add":
        if len(sys.argv) < 5:
            print("Usage: python script_hash_validator.py add <file> <name> <version>")
            sys.exit(1)
        
        file_path = Path(sys.argv[2])
        name = sys.argv[3]
        version = sys.argv[4]
        
        ScriptMarker.add_marker(file_path, name, version)
    
    elif command == "validate":
        if len(sys.argv) < 3:
            print("Usage: python script_hash_validator.py validate <file>")
            sys.exit(1)
        
        file_path = Path(sys.argv[2])
        result = ScriptMarker.validate(file_path)
        print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
