# 🔗 HYPERKIT-AGENT WORKFLOW STAGES: END-TO-END INTEGRATION

## **THE WORKFLOW PIPELINE**

When you run:
```bash
hyperagent workflow "Create a play-to-earn gaming token..."
```

This is what ACTUALLY happens (all 5 stages that MUST work together):

```
Stage 1: GENERATION
   ↓ (AI creates contract code)
Stage 2: AUDIT
   ↓ (Security analysis)
Stage 3: DEPLOYMENT
   ↓ (Deploy to blockchain)
Stage 4: VERIFICATION
   ↓ (Verify on explorer)
Stage 5: TESTING
   ↓ (Interact with contract)
RESULT: Complete report
```

---

## 📁 **FILE-BY-FILE INTEGRATION MAP**

### **STAGE 1: GENERATION**

**Files Involved**:
```
main.py (cli command)
  ↓
core/agent/main.py (HyperKitAgent class)
  ↓
core/llm/router.py (LLM selection - Gemini, GPT, Claude)
  ↓
services/generation/generator.py (Contract generation logic)
  ↓
core/config/loader.py (Get API keys)
```

**Flow**:
```python
# main.py
@cli.command()
def workflow(prompt: str):
    agent = HyperKitAgent(config)
    
    # CALLS: core/agent/main.py
    result = agent.generate_contract(prompt)
    # This calls: core/llm/router.py
    # Which calls: services/generation/generator.py
```

**What gets saved**:
```
./contracts/GeneratedContract.sol ← The generated code
./artifacts/generation_log.json ← Generation metadata
```

**Files that MUST exist**:
- ✅ `core/llm/router.py` - LLM provider logic
- ✅ `services/generation/generator.py` - Generation logic
- ✅ `core/config/loader.py` - API key loading
- ✅ `main.py` - CLI entry point

---

### **STAGE 2: AUDIT**

**Files Involved**:
```
Stage 1 output (GeneratedContract.sol)
  ↓
services/audit/auditor.py (Main audit logic)
  ↓
services/audit/slither_scanner.py (Slither integration)
  ↓
services/audit/custom_rules.py (Custom vulnerability checks)
  ↓
core/agent/main.py (Orchestration)
```

**Flow**:
```python
# core/agent/main.py - audit_contract method
def audit_contract(self, source_code: str):
    auditor = SmartContractAuditor()
    
    # CALLS: services/audit/auditor.py
    result = auditor.audit(source_code)
    # Which calls:
    # - services/audit/slither_scanner.py
    # - services/audit/custom_rules.py
```

**What gets saved**:
```
./artifacts/audit_report.json ← Security findings
{
  "findings": [
    {
      "severity": "medium",
      "description": "Potential integer overflow",
      "file": "GeneratedContract.sol"
    }
  ]
}
```

**Files that MUST exist**:
- ✅ `services/audit/auditor.py` - Audit coordinator
- ✅ `services/audit/slither_scanner.py` - Slither runner
- ✅ `services/audit/custom_rules.py` - Custom checks

---

### **STAGE 3: DEPLOYMENT**

**Files Involved**:
```
Stage 2 output (Audit report)
  ↓
core/agent/main.py (deploy_contract method)
  ↓
services/deploy/deployer.py (FoundryDeployer class)
  ↓
core/config/loader.py (Get RPC URL, private key)
  ↓
services/deploy/foundry_manager.py (Foundry binary management)
```

**Flow**:
```python
# core/agent/main.py - deploy_contract method
def deploy_contract(self, source_code: str, network: str):
    # Extract RPC URL from config
    rpc_url = self.config['networks'][network]['rpc_url']
    
    # CALLS: services/deploy/deployer.py
    deployer = FoundryDeployer()
    result = deployer.deploy(source_code, rpc_url, chain_id)
    
    # Returns:
    # {
    #   "success": True,
    #   "contract_address": "0x...",
    #   "tx_hash": "0x..."
    # }
```

**What gets saved**:
```
./artifacts/deployment_info.json
{
  "contract_address": "0x3dB0BCc4c21BcA2d1785334B413Db3356C9207C2",
  "tx_hash": "0xdeadbeef...",
  "network": "hyperion",
  "deployed_at": "2025-10-24T12:00:00Z"
}
```

**Files that MUST exist**:
- ✅ `services/deploy/deployer.py` - FoundryDeployer (from [194])
- ✅ `services/deploy/foundry_manager.py` - Foundry management
- ✅ `core/config/loader.py` - Config with RPC URLs

---

### **STAGE 4: VERIFICATION**

**Files Involved**:
```
Stage 3 output (Contract address)
  ↓
core/agent/main.py (if --auto-verification flag)
  ↓
services/verification/verifier.py (Main verification logic)
  ↓
services/verification/explorer_api.py (Explorer API integration)
  ↓
services/verification/ipfs_storage.py (Fallback IPFS storage)
```

**Flow**:
```python
# core/agent/main.py - within workflow command
if auto_verification and contract_address:
    # CALLS: services/verification/verifier.py
    result = verify_contract(source_code, contract_address, network)
    
    # For testnet (no explorer): stores on IPFS
    # For mainnet (has explorer): submits to Etherscan API
```

**What gets saved**:
```
./artifacts/verification_result.json
{
  "status": "submitted",  # or "verified" or "stored_on_ipfs"
  "address": "0x...",
  "explorer_url": "https://etherscan.io/address/0x...",
  "ipfs_hash": "QmXxxx..." # if no explorer
}
```

**Files that MUST exist**:
- ✅ `services/verification/verifier.py` - Main verifier (from [193])
- ✅ `services/verification/explorer_api.py` - Explorer integration
- ✅ `services/verification/ipfs_storage.py` - IPFS fallback

---

### **STAGE 5: TESTING**

**Files Involved**:
```
Stage 3 output (Contract address)
  ↓
core/agent/main.py (if testing enabled)
  ↓
services/testing/contract_tester.py (Test execution)
  ↓
services/testing/web3_interaction.py (Web3.py interactions)
  ↓
core/config/loader.py (RPC connection)
```

**Flow**:
```python
# core/agent/main.py - within workflow command
if not test_only:
    # CALLS: services/testing/contract_tester.py
    tester = ContractTester(rpc_url, contract_address)
    results = tester.run_tests()
    
    # Returns:
    # {
    #   "tests_passed": 2,
    #   "tests_failed": 0,
    #   "details": [...]
    # }
```

**What gets saved**:
```
./artifacts/test_results.json
{
  "contract_parsing": "✅ 4 functions detected",
  "syntax_validation": "✅ Valid Solidity",
  "tests_passed": 2,
  "tests_failed": 0,
  "interactions": [
    {
      "function": "balanceOf",
      "result": "1000000000000000000"
    }
  ]
}
```

**Files that MUST exist**:
- ✅ `services/testing/contract_tester.py` - Test runner
- ✅ `services/testing/web3_interaction.py` - Web3 interactions

---

## 🔄 **COMPLETE FILE DEPENDENCY CHAIN**

```
main.py (entry point)
├── core/agent/main.py (HyperKitAgent)
│   ├── core/llm/router.py (LLM providers)
│   │   ├── core/llm/providers/gemini.py
│   │   ├── core/llm/providers/openai.py
│   │   └── core/llm/providers/claude.py
│   ├── services/generation/generator.py
│   ├── services/audit/auditor.py
│   │   ├── services/audit/slither_scanner.py
│   │   └── services/audit/custom_rules.py
│   ├── services/deploy/deployer.py
│   │   └── services/deploy/foundry_manager.py
│   ├── services/verification/verifier.py
│   │   ├── services/verification/explorer_api.py
│   │   └── services/verification/ipfs_storage.py
│   └── services/testing/contract_tester.py
│       └── services/testing/web3_interaction.py
└── core/config/loader.py (Configuration)
```

---

## ✅ **INTEGRATION CHECKLIST: ALL FILES WORKING TOGETHER**

### **For GENERATION to work**:
```
✅ main.py has @cli.command("workflow")
✅ core/agent/main.py has generate_contract() method
✅ core/llm/router.py has LLM provider routing
✅ services/generation/generator.py has generation logic
✅ core/config/loader.py loads API keys
→ Result: Solidity file in ./contracts/
```

### **For AUDIT to work**:
```
✅ services/audit/auditor.py exists
✅ services/audit/slither_scanner.py runs slither
✅ services/audit/custom_rules.py has vulnerability patterns
✅ core/agent/main.py calls audit_contract()
→ Result: JSON report in ./artifacts/
```

### **For DEPLOYMENT to work**:
```
✅ services/deploy/deployer.py (FoundryDeployer class)
✅ services/deploy/foundry_manager.py (Foundry binary)
✅ core/config/loader.py has network RPC URLs
✅ core/agent/main.py extracts rpc_url as STRING (not dict!)
✅ core/agent/main.py calls deployer.deploy(code, rpc_url, chain_id)
→ Result: Contract address in ./artifacts/
```

### **For VERIFICATION to work**:
```
✅ services/verification/verifier.py exists
✅ services/verification/explorer_api.py has API logic
✅ services/verification/ipfs_storage.py has fallback
✅ core/agent/main.py passes --auto-verification flag
✅ Network detection (testnet vs mainnet)
→ Result: Verification status in ./artifacts/
```

### **For TESTING to work**:
```
✅ services/testing/contract_tester.py exists
✅ services/testing/web3_interaction.py has Web3 calls
✅ core/agent/main.py passes contract address
✅ RPC URL available for testnet/mainnet
→ Result: Test results in ./artifacts/
```

---

## 🔴 **COMMON INTEGRATION FAILURES**

### **Failure #1: Generation → Audit (BROKEN)**
```
Error: contract_tester.py not found
Reason: services/generation/generator.py exists
        but services/audit/auditor.py missing

Fix: Create services/audit/auditor.py
```

### **Failure #2: Audit → Deployment (BROKEN)**
```
Error: RPC URL is dict, not string
Reason: core/agent/main.py does:
        deployer.deploy(code, self.config['networks'][network])
        Instead of:
        deployer.deploy(code, rpc_url_string, chain_id)

Fix: Apply [194] (Foundry integration)
```

### **Failure #3: Deployment → Verification (BROKEN)**
```
Error: explorer_api.py not found
Reason: services/verification/ directory missing

Fix: Create services/verification/ with:
     - verifier.py
     - explorer_api.py
     - ipfs_storage.py
```

### **Failure #4: Verification → Testing (BROKEN)**
```
Error: contract_tester.py not found
Reason: services/testing/ directory missing

Fix: Create services/testing/ with:
     - contract_tester.py
     - web3_interaction.py
```

---

## 📋 **EXACT FILES YOU NEED**

### **Core Infrastructure** (Already exist)
- ✅ `main.py` - CLI entry
- ✅ `core/agent/main.py` - Orchestrator
- ✅ `core/config/loader.py` - Configuration
- ✅ `core/llm/router.py` - LLM routing

### **Critical: MUST CREATE**
- 🔴 `services/deploy/deployer.py` - FoundryDeployer (from [194])
- 🔴 `services/deploy/foundry_manager.py` - Foundry mgmt
- 🔴 `services/verification/verifier.py` - Verify logic (from [193])
- 🔴 `services/verification/explorer_api.py` - Explorer API
- 🔴 `services/verification/ipfs_storage.py` - IPFS backup

### **Already Exist: VERIFY THEY WORK**
- ⚠️ `services/generation/generator.py` - Verify AI integration
- ⚠️ `services/audit/auditor.py` - Verify Slither integration
- ⚠️ `services/testing/contract_tester.py` - Verify Web3 calls

---

## 🎯 **VERIFICATION TEST**

Run this to verify ALL stages work together:

```bash
# Stage 1: Generation
hyperagent generate "Create a simple ERC20 token" 
# ✅ Check: ./contracts/GeneratedContract.sol exists

# Stage 2: Audit
hyperagent audit contracts/GeneratedContract.sol
# ✅ Check: ./artifacts/audit_report.json exists

# Stage 3-5: Full workflow
hyperagent workflow "Create a simple ERC20 token" \
  --network hyperion \
  --auto-audit \
  --auto-deploy \
  --auto-verification \
  --output-dir ./test_workflow

# ✅ Check: All 5 output files exist
ls -la test_workflow/
# Should show:
# - GeneratedContract.sol
# - audit_report.json
# - deployment_info.json
# - verification_result.json
# - test_results.json
# - workflow_report.json
```

---

## 🚀 **IMPLEMENTATION ORDER** (What to fix first)

### **Week 1: Fix Deployment (CRITICAL)**
- Apply [194]: Foundry integration
- Create `services/deploy/deployer.py`
- Create `services/deploy/foundry_manager.py`
- Test Stage 1-3

### **Week 2: Add Verification (HIGH)**
- Create `services/verification/verifier.py`
- Create `services/verification/explorer_api.py`
- Create `services/verification/ipfs_storage.py`
- Test Stage 1-4

### **Week 3: Add Testing (HIGH)**
- Verify `services/testing/contract_tester.py` works
- Verify Web3 interactions
- Test Stage 1-5 (FULL WORKFLOW)

### **Week 4: Integration Testing**
- Run all 7 real prompts from [263]
- Verify each stage outputs correct files
- Fix any breaking points

---

## ✅ **SUCCESS CRITERIA**

When ALL files work together:

```bash
hyperagent workflow "Create a simple ERC20 token" --network hyperion

# Should output:
✅ Stage 1/5: Generating Contract
✅ Stage 2/5: Auditing Contract  
✅ Stage 3/5: Deploying to Blockchain
✅ Stage 4/5: Verifying Contract
✅ Stage 5/5: Testing Contract Functionality

# And create:
✅ contracts/GeneratedContract.sol
✅ artifacts/audit_report.json
✅ artifacts/deployment_info.json
✅ artifacts/verification_result.json
✅ artifacts/test_results.json
✅ artifacts/workflow_report.json
```

---

**This document ensures ALL 5 stages work together seamlessly.**

**File [264] is your integration blueprint.**

**Everything must work end-to-end. No broken links.**

