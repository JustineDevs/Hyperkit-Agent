"""
Health Check Utility - BRUTAL REALITY CHECK

Shows actual runtime health, not static badges.
Fails loud if dependencies are missing.
"""

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from core.validation.production_validator import validate_production_mode, get_production_validator

console = Console()

def health_check():
    """
    Perform comprehensive health check with brutal honesty.
    Shows actual runtime status, not static badges.
    """
    console.print("\n[bold blue]HYPERAGENT BRUTAL HEALTH CHECK[/bold blue]")
    console.print("=" * 60)
    
    # Validate production mode
    validator = get_production_validator()
    validation_results = validator.validate_production_mode()
    
    # Create status table
    table = Table(title="Runtime Health Status", show_header=True, header_style="bold magenta")
    table.add_column("Component", style="cyan", no_wrap=True)
    table.add_column("Status", justify="center")
    table.add_column("Details", style="white")
    
    # Add validation results to table
    for dep_name, result in validation_results['validation_results'].items():
        if result['status'] == 'success':
            status_text = Text("PASS", style="green")
        elif result['status'] == 'warning':
            status_text = Text("WARN", style="yellow")
        else:
            status_text = Text("FAIL", style="red")
        
        table.add_row(
            dep_name.replace('_', ' ').title(),
            status_text,
            result.get('message', 'No details')
        )
    
    console.print(table)
    
    # Show overall status
    if validation_results['production_mode']:
        console.print("\n[bold green]PRODUCTION MODE ENABLED[/bold green]")
        console.print("All critical dependencies are available and functional.")
        console.print("System is ready for production operations.")
    else:
        console.print("\n[bold red]SAFE MODE ONLY[/bold red]")
        console.print("Critical dependencies are missing. System will run in safe mode.")
        
        if validation_results['critical_failures']:
            console.print("\n[bold red]CRITICAL FAILURES:[/bold red]")
            for failure in validation_results['critical_failures']:
                console.print(f"  FAIL: {failure}")
        
        if validation_results['warnings']:
            console.print("\n[bold yellow]WARNINGS:[/bold yellow]")
            for warning in validation_results['warnings']:
                console.print(f"  WARN: {warning}")
    
    # Show next steps
    if not validation_results['production_mode']:
        console.print("\n[bold blue]NEXT STEPS:[/bold blue]")
        console.print("1. Install missing dependencies")
        console.print("2. Configure required environment variables")
        console.print("3. Run: hyperagent status --validate")
        console.print("4. Test with: hyperagent workflow run 'test' --network hyperion")
    
    return validation_results['production_mode']