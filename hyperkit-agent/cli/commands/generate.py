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
@click.argument('prompt', required=False)
@click.option('--type', '-t', help='Contract type (ERC20, ERC721, DeFi, etc.)')
@click.option('--name', '-n', help='Contract name')
@click.option('--output', '-o', help='Output directory')
@click.option('--network', default='hyperion', hidden=True, help='[DEPRECATED] Hyperion is the only supported network')
@click.option('--template', help='Use specific template')
@click.option('--use-rag/--no-use-rag', default=True, help='Use RAG templates for enhanced context')
@click.pass_context
def contract(ctx, prompt, type, name, output, network, template, use_rag):
    """
    Generate a smart contract with AI using RAG templates for context
    
    AI Model: [*] PRIMARY Gemini (gemini-2.5-flash-lite via Alith SDK adapter)
             [>] SECONDARY OpenAI (via Alith SDK) if Gemini unavailable
    
    ⚠️  WARNING: Templates are limited - many advanced templates not yet implemented.
    See docs/HONEST_STATUS.md for details.
    """
    from cli.utils.warnings import show_command_warning
    from cli.utils.interactive import prompt_for_missing_params
    show_command_warning('generate')
    from core.agent.main import HyperKitAgent
    from core.config.loader import get_config
    from services.core.rag_template_fetcher import get_template
    
    # CRITICAL FIX: Parse prompt if provided as argument
    # If prompt is provided, extract type and name from it
    if prompt:
        # Try to extract contract type and name from prompt
        prompt_lower = prompt.lower()
        if 'erc20' in prompt_lower:
            type = type or 'ERC20'
        elif 'erc721' in prompt_lower or 'nft' in prompt_lower:
            type = type or 'ERC721'
        elif 'erc1155' in prompt_lower:
            type = type or 'ERC1155'
        elif 'defi' in prompt_lower or 'staking' in prompt_lower or 'liquidity' in prompt_lower:
            type = type or 'DeFi'
        else:
            type = type or 'Custom'
        
        # Extract name from prompt if possible
        if not name:
            # Try to find a name in the prompt (e.g., "Create MyToken" -> "MyToken")
            import re
            name_match = re.search(r'\b([A-Z][a-zA-Z0-9]+)\b', prompt)
            if name_match:
                name = name_match.group(1)
    
    # Interactive prompts for missing required parameters
    if not type:
        try:
            import questionary
            contract_types = ['ERC20', 'ERC721', 'ERC1155', 'DeFi', 'Custom']
            type = questionary.select(
                "Select contract type",
                choices=contract_types
            ).ask()
        except ImportError:
            type = click.prompt("Contract type (ERC20, ERC721, DeFi, etc.)", type=str)
    
    if not name:
        try:
            import questionary
            name = questionary.text("Enter contract name").ask()
        except ImportError:
            name = click.prompt("Contract name", type=str)
    
    if not type or not name:
        console.print("[red]Contract type and name are required[/red]")
        console.print("[yellow]Usage: hyperagent generate contract [PROMPT] [OPTIONS][/yellow]")
        console.print("[yellow]Example: hyperagent generate contract 'Create a simple ERC20 token' --name MyToken[/yellow]")
        raise click.ClickException("Contract type and name are required")
    
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
        # Use provided prompt if available, otherwise build from type/name
        if prompt:
            base_prompt = prompt
        else:
            base_prompt = f"Create a {type} smart contract named {name}"
        enhanced_prompt = base_prompt
        
        if use_rag:
            console.print("Fetching RAG templates for enhanced context...", style="blue")
            try:
                # Get contract generation prompt template
                generation_prompt = asyncio.run(get_template('contract-generation-prompt'))
                
                # Get appropriate contract template
                template_name = template or f"{type.lower()}-template"
                
                # FIXED: Better error handling for missing templates
                contract_template = None
                try:
                    contract_template = asyncio.run(get_template(template_name))
                    if not contract_template:
                        console.print(f"Template '{template_name}' not found, continuing without template", style="yellow")
                except Exception as template_error:
                    console.print(f"Template '{template_name}' unavailable: {template_error}", style="yellow")
                    console.print("Continuing with generation prompt only", style="yellow")
                
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
    """List available contract templates from RAG (IPFS Pinata)"""
    console.print("[cyan]Available RAG Templates from IPFS Pinata[/cyan]\n")
    
    try:
        from services.core.rag_template_fetcher import get_template_fetcher
        
        fetcher = get_template_fetcher()
        all_templates = fetcher.list_templates()
        
        if not all_templates:
            console.print("[yellow]No templates found in registry. Using example templates...[/yellow]\n")
            _show_example_generate_templates(category)
            return
        
        # Filter by category if specified
        if category:
            filtered_templates = [
                t for t in all_templates 
                if t.get('category', '').lower() == category.lower()
            ]
            if not filtered_templates:
                console.print(f"[yellow]No templates found in category: {category}[/yellow]")
                console.print("[yellow]Available categories:[/yellow]")
                categories = set(t.get('category', 'Other') for t in all_templates)
                for cat in sorted(categories):
                    console.print(f"  • {cat}")
                return
            all_templates = filtered_templates
        
        # Group templates by category
        by_category = {}
        for template in all_templates:
            cat = template.get('category', 'Other')
            # Normalize category names
            cat = cat.capitalize() if cat else 'Other'
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(template)
        
        # Display templates organized by category
        for cat in sorted(by_category.keys()):
            items = sorted(by_category[cat], key=lambda x: x['name'])
            console.print(f"\n[bold cyan]{cat}:[/bold cyan]")
            
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
        
        # Show statistics if not filtering
        if not category:
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
        console.print(f"  hyperagent generate from-template --template erc20-template --name MyToken")
        console.print(f"  [dim]Templates are fetched from IPFS Pinata automatically[/dim]")
        
    except ImportError as e:
        console.print(f"[yellow]RAG template fetcher not available: {e}[/yellow]")
        console.print("[yellow]Falling back to example templates...[/yellow]\n")
        _show_example_generate_templates(category)
    except Exception as e:
        console.print(f"[red]Error fetching RAG templates: {e}[/red]")
        console.print("[yellow]Falling back to example templates...[/yellow]\n")
        _show_example_generate_templates(category)

def _show_example_generate_templates(category=None):
    """Show hardcoded example templates as fallback"""
    example_templates = {
        'tokens': ['ERC20', 'ERC721', 'ERC1155'],
        'defi': ['UniswapV2', 'UniswapV3', 'Staking'],
        'governance': ['Voting', 'Multisig', 'Timelock'],
        'nft': ['Basic', 'Advanced', 'Game'],
        'other': ['Auction', 'Vesting', 'Marketplace']
    }
    
    console.print("[dim]Example Contract Templates:[/dim]\n")
    
    if category:
        if category in example_templates:
            console.print(f"\n{category.upper()} Templates:")
            for template in example_templates[category]:
                console.print(f"  • {template}")
        else:
            console.print(f"[yellow]Unknown category: {category}[/yellow]")
            console.print(f"[yellow]Available categories: {', '.join(example_templates.keys())}[/yellow]")
    else:
        for cat, items in example_templates.items():
            console.print(f"\n[bold cyan]{cat.upper()}:[/bold cyan]")
            for item in items:
                console.print(f"  • {item}")

@generate_group.command()
@click.option('--template', '-t', required=True, help='Template name from IPFS RAG')
@click.option('--name', '-n', help='Contract name (optional)')
@click.option('--output', '-o', help='Output directory')
@click.option('--use-rag/--no-use-rag', default=True, help='Use RAG templates')
@click.pass_context
def from_template(ctx, template, name, output, use_rag):
    """
    Generate contract from specific template
    
    ⚠️  WARNING: This command fetches template from RAG but may not handle all template types.
    See docs/HONEST_STATUS.md for details.
    """
    from cli.utils.warnings import show_command_warning
    show_command_warning('generate')
    
    console.print(f"Generating contract from template: {template}")
    
    try:
        from services.core.rag_template_fetcher import get_template
        from core.agent.main import HyperKitAgent
        from core.config.loader import get_config
        import asyncio
        
        # Fetch template
        if use_rag:
            console.print(f"Fetching template '{template}' from RAG...", style="blue")
            try:
                template_content = asyncio.run(get_template(template))
                if not template_content:
                    console.print(f"[red]Template '{template}' not found in RAG[/red]")
                    console.print("[yellow]Available templates can be listed with: hyperagent generate templates[/yellow]")
                    ctx.exit(1)
                    return
            except Exception as e:
                console.print(f"[red]Failed to fetch template: {e}[/red]")
                console.print("[yellow]Check template name or RAG connection[/yellow]")
                ctx.exit(1)
                return
        else:
            console.print("[yellow]RAG disabled - cannot fetch template[/yellow]")
            ctx.exit(1)
            return
        
        # Initialize agent
        config = get_config().to_dict()
        agent = HyperKitAgent(config)
        
        # Build prompt from template
        contract_name = name or "Contract"
        prompt = f"""Generate a smart contract based on the following template:

Template:
{template_content}

Contract Name: {contract_name}
Please generate a complete, production-ready contract following the template structure and best practices.
"""
        
        # Generate contract
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Generating contract from template...", total=None)
            
            result = asyncio.run(agent.generate_contract(prompt))
            
            if result['status'] == 'success':
                file_path = result['path']
                console.print(f"[green]Generated contract from template: {template}[/green]")
                console.print(f"Saved to: {file_path}")
                
                if output:
                    import shutil
                    shutil.copy(file_path, output)
                    console.print(f"Copied to: {output}")
            else:
                console.print(f"[red]Generation failed: {result.get('error', 'Unknown error')}[/red]")
                ctx.exit(1)
    
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if ctx.obj.get('debug'):
            import traceback
            console.print(traceback.format_exc())
        ctx.exit(1)
