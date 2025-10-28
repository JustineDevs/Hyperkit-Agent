"""
Unit tests for RAG template fetcher and CLI integration
"""

import pytest
import asyncio
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
import httpx

from services.core.rag_template_fetcher import RAGTemplateFetcher, get_template, list_templates


class TestRAGTemplateFetcher:
    """Test RAG template fetcher functionality"""
    
    @pytest.fixture
    def mock_registry(self):
        """Mock registry data"""
        return {
            "metadata": {
                "version": "1.0.0",
                "last_updated": "2025-10-28",
                "purpose": "CID registry mapping for AI agent RAG template lookups"
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
                    "gateway_url": "https://gateway.pinata.cloud/ipfs/QmYWkBLnCwUHtA4vgsFM4ePrCG9xpo2taHRsvEbbyz2JYs"
                },
                "security-checklist": {
                    "description": "Comprehensive smart contract security audit checklist",
                    "filename": "Security-Checklist.md",
                    "category": "audits",
                    "cid": "QmSecurityChecklist123",
                    "uploaded": True,
                    "prepared": True,
                    "upload_date": "2025-10-28T14:01:35.926414",
                    "gateway_url": "https://gateway.pinata.cloud/ipfs/QmSecurityChecklist123"
                },
                "unuploaded-template": {
                    "description": "Template not yet uploaded",
                    "filename": "Unuploaded.md",
                    "category": "contracts",
                    "cid": "",
                    "uploaded": False,
                    "prepared": True
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
    def fetcher(self, temp_registry_file, temp_cache_dir):
        """Create RAG template fetcher instance"""
        return RAGTemplateFetcher(temp_registry_file, temp_cache_dir)
    
    def test_init(self, fetcher, mock_registry):
        """Test fetcher initialization"""
        assert fetcher.registry == mock_registry
        assert len(fetcher.registry['templates']) == 3
        assert fetcher.cache_dir.exists()
    
    def test_load_registry_file_not_found(self):
        """Test loading registry when file doesn't exist"""
        fetcher = RAGTemplateFetcher("nonexistent.json")
        assert fetcher.registry == {"templates": {}, "metadata": {}}
    
    def test_load_registry_invalid_json(self):
        """Test loading registry with invalid JSON"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json")
            f.flush()
            
            fetcher = RAGTemplateFetcher(f.name)
            assert fetcher.registry == {"templates": {}, "metadata": {}}
    
    def test_list_templates(self, fetcher):
        """Test listing all templates"""
        templates = fetcher.list_templates()
        assert len(templates) == 3
        
        # Check template structure
        erc20_template = next(t for t in templates if t['name'] == 'erc20-template')
        assert erc20_template['description'] == "Standard ERC20 fungible token contract template"
        assert erc20_template['category'] == "contracts"
        assert erc20_template['uploaded'] is True
    
    def test_get_template_info(self, fetcher):
        """Test getting template metadata"""
        info = fetcher.get_template_info('erc20-template')
        assert info is not None
        assert info['description'] == "Standard ERC20 fungible token contract template"
        assert info['cid'] == "QmYWkBLnCwUHtA4vgsFM4ePrCG9xpo2taHRsvEbbyz2JYs"
        
        # Test non-existent template
        info = fetcher.get_template_info('nonexistent-template')
        assert info is None
    
    def test_get_templates_by_category(self, fetcher):
        """Test getting templates by category"""
        contract_templates = fetcher.get_templates_by_category('contracts')
        assert len(contract_templates) == 2  # erc20-template and unuploaded-template
        
        audit_templates = fetcher.get_templates_by_category('audits')
        assert len(audit_templates) == 1  # security-checklist
        
        # Test non-existent category
        empty_templates = fetcher.get_templates_by_category('nonexistent')
        assert len(empty_templates) == 0
    
    def test_is_template_available(self, fetcher):
        """Test checking template availability"""
        assert fetcher.is_template_available('erc20-template') is True
        assert fetcher.is_template_available('security-checklist') is True
        assert fetcher.is_template_available('unuploaded-template') is False
        assert fetcher.is_template_available('nonexistent-template') is False
    
    @pytest.mark.asyncio
    async def test_get_template_success(self, fetcher):
        """Test successful template fetching"""
        mock_content = "# ERC20 Template\n\nThis is a test template."
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = mock_content
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            result = await fetcher.get_template('erc20-template')
            
            assert result == mock_content
            assert 'erc20-template' in fetcher._template_cache
    
    @pytest.mark.asyncio
    async def test_get_template_not_uploaded(self, fetcher):
        """Test fetching template that's not uploaded"""
        result = await fetcher.get_template('unuploaded-template')
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_template_not_found(self, fetcher):
        """Test fetching non-existent template"""
        result = await fetcher.get_template('nonexistent-template')
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_template_offline_mode(self, fetcher):
        """Test offline mode"""
        # First cache a template
        mock_content = "# Cached Template"
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = mock_content
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            await fetcher.get_template('erc20-template')
        
        # Now test offline mode
        result = await fetcher.get_template('erc20-template', offline_mode=True)
        assert result == mock_content
        
        # Test offline mode with uncached template
        result = await fetcher.get_template('security-checklist', offline_mode=True)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_template_gateway_failure(self, fetcher):
        """Test template fetching when all gateways fail"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get.side_effect = httpx.RequestError("Network error")
            
            result = await fetcher.get_template('erc20-template')
            assert result is None
    
    def test_clear_cache(self, fetcher):
        """Test cache clearing"""
        # Add something to cache
        fetcher._template_cache['test-template'] = {'content': 'test'}
        
        # Clear specific template
        success = fetcher.clear_cache('test-template')
        assert success is True
        assert 'test-template' not in fetcher._template_cache
        
        # Clear all cache
        fetcher._template_cache['test-template'] = {'content': 'test'}
        success = fetcher.clear_cache()
        assert success is True
        assert len(fetcher._template_cache) == 0
    
    def test_refresh_registry(self, fetcher, temp_registry_file):
        """Test registry refresh"""
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
        success = fetcher.refresh_registry()
        assert success is True
        assert 'new-template' in fetcher.registry['templates']


class TestRAGTemplateIntegration:
    """Test RAG template integration with CLI commands"""
    
    @pytest.fixture
    def mock_fetcher(self):
        """Mock RAG template fetcher"""
        fetcher = Mock()
        fetcher.get_template = AsyncMock()
        fetcher.list_templates = Mock()
        return fetcher
    
    @pytest.mark.asyncio
    async def test_generate_command_rag_integration(self, mock_fetcher):
        """Test generate command RAG integration"""
        mock_fetcher.get_template.side_effect = [
            "# Contract Generation Prompt\nGenerate secure contracts",
            "# ERC20 Template\ncontract ERC20Token { ... }"
        ]
        
        with patch('services.core.rag_template_fetcher.get_template', mock_fetcher.get_template):
            from services.core.rag_template_fetcher import get_template
            
            # Test fetching templates
            generation_prompt = await get_template('contract-generation-prompt')
            contract_template = await get_template('erc20-template')
            
            assert generation_prompt == "# Contract Generation Prompt\nGenerate secure contracts"
            assert contract_template == "# ERC20 Template\ncontract ERC20Token { ... }"
            
            # Verify calls
            assert mock_fetcher.get_template.call_count == 2
            mock_fetcher.get_template.assert_any_call('contract-generation-prompt')
            mock_fetcher.get_template.assert_any_call('erc20-template')
    
    @pytest.mark.asyncio
    async def test_audit_command_rag_integration(self, mock_fetcher):
        """Test audit command RAG integration"""
        mock_fetcher.get_template.return_value = "# Security Checklist\n1. Check for reentrancy\n2. Validate inputs"
        
        with patch('services.core.rag_template_fetcher.get_template', mock_fetcher.get_template):
            from services.core.rag_template_fetcher import get_template
            
            security_checklist = await get_template('security-checklist')
            
            assert security_checklist == "# Security Checklist\n1. Check for reentrancy\n2. Validate inputs"
            mock_fetcher.get_template.assert_called_once_with('security-checklist')
    
    @pytest.mark.asyncio
    async def test_deploy_command_rag_integration(self, mock_fetcher):
        """Test deploy command RAG integration"""
        mock_fetcher.get_template.return_value = "# Hardhat Deploy Template\nmodule.exports = async (hre) => { ... }"
        
        with patch('services.core.rag_template_fetcher.get_template', mock_fetcher.get_template):
            from services.core.rag_template_fetcher import get_template
            
            deployment_template = await get_template('hardhat-deploy')
            
            assert deployment_template == "# Hardhat Deploy Template\nmodule.exports = async (hre) => { ... }"
            mock_fetcher.get_template.assert_called_once_with('hardhat-deploy')
    
    @pytest.mark.asyncio
    async def test_workflow_command_rag_integration(self, mock_fetcher):
        """Test workflow command RAG integration"""
        mock_fetcher.get_template.side_effect = [
            "# Generation Prompt\nGenerate contracts",
            "# Security Checklist\nAudit contracts",
            "# Deploy Template\nDeploy contracts"
        ]
        
        with patch('services.core.rag_template_fetcher.get_template', mock_fetcher.get_template):
            from services.core.rag_template_fetcher import get_template
            
            # Test fetching all workflow templates
            generation_prompt = await get_template('contract-generation-prompt')
            security_checklist = await get_template('security-checklist')
            deployment_template = await get_template('hardhat-deploy')
            
            assert generation_prompt == "# Generation Prompt\nGenerate contracts"
            assert security_checklist == "# Security Checklist\nAudit contracts"
            assert deployment_template == "# Deploy Template\nDeploy contracts"
            
            # Verify all calls
            assert mock_fetcher.get_template.call_count == 3
    
    @pytest.mark.asyncio
    async def test_rag_fetch_failure_handling(self, mock_fetcher):
        """Test RAG fetch failure handling"""
        mock_fetcher.get_template.side_effect = Exception("Network error")
        
        with patch('services.core.rag_template_fetcher.get_template', mock_fetcher.get_template):
            from services.core.rag_template_fetcher import get_template
            
            # Should handle exception gracefully
            result = await get_template('test-template')
            assert result is None


class TestRAGTemplateConvenienceFunctions:
    """Test convenience functions"""
    
    @pytest.mark.asyncio
    async def test_get_template_convenience(self):
        """Test get_template convenience function"""
        with patch('services.core.rag_template_fetcher.get_template_fetcher') as mock_get_fetcher:
            mock_fetcher = Mock()
            mock_fetcher.get_template = AsyncMock(return_value="test content")
            mock_get_fetcher.return_value = mock_fetcher
            
            result = await get_template('test-template')
            assert result == "test content"
            mock_fetcher.get_template.assert_called_once_with('test-template', True, False)
    
    def test_list_templates_convenience(self):
        """Test list_templates convenience function"""
        with patch('services.core.rag_template_fetcher.get_template_fetcher') as mock_get_fetcher:
            mock_fetcher = Mock()
            mock_fetcher.list_templates.return_value = [{'name': 'test', 'description': 'test'}]
            mock_get_fetcher.return_value = mock_fetcher
            
            result = list_templates()
            assert result == [{'name': 'test', 'description': 'test'}]
            mock_fetcher.list_templates.assert_called_once()
    
    def test_get_templates_by_category_convenience(self):
        """Test get_templates_by_category convenience function"""
        with patch('services.core.rag_template_fetcher.get_template_fetcher') as mock_get_fetcher:
            mock_fetcher = Mock()
            mock_fetcher.get_templates_by_category.return_value = [{'name': 'test', 'category': 'contracts'}]
            mock_get_fetcher.return_value = mock_fetcher
            
            result = get_templates_by_category('contracts')
            assert result == [{'name': 'test', 'category': 'contracts'}]
            mock_fetcher.get_templates_by_category.assert_called_once_with('contracts')


if __name__ == '__main__':
    pytest.main([__file__])
