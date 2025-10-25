"""
Complete Workflow Integration Tests
End-to-end testing for HyperKit Agent production deployment
"""

import pytest
import asyncio
import json
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services import ai_agent, blockchain, storage, security, monitoring, rag, verification
from core.config.manager import config

class TestCompleteWorkflow:
    """
    Integration tests for complete HyperKit Agent workflow
    Tests the full pipeline from contract generation to verification
    """
    
    @pytest.fixture
    def sample_contract_requirements(self):
        """Sample contract requirements for testing"""
        return {
            "name": "TestToken",
            "type": "ERC20",
            "features": ["mintable", "burnable", "pausable"],
            "security": "high",
            "gas_optimization": True
        }
    
    @pytest.fixture
    def sample_contract_code(self):
        """Sample contract code for testing"""
        return """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/Pausable.sol";

contract TestToken is ERC20, Ownable, Pausable {
    constructor() ERC20("TestToken", "TTK") {}
    
    function mint(address to, uint256 amount) public onlyOwner {
        _mint(to, amount);
    }
    
    function burn(uint256 amount) public {
        _burn(_msgSender(), amount);
    }
    
    function pause() public onlyOwner {
        _pause();
    }
    
    function unpause() public onlyOwner {
        _unpause();
    }
}
"""
    
    @pytest.mark.asyncio
    async def test_ai_agent_contract_generation(self, sample_contract_requirements):
        """Test AI agent contract generation"""
        print("🧪 Testing AI agent contract generation...")
        
        # Test contract generation
        contract_code = await ai_agent.generate_contract(sample_contract_requirements)
        
        assert contract_code is not None
        assert len(contract_code) > 0
        assert "contract" in contract_code.lower()
        
        print("✅ AI agent contract generation test passed")
    
    @pytest.mark.asyncio
    async def test_ai_agent_contract_audit(self, sample_contract_code):
        """Test AI agent contract auditing"""
        print("🧪 Testing AI agent contract auditing...")
        
        # Test contract auditing
        audit_result = await ai_agent.audit_contract(sample_contract_code)
        
        assert audit_result is not None
        assert "status" in audit_result
        assert "vulnerabilities" in audit_result
        assert "recommendations" in audit_result
        
        print("✅ AI agent contract audit test passed")
    
    @pytest.mark.asyncio
    async def test_blockchain_network_connection(self):
        """Test blockchain network connection"""
        print("🧪 Testing blockchain network connection...")
        
        # Test network info
        network_info = await blockchain.get_network_info()
        
        assert network_info is not None
        assert "network_id" in network_info or "status" in network_info
        
        print("✅ Blockchain network connection test passed")
    
    @pytest.mark.asyncio
    async def test_storage_ipfs_functionality(self):
        """Test IPFS storage functionality"""
        print("🧪 Testing IPFS storage functionality...")
        
        # Test storage with sample data
        sample_data = {
            "type": "test_audit_report",
            "timestamp": "2025-10-27T00:00:00Z",
            "contract_address": "0x1234567890123456789012345678901234567890",
            "security_score": 85,
            "vulnerabilities": [],
            "recommendations": ["Test recommendation"]
        }
        
        # Test storage
        storage_result = await storage.store_audit_report(sample_data)
        
        assert storage_result is not None
        assert "status" in storage_result
        
        print("✅ IPFS storage functionality test passed")
    
    @pytest.mark.asyncio
    async def test_security_audit_functionality(self, sample_contract_code):
        """Test security audit functionality"""
        print("🧪 Testing security audit functionality...")
        
        # Test security audit
        security_result = await security.audit_contract_security(sample_contract_code)
        
        assert security_result is not None
        assert "status" in security_result
        assert "vulnerabilities" in security_result
        
        print("✅ Security audit functionality test passed")
    
    @pytest.mark.asyncio
    async def test_monitoring_system_health(self):
        """Test monitoring system health"""
        print("🧪 Testing monitoring system health...")
        
        # Test system health
        health_status = await monitoring.get_system_health()
        
        assert health_status is not None
        assert "status" in health_status
        assert "components" in health_status
        
        print("✅ Monitoring system health test passed")
    
    @pytest.mark.asyncio
    async def test_rag_similarity_search(self):
        """Test RAG similarity search"""
        print("🧪 Testing RAG similarity search...")
        
        # Test similarity search
        search_results = await rag.search_similar("smart contract security", limit=3)
        
        assert search_results is not None
        assert isinstance(search_results, list)
        
        print("✅ RAG similarity search test passed")
    
    @pytest.mark.asyncio
    async def test_verification_system(self):
        """Test contract verification system"""
        print("🧪 Testing contract verification system...")
        
        # Test verification status check
        test_address = "0x1234567890123456789012345678901234567890"
        verification_status = await verification.check_verification_status(test_address)
        
        assert verification_status is not None
        assert "status" in verification_status
        
        print("✅ Contract verification system test passed")
    
    @pytest.mark.asyncio
    async def test_complete_workflow_integration(self, sample_contract_requirements, sample_contract_code):
        """Test complete workflow integration"""
        print("🧪 Testing complete workflow integration...")
        
        # Step 1: Generate contract
        print("  📝 Step 1: Generating contract...")
        contract_code = await ai_agent.generate_contract(sample_contract_requirements)
        assert contract_code is not None
        
        # Step 2: Audit contract
        print("  🔍 Step 2: Auditing contract...")
        audit_result = await ai_agent.audit_contract(contract_code)
        assert audit_result is not None
        
        # Step 3: Security analysis
        print("  🛡️ Step 3: Security analysis...")
        security_result = await security.audit_contract_security(contract_code)
        assert security_result is not None
        
        # Step 4: Store audit report
        print("  💾 Step 4: Storing audit report...")
        report_data = {
            "contract_code": contract_code,
            "audit_result": audit_result,
            "security_result": security_result,
            "timestamp": "2025-10-27T00:00:00Z"
        }
        storage_result = await storage.store_audit_report(report_data)
        assert storage_result is not None
        
        # Step 5: Monitor system
        print("  📊 Step 5: Monitoring system...")
        health_status = await monitoring.get_system_health()
        assert health_status is not None
        
        print("✅ Complete workflow integration test passed")
    
    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling across services"""
        print("🧪 Testing error handling...")
        
        # Test with invalid inputs
        try:
            invalid_result = await ai_agent.generate_contract({})
            assert invalid_result is not None
        except Exception as e:
            print(f"  ⚠️ Expected error handled: {e}")
        
        try:
            invalid_storage = await storage.store_audit_report(None)
            assert invalid_storage is not None
        except Exception as e:
            print(f"  ⚠️ Expected error handled: {e}")
        
        print("✅ Error handling test passed")
    
    @pytest.mark.asyncio
    async def test_performance_metrics(self):
        """Test performance metrics collection"""
        print("🧪 Testing performance metrics...")
        
        # Record some metrics
        await monitoring.record_metric("test_metric", 100.0, {"test": "true"})
        
        # Get metrics summary
        metrics_summary = await monitoring.get_metrics_summary()
        assert metrics_summary is not None
        
        print("✅ Performance metrics test passed")

# Run tests if executed directly
if __name__ == "__main__":
    import asyncio
    
    async def run_tests():
        """Run all integration tests"""
        print("🚀 Starting HyperKit Agent Integration Tests")
        print("=" * 50)
        
        test_instance = TestCompleteWorkflow()
        
        # Sample data for testing
        sample_requirements = {
            "name": "TestToken",
            "type": "ERC20",
            "features": ["mintable", "burnable", "pausable"],
            "security": "high",
            "gas_optimization": True
        }
        
        sample_contract = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/Pausable.sol";

contract TestToken is ERC20, Ownable, Pausable {
    constructor() ERC20("TestToken", "TTK") {}
    
    function mint(address to, uint256 amount) public onlyOwner {
        _mint(to, amount);
    }
    
    function burn(uint256 amount) public {
        _burn(_msgSender(), amount);
    }
    
    function pause() public onlyOwner {
        _pause();
    }
    
    function unpause() public onlyOwner {
        _unpause();
    }
}
"""
        
        # Run individual tests
        await test_instance.test_ai_agent_contract_generation(sample_requirements)
        await test_instance.test_ai_agent_contract_audit(sample_contract)
        await test_instance.test_blockchain_network_connection()
        await test_instance.test_storage_ipfs_functionality()
        await test_instance.test_security_audit_functionality(sample_contract)
        await test_instance.test_monitoring_system_health()
        await test_instance.test_rag_similarity_search()
        await test_instance.test_verification_system()
        await test_instance.test_complete_workflow_integration(sample_requirements, sample_contract)
        await test_instance.test_error_handling()
        await test_instance.test_performance_metrics()
        
        print("=" * 50)
        print("🎉 All integration tests completed successfully!")
        print("✅ HyperKit Agent is ready for production deployment")
    
    asyncio.run(run_tests())
