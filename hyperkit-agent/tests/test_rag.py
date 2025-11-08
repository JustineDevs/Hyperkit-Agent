"""
Comprehensive RAG (Retrieval-Augmented Generation) Tests
Consolidated from test_rag_cli_integration.py, test_rag_connections.py, and test_rag_template_integration.py

Tests IPFS Pinata RAG template integration across all CLI commands, connections, and template fetcher functionality.
Note: Obsidian RAG has been removed - IPFS Pinata is now exclusive
"""

import pytest
import asyncio
import tempfile
import json
import sys
import logging
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
import httpx

from services.core.rag_template_fetcher import RAGTemplateFetcher, get_template, list_templates
from services.rag.ipfs_rag import get_ipfs_rag
from core.config.loader import get_config

# Suppress warnings for cleaner test output
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('asyncio').setLevel(logging.WARNING)
logging.getLogger('web3').setLevel(logging.WARNING)
logging.getLogger('alith').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)


# ============================================================================
# Shared Fixtures
# ============================================================================

@pytest.fixture
def mock_registry():
    """Mock registry data for template fetcher tests"""
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
def temp_registry_file(mock_registry):
    """Create temporary registry file"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(mock_registry, f)
        return f.name


@pytest.fixture
def temp_cache_dir():
    """Create temporary cache directory"""
    return tempfile.mkdtemp()


@pytest.fixture
def fetcher(temp_registry_file, temp_cache_dir):
    """Create RAG template fetcher instance"""
    return RAGTemplateFetcher(temp_registry_file, temp_cache_dir)


@pytest.fixture
def mock_fetcher(temp_registry_file, temp_cache_dir):
    """Create mock RAG template fetcher"""
    return RAGTemplateFetcher(temp_registry_file, temp_cache_dir)


@pytest.fixture
def mock_cli_environment():
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


# ============================================================================
# Section 1: RAG Template Fetcher Tests
# ============================================================================

@pytest.mark.integration
class TestRAGTemplateFetcher:
    """Test RAG template fetcher core functionality"""
    
    def test_init(self, fetcher, mock_registry):
        """Test fetcher initialization"""
        assert fetcher.registry == mock_registry
        assert len(fetcher.registry['templates']) == 5
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
        assert len(templates) == 5
        
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
    
    def test_template_search_and_filtering(self, fetcher):
        """Test template search and filtering capabilities"""
        # Test search by query
        results = fetcher.search_templates('ERC20')
        assert len(results) == 1
        assert results[0]['name'] == 'erc20-template'
        
        # Test search by category
        results = fetcher.search_templates('', {'category': 'contracts'})
        assert len(results) == 2  # erc20-template and unuploaded-template
        
        # Test search by tags
        results = fetcher.search_templates('', {'tags': ['security']})
        assert len(results) == 1
        assert results[0]['name'] == 'security-checklist'
        
        # Test search by author
        results = fetcher.search_templates('', {'author': 'Security Team'})
        assert len(results) == 1
        assert results[0]['name'] == 'security-checklist'
    
    def test_template_statistics(self, fetcher):
        """Test template statistics generation"""
        stats = fetcher.get_template_statistics()
        
        assert stats['total_templates'] == 5
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
    
    def test_template_versioning(self, fetcher):
        """Test template versioning functionality"""
        # Test getting template versions
        versions = fetcher.list_template_versions('erc20-template')
        assert len(versions) == 1
        assert versions[0]['name'] == 'erc20-template'
        assert versions[0]['version'] == 'latest'
        
        # Test getting specific version
        versioned_name = fetcher.get_template_version('erc20-template', 'latest')
        assert versioned_name == 'erc20-template'
        
        # Test deprecation
        success = fetcher.deprecate_template_version('erc20-template', 'latest')
        assert success is False  # Can't deprecate 'latest' version
    
    def test_offline_mode_sync(self, fetcher):
        """Test offline mode functionality (synchronous wrapper)"""
        # First cache a template
        fetcher._template_cache['erc20-template'] = {
            'content': '# Cached ERC20 Template',
            'cached': True
        }
        
        # Test offline mode with cached template
        result = asyncio.run(fetcher.get_template('erc20-template', offline_mode=True))
        assert result == '# Cached ERC20 Template'
        
        # Test offline mode with uncached template
        result = asyncio.run(fetcher.get_template('security-checklist', offline_mode=True))
        assert result is None


# ============================================================================
# Section 2: RAG CLI Integration Tests
# ============================================================================

@pytest.mark.integration
class TestRAGCLIIntegration:
    """Test RAG integration across all CLI commands"""
    
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


@pytest.mark.integration
class TestRAGCLICommandIntegration:
    """Test actual CLI command integration with RAG"""
    
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


# ============================================================================
# Section 3: RAG Connection Tests
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_all_rag_connections():
    """Test all RAG connections and return comprehensive results."""
    
    print("🔍 Testing RAG Connections...")
    print("=" * 60)
    
    results = {
        "timestamp": str(asyncio.get_event_loop().time()),
        "overall_status": "unknown",
        "components": {}
    }
    
    # Test 1: IPFS Pinata RAG
    print("\n1. Testing IPFS Pinata RAG Connection...")
    try:
        config = get_config().to_dict()
        ipfs_rag = get_ipfs_rag(config)
        connection_results = await ipfs_rag.test_connections()
        results["components"]["ipfs_pinata"] = connection_results
        
        status = connection_results.get("status", "failed")
        pinata_enabled = connection_results.get("pinata_enabled", False)
        registry_loaded = connection_results.get("cid_registry_loaded", False)
        
        print(f"   Pinata Enabled: {'✅' if pinata_enabled else '❌'}")
        print(f"   CID Registry: {'✅' if registry_loaded else '❌'}")
        print(f"   Overall Status: {'✅ PASSED' if status == 'success' else '❌ FAILED'}")
        
    except Exception as e:
        results["components"]["ipfs_pinata"] = {
            "status": "error",
            "error": str(e)
        }
        print(f"   IPFS Pinata RAG: ❌ ERROR - {e}")
    
    # Test 2: Configuration Check
    print("\n2. Testing Configuration...")
    try:
        config = get_config().to_dict()
        
        # Check Pinata IPFS config
        pinata_config = config.get("storage", {}).get("pinata", {})
        
        config_status = {
            "pinata_api_key": bool(pinata_config.get("api_key")),
            "pinata_secret_key": bool(pinata_config.get("secret_key")),
            "cid_registry_exists": Path("docs/RAG_TEMPLATES/cid-registry.json").exists()
        }
        
        results["components"]["configuration"] = config_status
        
        print(f"   Pinata API Key: {'✅' if config_status['pinata_api_key'] else '❌'}")
        print(f"   Pinata Secret Key: {'✅' if config_status['pinata_secret_key'] else '❌'}")
        print(f"   CID Registry File: {'✅' if config_status['cid_registry_exists'] else '❌'}")
        
    except Exception as e:
        results["components"]["configuration"] = {
            "status": "error",
            "error": str(e)
        }
        print(f"   Configuration: ❌ ERROR - {e}")
    
    # Test 3: Content Retrieval Test
    print("\n3. Testing Content Retrieval...")
    try:
        config = get_config().to_dict()
        ipfs_rag = get_ipfs_rag(config)
        test_content = await ipfs_rag.retrieve("smart contract security", max_results=3)
        
        retrieval_status = {
            "content_length": len(test_content),
            "has_content": len(test_content) > 100,
            "preview": test_content[:200] + "..." if len(test_content) > 200 else test_content
        }
        
        results["components"]["content_retrieval"] = retrieval_status
        
        print(f"   Content Length: {retrieval_status['content_length']} characters")
        print(f"   Has Content: {'✅' if retrieval_status['has_content'] else '❌'}")
        print(f"   Preview: {retrieval_status['preview']}")
        
    except Exception as e:
        results["components"]["content_retrieval"] = {
            "status": "error",
            "error": str(e)
        }
        print(f"   Content Retrieval: ❌ ERROR - {e}")
    
    # Determine overall status
    print("\n" + "=" * 60)
    print("📊 Overall Status Assessment")
    print("=" * 60)
    
    success_count = 0
    total_tests = 0
    
    for component, status in results["components"].items():
        if isinstance(status, dict):
            if status.get("status") == "success":
                success_count += 1
            total_tests += 1
    
    if success_count == total_tests and total_tests > 0:
        results["overall_status"] = "success"
        print("🎉 ALL TESTS PASSED!")
    elif success_count > 0:
        results["overall_status"] = "partial"
        print(f"⚠️  PARTIAL SUCCESS: {success_count}/{total_tests} components working")
    else:
        results["overall_status"] = "failed"
        print("❌ ALL TESTS FAILED!")
    
    # Save results
    results_file = Path("test_logs/rag_connection_test_results.json")
    results_file.parent.mkdir(exist_ok=True)
    results_file.write_text(json.dumps(results, indent=2))
    print(f"\n📄 Results saved to: {results_file}")
    
    return results


# ============================================================================
# Section 4: RAG Template Convenience Functions
# ============================================================================

@pytest.mark.integration
class TestRAGTemplateConvenienceFunctions:
    """Test convenience functions for RAG template access"""
    
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
        from services.core.rag_template_fetcher import get_templates_by_category
        
        with patch('services.core.rag_template_fetcher.get_template_fetcher') as mock_get_fetcher:
            mock_fetcher = Mock()
            mock_fetcher.get_templates_by_category.return_value = [{'name': 'test', 'category': 'contracts'}]
            mock_get_fetcher.return_value = mock_fetcher
            
            result = get_templates_by_category('contracts')
            assert result == [{'name': 'test', 'category': 'contracts'}]
            mock_fetcher.get_templates_by_category.assert_called_once_with('contracts')


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

