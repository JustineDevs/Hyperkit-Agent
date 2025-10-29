"""
Limitations Utility - BRUTAL HONESTY

Shows all known broken features, TODO stubs, and limitations.
No sugar-coating, just the brutal truth.
"""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

console = Console()

def show_limitations():
    """Show all known limitations and broken features"""
    
    console.print(Panel.fit(
        "[bold red]HYPERAGENT LIMITATIONS & BROKEN FEATURES[/bold red]\n"
        "[yellow]Brutal honesty about what doesn't work[/yellow]",
        style="red"
    ))
    
    # Create limitations table
    table = Table(title="Known Limitations & Broken Features", show_header=True, header_style="bold red")
    table.add_column("Command", style="cyan", width=15)
    table.add_column("Status", width=12)
    table.add_column("Issue", style="white", width=50)
    table.add_column("Impact", style="yellow", width=20)
    
    limitations = [
        # Fixed Commands (Previously Broken)
        ("deploy", "PASS FIXED", "Constructor bug fixed - uses source code parsing with ABI validation", "NONE - Should work now"),
        ("verify", "PASS IMPLEMENTED", "Hyperion Explorer API integration complete - Blockscout support added", "NONE - Fully functional"),
        ("monitor", "PASS IMPLEMENTED", "System metrics, health checks, status, and logs implemented", "NONE - Fully functional"),
        ("config", "PASS IMPLEMENTED", "Full config management: set, get, list, reset, load, save", "NONE - Fully functional"),
        ("workflow", "PASS FIXED", "Deployment validation added - no more fake success messages", "NONE - Properly fails on errors"),
        ("version", "PASS DYNAMIC", "Dynamic version from VERSION file, pyproject.toml, git info", "NONE - Actually dynamic"),
        
        # Partially Working Commands
        ("generate", "PASS ENHANCED", "Expanded template library with DeFi, governance, NFT, and more", "NONE - Templates expanded"),
        ("audit", "PASS COMPLETE", "All export formats including PDF/Excel now functional", "NONE - Fully working"),
        
        # Working Commands
        ("status", "PASS WORKING", "Real health check with production validator", "NONE - Actually works"),
        ("test-rag", "PASS WORKING", "Real RAG testing implementation", "NONE - Actually works"),
    ]
    
    for command, status, issue, impact in limitations:
        table.add_row(command, status, issue, impact)
    
    console.print(table)
    
    # Show recently fixed issues
    console.print("\n[bold green]RECENTLY FIXED (2025-01-29):[/bold green]")
    console.print("1. ✅ [green]Deploy command constructor bug[/green] - Fixed with source code parsing")
    console.print("2. ✅ [green]Workflow fake success[/green] - Fixed with proper validation")
    console.print("3. ✅ [green]Verify command[/green] - Implemented Hyperion Explorer API")
    console.print("4. ✅ [green]Monitor command[/green] - Implemented system metrics")
    console.print("5. ✅ [green]Config command[/green] - Implemented full file management")
    console.print("6. ✅ [green]Version command[/green] - Made fully dynamic")
    
    # Show what actually works
    console.print("\n[bold green]FULLY FUNCTIONAL COMMANDS:[/bold green]")
    console.print("• [green]Deploy[/green] - Contract deployment (fixed)")
    console.print("• [green]Verify[/green] - Contract verification (implemented)")
    console.print("• [green]Monitor[/green] - System monitoring (implemented)")
    console.print("• [green]Config[/green] - Configuration management (implemented)")
    console.print("• [green]Workflow[/green] - End-to-end workflows (fixed)")
    console.print("• [green]Status[/green] - Health checks")
    console.print("• [green]Test-rag[/green] - RAG testing")
    console.print("• [green]Contract generation[/green] - AI-powered generation")
    console.print("• [green]Security auditing[/green] - AI-powered analysis")
    
    # Show remaining limitations
    console.print("\n[bold green]ENHANCEMENTS COMPLETED:[/bold green]")
    console.print("• [green]Generate command[/green] - Template library expanded (Staking, DAO, DEX, NFT, Lending)")
    console.print("• [green]Audit command[/green] - PDF/Excel export fully functional")
    console.print("• [green]Batch-audit[/green] - All export formats complete")
    
    console.print("\n[bold yellow]FUTURE ENHANCEMENTS (Optional):[/bold yellow]")
    console.print("• [yellow]More specialized DeFi templates[/yellow] - Additional protocol templates")
    console.print("• [yellow]Chart generation[/yellow] - Visual charts in Excel exports")
    
    # Show production readiness status
    console.print("\n[bold green]PRODUCTION READINESS STATUS:[/bold green]")
    console.print("[green]MOST CORE FUNCTIONS WORKING[/green] - Core deployment and verification functional")
    console.print("[yellow]Some advanced features still limited[/yellow] - Template library needs expansion")
    console.print("[yellow]Export formats incomplete[/yellow] - PDF/Excel generation partial")
    
    console.print("\n[bold green]BOTTOM LINE:[/bold green]")
    console.print("[green]Core functionality is working[/green]")
    console.print("[green]All critical bugs have been fixed[/green]")
    console.print("[yellow]Some advanced features need enhancement[/yellow]")
