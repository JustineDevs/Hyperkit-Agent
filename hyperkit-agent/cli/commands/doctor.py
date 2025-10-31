"""
Doctor Command Module
Production-grade preflight and self-healing system
"""

import click
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

console = Console()

@click.command()
@click.option('--no-fix', is_flag=True, help='Disable automatic fixes (report only)')
@click.option('--workspace', type=str, help='Workspace directory path')
def doctor_command(no_fix, workspace):
    """
    🔬 HyperKit-Agent Doctor: Environment Preflight & Self-Healing
    
    Runs comprehensive preflight checks with hardened validation:
    
    \b
    Checks:
      ✅ Required tools (forge, python, node, npm)
      ✅ OpenZeppelin installation & version compatibility
      ✅ Foundry configuration (solc version)
      ✅ Git submodule issues (.gitmodules, .gitignore)
    
    \b
    Auto-Fixes:
      🔧 Installs missing OpenZeppelin contracts
      🔧 Fixes version mismatches in foundry.toml
      🔧 Cleans broken git submodule entries
      🔧 Removes submodule entries from wrong locations (.gitignore)
    
    \b
    Examples:
      # Run with auto-fix (default)
      hyperagent doctor
      
      # Report only (no fixes)
      hyperagent doctor --no-fix
      
      # Custom workspace
      hyperagent doctor --workspace /path/to/hyperkit-agent
    """
    try:
        from scripts.doctor import doctor as run_doctor
        
        workspace_path = Path(workspace) if workspace else None
        auto_fix = not no_fix
        
        console.print(Panel.fit(
            "🔬 HyperKit-Agent Doctor\n"
            "Environment Preflight & Self-Healing System",
            style="bold blue"
        ))
        
        success = run_doctor(workspace_dir=workspace_path, auto_fix=auto_fix)
        
        if success:
            console.print("\n✅ [bold green]All preflight checks passed![/bold green]")
            console.print("💡 System is ready for workflow execution.")
        else:
            console.print("\n❌ [bold red]Some preflight checks failed.[/bold red]")
            console.print("💡 Review errors above and fix manually, or run without --no-fix for auto-repair.")
            raise click.Abort()
            
    except ImportError:
        console.print("[bold red]❌ Doctor script not found[/bold red]")
        console.print("💡 Ensure scripts/doctor.py exists")
        raise click.Abort()
    except Exception as e:
        console.print(f"[bold red]❌ Doctor error: {e}[/bold red]")
        raise click.Abort()

