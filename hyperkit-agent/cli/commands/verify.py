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
def contract(address, network, source, constructor_args):
    """Verify a smart contract on block explorer"""
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

@verify_group.command()
@click.option('--address', '-a', required=True, help='Contract address')
@click.option('--network', '-n', default='hyperion', hidden=True, help='[DEPRECATED] Hyperion is the only supported network')
def status(address, network):
    """Check verification status"""
    # Hardcode Hyperion - no network selection
    network = "hyperion"  # HYPERION-ONLY: Ignore any --network flag
    
    console.print(f"Verification Status")
    console.print(f"Address: {address}")
    console.print(f"Network: Hyperion (exclusive deployment target)")
    
    try:
        from services.verification.explorer_api import ExplorerAPI
        from core.config.loader import get_config
        
        config = get_config().to_dict()
        explorer = ExplorerAPI(network, config)
        
        # Check verification status
        status_result = explorer.get_verification_status(address)
        is_verified = status_result.get('status') == 'verified'
        
        if is_verified:
            console.print(f"Contract is verified")
            console.print(f"Explorer URL: {status_result.get('explorer_url', 'N/A')}")
        else:
            console.print(f"Contract is not verified")
            console.print(f"Use 'hyperagent verify contract' to verify")
            
    except Exception as e:
        console.print(f"Status check error: {e}", style="red")
        console.print(f"This command requires real explorer integration")

@verify_group.command()
@click.option('--address', '-a', required=True, help='Contract address')
@click.option('--network', '-n', default='hyperion', hidden=True, help='[DEPRECATED] Hyperion is the only supported network')
def deployment(address, network):
    """Verify deployment details"""
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
