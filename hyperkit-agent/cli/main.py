#!/usr/bin/env python3
"""
HyperAgent CLI - Main Entry Point
Clean, modular CLI structure for production deployment
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv
import click
from rich.console import Console

# Load environment variables
load_dotenv()
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import CLI modules
from cli.commands.generate import generate_group
from cli.commands.deploy import deploy_group
from cli.commands.audit import audit_group
from cli.commands.verify import verify_group
from cli.commands.monitor import monitor_group
from cli.commands.config import config_group
from cli.commands.workflow import workflow_group
from cli.commands.test_rag import test_rag_command
from cli.utils.health import health_check
from cli.utils.version import show_version

console = Console()

@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.option('--debug', '-d', is_flag=True, help='Enable debug mode')
@click.pass_context
def cli(ctx, verbose, debug):
    """
    HyperAgent - Professional Web3 Development Platform
    
    Comprehensive smart contract generation, auditing, deployment, and management
    Production-ready with monitoring, caching, and error handling
    """
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    ctx.obj['debug'] = debug
    
    if verbose:
        console.print("🔍 Verbose mode enabled", style="blue")
    if debug:
        console.print("🐛 Debug mode enabled", style="yellow")

# Add command groups
cli.add_command(generate_group, name='generate')
cli.add_command(deploy_group, name='deploy')
cli.add_command(audit_group, name='audit')
cli.add_command(verify_group, name='verify')
cli.add_command(monitor_group, name='monitor')
cli.add_command(config_group, name='config')
cli.add_command(workflow_group, name='workflow')

# Add utility commands
@cli.command()
def health():
    """Check system health and status"""
    health_check()

@cli.command()
def version():
    """Show version information"""
    show_version()

@cli.command()
def test_rag():
    """Test RAG connections (Obsidian, IPFS, Local)"""
    test_rag_command()

if __name__ == '__main__':
    cli()
