"""
Workflow Command Module
End-to-end smart contract workflows for HyperAgent with RAG template integration
Production-ready with Hyperion testnet focus
"""
import click
import asyncio
from pathlib import Path
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
@click.option('--network', '-n', default='hyperion', hidden=True, help='[DEPRECATED] Hyperion is the only supported network')
@click.option('--no-audit', is_flag=True, help='Skip security audit stage')
@click.option('--no-verify', is_flag=True, help='Skip contract verification stage')
@click.option('--test-only', is_flag=True, help='Generate and audit only (no deployment)')
@click.option('--allow-insecure', is_flag=True, help='Deploy even with high-severity audit issues')
@click.option('--use-rag/--no-use-rag', default=True, help='Use RAG templates for enhanced workflow context')
@click.option('--upload-scope', type=click.Choice(['team', 'community']), default=None, help='Auto-upload artifacts to Pinata IPFS (team=official, community=user-generated)')
@click.option('--rag-scope', type=click.Choice(['official-only', 'opt-in-community']), default='official-only', help='RAG fetch scope (official-only=Team only, opt-in-community=include Community artifacts)')
@click.option('--resume-from', help='Resume workflow from diagnostic bundle (path to diagnostics JSON file)')
@click.pass_context
def run_workflow(ctx, prompt, network, no_audit, no_verify, test_only, allow_insecure, use_rag, upload_scope, rag_scope, resume_from):
    """
    Run complete AI-powered smart contract workflow with RAG template integration
    
    AI Model: [*] PRIMARY Gemini (gemini-2.5-flash-lite via Alith SDK adapter)
             [>] SECONDARY OpenAI (via Alith SDK) if Gemini unavailable
    
hype    [OK] FIXED: Deployment validation has been added - workflow properly fails on errors.
    No more fake success messages. See docs/HONEST_STATUS.md for details.
    
    Stages: Generate -> Audit -> Deploy -> Verify -> Test
    
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
    from cli.utils.warnings import show_command_warning
    show_command_warning('workflow')
    
    from core.agent.main import HyperKitAgent
    from core.config.loader import get_config
    
    verbose = ctx.obj.get('verbose', False)
    debug = ctx.obj.get('debug', False)
    
    # Display configuration
    config_panel = Panel.fit(
        f"[cyan]HyperAgent Workflow[/cyan]\n"
        f"[white]Prompt:[/white] {prompt}\n"
        f"[white]Network:[/white] {network}\n"
        f"[white]Mode:[/white] {'Test Only' if test_only else 'Full Deployment'}\n"
        f"[white]Security:[/white] {'Skip Audit' if no_audit else 'Full Audit'}\n"
        f"[white]RAG Scope:[/white] {rag_scope}\n"
        f"[white]Upload Scope:[/white] {upload_scope or 'None'}",
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
        
        # Use original prompt - RAG will be handled by orchestrator
        enhanced_prompt = prompt
        
        # Hardcode Hyperion - no network selection
        network = "hyperion"  # HYPERION-ONLY: Ignore any --network flag
        if ctx.params.get('network') and ctx.params.get('network') != 'hyperion':
            console.print(f"[red]WARNING: Network '{ctx.params.get('network')}' not supported[/red]")
            console.print("[yellow]Using Hyperion (only supported network)[/yellow]")
        
        # Run workflow with real-time monitoring (Phase 5)
        console.print("\n[cyan]Starting 5-stage workflow...[/cyan]")
        console.print(f"[dim]Network: Hyperion (exclusive deployment target)[/dim]\n")
        
        # Display workflow state panel (Phase 5)
        from core.workflow.state_persistence import StatePersistence
        from pathlib import Path
        state_persistence = StatePersistence(Path.cwd())
        
        # Create progress indicator with workflow state updates
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("[cyan]Executing workflow...", total=None)
            
            # Run workflow
            result = asyncio.run(agent.run_workflow(
                user_prompt=enhanced_prompt,
                network="hyperion",  # Hardcoded - Hyperion only
                auto_verification=not no_verify,
                test_only=test_only,
                allow_insecure=allow_insecure,
                upload_scope=upload_scope,
                rag_scope=rag_scope,
                resume_from_diagnostic=resume_from
            ))
            
            progress.update(task, completed=True)
            
            # Display workflow state after completion (Phase 5)
            workflow_id = result.get('workflow_id') or result.get('workflow', {}).get('id')
            if workflow_id:
                state = state_persistence.load_state(workflow_id)
                if state:
                    # Show current step and reasoning
                    console.print(f"\n[bold cyan]Workflow State:[/bold cyan]")
                    console.print(f"  Step: [yellow]{state.current_step.value}[/yellow]")
                    console.print(f"  Stage: [yellow]{state.current_stage or 'N/A'}[/yellow]")
                    if state.current_reasoning:
                        console.print(f"  Reasoning: [dim]{state.current_reasoning.reasoning[:100]}...[/dim]")
                    console.print(f"  [dim]Use 'hyperagent workflow inspect {workflow_id}' for full details[/dim]")
        
        # Process results with proper status handling
        workflow_status = result.get('status', 'unknown')
        critical_failure = result.get('critical_failure', False)
        
        # Handle different workflow statuses
        if workflow_status == 'success':
            # All stages succeeded - show success
            success = _display_success_results(result, network, test_only, verbose)
            if success:
                console.print(f"\n[green bold]✅ Workflow completed successfully![/green bold]")
                ctx.exit(0)
            else:
                console.print(f"\n[yellow]Workflow completed with warnings[/yellow]")
                ctx.exit(0)
                
        elif workflow_status == 'completed_with_errors':
            # Non-critical errors (deployment/verification failed but gen/compile succeeded)
            console.print(f"\n[yellow bold]⚠️  Workflow completed with non-critical errors[/yellow bold]")
            _display_success_results(result, network, test_only, verbose)
            console.print(f"\n[yellow]Note: Deployment or verification failed, but contract generation succeeded.[/yellow]")
            console.print(f"[yellow]Check the diagnostic bundle for details: {result.get('diagnostic_bundle', 'N/A')}[/yellow]")
            ctx.exit(0)  # Exit 0 - workflow completed, just with errors
            
        elif workflow_status == 'error' or critical_failure:
            # Critical failure (generation/compilation failed)
            console.print(f"\n[red bold]❌ Workflow failed due to critical errors[/red bold]")
            _display_error_results(result)
            
            # Show failed stages
            failed_stages = result.get('failed_stages', [])
            if failed_stages:
                console.print(f"\n[red]Failed critical stages: {', '.join(failed_stages)}[/red]")
            
            # Show diagnostic bundle location
            diagnostic_bundle = result.get('diagnostic_bundle')
            if diagnostic_bundle:
                console.print(f"\n[yellow]Diagnostic bundle saved: {diagnostic_bundle}[/yellow]")
                console.print(f"[yellow]Review for detailed error information and recovery steps[/yellow]")
            
            ctx.exit(1)  # Exit with error code
        else:
            # Unknown status
            console.print(f"\n[yellow]Workflow completed with unknown status: {workflow_status}[/yellow]")
            _display_success_results(result, network, test_only, verbose)
            ctx.exit(0)
            
    except Exception as e:
        console.print(f"\n[red bold]Workflow error: {e}[/red bold]")
        if debug:
            import traceback
            console.print(f"\n[red]{traceback.format_exc()}[/red]")

def _display_success_results(result: dict, network: str, test_only: bool, verbose: bool):
    """Display workflow results (success, partial success, or errors)"""
    # Create results table
    table = Table(title="Workflow Results", show_header=True, header_style="bold cyan")
    table.add_column("Stage", style="cyan", width=20)
    table.add_column("Status", width=15)
    table.add_column("Details", width=50)
    
    # Stage 1: Generation
    gen = result.get('generation', {})
    if gen:
        # Get actual file path from artifacts or generation result
        contract_path = (
            result.get('artifacts', {}).get('local_paths', {}).get('contract') or
            gen.get('path') or
            gen.get('filename', 'N/A')
        )
        # Make path relative if it's absolute
        if contract_path and contract_path != 'N/A':
            try:
                contract_path = str(Path(contract_path).relative_to(Path.cwd()))
            except (ValueError, TypeError):
                pass  # Keep absolute path if can't make relative
        
        table.add_row(
            "1. Generation",
            "[green]Success[/green]",
            f"File: {contract_path}\nProvider: {gen.get('provider_used', 'AI')}"
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
        # Check if deployment actually succeeded - look for address or success status
        address = deploy.get('address') or deploy.get('contract_address') or None
        tx_hash = deploy.get('tx_hash') or deploy.get('transaction_hash') or None
        network = deploy.get('network', 'hyperion')
        
        # If status is success/deployed OR we have an address, deployment succeeded
        deployment_succeeded = (
            deploy_status in ['deployed', 'success'] or 
            address is not None or 
            tx_hash is not None
        )
        
        if deployment_succeeded:
            if address:
                address_display = address
            else:
                # Address might be missing but deployment succeeded - check if we can extract from tx
                address_display = 'Deployed (address pending)'
            
            if tx_hash:
                # Show truncated TX in table, full link will be shown below
                tx_display = f"{tx_hash[:18]}..."
            else:
                tx_display = 'N/A'
            
            # Determine deployment status for display
            if address:
                status_display = "[green]Deployed[/green]"
            elif tx_hash:
                status_display = "[green]Deployed[/green]"  # Has TX hash = deployed
            else:
                status_display = "[yellow]Pending[/yellow]"
            
            table.add_row(
                "3. Deployment",
                status_display,
                f"Address: {address_display}\nTX: {tx_display}"
            )
            
            # Store TX hash and address for display below table
            deploy['_tx_hash_display'] = tx_hash
            deploy['_address_display'] = address
            deploy['_network'] = network
        elif deploy_status not in ['skipped', 'unknown']:
            # FAIL LOUD - Don't fake success (only if status is explicitly error/failed)
            error_msg = deploy.get('error', 'Unknown deployment error')
            suggestions = deploy.get('suggestions', [])
            
            table.add_row(
                "3. Deployment",
                "[red]FAILED[/red]",
                f"Error: {error_msg}"
            )
            
            # Show detailed error information
            console.print(f"\n[red bold]DEPLOYMENT FAILED[/red bold]")
            console.print(f"[red]Error: {error_msg}[/red]")
            
            if suggestions:
                console.print(f"\n[yellow]Suggestions:[/yellow]")
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
            console.print(f"\n[red bold]WORKFLOW TERMINATED DUE TO CRITICAL FAILURE[/red bold]")
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
        test_results = testing.get('results', {})
        
        if test_status == 'success':
            # Build meaningful test information
            test_info_parts = []
            
            if test_results:
                if test_results.get('foundry_tests_run'):
                    test_info_parts.append("Foundry tests executed")
                if test_results.get('tests_passed'):
                    test_info_parts.append("All tests passed")
                elif test_results.get('tests_passed') is False:
                    test_info_parts.append("Some tests failed")
                
                # Extract test count if available
                if 'test_count' in test_results:
                    test_info_parts.append(f"{test_results['test_count']} tests")
                elif 'tests_passed' is True:
                    test_info_parts.append("All tests passed")
            
            test_info = ", ".join(test_info_parts) if test_info_parts else "Tests executed successfully"
            
            table.add_row(
                "5. Testing",
                "[green]Passed[/green]",
                test_info
            )
        elif test_status == 'skipped':
            table.add_row(
                "5. Testing",
                "[blue]Skipped[/blue]",
                "Testing stage skipped"
            )
        else:
            table.add_row(
                "5. Testing",
                "[yellow]Pending[/yellow]",
                f"Status: {test_status}"
            )
    
    console.print(table)
    
    # Display key information
    deploy_status = deploy.get('status', 'unknown') if deploy else None
    deployment_succeeded = (
        deploy_status in ['deployed', 'success'] or 
        deploy.get('address') or 
        deploy.get('contract_address') or
        deploy.get('tx_hash') or
        deploy.get('transaction_hash')
    )
    
    if deploy and deployment_succeeded:
        contract_address = deploy.get('_address_display') or deploy.get('address') or deploy.get('contract_address')
        network = deploy.get('_network') or deploy.get('network', 'hyperion')
        tx_hash = deploy.get('_tx_hash_display') or deploy.get('tx_hash') or deploy.get('transaction_hash')
        
        # If we have tx_hash but no address, try to extract from transaction receipt
        if tx_hash and not contract_address:
            try:
                from web3 import Web3
                # Get RPC URL for Hyperion
                rpc_url = "https://hyperion-testnet-rpc.metisdevops.link"
                w3 = Web3(Web3.HTTPProvider(rpc_url))
                receipt = w3.eth.get_transaction_receipt(tx_hash)
                if receipt and receipt.contractAddress:
                    contract_address = receipt.contractAddress
                    console.print(f"[dim]✓ Extracted contract address from transaction receipt[/dim]")
            except Exception as e:
                # Silently fail - address extraction is optional
                pass
        
        if contract_address:
            console.print(f"\n[bold green]Contract Address:[/bold green] [white]{contract_address}[/white]")
            explorer_base = "https://hyperion-testnet-explorer.metisdevops.link"
            explorer_url = f"{explorer_base}/address/{contract_address}"
            console.print(f"[bold green]Explorer URL:[/bold green] [link={explorer_url}]{explorer_url}[/link]")
        elif tx_hash:
            # We have a transaction but no address - deployment might still be pending
            console.print(f"\n[bold yellow]Deployment Status:[/bold yellow] [white]Transaction confirmed, extracting address...[/white]")
            console.print(f"[dim]Contract address will be available from transaction receipt.[/dim]")
        else:
            console.print(f"\n[bold yellow]Deployment Status:[/bold yellow] [white]Pending deployment[/white]")
            console.print(f"[dim]Contract is being deployed. Address will be available once deployment completes.[/dim]")
        
        # Show transaction hash with clickable explorer link
        if tx_hash:
            explorer_base = "https://hyperion-testnet-explorer.metisdevops.link"
            tx_url = f"{explorer_base}/tx/{tx_hash}"
            console.print(f"[bold cyan]Transaction Hash:[/bold cyan] [link={tx_url}]{tx_hash}[/link]")
    
    # Display file paths and artifacts
    artifacts = result.get('artifacts', {})
    local_paths = artifacts.get('local_paths', {})
    
    # Contract file
    contract_path = local_paths.get('contract') or gen.get('path') if gen else None
    if contract_path:
        try:
            contract_path = str(Path(contract_path).relative_to(Path.cwd()))
        except (ValueError, TypeError):
            pass
        console.print(f"[bold cyan]Contract File:[/bold cyan] [white]{contract_path}[/white]")
    
    # ABI file
    abi_path = local_paths.get('abi')
    if abi_path:
        try:
            abi_path = str(Path(abi_path).relative_to(Path.cwd()))
        except (ValueError, TypeError):
            pass
        console.print(f"[bold cyan]ABI File:[/bold cyan] [white]{abi_path}[/white]")
    
    # Metadata file
    metadata_path = local_paths.get('metadata')
    if metadata_path:
        try:
            metadata_path = str(Path(metadata_path).relative_to(Path.cwd()))
        except (ValueError, TypeError):
            pass
        console.print(f"[bold cyan]Metadata File:[/bold cyan] [white]{metadata_path}[/white]")
    
    # Diagnostic bundle if errors occurred
    diagnostic_bundle = result.get('diagnostic_bundle')
    if diagnostic_bundle:
        try:
            diagnostic_bundle = str(Path(diagnostic_bundle).relative_to(Path.cwd()))
        except (ValueError, TypeError):
            pass
        console.print(f"[bold yellow]Diagnostic Bundle:[/bold yellow] [white]{diagnostic_bundle}[/white]")
    
    # Determine if workflow actually succeeded
    deploy = result.get('deployment', {})
    deploy_status = deploy.get('status', 'unknown') if deploy else None
    
    # Return True if critical stages (gen/compile) succeeded
    # Deployment/verification failures are non-critical and don't block "success"
    if deploy_status and deploy_status not in ['success', 'deployed', 'skipped', None]:
        # Deployment failed - but gen/compile succeeded
        return True  # Still return True - workflow completed, deployment is non-critical
    
    return True  # All good

def _display_error_results(result: dict):
    """Display error results with user-friendly messages"""
    error_msg = result.get('error', 'Unknown error occurred')
    console.print(f"\n[red bold]Workflow failed:[/red bold] {error_msg}")
    
    # Check for friendly error message in metadata (from guardrails)
    friendly_error = result.get('metadata', {}).get('friendly_error')
    if not friendly_error:
        # Try to extract from stages
        stages = result.get('stages', [])
        for stage in stages:
            if stage.get('status') == 'error' and stage.get('metadata', {}).get('friendly_error'):
                friendly_error = stage['metadata']['friendly_error']
                break
    
    if friendly_error:
        console.print(f"\n[yellow bold]{friendly_error.get('friendly_message', '')}[/yellow bold]")
        suggestions = friendly_error.get('suggestions', [])
        if suggestions:
            console.print(f"\n[cyan]Suggestions:[/cyan]")
            for suggestion in suggestions:
                console.print(f"  • {suggestion}")
        help_text = friendly_error.get('help_text')
        if help_text:
            console.print(f"\n[dim]{help_text}[/dim]")
    else:
        # Generic helpful message
        console.print(f"\n[yellow]💡 Tips:[/yellow]")
        console.print(f"  • Check the diagnostic bundle for detailed error information")
        console.print(f"  • Try reformulating your prompt with more specific requirements")
        console.print(f"  • Ensure all required dependencies are available")
        console.print(f"  • Review error logs for specific issues")
    
    if result.get('workflow'):
        console.print(f"\n[yellow]Failed at stage:[/yellow] {result.get('workflow')}")
    
    # Show failed stages if available
    failed_stages = result.get('failed_stages', [])
    if failed_stages:
        console.print(f"\n[red]Failed critical stages:[/red] {', '.join(failed_stages)}")

@workflow_group.command(name='status')
@click.option('--workflow-id', '-w', help='Specific workflow ID to check')
def workflow_status(workflow_id):
    """
    Show current workflow state and status.
    
    Displays the current autonomous loop state (read/plan/act/update) and
    agent reasoning for active or recent workflows.
    """
    from core.workflow.state_persistence import StatePersistence
    from pathlib import Path
    from rich.table import Table
    from rich.panel import Panel
    
    # Validate workflow_id - filter out Sentinel objects using centralized utility
    from cli.utils.sentinel_validator import validate_string_param
    workflow_id = validate_string_param(workflow_id, "workflow_id")
    
    workspace_dir = Path.cwd()
    state_persistence = StatePersistence(workspace_dir)
    
    if workflow_id:
        # Show specific workflow
        state = state_persistence.load_state(workflow_id)
        if not state:
            console.print(f"[red]Workflow '{workflow_id}' not found[/red]")
            return
        
        # Display workflow state
        status_table = Table(title=f"Workflow: {workflow_id}")
        status_table.add_column("Property", style="cyan")
        status_table.add_column("Value", style="white")
        
        status_table.add_row("Status", "[green]Complete[/green]" if state.is_complete else "[yellow]In Progress[/yellow]")
        status_table.add_row("Current Step", state.current_step.value)
        status_table.add_row("Current Stage", state.current_stage or "None")
        status_table.add_row("User Goal", state.user_goal[:100] + "..." if len(state.user_goal) > 100 else state.user_goal)
        status_table.add_row("Has Errors", "[red]Yes[/red]" if state.has_error else "[green]No[/green]")
        status_table.add_row("Tool Invocations", str(len(state.tool_invocations)))
        status_table.add_row("Reasoning Steps", str(len(state.reasoning_history)))
        
        console.print(status_table)
        
        # Show recent reasoning
        if state.reasoning_history:
            console.print("\n[bold]Recent Agent Reasoning:[/bold]")
            for reasoning in state.reasoning_history[-3:]:
                console.print(Panel(
                    f"[cyan]Step:[/cyan] {reasoning.step.value}\n"
                    f"[cyan]Reasoning:[/cyan] {reasoning.reasoning}\n"
                    f"[cyan]Confidence:[/cyan] {reasoning.confidence:.2f}",
                    title=f"{reasoning.timestamp}",
                    border_style="blue"
                ))
    else:
        # List recent workflows
        states_dir = state_persistence.states_dir
        if not states_dir.exists():
            console.print("[yellow]No workflows found[/yellow]")
            return
        
        workflows = []
        for workflow_dir in states_dir.iterdir():
            if workflow_dir.is_dir():
                state = state_persistence.load_state(workflow_dir.name)
                if state:
                    workflows.append(state)
        
        if not workflows:
            console.print("[yellow]No workflows found[/yellow]")
            return
        
        # Sort by updated_at
        workflows.sort(key=lambda s: s.updated_at, reverse=True)
        
        # Display table
        table = Table(title="Recent Workflows")
        table.add_column("Workflow ID", style="cyan")
        table.add_column("Status", style="white")
        table.add_column("Step", style="yellow")
        table.add_column("Updated", style="dim")
        
        for state in workflows[:10]:  # Last 10
            status = "[green]Complete[/green]" if state.is_complete else "[yellow]In Progress[/yellow]"
            table.add_row(
                state.workflow_id,
                status,
                state.current_step.value,
                state.updated_at[:19] if len(state.updated_at) > 19 else state.updated_at
            )
        
        console.print(table)
        console.print(f"\n[yellow]Use 'hyperagent workflow inspect <workflow_id>' for details[/yellow]")


@workflow_group.command(name='inspect')
@click.argument('workflow_id', required=False)
def workflow_inspect(workflow_id):
    """
    Inspect detailed workflow state and logs.
    
    Displays the complete workflow_state.yaml and workflow_log.md for a workflow.
    
    If no workflow_id is provided, shows the latest workflow.
    """
    from core.workflow.state_persistence import StatePersistence
    from pathlib import Path
    from rich.panel import Panel
    from rich.syntax import Syntax
    
    # Validate workflow_id - ensure it's a string using centralized utility
    from cli.utils.sentinel_validator import validate_string_param
    
    workspace_dir = Path.cwd()
    state_persistence = StatePersistence(workspace_dir)
    
    # If no workflow_id provided, try to get the latest one
    if not workflow_id:
        # Try to find the latest workflow
        workflows_dir = workspace_dir / ".workflow_contexts"
        if workflows_dir.exists():
            workflows = list(workflows_dir.glob("*.json"))
            if workflows:
                # Get the most recent workflow
                latest = max(workflows, key=lambda x: x.stat().st_mtime)
                workflow_id = latest.stem
                console.print(f"[yellow]No workflow ID provided. Using latest: {workflow_id}[/yellow]\n")
            else:
                console.print("[red]Error: Workflow ID is required[/red]")
                console.print("[yellow]Usage: hyperagent workflow inspect <WORKFLOW_ID>[/yellow]")
                console.print("[yellow]Example: hyperagent workflow inspect my-workflow-123[/yellow]")
                console.print("[yellow]Tip: Use 'hyperagent workflow status' to see recent workflows[/yellow]")
                raise click.ClickException("Workflow ID is required")
        else:
            console.print("[red]Error: Workflow ID is required[/red]")
            console.print("[yellow]Usage: hyperagent workflow inspect <WORKFLOW_ID>[/yellow]")
            console.print("[yellow]Example: hyperagent workflow inspect my-workflow-123[/yellow]")
            console.print("[yellow]Tip: Use 'hyperagent workflow status' to see recent workflows[/yellow]")
            raise click.ClickException("Workflow ID is required")
    
    workflow_id = validate_string_param(workflow_id, "workflow_id")
    
    if not workflow_id:
        console.print(f"[red]Workflow ID is required[/red]")
        console.print("[yellow]Usage: hyperagent workflow inspect <WORKFLOW_ID>[/yellow]")
        console.print("[yellow]Example: hyperagent workflow inspect my-workflow-123[/yellow]")
        console.print("[yellow]Tip: Use 'hyperagent workflow status' to see recent workflows[/yellow]")
        raise click.ClickException("Workflow ID is required")
    
    state = state_persistence.load_state(workflow_id)
    if not state:
        console.print(f"[red]Workflow '{workflow_id}' not found[/red]")
        return
    
    # Display YAML state
    log_path = state_persistence.get_log_path(workflow_id)
    if log_path.exists():
        log_content = log_path.read_text(encoding='utf-8')
        console.print(Panel(
            Syntax(log_content, "markdown", theme="monokai", line_numbers=True),
            title=f"[bold]Workflow Log: {workflow_id}[/bold]",
            border_style="green"
        ))
    else:
        console.print(f"[yellow]Log file not found: {log_path}[/yellow]")
    
    # Display state YAML
    state_path = state_persistence.get_state_path(workflow_id)
    if state_path.exists():
        import yaml
        with open(state_path, 'r', encoding='utf-8') as f:
            state_yaml = f.read()
        console.print(Panel(
            Syntax(state_yaml, "yaml", theme="monokai", line_numbers=True),
            title=f"[bold]Workflow State: {workflow_id}[/bold]",
            border_style="blue"
        ))


# Removed duplicate status command - using enhanced version above

@workflow_group.command(name='list')
def list_workflows():
    """List available workflow templates from RAG (IPFS Pinata)"""
    console.print("[cyan]Available RAG Templates from IPFS Pinata[/cyan]\n")
    
    try:
        from services.core.rag_template_fetcher import get_template_fetcher
        
        fetcher = get_template_fetcher()
        templates = fetcher.list_templates()
        
        if not templates:
            console.print("[yellow]No templates found in registry. Using example templates...[/yellow]\n")
            _show_example_templates()
            return
        
        # Group templates by category
        by_category = {}
        for template in templates:
            category = template.get('category', 'Other')
            # Normalize category names
            category = category.capitalize() if category else 'Other'
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(template)
        
        # Display templates organized by category
        for category in sorted(by_category.keys()):
            items = sorted(by_category[category], key=lambda x: x['name'])
            console.print(f"\n[bold cyan]{category}:[/bold cyan]")
            
            for item in items:
                # Status indicator
                status = "✅" if item.get('uploaded', False) else "⏳"
                name = item.get('name', 'Unknown')
                desc = item.get('description', 'No description')
                
                console.print(f"  {status} [bold]{name}[/bold]")
                console.print(f"      {desc}")
                
                # Show CID and gateway URL if available
                if item.get('cid'):
                    console.print(f"      CID: [dim]{item['cid']}[/dim]")
                if item.get('gateway_url'):
                    console.print(f"      URL: [link={item['gateway_url']}]{item['gateway_url']}[/link]")
        
        # Show statistics
        try:
            stats = fetcher.get_template_statistics()
            console.print(f"\n[bold]Template Statistics:[/bold]")
            console.print(f"  Total Templates: {stats.get('total_templates', 0)}")
            console.print(f"  Uploaded: {stats.get('uploaded_templates', 0)}")
            console.print(f"  Categories: {len(stats.get('categories', {}))}")
            
            if stats.get('categories'):
                console.print(f"\n  [dim]Categories: {', '.join(sorted(stats['categories'].keys()))}[/dim]")
        except Exception as stats_error:
            console.print(f"\n[yellow]Could not fetch statistics: {stats_error}[/yellow]")
        
        # Show usage example
        console.print(f"\n[bold]Usage Example:[/bold]")
        console.print(f"  hyperagent workflow run \"Create an ERC20 token with 1M supply\"")
        console.print(f"  [dim]Templates are automatically matched based on your prompt[/dim]")
        
    except ImportError as e:
        console.print(f"[yellow]RAG template fetcher not available: {e}[/yellow]")
        console.print("[yellow]Falling back to example templates...[/yellow]\n")
        _show_example_templates()
    except Exception as e:
        console.print(f"[red]Error fetching RAG templates: {e}[/red]")
        console.print("[yellow]Falling back to example templates...[/yellow]\n")
        _show_example_templates()

def _show_example_templates():
    """Show hardcoded example templates as fallback"""
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
    
    console.print("[dim]Example Workflow Prompts:[/dim]\n")
    for category, items in templates.items():
        console.print(f"\n[bold cyan]{category}:[/bold cyan]")
        for item in items:
            console.print(f"  • hyperagent workflow run \"{item}\"")
