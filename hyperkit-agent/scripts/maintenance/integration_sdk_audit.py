#!/usr/bin/env python3
"""
Integration SDK Audit Script
Verifies ALITH SDK status and LazAI network configuration

CRITICAL NOTES:
- Alith SDK is the ONLY AI agent (uses OpenAI API key)
- LazAI is network-only (blockchain RPC), NOT an AI agent
- Obsidian RAG is deprecated - IPFS Pinata RAG is exclusive
"""

import os
import re
import json
from pathlib import Path
from datetime import datetime

class IntegrationSDKAuditor:
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "integrations": {},
            "recommendations": []
        }
    
    def audit_alith_integration(self):
        """
        Audit ALITH SDK integration
        
        Alith SDK is the ONLY AI agent - uses OpenAI API key (not LazAI key).
        Checks for proper implementation in services/core/ai_agent.py
        """
        alith_status = {
            "name": "ALITH SDK",
            "status": "implemented",
            "type": "ai_agent",
            "files": [],
            "issues": [],
            "recommendations": [],
            "config_requirements": ["OPENAI_API_KEY", "ALITH_ENABLED"]
        }
        
        # Check main AI agent implementation
        ai_agent_file = "services/core/ai_agent.py"
        if os.path.exists(ai_agent_file):
            alith_status["files"].append(ai_agent_file)
            with open(ai_agent_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if "from alith import Agent" in content:
                    alith_status["status"] = "implemented"
                    if "LAZAI_API_KEY" in content and "lazai.*agent" in content.lower():
                        alith_status["issues"].append("Contains deprecated LazAI AI agent references")
                        alith_status["recommendations"].append("Remove LazAI AI agent code - LazAI is network-only")
                else:
                    alith_status["status"] = "not_implemented"
                    alith_status["recommendations"].append("Alith SDK integration missing from ai_agent.py")
        
        # Check stub in services/alith/__init__.py
        alith_init = "services/alith/__init__.py"
        if os.path.exists(alith_init):
            alith_status["files"].append(alith_init)
            with open(alith_init, 'r', encoding='utf-8') as f:
                content = f.read()
                if "is_alith_available" in content:
                    alith_status["status"] = "implemented"  # Stub exists, implementation in ai_agent.py
        
        return alith_status
    
    def audit_lazai_integration(self):
        """
        Audit LazAI integration
        
        LazAI is network-only (blockchain RPC endpoint), NOT an AI agent.
        Should only be configured in network config, not as AI agent.
        """
        lazai_status = {
            "name": "LAZAI SDK",
            "status": "not_implemented",
            "files": [],
            "issues": [],
            "recommendations": []
        }
        
        # Check for LAZAI files
        lazai_files = [
            "services/lazai/agent.py",
            "services/lazai/__init__.py",
            "services/lazai/sdk.py"
        ]
        
        for file_path in lazai_files:
            if os.path.exists(file_path):
                lazai_status["files"].append(file_path)
            else:
                lazai_status["issues"].append(f"Missing file: {file_path}")
        
        # Check references in code
        reference_files = []
        for root, dirs, files in os.walk("."):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            if "lazai" in content.lower() and "not available" not in content.lower():
                                reference_files.append(file_path)
                    except:
                        pass
        
        lazai_status["reference_files"] = reference_files
        
        # Check if explicitly marked as not available
        not_available_files = []
        for root, dirs, files in os.walk("."):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            if "lazai" in content.lower() and "not available" in content.lower():
                                not_available_files.append(file_path)
                    except:
                        pass
        
        lazai_status["not_available_files"] = not_available_files
        
        # Determine status
        if not_available_files:
            lazai_status["status"] = "explicitly_disabled"
            lazai_status["recommendations"].append("Remove all LAZAI references - marked as not available")
        elif not lazai_status["files"]:
            lazai_status["status"] = "not_implemented"
            lazai_status["recommendations"].append("Remove all LAZAI references")
        else:
            lazai_status["status"] = "implemented"
        
        return lazai_status
    
    def generate_cleanup_script(self):
        """Generate script to clean up mock integrations"""
        cleanup_script = '''#!/usr/bin/env python3
"""
Integration Cleanup Script
Removes mock LAZAI/ALITH integrations and marks as NOT IMPLEMENTED
"""

import os
import re
import shutil

def remove_mock_integrations():
    """Remove mock integration files and references"""
    
    # Files to remove
    files_to_remove = [
        "services/alith/agent.py",  # Missing file
        "services/lazai/",  # Entire directory if exists
    ]
    
    # Remove files
    for file_path in files_to_remove:
        if os.path.exists(file_path):
            if os.path.isdir(file_path):
                shutil.rmtree(file_path)
                print(f"Removed directory: {file_path}")
            else:
                os.remove(file_path)
                print(f"Removed file: {file_path}")
    
    print("Cleanup completed")

if __name__ == "__main__":
    remove_mock_integrations()
'''
        
        with open("scripts/cleanup_mock_integrations.py", "w", encoding="utf-8") as f:
            f.write(cleanup_script)
        
        print("Generated cleanup script: scripts/cleanup_mock_integrations.py")
    
    def run_audit(self):
        """Run complete integration audit"""
        print("Starting Integration SDK Audit...")
        
        # Audit each integration
        self.results["integrations"]["alith"] = self.audit_alith_integration()
        self.results["integrations"]["lazai"] = self.audit_lazai_integration()
        
        # Generate recommendations
        self.generate_recommendations()
        
        # Generate report
        self.generate_report()
        
        # Generate cleanup script
        self.generate_cleanup_script()
        
        return self.results
    
    def generate_recommendations(self):
        """Generate cleanup recommendations"""
        recommendations = []
        
        # ALITH recommendations
        alith = self.results["integrations"]["alith"]
        if alith["status"] == "not_implemented":
            recommendations.append("Remove all ALITH SDK references from codebase")
            recommendations.append("Update documentation to reflect ALITH is not implemented")
        
        # LAZAI recommendations
        lazai = self.results["integrations"]["lazai"]
        if lazai["status"] == "explicitly_disabled":
            recommendations.append("Remove all LAZAI SDK references from codebase")
            recommendations.append("Update documentation to reflect LAZAI is not available")
        
        self.results["recommendations"] = recommendations
    
    def generate_report(self):
        """Generate audit report"""
        report_content = f"""# Integration SDK Audit Report

<!-- VERSION_PLACEHOLDER -->
**Version**: 1.4.5
**Last Updated**: {datetime.now().strftime('%Y-%m-%d')}
**Commit**: unknown
<!-- /VERSION_PLACEHOLDER -->

## Summary

This audit examines the status of LAZAI and ALITH SDK integrations in the HyperKit Agent codebase.

## Integration Status

### ALITH SDK
- **Status**: {self.results['integrations']['alith']['status'].upper()}
- **Files**: {', '.join(self.results['integrations']['alith']['files']) if self.results['integrations']['alith']['files'] else 'None'}
- **Issues**: {len(self.results['integrations']['alith']['issues'])} issues found

### LAZAI SDK
- **Status**: {self.results['integrations']['lazai']['status'].upper()}
- **Files**: {', '.join(self.results['integrations']['lazai']['files']) if self.results['integrations']['lazai']['files'] else 'None'}
- **Issues**: {len(self.results['integrations']['lazai']['issues'])}

## Detailed Findings

### ALITH SDK Issues
"""
        
        for issue in self.results['integrations']['alith']['issues']:
            report_content += f"- {issue}\n"
        
        report_content += "\n### LAZAI SDK Issues\n"
        for issue in self.results['integrations']['lazai']['issues']:
            report_content += f"- {issue}\n"
        
        report_content += "\n## Recommendations\n"
        for rec in self.results['recommendations']:
            report_content += f"- {rec}\n"
        
        report_content += """
## Action Items

1. **Immediate Cleanup**
   - Remove mock integration files
   - Update documentation to reflect actual status
   - Remove references from code

2. **Documentation Updates**
   - Mark integrations as NOT IMPLEMENTED
   - Update API documentation
   - Remove from feature lists

3. **Code Cleanup**
   - Remove unused imports
   - Clean up error handling
   - Update configuration schemas

---
*This report is automatically generated by the Integration SDK Audit script.*
"""
        
        # Save MD report to integration category
        report_path = Path("REPORTS/integration/integration_sdk_audit_report.md")
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_content)
        
        # Save JSON results to JSON_DATA directory
        json_path = Path("REPORTS/JSON_DATA/integration_audit_results.json")
        json_path.parent.mkdir(parents=True, exist_ok=True)
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2)
        
        print("Generated Integration SDK Audit report")

def main():
    """Main function"""
    auditor = IntegrationSDKAuditor()
    results = auditor.run_audit()
    
    # Print summary
    print("\n" + "="*50)
    print("INTEGRATION SDK AUDIT SUMMARY")
    print("="*50)
    
    for name, integration in results["integrations"].items():
        print(f"{name.upper()}: {integration['status'].upper()}")
        print(f"  Files: {len(integration['files'])}")
        print(f"  Issues: {len(integration['issues'])}")
    
    print(f"\nRecommendations: {len(results['recommendations'])}")
    
    return 0

if __name__ == "__main__":
    exit(main())
