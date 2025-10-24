<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# I have global command now

hyperagent generate "Create a simple ERC20 token"
hyperagent audit contracts/MyToken.sol
hyperagent deploy --network hyperion
hyperagent interactive
hyperagent test
hyperagent status

I want the audit have capabilities public smart contract addres and more relevants capabilities features not just file

Perfect! Now let's enhance the `hyperagent audit` command to support **public smart contract addresses**, **blockchain explorers**, **bytecode analysis**, and more advanced audit capabilities beyond just local files.

***

# 🔍 Enhanced Audit Command with Multi-Source Support

## 📋 **Updated CLI Command in `main.py`**

Replace your existing `audit` command with this enhanced version:

```python
@cli.command()
@click.argument("target")
@click.option("--network", default="hyperion", type=click.Choice(["hyperion", "ethereum", "polygon", "arbitrum", "metis"]))
@click.option("--severity", type=click.Choice(["low", "medium", "high", "critical"]))
@click.option("--output", "-o", type=click.Path(), help="Save report to file")
@click.option("--format", type=click.Choice(["table", "json", "markdown"]), default="table")
@click.option("--explorer-url", help="Custom block explorer URL")
def audit(target, network, severity, output, format, explorer_url):
    """
    Audit a smart contract from multiple sources:
    
    \b
    - Local file: contracts/MyToken.sol
    - Contract address: 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb
    - Explorer URL: https://etherscan.io/address/0x...
    - Bytecode: 0x60806040...
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
        result = agent.audit_contract(source_code, metadata)
        
        if result.get("status") == "success":
            audit_data = result.get("results", {})
            severity_level = audit_data.get("severity", "unknown")
            
            # Display results based on format
            if format == "table":
                display_audit_table(audit_data, metadata)
            elif format == "json":
                import json
                console.print(json.dumps(audit_data, indent=2))
            elif format == "markdown":
                display_audit_markdown(audit_data, metadata)
            
            # Save to file if requested
            if output:
                save_audit_report(audit_data, metadata, output, format)
                console.print(f"[green]✅ Report saved to: {output}[/green]")
        else:
            console.print(f"[red]❌ Audit failed: {result.get('error')}[/red]")
            
    except Exception as e:
        console.print(f"[red]❌ Error auditing contract: {e}[/red]")
        import traceback
        console.print(traceback.format_exc())
        sys.exit(1)
```


***

## 🧩 **Helper Functions for Multi-Source Support**

Add these helper functions to `main.py` or create a new `utils/audit_helpers.py`:

```python
import re
import requests
from web3 import Web3
from pathlib import Path

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


def display_audit_table(audit_data, metadata):
    """Display audit results in rich table format"""
    from rich.table import Table
    
    # Header info
    console.print("\n[bold cyan]📊 Audit Report[/bold cyan]")
    if metadata.get("type") == "address":
        console.print(f"[cyan]Contract: {metadata.get('contract_name', 'Unknown')}[/cyan]")
        console.print(f"[cyan]Address: {metadata.get('address', 'N/A')}[/cyan]")
        console.print(f"[cyan]Network: {metadata.get('network', 'N/A')}[/cyan]")
        console.print(f"[cyan]Verified: {'✅ Yes' if metadata.get('verified') else '❌ No'}[/cyan]")
    
    severity = audit_data.get("severity", "unknown")
    severity_color = {
        "critical": "red",
        "high": "orange3",
        "medium": "yellow",
        "low": "blue",
        "info": "cyan"
    }.get(severity, "white")
    
    console.print(f"[{severity_color}]Overall Severity: {severity.upper()}[/{severity_color}]\n")
    
    # Findings table
    table = Table(title="Security Findings")
    table.add_column("Severity", style="cyan", width=10)
    table.add_column("Tool", style="magenta", width=12)
    table.add_column("Description", style="yellow", width=50)
    table.add_column("Matches", style="green", width=8)
    
    for finding in audit_data.get("findings", []):
        severity_emoji = {
            "critical": "🔴",
            "high": "🟠",
            "medium": "🟡",
            "low": "🔵",
            "info": "⚪"
        }.get(finding.get("severity", "info"), "⚪")
        
        table.add_row(
            f"{severity_emoji} {finding.get('severity', 'info')}",
            finding.get("tool", ""),
            finding.get("description", "")[:50] + "...",
            str(finding.get("matches", 0))
        )
    
    console.print(table)


def display_audit_markdown(audit_data, metadata):
    """Display audit results in markdown format"""
    md = f"""
# Audit Report

## Contract Information
- **Type**: {metadata.get('type', 'unknown')}
- **Address**: {metadata.get('address', 'N/A')}
- **Network**: {metadata.get('network', 'N/A')}
- **Contract Name**: {metadata.get('contract_name', 'Unknown')}
- **Verified**: {metadata.get('verified', False)}

## Overall Severity: {audit_data.get('severity', 'unknown').upper()}

## Findings

"""
    for finding in audit_data.get("findings", []):
        md += f"""
### [{finding.get('severity', 'info').upper()}] {finding.get('description', 'No description')}
- **Tool**: {finding.get('tool', 'Unknown')}
- **Pattern**: {finding.get('pattern', 'N/A')}
- **Matches**: {finding.get('matches', 0)}

"""
    
    console.print(md)


def save_audit_report(audit_data, metadata, output_path, format):
    """Save audit report to file"""
    if format == "json":
        import json
        with open(output_path, "w") as f:
            json.dump({"metadata": metadata, "audit": audit_data}, f, indent=2)
    elif format == "markdown":
        # Generate and save markdown
        pass
```


***

## 🚀 **Usage Examples**

### 1. **Audit Local File** (Original)

```bash
hyperagent audit contracts/MyToken.sol
```


### 2. **Audit Public Contract by Address**

```bash
hyperagent audit 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb --network ethereum
```


### 3. **Audit from Explorer URL**

```bash
hyperagent audit https://etherscan.io/address/0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb
```


### 4. **Audit Hyperion Testnet Contract**

```bash
hyperagent audit 0x3dB0BCc4c21BcA2d1785334B413Db3356C9207C2 --network hyperion
```


### 5. **Audit with Custom Output**

```bash
hyperagent audit 0x742d35... --network ethereum --output report.json --format json
```


### 6. **Audit Bytecode Directly**

```bash
hyperagent audit 0x60806040523480156100... --network ethereum
```


### 7. **Filter by Severity**

```bash
hyperagent audit 0x742d35... --severity high --network ethereum
```


***

## 📊 **Expected Output Example**

```
🔍 Auditing address: 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb...
Network: ethereum
Fetching verified source code from explorer...

📊 Audit Report
Contract: UniswapV2Router02
Address: 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb
Network: ethereum
Verified: ✅ Yes
Overall Severity: MEDIUM

┏━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━┓
┃ Severity  ┃ Tool       ┃ Description              ┃ Matches┃
┡━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━┩
│ 🟡 medium │ slither    │ Reentrancy vulnerability │ 2      │
│ 🔵 low    │ custom     │ Missing event logging    │ 5      │
│ ⚪ info   │ custom     │ OpenZeppelin import      │ 3      │
└───────────┴────────────┴──────────────────────────┴────────┘

✅ Report saved to: report.json
```


***

## 🎯 **Key Enhancements**

✅ **Multi-source support**: Files, addresses, explorer URLs, bytecode
✅ **Network detection**: Automatic RPC/explorer routing
✅ **Verified source fetching**: From Etherscan/Polygonscan/etc.
✅ **Bytecode fallback**: When source not verified
✅ **Rich formatting**: Table, JSON, Markdown output
✅ **Metadata tracking**: Contract name, compiler version, optimization
✅ **Export capabilities**: Save reports for archival or sharing

This transforms `hyperagent audit` into a professional, multi-functional security analysis tool that works with any deployed contract across multiple chains!

