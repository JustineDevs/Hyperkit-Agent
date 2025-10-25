"""
Version Utilities
Version information for HyperKit Agent
"""

from rich.console import Console
from rich.panel import Panel

console = Console()

def show_version():
    """Display version information"""
    version_info = {
        "HyperKit Agent": "1.0.0",
        "Python": "3.8+",
        "Web3": "6.0+",
        "Status": "Production Ready",
        "Build": "2025-10-25"
    }
    
    console.print("🚀 HyperKit Agent Version Information")
    console.print("=" * 50)
    
    for key, value in version_info.items():
        console.print(f"{key}: {value}")
    
    console.print("\n📋 Features:")
    console.print("  • Smart Contract Generation")
    console.print("  • Security Auditing")
    console.print("  • Contract Deployment")
    console.print("  • Verification System")
    console.print("  • IPFS Storage")
    console.print("  • Real-time Monitoring")
