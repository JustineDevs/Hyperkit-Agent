"""
Interactive CLI Utilities
Global interactive prompts, parameter collection, and confirmation dialogs
"""

import functools
from typing import Any, Optional, List, Dict, Callable
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
import click

console = Console()

# Global execution flags - must be accessible from main CLI
_execution_in_progress = False


def prompt_for_missing_params(ctx: click.Context, command: click.Command) -> Dict[str, Any]:
    """
    Prompt for missing required parameters interactively.
    
    Args:
        ctx: Click context
        command: Click command object
    
    Returns:
        Dictionary of collected parameter values
    """
    params = {}
    
    try:
        import questionary
        use_questionary = True
    except ImportError:
        use_questionary = False
    
    for param in command.params:
        if isinstance(param, click.Option):
            # Skip if already provided (check both ctx.params and ctx.obj)
            param_value = ctx.params.get(param.name) if ctx.params else None
            if param_value is not None and param_value != "":
                continue
            # Only prompt for required params if they're truly missing
            if not param.required:
                continue
            
            # Get prompt text
            prompt_text = param.help or f"Enter {param.name}"
            
            try:
                if use_questionary:
                    # Use questionary for better UX
                    if param.type == click.BOOL:
                        value = questionary.confirm(prompt_text, default=param.default).ask()
                    elif isinstance(param.type, click.Choice):
                        value = questionary.select(
                            prompt_text,
                            choices=list(param.type.choices),
                            default=param.default
                        ).ask()
                    else:
                        default_val = str(param.default) if param.default is not None else None
                        value = questionary.text(prompt_text, default=default_val).ask()
                else:
                    # Fallback to click.prompt
                    value = click.prompt(prompt_text, default=param.default, type=param.type)
                
                if value is not None:
                    params[param.name] = value
            except (KeyboardInterrupt, EOFError):
                # User cancelled
                break
            except Exception as e:
                console.print(f"[yellow]Error prompting for {param.name}: {e}[/yellow]")
                continue
    
    return params


def confirm_destructive_action(action: str, details: Optional[str] = None) -> bool:
    """
    Confirm a destructive action with a clear warning.
    
    Args:
        action: Description of the action
        details: Additional details to show
    
    Returns:
        True if confirmed, False otherwise
    """
    warning_text = f"[bold red]WARNING:[/bold red] {action}"
    if details:
        warning_text += f"\n\n{details}"
    
    console.print(Panel(warning_text, title="[bold red]Destructive Action[/bold red]", border_style="red"))
    
    try:
        import questionary
        return questionary.confirm(
            "Are you sure you want to proceed?",
            default=False
        ).ask()
    except ImportError:
        return click.confirm("Are you sure you want to proceed?", default=False)


def interactive_file_selection(
    prompt: str,
    file_pattern: str = "*",
    directory: Optional[str] = None
) -> Optional[str]:
    """
    Interactively select a file from available options.
    
    Args:
        prompt: Prompt text
        file_pattern: File pattern to match (e.g., "*.sol")
        directory: Directory to search (default: current)
    
    Returns:
        Selected file path or None
    """
    search_dir = Path(directory) if directory else Path.cwd()
    files = list(search_dir.glob(file_pattern))
    
    if not files:
        console.print(f"[yellow]No files found matching {file_pattern}[/yellow]")
        return None
    
    try:
        import questionary
        choices = [f.name for f in files]
        selected = questionary.select(prompt, choices=choices).ask()
        if selected:
            return str(search_dir / selected)
        return None
    except ImportError:
        # Fallback to simple prompt
        console.print(f"\n[bold]Available files:[/bold]")
        for i, f in enumerate(files, 1):
            console.print(f"  {i}. {f.name}")
        try:
            choice = click.prompt(prompt, type=int)
            if 1 <= choice <= len(files):
                return str(files[choice - 1])
        except (ValueError, click.Abort):
            pass
        return None


def interactive_network_selection() -> Optional[str]:
    """
    Interactively select a network from available options.
    
    Returns:
        Selected network name or None
    """
    try:
        from core.config.loader import get_config
        
        config = get_config()
        networks = list(config.networks.keys())
        
        if not networks:
            console.print("[yellow]No networks configured[/yellow]")
            return None
        
        try:
            import questionary
            selected = questionary.select(
                "Select network",
                choices=networks,
                default=networks[0] if networks else None
            ).ask()
            return selected
        except ImportError:
            # Fallback
            console.print("\n[bold]Available networks:[/bold]")
            for i, net in enumerate(networks, 1):
                console.print(f"  {i}. {net}")
            try:
                choice = click.prompt("Select network", type=int)
                if 1 <= choice <= len(networks):
                    return networks[choice - 1]
            except (ValueError, click.Abort):
                pass
            return None
    except Exception as e:
        console.print(f"[red]Error loading networks: {e}[/red]")
        return None


def collect_command_params_interactively(
    command: click.Command,
    ctx: click.Context
) -> Dict[str, Any]:
    """
    Collect all command parameters interactively (options AND arguments).
    
    Args:
        command: Click command object
        ctx: Click context
    
    Returns:
        Dictionary of parameter values
    """
    params = {}
    
    # First, collect missing required arguments
    for param in command.params:
        if isinstance(param, click.Argument):
            # Check if argument is already provided
            if param.name in ctx.params and ctx.params[param.name] is not None:
                continue
            if not param.required:
                continue
            
            # Prompt for argument
            prompt_text = f"Enter {param.name}"
            if hasattr(param, 'nargs') and param.nargs and param.nargs > 1:
                # Multiple values
                try:
                    import questionary
                    value = questionary.text(
                        prompt_text,
                        instruction="Enter multiple values separated by spaces"
                    ).ask()
                    if value:
                        params[param.name] = value.split()
                except ImportError:
                    value = click.prompt(prompt_text, type=str)
                    if value:
                        params[param.name] = value.split()
            else:
                # Single value
                try:
                    import questionary
                    value = questionary.text(prompt_text).ask()
                except ImportError:
                    value = click.prompt(prompt_text, type=param.type if hasattr(param, 'type') else str)
                
                if value:
                    params[param.name] = value
    
    # Then, collect missing required options
    missing = prompt_for_missing_params(ctx, command)
    params.update(missing)
    
    # Then, offer to set optional params
    try:
        import questionary
        optional_params = [
            p for p in command.params
            if isinstance(p, click.Option) and not p.required
            and p.name not in ctx.params and p.name not in params
        ]
        
        if optional_params and questionary.confirm(
            "Would you like to configure optional parameters?",
            default=False
        ).ask():
            from cli.utils.sentinel_validator import is_sentinel
            for param in optional_params:
                # Skip if param value is already set (even if it's a Sentinel)
                param_value = ctx.params.get(param.name) if ctx.params else None
                if param_value is not None:
                    # Check if it's a Sentinel - if so, we can still prompt
                    if is_sentinel(param_value):
                        pass  # Continue to prompt
                    else:
                        continue  # Skip if already has valid value
                
                prompt_text = param.help or f"Enter {param.name} (optional)"
                if param.type == click.BOOL:
                    value = questionary.confirm(prompt_text, default=param.default).ask()
                elif isinstance(param.type, click.Choice):
                    value = questionary.select(
                        prompt_text,
                        choices=list(param.type.choices),
                        default=param.default
                    ).ask()
                else:
                    value = questionary.text(
                        prompt_text,
                        default=str(param.default) if param.default else None
                    ).ask()
                if value:
                    params[param.name] = value
    except ImportError:
        pass
    
    return params


def prompt_if_missing(param_name: str, prompt_text: str, param_type: Any = str, default: Any = None) -> Callable:
    """
    Decorator to prompt for a parameter if it's missing.
    
    Args:
        param_name: Name of the parameter to check
        prompt_text: Text to show in prompt
        param_type: Type of the parameter
        default: Default value
    
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Check if parameter is missing
            if param_name not in kwargs or kwargs[param_name] is None:
                try:
                    import questionary
                    if param_type == bool:
                        value = questionary.confirm(prompt_text, default=default).ask()
                    else:
                        value = questionary.text(prompt_text, default=str(default) if default else None).ask()
                        if param_type != str:
                            value = param_type(value)
                    kwargs[param_name] = value
                except ImportError:
                    kwargs[param_name] = click.prompt(prompt_text, default=default, type=param_type)
            return func(*args, **kwargs)
        return wrapper
    return decorator


def execute_with_progress_indicator(
    command: click.Command,
    params: Dict[str, Any],
    ctx: click.Context,
    command_name: str
) -> bool:
    """
    Execute a command with abstract progress indicators.
    Suppresses verbose output and shows only progress/errors.
    
    Args:
        command: Click command to execute
        params: Parameters to pass to command
        ctx: Click context
        command_name: Display name for the command
    
    Returns:
        True if successful, False otherwise
    """
    global _execution_in_progress
    
    # Debug logging for recursion tracking
    import os
    DEBUG_RECURSION = os.environ.get('HYPERAGENT_DEBUG_RECURSION', 'false').lower() == 'true'
    
    if DEBUG_RECURSION:
        import logging
        import threading
        logger = logging.getLogger('hyperkit.cli.recursion')
        thread_id = threading.current_thread().ident
        logger.debug(f"[RECURSION_DEBUG] execute_with_progress_indicator called: command={command_name}, _execution_in_progress={_execution_in_progress}, thread_id={thread_id}")
    
    # CRITICAL FIX: Prevent recursive execution - return immediately if already executing
    if _execution_in_progress:
        if DEBUG_RECURSION:
            logger.warning(f"[RECURSION_DEBUG] RECURSION PREVENTED: command={command_name}, thread_id={thread_id}")
            import traceback
            logger.warning(f"[RECURSION_DEBUG] Stack trace:\n{''.join(traceback.format_stack()[:-1])}")
        console.print("[yellow]Command already executing, skipping recursive call[/yellow]")
        return False  # Don't invoke command again - just return False
    
    _execution_in_progress = True
    
    if DEBUG_RECURSION:
        logger.debug(f"[RECURSION_DEBUG] Execution started: command={command_name}, thread_id={thread_id}")
    
    try:
        from rich.progress import Progress, SpinnerColumn, TextColumn
        import click
        import sys
        from io import StringIO
        
        # Filter params - remove None, empty strings, and Click Sentinel objects
        from cli.utils.sentinel_validator import is_sentinel
        def is_valid_param_value(v):
            """Check if parameter value is valid (not None, empty, or Sentinel)."""
            if v is None:
                return False
            if isinstance(v, str) and not v.strip():
                return False
            # Check for Click Sentinel objects using centralized utility
            if is_sentinel(v):
                return False
            return True
        
        # Filter params before updating context
        filtered_params = {k: v for k, v in params.items() if is_valid_param_value(v)}
        
        # Also filter ctx.params to remove Sentinel objects before merging
        filtered_ctx_params = {}
        if ctx.params:
            for k, v in ctx.params.items():
                if is_valid_param_value(v):
                    filtered_ctx_params[k] = v
        
        # Update context - ensure params dict exists and use filtered params
        if ctx.params is None:
            ctx.params = {}
        
        # Debug logging for params clearing
        if DEBUG_RECURSION:
            sentinel_count = sum(1 for v in ctx.params.values() if is_sentinel(v)) if ctx.params else 0
            total_params = len(ctx.params) if ctx.params else 0
            logger.debug(f"[RECURSION_DEBUG] Clearing params: total={total_params}, sentinels={sentinel_count}, filtered_params={len(filtered_params)}, filtered_ctx_params={len(filtered_ctx_params)}")
        
        # CRITICAL FIX: Clear existing params first to remove any Sentinel values
        ctx.params.clear()  # Clear first to remove any existing Sentinel values
        ctx.params.update(filtered_ctx_params)
        ctx.params.update(filtered_params)
        
        if DEBUG_RECURSION:
            logger.debug(f"[RECURSION_DEBUG] Params after update: total={len(ctx.params)}, sentinels={sum(1 for v in ctx.params.values() if is_sentinel(v))}")
        
        # Suppress verbose logging during command execution
        import logging
        import os
        original_levels = {}
        verbose_loggers = ['alith_interface', 'alith', 'hyperkit.ai_agent']
        for logger_name in verbose_loggers:
            logger = logging.getLogger(logger_name)
            original_levels[logger_name] = logger.level
            logger.setLevel(logging.WARNING)
        
        # Suppress Rust logging via environment variable (if supported)
        original_rust_log = os.environ.get('RUST_LOG')
        os.environ['RUST_LOG'] = 'warn'  # Only show warnings and errors from Rust
        
        # Create progress indicator with manual control (no context manager)
        progress = None
        task = None
        try:
            progress = Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
                transient=True,
                disable=False
            )
            # Manually start progress (don't use context manager)
            progress.start()
            task = progress.add_task(f"[cyan]Executing {command_name}...", total=None)
            
            # Execute command with stdout and stderr filtering to suppress verbose Rust logs
            import sys
            import io
            from contextlib import redirect_stderr, redirect_stdout
            
            # Filter both stdout and stderr to suppress verbose Alith SDK Rust logs
            import re
            class OutputFilter:
                def __init__(self, original_stream):
                    self.original_stream = original_stream
                    self.suppress_mode = False
                    self.suppress_line_count = 0
                    self.max_suppress_lines = 100  # Max lines to suppress in a block
                    self.suppress_patterns = [
                        'alith_interface::requests::completion',
                        'CompletionRequest:',
                        'CompletionResponse:',
                        'total_prompt_tokens:',
                        'messages:',
                        'User:',
                        'content:',
                        'finish_reason:',
                        'generation_settings:',
                        'timing_usage:',
                        'token_usage:',
                        'model:',
                        'frequency_penalty:',
                        'presence_penalty:',
                        'temperature:',
                        'stop_sequences:',
                        'config:',
                        'tokens_cached:',
                        'prompt_tokens:',
                        'completion_tokens:',
                        'total_tokens:',
                        'token_calls:',
                        'n_choices:',
                        'n_predict:',
                        'n_ctx:',
                        'logit_bias:',
                        'grammar:'
                    ]
                
                def write(self, text):
                    # Check for verbose log patterns that should always be suppressed
                    text_lower = text.lower()
                    
                    # Detect timestamp-based log entries (Rust logging format)
                    is_timestamp_log = bool(re.match(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', text.strip()))
                    
                    # Always suppress verbose Rust completion logs and user prompts
                    if any(pattern in text for pattern in [
                        'alith_interface::requests::completion',
                        'completionrequest:',
                        'completionresponse:',
                        'generate a production-ready smart contract',
                        'user:',
                        'finish_reason:',
                        'generation_settings:'
                    ]) or (is_timestamp_log and 'alith_interface' in text_lower):
                        # Start suppressing
                        self.suppress_mode = True
                        self.suppress_line_count = 0
                        return
                    
                    # Check if this line starts a verbose log block (including timestamp lines)
                    if (any(pattern in text_lower for pattern in ['completionrequest:', 'completionresponse:', 'user:']) or
                        (is_timestamp_log and ('completion' in text_lower or 'alith' in text_lower))):
                        self.suppress_mode = True
                        self.suppress_line_count = 0
                        return
                    
                    # Check if this line ends the verbose log block
                    if self.suppress_mode:
                        self.suppress_line_count += 1
                        
                        # Detect Solidity code patterns
                        is_solidity_code = any(x in text for x in [
                            'pragma solidity', 'contract ', 'function ', 'import ', 
                            'event ', 'struct ', 'mapping(', 'modifier ', 'constructor',
                            '@openzeppelin', 'Ownable', 'ReentrancyGuard'
                        ])
                        
                        # Stop suppressing after max lines, on new timestamp (different log), or non-verbose content
                        is_timestamp_line = bool(re.match(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', text.strip()))
                        is_verbose = (any(p in text for p in self.suppress_patterns) or 
                                     'INFO' in text or 
                                     'alith_interface' in text or 
                                     is_solidity_code or
                                     'completion' in text_lower or
                                     'token_usage' in text_lower or
                                     'timing_usage' in text_lower)
                        
                        # Check if we've hit a new log entry (timestamp with different content)
                        # If it's a timestamp but not related to completion/alith, stop suppressing
                        if is_timestamp_line and not is_verbose and self.suppress_line_count > 5:
                            self.suppress_mode = False
                            self.suppress_line_count = 0
                            # Don't print the timestamp line if it was part of verbose block
                            return
                        
                        # If we see a timestamp with alith/completion, keep suppressing
                        if is_timestamp_line and is_verbose:
                            return
                        
                        # Stop suppressing if we hit a non-verbose line that's not Solidity code
                        if (self.suppress_line_count > self.max_suppress_lines or 
                            (text.strip() and not is_verbose and not is_solidity_code and 
                             not any(x in text for x in ['content:', '  ', '    ']))):
                            self.suppress_mode = False
                            self.suppress_line_count = 0
                            # Only print if it's not part of the verbose block
                            if text.strip() and not any(x in text for x in [
                                'alith_interface', 'CompletionRequest', 'CompletionResponse', 
                                'User:', 'pragma solidity', 'contract ', 'function '
                            ]):
                                self.original_stream.write(text)
                            return
                        else:
                            # Still in verbose block - suppress
                            return
                    
                    # Keep errors and important messages (but filter out verbose Rust logs and contract code)
                    should_suppress = any(pattern in text_lower for pattern in [
                        'alith_interface::requests::completion',
                        'completionrequest',
                        'completionresponse',
                        'user:',
                        'generate a production-ready smart contract',
                        'pragma solidity',
                        'contract ',
                        'function ',
                        'import \'@openzeppelin',
                        'finish_reason:',
                        'generation_settings:',
                        'timing_usage:',
                        'token_usage:'
                    ])
                    
                    if not should_suppress:
                        self.original_stream.write(text)
                
                def flush(self):
                    self.original_stream.flush()
                
                # Add missing attributes that might be accessed
                def __getattr__(self, name):
                    # Return None for any missing attributes to prevent AttributeError
                    if name == 'buffer':
                        return None
                    raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")
            
            filtered_stderr = OutputFilter(sys.stderr)
            filtered_stdout = OutputFilter(sys.stdout)
            
            # Execute command with filtered stdout and stderr
            try:
                with redirect_stderr(filtered_stderr), redirect_stdout(filtered_stdout):
                    ctx.invoke(command, **filtered_params)
                if progress and task is not None:
                    try:
                        progress.update(task, description=f"[green]✓ {command_name} completed successfully")
                        # Give a moment to show success message
                        import time
                        time.sleep(0.3)
                    except (ValueError, OSError, AttributeError):
                        pass
                return True
            except click.exceptions.Exit as e:
                if progress and task is not None:
                    try:
                        progress.update(task, description=f"[red]✗ {command_name} failed")
                    except (ValueError, OSError, AttributeError):
                        pass
                if e.exit_code != 0:
                    try:
                        console.print(f"[red]Command exited with code {e.exit_code}[/red]")
                    except (ValueError, OSError):
                        pass
                return False
            except click.ClickException as e:
                # CRITICAL: ClickException should stop execution immediately - don't retry
                if progress and task is not None:
                    try:
                        progress.update(task, description=f"[red]✗ {command_name} failed")
                    except (ValueError, OSError, AttributeError):
                        pass
                try:
                    console.print(f"\n[bold red]Error:[/bold red] {str(e)}")
                except (ValueError, OSError):
                    pass
                if DEBUG_RECURSION:
                    logger.warning(f"[RECURSION_DEBUG] ClickException raised: command={command_name}, error={str(e)}, stopping execution")
                # CRITICAL: Return False immediately - don't allow retries
                return False
            except Exception as e:
                if progress and task is not None:
                    try:
                        progress.update(task, description=f"[red]✗ {command_name} failed")
                    except (ValueError, OSError, AttributeError):
                        pass
                try:
                    console.print(f"\n[bold red]Error:[/bold red] {str(e)}")
                except (ValueError, OSError):
                    pass
                if ctx.obj.get('debug', False) if ctx.obj else False:
                    import traceback
                    traceback.print_exc()
                return False
        except (ValueError, OSError) as console_error:
            # Console/file already closed - execute without progress indicator
            # CRITICAL: Check recursion guard even in fallback path
            if _execution_in_progress:
                if DEBUG_RECURSION:
                    logger.warning(f"[RECURSION_DEBUG] RECURSION PREVENTED in fallback path: command={command_name}, thread_id={threading.current_thread().ident}")
                return False  # Don't recurse even in fallback
            try:
                ctx.invoke(command, **filtered_params)
                return True
            except click.ClickException as e:
                # CRITICAL: ClickException in fallback path - stop immediately
                if DEBUG_RECURSION:
                    logger.warning(f"[RECURSION_DEBUG] ClickException in fallback path: command={command_name}, error={str(e)}")
                return False  # Don't retry
            except Exception as e:
                return False
    finally:
        # Reset execution flag
        if DEBUG_RECURSION:
            logger.debug(f"[RECURSION_DEBUG] Execution completed: command={command_name}, thread_id={threading.current_thread().ident}, resetting flag")
        _execution_in_progress = False
        # Clean up progress indicator safely
        if progress:
            try:
                progress.stop()
            except (ValueError, OSError, AttributeError):
                pass
        
        # Restore original log levels
        for logger_name, original_level in original_levels.items():
            try:
                logging.getLogger(logger_name).setLevel(original_level)
            except:
                pass
        
        # Restore original RUST_LOG
        if original_rust_log is not None:
            os.environ['RUST_LOG'] = original_rust_log
        elif 'RUST_LOG' in os.environ:
            del os.environ['RUST_LOG']

