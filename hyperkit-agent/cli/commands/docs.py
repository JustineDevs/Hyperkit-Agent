#!/usr/bin/env python3
"""
Documentation Access Command

Helps users access documentation from devlog branch.
"""

import subprocess
import sys
from pathlib import Path
import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

REPO_URL = "https://github.com/JustineDevs/Hyperkit-Agent"
DEVLOG_BRANCH = "devlog"

@click.group()
def docs_group():
    """Access HyperAgent documentation"""
    pass

@docs_group.command(name='open')
@click.argument('doc_path', required=False)
@click.option('--local', is_flag=True, help='Open local docs if available (devlog branch)')
@click.option('--browser', is_flag=True, help='Open in default browser')
def open_docs(doc_path, local, browser):
    """
    Open documentation in browser or local file
    
    Examples:
        hyperagent docs open                    # Open main docs page
        hyperagent docs open --local            # Check if devlog branch exists locally
        hyperagent docs open REPORTS/STATUS     # Open specific doc category
        hyperagent docs open --browser          # Open GitHub docs in browser
    """
    if not doc_path:
        # Show main documentation index
        console.print("\n[bold cyan]HyperAgent Documentation[/bold cyan]\n")
        
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Category", style="cyan")
        table.add_column("Description")
        table.add_column("Link")
        
        docs = [
            ("Quick Start", "Get started with HyperAgent", f"{REPO_URL}/blob/{DEVLOG_BRANCH}/hyperkit-agent/docs/GUIDE/QUICK_START.md"),
            ("Environment Setup", "Setup guide", f"{REPO_URL}/blob/{DEVLOG_BRANCH}/hyperkit-agent/docs/GUIDE/ENVIRONMENT_SETUP.md"),
            ("Implementation Status", "Current project status", f"{REPO_URL}/blob/{DEVLOG_BRANCH}/hyperkit-agent/REPORTS/HONEST_STATUS_ASSESSMENT.md"),
            ("Audit Reports", "Security audit reports", f"{REPO_URL}/blob/{DEVLOG_BRANCH}/hyperkit-agent/REPORTS/AUDIT/AUDIT.md"),
            ("Developer Guide", "Developer documentation", f"{REPO_URL}/blob/{DEVLOG_BRANCH}/hyperkit-agent/docs/TEAM/DEVELOPER_GUIDE.md"),
            ("Integration Docs", "Integration guides", f"{REPO_URL}/tree/{DEVLOG_BRANCH}/hyperkit-agent/docs/INTEGRATION"),
        ]
        
        for category, desc, link in docs:
            table.add_row(category, desc, link)
        
        console.print(table)
        console.print(f"\n[dim]View all docs:[/dim] {REPO_URL}/tree/{DEVLOG_BRANCH}")
        return
    
    # Check if local devlog branch exists
    if local:
        try:
            repo_root = Path(__file__).parent.parent.parent.parent
            result = subprocess.run(
                ['git', 'rev-parse', '--verify', '--quiet', 'refs/heads/devlog'],
                cwd=repo_root,
                capture_output=True
            )
            
            if result.returncode == 0:
                console.print("[green]✓[/green] devlog branch found locally")
                console.print(f"[dim]Switch to devlog:[/dim] git checkout devlog")
            else:
                console.print("[yellow]⚠[/yellow] devlog branch not found locally")
                console.print(f"[dim]Fetch devlog:[/dim] git fetch origin devlog:devlog")
        except Exception as e:
            console.print(f"[red]Error checking local branch:[/red] {e}")
    
    # Open in browser
    if browser:
        url = f"{REPO_URL}/blob/{DEVLOG_BRANCH}/{doc_path}" if doc_path else f"{REPO_URL}/tree/{DEVLOG_BRANCH}"
        console.print(f"[cyan]Opening:[/cyan] {url}")
        
        import webbrowser
        try:
            webbrowser.open(url)
            console.print("[green]✓[/green] Opened in browser")
        except Exception as e:
            console.print(f"[red]Error opening browser:[/red] {e}")
            console.print(f"[yellow]Manual link:[/yellow] {url}")

@docs_group.command(name='checkout')
def checkout_devlog():
    """Checkout devlog branch to access full documentation locally"""
    try:
        repo_root = Path(__file__).parent.parent.parent.parent
        
        # Check if devlog exists locally
        result = subprocess.run(
            ['git', 'rev-parse', '--verify', '--quiet', 'refs/heads/devlog'],
            cwd=repo_root,
            capture_output=True
        )
        
        if result.returncode != 0:
            # Fetch devlog branch
            console.print("[cyan]Fetching devlog branch from remote...[/cyan]")
            result = subprocess.run(
                ['git', 'fetch', 'origin', f'{DEVLOG_BRANCH}:{DEVLOG_BRANCH}'],
                cwd=repo_root,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                console.print(f"[red]Error fetching devlog:[/red] {result.stderr}")
                return
        
        # Checkout devlog
        console.print("[cyan]Checking out devlog branch...[/cyan]")
        result = subprocess.run(
            ['git', 'checkout', DEVLOG_BRANCH],
            cwd=repo_root,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            console.print("[green]✓[/green] Switched to devlog branch")
            console.print("[dim]Full documentation is now available locally[/dim]")
            console.print(f"[dim]Return to main:[/dim] git checkout main")
        else:
            console.print(f"[red]Error checking out devlog:[/red] {result.stderr}")
            
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")

@docs_group.command(name='info')
def docs_info():
    """Show documentation access information"""
    console.print("\n[bold cyan]Documentation Access Guide[/bold cyan]\n")
    
    info_panel = Panel(
        f"""
[bold]Branch Structure:[/bold]
  • main branch: Code + essential docs (~794 KB)
  • devlog branch: Full documentation (~1.9 MB)

[bold]Quick Access:[/bold]
  • View online: {REPO_URL}/tree/{DEVLOG_BRANCH}
  • Switch locally: git checkout devlog
  • Clone full: git clone -b {DEVLOG_BRANCH} <repo-url>

[bold]Essential Docs (in main):[/bold]
  • README.md
  • QUICK_START.md
  • ENVIRONMENT_SETUP.md

[bold]Full Docs (in devlog):[/bold]
  • All REPORTS/ directories
  • All docs/ subdirectories
  • Team guides and integration docs
        """,
        title="📚 Documentation",
        border_style="cyan"
    )
    
    console.print(info_panel)

