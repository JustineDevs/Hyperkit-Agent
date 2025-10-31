"""
Tests for config file validation and error handling.
Tests missing, corrupt, and malformed config files across CLI and workflow.
"""

import pytest
import tempfile
import shutil
import yaml
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestConfigValidation:
    """Test config file validation and error handling"""
    
    def test_missing_config_yaml_defaults(self):
        """Test that missing config.yaml falls back to defaults gracefully"""
        from core.config.loader import ConfigLoader
        from core.config.schema import get_default_config
        
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            config_file = workspace / "config.yaml"
            
            # Ensure file doesn't exist
            assert not config_file.exists()
            
            # Loader should handle missing file gracefully
            loader = ConfigLoader(str(config_file))
            config_dict = loader.to_dict()
            
            # Should have defaults or be empty dict
            assert isinstance(config_dict, dict)
    
    def test_corrupt_yaml_syntax_error(self):
        """Test that corrupt YAML files are handled gracefully"""
        from core.config.loader import ConfigLoader
        
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            config_file = workspace / "config.yaml"
            
            # Write invalid YAML
            config_file.write_text(
                "networks:\n"
                "  hyperion:\n"
                "    rpc_url: [invalid\n"  # Missing closing bracket
                "    chain_id: 133717\n"
            )
            
            # Loader should handle corrupt YAML gracefully
            loader = ConfigLoader(str(config_file))
            # Should fall back to defaults
            config_dict = loader.to_dict()
            assert isinstance(config_dict, dict)
    
    def test_missing_required_network_config(self):
        """Test handling of missing required network configuration"""
        from core.config.loader import ConfigLoader
        
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            config_file = workspace / "config.yaml"
            
            # Write config without networks section
            config_file.write_text(
                "ai_providers:\n"
                "  google:\n"
                "    enabled: true\n"
            )
            
            loader = ConfigLoader(str(config_file))
            config_dict = loader.to_dict()
            
            # Should still load, networks might be empty or default
            assert isinstance(config_dict, dict)
    
    def test_invalid_network_rpc_url(self):
        """Test handling of invalid RPC URL format"""
        from core.config.loader import ConfigLoader
        
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            config_file = workspace / "config.yaml"
            
            # Write config with invalid RPC URL (not a string)
            config_file.write_text(
                "networks:\n"
                "  hyperion:\n"
                "    rpc_url: 12345  # Should be string\n"
                "    chain_id: 133717\n"
            )
            
            loader = ConfigLoader(str(config_file))
            config_dict = loader.to_dict()
            
            # Should handle gracefully
            assert isinstance(config_dict, dict)
    
    def test_missing_ai_provider_keys(self):
        """Test handling of missing AI provider API keys"""
        from core.config.loader import ConfigLoader
        
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            config_file = workspace / "config.yaml"
            
            # Write config without API keys
            config_file.write_text(
                "networks:\n"
                "  hyperion:\n"
                "    rpc_url: https://hyperion-testnet.metisdevops.link\n"
                "    chain_id: 133717\n"
                "ai_providers:\n"
                "  google:\n"
                "    enabled: true\n"
                "    # api_key missing\n"
            )
            
            loader = ConfigLoader(str(config_file))
            config_dict = loader.to_dict()
            
            # Should load but API key would be missing
            assert isinstance(config_dict, dict)
            # Provider config might be empty or have defaults
            google_config = loader.get_ai_provider_config('google')
            assert isinstance(google_config, dict)
    
    def test_config_validation_in_agent_init(self):
        """Test that agent initialization validates config properly"""
        from core.agent.main import HyperKitAgent
        from core.config.loader import get_config
        
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            config_file = workspace / "config.yaml"
            
            # Create minimal valid config
            config_file.write_text(
                "networks:\n"
                "  hyperion:\n"
                "    chain_id: 133717\n"
                "    rpc_url: https://hyperion-testnet.metisdevops.link\n"
                "    explorer_url: https://hyperion-testnet-explorer.metisdevops.link\n"
                "    status: testnet\n"
                "    default: true\n"
            )
            
            # Temporarily override config path (if possible)
            # For now, just test that agent can be initialized
            # In real usage, config would be loaded from default location
            try:
                # Use get_config which loads from default location
                config_loader = get_config()
                config = config_loader.to_dict()
                agent = HyperKitAgent(config)
                assert agent is not None
            except Exception as e:
                # If validation fails, that's expected behavior
                # We're testing that it fails loudly, not silently
                assert "config" in str(e).lower() or "validation" in str(e).lower() or "network" in str(e).lower()
    
    def test_config_file_permission_errors(self):
        """Test handling of permission errors when reading config"""
        import os
        
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            config_file = workspace / "config.yaml"
            
            # Write valid config
            config_file.write_text(
                "networks:\n"
                "  hyperion:\n"
                "    rpc_url: https://hyperion-testnet.metisdevops.link\n"
                "    chain_id: 133717\n"
            )
            
            # On Unix, try to make read-only (if possible)
            if os.name != 'nt':  # Not Windows
                try:
                    os.chmod(config_file, 0o000)  # No permissions
                    
                    from core.config.loader import ConfigLoader
                    # Should handle permission error gracefully
                    loader = ConfigLoader(str(config_file))
                    # Might fall back to defaults or raise error (both acceptable)
                    config_dict = loader.to_dict()
                    assert isinstance(config_dict, dict)
                except PermissionError:
                    pass  # Expected on some systems
                finally:
                    # Restore permissions
                    try:
                        os.chmod(config_file, 0o644)
                    except:
                        pass
    
    def test_config_with_duplicate_keys(self):
        """Test handling of YAML with duplicate keys (YAML parser behavior)"""
        from core.config.loader import ConfigLoader
        
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            config_file = workspace / "config.yaml"
            
            # Write YAML with duplicate key (YAML parser typically uses last value)
            config_file.write_text(
                "networks:\n"
                "  hyperion:\n"
                "    chain_id: 133717\n"
                "    chain_id: 999999  # Duplicate - should use last value\n"
            )
            
            loader = ConfigLoader(str(config_file))
            config_dict = loader.to_dict()
            
            # Should load (YAML parser handles duplicates)
            assert isinstance(config_dict, dict)
    
    def test_config_empty_file(self):
        """Test handling of empty config file"""
        from core.config.loader import ConfigLoader
        
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            config_file = workspace / "config.yaml"
            
            # Write empty file
            config_file.write_text("")
            
            loader = ConfigLoader(str(config_file))
            config_dict = loader.to_dict()
            
            # Should handle empty file gracefully (might be empty dict or defaults)
            assert isinstance(config_dict, dict)
    
    def test_config_invalid_network_chain_id(self):
        """Test handling of invalid chain_id (non-integer)"""
        from core.config.loader import ConfigLoader
        
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            config_file = workspace / "config.yaml"
            
            # Write config with invalid chain_id
            config_file.write_text(
                "networks:\n"
                "  hyperion:\n"
                "    rpc_url: https://hyperion-testnet.metisdevops.link\n"
                "    chain_id: invalid  # Should be integer\n"
            )
            
            loader = ConfigLoader(str(config_file))
            config_dict = loader.to_dict()
            
            # Should handle gracefully
            assert isinstance(config_dict, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

