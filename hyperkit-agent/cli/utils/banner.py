"""
ASCII Banner Utility for HyperAgent CLI
Pure ASCII banner with optional color support
Based on patorjk.com Big Money font style for professional banner
Enhanced with Rich Panel wrappers and status panels
"""

import os
import sys
from rich.console import Console
from rich.panel import Panel
from rich.align import Align
from rich.text import Text

console = Console()

# Pure ASCII banner (no color codes, no emoji, no Unicode)
# Simple style - Big Money font from patorjk.com - "HyperAgent" text
# Source: https://patorjk.com/software/taag/#p=display&f=Big%20Money-se&t=HyperAgent
HYPERAGENT_BANNER = r"""
 __    __                                           ______                                  __     
|  \  |  \                                         /      \                                |  \    
| $$  | $$ __    __   ______    ______    ______  |  $$$$$$\  ______    ______   _______  _| $$_   
| $$__| $$|  \  |  \ /      \  /      \  /      \ | $$__| $$ /      \  /      \ |       \|   $$ \  
| $$    $$| $$  | $$|  $$$$$$\|  $$$$$$\|  $$$$$$\| $$    $$|  $$$$$$\|  $$$$$$\| $$$$$$$\\$$$$$$  
| $$$$$$$$| $$  | $$| $$  | $$| $$    $$| $$   \$$| $$$$$$$$| $$  | $$| $$    $$| $$  | $$ | $$ __ 
| $$  | $$| $$__/ $$| $$__/ $$| $$$$$$$$| $$      | $$  | $$| $$__| $$| $$$$$$$$| $$  | $$ | $$|  \
| $$  | $$ \$$    $$| $$    $$ \$$     \| $$      | $$  | $$ \$$    $$ \$$     \| $$  | $$  \$$  $$
 \$$   \$$ _\$$$$$$$| $$$$$$$   \$$$$$$$ \$$       \$$   \$$ _\$$$$$$$  \$$$$$$$ \$$   \$$   \$$$$ 
          |  \__| $$| $$                                    |  \__| $$                             
           \$$    $$| $$                                     \$$    $$                             
            \$$$$$$  \$$                                      \$$$$$$                              
"""

# Alternative compact banner - Big Money font - "HyperAgent" text
# Same style as simple, for consistency
HYPERAGENT_BANNER_COMPACT = r"""
 __    __                                           ______                                  __     
|  \  |  \                                         /      \                                |  \    
| $$  | $$ __    __   ______    ______    ______  |  $$$$$$\  ______    ______   _______  _| $$_   
| $$__| $$|  \  |  \ /      \  /      \  /      \ | $$__| $$ /      \  /      \ |       \|   $$ \  
| $$    $$| $$  | $$|  $$$$$$\|  $$$$$$\|  $$$$$$\| $$    $$|  $$$$$$\|  $$$$$$\| $$$$$$$\\$$$$$$  
| $$$$$$$$| $$  | $$| $$  | $$| $$    $$| $$   \$$| $$$$$$$$| $$  | $$| $$    $$| $$  | $$ | $$ __ 
| $$  | $$| $$__/ $$| $$__/ $$| $$$$$$$$| $$      | $$  | $$| $$__| $$| $$$$$$$$| $$  | $$ | $$|  \
| $$  | $$ \$$    $$| $$    $$ \$$     \| $$      | $$  | $$ \$$    $$ \$$     \| $$  | $$  \$$  $$
 \$$   \$$ _\$$$$$$$| $$$$$$$   \$$$$$$$ \$$       \$$   \$$ _\$$$$$$$  \$$$$$$$ \$$   \$$   \$$$$ 
          |  \__| $$| $$                                    |  \__| $$                             
           \$$    $$| $$                                     \$$    $$                             
            \$$$$$$  \$$                                      \$$$$$$                              
"""

# Professional banner using Big Money style from patorjk.com
# Source: https://patorjk.com/software/taag/#p=display&f=Big%20Money-se&t=HyperAgent
# This correctly spells "HyperAgent" (not "Hypertian")
HYPERAGENT_BANNER_PROFESSIONAL = r"""
 __    __                                           ______                                  __     
|  \  |  \                                         /      \                                |  \    
| $$  | $$ __    __   ______    ______    ______  |  $$$$$$\  ______    ______   _______  _| $$_   
| $$__| $$|  \  |  \ /      \  /      \  /      \ | $$__| $$ /      \  /      \ |       \|   $$ \  
| $$    $$| $$  | $$|  $$$$$$\|  $$$$$$\|  $$$$$$\| $$    $$|  $$$$$$\|  $$$$$$\| $$$$$$$\\$$$$$$  
| $$$$$$$$| $$  | $$| $$  | $$| $$    $$| $$   \$$| $$$$$$$$| $$  | $$| $$    $$| $$  | $$ | $$ __ 
| $$  | $$| $$__/ $$| $$__/ $$| $$$$$$$$| $$      | $$  | $$| $$__| $$| $$$$$$$$| $$  | $$ | $$|  \
| $$  | $$ \$$    $$| $$    $$ \$$     \| $$      | $$  | $$ \$$    $$ \$$     \| $$  | $$  \$$  $$
 \$$   \$$ _\$$$$$$$| $$$$$$$   \$$$$$$$ \$$       \$$   \$$ _\$$$$$$$  \$$$$$$$ \$$   \$$   \$$$$ 
          |  \__| $$| $$                                    |  \__| $$                             
           \$$    $$| $$                                     \$$    $$                             
            \$$$$$$  \$$                                      \$$$$$$                              
"""


def get_banner_style() -> str:
    """
    Get banner style from environment variable.
    Options: 'compact', 'professional', 'simple' (default)
    """
    style = os.getenv('HYPERAGENT_BANNER_STYLE', 'simple').lower()
    return style


def should_use_color() -> bool:
    """
    Determine if color should be used based on:
    1. --color flag (checked by caller)
    2. HYPERAGENT_COLOR environment variable
    3. Terminal capability (default: False for compatibility)
    """
    # Check environment variable
    color_env = os.getenv('HYPERAGENT_COLOR', '').lower()
    if color_env in ('1', 'true', 'yes', 'on'):
        return True
    
    # Check if output is a TTY and supports color
    if hasattr(sys.stdout, 'isatty') and sys.stdout.isatty():
        # Default to False for maximum compatibility
        # Can be enabled via env var or flag
        return False
    
    return False


def print_banner(ctx=None, use_color: bool = False, style: str = None, no_banner: bool = False):
    """
    Print HyperAgent ASCII banner.
    
    Args:
        ctx: Click context (optional, for checking --no-banner flag)
        use_color: Whether to use color (default: False)
        style: Banner style ('simple', 'compact', 'professional')
        no_banner: Explicit flag to suppress banner
    """
    # Check if banner should be suppressed
    if no_banner:
        return
    if ctx and hasattr(ctx, 'params') and ctx.params and ctx.params.get('no_banner', False):
        return
    
    # Get banner style
    if style is None:
        style = get_banner_style()
    
    # Select banner text
    if style == 'compact':
        banner_text = HYPERAGENT_BANNER_COMPACT
    elif style == 'professional':
        banner_text = HYPERAGENT_BANNER_PROFESSIONAL
    else:  # 'simple' or default
        banner_text = HYPERAGENT_BANNER
    
    # Calculate banner width for centering tagline
    banner_lines = banner_text.strip().split('\n')
    banner_width = max(len(line) for line in banner_lines if line.strip()) if banner_lines else 100
    
    # Tagline text
    tagline = "Autonomous Smart Contract Agent"
    
    # Print banner
    try:
        # Ensure UTF-8 encoding for output
        import sys
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        
        if use_color and should_use_color():
            # Use Rich for colored output (rainbow gradient effect)
            # Rich will apply rainbow colors dynamically to the ASCII art
            try:
                # Try rainbow style if available
                console.print(banner_text, style="bold rainbow")
            except:
                # Fallback to cyan if rainbow not available
                console.print(banner_text, style="bold cyan")
            # Add blank line for spacing
            print()
            # Center the tagline using Rich's alignment
            tagline_text = Text(tagline, style="dim")
            console.print(Align.center(tagline_text))
        else:
            # Pure ASCII, no color
            print(banner_text.rstrip())
            # Add blank line for spacing
            print()
            # Center the tagline manually
            tagline_centered = tagline.center(banner_width)
            print(tagline_centered)
        
        print()  # Blank line after banner
    except (UnicodeEncodeError, AttributeError):
        # Fallback: use simple ASCII banner
        print_banner_simple()


def print_enhanced_banner(ctx=None, use_color: bool = False, style: str = None, no_banner: bool = False):
    """
    Print enhanced banner with Rich Panel wrapper and status panels.
    
    Args:
        ctx: Click context (optional, for checking --no-banner flag)
        use_color: Whether to use color (default: False)
        style: Banner style ('simple', 'compact', 'professional')
        no_banner: Explicit flag to suppress banner
    """
    # Check if banner should be suppressed
    if no_banner:
        return
    if ctx and hasattr(ctx, 'params') and ctx.params and ctx.params.get('no_banner', False):
        return
    
    # Import menu utilities for panels
    from cli.utils.menu import (
        print_welcome_panel,
        print_status_panel,
        print_production_mode_panel,
        print_llm_config_panel
    )
    
    # Print welcome panel with time-based greeting
    print_welcome_panel()
    print()  # Spacing
    
    # Print ASCII banner (original banner, no panel wrapper to preserve ASCII art)
    print_banner(ctx=ctx, use_color=use_color, style=style, no_banner=no_banner)
    
    # Print status panels
    print_status_panel()
    print()  # Spacing
    
    print_production_mode_panel()
    print()  # Spacing
    
    print_llm_config_panel()
    print()  # Spacing


def print_banner_simple():
    """Simple banner print function for maximum compatibility."""
    try:
        # Use sys.stdout with UTF-8 encoding for better compatibility
        import sys
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        
        # Calculate banner width for centering
        banner_lines = HYPERAGENT_BANNER.strip().split('\n')
        banner_width = max(len(line) for line in banner_lines if line.strip()) if banner_lines else 100
        
        print(HYPERAGENT_BANNER.rstrip())
        # Add blank line for spacing
        print()
        # Center the tagline
        tagline = "Autonomous Smart Contract Agent"
        tagline_centered = tagline.center(banner_width)
        print(tagline_centered)
        print()
    except (UnicodeEncodeError, AttributeError):
        # Fallback to ASCII-only if encoding fails
        banner_ascii = r"""
 __    __                                           ______                                  __     
|  \  |  \                                         /      \                                |  \    
| $$  | $$ __    __   ______    ______    ______  |  $$$$$$\  ______    ______   _______  _| $$_   
| $$__| $$|  \  |  \ /      \  /      \  /      \ | $$__| $$ /      \  /      \ |       \|   $$ \  
| $$    $$| $$  | $$|  $$$$$$\|  $$$$$$\|  $$$$$$\| $$    $$|  $$$$$$\|  $$$$$$\| $$$$$$$\\$$$$$$  
| $$$$$$$$| $$  | $$| $$  | $$| $$    $$| $$   \$$| $$$$$$$$| $$  | $$| $$    $$| $$  | $$ | $$ __ 
| $$  | $$| $$__/ $$| $$__/ $$| $$$$$$$$| $$      | $$  | $$| $$__| $$| $$$$$$$$| $$  | $$ | $$|  \
| $$  | $$ \$$    $$| $$    $$ \$$     \| $$      | $$  | $$ \$$    $$ \$$     \| $$  | $$  \$$  $$
 \$$   \$$ _\$$$$$$$| $$$$$$$   \$$$$$$$ \$$       \$$   \$$ _\$$$$$$$  \$$$$$$$ \$$   \$$   \$$$$ 
          |  \__| $$| $$                                    |  \__| $$                             
           \$$    $$| $$                                     \$$    $$                             
            \$$$$$$  \$$                                      \$$$$$$                              
"""
        banner_lines = banner_ascii.strip().split('\n')
        banner_width = max(len(line) for line in banner_lines if line.strip()) if banner_lines else 100
        print(banner_ascii.rstrip())
        # Add blank line for spacing
        print()
        # Center the tagline
        tagline = "Autonomous Smart Contract Agent"
        tagline_centered = tagline.center(banner_width)
        print(tagline_centered)
        print()
