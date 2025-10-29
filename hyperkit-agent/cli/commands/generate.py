"""
Generate Command Module
Smart contract generation functionality with RAG template integration
"""

import asyncio
import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from pathlib import Path

console = Console()

@click.group()
def generate_group():
    """Generate smart contracts and templates"""
    pass

@generate_group.command()
@click.option('--type', '-t', required=True, help='Contract type (ERC20, ERC721, DeFi, etc.)')
@click.option('--name', '-n', required=True, help='Contract name')
@click.option('--output', '-o', help='Output directory')
@click.option('--network', default='hyperion', hidden=True, help='[DEPRECATED] Hyperion is the only supported network')
@click.option('--template', help='Use specific template')
@click.option('--use-rag/--no-use-rag', default=True, help='Use RAG templates for enhanced context')
@click.pass_context
def contract(ctx, type, name, output, network, template, use_rag):
    """Generate a smart contract with AI using RAG templates for context"""
    from core.agent.main import HyperKitAgent
    from core.config.loader import get_config
    from services.core.rag_template_fetcher import get_template
    
    # Hardcode Hyperion - no network selection
    network = "hyperion"  # HYPERION-ONLY: Ignore any --network flag
    if ctx.params.get('network') and ctx.params.get('network') != 'hyperion':
        console.print(f"[yellow]WARNING: Network '{ctx.params.get('network')}' not supported - using Hyperion[/yellow]")
    
    console.print(f"Generating {type} contract: {name}")
    console.print(f"Network: Hyperion (exclusive deployment target)")
    
    try:
        # Initialize agent
        config = get_config().to_dict()
        agent = HyperKitAgent(config)
        
        # Build enhanced prompt with RAG templates if enabled
        base_prompt = f"Create a {type} smart contract named {name}"
        enhanced_prompt = base_prompt
        
        if use_rag:
            console.print("Fetching RAG templates for enhanced context...", style="blue")
            try:
                # Get contract generation prompt template
                generation_prompt = asyncio.run(get_template('contract-generation-prompt'))
                
                # Get appropriate contract template
                template_name = template or f"{type.lower()}-template"
                contract_template = asyncio.run(get_template(template_name))
                
                # Compose enhanced prompt
                if generation_prompt and contract_template:
                    enhanced_prompt = f"""{generation_prompt}

Contract Type: {type}
Contract Name: {name}
Network: {network}

Requirements:
{base_prompt}

Reference Template:
{contract_template}
"""
                    console.print("RAG context loaded successfully", style="green")
                elif generation_prompt:
                    enhanced_prompt = f"""{generation_prompt}

Contract Type: {type}
Contract Name: {name}
Network: {network}

Requirements:
{base_prompt}
"""
                    console.print("RAG generation prompt loaded", style="green")
                else:
                    console.print("RAG templates unavailable, using base prompt", style="yellow")
                    enhanced_prompt = base_prompt
            except Exception as rag_error:
                console.print(f"RAG fetch failed: {rag_error}", style="yellow")
                enhanced_prompt = base_prompt
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Generating contract with AI...", total=None)
            
            # Run generation
            result = asyncio.run(agent.generate_contract(enhanced_prompt))
            
            if result['status'] == 'success':
                contract_code = result['contract_code']
                file_path = result['path']
                
                console.print(f"Generated {type} contract: {name}")
                console.print(f"Saved to: {file_path}")
                console.print(f"Provider: {result.get('provider_used', 'AI')}")
                console.print(f"Method: {result.get('method', 'AI')}")
                
                if output:
                    import shutil
                    shutil.copy(file_path, output)
                    console.print(f"Copied to: {output}")
            else:
                console.print(f"Generation failed: {result.get('error', 'Unknown error')}", style="red")
                
    except Exception as e:
        console.print(f"Error: {e}", style="red")
        if ctx.obj.get('debug'):
            import traceback
            console.print(traceback.format_exc())

@generate_group.command()
@click.option('--category', '-c', help='Template category')
def templates(category):
    """List available contract templates"""
    console.print("Available Contract Templates:")
    
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
            console.print(f"Unknown category: {category}")
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
    console.print(f"Generating from template: {template}")
    
    # TODO: Implement template-based generation
    console.print(f"Generated contract from template: {template}")
    if output:
        console.print(f"Output directory: {output}")
