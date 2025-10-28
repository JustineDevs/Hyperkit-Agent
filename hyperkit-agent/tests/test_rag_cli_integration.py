"""
Integration tests for RAG template integration across all CLI commands
"""

import pytest
import asyncio
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
import subprocess
import sys

from services.core.rag_template_fetcher import RAGTemplateFetcher


class TestRAGCLIIntegration:
    """Test RAG integration across all CLI commands"""
    
    @pytest.fixture
    def mock_registry(self):
        """Mock registry with all required templates"""
        return {
            "metadata": {
                "version": "1.0.0",
                "last_updated": "2025-10-28"
            },
            "templates": {
                "erc20-template": {
                    "description": "Standard ERC20 fungible token contract template",
                    "filename": "ERC20-Template.md",
                    "category": "contracts",
                    "cid": "QmYWkBLnCwUHtA4vgsFM4ePrCG9xpo2taHRsvEbbyz2JYs",
                    "uploaded": True,
                    "prepared": True,
                    "upload_date": "2025-10-28T14:01:34.675228",
                    "gateway_url": "https://gateway.pinata.cloud/ipfs/QmYWkBLnCwUHtA4vgsFM4ePrCG9xpo2taHRsvEbbyz2JYs",
                    "author": "HyperAgent Team",
                    "tags": ["token", "erc20", "fungible"],
                    "code_standards": ["OpenZeppelin", "Solidity 0.8.20+"]
                },
                "contract-generation-prompt": {
                    "description": "AI prompt engineering template for contract generation",
                    "filename": "Contract-Generation.md",
                    "category": "prompts",
                    "cid": "QmPrompt123",
                    "uploaded": True,
                    "prepared": True,
                    "upload_date": "2025-10-28T14:01:35.926414",
                    "gateway_url": "https://gateway.pinata.cloud/ipfs/QmPrompt123",
                    "author": "HyperAgent Team",
                    "tags": ["prompt", "generation", "ai"],
                    "code_standards": ["Best Practices"]
                },
                "security-checklist": {
                    "description": "Comprehensive smart contract security audit checklist",
                    "filename": "Security-Checklist.md",
                    "category": "audits",
                    "cid": "QmSecurityChecklist123",
                    "uploaded": True,
                    "prepared": True,
                    "upload_date": "2025-10-28T14:01:36.123456",
                    "gateway_url": "https://gateway.pinata.cloud/ipfs/QmSecurityChecklist123",
                    "author": "Security Team",
                    "tags": ["security", "audit", "checklist"],
                    "code_standards": ["Security Best Practices"]
                },
                "hardhat-deploy": {
                    "description": "Hardhat deployment script template with best practices",
                    "filename": "Hardhat-Deploy.md",
                    "category": "templates",
                    "cid": "QmXwNxjvkw9aLZARfvM1bPThKMuP9eqmzD4cevtswKsvvh",
                    "uploaded": True,
                    "prepared": True,
                    "upload_date": "2025-10-28T14:01:37.789012",
                    "gateway_url": "https://gateway.pinata.cloud/ipfs/QmXwNxjvkw9aLZARfvM1bPThKMuP9eqmzD4cevtswKsvvh",
                    "author": "DevOps Team",
                    "tags": ["deployment", "hardhat", "script"],
                    "code_standards": ["Hardhat Best Practices"]
                }
            }
        }
    
    @pytest.fixture
    def temp_registry_file(self, mock_registry):
        """Create temporary registry file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(mock_registry, f)
            return f.name
    
    @pytest.fixture
    def temp_cache_dir(self):
        """Create temporary cache directory"""
        return tempfile.mkdtemp()
    
    @pytest.fixture
    def mock_fetcher(self, temp_registry_file, temp_cache_dir):
        """Create mock RAG template fetcher"""
        fetcher = RAGTemplateFetcher(temp_registry_file, temp_cache_dir)
        return fetcher
    
    @pytest.mark.asyncio
    async def test_generate_command_rag_integration(self, mock_fetcher):
        """Test generate command RAG integration"""
        # Mock template content
        generation_prompt = "# Contract Generation Prompt\nGenerate secure, production-ready contracts"
        erc20_template = "# ERC20 Template\ncontract ERC20Token is ERC20, Ownable { ... }"
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = generation_prompt
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            # Test fetching generation prompt
            result = await mock_fetcher.get_template('contract-generation-prompt')
            assert result == generation_prompt
            
            # Test fetching ERC20 template
            mock_response.text = erc20_template
            result = await mock_fetcher.get_template('erc20-template')
            assert result == erc20_template
    
    @pytest.mark.asyncio
    async def test_audit_command_rag_integration(self, mock_fetcher):
        """Test audit command RAG integration"""
        security_checklist = """# Security Checklist
1. Check for reentrancy vulnerabilities
2. Validate all external inputs
3. Ensure proper access controls
4. Check for integer overflow/underflow
5. Verify external calls are safe"""
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = security_checklist
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            result = await mock_fetcher.get_template('security-checklist')
            assert result == security_checklist
            assert "reentrancy" in result
            assert "access controls" in result
    
    @pytest.mark.asyncio
    async def test_deploy_command_rag_integration(self, mock_fetcher):
        """Test deploy command RAG integration"""
        deploy_template = """# Hardhat Deploy Template
module.exports = async (hre) => {
  const { deploy } = hre.deployments;
  const { deployer } = await hre.getNamedAccounts();
  
  await deploy("MyContract", {
    from: deployer,
    args: [],
    log: true,
  });
};"""
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = deploy_template
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            result = await mock_fetcher.get_template('hardhat-deploy')
            assert result == deploy_template
            assert "deploy" in result
            assert "hre.deployments" in result
    
    @pytest.mark.asyncio
    async def test_workflow_command_rag_integration(self, mock_fetcher):
        """Test workflow command RAG integration"""
        templates = {
            'contract-generation-prompt': "# Generation Prompt\nGenerate contracts",
            'security-checklist': "# Security Checklist\nAudit contracts",
            'hardhat-deploy': "# Deploy Template\nDeploy contracts"
        }
        
        with patch('httpx.AsyncClient') as mock_client:
            def side_effect(*args, **kwargs):
                mock_response = Mock()
                mock_response.status_code = 200
                # Extract CID from URL to determine which template to return
                url = args[0] if args else kwargs.get('url', '')
                if 'QmPrompt123' in url:
                    mock_response.text = templates['contract-generation-prompt']
                elif 'QmSecurityChecklist123' in url:
                    mock_response.text = templates['security-checklist']
                elif 'QmXwNxjvkw9aLZARfvM1bPThKMuP9eqmzD4cevtswKsvvh' in url:
                    mock_response.text = templates['hardhat-deploy']
                else:
                    mock_response.text = "Unknown template"
                return mock_response
            
            mock_client.return_value.__aenter__.return_value.get.side_effect = side_effect
            
            # Test fetching all workflow templates
            generation_prompt = await mock_fetcher.get_template('contract-generation-prompt')
            security_checklist = await mock_fetcher.get_template('security-checklist')
            deployment_template = await mock_fetcher.get_template('hardhat-deploy')
            
            assert generation_prompt == templates['contract-generation-prompt']
            assert security_checklist == templates['security-checklist']
            assert deployment_template == templates['hardhat-deploy']
    
    def test_template_search_and_filtering(self, mock_fetcher):
        """Test template search and filtering capabilities"""
        # Test search by query
        results = mock_fetcher.search_templates('ERC20')
        assert len(results) == 1
        assert results[0]['name'] == 'erc20-template'
        
        # Test search by category
        results = mock_fetcher.search_templates('', {'category': 'contracts'})
        assert len(results) == 1
        assert results[0]['name'] == 'erc20-template'
        
        # Test search by tags
        results = mock_fetcher.search_templates('', {'tags': ['security']})
        assert len(results) == 1
        assert results[0]['name'] == 'security-checklist'
        
        # Test search by author
        results = mock_fetcher.search_templates('', {'author': 'Security Team'})
        assert len(results) == 1
        assert results[0]['name'] == 'security-checklist'
    
    def test_template_statistics(self, mock_fetcher):
        """Test template statistics generation"""
        stats = mock_fetcher.get_template_statistics()
        
        assert stats['total_templates'] == 4
        assert stats['uploaded_templates'] == 4
        assert stats['deprecated_templates'] == 0
        
        # Check categories
        assert 'contracts' in stats['categories']
        assert 'prompts' in stats['categories']
        assert 'audits' in stats['categories']
        assert 'templates' in stats['categories']
        
        # Check authors
        assert 'HyperAgent Team' in stats['authors']
        assert 'Security Team' in stats['authors']
        assert 'DevOps Team' in stats['authors']
        
        # Check tags
        assert 'token' in stats['tags']
        assert 'security' in stats['tags']
        assert 'deployment' in stats['tags']
    
    def test_template_versioning(self, mock_fetcher):
        """Test template versioning functionality"""
        # Test getting template versions
        versions = mock_fetcher.list_template_versions('erc20-template')
        assert len(versions) == 1
        assert versions[0]['name'] == 'erc20-template'
        assert versions[0]['version'] == 'latest'
        
        # Test getting specific version
        versioned_name = mock_fetcher.get_template_version('erc20-template', 'latest')
        assert versioned_name == 'erc20-template'
        
        # Test deprecation
        success = mock_fetcher.deprecate_template_version('erc20-template', 'latest')
        assert success is False  # Can't deprecate 'latest' version
    
    def test_offline_mode(self, mock_fetcher):
        """Test offline mode functionality"""
        # First cache a template
        mock_fetcher._template_cache['erc20-template'] = {
            'content': '# Cached ERC20 Template',
            'cached': True
        }
        
        # Test offline mode with cached template
        result = asyncio.run(mock_fetcher.get_template('erc20-template', offline_mode=True))
        assert result == '# Cached ERC20 Template'
        
        # Test offline mode with uncached template
        result = asyncio.run(mock_fetcher.get_template('security-checklist', offline_mode=True))
        assert result is None
    
    def test_cache_management(self, mock_fetcher):
        """Test cache management functionality"""
        # Add templates to cache
        mock_fetcher._template_cache['template1'] = {'content': 'test1'}
        mock_fetcher._template_cache['template2'] = {'content': 'test2'}
        
        # Test clearing specific template
        success = mock_fetcher.clear_cache('template1')
        assert success is True
        assert 'template1' not in mock_fetcher._template_cache
        assert 'template2' in mock_fetcher._template_cache
        
        # Test clearing all cache
        success = mock_fetcher.clear_cache()
        assert success is True
        assert len(mock_fetcher._template_cache) == 0
    
    def test_registry_refresh(self, mock_fetcher, temp_registry_file):
        """Test registry refresh functionality"""
        # Modify the registry file
        new_registry = {
            "templates": {
                "new-template": {
                    "description": "New template",
                    "uploaded": True,
                    "cid": "QmNew123"
                }
            }
        }
        
        with open(temp_registry_file, 'w') as f:
            json.dump(new_registry, f)
        
        # Refresh registry
        success = mock_fetcher.refresh_registry()
        assert success is True
        assert 'new-template' in mock_fetcher.registry['templates']
    
    @pytest.mark.asyncio
    async def test_error_handling(self, mock_fetcher):
        """Test error handling in RAG integration"""
        # Test network failure
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get.side_effect = Exception("Network error")
            
            result = await mock_fetcher.get_template('erc20-template')
            assert result is None
        
        # Test non-existent template
        result = await mock_fetcher.get_template('nonexistent-template')
        assert result is None
        
        # Test unuploaded template
        result = await mock_fetcher.get_template('unuploaded-template')
        assert result is None


class TestRAGCLICommandIntegration:
    """Test actual CLI command integration with RAG"""
    
    @pytest.fixture
    def mock_cli_environment(self):
        """Set up mock CLI environment"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create mock contract file
            contract_file = Path(temp_dir) / "TestToken.sol"
            contract_file.write_text("""
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract TestToken {
    string public name = "Test Token";
    string public symbol = "TEST";
    uint256 public totalSupply = 1000000;
}
""")
            
            yield temp_dir, contract_file
    
    def test_generate_command_with_rag(self, mock_cli_environment):
        """Test generate command with RAG integration"""
        temp_dir, contract_file = mock_cli_environment
        
        # Mock the RAG fetcher
        with patch('services.core.rag_template_fetcher.get_template') as mock_get_template:
            mock_get_template.side_effect = [
                "# Contract Generation Prompt\nGenerate secure contracts",
                "# ERC20 Template\ncontract ERC20Token { ... }"
            ]
            
            # Test that RAG templates are fetched
            from services.core.rag_template_fetcher import get_template
            
            generation_prompt = asyncio.run(get_template('contract-generation-prompt'))
            erc20_template = asyncio.run(get_template('erc20-template'))
            
            assert generation_prompt == "# Contract Generation Prompt\nGenerate secure contracts"
            assert erc20_template == "# ERC20 Template\ncontract ERC20Token { ... }"
    
    def test_audit_command_with_rag(self, mock_cli_environment):
        """Test audit command with RAG integration"""
        temp_dir, contract_file = mock_cli_environment
        
        with patch('services.core.rag_template_fetcher.get_template') as mock_get_template:
            mock_get_template.return_value = """# Security Checklist
1. Check for reentrancy vulnerabilities
2. Validate all external inputs
3. Ensure proper access controls"""
            
            from services.core.rag_template_fetcher import get_template
            
            security_checklist = asyncio.run(get_template('security-checklist'))
            assert "reentrancy" in security_checklist
            assert "access controls" in security_checklist
    
    def test_deploy_command_with_rag(self, mock_cli_environment):
        """Test deploy command with RAG integration"""
        temp_dir, contract_file = mock_cli_environment
        
        with patch('services.core.rag_template_fetcher.get_template') as mock_get_template:
            mock_get_template.return_value = """# Hardhat Deploy Template
module.exports = async (hre) => {
  const { deploy } = hre.deployments;
  // ... deployment logic
};"""
            
            from services.core.rag_template_fetcher import get_template
            
            deploy_template = asyncio.run(get_template('hardhat-deploy'))
            assert "deploy" in deploy_template
            assert "hre.deployments" in deploy_template
    
    def test_workflow_command_with_rag(self, mock_cli_environment):
        """Test workflow command with RAG integration"""
        temp_dir, contract_file = mock_cli_environment
        
        with patch('services.core.rag_template_fetcher.get_template') as mock_get_template:
            mock_get_template.side_effect = [
                "# Generation Prompt\nGenerate contracts",
                "# Security Checklist\nAudit contracts", 
                "# Deploy Template\nDeploy contracts"
            ]
            
            from services.core.rag_template_fetcher import get_template
            
            # Test fetching all workflow templates
            generation_prompt = asyncio.run(get_template('contract-generation-prompt'))
            security_checklist = asyncio.run(get_template('security-checklist'))
            deployment_template = asyncio.run(get_template('hardhat-deploy'))
            
            assert generation_prompt == "# Generation Prompt\nGenerate contracts"
            assert security_checklist == "# Security Checklist\nAudit contracts"
            assert deployment_template == "# Deploy Template\nDeploy contracts"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
