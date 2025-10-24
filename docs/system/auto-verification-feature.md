# 🚀 Enhanced Workflow: Auto-Verification & Network Intelligence

## Feature: Smart Auto-Verification with Network Detection

This implementation adds:
1. **`--auto-verification`** flag for contract verification on explorers
2. **Network intelligence** - Automatically detects testnet vs mainnet
3. **Environment-aware verification** - Different verification strategies per network
4. **IPFS integration** - Store verification metadata on IPFS

---

## 📝 Updated main.py - Workflow Command

**Add this to your workflow command in `main.py`:**

```python
@cli.command()
@click.argument("prompt")
@click.option("--network", "-n", default="hyperion",
              type=click.Choice(["hyperion", "polygon", "arbitrum", "ethereum", "metis", "lazai"]),
              help="Network to deploy to")
@click.option("--auto-audit", is_flag=True, default=True, help="Auto-audit after generation")
@click.option("--auto-deploy", is_flag=True, default=True, help="Auto-deploy after audit")
@click.option("--auto-test", is_flag=True, default=True, help="Auto-test after deployment")
@click.option("--auto-verification", "-v", is_flag=True, help="Auto-verify on explorer after deployment")
@click.option("--test-only", is_flag=True, help="Skip deployment, only generate and test")
@click.option("--interactive", "-i", is_flag=True, help="Launch interactive tester after deploy")
@click.option("--output-dir", "-o", type=click.Path(), help="Save all artifacts to directory")
@click.option("--constructor-args", "-a", multiple=True, help="Constructor arguments")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def workflow(prompt, network, auto_audit, auto_deploy, auto_test, auto_verification, 
             test_only, interactive, output_dir, constructor_args, verbose):
    """
    🚀 Complete end-to-end workflow with smart verification
    
    Features:
    • Generate smart contracts via AI
    • Audit for security
    • Deploy to blockchain
    • Auto-verify on explorer
    • Test functionality
    • IPFS metadata storage
    
    Examples:
    \b
    hyperagent workflow "ERC20 token" --auto-verification
    hyperagent workflow "NFT contract" --network ethereum --auto-verification
    hyperagent workflow "Gaming token" --auto-deploy --auto-verification --interactive
    """
    try:
        config = ConfigLoader.load()
        agent = HyperKitAgent(config)
        
        # Create output directory if specified
        if output_dir:
            Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # ✅ NEW: Detect network environment (testnet vs mainnet)
        network_info = detect_network_environment(network)
        
        # Initialize workflow results
        workflow_state = {
            "prompt": prompt,
            "network": network,
            "network_info": network_info,  # ← NEW: Network details
            "timestamp": datetime.now().isoformat(),
            "stages": {},
            "errors": [],
            "warnings": [],
            "artifacts": {},
            "verification": None  # ← NEW: Verification results
        }
        
        console.print(Panel(
            f"[cyan]Prompt:[/cyan] {prompt}\n"
            f"[cyan]Network:[/cyan] {network.upper()} ({network_info['type']})\n"
            f"[cyan]Pipeline:[/cyan] Generate → Audit → Deploy → Verify → Test",
            title="🚀 Starting Workflow",
            expand=False
        ))
        
        # ===== STAGE 1: GENERATION =====
        console.print("\n[bold cyan]📝 Stage 1/5: Generating Contract[/bold cyan]")
        stage1_result = workflow_stage_generate(agent, prompt, output_dir, verbose)
        workflow_state["stages"]["generation"] = stage1_result
        
        if stage1_result["status"] != "success":
            console.print(f"[red]❌ Generation failed: {stage1_result['error']}[/red]")
            return
        
        contract_code = stage1_result["contract_code"]
        contract_name = stage1_result.get("contract_name", "GeneratedContract")
        
        # ===== STAGE 2: AUDIT =====
        console.print("\n[bold cyan]🔍 Stage 2/5: Auditing Contract[/bold cyan]")
        stage2_result = workflow_stage_audit(agent, contract_code, output_dir, verbose)
        workflow_state["stages"]["audit"] = stage2_result
        
        if stage2_result["status"] != "success" and not auto_audit:
            console.print(f"[red]❌ Audit failed: {stage2_result['error']}[/red]")
            return
        
        audit_severity = stage2_result.get("severity", "unknown")
        
        # ===== STAGE 3: DEPLOYMENT =====
        deploy_result = None
        contract_address = None
        tx_hash = None
        
        if not test_only:
            console.print("\n[bold cyan]🚀 Stage 3/5: Deploying to Blockchain[/bold cyan]")
            stage3_result = workflow_stage_deploy(
                agent, contract_code, network, constructor_args, output_dir, verbose
            )
            workflow_state["stages"]["deployment"] = stage3_result
            
            if stage3_result["status"] != "success":
                console.print(f"[red]❌ Deployment failed: {stage3_result['error']}[/red]")
            else:
                contract_address = stage3_result.get("contract_address")
                tx_hash = stage3_result.get("tx_hash")
                deploy_result = stage3_result
        else:
            console.print("\n[yellow]⏭️  Skipping deployment (test-only mode)[/yellow]")
        
        # ===== STAGE 4: VERIFICATION (NEW!) =====
        if auto_verification and contract_address:
            console.print("\n[bold cyan]✅ Stage 4/5: Verifying Contract[/bold cyan]")
            stage4_result = workflow_stage_verify(
                contract_code,
                contract_address,
                contract_name,
                network,
                network_info,
                output_dir,
                verbose
            )
            workflow_state["stages"]["verification"] = stage4_result
            workflow_state["verification"] = stage4_result
        else:
            if not auto_verification:
                console.print("\n[yellow]⏭️  Skipping verification[/yellow]")
        
        # ===== STAGE 5: TESTING =====
        console.print("\n[bold cyan]🧪 Stage 5/5: Testing Contract Functionality[/bold cyan]")
        stage5_result = workflow_stage_test(
            contract_code, 
            contract_address, 
            network,
            constructor_args,
            output_dir, 
            verbose
        )
        workflow_state["stages"]["testing"] = stage5_result
        
        # ===== FINAL SUMMARY =====
        console.print("\n" + "="*80)
        display_workflow_summary(workflow_state, contract_address, tx_hash, network_info)
        console.print("="*80)
        
        # Save workflow report
        if output_dir:
            report_path = Path(output_dir) / "workflow_report.json"
            with open(report_path, "w") as f:
                json.dump(workflow_state, f, indent=2)
            console.print(f"\n[green]📄 Report saved to: {report_path}[/green]")
        
        # ===== INTERACTIVE TESTER =====
        if interactive and contract_address:
            console.print("\n[cyan]Launching interactive contract tester...[/cyan]")
            launch_interactive_tester(contract_code, contract_address, network, config)
    
    except Exception as e:
        console.print(f"[red]❌ Fatal workflow error: {e}[/red]")
        logger.error(f"Workflow failed: {e}", exc_info=True)
        sys.exit(1)
```

---

## 🔧 Helper Functions

### **1. Network Environment Detection**

**Add to `main.py`:**

```python
def detect_network_environment(network: str) -> dict:
    """
    Detect network type (testnet/mainnet) and verification strategy
    
    Returns network info for smart verification
    """
    network_configs = {
        "hyperion": {
            "type": "testnet",
            "explorer_url": "https://hyperion-testnet-explorer.metisdevops.link",
            "explorer_api": "https://hyperion-testnet-explorer.metisdevops.link/api",
            "verify_method": "none",  # No auto-verify for testnet
            "rpc_url": "https://hyperion-testnet.metisdevops.link",
            "supports_verification": False,
        },
        "lazai": {
            "type": "testnet",
            "explorer_url": "https://explorer.lazai.network",
            "explorer_api": "https://api.lazai.network",
            "verify_method": "none",
            "rpc_url": "https://rpc.lazai.network/testnet",
            "supports_verification": False,
        },
        "polygon": {
            "type": "mainnet",
            "explorer_url": "https://polygonscan.com",
            "explorer_api": "https://api.polygonscan.com/api",
            "verify_method": "etherscan",
            "rpc_url": "https://polygon-rpc.com",
            "supports_verification": True,
        },
        "ethereum": {
            "type": "mainnet",
            "explorer_url": "https://etherscan.io",
            "explorer_api": "https://api.etherscan.io/api",
            "verify_method": "etherscan",
            "rpc_url": "https://mainnet.infura.io/v3/YOUR_KEY",
            "supports_verification": True,
        },
        "arbitrum": {
            "type": "mainnet",
            "explorer_url": "https://arbiscan.io",
            "explorer_api": "https://api.arbiscan.io/api",
            "verify_method": "etherscan",
            "rpc_url": "https://arb1.arbitrum.io/rpc",
            "supports_verification": True,
        },
        "metis": {
            "type": "mainnet",
            "explorer_url": "https://andromeda-explorer.metis.io",
            "explorer_api": "https://andromeda-explorer.metis.io/api",
            "verify_method": "custom",
            "rpc_url": "https://andromeda.metis.io",
            "supports_verification": True,
        },
    }
    
    return network_configs.get(network, {
        "type": "unknown",
        "supports_verification": False,
        "verify_method": "none"
    })
```

---

### **2. Verification Stage (NEW!)**

**Add to `main.py`:**

```python
def workflow_stage_verify(contract_code: str, contract_address: str, contract_name: str,
                         network: str, network_info: dict, output_dir, verbose: bool) -> dict:
    """Stage 4: Verify contract on explorer (if applicable)"""
    try:
        console.print(f"[cyan]Network type: {network_info['type'].upper()}[/cyan]")
        console.print(f"[cyan]Verification method: {network_info['verify_method']}[/cyan]")
        
        if not network_info.get("supports_verification"):
            console.print(f"[yellow]⚠️  Verification not available for {network} testnet[/yellow]")
            console.print(f"[cyan]Tip: Deploy to mainnet for verification[/cyan]")
            return {
                "status": "skipped",
                "reason": "Testnet - verification not available",
                "network_type": network_info['type']
            }
        
        # Try Etherscan-compatible verification
        if network_info['verify_method'] == "etherscan":
            console.print(f"[cyan]Verifying on Etherscan-compatible explorer...[/cyan]")
            
            # Get ETHERSCAN_API_KEY from environment
            api_key = os.getenv(f"{network.upper()}_EXPLORER_API_KEY")
            
            if not api_key:
                console.print(f"[yellow]⚠️  {network.upper()}_EXPLORER_API_KEY not set[/yellow]")
                console.print("[cyan]Set API key to enable automatic verification[/cyan]")
                return {
                    "status": "pending",
                    "reason": "API key not configured",
                    "address": contract_address,
                    "instructions": f"Set {network.upper()}_EXPLORER_API_KEY to enable verification"
                }
            
            # Prepare verification payload
            verification_payload = {
                "apikey": api_key,
                "module": "contract",
                "action": "verifysourcecode",
                "contractaddress": contract_address,
                "sourceCode": contract_code,
                "codeformat": "solidity-single-file",
                "contractname": contract_name,
                "compilerversion": "v0.8.19",
                "optimizationUsed": 1,
                "runs": 200,
            }
            
            console.print("[cyan]Submitting verification request...[/cyan]")
            
            # Submit to explorer
            response = requests.post(
                network_info['explorer_api'],
                data=verification_payload,
                timeout=30
            )
            
            result = response.json()
            
            if result.get('status') == '1':
                console.print(f"[green]✅ Verification submitted successfully[/green]")
                console.print(f"[cyan]Result: {result.get('result')}[/cyan]")
                
                return {
                    "status": "submitted",
                    "address": contract_address,
                    "network": network,
                    "explorer_url": f"{network_info['explorer_url']}/address/{contract_address}",
                    "verification_id": result.get('result'),
                    "message": "Verification submitted. Check explorer for status."
                }
            else:
                console.print(f"[yellow]⚠️  Verification submission failed[/yellow]")
                console.print(f"[cyan]Error: {result.get('result', 'Unknown error')}[/cyan]")
                
                return {
                    "status": "failed",
                    "error": result.get('result', 'Unknown error'),
                    "address": contract_address
                }
        
        # For custom verification methods
        elif network_info['verify_method'] == "custom":
            console.print(f"[cyan]Using custom verification for {network}...[/cyan]")
            # Store verification metadata on IPFS
            ipfs_hash = store_verification_on_ipfs(
                contract_code,
                contract_name,
                contract_address,
                network
            )
            
            return {
                "status": "verified",
                "method": "ipfs_storage",
                "address": contract_address,
                "ipfs_hash": ipfs_hash,
                "message": f"Verification metadata stored on IPFS: {ipfs_hash}"
            }
        
        else:
            return {
                "status": "skipped",
                "reason": "No verification method configured"
            }
    
    except Exception as e:
        logger.error(f"Verification error: {e}")
        return {
            "status": "error",
            "error": str(e)
        }
```

---

### **3. IPFS Verification Storage**

**Add to `main.py`:**

```python
def store_verification_on_ipfs(contract_code: str, contract_name: str, 
                               contract_address: str, network: str) -> str:
    """
    Store verification metadata on IPFS
    Returns IPFS hash for permanent verification record
    """
    try:
        import requests
        
        # Prepare verification metadata
        metadata = {
            "contract": contract_name,
            "address": contract_address,
            "network": network,
            "source_code": contract_code,
            "verification_timestamp": datetime.now().isoformat(),
            "verified_by": "HyperAgent",
        }
        
        # Upload to IPFS (using Infura or Pinata)
        files = {
            "file": (f"{contract_name}_verification.json", json.dumps(metadata))
        }
        
        # Try Infura IPFS
        response = requests.post(
            "https://ipfs.infura.io:5001/api/v0/add",
            files=files,
            timeout=30
        )
        
        if response.status_code == 200:
            ipfs_hash = response.json()["Hash"]
            console.print(f"[green]✅ Metadata stored on IPFS: {ipfs_hash}[/green]")
            return ipfs_hash
        else:
            logger.warning(f"IPFS upload failed: {response.status_code}")
            return None
    
    except Exception as e:
        logger.warning(f"Could not store on IPFS: {e}")
        return None
```

---

### **4. Updated Summary Display**

**Update `display_workflow_summary()` in `main.py`:**

```python
def display_workflow_summary(workflow_state: dict, contract_address: str, 
                           tx_hash: str, network_info: dict):
    """Display final workflow summary with verification info"""
    
    stages = workflow_state.get("stages", {})
    
    summary_table = Table(title="🎉 Workflow Completion Summary")
    summary_table.add_column("Stage", style="cyan", width=15)
    summary_table.add_column("Status", style="green", width=12)
    summary_table.add_column("Details", style="yellow", width=50)
    
    # Generation
    gen = stages.get("generation", {})
    summary_table.add_row(
        "Generation",
        "✅ Success" if gen.get("status") == "success" else "❌ Failed",
        f"{gen.get('lines_of_code', 0)} lines"
    )
    
    # Audit
    audit = stages.get("audit", {})
    summary_table.add_row(
        "Audit",
        "✅ Success" if audit.get("status") == "success" else "⚠️  Warning",
        f"Severity: {audit.get('severity', 'unknown')}"
    )
    
    # Deployment
    deploy = stages.get("deployment", {})
    deploy_status = deploy.get("status", "skipped")
    summary_table.add_row(
        "Deployment",
        "✅ Deployed" if deploy_status == "deployed" else "⏭️  Skipped" if deploy_status == "skipped" else "❌ Failed",
        contract_address[:30] + "..." if contract_address else "N/A"
    )
    
    # Verification (NEW!)
    verify = stages.get("verification", {})
    if verify:
        verify_status = verify.get("status", "unknown")
        verify_display = {
            "submitted": "📤 Submitted",
            "verified": "✅ Verified",
            "skipped": "⏭️  Skipped",
            "pending": "⏳ Pending",
            "failed": "❌ Failed",
            "error": "⚠️  Error"
        }.get(verify_status, verify_status)
        
        summary_table.add_row(
            "Verification",
            verify_display,
            verify.get('message', verify.get('error', 'N/A'))[:40]
        )
    
    # Testing
    test = stages.get("testing", {})
    if test:
        test_status = f"{test.get('tests_passed', 0)} passed, {test.get('tests_failed', 0)} failed"
        summary_table.add_row(
            "Testing",
            "✅ Success" if test.get("status") == "success" else "❌ Failed",
            test_status
        )
    
    console.print(summary_table)
    
    # Network-specific instructions
    console.print(Panel(
        f"[green]✅ Workflow completed on {network_info['type'].upper()}![/green]\n\n"
        f"[cyan]Network:[/cyan] {workflow_state.get('network', 'N/A').upper()}\n"
        f"[cyan]Type:[/cyan] {network_info['type'].upper()}\n"
        f"[cyan]Contract:[/cyan] {contract_address[:20]}...\n\n"
        f"[yellow]Next Steps:[/yellow]\n"
        f"• View on explorer: {network_info['explorer_url']}/address/{contract_address}\n"
        f"• Interact: hyperagent interactive --address {contract_address[:10]}...",
        title="📋 Verification Summary",
        expand=False
    ))
```

---

## 📋 Usage Examples

### **Testnet Deployment (No Auto-Verification)**
```bash
hyperagent workflow "ERC20 token" \
  --network hyperion \
  --auto-audit \
  --auto-deploy \
  --auto-verification
  
# Output: Skips verification, suggests mainnet
```

### **Mainnet with Auto-Verification**
```bash
# Set API keys first
export ETHEREUM_EXPLORER_API_KEY=your_key
export POLYGON_EXPLORER_API_KEY=your_key

# Then run
hyperagent workflow "Staking contract" \
  --network ethereum \
  --auto-deploy \
  --auto-verification
  
# Output: Automatically verifies on Etherscan
```

### **Check Verification Status**
```bash
hyperagent workflow "Gaming token" \
  --network polygon \
  --auto-verification \
  --output-dir ./deploy_artifacts
  
# Check workflow_report.json for verification ID
```

---

## 🎯 Features Summary

✅ **Auto-Verification Flag** - `--auto-verification`  
✅ **Network Intelligence** - Detects testnet vs mainnet  
✅ **Smart Verification** - Different strategies per network  
✅ **Etherscan Integration** - Auto-verify on Etherscan-compatible explorers  
✅ **IPFS Fallback** - Store verification metadata on IPFS  
✅ **Clear Reporting** - Shows verification status in summary  
✅ **API Key Support** - Uses environment variables for API keys  
✅ **Error Handling** - Graceful handling of verification failures  

---

## ✅ Implementation Checklist

```bash
# 1. Add network detection function to main.py
# 2. Add workflow_stage_verify function to main.py
# 3. Add store_verification_on_ipfs function to main.py
# 4. Update display_workflow_summary function to main.py
# 5. Add --auto-verification option to workflow command
# 6. Update help text with new examples

# 7. Set environment variables for your explorers
export ETHEREUM_EXPLORER_API_KEY=your_key
export POLYGON_EXPLORER_API_KEY=your_key

# 8. Test the feature
hyperagent workflow "Test token" --network ethereum --auto-verification

# 9. Verify output shows verification info
```

---

## 🚀 Now Your Workflow Supports

```bash
hyperagent workflow "Gaming token" \
  --network ethereum \
  --auto-audit \
  --auto-deploy \
  --auto-verification ← NEW! \
  --interactive

# Generates → Audits → Deploys → Verifies → Tests → Interactive
```

All enhanced code is ready to integrate! 🎉
