"""
Enhanced CLI Menu System
Beautiful, friendly, semi-GUI CLI experience with grouped commands and interactive menu
"""

import datetime
from typing import Dict, List, Tuple, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.align import Align

console = Console()

# Global menu execution flag - must be accessible from main CLI
_menu_execution_in_progress = False

# Command grouping configuration
COMMAND_GROUPS = {
    "Deployment & Projects": [
        ("deploy", "Deploy contracts to blockchain"),
        ("verify", "Verify contracts on blockchain explorer"),
        ("config", "Manage configuration settings and AI/LLM"),
        ("monitor", "Monitor system health and performance"),
        ("workflow", "Run end-to-end smart contract workflows (with autonomous loop)"),
    ],
    "AI & Audit Automation": [
        ("audit", "Audit smart contracts for vulnerabilities"),
        ("batch-audit", "Batch audit multiple contracts"),
        ("generate", "Generate smart contracts and templates"),
        ("context", "Advanced debug output & troubleshooting"),
    ],
    "Status & Docs": [
        ("status", "Show CLI and system status"),
        ("doctor", "Run environment preflight checks"),
        ("docs", "Access documentation"),
        ("limitations", "Show broken features and limitations"),
        ("test-rag", "Test IPFS Pinata RAG connections"),
        ("version", "Show version information"),
    ]
}


def get_time_based_greeting() -> str:
    """
    Get time-based greeting message.
    
    Returns:
        Greeting string based on time of day
    """
    hour = datetime.datetime.now().hour
    
    if 5 <= hour < 12:
        return "Good morning, Operator. The network is listening."
    elif 12 <= hour < 17:
        return "Good afternoon, Operator. AI agent standing by."
    elif 17 <= hour < 21:
        return "Good evening, Operator. Ready for deployment."
    else:
        return "Good night, Operator. System monitoring active."


def get_command_groups() -> Dict[str, List[Tuple[str, str]]]:
    """
    Get commands grouped by category.
    
    Returns:
        Dictionary mapping group names to list of (command, description) tuples
    """
    return COMMAND_GROUPS


def get_all_commands() -> List[str]:
    """
    Get list of all available command names.
    
    Returns:
        List of command names
    """
    commands = []
    groups = get_command_groups()
    for group_commands in groups.values():
        for command, _ in group_commands:
            commands.append(command)
    return commands


def print_command_menu(show_groups: bool = True) -> None:
    """
    Display grouped command table with Rich formatting.
    
    Args:
        show_groups: Whether to show group headers
    """
    console.print("\n[bold cyan]Available Commands:[/bold cyan]\n")
    
    groups = get_command_groups()
    
    for group_name, commands in groups.items():
        # Print group header
        if show_groups:
            console.print(f"[bold green]▶ {group_name}[/bold green]")
            console.print()
        
        # Create table for this group
        table = Table(
            show_header=True,
            header_style="bold blue",
            box=None,
            padding=(0, 2)
        )
        table.add_column("Command", style="cyan", no_wrap=True, width=18)
        table.add_column("Description", style="white")
        
        for command, description in commands:
            table.add_row(command, description)
        
        console.print(table)
        console.print()  # Spacing between groups


def print_usage_examples() -> None:
    """
    Display usage examples at the bottom of help.
    """
    examples = [
        ("Deploy a contract", "hyperagent deploy MyToken.sol"),
        ("Run an audit", "hyperagent audit contract.sol"),
        ("Generate contract", "hyperagent generate contract ERC20 --name MyToken"),
        ("Check system status", "hyperagent status"),
        ("Run workflow", "hyperagent workflow run \"create ERC20 token\""),
    ]
    
    console.print("\n[bold yellow]Examples:[/bold yellow]")
    for label, command in examples:
        console.print(f"  [dim]# {label}[/dim]")
        console.print(f"  [cyan]$ {command}[/cyan]")


def print_keyboard_shortcuts() -> None:
    """
    Display keyboard shortcuts information.
    """
    shortcuts = [
        ("↑/↓", "Navigate command history"),
        ("Tab", "Complete command name"),
        ("Ctrl+C", "Cancel current operation"),
        ("--help", "Show command-specific help"),
    ]
    
    console.print("\n[bold yellow]Keyboard Shortcuts:[/bold yellow]")
    for key, description in shortcuts:
        console.print(f"  [cyan]{key:12}[/cyan] [white]{description}[/white]")


def suggest_command(unknown_command: str, available_commands: List[str]) -> Optional[str]:
    """
    Suggest a command using fuzzy matching.
    
    Args:
        unknown_command: The command that was not found
        available_commands: List of available command names
    
    Returns:
        Suggested command name or None if no good match
    """
    try:
        from difflib import get_close_matches
        matches = get_close_matches(unknown_command.lower(), 
                                   [cmd.lower() for cmd in available_commands], 
                                   n=1, cutoff=0.6)
        if matches:
            # Find original case version
            for cmd in available_commands:
                if cmd.lower() == matches[0]:
                    return cmd
    except ImportError:
        pass
    
    return None


def show_interactive_menu() -> Optional[str]:
    """
    Show interactive menu for command selection.
    
    Returns:
        Selected command name or None if cancelled
    """
    try:
        import questionary
    except ImportError:
        # Fallback to non-interactive if questionary not available
        console.print("[dim]Install 'questionary' for interactive menu: pip install questionary[/dim]")
        return None
    
    # Build choices from command groups
    choices = []
    groups = get_command_groups()
    
    for group_name, commands in groups.items():
        # Add separator for each group
        if choices:  # Don't add separator before first group
            choices.append(questionary.Separator(f"─── {group_name} ───"))
        
        for command, description in commands:
            choices.append(
                questionary.Choice(
                    title=f"{command:16} {description}",
                    value=command
                )
            )
    
    choices.append(questionary.Separator())
    choices.append(questionary.Choice(title="Show command list (non-interactive)", value="list"))
    choices.append(questionary.Choice(title="Quit", value="quit"))
    
    # Check if we're in an interactive terminal
    import sys
    is_interactive = sys.stdin.isatty() and sys.stdout.isatty()
    
    if not is_interactive:
        # Non-interactive mode: show command list
        console.print("\n[cyan]Available Commands:[/cyan]\n")
        for group_name, commands in groups.items():
            console.print(f"[bold cyan]{group_name}:[/bold cyan]")
            for command, description in commands:
                console.print(f"  [green]{command:16}[/green] {description}")
            console.print()
        console.print("[yellow]Note: Interactive menu requires a TTY. Use commands directly:[/yellow]")
        console.print("[dim]  Example: hyperagent workflow run \"your prompt here\"[/dim]\n")
        return "list"
    
    try:
        selected = questionary.select(
            "What do you want to do?",
            choices=choices,
            style=questionary.Style([
                ('qmark', 'fg:#673ab7 bold'),       # token in front of the question
                ('question', 'bold'),               # question text
                ('answer', 'fg:#f44336 bold'),      # submitted answer text behind the question
                ('pointer', 'fg:#673ab7 bold'),     # pointer used in select and checkbox prompts
                ('highlighted', 'fg:#673ab7 bold'), # pointed-at choice in select and checkbox prompts
                ('selected', 'fg:#cc5454'),        # style for a selected item of a checkbox
                ('separator', 'fg:#cc5444'),       # separator in lists
                ('instruction', ''),                # user instructions for select, rawselect, checkbox
                ('text', ''),                       # plain text
                ('disabled', 'fg:#858585 italic')   # disabled choices for select and checkbox prompts
            ])
        ).ask()
        
        if selected == "quit":
            return None
        
        if selected == "list":
            # Show non-interactive menu
            return "list"
        
        return selected
    except (KeyboardInterrupt, EOFError):
        return None
    except Exception as e:
        # Fallback for any other errors (e.g., NoConsoleScreenBufferError on Windows)
        console.print(f"\n[yellow]Interactive menu unavailable (non-TTY environment)[/yellow]")
        console.print(f"[dim]Error: {type(e).__name__}[/dim]")
        console.print("[cyan]Available Commands:[/cyan]\n")
        
        # Show all commands grouped
        groups = get_command_groups()
        for group_name, commands in groups.items():
            console.print(f"[bold cyan]{group_name}:[/bold cyan]")
            for command, description in commands:
                console.print(f"  [green]{command:16}[/green] {description}")
            console.print()
        
        console.print("[yellow]Use commands directly:[/yellow]")
        console.print("[dim]  Example: hyperagent workflow run \"your prompt here\"[/dim]\n")
        return "list"


def show_interactive_menu_and_execute() -> Optional[str]:
    """
    Show interactive menu and execute selected command with parameter collection.
    Handles command groups recursively.
    
    Returns:
        None if cancelled, command name if executed
    """
    global _menu_execution_in_progress
    
    # Prevent recursive menu calls
    if _menu_execution_in_progress:
        console.print("[yellow]Menu already in progress, skipping recursive call[/yellow]")
        return None
    
    _menu_execution_in_progress = True
    
    try:
        from cli.utils.interactive import (
            collect_command_params_interactively,
            execute_with_progress_indicator
        )
        import click
        
        # Show menu
        selected_command = show_interactive_menu()
        
        if not selected_command or selected_command in ["list", "quit"]:
            return selected_command
        
        # Get the command object from the main CLI
        # Import the main CLI group
        from cli.main import cli as main_cli
        
        # Create a context for the main CLI
        ctx = click.Context(main_cli)
        ctx.ensure_object(dict)
        
        # Get the command
        cmd = main_cli.get_command(ctx, selected_command)
        
        if not cmd:
            console.print(f"[red]Command '{selected_command}' not found[/red]")
            return None
        
        # Handle command groups recursively
        if isinstance(cmd, click.Group):
            # Show subcommands interactively
            subcommands = []
            for subcmd_name in cmd.list_commands(ctx):
                subcmd = cmd.get_command(ctx, subcmd_name)
                if subcmd:
                    desc = subcmd.get_short_help_str() or 'No description'
                    subcommands.append((subcmd_name, desc))
            
            if not subcommands:
                console.print(f"[yellow]No subcommands available for '{selected_command}'[/yellow]")
                return None
            
            # Show interactive subcommand selection
            try:
                import questionary
                choices = [
                    questionary.Choice(
                        title=f"{name:20} {desc}",
                        value=name
                    )
                    for name, desc in subcommands
                ]
                choices.append(questionary.Separator())
                choices.append(questionary.Choice(title="← Back to main menu", value="__back__"))
                
                selected_subcmd = questionary.select(
                    f"Select {selected_command} subcommand",
                    choices=choices
                ).ask()
                
                if selected_subcmd == "__back__":
                    # Go back to main menu (reset flag first to allow new menu)
                    _menu_execution_in_progress = False
                    # CRITICAL: Check recursion guard before recursive call
                    # Small delay to ensure flag is reset
                    import time
                    time.sleep(0.1)
                    # Only recurse if flag is still False (not set by another thread)
                    if not _menu_execution_in_progress:
                        return show_interactive_menu_and_execute()
                    else:
                        # Flag was set by another thread - don't recurse
                        console.print("[yellow]Menu execution in progress, cannot go back[/yellow]")
                        return None
                
                # Get the subcommand and collect parameters
                subcmd = cmd.get_command(ctx, selected_subcmd)
                if not subcmd:
                    console.print(f"[red]Subcommand '{selected_subcmd}' not found[/red]")
                    return None
                
                # Collect parameters for subcommand
                console.print(f"\n[bold cyan]Configuring {selected_command} {selected_subcmd}...[/bold cyan]\n")
                
                # Create proper nested context for subcommand (parent group context)
                parent_ctx = click.Context(cmd, parent=ctx)
                parent_ctx.ensure_object(dict)
                parent_ctx.obj.update(ctx.obj)
                
                params = collect_command_params_interactively(subcmd, parent_ctx)
                
                # Execute with progress wrapper using parent context
                full_command_name = f"{selected_command} {selected_subcmd}"
                success = execute_with_progress_indicator(subcmd, params, parent_ctx, full_command_name)
                return full_command_name if success else None
                
            except ImportError:
                # Fallback without questionary
                console.print(f"\n[bold]Available {selected_command} subcommands:[/bold]")
                for i, (name, desc) in enumerate(subcommands, 1):
                    console.print(f"  {i}. {name}: {desc}")
                console.print(f"\n[yellow]Install 'questionary' for interactive subcommand selection[/yellow]")
                return None
        
        # Regular command - collect parameters
        console.print(f"\n[bold cyan]Configuring {selected_command}...[/bold cyan]\n")
        params = collect_command_params_interactively(cmd, ctx)
        
        # Execute with progress wrapper
        success = execute_with_progress_indicator(cmd, params, ctx, selected_command)
        return selected_command if success else None
        
    except click.ClickException as e:
        # CRITICAL: ClickException means invalid input - don't retry, just show error and return
        try:
            console.print(f"[red]Error: {e}[/red]")
        except (ValueError, OSError):
            pass
        # Debug logging if enabled
        import os
        if os.environ.get('HYPERAGENT_DEBUG_RECURSION', 'false').lower() == 'true':
            import logging
            logger = logging.getLogger('hyperkit.cli.recursion')
            logger.warning(f"[RECURSION_DEBUG] ClickException in menu: {str(e)}, stopping execution")
        return None  # Stop - don't retry
    except Exception as e:
        # Handle console closure gracefully
        try:
            console.print(f"[red]Error: {e}[/red]")
        except (ValueError, OSError):
            # Console/file already closed - can't print, but that's okay
            pass
        import traceback
        # Check if debug mode is enabled
        try:
            ctx_obj = ctx.obj if 'ctx' in locals() else {}
            if ctx_obj.get('debug', False):
                traceback.print_exc()
        except:
            pass
        return None
    finally:
        # Always reset the flag, even on exception
        _menu_execution_in_progress = False


def print_welcome_panel() -> None:
    """
    Print welcome panel with time-based greeting.
    """
    greeting = get_time_based_greeting()
    
    welcome_text = f"[bold cyan]{greeting}[/bold cyan]\n\n"
    welcome_text += "[dim]HyperAgent - AI-Powered Smart Contract Development Platform[/dim]"
    
    console.print(
        Panel.fit(
            welcome_text,
            title="[bold green]Welcome[/bold green]",
            border_style="green"
        )
    )


def print_status_panel() -> None:
    """
    Print status panel showing development mode warning.
    """
    status_text = (
        "[bold yellow]STATUS WARNING:[/bold yellow] Development Mode – NOT Production Ready\n"
        "Many CLI commands are partial or broken. Run '[bold]hyperagent limitations[/bold]' for details."
    )
    
    console.print(
        Panel.fit(
            status_text,
            title="[bold red]System Status[/bold red]",
            border_style="red"
        )
    )


def print_production_mode_panel() -> None:
    """
    Print panel explaining Production Mode vs Safe Mode.
    """
    mode_text = (
        "[bold white]PRODUCTION MODE vs SAFE MODE[/bold white]\n\n"
        "[green]PRODUCTION MODE:[/green] All dependencies available, full functionality.\n"
        "[yellow]SAFE MODE:[/yellow] Missing dependencies, operations blocked."
    )
    
    console.print(
        Panel.fit(
            mode_text,
            title="[bold blue]Mode Information[/bold blue]",
            border_style="blue"
        )
    )


def print_llm_config_panel() -> None:
    """
    Print panel showing AI/LLM configuration.
    """
    config_text = (
        "[bold]AI/LLM Configuration[/bold]\n\n"
        "[cyan][*] PRIMARY: Gemini (via Alith SDK)[/cyan] | Model: gemini-2.0-pro\n"
        "[magenta][>] SECONDARY: OpenAI (via Alith SDK)[/magenta] | Used if Gemini unavailable"
    )
    
    console.print(
        Panel.fit(
            config_text,
            title="[bold green]AI Configuration[/bold green]",
            border_style="green"
        )
    )


def print_tip_footer() -> None:
    """
    Print helpful tip footer.
    """
    tip_text = (
        "[yellow bold]Tip:[/yellow bold] "
        "Run '[bold green]hyperagent help <command>[/bold green]' for details and examples.\n"
        "[yellow bold]Keyboard Shortcuts:[/yellow bold] "
        "[cyan]↑↓[/cyan] [white]Navigate[/white], "
        "[cyan]Tab[/cyan] [white]complete[/white], "
        "[cyan]Ctrl+C[/cyan] [white]cancel[/white]"
    )
    
    console.print(f"\n{tip_text}")

