"""
Production Mode Tests
Enforces that production code uses only current config/services (no mocks, no deprecated)
"""

import pytest
import os
import re
from pathlib import Path


class TestProductionMode:
    """Test that production code enforces current architecture"""
    
    def test_no_obsidian_rag_in_production(self):
        """Test that Obsidian RAG is not used in production code"""
        project_root = Path(__file__).parent.parent
        issues = []
        
        exclude_dirs = {'__pycache__', '.git', 'node_modules', '.pytest_cache', 'tests', 'docs'}
        
        for root, dirs, files in os.walk(project_root):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            for file in files:
                if file.endswith('.py'):
                    file_path = Path(root) / file
                    try:
                        content = file_path.read_text(encoding='utf-8')
                        # Check for Obsidian RAG imports (deprecated)
                        if 'obsidian_rag' in content.lower() and 'deprecated' not in content.lower()[:300]:
                            if 'from services.rag.obsidian' in content or 'import.*obsidian.*rag' in content.lower():
                                issues.append(str(file_path.relative_to(project_root)))
                    except:
                        pass
        
        if issues:
            pytest.fail(f"Found Obsidian RAG usage in production code (should use IPFS Pinata): {issues}")
    
    def test_no_lazai_ai_agent_in_production(self):
        """Test that LazAI AI agent is not used (LazAI is network-only)"""
        project_root = Path(__file__).parent.parent
        issues = []
        
        exclude_dirs = {'__pycache__', '.git', 'node_modules', '.pytest_cache', 'tests', 'docs'}
        
        for root, dirs, files in os.walk(project_root):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            for file in files:
                if file.endswith('.py') and 'test' not in file.lower():
                    file_path = Path(root) / file
                    try:
                        content = file_path.read_text(encoding='utf-8')
                        # Check for LazAI AI agent usage (should only be network config)
                        if re.search(r'lazai.*agent|lazai_api_key.*ai', content, re.IGNORECASE):
                            if 'network-only' not in content.lower()[:500] and 'deprecated' not in content.lower()[:500]:
                                # Allow if clearly marked as network-only
                                if 'network.*only|blockchain.*rpc|not.*ai' not in content.lower()[:500]:
                                    issues.append(str(file_path.relative_to(project_root)))
                    except:
                        pass
        
        if issues:
            pytest.fail(f"Found LazAI AI agent usage (LazAI is network-only, use Alith SDK for AI): {issues}")
    
    def test_alith_uses_openai_key(self):
        """Test that Alith SDK uses OpenAI key, not LazAI key"""
        project_root = Path(__file__).parent.parent
        ai_agent_file = project_root / "services" / "core" / "ai_agent.py"
        
        if ai_agent_file.exists():
            content = ai_agent_file.read_text(encoding='utf-8')
            
            # Should use OpenAI key for Alith
            assert 'OPENAI_API_KEY' in content or 'openai.*api.*key' in content.lower(), \
                "Alith SDK should use OpenAI API key"
            
            # Should NOT require LazAI key for AI agent
            if 'LAZAI_API_KEY' in content and 'network-only' not in content[:1000]:
                pytest.fail("Alith SDK should not use LAZAI_API_KEY (LazAI is network-only)")
    
    def test_ipfs_pinata_rag_exclusive(self):
        """Test that IPFS Pinata is the exclusive RAG backend"""
        project_root = Path(__file__).parent.parent
        rag_file = project_root / "services" / "rag" / "ipfs_rag.py"
        
        if rag_file.exists():
            content = rag_file.read_text(encoding='utf-8')
            
            # Should enforce Pinata config
            assert 'PINATA_API_KEY' in content, "IPFS RAG should require Pinata keys"
            assert 'raise RuntimeError' in content or 'fail' in content.lower(), \
                "IPFS RAG should fail hard if not configured (no mock fallbacks)"
    
    def test_network_chain_ids_correct(self):
        """Test that network chain IDs are correct"""
        from services.deployment.foundry_deployer import FoundryDeployer
        
        deployer = FoundryDeployer()
        expected_chain_ids = {
            'hyperion': 133717,
            'lazai': 9001,
            'metis': 1088
        }
        
        for network, expected_id in expected_chain_ids.items():
            config = deployer.get_network_config(network)
            assert config is not None, f"Network {network} not configured"
            assert config['chain_id'] == expected_id, \
                f"Network {network} has wrong chain_id: {config['chain_id']}, expected {expected_id}"

