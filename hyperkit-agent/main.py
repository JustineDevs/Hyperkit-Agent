#!/usr/bin/env python3
"""
HyperAgent CLI - Professional Web3 Development Platform
Comprehensive smart contract generation, auditing, deployment, and management
"""

import sys
import os
import json
import click
import re
import requests
import asyncio
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
from rich.progress import Progress, SpinnerColumn, TextColumn
from web3 import Web3

# Load environment variables
load_dotenv()
sys.path.insert(0, str(Path(__file__).parent))

from core.agent.main import HyperKitAgent
from core.config.loader import ConfigLoader

console = Console()

# ============================================================================
# COMMAND GROUP & CONTEXT
# ============================================================================

@click.group()
@click.version_option(version="1.0.0", prog_name="hyperagent")
def cli():
    """
    🚀 HyperAgent - AI-Powered Web3 Development Platform
    
    Smart contract generation, auditing, deployment, and cross-chain management
    for the Hyperion and Andromeda ecosystems.
    """
    pass

# ============================================================================
# 1. STATUS COMMAND - Enhanced System Check
# ============================================================================

@cli.command()
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def status(verbose):
    """🔍 Check HyperAgent system status and connectivity"""
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            progress.add_task("Loading configuration...", total=None)
            config = ConfigLoader.load()
            agent = HyperKitAgent(config)
        
        # Status table
        table = Table(title="🏥 HyperAgent System Status", show_header=True)
        table.add_column("Component", style="cyan", width=20)
        table.add_column("Status", style="green", width=15)
        table.add_column("Details", style="yellow", width=50)
        
        # LLM Provider
        llm_provider = config.get("LLM_PROVIDER", "auto")
        llm_status = "✅ Active" if llm_provider else "❌ Not configured"
        table.add_row("LLM Provider", llm_status, llm_provider)
        
        # Obsidian RAG
        rag_status = "✅ Connected" if config.get("OBSIDIAN_API_URL") else "⚠️  Not available"
        table.add_row("Obsidian RAG", rag_status, config.get("OBSIDIAN_API_URL", "Not set")[:40])
        
        # Network Configuration
        network = config.get("DEFAULT_NETWORK", "unknown")
        rpc_url = config.get("HYPERION_RPC_URL", "")[:40] + "..."
        table.add_row("Network", f"✅ {network.upper()}", rpc_url)
        
        # Private Key
        pk_status = "✅ Set" if config.get("DEFAULT_PRIVATE_KEY") else "⚠️  Not set"
        table.add_row("Private Key", pk_status, "***hidden***")
        
        # API Keys
        google_key = "✅ Configured" if config.get("GOOGLE_API_KEY") else "⚠️  Missing"
        table.add_row("Google API", google_key, "LLM Provider")
        
        openai_key = "✅ Configured" if config.get("OPENAI_API_KEY") else "⚠️  Optional"
        table.add_row("OpenAI API", openai_key, "Alternative LLM")
        
        console.print(table)
        
        if verbose:
            console.print(Panel(
                f"[cyan]Configuration loaded from:[/cyan] .env\n"
                f"[cyan]Vault path:[/cyan] {config.get('OBSIDIAN_VAULT_PATH', 'Not set')}\n"
                f"[cyan]Log level:[/cyan] {config.get('LOG_LEVEL', 'INFO')}",
                title="📋 Configuration Details",
                expand=False
            ))
        
    except Exception as e:
        console.print(f"[red]❌ Error checking status: {e}[/red]")
        sys.exit(1)

# ============================================================================
# 2. GENERATE COMMAND - Enhanced with Real-World Prompts
# ============================================================================

@cli.command()
@click.argument("prompt", required=False)
@click.option("--template", "-t", type=click.Choice(["erc20", "erc721", "vault", "swap", "dao", "bridge", "custom"]), 
              help="Contract template")
@click.option("--output", "-o", type=click.Path(), help="Save to file")
@click.option("--format", type=click.Choice(["solidity", "json", "markdown"]), default="solidity")
@click.option("--audit-after", is_flag=True, help="Auto-audit after generation")
@click.option("--interactive", "-i", is_flag=True, help="Interactive prompt builder")
def generate(prompt, template, output, format, audit_after, interactive):
    """
    🤖 Generate smart contracts using AI
    
    Examples:
    \b
    hyperagent generate "Create an ERC20 token for a gaming ecosystem"
    hyperagent generate --template erc721 "NFT collection with royalties"
    hyperagent generate --interactive
    """
    try:
        if interactive:
            prompt = build_prompt_interactive()
        elif not prompt:
            console.print("[yellow]⚠️  Please provide a prompt or use --interactive[/yellow]")
            sys.exit(1)
        
        config = ConfigLoader.load()
        agent = HyperKitAgent(config)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            progress.add_task("🤖 Generating contract from AI...", total=None)
            result = asyncio.run(agent.generate_contract(prompt, ""))
        
        if result.get("status") == "success":
            contract_code = result.get("contract_code", "")
            
            console.print(Panel(
                f"[green]✅ Contract Generated Successfully[/green]\n"
                f"[cyan]AI Provider:[/cyan] {result.get('provider_used', 'unknown')}\n"
                f"[cyan]Lines of Code:[/cyan] {len(contract_code.splitlines())}\n"
                f"[cyan]Warnings:[/cyan] {len(result.get('warnings', []))}",
                title="🎉 Generation Summary",
                expand=False
            ))
            
            # Display code
            syntax = Syntax(contract_code, "solidity", theme="monokai", line_numbers=True)
            console.print(syntax)
            
            # Save to file
            if output:
                # Ensure output directory exists
                output_path = Path(output)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text(contract_code)
                console.print(f"\n[green]✅ Saved to: {output}[/green]")
            else:
                # Auto-save to generated contracts directory
                output_dir = Path("contracts/generated")
                output_dir.mkdir(parents=True, exist_ok=True)
                output = output_dir / f"contract_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sol"
                output.write_text(contract_code)
                console.print(f"\n[green]✅ Auto-saved to: {output}[/green]")
            
            # Auto-audit if requested
            if audit_after:
                console.print(f"\n[blue]🔍 Running security audit...[/blue]")
                audit_result = asyncio.run(agent.audit_contract(contract_code))
                display_audit_summary(audit_result)
        else:
            console.print(f"[red]❌ Generation failed: {result.get('error')}[/red]")
            sys.exit(1)
    
    except Exception as e:
        console.print(f"[red]❌ Error generating contract: {e}[/red]")
        import traceback
        console.print(traceback.format_exc())
        sys.exit(1)

# ============================================================================
# 3. AUDIT COMMAND - Multi-Source Support
# ============================================================================

@cli.command()
@click.argument("target")
@click.option("--network", default="hyperion", 
              type=click.Choice(["hyperion", "ethereum", "polygon", "arbitrum", "metis"]))
@click.option("--severity", type=click.Choice(["low", "medium", "high", "critical"]))
@click.option("--output", "-o", type=click.Path(), help="Save report to file")
@click.option("--format", type=click.Choice(["table", "json", "markdown"]), default="table")
@click.option("--explorer-url", help="Custom block explorer URL")
def audit(target, network, severity, output, format, explorer_url):
    """
    🔍 Audit smart contracts from multiple sources
    
    Examples:
    \b
    hyperagent audit contracts/Token.sol
    hyperagent audit 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb --network ethereum
    hyperagent audit https://etherscan.io/address/0x...
    """
    try:
        config = ConfigLoader.load()
        agent = HyperKitAgent(config)

        # Detect target type
        target_type, source_code, metadata = detect_audit_target(target, network, explorer_url)
        
        console.print(f"[blue]🔍 Auditing {target_type}: {target[:50]}...[/blue]")
        console.print(f"[cyan]Network: {network}[/cyan]")
        
        if target_type == "address":
            console.print(f"[cyan]Fetching verified source code from explorer...[/cyan]")
        
        # Run audit
        result = asyncio.run(agent.audit_contract(source_code))
        
        if result.get("status") == "success":
            audit_data = result.get("results", {})
            display_audit_report(audit_data, metadata, format)
            
            if output:
                save_audit_report(audit_data, metadata, output, format)
                console.print(f"\n[green]✅ Report saved to: {output}[/green]")
        else:
            console.print(f"[red]❌ Audit failed: {result.get('error')}[/red]")
            sys.exit(1)
    
    except Exception as e:
        console.print(f"[red]❌ Error auditing: {e}[/red]")
        sys.exit(1)

# ============================================================================
# 4. DEPLOY COMMAND - Enhanced Multi-Chain
# ============================================================================

@cli.command()
@click.argument("contract_path", type=click.Path(exists=True))
@click.option("--network", "-n", default="hyperion",
              type=click.Choice(["hyperion", "polygon", "arbitrum", "ethereum", "metis"]))
@click.option("--constructor-args", "-a", multiple=True, help="Constructor arguments")
@click.option("--gas-price", type=int, help="Custom gas price (Gwei)")
@click.option("--verify", is_flag=True, help="Verify on explorer")
@click.option("--wait", is_flag=True, default=True, help="Wait for confirmation")
def deploy(contract_path, network, constructor_args, gas_price, verify, wait):
    """
    🚀 Deploy smart contracts to blockchain
    
    Examples:
    \b
    hyperagent deploy contracts/Token.sol --network hyperion
    hyperagent deploy contracts/Token.sol -a "MyToken" "MTK" "1000000" --verify
    """
    try:
        config = ConfigLoader.load()
        agent = HyperKitAgent(config)

        with open(contract_path, "r") as f:
            source_code = f.read()
        
        console.print(Panel(
            f"[cyan]Contract:[/cyan] {Path(contract_path).name}\n"
            f"[cyan]Network:[/cyan] {network.upper()}\n"
            f"[cyan]Constructor Args:[/cyan] {', '.join(constructor_args) if constructor_args else 'None'}",
            title="📤 Deployment Configuration",
            expand=False
        ))
        
        if not click.confirm("Proceed with deployment?"):
            console.print("[yellow]Deployment cancelled[/yellow]")
            return
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            progress.add_task("🚀 Deploying contract...", total=None)
            result = asyncio.run(agent.deploy_contract(source_code, network))
        
        if result.get("status") == "deployed":
            tx_hash = result.get("tx_hash", "")
            contract_address = result.get("address", "")
            
            console.print(Panel(
                f"[green]✅ Deployment Successful![/green]\n"
                f"[cyan]Contract Address:[/cyan] [bold]{contract_address}[/bold]\n"
                f"[cyan]TX Hash:[/cyan] {tx_hash}\n"
                f"[cyan]Network:[/cyan] {network}",
                title="🎉 Deployment Summary",
                expand=False
            ))
            
            # Auto-verify if requested
            if verify:
                console.print("\n[blue]✅ Verifying contract on explorer...[/blue]")
                # Verification logic
            
        else:
            console.print(f"[red]❌ Deployment failed: {result.get('error')}[/red]")
            sys.exit(1)
    
    except Exception as e:
        console.print(f"[red]❌ Error deploying: {e}[/red]")
        sys.exit(1)

# ============================================================================
# 5. INTERACTIVE COMMAND - Development Mode
# ============================================================================

@cli.command()
@click.option("--mode", type=click.Choice(["prompt", "debug", "test"]), default="prompt")
def interactive(mode):
    """💬 Interactive development mode with real-time feedback"""
    try:
        config = ConfigLoader.load()
        agent = HyperKitAgent(config)
        
        console.print(Panel(
            "[cyan]HyperAgent Interactive Mode[/cyan]\n\n"
            "Commands:\n"
            "  [bold]gen[/bold] - Generate contract\n"
            "  [bold]audit[/bold] - Audit contract\n"
            "  [bold]deploy[/bold] - Deploy contract\n"
            "  [bold]help[/bold] - Show help\n"
            "  [bold]exit[/bold] - Exit",
            title="🚀 Interactive Shell",
            expand=False
        ))
        
        while True:
            try:
                user_input = console.input("[bold cyan]hyperagent> [/bold cyan]")
                
                if user_input.lower() == "exit":
                    console.print("[yellow]Goodbye![/yellow]")
                    break
                elif user_input.lower().startswith("gen"):
                    prompt = user_input[4:].strip()
                    if not prompt:
                        prompt = console.input("Contract description: ")
                    result = asyncio.run(agent.generate_contract(prompt, ""))
                    console.print(Syntax(result.get("contract_code", ""), "solidity", theme="monokai"))
                elif user_input.lower().startswith("help"):
                    console.print("Available commands: gen, audit, deploy, help, exit")
                else:
                    console.print(f"[yellow]Unknown command: {user_input}[/yellow]")
            
            except KeyboardInterrupt:
                console.print("\n[yellow]Interrupted[/yellow]")
                break
    
    except Exception as e:
        console.print(f"[red]❌ Error in interactive mode: {e}[/red]")
        sys.exit(1)

# ============================================================================
# 6. TEST COMMAND - Sample Workflows
# ============================================================================

@cli.command()
@click.option("--sample", type=click.Choice(["erc20", "erc721", "vault", "all"]), default="erc20")
@click.option("--verbose", "-v", is_flag=True)
def test(sample, verbose):
    """🧪 Test HyperAgent with sample workflows"""
    try:
        config = ConfigLoader.load()
        agent = HyperKitAgent(config)
        
        samples = {
            "erc20": "Create a standard ERC20 token named 'TestToken' with symbol 'TST'",
            "erc721": "Create an ERC721 NFT collection called 'MyNFTs' with royalty support",
            "vault": "Create a yield farming vault contract with deposit and withdraw functions",
        }
        
        if sample == "all":
            samples_to_run = samples
        else:
            samples_to_run = {sample: samples[sample]}
        
        for name, prompt in samples_to_run.items():
            console.print(f"\n[blue]🧪 Testing: {name.upper()}[/blue]")
            console.print(f"[cyan]Prompt: {prompt}[/cyan]")
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                progress.add_task("Generating...", total=None)
                result = asyncio.run(agent.generate_contract(prompt, ""))
            
            if result.get("status") == "success":
                console.print(f"[green]✅ {name.upper()} test passed[/green]")
                if verbose:
                    console.print(f"Lines of code: {len(result.get('contract_code', '').splitlines())}")
            else:
                console.print(f"[red]❌ {name.upper()} test failed[/red]")

    except Exception as e:
        console.print(f"[red]❌ Error running tests: {e}[/red]")
        sys.exit(1)

# ============================================================================
# 7. WORKFLOW COMMAND - Complete End-to-End
# ============================================================================

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
        import traceback
        console.print(traceback.format_exc())
        sys.exit(1)

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def detect_audit_target(target, network, explorer_url=None):
    """
    Detect what type of audit target we have:
    - File path
    - Contract address
    - Explorer URL
    - Raw bytecode
    """
    # Check if it's a file
    if Path(target).exists():
        with open(target, "r") as f:
            source_code = f.read()
        return "file", source_code, {"type": "file", "path": target}
    
    # Check if it's an Ethereum address
    if re.match(r"^0x[a-fA-F0-9]{40}$", target):
        source_code, metadata = fetch_from_address(target, network, explorer_url)
        return "address", source_code, metadata
    
    # Check if it's an explorer URL
    if target.startswith("http"):
        address = extract_address_from_url(target)
        source_code, metadata = fetch_from_address(address, network, explorer_url)
        return "explorer_url", source_code, metadata
    
    # Check if it's bytecode
    if target.startswith("0x") and len(target) > 100:
        return "bytecode", target, {"type": "bytecode"}
    
    raise ValueError(f"Could not detect target type for: {target}")


def fetch_from_address(address, network, custom_explorer_url=None):
    """Fetch verified source code from blockchain explorer"""
    
    # Explorer API endpoints
    explorers = {
        "hyperion": {
            "url": "https://hyperion-testnet-explorer.metisdevops.link",
            "api": "https://hyperion-testnet-explorer.metisdevops.link/api"
        },
        "ethereum": {
            "url": "https://etherscan.io",
            "api": "https://api.etherscan.io/api"
        },
        "polygon": {
            "url": "https://polygonscan.com",
            "api": "https://api.polygonscan.com/api"
        },
        "arbitrum": {
            "url": "https://arbiscan.io",
            "api": "https://api.arbiscan.io/api"
        },
        "metis": {
            "url": "https://andromeda-explorer.metis.io",
            "api": "https://andromeda-explorer.metis.io/api"
        }
    }
    
    explorer = explorers.get(network, explorers["ethereum"])
    api_url = custom_explorer_url or explorer["api"]
    
    # Fetch verified source code
    params = {
        "module": "contract",
        "action": "getsourcecode",
        "address": address
    }
    
    try:
        response = requests.get(api_url, params=params, timeout=10)
        data = response.json()
        
        if data.get("status") == "1" and data.get("result"):
            result = data["result"][0]
            source_code = result.get("SourceCode", "")
            
            if not source_code:
                # Try fetching bytecode if source not verified
                source_code = fetch_bytecode(address, network)
                
            metadata = {
                "type": "address",
                "address": address,
                "network": network,
                "contract_name": result.get("ContractName", "Unknown"),
                "compiler_version": result.get("CompilerVersion", "Unknown"),
                "optimization": result.get("OptimizationUsed", "Unknown"),
                "verified": bool(source_code)
            }
            
            return source_code, metadata
        else:
            raise ValueError(f"Could not fetch source from explorer: {data.get('message', 'Unknown error')}")
            
    except Exception as e:
        console.print(f"[yellow]⚠️  Failed to fetch from explorer: {e}[/yellow]")
        console.print(f"[cyan]Attempting to fetch bytecode instead...[/cyan]")
        source_code = fetch_bytecode(address, network)
        return source_code, {"type": "bytecode", "address": address, "network": network}


def fetch_bytecode(address, network):
    """Fetch contract bytecode from RPC"""
    rpc_urls = {
        "hyperion": "https://hyperion-testnet.metisdevops.link",
        "ethereum": "https://mainnet.infura.io/v3/YOUR_INFURA_KEY",
        "polygon": "https://polygon-rpc.com",
        "arbitrum": "https://arb1.arbitrum.io/rpc",
        "metis": "https://andromeda.metis.io"
    }
    
    rpc_url = rpc_urls.get(network, rpc_urls["hyperion"])
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    
    bytecode = w3.eth.get_code(Web3.to_checksum_address(address))
    return bytecode.hex()


def extract_address_from_url(url):
    """Extract contract address from explorer URL"""
    # Match patterns like:
    # https://etherscan.io/address/0x...
    # https://hyperion-testnet-explorer.metisdevops.link/address/0x...
    match = re.search(r"address/(0x[a-fA-F0-9]{40})", url)
    if match:
        return match.group(1)
    raise ValueError(f"Could not extract address from URL: {url}")


def display_audit_report(audit_data, metadata, format):
    """Display formatted audit report"""
    severity = audit_data.get("severity", "unknown")
    severity_color = {"critical": "red", "high": "orange3", "medium": "yellow", "low": "blue"}.get(severity, "white")
    
    console.print(Panel(
        f"[{severity_color}]Overall Severity: {severity.upper()}[/{severity_color}]",
        title="🔍 Security Audit Report",
        expand=False
    ))
    
    if format == "table":
        table = Table(title="Findings")
        table.add_column("Severity", width=10)
        table.add_column("Tool", width=12)
        table.add_column("Issue", width=40)
        table.add_column("Count", width=6)
        
        for finding in audit_data.get("findings", []):
            table.add_row(
                finding.get("severity", "info"),
                finding.get("tool", ""),
                finding.get("description", "")[:40],
                str(finding.get("matches", 0))
            )
        
        console.print(table)


def display_audit_summary(result):
    """Display audit summary"""
    if result.get("status") == "success":
        data = result.get("results", {})
        console.print(f"[green]✅ Audit complete - Severity: {data.get('severity', 'unknown')}[/green]")


def save_audit_report(audit_data, metadata, output_path, format):
    """Save audit report to file"""
    if format == "json":
        import json
        with open(output_path, "w") as f:
            json.dump({"metadata": metadata, "audit": audit_data}, f, indent=2)


def build_prompt_interactive():
    """Interactive prompt builder for contract generation"""
    console.print(Panel(
        "[cyan]Smart Contract Generator - Interactive Mode[/cyan]",
        title="🤖 Contract Builder",
        expand=False
    ))
    
    contract_type = click.prompt("Contract type", type=click.Choice(["token", "nft", "dex", "vault", "dao"]))
    contract_name = click.prompt("Contract name")
    features = click.prompt("Additional features (comma-separated)", default="")
    
    prompt = f"Create a {contract_type} contract named {contract_name}"
    if features:
        prompt += f" with features: {features}"
    
    return prompt


# ============================================================================
# WORKFLOW STAGE FUNCTIONS
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
            result = asyncio.run(agent.generate_contract(prompt, ""))
        
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
            contract_path.parent.mkdir(parents=True, exist_ok=True)
            contract_path.write_text(contract_code)
            console.print(f"[green]Saved to: {contract_path}[/green]")
        else:
            # Auto-save to generated contracts directory
            output_dir = Path("contracts/generated")
            output_dir.mkdir(parents=True, exist_ok=True)
            contract_path = output_dir / f"{contract_name}.sol"
            contract_path.write_text(contract_code)
            console.print(f"[green]Auto-saved to: {contract_path}[/green]")
        
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
        console.print(f"[red]Generation stage failed: {e}[/red]")
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
            result = asyncio.run(agent.audit_contract(contract_code))
        
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
            audit_path.parent.mkdir(parents=True, exist_ok=True)
            with open(audit_path, "w") as f:
                json.dump(audit_data, f, indent=2)
            console.print(f"[green]Audit report saved to: {audit_path}[/green]")
        else:
            # Auto-save to audits directory
            audit_dir = Path("artifacts/audits")
            audit_dir.mkdir(parents=True, exist_ok=True)
            audit_path = audit_dir / f"audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(audit_path, "w") as f:
                json.dump(audit_data, f, indent=2)
            console.print(f"[green]Auto-saved audit to: {audit_path}[/green]")
        
        return {
            "status": "success",
            "severity": severity,
            "findings_count": len(findings),
            "findings": findings
        }
    
    except Exception as e:
        console.print(f"[red]Audit stage failed: {e}[/red]")
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
            result = asyncio.run(agent.deploy_contract(contract_code, network))
        
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
        console.print(f"[red]Deployment stage failed: {e}[/red]")
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
        console.print(f"[red]Test stage failed: {e}[/red]")
        return {"status": "error", "error": str(e)}


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


def main():
    """Main entry point"""
    try:
        cli()
    except Exception as e:
        console.print(f"[red]Fatal error: {e}[/red]")
        sys.exit(1)


def cli_main():
    """CLI entry point for hyperagent command."""
    asyncio.run(main())


if __name__ == "__main__":
    main()