"""
Audit Command Module
Smart contract auditing functionality with RAG template integration
"""

import asyncio
import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from services.core.rag_template_fetcher import get_template

console = Console()

@click.group()
def audit_group():
    """Audit smart contracts for security vulnerabilities"""
    pass

@audit_group.command()
@click.option('--contract', '-c', help='Contract file path')
@click.option('--address', '-a', help='Contract address to audit')
@click.option('--network', '-n', default='hyperion', hidden=True, help='[DEPRECATED] Hyperion is the only supported network')
@click.option('--output', '-o', help='Output file for audit report')
@click.option('--format', '-f', default='json', help='Output format (json, markdown, html)')
@click.option('--severity', '-s', help='Minimum severity level (low, medium, high, critical)')
@click.option('--use-rag/--no-use-rag', default=True, help='Use RAG security checklists for enhanced auditing')
@click.pass_context
def contract(ctx, contract, address, network, output, format, severity, use_rag):
    """Audit a smart contract for security issues using RAG checklists"""
    from core.agent.main import HyperKitAgent
    from core.config.loader import get_config
    
    # Validate input - either contract file or address must be provided
    if not contract and not address:
        console.print("Error: Either --contract or --address must be provided", style="red")
        return
    
    if contract and address:
        console.print("Error: Cannot specify both --contract and --address", style="red")
        return
    
    # Load RAG security checklist if enabled
    security_checklist = None
    if use_rag:
        console.print("Fetching RAG security checklist for enhanced auditing...", style="blue")
        try:
            security_checklist = asyncio.run(get_template('security-checklist'))
            if security_checklist:
                console.print("Security checklist loaded from RAG", style="green")
            else:
                console.print("Security checklist unavailable, using default audit", style="yellow")
        except Exception as rag_error:
            console.print(f"RAG fetch failed: {rag_error}", style="yellow")
    
    try:
        # Initialize agent
        config = get_config().to_dict()
        agent = HyperKitAgent(config)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            if contract:
                console.print(f"🔍 Auditing contract file: {contract}")
                task = progress.add_task("Reading contract file...", total=None)
                
                # Read contract file
                with open(contract, 'r') as f:
                    contract_code = f.read()
                
                progress.update(task, description="Running security audit...")
                # Run audit
                result = asyncio.run(agent.audit_contract(contract_code))
                
            else:  # address-based audit
                console.print(f"🔍 Auditing contract address: {address}")
                console.print(f"🌐 Network: {network}")
                task = progress.add_task("Fetching contract from blockchain...", total=None)
                
                # Fetch contract from blockchain
                from services.blockchain.contract_fetcher import ContractFetcher
                fetcher = ContractFetcher()
                contract_result = fetcher.fetch_contract_source(address, network)
                
                if not contract_result or not contract_result.get("source"):
                    console.print(f"Error: Could not fetch contract source for {address}", style="red")
                    console.print(f"💡 This contract may not be verified on the explorer", style="yellow")
                    return
                
                contract_code = contract_result["source"]
                
                progress.update(task, description="Running security audit...")
                # Run audit
                result = asyncio.run(agent.audit_contract(contract_code))
            
            if result['status'] == 'success':
                console.print(f"Audit completed")
                console.print(f"🔍 Severity: {result.get('severity', 'unknown').upper()}")
                console.print(f"Method: {result.get('method', 'AI')}")
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
                console.print(f"Audit failed: {result.get('error', 'Unknown error')}", style="red")
                
    except Exception as e:
        console.print(f"Error: {e}", style="red")
        if ctx.obj.get('debug'):
            import traceback
            console.print(traceback.format_exc())

@audit_group.command()
@click.option('--directory', '-d', help='Directory containing Solidity contracts')
@click.option('--file', '-f', help='Text file with list of contract paths (one per line)')
@click.option('--recursive', '-r', is_flag=True, help='Recursively audit subdirectories')
@click.option('--network', '-n', default='hyperion', hidden=True, help='[DEPRECATED] Hyperion is the only supported network')
@click.option('--output', '-o', help='Output directory for audit reports')
@click.option('--format', default='json', help='Output format (json, markdown)')
@click.option('--severity', '-s', help='Filter by minimum severity (low, medium, high, critical)')
@click.pass_context
def batch(ctx, directory, file, recursive, network, output, format, severity):
    """Audit multiple contracts in batch"""
    import asyncio
    import os
    from pathlib import Path
    from core.agent.main import HyperKitAgent
    from core.config.loader import get_config
    from rich.table import Table
    from datetime import datetime
    
    # Validate input
    if not directory and not file:
        console.print("Error: Either --directory or --file must be provided", style="red")
        console.print("\nUsage:")
        console.print("  hyperagent audit batch --directory ./contracts")
        console.print("  hyperagent audit batch --file contracts.txt")
        return
    
    if directory and file:
        console.print("Error: Cannot specify both --directory and --file", style="red")
        return
    
    # Get contract files
    contracts_to_audit = []
    
    if directory:
        console.print(f"Scanning directory: {directory}")
        dir_path = Path(directory)
        
        if not dir_path.exists():
            console.print(f"Error: Directory not found: {directory}", style="red")
            return
        
        # Find .sol files
        if recursive:
            console.print("🔄 Recursive mode enabled")
            contracts_to_audit = list(dir_path.rglob("*.sol"))
        else:
            contracts_to_audit = list(dir_path.glob("*.sol"))
        
        console.print(f"Found {len(contracts_to_audit)} Solidity contracts")
    
    elif file:
        console.print(f"📄 Reading contracts from: {file}")
        
        if not Path(file).exists():
            console.print(f"Error: File not found: {file}", style="red")
            return
        
        with open(file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    contract_path = Path(line)
                    if contract_path.exists():
                        contracts_to_audit.append(contract_path)
                    else:
                        console.print(f"Warning: Contract not found: {line}", style="yellow")
        
        console.print(f"Found {len(contracts_to_audit)} contracts to audit")
    
    if not contracts_to_audit:
        console.print("No contracts found to audit", style="yellow")
        return
    
    # Initialize agent
    try:
        config = get_config().to_dict()
        agent = HyperKitAgent(config)
    except Exception as e:
        console.print(f"Error initializing agent: {e}", style="red")
        return
    
    # Audit each contract
    results = []
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task(f"Auditing contracts...", total=len(contracts_to_audit))
        
        for contract_path in contracts_to_audit:
            progress.update(task, description=f"Auditing {contract_path.name}...")
            
            try:
                # Read contract
                with open(contract_path, 'r') as f:
                    contract_code = f.read()
                
                # Run audit
                result = asyncio.run(agent.audit_contract(contract_code))
                
                results.append({
                    'contract': str(contract_path),
                    'name': contract_path.name,
                    'status': result.get('status', 'unknown'),
                    'severity': result.get('severity', 'unknown'),
                    'method': result.get('method', 'AI'),
                    'issues_found': len(result.get('results', {}).get('issues', [])),
                    'result': result
                })
                
            except Exception as e:
                results.append({
                    'contract': str(contract_path),
                    'name': contract_path.name,
                    'status': 'error',
                    'severity': 'unknown',
                    'method': 'N/A',
                    'issues_found': 0,
                    'error': str(e)
                })
            
            progress.update(task, advance=1)
    
    # Display results table
    table = Table(title=f"🔍 Batch Audit Results - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    table.add_column("Contract", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Severity", style="yellow")
    table.add_column("Issues", justify="right")
    
    for result in results:
        status_emoji = "PASS" if result['status'] == 'success' else "FAIL"
        severity_color = {
            'critical': 'red',
            'high': 'red',
            'medium': 'yellow',
            'low': 'green',
            'unknown': 'white'
        }.get(result.get('severity', 'unknown').lower(), 'white')
        
        table.add_row(
            result['name'],
            f"{status_emoji} {result['status']}",
            f"[{severity_color}]{result.get('severity', 'unknown').upper()}[/{severity_color}]",
            str(result.get('issues_found', 0))
        )
    
    console.print(table)
    
    # Save reports if output specified
    if output:
        output_path = Path(output)
        output_path.mkdir(parents=True, exist_ok=True)
        
        console.print(f"\nSaving reports to: {output}")
        
        for result in results:
            if result['status'] == 'success':
                report_name = f"{Path(result['name']).stem}_audit.{format}"
                report_path = output_path / report_name
                
                with open(report_path, 'w') as f:
                    if format == 'json':
                        import json
                        json.dump(result['result'], f, indent=2)
                    else:  # markdown
                        f.write(f"# Security Audit Report\n\n")
                        f.write(f"**Contract:** {result['name']}\n")
                        f.write(f"**Status:** {result['status']}\n")
                        f.write(f"**Severity:** {result.get('severity', 'unknown')}\n")
                        f.write(f"**Issues Found:** {result.get('issues_found', 0)}\n")
                        f.write(f"**Method:** {result.get('method', 'AI')}\n\n")
                        f.write(f"**Results:**\n```json\n")
                        import json
                        f.write(json.dumps(result['result'].get('results', {}), indent=2))
                        f.write("\n```\n")
        
        console.print(f"Saved {len([r for r in results if r['status'] == 'success'])} reports")
    
    # Summary
    total = len(results)
    success = len([r for r in results if r['status'] == 'success'])
    errors = len([r for r in results if r['status'] == 'error'])
    
    console.print(f"\nSummary:")
    console.print(f"  Total Contracts: {total}")
    console.print(f"  Successful: {success}")
    console.print(f"  Errors: {errors}")
    
    # Filter by severity if specified
    if severity:
        filtered = [r for r in results if r.get('severity', '').lower() == severity.lower()]
        console.print(f"  🔍 Filtered ({severity}): {len(filtered)}")
    
    console.print("\nBatch audit completed")

@audit_group.command()
@click.option('--report', '-r', required=True, help='Audit report file (JSON or Markdown)')
@click.option('--format', '-f', help='Output format (table, json, markdown)')
def report(report, format):
    """View audit report"""
    from pathlib import Path
    import json
    from rich.table import Table
    from rich.markdown import Markdown
    
    report_path = Path(report)
    
    if not report_path.exists():
        console.print(f"Error: Report file not found: {report}", style="red")
        return
    
    try:
        # Determine file type
        if report_path.suffix == '.json':
            with open(report_path, 'r') as f:
                data = json.load(f)
            
            # Display based on format
            if format == 'json':
                console.print(json.dumps(data, indent=2))
            else:
                # Display as table (default)
                console.print(f"\nAudit Report: {report_path.name}\n")
                
                # Basic info
                console.print(f"[cyan]Status:[/cyan] {data.get('status', 'unknown')}")
                console.print(f"[cyan]Severity:[/cyan] {data.get('severity', 'unknown').upper()}")
                console.print(f"[cyan]Method:[/cyan] {data.get('method', 'AI')}")
                console.print(f"[cyan]Provider:[/cyan] {data.get('provider', 'AI')}")
                
                # Issues table
                if 'results' in data and 'issues' in data['results']:
                    issues = data['results']['issues']
                    
                    if issues:
                        console.print(f"\n🔍 Found {len(issues)} issues:\n")
                        
                        table = Table(title="Security Issues")
                        table.add_column("Severity", style="yellow")
                        table.add_column("Type", style="cyan")
                        table.add_column("Description")
                        
                        for issue in issues:
                            severity_color = {
                                'critical': 'red',
                                'high': 'red',
                                'medium': 'yellow',
                                'low': 'green'
                            }.get(issue.get('severity', '').lower(), 'white')
                            
                            table.add_row(
                                f"[{severity_color}]{issue.get('severity', 'unknown').upper()}[/{severity_color}]",
                                issue.get('type', 'unknown'),
                                issue.get('description', 'No description')
                            )
                        
                        console.print(table)
                    else:
                        console.print("\nNo security issues found")
        
        elif report_path.suffix == '.md':
            with open(report_path, 'r') as f:
                md_content = f.read()
            
            if format == 'markdown':
                console.print(md_content)
            else:
                # Render markdown
                md = Markdown(md_content)
                console.print(md)
        
        else:
            console.print(f"Error: Unsupported report format: {report_path.suffix}", style="red")
            console.print("Supported formats: .json, .md")
            return
        
        console.print(f"\nReport displayed successfully")
        
    except json.JSONDecodeError as e:
        console.print(f"Error: Invalid JSON format: {e}", style="red")
    except Exception as e:
        console.print(f"Error reading report: {e}", style="red")
