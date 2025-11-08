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

# CRITICAL: Set RUST_LOG before any imports that might trigger Rust logging
# This must be done BEFORE importing any modules that use the Alith SDK
if 'RUST_LOG' not in os.environ:
    os.environ['RUST_LOG'] = 'warn'  # Only show warnings and errors from Rust

import click
from rich.console import Console

# CRITICAL: Check for help BEFORE any imports that might trigger initialization
# This allows us to suppress initialization messages for help commands
_is_help_request = len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h', 'help']

# Suppress verbose Alith SDK logs for cleaner CLI output
logging.getLogger("alith_interface").setLevel(logging.WARNING)
logging.getLogger("alith").setLevel(logging.WARNING)

# If help is requested, suppress all INFO level logs to prevent initialization messages
if _is_help_request:
    logging.getLogger().setLevel(logging.WARNING)
    logging.getLogger("hyperkit").setLevel(logging.WARNING)
    logging.getLogger("hyperkit.ai_agent").setLevel(logging.ERROR)
    logging.getLogger("hyperkit.system").setLevel(logging.ERROR)

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
from cli.utils.banner import print_banner

console = Console()

# Informational commands that don't require private key validation
INFORMATIONAL_COMMANDS = {
    'help', 'version', 'status', 'limitations', 'doctor', 
    'test-rag', 'context', 'config', 'docs'
}

def _should_skip_private_key_validation(ctx) -> bool:
    """
    Determine if private key validation should be skipped.
    
    Informational commands (help, version, status, etc.) don't need private keys.
    Contract-related commands (generate, deploy, workflow, audit) require them.
    """
    # Early check: if --help or -h is in command line args, skip validation
    # This handles the case where ctx might not be fully initialized yet
    if '--help' in sys.argv or '-h' in sys.argv:
        return True
    
    if not ctx:
        return False
    
    invoked_subcommand = ctx.invoked_subcommand
    
    # Click's help command is None when --help is used
    if invoked_subcommand is None:
        return True  # No subcommand = likely help or main command
    
    # Check if command is informational
    if invoked_subcommand in INFORMATIONAL_COMMANDS:
        return True
    
    # Check command groups that are informational
    if invoked_subcommand in ['config', 'docs']:
        return True
    
    return False

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

@click.group(
    invoke_without_command=True,
    context_settings={
        'help_option_names': ['-h', '--help'],
        'max_content_width': 120
    }
)
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.option('--debug', '-d', is_flag=True, help='Enable debug mode')
@click.option('--no-banner', is_flag=True, help='Suppress ASCII banner display')
@click.option('--color', is_flag=True, help='Enable colored output (requires terminal support)')
@click.pass_context
def cli(ctx, verbose, debug, no_banner, color):
    """
    HyperAgent - AI-Powered Smart Contract Development Platform
    
    HyperAgent combines AI-powered contract generation, comprehensive auditing,
    and seamless deployment for the Hyperion ecosystem.
    
    ⚠️  STATUS WARNING: Development Mode - NOT Production Ready
    Many CLI commands are partial or broken. Run 'hyperagent limitations' for details.
    
    PRODUCTION MODE vs SAFE MODE:
    - PRODUCTION MODE: All dependencies available, full functionality
    - SAFE MODE: Missing dependencies, operations blocked with clear errors
    
    AI/LLM Configuration:
    [*] PRIMARY: Gemini (via Alith SDK adapter) - gemini-2.5-flash-lite
    [>] SECONDARY: OpenAI (via Alith SDK) - used if Gemini unavailable
    
    Check your mode: hyperagent status
    Check limitations: hyperagent limitations
    Honest status: See docs/HONEST_STATUS.md
    
    For detailed documentation: https://github.com/JustineDevs/HyperAgent
    """
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    ctx.obj['debug'] = debug
    
    # CRITICAL FIX: Check if --help was used BEFORE any initialization
    # This prevents tracebacks during help command execution
    is_help_command = (
        '--help' in sys.argv or 
        '-h' in sys.argv or 
        ctx.invoked_subcommand == 'help' or
        (ctx.invoked_subcommand is None and len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h', 'help'])
    )
    
    # Skip all initialization for help commands to prevent tracebacks
    if is_help_command:
        # Suppress any initialization messages that might have already appeared
        # Let Click handle help display - don't interfere with initialization
        return
    
    # Skip private key validation for informational commands
    skip_private_key = _should_skip_private_key_validation(ctx)
    
    # Only validate config for non-informational commands
    # Informational commands can run without private key
    try:
        from core.config.manager import config
        config._validate_startup_config(skip_private_key=skip_private_key)
    except SystemExit:
        # Re-raise to maintain current behavior for critical errors
        raise
    except Exception as e:
        # For help commands, we should have returned earlier
        # But if we get here, log and continue
        if verbose or debug:
            console.print(f"[yellow]Config validation warning: {e}[/yellow]")
    
    _ensure_first_run_health()
    
    # Check if no command was provided (show enhanced menu)
    if ctx.invoked_subcommand is None:
        # CRITICAL: Check if we're already executing a command to prevent recursion
        from cli.utils.interactive import _execution_in_progress
        from cli.utils.menu import _menu_execution_in_progress
        
        # If a command is already executing, don't show the menu again
        if _execution_in_progress or _menu_execution_in_progress:
            # Command is being executed - don't show menu, just return
            return
        
        # Show enhanced menu when no command provided
        from cli.utils.banner import print_enhanced_banner
        from cli.utils.menu import (
            print_command_menu,
            print_usage_examples,
            print_keyboard_shortcuts,
            print_tip_footer,
            show_interactive_menu_and_execute
        )
        
        # Show enhanced banner with panels
        if not no_banner:
            print_enhanced_banner(ctx=ctx, use_color=color, no_banner=no_banner)
        
        # Show interactive menu and execute selected command
        result = show_interactive_menu_and_execute()
        
        if result == "list":
            # User chose to see non-interactive list - continue to show menu
            pass
        elif result and result not in ["quit", "list"]:
            # Command was executed - exit
            return
        else:
            # User cancelled or questionary not available - show menu anyway
            pass
        
        # Show grouped command list
        print_command_menu(show_groups=True)
        
        # Show usage examples
        print_usage_examples()
        
        # Show keyboard shortcuts
        print_keyboard_shortcuts()
        
        # Show tip footer
        print_tip_footer()
        
        return
    
    # Command was provided - show regular banner if not disabled
    if not no_banner:
        print_banner(ctx=ctx, use_color=color, no_banner=no_banner)
    
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
    from cli.utils.sentinel_validator import validate_string_param, is_sentinel
    
    workspace_dir = Path(__file__).parent.parent
    context_manager = ContextManager(workspace_dir)
    
    # Validate and filter out Sentinel objects
    
    # Debug logging for Sentinel detection
    import os
    DEBUG_RECURSION = os.environ.get('HYPERAGENT_DEBUG_RECURSION', 'false').lower() == 'true'
    
    if workflow_id and is_sentinel(workflow_id):
        if DEBUG_RECURSION:
            import logging
            import threading
            logger = logging.getLogger('hyperkit.cli.recursion')
            thread_id = threading.current_thread().ident
            logger.warning(f"[RECURSION_DEBUG] Sentinel detected in context command: type={type(workflow_id)}, value={workflow_id}, thread_id={thread_id}")
            import traceback
            logger.warning(f"[RECURSION_DEBUG] Stack trace:\n{''.join(traceback.format_stack()[:-1])}")
        console.print("[red]Error: Invalid workflow-id parameter (Sentinel object detected)[/red]")
        console.print("[yellow]Tip: Use 'hyperagent context' without --workflow-id to list available contexts[/yellow]")
        raise click.ClickException("Invalid workflow-id parameter (Sentinel object detected)")
    
    validated_workflow_id = validate_string_param(workflow_id, "workflow-id")
    
    if validated_workflow_id:
        try:
            context = context_manager.load_context(validated_workflow_id)
            if context:
                console.print(f"\n[bold]Workflow Context: {validated_workflow_id}[/bold]")
                console.print(context.to_json())
                
                # Generate diagnostic bundle
                bundle_path = context_manager.save_diagnostic_bundle(context)
                console.print(f"\n[green]Diagnostic bundle saved:[/green] {bundle_path}")
            else:
                console.print(f"[red]Context not found for workflow: {validated_workflow_id}[/red]")
                # CRITICAL FIX: Return non-zero exit code when workflow-id provided but not found
                import sys
                sys.exit(1)
        except ValueError as e:
            console.print(f"[red]Error loading context: {e}[/red]")
            console.print("[yellow]Tip: Use 'hyperagent context' without --workflow-id to list available contexts[/yellow]")
            # CRITICAL FIX: Return non-zero exit code on validation error
            import sys
            sys.exit(1)
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


@cli.command(name='help')
@click.argument('command', required=False)
@click.pass_context
def help_command(ctx, command):
    """
    Show help for a command using Rich formatting.
    
    If no command is specified, shows the main help menu.
    """
    if command:
        # Show help for specific command
        try:
            # Try to get the command from the parent group
            parent_cmd = ctx.parent.command if ctx.parent else cli
            cmd = parent_cmd.get_command(ctx, command)
            if cmd:
                from cli.utils.help import format_command_help
                format_command_help(cmd, ctx)
            else:
                from cli.utils.help import show_command_suggestion
                from cli.utils.menu import get_all_commands
                available_commands = get_all_commands()
                show_command_suggestion(command, available_commands)
        except Exception:
            # Fallback to standard help
            from cli.utils.help import show_command_suggestion
            from cli.utils.menu import get_all_commands
            available_commands = get_all_commands()
            show_command_suggestion(command, available_commands)
    else:
        # Show main help - trigger the enhanced menu
        ctx.info_name = 'hyperagent'
        click.echo(ctx.get_help())


def main():
    """Main entry point with error handling for unknown commands."""
    # CRITICAL FIX: Check for help BEFORE calling cli() to prevent initialization
    # This catches help requests before any Click processing
    if len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h', 'help']:
        # For help, set UTF-8 encoding on Windows to prevent Unicode errors
        if sys.platform == 'win32':
            import io
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
        # Let Click handle help - it will call cli() but we've already set up encoding
        try:
            cli()
        except UnicodeEncodeError:
            # Fallback: if encoding still fails, use ASCII-safe output
            import io
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='ascii', errors='replace')
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='ascii', errors='replace')
            cli()
        return
    
    try:
        cli()
    except click.exceptions.UsageError as e:
        # Handle unknown commands with suggestions
        error_msg = str(e)
        if 'No such command' in error_msg or 'Unknown command' in error_msg:
            # Extract command name from error message
            import re
            # Try multiple patterns to extract command name
            match = re.search(r"'([\w-]+)'", error_msg) or re.search(r'(\w+)', error_msg)
            if match:
                unknown_cmd = match.group(1)
                from cli.utils.help import show_command_suggestion
                from cli.utils.menu import get_all_commands
                
                available_commands = get_all_commands()
                show_command_suggestion(unknown_cmd, available_commands)
                console.print("\n[yellow]Run 'hyperagent' to see all available commands[/yellow]")
                sys.exit(1)
        # Re-raise other usage errors
        raise
    except Exception as e:
        # Re-raise other exceptions
        raise


if __name__ == '__main__':
    main()
