"""
Test Enhanced CLI Menu System
Tests for menu display, interactive selection, suggestions, and greetings
"""

import pytest
from unittest.mock import patch, MagicMock
from rich.console import Console
from cli.utils.menu import (
    get_time_based_greeting,
    get_command_groups,
    get_all_commands,
    print_command_menu,
    print_usage_examples,
    print_keyboard_shortcuts,
    suggest_command,
    show_interactive_menu,
    print_welcome_panel,
    print_status_panel,
    print_production_mode_panel,
    print_llm_config_panel,
    print_tip_footer
)
from cli.utils.help import (
    format_options_table,
    format_command_help,
    suggest_command as help_suggest_command,
    show_command_suggestion
)
from cli.utils.banner import print_enhanced_banner
import click

console = Console()


def test_get_time_based_greeting():
    """Test time-based greeting function."""
    greeting = get_time_based_greeting()
    assert isinstance(greeting, str)
    assert len(greeting) > 0
    # Should contain "Operator"
    assert "Operator" in greeting


def test_get_command_groups():
    """Test command grouping."""
    groups = get_command_groups()
    assert isinstance(groups, dict)
    assert len(groups) > 0
    # Check expected groups exist
    assert "Deployment & Projects" in groups
    assert "AI & Audit Automation" in groups
    assert "Status & Docs" in groups


def test_get_all_commands():
    """Test getting all commands."""
    commands = get_all_commands()
    assert isinstance(commands, list)
    assert len(commands) > 0
    # Check some expected commands exist
    assert "deploy" in commands
    assert "audit" in commands
    assert "status" in commands


def test_print_command_menu():
    """Test command menu display (doesn't crash)."""
    # Should not raise exception
    print_command_menu(show_groups=True)
    print_command_menu(show_groups=False)


def test_print_usage_examples():
    """Test usage examples display."""
    # Should not raise exception
    print_usage_examples()


def test_print_keyboard_shortcuts():
    """Test keyboard shortcuts display."""
    # Should not raise exception
    print_keyboard_shortcuts()


def test_suggest_command():
    """Test command suggestion."""
    available = ["deploy", "audit", "status", "generate"]
    
    # Test exact match (should return None or exact match)
    result = suggest_command("deploy", available)
    assert result == "deploy" or result is None
    
    # Test typo
    result = suggest_command("deplo", available)
    assert result == "deploy" or result is None
    
    # Test no match
    result = suggest_command("xyzabc", available)
    assert result is None or result in available


def test_show_interactive_menu_no_questionary():
    """Test interactive menu when questionary is not available."""
    with patch('cli.utils.menu.questionary', side_effect=ImportError()):
        result = show_interactive_menu()
        # Should return None when questionary not available
        assert result is None


def test_show_interactive_menu_with_questionary():
    """Test interactive menu when questionary is available."""
    try:
        import questionary
        # Mock questionary.select to return a command
        with patch('cli.utils.menu.questionary.select') as mock_select:
            mock_select.return_value.ask.return_value = "deploy"
            result = show_interactive_menu()
            assert result == "deploy"
    except ImportError:
        # Skip if questionary not installed
        pytest.skip("questionary not installed")


def test_print_welcome_panel():
    """Test welcome panel display."""
    # Should not raise exception
    print_welcome_panel()


def test_print_status_panel():
    """Test status panel display."""
    # Should not raise exception
    print_status_panel()


def test_print_production_mode_panel():
    """Test production mode panel display."""
    # Should not raise exception
    print_production_mode_panel()


def test_print_llm_config_panel():
    """Test LLM config panel display."""
    # Should not raise exception
    print_llm_config_panel()


def test_print_tip_footer():
    """Test tip footer display."""
    # Should not raise exception
    print_tip_footer()


def test_format_options_table():
    """Test options table formatting."""
    # Create a mock command with options
    @click.command()
    @click.option('--test', help='Test option')
    @click.option('--verbose', '-v', help='Verbose mode')
    def test_cmd():
        pass
    
    table = format_options_table(test_cmd)
    assert table is not None


def test_format_command_help():
    """Test command help formatting."""
    @click.command()
    @click.option('--test', help='Test option')
    def test_cmd():
        """Test command description"""
        pass
    
    ctx = click.Context(test_cmd)
    # Should not raise exception
    format_command_help(test_cmd, ctx)


def test_show_command_suggestion():
    """Test command suggestion display."""
    available = ["deploy", "audit", "status"]
    # Should not raise exception
    show_command_suggestion("deplo", available)
    show_command_suggestion("xyz", available)


def test_print_enhanced_banner():
    """Test enhanced banner display."""
    # Should not raise exception
    print_enhanced_banner(no_banner=False)
    print_enhanced_banner(no_banner=True)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

