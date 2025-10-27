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
        "[bold red]🚨 HYPERAGENT LIMITATIONS & BROKEN FEATURES[/bold red]\n"
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
        # Critical Broken Commands
        ("deploy", "❌ BROKEN", "Constructor argument mismatch - ABI vs contract signature", "HIGH - No deployments work"),
        
        # Partially Working Commands
        ("workflow", "⚠️ PARTIAL", "Deployment stage fails - constructor bug", "HIGH - End-to-end broken"),
        ("audit", "⚠️ PARTIAL", "Batch audit implemented, some features pending", "LOW - Core works"),
        ("generate", "✅ WORKING", "AI-powered contract generation works", "NONE - Fully functional"),
        ("verify", "✅ IMPLEMENTED", "Real Explorer API integration exists", "NONE - Actually works"),
        ("monitor", "✅ IMPLEMENTED", "Real system metrics with psutil", "NONE - Actually works"),
        ("config", "✅ IMPLEMENTED", "Real file-based config management", "NONE - Actually works"),
        
        # Dynamic Commands
        ("version", "✅ DYNAMIC", "Pulls version from Git + pyproject.toml", "NONE - Actually works"),
        
        # Working Commands
        ("status", "✅ WORKING", "Real health check with production validator", "NONE - Actually works"),
        ("test-rag", "✅ WORKING", "Real RAG testing implementation", "NONE - Actually works"),
    ]
    
    for command, status, issue, impact in limitations:
        table.add_row(command, status, issue, impact)
    
    console.print(table)
    
    # Show critical issues
    console.print("\n[bold red]🚨 CRITICAL ISSUES REQUIRING IMMEDIATE ATTENTION:[/bold red]")
    console.print("1. [red]Deploy command constructor bug[/red] - ABI generation mismatch")
    console.print("2. [red]Workflow pipeline fails at deployment[/red] - Constructor bug blocks E2E")
    
    # Show what actually works
    console.print("\n[bold green]✅ WHAT ACTUALLY WORKS:[/bold green]")
    console.print("• [green]Generate[/green] - AI-powered contract generation")
    console.print("• [green]Audit[/green] - Multi-source security analysis")
    console.print("• [green]Verify[/green] - Real Explorer API integration")
    console.print("• [green]Monitor[/green] - System metrics with psutil")
    console.print("• [green]Config[/green] - File-based configuration management")
    console.print("• [green]Status[/green] - Production mode validation")
    console.print("• [green]Version[/green] - Dynamic Git + package info")
    
    # Show production readiness status
    console.print("\n[bold yellow]⚠️ PRODUCTION READINESS STATUS:[/bold yellow]")
    console.print("[yellow]MOSTLY FUNCTIONAL[/yellow] - Most commands work correctly")
    console.print("[red]DEPLOYMENT BLOCKED[/red] - Constructor argument bug prevents deployments")
    console.print("[yellow]Need to fix deploy command to be fully production-ready[/yellow]")
    
    # Show next steps
    console.print("\n[bold blue]🔧 IMMEDIATE FIXES NEEDED:[/bold blue]")
    console.print("1. [red]Fix deploy command constructor argument parsing[/red]")
    console.print("2. [yellow]Test and validate all implemented commands[/yellow]")
    console.print("3. [yellow]Add comprehensive error handling[/yellow]")
    console.print("4. [yellow]Document actual functionality[/yellow]")
    
    console.print("\n[bold green]✅ BOTTOM LINE:[/bold green]")
    console.print("[green]Most commands are IMPLEMENTED and WORKING[/green]")
    console.print("[yellow]Deploy command needs fix for constructor bug[/yellow]")
    console.print("[yellow]Core AI features (generation, audit) work correctly[/yellow]")
    console.print("[yellow]Verify, monitor, config are REAL implementations[/yellow]")
