#!/usr/bin/env python3
"""
Test script for version update automation
Run this to test the versioning system without making actual changes

⚠️ NOTE: This script tests the legacy version_update.py script.
For production, use the canonical scripts from hyperkit-agent/scripts/ci/
"""

import os
import sys
from pathlib import Path

# Add the scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Try to import from legacy script (for backward compatibility)
try:
    from version_update import get_current_version, bump_version, validate_environment
except ImportError:
    print("⚠️  Legacy version_update.py not available")
    print("   Use canonical scripts from hyperkit-agent/scripts/ci/ instead")
    sys.exit(1)

def test_version_system():
    """Test the version system without making changes."""
    print("🧪 Testing HyperKit Version System")
    print("=" * 50)
    
    try:
        # Test environment validation
        print("1. Testing environment validation...")
        if validate_environment():
            print("   ✅ Environment validation passed")
        else:
            print("   ❌ Environment validation failed")
            return False
        
        # Test version detection
        print("\n2. Testing version detection...")
        current_version = get_current_version()
        print(f"   ✅ Current version: {current_version}")
        
        # Test version bumping
        print("\n3. Testing version bumping...")
        test_cases = [
            ("patch", "1.2.0", "1.2.1"),
            ("minor", "1.2.0", "1.3.0"),
            ("major", "1.2.0", "2.0.0"),
            ("patch", "2.1.5", "2.1.6"),
            ("minor", "2.1.5", "2.2.0"),
            ("major", "2.1.5", "3.0.0"),
        ]
        
        for bump_type, input_version, expected in test_cases:
            result = bump_version(input_version, bump_type)
            if result == expected:
                print(f"   ✅ {bump_type}: {input_version} → {result}")
            else:
                print(f"   ❌ {bump_type}: {input_version} → {result} (expected {expected})")
                return False
        
        print("\n🎉 All tests passed!")
        print("\n📋 Ready to run version update (use canonical scripts):")
        print("   npm run version:patch      # Recommended")
        print("   npm run version:minor      # Recommended")
        print("   npm run version:major      # Recommended")
        print("\n   Or directly:")
        print("   python hyperkit-agent/scripts/ci/version_bump.py patch")
        print("\n⚠️  Legacy script (not recommended):")
        print("   python .github/workflows/scripts/version_update.py")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_version_system()
    sys.exit(0 if success else 1)
