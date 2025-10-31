"""
Config Command Module
Configuration management functionality
"""

import click
import json
import os
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

@click.group()
def config_group():
    """
    Manage configuration settings
    
    ⚠️  WARNING: This command has partial implementation - some features may be limited.
    See docs/HONEST_STATUS.md for details.
    """
    from cli.utils.warnings import show_command_warning
    show_command_warning('config')
    pass

@config_group.command()
@click.option('--key', '-k', help='Configuration key')
@click.option('--value', '-v', help='Configuration value')
@click.pass_context
def set(ctx, key, value):
    """Set configuration value"""
    verbose = ctx.obj.get('verbose', False) if ctx.obj else False
    debug = ctx.obj.get('debug', False) if ctx.obj else False
    if key and value:
        console.print(f"Setting {key} = {value}")
        
        try:
            # Load current config
            config_file = Path("config.yaml")
            config_data = {}
            
            if config_file.exists():
                import yaml
                with open(config_file, 'r') as f:
                    config_data = yaml.safe_load(f) or {}
            
            # Set the value
            config_data[key] = value
            
            # Save back to file
            import yaml
            with open(config_file, 'w') as f:
                yaml.dump(config_data, f, default_flow_style=False)
            
            console.print(f"Configuration updated: {key} = {value}")
            
        except ImportError:
            console.print(f"PyYAML not available - install with: pip install pyyaml")
        except Exception as e:
            console.print(f"Config error: {e}", style="red")
            if ctx.obj.get('debug', False) if ctx.obj else False:
                import traceback
                console.print(traceback.format_exc())
    else:
        console.print("Please provide both key and value")
        console.print("Usage: hyperagent config set --key <key> --value <value>")

@config_group.command(name='foundry-check')
def foundry_check():
    """Check Foundry version status and diagnose issues"""
    try:
        from services.deployment.foundry_manager import FoundryManager
        from rich.table import Table
        
        console.print("[bold cyan]Foundry Version Diagnostic[/bold cyan]\n")
        
        fm = FoundryManager()
        status = fm.get_version_status()
        
        # Create diagnostic table
        table = Table(title="Foundry Version Status", show_header=True, header_style="bold magenta")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="yellow")
        table.add_column("Status", style="green")
        
        # Installation status
        table.add_row(
            "Installed",
            "Yes" if status["installed"] else "No",
            "✅" if status["installed"] else "❌"
        )
        
        # Current version
        table.add_row(
            "Current Version",
            status["current_version"] or "Unknown",
            "⚠️" if status["is_nightly"] else "✅"
        )
        
        # Expected version
        table.add_row(
            "Expected Version Hint",
            status["expected_version_hint"],
            "✅" if not status["version_mismatch"] else "⚠️"
        )
        
        # Nightly build
        table.add_row(
            "Is Nightly Build",
            "Yes" if status["is_nightly"] else "No",
            "❌" if status["is_nightly"] else "✅"
        )
        
        # Version mismatch
        table.add_row(
            "Version Mismatch",
            "Yes" if status["version_mismatch"] else "No",
            "⚠️" if status["version_mismatch"] else "✅"
        )
        
        # Strict mode
        table.add_row(
            "Strict Mode Enabled",
            "Yes" if status["strict_mode"] else "No",
            "⚠️" if status["strict_mode"] and (status["is_nightly"] or status["version_mismatch"]) else "✅"
        )
        
        # Would refuse deploy
        table.add_row(
            "Would Refuse Deploy",
            "Yes" if status["should_refuse"] else "No",
            "❌" if status["should_refuse"] else "✅"
        )
        
        # Forge path
        table.add_row(
            "Forge Path",
            status["forge_path"] or "Not found",
            "✅" if status["forge_path"] else "❌"
        )
        
        console.print(table)
        
        # Provide recommendations
        console.print("\n[bold yellow]Recommendations:[/bold yellow]\n")
        
        if not status["installed"]:
            console.print("[red]❌ Foundry is not installed or not in PATH[/red]")
            console.print("  → Install Foundry: curl -L https://foundry.paradigm.xyz | bash")
            console.print("  → Run: foundryup")
        elif status["is_nightly"]:
            console.print("[yellow]⚠️  Nightly build detected - unstable for production[/yellow]")
            console.print("  → Install stable version:")
            console.print("    1. Find all forge binaries: which -a forge")
            console.print("    2. Remove nightly: rm -f ~/.foundry/bin/forge (if in that path)")
            console.print("    3. Install stable: foundryup")
            console.print("    4. Verify: forge --version")
            console.print("  → On Windows: Download stable from https://github.com/foundry-rs/foundry/releases")
        elif status["version_mismatch"]:
            console.print("[yellow]⚠️  Version mismatch detected[/yellow]")
            console.print(f"  → Current: {status['current_version']}")
            console.print(f"  → Expected hint: {status['expected_version_hint']}")
            console.print("  → Fix by:")
            console.print("    1. Check PATH: which -a forge")
            console.print("    2. Install matching version: foundryup")
            console.print("    3. Or update HYPERAGENT_FORGE_VERSION env var")
        elif status["should_refuse"]:
            console.print("[red]❌ Deployment would be refused in strict mode[/red]")
            console.print("  → Either fix Foundry version OR disable strict mode:")
            console.print("     export HYPERAGENT_STRICT_FORGE=0  # Not recommended")
        else:
            console.print("[green]✅ Foundry version looks good![/green]")
            console.print("  → No issues detected - ready for deployment")
    except Exception as e:
        console.print(f"[red]Error checking Foundry version: {e}[/red]")
        import traceback
        if os.getenv("DEBUG"):
            console.print(traceback.format_exc())

@config_group.command()
@click.argument('key', required=False)
@click.pass_context
def get(ctx, key):
    """Get configuration value"""
    verbose = ctx.obj.get('verbose', False) if ctx.obj else False
    debug = ctx.obj.get('debug', False) if ctx.obj else False
    try:
        config_file = Path("config.yaml")
        
        if not config_file.exists():
            console.print(f"No configuration file found at {config_file}")
            console.print(f"Use 'hyperagent config set' to create configuration")
            return
        
        import yaml
        with open(config_file, 'r') as f:
            config_data = yaml.safe_load(f) or {}
        
        if key:
            console.print(f"Getting {key}")
            if key in config_data:
                console.print(f"{key} = {config_data[key]}")
            else:
                console.print(f"Key '{key}' not found in configuration")
        else:
            console.print("All configuration values:")
            if config_data:
                for k, v in config_data.items():
                    console.print(f"  {k} = {v}")
            else:
                console.print("  (no configuration values set)")
            console.print(f"\nConfiguration displayed")
            
    except ImportError:
        console.print(f"PyYAML not available - install with: pip install pyyaml")
    except Exception as e:
        console.print(f"Config error: {e}", style="red")

@config_group.command()
@click.pass_context
def list(ctx):
    """List all configuration values"""
    verbose = ctx.obj.get('verbose', False) if ctx.obj else False
    debug = ctx.obj.get('debug', False) if ctx.obj else False
    try:
        config_file = Path("config.yaml")
        
        if not config_file.exists():
            console.print(f"No configuration file found at {config_file}")
            console.print(f"Use 'hyperagent config reset' to create default configuration")
            return
        
        import yaml
        with open(config_file, 'r') as f:
            config_data = yaml.safe_load(f) or {}
        
        console.print("Configuration values:")
        if config_data:
            for k, v in config_data.items():
                console.print(f"  {k} = {v}")
        else:
            console.print("  (no configuration values set)")
            
    except ImportError:
        console.print(f"PyYAML not available - install with: pip install pyyaml")
    except Exception as e:
        console.print(f"Config error: {e}", style="red")

@config_group.command()
@click.pass_context
def reset(ctx):
    """Reset configuration to defaults"""
    verbose = ctx.obj.get('verbose', False) if ctx.obj else False
    debug = ctx.obj.get('debug', False) if ctx.obj else False
    console.print("Resetting configuration to defaults")
    
    try:
        config_file = Path("config.yaml")
        
        # Create default configuration (Hyperion-only)
        default_config = {
            "networks": {
                "hyperion": {
                    "rpc_url": "https://hyperion-testnet.metisdevops.link",
                    "chain_id": 133717,
                    "explorer_url": "https://hyperion-testnet-explorer.metisdevops.link",
                    "status": "testnet",
                    "default": True
                }
            },
            "ai_providers": {
                "openai": {
                    "api_key": "",
                    "model": "gpt-4"
                },
                "google": {
                    "api_key": "",
                    "model": "gemini-pro"
                },
                "anthropic": {
                    "api_key": "",
                    "model": "claude-3-sonnet"
                }
            },
            "security": {
                "private_key": "",
                "enable_audit": True,
                "enable_verification": True
            }
        }
        
        import yaml
        with open(config_file, 'w') as f:
            yaml.dump(default_config, f, default_flow_style=False)
        
        console.print(f"Configuration reset to defaults")
        console.print(f"Configuration file: {config_file.absolute()}")
        
    except ImportError:
        console.print(f"PyYAML not available - install with: pip install pyyaml")
    except Exception as e:
        console.print(f"Config error: {e}", style="red")

@config_group.command()
@click.option('--file', '-f', help='Configuration file path')
@click.pass_context
def load(ctx, file):
    """Load configuration from file"""
    verbose = ctx.obj.get('verbose', False) if ctx.obj else False
    debug = ctx.obj.get('debug', False) if ctx.obj else False
    if not file:
        console.print("Please provide a file path")
        console.print("Usage: hyperagent config load --file <path>")
        return
    
    console.print(f"Loading configuration from: {file}")
    
    try:
        source_file = Path(file)
        target_file = Path("config.yaml")
        
        if not source_file.exists():
            console.print(f"Source file not found: {source_file}")
            return
        
        import yaml
        with open(source_file, 'r') as f:
            config_data = yaml.safe_load(f)
        
        with open(target_file, 'w') as f:
            yaml.dump(config_data, f, default_flow_style=False)
        
        console.print(f"Configuration loaded from {source_file}")
        console.print(f"Active configuration: {target_file.absolute()}")
        
    except ImportError:
        console.print(f"PyYAML not available - install with: pip install pyyaml")
    except Exception as e:
        console.print(f"Config error: {e}", style="red")

@config_group.command()
@click.option('--file', '-f', help='Configuration file path')
@click.pass_context
def save(ctx, file):
    """Save configuration to file"""
    verbose = ctx.obj.get('verbose', False) if ctx.obj else False
    debug = ctx.obj.get('debug', False) if ctx.obj else False
    if not file:
        console.print("Please provide a file path")
        console.print("Usage: hyperagent config save --file <path>")
        return
    
    console.print(f"Saving configuration to: {file}")
    
    try:
        source_file = Path("config.yaml")
        target_file = Path(file)
        
        if not source_file.exists():
            console.print(f"No active configuration found at {source_file}")
            console.print(f"Use 'hyperagent config reset' to create default configuration")
            return
        
        import yaml
        with open(source_file, 'r') as f:
            config_data = yaml.safe_load(f)
        
        with open(target_file, 'w') as f:
            yaml.dump(config_data, f, default_flow_style=False)
        
        console.print(f"Configuration saved to {target_file}")
        console.print(f"Source configuration: {source_file.absolute()}")
        
    except ImportError:
        console.print(f"PyYAML not available - install with: pip install pyyaml")
    except Exception as e:
        console.print(f"Config error: {e}", style="red")
