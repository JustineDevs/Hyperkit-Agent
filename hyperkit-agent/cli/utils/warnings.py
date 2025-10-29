"""
CLI Command Status Warnings

Shows transparent status badges for each CLI command.
"""

from rich.console import Console
from rich.panel import Panel

console = Console()

# Command status mapping
COMMAND_STATUS = {
    'generate': {
        'status': 'WORKING',
        'emoji': '✅',
        'color': 'green',
        'message': 'Expanded template library with DeFi, governance, NFT, and more templates'
    },
    'deploy': {
        'status': 'WORKING',
        'emoji': '✅',
        'color': 'green',
        'message': 'Constructor bug fixed - uses source code parsing'
    },
    'audit': {
        'status': 'WORKING',
        'emoji': '✅',
        'color': 'green',
        'message': 'All export formats including PDF/Excel fully functional'
    },
    'batch-audit': {
        'status': 'WORKING',
        'emoji': '✅',
        'color': 'green',
        'message': 'All export formats (JSON, Markdown, HTML, CSV, PDF, Excel) complete'
    },
    'verify': {
        'status': 'WORKING',
        'emoji': '✅',
        'color': 'green',
        'message': 'Hyperion Explorer API integration complete'
    },
    'monitor': {
        'status': 'WORKING',
        'emoji': '✅',
        'color': 'green',
        'message': 'System metrics, health checks, and logs fully functional'
    },
    'config': {
        'status': 'WORKING',
        'emoji': '✅',
        'color': 'green',
        'message': 'Full configuration management: set, get, list, reset, load, save'
    },
    'workflow': {
        'status': 'WORKING',
        'emoji': '✅',
        'color': 'green',
        'message': 'Deployment validation fixed - properly fails on errors'
    },
    'status': {
        'status': 'WORKING',
        'emoji': '✅',
        'color': 'green',
        'message': 'Fully functional'
    },
    'test-rag': {
        'status': 'WORKING',
        'emoji': '✅',
        'color': 'green',
        'message': 'Fully functional'
    }
}

def show_command_warning(command_name: str, show_always: bool = False):
    """Show warning banner for a command based on its status"""
    status_info = COMMAND_STATUS.get(command_name)
    
    if not status_info:
        return  # Unknown command, skip warning
    
    # Skip warning for working commands unless explicitly requested
    if status_info['status'] == 'WORKING' and not show_always:
        return
    
    # Skip warning for partial commands in non-verbose mode
    if status_info['status'] == 'PARTIAL' and not show_always:
        return
    
    emoji = status_info['emoji']
    color = status_info['color']
    message = status_info['message']
    status = status_info['status']
    
    panel_text = (
        f"[bold {color}]{emoji} Command Status: {status}[/bold {color}]\n"
        f"[{color}]{message}[/{color}]\n\n"
        f"[dim]Run 'hyperagent limitations' for full details[/dim]"
    )
    
    console.print(Panel(panel_text, border_style=color, title=f"{command_name} command"))

def get_command_status(command_name: str) -> dict:
    """Get status information for a command"""
    return COMMAND_STATUS.get(command_name, {
        'status': 'UNKNOWN',
        'emoji': '❓',
        'color': 'white',
        'message': 'Unknown command status'
    })

