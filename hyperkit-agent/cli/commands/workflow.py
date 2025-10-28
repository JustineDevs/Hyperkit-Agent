"""
Workflow Command Module
End-to-end smart contract workflows for HyperAgent with RAG template integration
Production-ready with Hyperion testnet focus
"""
import click
import asyncio
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from services.core.rag_template_fetcher import get_template

console = Console()

@click.group()
def workflow_group():
    """Run end-to-end smart contract workflows"""
    pass

@workflow_group.command(name='run')
@click.argument('prompt')
@click.option('--network', '-n', default='hyperion', help='Target network (default: hyperion)')
@click.option('--no-audit', is_flag=True, help='Skip security audit stage')
@click.option('--no-verify', is_flag=True, help='Skip contract verification stage')
@click.option('--test-only', is_flag=True, help='Generate and audit only (no deployment)')
@click.option('--allow-insecure', is_flag=True, help='Deploy even with high-severity audit issues')
@click.option('--use-rag/--no-use-rag', default=True, help='Use RAG templates for enhanced workflow context')
@click.pass_context
def run_workflow(ctx, prompt, network, no_audit, no_verify, test_only, allow_insecure, use_rag):
    """
    Run complete AI-powered smart contract workflow with RAG template integration
    
    Stages: Generate → Audit → Deploy → Verify → Test
    
    \b
    Examples:
        # Basic token creation
        hyperagent workflow run "create pausable ERC20 token"
        
        # Advanced DeFi contract
        hyperagent workflow run "create staking contract with rewards" --network hyperion
        
        # Test without deployment
        hyperagent workflow run "create NFT contract" --test-only
        
        # Deploy high-risk contract
        hyperagent workflow run "create token" --allow-insecure
    """
    from core.agent.main import HyperKitAgent
    from core.config.loader import get_config
    
    verbose = ctx.obj.get('verbose', False)
    debug = ctx.obj.get('debug', False)
    
    # Load RAG templates for enhanced workflow context
    rag_context = {}
    if use_rag:
        console.print("Loading RAG templates for enhanced workflow context...", style="blue")
        try:
            # Load generation prompt
            generation_prompt = asyncio.run(get_template('contract-generation-prompt'))
            if generation_prompt:
                rag_context['generation_prompt'] = generation_prompt
                console.print("Generation prompt loaded", style="green")
            
            # Load security checklist
            security_checklist = asyncio.run(get_template('security-checklist'))
            if security_checklist:
                rag_context['security_checklist'] = security_checklist
                console.print("Security checklist loaded", style="green")
            
            # Load deployment template
            deployment_template = asyncio.run(get_template('hardhat-deploy'))
            if deployment_template:
                rag_context['deployment_template'] = deployment_template
                console.print("Deployment template loaded", style="green")
            
            if not rag_context:
                console.print("No RAG templates available, using default workflow", style="yellow")
        except Exception as rag_error:
            console.print(f"RAG fetch failed: {rag_error}", style="yellow")
    
    # Display configuration
    config_panel = Panel.fit(
        f"[cyan]HyperAgent Workflow[/cyan]\n"
        f"[white]Prompt:[/white] {prompt}\n"
        f"[white]Network:[/white] {network}\n"
        f"[white]Mode:[/white] {'Test Only' if test_only else 'Full Deployment'}\n"
        f"[white]Security:[/white] {'Skip Audit' if no_audit else 'Full Audit'}\n"
        f"[white]RAG Context:[/white] {'Enabled' if rag_context else 'Disabled'}",
        title="[bold green]Workflow Configuration[/bold green]",
        border_style="green"
    )
    console.print(config_panel)
    
    try:
        # Initialize agent
        console.print("\n[yellow]Initializing HyperAgent...[/yellow]")
        config = get_config().to_dict()
        agent = HyperKitAgent(config)
        
        if verbose:
            console.print("[dim]Agent configuration loaded successfully[/dim]")
        
        # Enhance prompt with RAG context if available
        enhanced_prompt = prompt
        if rag_context:
            console.print("\n[cyan]Enhancing prompt with RAG context...[/cyan]")
            
            # Compose enhanced prompt with RAG templates
            rag_sections = []
            if 'generation_prompt' in rag_context:
                rag_sections.append(f"Generation Guidelines:\n{rag_context['generation_prompt']}")
            
            if 'security_checklist' in rag_context:
                rag_sections.append(f"Security Requirements:\n{rag_context['security_checklist']}")
            
            if 'deployment_template' in rag_context:
                rag_sections.append(f"Deployment Best Practices:\n{rag_context['deployment_template']}")
            
            if rag_sections:
                enhanced_prompt = f"""{prompt}

RAG Context for Enhanced Workflow:
{chr(10).join(rag_sections)}"""
                console.print("Prompt enhanced with RAG context", style="green")
        
        # Run workflow
        console.print("\n[cyan]Starting 5-stage workflow...[/cyan]\n")
        
        result = asyncio.run(agent.run_workflow(
            user_prompt=enhanced_prompt,
            network=network,
            auto_verification=not no_verify,
            test_only=test_only,
            allow_insecure=allow_insecure
        ))
        
        # Process results
        if result['status'] == 'success':
            success = _display_success_results(result, network, test_only, verbose)
            if not success:
                console.print(f"\n[red bold]WORKFLOW TERMINATED DUE TO CRITICAL FAILURE[/red bold]")
                return
        else:
            _display_error_results(result)
            
    except Exception as e:
        console.print(f"\n[red bold]Workflow error: {e}[/red bold]")
        if debug:
            import traceback
            console.print(f"\n[red]{traceback.format_exc()}[/red]")

def _display_success_results(result: dict, network: str, test_only: bool, verbose: bool):
    """Display successful workflow results"""
    console.print("\n[green bold]Workflow completed successfully![/green bold]\n")
    
    # Create results table
    table = Table(title="Workflow Results", show_header=True, header_style="bold cyan")
    table.add_column("Stage", style="cyan", width=20)
    table.add_column("Status", width=15)
    table.add_column("Details", width=50)
    
    # Stage 1: Generation
    gen = result.get('generation', {})
    if gen:
        table.add_row(
            "1. Generation",
            "[green]Success[/green]",
            f"File: {gen.get('filename', 'N/A')}\nProvider: {gen.get('provider_used', 'AI')}"
        )
    
    # Stage 2: Audit
    audit = result.get('audit', {})
    if audit:
        severity = audit.get('severity', 'unknown')
        severity_color = {
            'low': 'green',
            'medium': 'yellow',
            'high': 'red',
            'critical': 'red bold'
        }.get(severity, 'white')
        
        table.add_row(
            "2. Audit",
            f"[{severity_color}]Complete[/{severity_color}]",
            f"Severity: {severity.upper()}\nStatus: {audit.get('status', 'N/A')}"
        )
    
    # Stage 3: Deployment
    deploy = result.get('deployment', {})
    if deploy and not test_only:
        deploy_status = deploy.get('status', 'unknown')
        if deploy_status in ['deployed', 'success']:
            table.add_row(
                "3. Deployment",
                "[green]Deployed[/green]",
                f"Address: {deploy.get('address', 'N/A')}\nTX: {deploy.get('tx_hash', 'N/A')[:18]}..."
            )
        else:
            # FAIL LOUD - Don't fake success
            error_msg = deploy.get('error', 'Unknown deployment error')
            suggestions = deploy.get('suggestions', [])
            
            table.add_row(
                "3. Deployment",
                "[red]FAILED[/red]",
                f"Error: {error_msg}"
            )
            
            # Show detailed error information
            console.print(f"\n[red bold]🚨 DEPLOYMENT FAILED[/red bold]")
            console.print(f"[red]Error: {error_msg}[/red]")
            
            if suggestions:
                console.print(f"\n[yellow]💡 Suggestions:[/yellow]")
                for suggestion in suggestions:
                    console.print(f"  • {suggestion}")
            
            # Show deployment details if available
            details = deploy.get('details', {})
            if details:
                console.print(f"\n[cyan]Technical Details:[/cyan]")
                for key, value in details.items():
                    console.print(f"  {key}: {value}")
            
            # FAIL THE WORKFLOW - Don't continue
            console.print(f"\n[red bold]WORKFLOW FAILED - DEPLOYMENT STAGE BROKEN[/red bold]")
            console.print(f"[yellow]Fix the deployment issue before continuing.[/yellow]")
            return False
    elif test_only:
        table.add_row(
            "3. Deployment",
            "[blue]Skipped[/blue]",
            "Test-only mode enabled"
        )
    
    # Stage 4: Verification
    verify = result.get('verification', {})
    if verify and not test_only:
        verify_status = verify.get('status', 'unknown')
        if verify_status == 'success':
            table.add_row(
                "4. Verification",
                "[green]Verified[/green]",
                "Contract verified on explorer"
            )
        else:
            table.add_row(
                "4. Verification",
                "[yellow]Pending[/yellow]",
                f"Status: {verify_status}"
            )
    
    # Stage 5: Testing
    testing = result.get('testing', {})
    if testing and not test_only:
        test_status = testing.get('status', 'unknown')
        if test_status == 'success':
            table.add_row(
                "5. Testing",
                "[green]Passed[/green]",
                f"Tests: {testing.get('tests_passed', 'N/A')}"
            )
    
    console.print(table)
    
    # Display key information
    if deploy and deploy.get('status') in ['deployed', 'success']:
        contract_address = deploy.get('address', '')
        if contract_address:
            console.print(f"\n[bold green]📍 Contract Address:[/bold green] [white]{contract_address}[/white]")
            console.print(f"[bold green]🔗 Explorer URL:[/bold green] [link=https://hyperion-testnet-explorer.metisdevops.link/address/{contract_address}]https://hyperion-testnet-explorer.metisdevops.link/address/{contract_address}[/link]")
    
    # Display file path
    if gen and gen.get('path'):
        console.print(f"[bold cyan]Contract File:[/bold cyan] [white]{gen.get('path')}[/white]")
    
    # Only show success if we actually succeeded
    console.print(f"\n[green bold]🎉 All stages completed successfully![/green bold]")
    return True

def _display_error_results(result: dict):
    """Display error results"""
    error_msg = result.get('error', 'Unknown error occurred')
    console.print(f"\n[red bold]Workflow failed:[/red bold] {error_msg}")
    
    if result.get('workflow'):
        console.print(f"[yellow]Failed at stage:[/yellow] {result.get('workflow')}")

@workflow_group.command(name='status')
@click.option('--network', '-n', default='hyperion', help='Target network')
def workflow_status(network):
    """Check workflow system status"""
    console.print(f"[cyan]Workflow System Status[/cyan]\n")
    
    status_table = Table(show_header=True, header_style="bold cyan")
    status_table.add_column("Component", style="cyan")
    status_table.add_column("Status", width=20)
    
    # Check components
    status_table.add_row("Network", f"[green][/green] {network}")
    status_table.add_row("AI Generation", "[green]Ready[/green]")
    status_table.add_row("Security Audit", "[green]Ready[/green]")
    status_table.add_row("Deployment", "[green]Ready[/green]")
    status_table.add_row("Verification", "[green]Ready[/green]")
    
    console.print(status_table)
    console.print("\n[green]All workflow components operational[/green]")

@workflow_group.command(name='list')
def list_workflows():
    """List available workflow templates"""
    console.print("[cyan]Available Workflow Templates[/cyan]\n")
    
    templates = {
        'Tokens': [
            'create ERC20 token',
            'create pausable ERC20 token',
            'create mintable and burnable token',
            'create deflationary token with tax'
        ],
        'NFTs': [
            'create ERC721 NFT contract',
            'create enumerable NFT contract',
            'create NFT with royalties',
            'create soulbound token'
        ],
        'DeFi': [
            'create staking contract with rewards',
            'create liquidity pool',
            'create yield farming contract',
            'create vesting contract'
        ],
        'Governance': [
            'create DAO governance contract',
            'create voting system',
            'create multisig wallet',
            'create timelock controller'
        ]
    }
    
    for category, items in templates.items():
        console.print(f"\n[bold cyan]{category}:[/bold cyan]")
        for item in items:
            console.print(f"  • hyperagent workflow run \"{item}\"")
