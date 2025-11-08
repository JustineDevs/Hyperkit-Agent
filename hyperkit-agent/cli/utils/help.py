"""
Enhanced Help System
Rich-formatted help with command grouping, aligned options, and smart suggestions
"""

from typing import List, Optional, Dict, Any
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
import click

console = Console()


def format_options_table(command: click.Command) -> Table:
    """
    Format command options as an aligned table.
    
    Args:
        command: Click command object
    
    Returns:
        Rich Table with aligned options
    """
    table = Table(show_header=True, header_style="bold cyan", box=None)
    table.add_column("Option", style="cyan", width=20)
    table.add_column("Description", style="white")
    
    # Get all options from command
    for param in command.params:
        if isinstance(param, click.Option):
            # Format option flags
            opts = ', '.join(sorted(param.opts, key=lambda x: len(x)))
            if param.help:
                table.add_row(opts, param.help)
            else:
                table.add_row(opts, "")
    
    return table


def format_command_help(command: click.Command, ctx: click.Context) -> None:
    """
    Format and display Rich-formatted help for a command.
    
    Args:
        command: Click command object
        ctx: Click context
    """
    # Command name and description
    if command.help:
        console.print(Panel.fit(
            command.help,
            title=f"[bold cyan]{command.name}[/bold cyan]",
            border_style="cyan"
        ))
    else:
        console.print(f"[bold cyan]{command.name}[/bold cyan]")
    
    # Options table
    if command.params:
        options_table = format_options_table(command)
        console.print("\n[bold]Options:[/bold]")
        console.print(options_table)
    
    # Usage examples (if available)
    # This could be extended to read from command metadata
    console.print("\n[bold yellow]Usage:[/bold yellow]")
    console.print(f"  [cyan]hyperagent {command.name}[/cyan] [dim]<options>[/dim]")


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
        matches = get_close_matches(
            unknown_command.lower(),
            [cmd.lower() for cmd in available_commands],
            n=1,
            cutoff=0.6
        )
        if matches:
            # Find original case version
            for cmd in available_commands:
                if cmd.lower() == matches[0]:
                    return cmd
    except ImportError:
        pass
    
    return None


def show_command_suggestion(unknown_command: str, available_commands: List[str]) -> None:
    """
    Display command suggestion when unknown command is entered.
    
    Args:
        unknown_command: The command that was not found
        available_commands: List of available command names
    """
    suggestion = suggest_command(unknown_command, available_commands)
    
    if suggestion:
        console.print(f"\n[bold red]Unknown command:[/bold red] [yellow]{unknown_command}[/yellow]")
        console.print(f"[bold green]Did you mean:[/bold green] [cyan]hyperagent {suggestion}[/cyan]")
    else:
        console.print(f"\n[bold red]Unknown command:[/bold red] [yellow]{unknown_command}[/yellow]")
        console.print("[yellow]Run 'hyperagent' to see available commands[/yellow]")


class RichHelpFormatter(click.HelpFormatter):
    """
    Custom Click help formatter using Rich for beautiful output.
    """
    
    def write_usage(self, prog: str, args: str = "", prefix: Optional[str] = None) -> None:
        """Write usage line with Rich formatting."""
        if prefix is None:
            prefix = "Usage:"
        
        console.print(f"\n[bold cyan]{prefix}[/bold cyan] [cyan]{prog}[/cyan] [dim]{args}[/dim]")
    
    def write_heading(self, heading: str) -> None:
        """Write section heading with Rich formatting."""
        console.print(f"\n[bold yellow]{heading}:[/bold yellow]")
    
    def write_dl(self, rows: List[tuple], col_max: int = 30, col_spacing: int = 2) -> None:
        """Write definition list as Rich table."""
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Term", style="cyan", width=col_max)
        table.add_column("Definition", style="white")
        
        for term, definition in rows:
            table.add_row(term, definition)
        
        console.print(table)
    
    def write_text(self, text: str) -> None:
        """Write text with Rich formatting."""
        console.print(text)
    
    def write_paragraph(self) -> None:
        """Write paragraph spacing."""
        console.print()  # Empty line

