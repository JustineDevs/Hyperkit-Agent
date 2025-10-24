#!/usr/bin/env python3
"""
🔍 HyperAgent Deployment Error Root Cause Analyzer
Traces data flow through configuration → agent → deployer
"""

import os
import sys
import json
import inspect
from pathlib import Path
from typing import Any, Dict

# Color codes for output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text: str):
    """Print formatted header"""
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*80}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.HEADER}🔍 {text}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.HEADER}{'='*80}{Colors.END}\n")

def print_section(text: str):
    """Print formatted section"""
    print(f"\n{Colors.CYAN}{Colors.BOLD}→ {text}{Colors.END}")
    print(f"{Colors.CYAN}{'-'*70}{Colors.END}")

def print_success(text: str):
    """Print success message"""
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")

def print_error(text: str):
    """Print error message"""
    print(f"{Colors.RED}❌ {text}{Colors.END}")

def print_warning(text: str):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")

def print_info(text: str, value: Any = None):
    """Print info with value"""
    if value is None:
        print(f"{Colors.BLUE}ℹ️  {text}{Colors.END}")
    else:
        print(f"{Colors.BLUE}ℹ️  {text}: {Colors.BOLD}{value}{Colors.END}")

def analyze_config_file():
    """Step 1: Analyze configuration file"""
    print_section("Step 1: Analyzing Configuration Loading")
    
    try:
        from core.config.loader import ConfigLoader
        
        print_info("Loading configuration...")
        config = ConfigLoader.load()
        
        # Check if config is dict
        if not isinstance(config, dict):
            print_error(f"Config is {type(config).__name__}, expected dict")
            return None
        
        print_success(f"Config loaded as {type(config).__name__}")
        
        # Check networks
        if 'networks' not in config:
            print_error("'networks' key missing from config")
            return config
        
        networks_config = config['networks']
        print_info("Networks found", list(networks_config.keys()))
        
        # Check hyperion config
        if 'hyperion' not in networks_config:
            print_error("'hyperion' network not in config")
            return config
        
        hyperion_config = networks_config['hyperion']
        print_info("Hyperion config type", type(hyperion_config).__name__)
        print_info("Hyperion config keys", list(hyperion_config.keys()) if isinstance(hyperion_config, dict) else "NOT A DICT")
        
        # Check RPC URL
        if isinstance(hyperion_config, dict):
            rpc_url = hyperion_config.get('rpc_url')
            print_info("RPC URL type", type(rpc_url).__name__)
            print_info("RPC URL value", str(rpc_url)[:60] if rpc_url else "NOT SET")
            
            if not isinstance(rpc_url, str):
                print_error(f"RPC URL should be STRING, got {type(rpc_url).__name__}")
            else:
                print_success("RPC URL is a STRING ✓")
        else:
            print_error(f"Hyperion config should be dict, got {type(hyperion_config).__name__}")
        
        return config
    
    except Exception as e:
        print_error(f"Error loading config: {e}")
        import traceback
        traceback.print_exc()
        return None

def analyze_agent_deployment():
    """Step 2: Analyze agent deploy_contract method"""
    print_section("Step 2: Analyzing Agent deploy_contract Method")
    
    try:
        from core.agent.main import HyperKitAgent
        from core.config.loader import ConfigLoader
        
        config = ConfigLoader.load()
        agent = HyperKitAgent(config)
        
        print_success("Agent initialized")
        
        # Get the deploy_contract method
        deploy_method = agent.deploy_contract
        
        # Get source code
        source = inspect.getsource(deploy_method)
        print_info("Method source (first 500 chars):")
        print(f"  {Colors.YELLOW}{source[:500]}{Colors.END}...")
        
        # Check for critical issues
        if "deployer.deploy" in source:
            print_success("Found deployer.deploy call")
            
            # Extract the line
            for i, line in enumerate(source.split('\n')):
                if 'deployer.deploy' in line:
                    print_info(f"Line {i}: {Colors.YELLOW}{line.strip()}{Colors.END}")
                    
                    # Check what's being passed
                    if "self.config['networks']" in line:
                        print_error("❌ FOUND BUG: Passing entire config dict instead of RPC URL!")
                        print_warning("Should pass: rpc_url (string)")
                        print_warning("Currently passing: self.config['networks'][network] (dict)")
                    elif "rpc_url" in line:
                        print_success("✓ Correctly passing rpc_url")
        else:
            print_warning("deployer.deploy call not found")
        
        return agent
    
    except Exception as e:
        print_error(f"Error analyzing agent: {e}")
        import traceback
        traceback.print_exc()
        return None

def analyze_deployer_method():
    """Step 3: Analyze deployer.deploy method signature"""
    print_section("Step 3: Analyzing Deployer deploy Method")
    
    try:
        from services.deployment.deployer import MultiChainDeployer
        
        deployer = MultiChainDeployer({})
        print_success("Deployer initialized")
        
        # Get method signature
        deploy_method = deployer.deploy
        sig = inspect.signature(deploy_method)
        
        print_info("Method signature:")
        print(f"  {Colors.YELLOW}def deploy{sig}{Colors.END}")
        
        # Check parameters
        params = sig.parameters
        print_info("Parameters:")
        for param_name, param in params.items():
            if param_name == 'self':
                continue
            
            param_type = param.annotation if param.annotation != inspect.Parameter.empty else "not specified"
            print(f"  • {Colors.BOLD}{param_name}{Colors.END}: {param_type}")
        
        # Check if second parameter is rpc_url or config
        param_names = [p for p in params.keys() if p != 'self']
        if len(param_names) > 1:
            second_param = param_names[1]
            if second_param == 'config':
                print_error("❌ FOUND BUG: Deployer expects 'config' dict, not 'rpc_url' string!")
            elif second_param == 'network':
                print_success("✓ Deployer correctly expects 'network' string")
            else:
                print_warning(f"Unexpected parameter: {second_param}")
        
        # Get source code
        source = inspect.getsource(deploy_method)
        print_info("Method source (first 300 chars):")
        print(f"  {Colors.YELLOW}{source[:300]}{Colors.END}...")
        
        return deployer
    
    except Exception as e:
        print_error(f"Error analyzing deployer: {e}")
        import traceback
        traceback.print_exc()
        return None

def trace_data_flow():
    """Step 4: Trace data flow through system"""
    print_section("Step 4: Tracing Data Flow Path")
    
    try:
        from core.config.loader import ConfigLoader
        from core.agent.main import HyperKitAgent
        
        print_info("Starting data flow trace...")
        
        # Load config
        config = ConfigLoader.load()
        print_info("1. Config loaded:", type(config).__name__)
        
        # Initialize agent
        agent = HyperKitAgent(config)
        print_info("2. Agent initialized")
        
        # Get network config
        network = "hyperion"
        network_config = config['networks'][network]
        print_info("3. Network config retrieved:", type(network_config).__name__)
        
        # Get RPC URL
        rpc_url = network_config.get('rpc_url')
        print_info("4. RPC URL extracted:", type(rpc_url).__name__)
        print_info("   Value:", str(rpc_url)[:60] if rpc_url else "NONE")
        
        # Show what SHOULD happen vs what IS happening
        print_info("\n📊 Expected vs Actual:")
        print(f"  {Colors.GREEN}Expected: agent.deploy_contract() → extracts rpc_url (str) → deployer.deploy(src, network, args){Colors.END}")
        print(f"  {Colors.RED}Actual: agent.deploy_contract() → passes network_config (dict) → deployer.deploy(src, config_dict){Colors.END}")
        
        return True
    
    except Exception as e:
        print_error(f"Error tracing data flow: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_file_contents():
    """Step 5: Check actual file contents"""
    print_section("Step 5: Checking File Contents")
    
    files_to_check = [
        ("core/agent/main.py", "deployer.deploy"),
        ("services/deployment/deployer.py", "def deploy")
    ]
    
    for filepath, search_term in files_to_check:
        print_info(f"Checking {filepath}:")
        
        try:
            with open(filepath, 'r') as f:
                lines = f.readlines()
            
            found = False
            for i, line in enumerate(lines, 1):
                if search_term in line:
                    found = True
                    # Print context (5 lines before and after)
                    start = max(0, i - 6)
                    end = min(len(lines), i + 5)
                    
                    print(f"\n  {Colors.YELLOW}Line {i} (with context):{Colors.END}")
                    for j in range(start, end):
                        prefix = "→ " if j == i - 1 else "  "
                        print(f"    {prefix}{j+1}: {lines[j].rstrip()}")
            
            if not found:
                print_warning(f"  '{search_term}' not found in {filepath}")
        
        except FileNotFoundError:
            print_error(f"  File not found: {filepath}")
        except Exception as e:
            print_error(f"  Error reading file: {e}")

def generate_report():
    """Generate final report"""
    print_header("📋 FINAL ANALYSIS REPORT")
    
    print(f"\n{Colors.BOLD}{Colors.BLUE}Analysis Summary:{Colors.END}\n")
    
    issues = []
    
    # Check 1: Configuration
    print("Checking configuration...")
    try:
        from core.config.loader import ConfigLoader
        config = ConfigLoader.load()
        hyperion = config['networks']['hyperion']
        rpc_url = hyperion.get('rpc_url')
        
        if not isinstance(rpc_url, str):
            issues.append("Configuration: RPC URL is not a string")
        else:
            print_success("✓ Configuration OK: RPC URL is string")
    except Exception as e:
        issues.append(f"Configuration: Error loading - {e}")
    
    # Check 2: Agent method
    print("Checking agent deploy method...")
    try:
        from core.agent.main import HyperKitAgent
        source = inspect.getsource(HyperKitAgent.deploy_contract)
        
        if "self.config['networks']" in source and "deployer.deploy" in source:
            issues.append("Agent: Passing config dict instead of rpc_url to deployer")
        else:
            print_success("✓ Agent OK: Correctly extracting rpc_url")
    except Exception as e:
        issues.append(f"Agent: Error analyzing - {e}")
    
    # Check 3: Deployer signature
    print("Checking deployer signature...")
    try:
        from services.deployment.deployer import MultiChainDeployer
        sig = inspect.signature(MultiChainDeployer.deploy)
        params = list(sig.parameters.keys())
        
        if 'config' in params:
            issues.append("Deployer: Still expects 'config' dict instead of 'rpc_url' string")
        else:
            print_success("✓ Deployer OK: Correct parameter names")
    except Exception as e:
        issues.append(f"Deployer: Error analyzing - {e}")
    
    # Report
    if issues:
        print_error(f"\n⚠️  {len(issues)} ISSUE(S) FOUND:\n")
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. {Colors.RED}{issue}{Colors.END}")
    else:
        print_success("\n✅ All checks passed! No issues found.")
    
    print(f"\n{Colors.BOLD}{Colors.BLUE}Recommendations:{Colors.END}\n")
    if issues:
        print("  1. Apply fixes from previous guidance")
        print("  2. Replace deployer.py with correct parameter names")
        print("  3. Update agent deploy_contract to extract rpc_url as string")
        print("  4. Run this script again to verify fixes")
    else:
        print("  System is correctly configured!")

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Run all analyses"""
    print(f"{Colors.BOLD}{Colors.HEADER}")
    print("╔" + "="*78 + "╗")
    print("║" + " "*78 + "║")
    print("║" + "  HyperAgent Deployment Error Root Cause Analyzer  ".center(78) + "║")
    print("║" + " "*78 + "║")
    print("╚" + "="*78 + "╝")
    print(f"{Colors.END}\n")
    
    # Run all analyses
    print_header("Running Comprehensive Analysis")
    
    config = analyze_config_file()
    agent = analyze_agent_deployment()
    deployer = analyze_deployer_method()
    trace_data_flow()
    check_file_contents()
    
    # Generate final report
    generate_report()
    
    print(f"\n{Colors.BOLD}{Colors.GREEN}✅ Debug analysis complete!{Colors.END}\n")

if __name__ == "__main__":
    main()
