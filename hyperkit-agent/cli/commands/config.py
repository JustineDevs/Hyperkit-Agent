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
    """Manage configuration settings"""
    pass

@config_group.command()
@click.option('--key', '-k', help='Configuration key')
@click.option('--value', '-v', help='Configuration value')
def set(key, value):
    """Set configuration value"""
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
    else:
        console.print("Please provide both key and value")
        console.print("Usage: hyperagent config set --key <key> --value <value>")

@config_group.command()
@click.argument('key', required=False)
def get(key):
    """Get configuration value"""
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
def list():
    """List all configuration values"""
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
def reset():
    """Reset configuration to defaults"""
    console.print("Resetting configuration to defaults")
    
    try:
        config_file = Path("config.yaml")
        
        # Create default configuration
        default_config = {
            "networks": {
                "hyperion": {
                    "rpc_url": "https://hyperion-testnet.metisdevops.link",
                    "chain_id": 1001,
                    "explorer_url": "https://hyperion-testnet-explorer.metisdevops.link"
                },
                "ethereum": {
                    "rpc_url": "https://eth-mainnet.g.alchemy.com/v2/YOUR_KEY",
                    "chain_id": 1,
                    "explorer_url": "https://etherscan.io"
                }
            },
            "ai_providers": {
                "openai_api_key": "",
                "google_api_key": "",
                "lazai_rsa_private_key": ""
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
def load(file):
    """Load configuration from file"""
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
def save(file):
    """Save configuration to file"""
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
