"""
Basic tests for HyperKit AI Agent
"""
import pytest
import sys
import os

# Add the parent directory to the path so we can import the modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_imports():
    """Test that core modules can be imported"""
    try:
        from core.agent.main import HyperKitAgent
        from core.config.loader import get_config
        from core.intent_router import IntentRouter
        assert True
    except ImportError as e:
        pytest.fail(f"Failed to import core modules: {e}")

def test_config_loading():
    """Test that configuration can be loaded"""
    try:
        from core.config.loader import get_config
        config = get_config()
        assert config is not None
        assert hasattr(config, 'to_dict')
    except Exception as e:
        pytest.fail(f"Failed to load configuration: {e}")

def test_intent_router():
    """Test that intent router can be initialized"""
    try:
        from core.intent_router import IntentRouter
        router = IntentRouter()
        assert router is not None
        assert hasattr(router, 'classify_intent')
    except Exception as e:
        pytest.fail(f"Failed to initialize intent router: {e}")

def test_agent_initialization():
    """Test that the main agent can be initialized"""
    try:
        from core.agent.main import HyperKitAgent
        from core.config.loader import get_config
        
        config = get_config()
        agent = HyperKitAgent(config.to_dict())
        assert agent is not None
        assert hasattr(agent, 'process_request')
    except Exception as e:
        pytest.fail(f"Failed to initialize HyperKitAgent: {e}")

if __name__ == "__main__":
    pytest.main([__file__])
