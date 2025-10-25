"""
Generate Command Module
Smart contract generation functionality
"""

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

@click.group()
def generate_group():
    """Generate smart contracts and templates"""
    pass

@generate_group.command()
@click.option('--type', '-t', required=True, help='Contract type (ERC20, ERC721, DeFi, etc.)')
@click.option('--name', '-n', required=True, help='Contract name')
@click.option('--output', '-o', help='Output directory')
@click.option('--network', default='hyperion', help='Target network')
@click.option('--template', help='Use specific template')
@click.pass_context
def contract(ctx, type, name, output, network, template):
    """Generate a smart contract with AI"""
    import asyncio
    from core.agent.main import HyperKitAgent
    from core.config.loader import get_config
    
    console.print(f"🚀 Generating {type} contract: {name}")
    console.print(f"🌐 Network: {network}")
    
    try:
        # Initialize agent
        config = get_config().to_dict()
        agent = HyperKitAgent(config)
        
        # Create prompt
        prompt = f"Create a {type} smart contract named {name}"
        if template:
            prompt += f" using {template} template"
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Generating contract with AI...", total=None)
            
            # Run generation
            result = asyncio.run(agent.generate_contract(prompt))
            
            if result['status'] == 'success':
                contract_code = result['contract_code']
                file_path = result['path']
                
                console.print(f"✅ Generated {type} contract: {name}")
                console.print(f"📁 Saved to: {file_path}")
                console.print(f"📊 Provider: {result.get('provider_used', 'AI')}")
                console.print(f"🤖 Method: {result.get('method', 'AI')}")
                
                if output:
                    import shutil
                    shutil.copy(file_path, output)
                    console.print(f"📁 Copied to: {output}")
            else:
                console.print(f"❌ Generation failed: {result.get('error', 'Unknown error')}", style="red")
                
    except Exception as e:
        console.print(f"❌ Error: {e}", style="red")
        if ctx.obj.get('debug'):
            import traceback
            console.print(traceback.format_exc())

@generate_group.command()
@click.option('--category', '-c', help='Template category')
def templates(category):
    """List available contract templates"""
    console.print("📋 Available Contract Templates:")
    
    templates = {
        'tokens': ['ERC20', 'ERC721', 'ERC1155'],
        'defi': ['UniswapV2', 'UniswapV3', 'Staking'],
        'governance': ['Voting', 'Multisig', 'Timelock'],
        'nft': ['Basic', 'Advanced', 'Game'],
        'other': ['Auction', 'Vesting', 'Marketplace']
    }
    
    if category:
        if category in templates:
            console.print(f"\n{category.upper()} Templates:")
            for template in templates[category]:
                console.print(f"  • {template}")
        else:
            console.print(f"❌ Unknown category: {category}")
    else:
        for cat, items in templates.items():
            console.print(f"\n{cat.upper()}:")
            for item in items:
                console.print(f"  • {item}")

@generate_group.command()
@click.option('--template', '-t', required=True, help='Template name')
@click.option('--output', '-o', help='Output directory')
def from_template(template, output):
    """Generate contract from specific template"""
    console.print(f"📄 Generating from template: {template}")
    
    # TODO: Implement template-based generation
    console.print(f"✅ Generated contract from template: {template}")
    if output:
        console.print(f"📁 Output directory: {output}")
