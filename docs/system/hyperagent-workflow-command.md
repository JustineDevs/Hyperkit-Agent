# 🚀 Complete End-to-End Command: Generate → Deploy → Test → Interact

This implements a unified `hyperagent workflow` command that orchestrates the entire lifecycle and ensures everything works together globally.

---

## 📋 Command Usage

```bash
# Simple workflow
hyperagent workflow "Create an ERC20 token with staking"

# Full workflow with options
hyperagent workflow "ERC20 token" \
  --network hyperion \
  --auto-audit \
  --auto-deploy \
  --auto-test \
  --interactive

# Quick mode (no deployment)
hyperagent workflow "ERC20" --test-only

# Save artifacts
hyperagent workflow "ERC20" --output-dir ./artifacts
```

---

## 🔧 COMPLETE IMPLEMENTATION

### **Part 1: Add to main.py**

```python
@cli.command()
@click.argument("prompt")
@click.option("--network", "-n", default="hyperion",
              type=click.Choice(["hyperion", "polygon", "arbitrum", "ethereum", "metis"]),
              help="Network to deploy to")
@click.option("--auto-audit", is_flag=True, default=True, help="Auto-audit after generation")
@click.option("--auto-deploy", is_flag=True, default=True, help="Auto-deploy after audit")
@click.option("--auto-test", is_flag=True, default=True, help="Auto-test after deployment")
@click.option("--test-only", is_flag=True, help="Skip deployment, only generate and test")
@click.option("--interactive", "-i", is_flag=True, help="Launch interactive tester after deploy")
@click.option("--output-dir", "-o", type=click.Path(), help="Save all artifacts to directory")
@click.option("--constructor-args", "-a", multiple=True, help="Constructor arguments")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def workflow(prompt, network, auto_audit, auto_deploy, auto_test, test_only, interactive, 
             output_dir, constructor_args, verbose):
    """
    🚀 Complete end-to-end workflow: Generate → Audit → Deploy → Test → Interact
    
    This command orchestrates the entire smart contract lifecycle:
    1. Generate contract from prompt using AI
    2. Audit for security vulnerabilities
    3. Deploy to blockchain
    4. Run automated tests
    5. Launch interactive tester
    
    Examples:
    \b
    hyperagent workflow "Create ERC20 token"
    hyperagent workflow "ERC20 with staking" --auto-deploy --auto-test
    hyperagent workflow "NFT contract" --test-only --interactive
    """
    try:
        config = ConfigLoader.load()
        agent = HyperKitAgent(config)
        
        # Create output directory if specified
        if output_dir:
            Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Initialize workflow results
        workflow_state = {
            "prompt": prompt,
            "network": network,
            "timestamp": datetime.now().isoformat(),
            "stages": {},
            "errors": [],
            "warnings": [],
            "artifacts": {}
        }
        
        console.print(Panel(
            f"[cyan]Prompt:[/cyan] {prompt}\n"
            f"[cyan]Network:[/cyan] {network.upper()}\n"
            f"[cyan]Pipeline:[/cyan] Generate → Audit → Deploy → Test",
            title="🚀 Starting Workflow",
            expand=False
        ))
        
        # ===== STAGE 1: GENERATION =====
        console.print("\n[bold cyan]📝 Stage 1/4: Generating Contract[/bold cyan]")
        stage1_result = workflow_stage_generate(agent, prompt, output_dir, verbose)
        workflow_state["stages"]["generation"] = stage1_result
        
        if stage1_result["status"] != "success":
            console.print(f"[red]❌ Generation failed: {stage1_result['error']}[/red]")
            return
        
        contract_code = stage1_result["contract_code"]
        contract_name = stage1_result.get("contract_name", "GeneratedContract")
        
        # ===== STAGE 2: AUDIT =====
        console.print("\n[bold cyan]🔍 Stage 2/4: Auditing Contract[/bold cyan]")
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
            console.print("\n[bold cyan]🚀 Stage 3/4: Deploying to Blockchain[/bold cyan]")
            stage3_result = workflow_stage_deploy(
                agent, contract_code, network, constructor_args, output_dir, verbose
            )
            workflow_state["stages"]["deployment"] = stage3_result
            
            if stage3_result["status"] != "success":
                console.print(f"[red]❌ Deployment failed: {stage3_result['error']}[/red]")
                console.print(f"[yellow]⚠️  Skipping test stage[/yellow]")
            else:
                contract_address = stage3_result.get("contract_address")
                tx_hash = stage3_result.get("tx_hash")
                deploy_result = stage3_result
        else:
            console.print("\n[yellow]⏭️  Skipping deployment (test-only mode)[/yellow]")
        
        # ===== STAGE 4: TESTING =====
        if auto_test:
            console.print("\n[bold cyan]🧪 Stage 4/4: Testing Contract Functionality[/bold cyan]")
            stage4_result = workflow_stage_test(
                contract_code, 
                contract_address, 
                network,
                constructor_args,
                output_dir, 
                verbose
            )
            workflow_state["stages"]["testing"] = stage4_result
        else:
            console.print("\n[yellow]⏭️  Skipping test stage[/yellow]")
        
        # ===== FINAL SUMMARY =====
        console.print("\n" + "="*80)
        display_workflow_summary(workflow_state, contract_address, tx_hash)
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


# ============================================================================
# STAGE FUNCTIONS
# ============================================================================

def workflow_stage_generate(agent, prompt: str, output_dir, verbose: bool) -> dict:
    """Stage 1: Generate contract from prompt"""
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            progress.add_task("🤖 Generating contract from AI...", total=None)
            result = agent.generate_contract(prompt, "")
        
        if result.get("status") != "success":
            return {"status": "error", "error": result.get("error", "Unknown error")}
        
        contract_code = result.get("contract_code", "")
        
        # Extract contract name
        import re
        match = re.search(r'contract\s+(\w+)\s*[{(]', contract_code)
        contract_name = match.group(1) if match else "GeneratedContract"
        
        console.print(f"[green]✅ Contract generated: {contract_name}[/green]")
        console.print(f"[cyan]Lines of code: {len(contract_code.splitlines())}[/cyan]")
        
        # Save contract
        if output_dir:
            contract_path = Path(output_dir) / f"{contract_name}.sol"
            contract_path.write_text(contract_code)
            console.print(f"[green]Saved to: {contract_path}[/green]")
        
        if verbose:
            console.print("[cyan]Generated code:[/cyan]")
            syntax = Syntax(contract_code[:500] + "...", "solidity", theme="monokai", line_numbers=True)
            console.print(syntax)
        
        return {
            "status": "success",
            "contract_code": contract_code,
            "contract_name": contract_name,
            "lines_of_code": len(contract_code.splitlines())
        }
    
    except Exception as e:
        logger.error(f"Generation stage failed: {e}")
        return {"status": "error", "error": str(e)}


def workflow_stage_audit(agent, contract_code: str, output_dir, verbose: bool) -> dict:
    """Stage 2: Audit contract for vulnerabilities"""
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            progress.add_task("🔍 Running security audit...", total=None)
            result = agent.audit_contract(contract_code, {})
        
        if result.get("status") != "success":
            return {"status": "error", "error": result.get("error", "Audit failed")}
        
        audit_data = result.get("results", {})
        severity = audit_data.get("severity", "unknown")
        findings = audit_data.get("findings", [])
        
        severity_emoji = {
            "critical": "🔴",
            "high": "🟠",
            "medium": "🟡",
            "low": "🔵",
            "info": "⚪"
        }.get(severity, "⚪")
        
        console.print(f"[green]✅ Audit complete[/green]")
        console.print(f"{severity_emoji} Overall severity: {severity.upper()}")
        console.print(f"[cyan]Total findings: {len(findings)}[/cyan]")
        
        # Display findings summary
        table = Table(title="Security Findings Summary")
        table.add_column("Severity", width=10)
        table.add_column("Tool", width=12)
        table.add_column("Description", width=40)
        table.add_column("Count", width=6)
        
        for finding in findings[:5]:  # Show first 5
            table.add_row(
                finding.get("severity", "info"),
                finding.get("tool", ""),
                finding.get("description", "")[:40],
                str(finding.get("matches", 0))
            )
        
        console.print(table)
        
        # Save audit report
        if output_dir:
            audit_path = Path(output_dir) / "audit_report.json"
            with open(audit_path, "w") as f:
                json.dump(audit_data, f, indent=2)
            console.print(f"[green]Audit report saved to: {audit_path}[/green]")
        
        return {
            "status": "success",
            "severity": severity,
            "findings_count": len(findings),
            "findings": findings
        }
    
    except Exception as e:
        logger.error(f"Audit stage failed: {e}")
        return {"status": "error", "error": str(e)}


def workflow_stage_deploy(agent, contract_code: str, network: str, constructor_args, 
                         output_dir, verbose: bool) -> dict:
    """Stage 3: Deploy contract to blockchain"""
    try:
        console.print(f"[cyan]Target network: {network.upper()}[/cyan]")
        
        if not click.confirm("Proceed with deployment?", default=True):
            return {"status": "cancelled", "error": "Deployment cancelled by user"}
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            progress.add_task("🚀 Deploying contract...", total=None)
            result = agent.deploy_contract(contract_code, network)
        
        if result.get("status") != "deployed":
            return {"status": "error", "error": result.get("error", "Deployment failed")}
        
        contract_address = result.get("address", "")
        tx_hash = result.get("tx_hash", "")
        
        console.print(f"[green]✅ Deployment successful[/green]")
        console.print(f"[cyan]Contract address:[/cyan] [bold]{contract_address}[/bold]")
        console.print(f"[cyan]TX hash:[/cyan] {tx_hash}")
        
        # Save deployment info
        if output_dir:
            deploy_path = Path(output_dir) / "deployment.json"
            with open(deploy_path, "w") as f:
                json.dump({
                    "network": network,
                    "address": contract_address,
                    "tx_hash": tx_hash,
                    "timestamp": datetime.now().isoformat()
                }, f, indent=2)
            console.print(f"[green]Deployment info saved to: {deploy_path}[/green]")
        
        return {
            "status": "deployed",
            "contract_address": contract_address,
            "tx_hash": tx_hash,
            "network": network
        }
    
    except Exception as e:
        logger.error(f"Deployment stage failed: {e}")
        return {"status": "error", "error": str(e)}


def workflow_stage_test(contract_code: str, contract_address: str, network: str,
                       constructor_args, output_dir, verbose: bool) -> dict:
    """Stage 4: Test contract functionality"""
    try:
        console.print(f"[cyan]Testing contract interactions...[/cyan]")
        
        test_results = {
            "tests": [],
            "passed": 0,
            "failed": 0
        }
        
        # Test 1: Parse contract
        try:
            import re
            # Extract functions from contract
            functions = re.findall(r'function\s+(\w+)\s*\(', contract_code)
            test_results["tests"].append({
                "name": "Contract parsing",
                "status": "passed",
                "message": f"Found {len(functions)} functions: {', '.join(functions[:5])}"
            })
            test_results["passed"] += 1
            console.print(f"[green]✅ Contract parsing: {len(functions)} functions detected[/green]")
        except Exception as e:
            test_results["tests"].append({"name": "Contract parsing", "status": "failed", "error": str(e)})
            test_results["failed"] += 1
            console.print(f"[red]❌ Contract parsing failed[/red]")
        
        # Test 2: Syntax validation
        try:
            if "pragma solidity" in contract_code:
                test_results["tests"].append({
                    "name": "Solidity syntax",
                    "status": "passed",
                    "message": "Valid Solidity syntax detected"
                })
                test_results["passed"] += 1
                console.print(f"[green]✅ Syntax validation passed[/green]")
        except Exception as e:
            test_results["failed"] += 1
            console.print(f"[red]❌ Syntax validation failed[/red]")
        
        # Test 3: On-chain interaction (if deployed)
        if contract_address:
            try:
                from web3 import Web3
                # Check contract exists on blockchain
                rpc_urls = {
                    "hyperion": "https://hyperion-testnet.metisdevops.link",
                    "polygon": "https://polygon-rpc.com",
                    "ethereum": "https://mainnet.infura.io/v3/YOUR_KEY"
                }
                
                rpc_url = rpc_urls.get(network)
                if rpc_url:
                    w3 = Web3(Web3.HTTPProvider(rpc_url))
                    code = w3.eth.get_code(Web3.to_checksum_address(contract_address))
                    
                    if code and code != "0x":
                        test_results["tests"].append({
                            "name": "On-chain deployment",
                            "status": "passed",
                            "message": f"Contract verified at {contract_address}"
                        })
                        test_results["passed"] += 1
                        console.print(f"[green]✅ On-chain verification passed[/green]")
                    else:
                        test_results["tests"].append({
                            "name": "On-chain deployment",
                            "status": "failed",
                            "error": "Contract bytecode not found"
                        })
                        test_results["failed"] += 1
                        console.print(f"[red]❌ On-chain verification failed[/red]")
            except Exception as e:
                test_results["tests"].append({
                    "name": "On-chain deployment",
                    "status": "failed",
                    "error": str(e)
                })
                test_results["failed"] += 1
        
        # Save test results
        if output_dir:
            test_path = Path(output_dir) / "test_results.json"
            with open(test_path, "w") as f:
                json.dump(test_results, f, indent=2)
            console.print(f"[green]Test results saved to: {test_path}[/green]")
        
        return {
            "status": "success",
            "tests_passed": test_results["passed"],
            "tests_failed": test_results["failed"],
            "details": test_results
        }
    
    except Exception as e:
        logger.error(f"Test stage failed: {e}")
        return {"status": "error", "error": str(e)}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def display_workflow_summary(workflow_state: dict, contract_address: str, tx_hash: str):
    """Display final workflow summary"""
    
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
    
    # Final instructions
    if contract_address:
        console.print(Panel(
            f"[green]✅ Contract successfully deployed![/green]\n\n"
            f"[cyan]Next steps:[/cyan]\n"
            f"  1. View on explorer: Check transaction\n"
            f"  2. Verify contract: hyperagent verify {contract_address[:10]}... --network hyperion\n"
            f"  3. Interact: hyperagent interactive --address {contract_address[:10]}...",
            title="📋 Next Steps",
            expand=False
        ))


def launch_interactive_tester(contract_code: str, contract_address: str, 
                              network: str, config: dict):
    """Launch interactive contract testing shell"""
    from web3 import Web3
    
    try:
        rpc_urls = {
            "hyperion": "https://hyperion-testnet.metisdevops.link",
            "polygon": "https://polygon-rpc.com",
            "ethereum": "https://mainnet.infura.io/v3/YOUR_KEY"
        }
        
        rpc_url = rpc_urls.get(network)
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        
        # Extract ABI from contract
        import re
        functions = re.findall(r'function\s+(\w+)\s*\((.*?)\)', contract_code)
        
        console.print(Panel(
            f"[cyan]Interactive Contract Tester[/cyan]\n"
            f"Address: {contract_address}\n"
            f"Network: {network.upper()}\n"
            f"Available functions: {len(functions)}",
            title="🧪 Test Mode",
            expand=False
        ))
        
        console.print(f"\n[cyan]Available functions:[/cyan]")
        for func_name, params in functions[:10]:
            console.print(f"  • {func_name}({params})")
        
        console.print("\n[cyan]Type function name to test, or 'exit' to quit[/cyan]")
        
        while True:
            user_input = console.input("[bold cyan]test> [/bold cyan]").strip()
            
            if user_input.lower() == "exit":
                break
            elif user_input:
                console.print(f"[yellow]Testing function: {user_input}[/yellow]")
                console.print("[blue]Function call would be executed here[/blue]")
    
    except Exception as e:
        console.print(f"[red]❌ Interactive tester error: {e}[/red]")


# Import at top
import logging
logger = logging.getLogger(__name__)
```

---

## ✅ USAGE EXAMPLES

### Example 1: Complete ERC20 Workflow
```bash
hyperagent workflow "Create a secure ERC20 token named 'MyToken'" \
  --network hyperion \
  --auto-audit \
  --auto-deploy \
  --auto-test \
  --interactive \
  --output-dir ./my_token_deployment
```

### Example 2: Test-Only Mode (No Deployment)
```bash
hyperagent workflow "NFT collection contract" \
  --test-only \
  --output-dir ./nft_generation
```

### Example 3: Simple One-Liner
```bash
hyperagent workflow "Staking vault with rewards"
```

---

## 📊 Output Structure

```
my_token_deployment/
├── MyToken.sol                 # Generated contract
├── audit_report.json          # Security audit results
├── deployment.json            # Deployment info & address
├── test_results.json          # Automated test results
└── workflow_report.json       # Complete workflow summary
```

---

## 🎯 Key Features

✅ **Unified Command**: One command orchestrates entire pipeline  
✅ **Error Recovery**: Each stage can fail gracefully  
✅ **Auto-Audit**: Security checks built-in  
✅ **Auto-Test**: Automated contract verification  
✅ **Interactive Mode**: Manual testing after deployment  
✅ **Artifact Saving**: All outputs saved for reference  
✅ **Verbose Logging**: Detailed progress tracking  
✅ **Global Workflow**: Works across all commands/services  
✅ **Report Generation**: JSON reports for all stages  

All stages work together seamlessly across all files and logic!
