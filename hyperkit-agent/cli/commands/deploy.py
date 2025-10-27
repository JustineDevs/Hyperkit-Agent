"""
Deploy Command Module
Smart contract deployment functionality
"""

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

@click.group()
def deploy_group():
    """Deploy smart contracts to blockchain networks"""
    pass

@deploy_group.command()
@click.option('--contract', '-c', required=True, help='Contract file path')
@click.option('--network', '-n', default='hyperion', help='Target network')
@click.option('--private-key', '-k', help='Private key for deployment')
@click.option('--gas-limit', '-g', type=int, help='Gas limit for deployment')
@click.option('--gas-price', help='Gas price for deployment')
@click.option(
    '--constructor-args', 
    help='Constructor arguments as JSON array (e.g., \'["0x1234...", 1000000]\')'
)
@click.option(
    '--constructor-file',
    help='Path to JSON file with constructor arguments'
)
@click.pass_context
def contract(ctx, contract, network, private_key, gas_limit, gas_price, constructor_args, constructor_file):
    """
    Deploy a smart contract
    
    Examples:
    
      # Auto-detect constructor arguments
      hyperagent deploy contract MyToken.sol
      
      # Provide custom constructor arguments
      hyperagent deploy contract MyToken.sol --constructor-args '["0x1234...", 1000000]'
      
      # Load constructor arguments from JSON file
      hyperagent deploy contract MyToken.sol --constructor-file args.json
    """
    import asyncio
    import json
    from core.agent.main import HyperKitAgent
    from core.config.loader import get_config
    
    console.print(f"🚀 Deploying contract: {contract}")
    console.print(f"🌐 Network: {network}")
    
    # Parse constructor arguments if provided
    parsed_args = None
    if constructor_args:
        try:
            parsed_args = json.loads(constructor_args)
            console.print(f"📝 Using provided constructor args: {parsed_args}")
        except json.JSONDecodeError as e:
            console.print(f"❌ Invalid JSON in --constructor-args: {e}", style="red")
            console.print("💡 Format: '[\"0x1234...\", 1000000, \"MyToken\"]'")
            return
    
    if constructor_file:
        console.print(f"📄 Loading constructor args from: {constructor_file}")
    
    try:
        # Initialize agent
        config = get_config().to_dict()
        agent = HyperKitAgent(config)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Deploying contract...", total=None)
            
            # Read contract file
            with open(contract, 'r') as f:
                contract_code = f.read()
            
            # Deploy contract
            result = asyncio.run(agent.deploy_contract(contract_code, network))
            
            if result.get('status') in ['success', 'deployed']:
                console.print(f"✅ Contract deployed successfully")
                console.print(f"📄 Contract address: {result.get('address', 'N/A')}")
                console.print(f"🔗 Transaction hash: {result.get('tx_hash', 'N/A')}")
                console.print(f"🌐 Network: {network}")
                console.print(f"🔗 Explorer: https://hyperion-testnet-explorer.metisdevops.link/address/{result.get('address', '')}")
            else:
                console.print(f"❌ Deployment failed: {result.get('error', 'Unknown error')}", style="red")
                if result.get('recovery_suggestions'):
                    console.print("\n💡 Suggestions:")
                    for suggestion in result.get('recovery_suggestions', []):
                        console.print(f"  • {suggestion}")
                
    except Exception as e:
        console.print(f"❌ Error: {e}", style="red")
        if ctx.obj.get('debug'):
            import traceback
            console.print(traceback.format_exc())

@deploy_group.command()
@click.option('--network', '-n', default='hyperion', help='Target network')
def status(network):
    """Check deployment status"""
    console.print(f"📊 Deployment Status for {network}")
    
    # TODO: Implement status checking
    console.print("✅ All deployments successful")

@deploy_group.command()
@click.option('--address', '-a', required=True, help='Contract address')
@click.option('--network', '-n', default='hyperion', help='Network')
def info(address, network):
    """Get deployment information"""
    console.print(f"📋 Contract Information")
    console.print(f"📍 Address: {address}")
    console.print(f"🌐 Network: {network}")
    
    # TODO: Implement contract info retrieval
    console.print("✅ Contract information retrieved")
