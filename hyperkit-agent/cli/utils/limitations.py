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
        # Critical Broken Commands
        ("deploy", "FAIL BROKEN", "Constructor argument mismatch - ABI vs contract signature", "HIGH - No deployments work"),
        ("verify", "FAIL STUB", "All TODO comments - no real implementation", "HIGH - No verification"),
        ("monitor", "FAIL STUB", "All TODO comments - no real implementation", "MEDIUM - No monitoring"),
        ("config", "FAIL STUB", "All TODO comments - no real implementation", "MEDIUM - No config management"),
        
        # Partially Working Commands
        ("workflow", "WARN PARTIAL", "Deployment stage fails - constructor bug", "HIGH - End-to-end broken"),
        ("generate", "WARN PARTIAL", "Templates are hardcoded stubs", "MEDIUM - Limited templates"),
        ("audit", "WARN PARTIAL", "Batch audit and report viewing not implemented", "LOW - Core works"),
        
        # Fake Commands
        ("version", "FAIL FAKE", "Hardcoded static data, not dynamic", "LOW - Misleading info"),
        
        # Working Commands
        ("status", "PASS WORKING", "Real health check with production validator", "NONE - Actually works"),
        ("test-rag", "PASS WORKING", "Real RAG testing implementation", "NONE - Actually works"),
    ]
    
    for command, status, issue, impact in limitations:
        table.add_row(command, status, issue, impact)
    
    console.print(table)
    
    # Show critical issues
    console.print("\n[bold red]CRITICAL ISSUES REQUIRING IMMEDIATE ATTENTION:[/bold red]")
    console.print("1. [red]Deploy command constructor bug[/red] - ABI generation mismatch")
    console.print("2. [red]Workflow pipeline fails silently[/red] - Shows fake success")
    console.print("3. [red]Verify command completely broken[/red] - All TODO stubs")
    console.print("4. [red]Monitor command completely broken[/red] - All TODO stubs")
    console.print("5. [red]Config command completely broken[/red] - All TODO stubs")
    
    # Show what actually works
    console.print("\n[bold green]WHAT ACTUALLY WORKS:[/bold green]")
    console.print("• [green]Status command[/green] - Real health check")
    console.print("• [green]Test-rag command[/green] - RAG testing")
    console.print("• [green]Contract generation[/green] - AI-powered generation")
    console.print("• [green]Security auditing[/green] - AI-powered analysis")
    
    # Show production readiness status
    console.print("\n[bold yellow]WARN PRODUCTION READINESS STATUS:[/bold yellow]")
    console.print("[red]NOT PRODUCTION READY[/red] - This is a demo/prototype")
    console.print("[yellow]Most commands are stubs or broken[/yellow]")
    console.print("[yellow]Deployment pipeline is broken[/yellow]")
    console.print("[yellow]No real verification system[/yellow]")
    
    # Show next steps
    console.print("\n[bold blue]IMMEDIATE FIXES NEEDED:[/bold blue]")
    console.print("1. Fix deploy command constructor argument parsing")
    console.print("2. Implement real verify command with Hyperion Explorer")
    console.print("3. Implement real monitor command with system metrics")
    console.print("4. Implement real config command with file management")
    console.print("5. Make version command dynamic")
    console.print("6. Remove all fake success messages")
    
    console.print("\n[bold red]BOTTOM LINE:[/bold red]")
    console.print("[red]This is NOT a production system.[/red]")
    console.print("[red]It's a demo/prototype with mostly broken infrastructure.[/red]")
    console.print("[red]Only core AI features (generation, audit) actually work.[/red]")
