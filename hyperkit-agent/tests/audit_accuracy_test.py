"""
Audit Accuracy Benchmark Testing
Tests the auditor against known vulnerable contracts to measure accuracy
"""

import asyncio
import pytest
from services.audit.auditor import SmartContractAuditor


class TestAuditAccuracy:
    """Test audit accuracy against known vulnerable contracts"""
    
    def setup_method(self):
        """Setup auditor for testing"""
        self.auditor = SmartContractAuditor()
    
    # DAO Hack Reentrancy Vulnerability
    DAO_HACK_CONTRACT = """
    // SPDX-License-Identifier: MIT
    pragma solidity ^0.4.0;
    
    contract DAOHack {
        mapping(address => uint) public balances;
        
        function withdraw() public {
            uint amount = balances[msg.sender];
            require(amount > 0);
            
            // CRITICAL: Reentrancy vulnerability
            if (msg.sender.call.value(amount)()) {
                balances[msg.sender] = 0;
            }
        }
        
        function deposit() public payable {
            balances[msg.sender] += msg.value;
        }
    }
    """
    
    # Integer Overflow Vulnerability
    BATCH_OVERFLOW_CONTRACT = """
    // SPDX-License-Identifier: MIT
    pragma solidity ^0.4.0;
    
    contract BatchOverflow {
        mapping(address => uint256) public balances;
        
        function batchTransfer(address[] _receivers, uint256 _value) public {
            // CRITICAL: Integer overflow vulnerability
            uint256 amount = _receivers.length * _value;
            require(balances[msg.sender] >= amount);
            
            balances[msg.sender] -= amount;
            for (uint i = 0; i < _receivers.length; i++) {
                balances[_receivers[i]] += _value;
            }
        }
        
        function deposit() public payable {
            balances[msg.sender] += msg.value;
        }
    }
    """
    
    # tx.origin Vulnerability
    TX_ORIGIN_CONTRACT = """
    // SPDX-License-Identifier: MIT
    pragma solidity ^0.8.0;
    
    contract TxOriginVulnerability {
        address public owner;
        
        constructor() {
            owner = msg.sender;
        }
        
        function withdraw() public {
            // MEDIUM: tx.origin vulnerability
            require(tx.origin == owner, "Not owner");
            payable(owner).transfer(address(this).balance);
        }
        
        receive() external payable {}
    }
    """
    
    # Unchecked Call Vulnerability
    UNCHECKED_CALL_CONTRACT = """
    // SPDX-License-Identifier: MIT
    pragma solidity ^0.8.0;
    
    contract UncheckedCall {
        mapping(address => uint256) public balances;
        
        function withdraw() public {
            uint256 amount = balances[msg.sender];
            require(amount > 0);
            balances[msg.sender] = 0;
            
            // MEDIUM: Unchecked call return value
            msg.sender.call{value: amount}("");
        }
        
        function deposit() public payable {
            balances[msg.sender] += msg.value;
        }
    }
    """
    
    # Safe Contract (No Vulnerabilities)
    SAFE_CONTRACT = """
    // SPDX-License-Identifier: MIT
    pragma solidity ^0.8.0;
    
    import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
    import "@openzeppelin/contracts/security/Pausable.sol";
    import "@openzeppelin/contracts/access/Ownable.sol";
    
    contract SafeContract is ReentrancyGuard, Pausable, Ownable {
        mapping(address => uint256) public balances;
        
        function withdraw() public nonReentrant whenNotPaused {
            uint256 amount = balances[msg.sender];
            require(amount > 0, "No balance");
            balances[msg.sender] = 0;
            
            (bool success, ) = msg.sender.call{value: amount}("");
            require(success, "Transfer failed");
        }
        
        function deposit() public payable {
            balances[msg.sender] += msg.value;
        }
        
        function pause() public onlyOwner {
            _pause();
        }
    }
    """
    
    @pytest.mark.asyncio
    async def test_dao_hack_reentrancy_detection(self):
        """Test detection of DAO hack reentrancy vulnerability"""
        result = await self.auditor.audit(self.DAO_HACK_CONTRACT)
        
        assert result["status"] == "success"
        assert result["severity"] in ["critical", "high"]
        
        # Check for reentrancy detection
        findings = result.get("findings", [])
        reentrancy_found = any(
            "reentrancy" in finding.get("description", "").lower() or
            "reentrancy" in finding.get("type", "").lower()
            for finding in findings
        )
        
        assert reentrancy_found, "Reentrancy vulnerability not detected"
        print(f"✅ DAO Hack Reentrancy: {result['severity']} severity detected")
    
    @pytest.mark.asyncio
    async def test_batch_overflow_detection(self):
        """Test detection of integer overflow vulnerability"""
        result = await self.auditor.audit(self.BATCH_OVERFLOW_CONTRACT)
        
        assert result["status"] == "success"
        assert result["severity"] in ["critical", "high", "medium"]
        
        # Check for overflow detection
        findings = result.get("findings", [])
        overflow_found = any(
            "overflow" in finding.get("description", "").lower() or
            "overflow" in finding.get("type", "").lower() or
            "integer" in finding.get("description", "").lower()
            for finding in findings
        )
        
        assert overflow_found, "Integer overflow vulnerability not detected"
        print(f"✅ Batch Overflow: {result['severity']} severity detected")
    
    @pytest.mark.asyncio
    async def test_tx_origin_detection(self):
        """Test detection of tx.origin vulnerability"""
        result = await self.auditor.audit(self.TX_ORIGIN_CONTRACT)
        
        assert result["status"] == "success"
        assert result["severity"] in ["medium", "high", "low"]
        
        # Check for tx.origin detection
        findings = result.get("findings", [])
        tx_origin_found = any(
            "tx.origin" in finding.get("description", "").lower() or
            "tx.origin" in finding.get("type", "").lower()
            for finding in findings
        )
        
        assert tx_origin_found, "tx.origin vulnerability not detected"
        print(f"✅ tx.origin: {result['severity']} severity detected")
    
    @pytest.mark.asyncio
    async def test_unchecked_call_detection(self):
        """Test detection of unchecked call vulnerability"""
        result = await self.auditor.audit(self.UNCHECKED_CALL_CONTRACT)
        
        assert result["status"] == "success"
        assert result["severity"] in ["medium", "high", "low"]
        
        # Check for unchecked call detection
        findings = result.get("findings", [])
        unchecked_found = any(
            "unchecked" in finding.get("description", "").lower() or
            "unchecked" in finding.get("type", "").lower() or
            "call" in finding.get("description", "").lower()
            for finding in findings
        )
        
        assert unchecked_found, "Unchecked call vulnerability not detected"
        print(f"✅ Unchecked Call: {result['severity']} severity detected")
    
    @pytest.mark.asyncio
    async def test_safe_contract_no_false_positives(self):
        """Test that safe contract doesn't generate false positives"""
        result = await self.auditor.audit(self.SAFE_CONTRACT)
        
        assert result["status"] == "success"
        
        # Safe contract should have low severity
        assert result["severity"] in ["low", "info", "none"]
        
        findings = result.get("findings", [])
        critical_high_findings = [
            f for f in findings 
            if f.get("severity") in ["critical", "high"]
        ]
        
        # Should have minimal critical/high findings
        assert len(critical_high_findings) <= 2, f"Too many false positives: {len(critical_high_findings)}"
        print(f"✅ Safe Contract: {result['severity']} severity, {len(critical_high_findings)} critical/high findings")
    
    @pytest.mark.asyncio
    async def test_accuracy_benchmark(self):
        """Run comprehensive accuracy benchmark"""
        test_cases = [
            {
                "name": "DAO Hack Reentrancy",
                "contract": self.DAO_HACK_CONTRACT,
                "expected_findings": ["reentrancy"],
                "expected_severity": ["critical", "high"]
            },
            {
                "name": "Batch Overflow",
                "contract": self.BATCH_OVERFLOW_CONTRACT,
                "expected_findings": ["overflow", "integer"],
                "expected_severity": ["critical", "high", "medium"]
            },
            {
                "name": "tx.origin Vulnerability",
                "contract": self.TX_ORIGIN_CONTRACT,
                "expected_findings": ["tx.origin"],
                "expected_severity": ["medium", "high", "low"]
            },
            {
                "name": "Unchecked Call",
                "contract": self.UNCHECKED_CALL_CONTRACT,
                "expected_findings": ["unchecked", "call"],
                "expected_severity": ["medium", "high", "low"]
            },
            {
                "name": "Safe Contract",
                "contract": self.SAFE_CONTRACT,
                "expected_findings": [],
                "expected_severity": ["low", "info", "none"]
            }
        ]
        
        accuracy_scores = []
        results = []
        
        for test_case in test_cases:
            result = await self.auditor.audit(test_case["contract"])
            findings = result.get("findings", [])
            
            # Check if expected findings were detected
            found_expected = False
            if test_case["expected_findings"]:
                for expected in test_case["expected_findings"]:
                    if any(expected in finding.get("description", "").lower() or 
                          expected in finding.get("type", "").lower()
                          for finding in findings):
                        found_expected = True
                        break
            else:
                # For safe contract, check for low severity
                found_expected = result["severity"] in test_case["expected_severity"]
            
            # Check severity matches expectation
            severity_match = result["severity"] in test_case["expected_severity"]
            
            accuracy_score = 1 if (found_expected and severity_match) else 0
            accuracy_scores.append(accuracy_score)
            
            results.append({
                "test": test_case["name"],
                "found_expected": found_expected,
                "severity_match": severity_match,
                "severity": result["severity"],
                "confidence": result.get("consensus_score", 0),
                "accuracy": accuracy_score
            })
        
        # Calculate overall accuracy
        average_accuracy = sum(accuracy_scores) / len(accuracy_scores)
        
        print(f"\n📊 AUDIT ACCURACY BENCHMARK RESULTS")
        print(f"Overall Accuracy: {average_accuracy * 100:.1f}%")
        print(f"Target: 80-95% (Professional grade)")
        
        for result in results:
            status = "✅ PASS" if result["accuracy"] else "❌ FAIL"
            print(f"{status} {result['test']}: {result['severity']} severity, {result['confidence']:.0%} confidence")
        
        # Assert minimum accuracy threshold
        assert average_accuracy >= 0.8, f"Accuracy {average_accuracy * 100:.1f}% below 80% threshold"
        
        return {
            "overall_accuracy": average_accuracy,
            "results": results,
            "status": "PASS" if average_accuracy >= 0.8 else "FAIL"
        }


def run_accuracy_test():
    """Run the accuracy test manually"""
    async def main():
        test = TestAuditAccuracy()
        test.setup_method()
        
        print("🧪 Running Audit Accuracy Benchmark...")
        result = await test.test_accuracy_benchmark()
        
        if result["overall_accuracy"] >= 0.8:
            print(f"\n✅ BENCHMARK PASSED: {result['overall_accuracy'] * 100:.1f}% accuracy")
        else:
            print(f"\n❌ BENCHMARK FAILED: {result['overall_accuracy'] * 100:.1f}% accuracy")
        
        return result
    
    return asyncio.run(main())


if __name__ == "__main__":
    run_accuracy_test()
