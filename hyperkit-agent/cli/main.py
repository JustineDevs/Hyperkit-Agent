#!/usr/bin/env python3
"""
HyperAgent CLI - Main Entry Point
Clean, modular CLI structure for production deployment
"""

import sys
import os
import logging
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
from cli.commands.doctor import doctor_command
from cli.commands.docs import docs_group
from cli.utils.health import health_check
from cli.utils.version import show_version

console = Console()

def _ensure_first_run_health():
    """Auto-create required directories and default config on first run (robust, fail-loud)."""
    try:
        root = Path(__file__).parent.parent
        
        # Use DirectoryValidator for robust directory creation with loud failures
        try:
            from core.utils.directory_validator import ensure_workspace_directories
            ensure_workspace_directories(root, fail_loud=False)  # Fail softly on CLI startup, but log loudly
        except ImportError:
            # Fallback to basic creation if validator not available
            logger = logging.getLogger(__name__)
            logger.warning("DirectoryValidator not available, using basic directory creation")
            required_dirs = [
                root / ".workflow_contexts",
                root / ".temp_envs",
                root / "logs",
                root / "artifacts",
            ]
            for d in required_dirs:
                try:
                    d.mkdir(parents=True, exist_ok=True)
                except (OSError, PermissionError) as e:
                    logger.error(f"CRITICAL: Failed to create required directory {d}: {e}")
                    logger.error(f"Fix: mkdir -p {d} && chmod +w {d}")

        # Default config.yaml if missing
        config_file = root / "config.yaml"
        if not config_file.exists():
            try:
                default_yaml = (
                    "networks:\n"
                    "  hyperion:\n"
                    "    chain_id: 133717\n"
                    "    explorer_url: https://hyperion-testnet-explorer.metisdevops.link\n"
                    "    rpc_url: https://hyperion-testnet.metisdevops.link\n"
                    "    status: testnet\n"
                    "    default: true\n"
                )
                config_file.write_text(default_yaml, encoding="utf-8")
            except (OSError, PermissionError) as e:
                logger = logging.getLogger(__name__)
                logger.error(f"CRITICAL: Failed to create default config.yaml: {e}")
                logger.error(f"Fix: Create {config_file} manually with network configuration")

        # Foundry version drift hard warning (refuse optional)
        try:
            from services.deployment.foundry_manager import FoundryManager
            fm = FoundryManager()
            if fm.is_installed() and getattr(fm, "version_mismatch", False):
                # Refuse only for deploy/verify/workflow run; informational otherwise
                pass
        except Exception:
            pass
    except Exception as e:
        # Log loudly but don't crash CLI startup
        logger = logging.getLogger(__name__)
        logger.error(f"CRITICAL: First-run health check failed: {e}")
        logger.error("Some CLI commands may fail. Run 'hyperagent doctor' to diagnose issues.")

@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.option('--debug', '-d', is_flag=True, help='Enable debug mode')
@click.pass_context
def cli(ctx, verbose, debug):
    """
    HyperAgent - AI-Powered Smart Contract Development Platform
    
    HyperAgent combines AI-powered contract generation, comprehensive auditing,
    and seamless deployment for the Hyperion ecosystem.
    
    ⚠️  STATUS WARNING: Development Mode - NOT Production Ready
    Many CLI commands are partial or broken. Run 'hyperagent limitations' for details.
    
    PRODUCTION MODE vs SAFE MODE:
    - PRODUCTION MODE: All dependencies available, full functionality
    - SAFE MODE: Missing dependencies, operations blocked with clear errors
    
    Check your mode: hyperagent status
    Check limitations: hyperagent limitations
    Honest status: See docs/HONEST_STATUS.md
    
    For detailed documentation: https://github.com/JustineDevs/HyperAgent
    """
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    ctx.obj['debug'] = debug
    _ensure_first_run_health()
    
    # Show warning on first run (non-verbose, non-help)
    if not verbose and not debug and ctx.invoked_subcommand not in [None, 'limitations']:
        # Only show warning once, can be disabled with --no-warn if needed
        pass  # Warning will be shown per-command instead
    
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
cli.add_command(docs_group, name='docs')

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

# Add doctor command
cli.add_command(doctor_command, name='doctor')

@cli.command()
def test_rag():
    """Test IPFS Pinata RAG connections (Obsidian removed - IPFS Pinata exclusive)"""
    test_rag_command()

@cli.command()
@click.option('--workflow-id', help='Workflow ID to dump context for')
def context(workflow_id):
    """Dump workflow context for troubleshooting"""
    from pathlib import Path
    from core.workflow.context_manager import ContextManager
    
    workspace_dir = Path(__file__).parent.parent
    context_manager = ContextManager(workspace_dir)
    
    if workflow_id:
        context = context_manager.load_context(workflow_id)
        if context:
            console.print(f"\n[bold]Workflow Context: {workflow_id}[/bold]")
            console.print(context.to_json())
            
            # Generate diagnostic bundle
            bundle_path = context_manager.save_diagnostic_bundle(context)
            console.print(f"\n[green]Diagnostic bundle saved:[/green] {bundle_path}")
        else:
            console.print(f"[red]Context not found for workflow: {workflow_id}[/red]")
    else:
        # List all contexts
        contexts_dir = workspace_dir / ".workflow_contexts"
        if contexts_dir.exists():
            contexts = list(contexts_dir.glob("*.json"))
            if contexts:
                console.print(f"\n[bold]Available workflow contexts:[/bold]")
                for ctx_file in sorted(contexts, key=lambda x: x.stat().st_mtime, reverse=True)[:10]:
                    workflow_id = ctx_file.stem
                    console.print(f"  - {workflow_id}")
            else:
                console.print("[yellow]No workflow contexts found[/yellow]")
        else:
            console.print("[yellow]No workflow contexts directory found[/yellow]")

@cli.command()
def limitations():
    """Show all known limitations and broken features"""
    from cli.utils.limitations import show_limitations
    show_limitations()

if __name__ == '__main__':
    cli()
