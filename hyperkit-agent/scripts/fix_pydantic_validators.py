#!/usr/bin/env python3
"""
Fix Pydantic v1 validators to v2 style
"""

import re

def fix_pydantic_validators(file_path):
    """Fix Pydantic validators in a file"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Replace @validator with @field_validator and add @classmethod
    content = re.sub(
        r'@validator\(([^)]+)\)\s*\n\s*def\s+(\w+)\(cls,\s*v\):',
        r'@field_validator(\1)\n    @classmethod\n    def \2(cls, v):',
        content
    )
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"Fixed validators in {file_path}")

if __name__ == "__main__":
    fix_pydantic_validators("core/config/schema.py")
