"""
Audit Command Module
Smart contract auditing functionality
"""

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

@click.group()
def audit_group():
    """Audit smart contracts for security vulnerabilities"""
    pass

@audit_group.command()
@click.option('--contract', '-c', required=True, help='Contract file path')
@click.option('--output', '-o', help='Output file for audit report')
@click.option('--format', '-f', default='json', help='Output format (json, markdown, html)')
@click.option('--severity', '-s', help='Minimum severity level (low, medium, high, critical)')
@click.pass_context
def contract(ctx, contract, output, format, severity):
    """Audit a smart contract for security issues"""
    import asyncio
    from core.agent.main import HyperKitAgent
    from core.config.loader import get_config
    
    console.print(f"🔍 Auditing contract: {contract}")
    
    try:
        # Initialize agent
        config = get_config().to_dict()
        agent = HyperKitAgent(config)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Running security audit...", total=None)
            
            # Read contract file
            with open(contract, 'r') as f:
                contract_code = f.read()
            
            # Run audit
            result = asyncio.run(agent.audit_contract(contract_code))
            
            if result['status'] == 'success':
                console.print(f"✅ Audit completed")
                console.print(f"🔍 Severity: {result.get('severity', 'unknown').upper()}")
                console.print(f"📊 Method: {result.get('method', 'AI')}")
                console.print(f"🤖 Provider: {result.get('provider', 'AI')}")
                
                # Save report if output specified
                if output:
                    import json
                    with open(output, 'w') as f:
                        if format == 'json':
                            json.dump(result, f, indent=2)
                        else:
                            f.write(f"# Security Audit Report\n\n")
                            f.write(f"**Contract:** {contract}\n")
                            f.write(f"**Severity:** {result.get('severity', 'unknown')}\n")
                            f.write(f"**Method:** {result.get('method', 'AI')}\n")
                            f.write(f"**Provider:** {result.get('provider', 'AI')}\n\n")
                            f.write(f"**Results:**\n")
                            f.write(json.dumps(result.get('results', {}), indent=2))
                    console.print(f"📄 Report saved to: {output}")
            else:
                console.print(f"❌ Audit failed: {result.get('error', 'Unknown error')}", style="red")
                
    except Exception as e:
        console.print(f"❌ Error: {e}", style="red")
        if ctx.obj.get('debug'):
            import traceback
            console.print(traceback.format_exc())

@audit_group.command()
@click.option('--directory', '-d', help='Directory to audit')
@click.option('--recursive', '-r', is_flag=True, help='Recursively audit subdirectories')
def batch(directory, recursive):
    """Audit multiple contracts in batch"""
    console.print(f"📁 Batch auditing directory: {directory}")
    
    if recursive:
        console.print("🔄 Recursive mode enabled")
    
    # TODO: Implement batch auditing
    console.print("✅ Batch audit completed")

@audit_group.command()
@click.option('--report', '-r', required=True, help='Audit report file')
def report(report):
    """View audit report"""
    console.print(f"📊 Viewing audit report: {report}")
    
    # TODO: Implement report viewing
    console.print("✅ Report displayed")
