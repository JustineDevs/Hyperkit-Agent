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
from cli.commands.batch_audit import batch_audit_group
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
    HyperAgent - AI-Powered Smart Contract Development Platform
    
    HyperAgent combines AI-powered contract generation, comprehensive auditing,
    and seamless deployment for the Hyperion ecosystem.
    
    PRODUCTION MODE vs SAFE MODE:
    - PRODUCTION MODE: All dependencies available, full functionality
    - SAFE MODE: Missing dependencies, operations blocked with clear errors
    
    Check your mode: hyperagent status
    
    For detailed documentation: https://github.com/JustineDevs/HyperAgent
    """
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    ctx.obj['debug'] = debug
    
    if verbose:
        console.print("Verbose mode enabled", style="blue")
    if debug:
        console.print("Debug mode enabled", style="yellow")

# Add command groups
cli.add_command(generate_group, name='generate')
cli.add_command(deploy_group, name='deploy')
cli.add_command(audit_group, name='audit')
cli.add_command(batch_audit_group, name='batch-audit')
cli.add_command(verify_group, name='verify')
cli.add_command(monitor_group, name='monitor')
cli.add_command(config_group, name='config')
cli.add_command(workflow_group, name='workflow')

# Add utility commands
@cli.command()
def status():
    """Check system health and production mode status"""
    from cli.utils.health import health_check
    health_check()

@cli.command()
def version():
    """Show version information"""
    show_version()

@cli.command()
def test_rag():
    """Test IPFS Pinata RAG connections (Obsidian removed - IPFS Pinata exclusive)"""
    test_rag_command()

@cli.command()
def limitations():
    """Show all known limitations and broken features"""
    from cli.utils.limitations import show_limitations
    show_limitations()

if __name__ == '__main__':
    cli()
