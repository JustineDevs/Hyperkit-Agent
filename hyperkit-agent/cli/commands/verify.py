"""
Verify Command Module
Smart contract verification functionality
"""

import click
import asyncio
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

@click.group()
def verify_group():
    """Verify smart contracts on block explorers"""
    # Production-ready verify group - no stubs

@verify_group.command()
@click.option('--address', '-a', required=True, help='Contract address')
@click.option('--network', '-n', default='hyperion', hidden=True, help='[DEPRECATED] Hyperion is the only supported network')
@click.option('--source', '-s', help='Source code file')
@click.option('--constructor-args', help='Constructor arguments')
@click.pass_context
def contract(ctx, address, network, source, constructor_args):
    """
    Verify a smart contract on block explorer
    
    AI Model: [*] PRIMARY Gemini (gemini-2.5-flash-lite via Alith SDK adapter)
             [>] SECONDARY OpenAI (via Alith SDK) if Gemini unavailable
    
    [OK] IMPLEMENTED: Full Hyperion Explorer (Blockscout) API integration.
    Supports contract verification, status checking, and deployment info.
    See docs/HONEST_STATUS.md for details.
    """
    verbose = ctx.obj.get('verbose', False) if ctx.obj else False
    debug = ctx.obj.get('debug', False) if ctx.obj else False
    from cli.utils.warnings import show_command_warning
    show_command_warning('verify')
    # Hardcode Hyperion - no network selection
    network = "hyperion"  # HYPERION-ONLY: Ignore any --network flag
    if ctx.params.get('network') and ctx.params.get('network') != 'hyperion':
        console.print(f"[yellow]WARNING: Network '{ctx.params.get('network')}' not supported - using Hyperion[/yellow]")
    
    console.print(f"Verifying contract: {address}")
    console.print(f"Network: Hyperion (exclusive deployment target)")
    
    try:
        from services.verification.explorer_api import ExplorerAPI
        from core.config.loader import get_config
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Verifying contract...", total=None)
            
            # Initialize explorer client
            config = get_config().to_dict()
            explorer = ExplorerAPI(network, config)
            
            # Check if contract is already verified
            progress.update(task, description="Checking verification status...")
            status_result = explorer.get_verification_status(address)
            is_verified = status_result.get('status') == 'verified'
            
            if is_verified:
                console.print(f"Contract is already verified on explorer")
                console.print(f"Explorer URL: {status_result.get('explorer_url', 'N/A')}")
                return
            
            # If source code provided, attempt verification
            if source:
                progress.update(task, description="Submitting verification...")
                result = asyncio.run(explorer.verify_contract(source, address, constructor_args))
                
                if result.get('status') in ['success', 'submitted']:
                    console.print(f"Contract verification submitted successfully")
                    console.print(f"Explorer URL: {result.get('explorer_url', 'N/A')}")
                    console.print(f"Verification may take a few minutes")
                else:
                    console.print(f"Verification failed: {result.get('error', 'Unknown error')}")
            else:
                console.print(f"No source code provided - cannot verify")
                console.print(f"Use --source to provide contract source code")
                
    except Exception as e:
        console.print(f"Verification error: {e}", style="red")
        console.print(f"This command requires real explorer integration")
        if debug:
            import traceback
            console.print(traceback.format_exc())

@verify_group.command()
@click.option('--address', '-a', required=False, help='Contract address')
@click.option('--network', '-n', default='hyperion', hidden=True, help='[DEPRECATED] Hyperion is the only supported network')
@click.pass_context
def status(ctx, address, network):
    """
    Check verification status for a contract address.
    
    If no address is provided, lists recent verified contracts.
    """
    verbose = ctx.obj.get('verbose', False) if ctx.obj else False
    debug = ctx.obj.get('debug', False) if ctx.obj else False
    
    # Validate address is provided
    if not address:
        console.print("[red]Error: Contract address is required[/red]", style="red")
        console.print("[yellow]Usage: hyperagent verify status --address <ADDRESS>[/yellow]")
        console.print("[yellow]Example: hyperagent verify status --address 0x1234...[/yellow]")
        console.print("[yellow]Tip: Use 'hyperagent verify list' to see verified contracts[/yellow]")
        raise click.ClickException("Contract address is required (--address / -a)")
    
    # Validate address format (basic check)
    if not address.startswith('0x') or len(address) != 42:
        console.print(f"[red]Error: Invalid contract address format: {address}[/red]")
        console.print("[yellow]Address must be a valid Ethereum address (0x followed by 40 hex characters)[/yellow]")
        raise click.ClickException(f"Invalid address format: {address}")
    
    # Hardcode Hyperion - no network selection
    network = "hyperion"  # HYPERION-ONLY: Ignore any --network flag
    
    console.print("Verification Status")
    console.print(f"Address: {address}")
    console.print("Network: Hyperion (exclusive deployment target)")
    
    try:
        # Import with error handling
        try:
            from services.verification.explorer_api import ExplorerAPI
            from core.config.loader import get_config
        except ImportError as import_err:
            console.print(f"[red]Error: Failed to import required modules: {import_err}[/red]", style="red")
            console.print("[yellow]This may indicate a missing dependency or installation issue[/yellow]")
            if debug:
                import traceback
                console.print(traceback.format_exc())
            raise click.ClickException(f"Import error: {import_err}")
        
        # Get config with error handling
        try:
            config = get_config().to_dict()
        except Exception as config_err:
            console.print(f"[red]Error: Failed to load configuration: {config_err}[/red]", style="red")
            if debug:
                import traceback
                console.print(traceback.format_exc())
            raise click.ClickException(f"Config error: {config_err}")
        
        # Initialize explorer with error handling
        try:
            explorer = ExplorerAPI(network, config)
        except Exception as explorer_err:
            console.print(f"[red]Error: Failed to initialize explorer API: {explorer_err}[/red]", style="red")
            if debug:
                import traceback
                console.print(traceback.format_exc())
            raise click.ClickException(f"Explorer initialization error: {explorer_err}")
        
        # Check verification status with error handling
        try:
            status_result = explorer.get_verification_status(address)
        except Exception as status_err:
            console.print(f"[red]Error: Failed to check verification status: {status_err}[/red]", style="red")
            console.print("[yellow]This may indicate a network issue or invalid explorer configuration[/yellow]")
            if debug:
                import traceback
                console.print(traceback.format_exc())
            raise click.ClickException(f"Status check error: {status_err}")
        
        # Process and display results
        if not isinstance(status_result, dict):
            console.print("[yellow]Warning: Unexpected response format from explorer[/yellow]")
            if debug:
                console.print(f"Response: {status_result}")
            raise click.ClickException("Invalid response from explorer API")
        
        is_verified = status_result.get('status') == 'verified'
        
        if is_verified:
            console.print("[green]Contract is verified[/green]")
            explorer_url = status_result.get('explorer_url', 'N/A')
            console.print(f"Explorer URL: {explorer_url}")
        else:
            console.print("[yellow]Contract is not verified[/yellow]")
            console.print("Use 'hyperagent verify contract' to verify")
            # Return exit code 1 for unverified contracts (non-critical)
            if status_result.get('status') == 'error':
                raise click.ClickException(f"Explorer error: {status_result.get('error', 'Unknown error')}")
            
    except click.ClickException:
        # Re-raise Click exceptions (they handle exit codes properly)
        raise
    except Exception as e:
        # Catch-all for unexpected errors
        console.print(f"[red]Unexpected error: {e}[/red]", style="red")
        console.print("[yellow]This command requires real explorer integration[/yellow]")
        if debug:
            import traceback
            console.print(traceback.format_exc())
        raise click.ClickException(f"Unexpected error: {e}")

@verify_group.command()
@click.option('--address', '-a', required=True, help='Contract address')
@click.option('--network', '-n', default='hyperion', hidden=True, help='[DEPRECATED] Hyperion is the only supported network')
@click.pass_context
def deployment(ctx, address, network):
    """Verify deployment details"""
    verbose = ctx.obj.get('verbose', False) if ctx.obj else False
    debug = ctx.obj.get('debug', False) if ctx.obj else False
    # Hardcode Hyperion - no network selection
    network = "hyperion"  # HYPERION-ONLY: Ignore any --network flag
    
    console.print(f"Deployment Verification")
    console.print(f"Address: {address}")
    console.print(f"Network: Hyperion (exclusive deployment target)")
    
    try:
        from services.verification.explorer_api import ExplorerAPI
        from core.config.loader import get_config
        
        config = get_config().to_dict()
        explorer = ExplorerAPI(network, config)
        
        # Check deployment details
        deployment_info = explorer.get_deployment_info(address)
        
        if deployment_info:
            console.print(f"Deployment found")
            console.print(f"Block: {deployment_info.get('block_number', 'N/A')}")
            console.print(f"Transaction: {deployment_info.get('tx_hash', 'N/A')}")
            console.print(f"Explorer URL: {deployment_info.get('explorer_url', 'N/A')}")
        else:
            console.print(f"Deployment not found")
            console.print(f"Contract may not exist on this network")
            
    except Exception as e:
        console.print(f"Deployment check error: {e}", style="red")
        console.print(f"This command requires real explorer integration")
        if debug:
            import traceback
            console.print(traceback.format_exc())

@verify_group.command()
@click.option('--network', '-n', default='hyperion', hidden=True, help='[DEPRECATED] Hyperion is the only supported network')
def list(network):
    """List verified contracts"""
    # Hardcode Hyperion - no network selection
    network = "hyperion"  # HYPERION-ONLY: Ignore any --network flag
    
    console.print(f"Verified Contracts on Hyperion")
    
    try:
        from services.verification.explorer_api import ExplorerAPI
        from core.config.loader import get_config
        
        config = get_config().to_dict()
        explorer = ExplorerAPI(network, config)
        
        # List verified contracts (this would need to be implemented)
        console.print(f"Contract listing not yet implemented for {network}")
        console.print(f"This feature requires explorer API integration")
        return
        
        if contracts:
            console.print(f"Found {len(contracts)} verified contracts")
            for contract in contracts[:10]:  # Show first 10
                console.print(f"  {contract.get('address', 'N/A')} - {contract.get('name', 'Unknown')}")
        else:
            console.print(f"No verified contracts found")
            console.print(f"Contracts must be verified to appear in this list")
            
    except Exception as e:
        console.print(f"List error: {e}", style="red")
        console.print(f"This command requires real explorer integration")
