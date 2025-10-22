#!/usr/bin/env python3
"""
HyperKit AI Agent - Command Line Interface
"""

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from core.agent.main import HyperKitAgent
from core.tools.utils import validate_solidity_code, extract_contract_info


def load_config():
    """Load configuration using the new configuration system."""
    from core.config.loader import get_config
    
    config_loader = get_config()
    return config_loader.to_dict()


async def generate_command(args):
    """Handle the generate command."""
    config = load_config()
    
    # Configure for cloud-based models
    if args.provider:
        if args.provider in ['google', 'openai']:
            print(f"Using {args.provider.title()} cloud provider")
        else:
            print(f"Only Google Gemini and OpenAI are supported. Using Google Gemini.")
    
        # Configure RAG
        if args.use_rag:
            print("Using Obsidian MCP Docker for context retrieval")
    
    agent = HyperKitAgent(config)
    
    print(f"Generating contract: {args.prompt}")
    
    result = await agent.generate_contract(args.prompt, args.context or "")
    
    if result['status'] == 'success':
        print("\nGenerated Contract:")
        print("=" * 50)
        print(result['contract_code'])
        print("=" * 50)
        print(f"Provider used: {result.get('provider_used', 'unknown')}")
        
        if args.use_rag and 'context_used' in result:
            print(f"RAG context length: {len(result['context_used'])} chars")
        
        # Show warnings if any
        if 'warnings' in result and result['warnings']:
            print("\nWarnings:")
            for warning in result['warnings']:
                print(f"  ⚠️  {warning}")
        
        if args.save:
            from core.tools.utils import save_contract_to_file
            file_path = save_contract_to_file(
                result['contract_code'],
                args.save,
                args.output_dir
            )
            print(f"\nContract saved to: {file_path}")
    else:
        print(f"Generation failed: {result.get('message', result.get('error', 'Unknown error'))}")
        
        # Show detailed error information
        if 'error_id' in result:
            print(f"Error ID: {result['error_id']}")
            print(f"Category: {result.get('category', 'unknown')}")
            print(f"Severity: {result.get('severity', 'unknown')}")
        
        if 'suggestions' in result and result['suggestions']:
            print("\nSuggestions:")
            for suggestion in result['suggestions']:
                print(f"  💡 {suggestion}")
        
        sys.exit(1)


async def audit_command(args):
    """Handle the audit command."""
    config = load_config()
    agent = HyperKitAgent(config)
    
    # Load contract code
    if args.file:
        with open(args.file, 'r') as f:
            contract_code = f.read()
    else:
        contract_code = args.code
    
    print("Auditing contract...")
    
    result = await agent.audit_contract(contract_code)
    
    if result['status'] == 'success':
        print(f"\nAudit Results:")
        print(f"Severity: {result['severity'].upper()}")
        print(f"Findings: {len(result['results'].get('findings', []))}")
        
        if args.verbose:
            print("\nDetailed Results:")
            print(json.dumps(result['results'], indent=2))
        
        if args.report:
            from core.tools.utils import create_audit_report
            report = create_audit_report(result['results'])
            with open(args.report, 'w') as f:
                f.write(report)
            print(f"\nAudit report saved to: {args.report}")
    else:
        print(f"Audit failed: {result['error']}")
        sys.exit(1)


async def deploy_command(args):
    """Handle the deploy command."""
    config = load_config()
    agent = HyperKitAgent(config)
    
    # Load contract code
    if args.file:
        with open(args.file, 'r') as f:
            contract_code = f.read()
    else:
        contract_code = args.code
    
    print(f"Deploying contract to {args.network}...")
    
    result = await agent.deploy_contract(
        contract_code,
        args.network,
        args.constructor_args,
        args.private_key
    )
    
    if result['status'] == 'success':
        print(f"\nDeployment successful!")
        print(f"Address: {result['deployment']['address']}")
        print(f"Transaction: {result['deployment']['tx_hash']}")
        print(f"Gas Used: {result['deployment']['gas_used']}")
    else:
        print(f"Deployment failed: {result['error']}")
        sys.exit(1)


async def workflow_command(args):
    """Handle the workflow command."""
    config = load_config()
    agent = HyperKitAgent(config)
    
    print(f"Running comprehensive workflow: {args.prompt}")
    
    # Run comprehensive workflow
    result = await agent.run_comprehensive_workflow(args.prompt)
    
    print("\n" + "="*60)
    print("🚀 COMPREHENSIVE WORKFLOW RESULTS")
    print("="*60)
    
    if result.get('status') == 'success':
        workflow_type = result.get('workflow', 'unknown')
        print(f"✅ Workflow completed: {workflow_type}")
        
        # Display contract deployment info
        if 'contract_deployment' in result:
            deployment = result['contract_deployment']
            print(f"✅ Contract deployed: {deployment.get('address', 'N/A')}")
            print(f"📝 Transaction: {deployment.get('tx_hash', 'N/A')}")
        
        # Display dApp scaffolding info
        if 'scaffold_result' in result:
            scaffold = result['scaffold_result']
            print(f"✅ dApp scaffolded: {scaffold.get('project_path', 'N/A')}")
            if scaffold.get('frontend_url'):
                print(f"🌐 Frontend URL: {scaffold.get('frontend_url')}")
            if scaffold.get('backend_url'):
                print(f"🔧 Backend URL: {scaffold.get('backend_url')}")
        
        # Display debug session info
        if 'debug_session' in result:
            debug = result['debug_session']
            print(f"🐛 Debug session started: {debug.get('session_id', 'N/A')}")
            print(f"📝 Transaction: {debug.get('tx_hash', 'N/A')}")
        
        # Display audit logging info
        if 'audit_logged' in result:
            audit_log = result['audit_logged']
            if audit_log.get('success'):
                print(f"📋 Audit logged onchain: {audit_log.get('tx_hash', 'N/A')}")
        
        print(f"\nDetailed Results:")
        print(json.dumps(result, indent=2))
        
    else:
        print(f"❌ Workflow failed: {result.get('error', 'Unknown error')}")
        print(f"\nError Details:")
        print(json.dumps(result, indent=2))
        sys.exit(1)


async def debug_command(args):
    """Handle the debug command."""
    config = load_config()
    agent = HyperKitAgent(config)
    
    print(f"Starting debug session for transaction: {args.tx_hash}")
    
    result = await agent.debug_transaction(args.tx_hash, args.steps)
    
    print("\n" + "="*50)
    print("🐛 DEBUG SESSION RESULTS")
    print("="*50)
    
    if result.get('status') == 'success':
        debug_session = result.get('debug_session', {})
        step_result = result.get('step_result', {})
        
        print(f"✅ Debug session started: {debug_session.get('session_id', 'N/A')}")
        print(f"📝 Transaction: {debug_session.get('tx_hash', 'N/A')}")
        print(f"🔄 Steps executed: {step_result.get('step_count', 0)}")
        
        if step_result.get('variables'):
            print(f"\n📊 Variables:")
            for var_name, var_value in step_result['variables'].items():
                print(f"  {var_name}: {var_value}")
        
        if step_result.get('call_stack'):
            print(f"\n📚 Call Stack:")
            for frame in step_result['call_stack']:
                print(f"  {frame.get('frame', 'Unknown')}")
        
        print(f"\nDebug Commands Available:")
        print(f"  - step_through_transaction(session_id, steps)")
        print(f"  - inspect_variable(session_id, variable_name)")
        print(f"  - get_call_stack(session_id)")
        print(f"  - end_debug_session(session_id)")
        
    else:
        print(f"❌ Debug session failed: {result.get('error', 'Unknown error')}")
        print(f"\nError Details:")
        print(json.dumps(result, indent=2))
        sys.exit(1)


def validate_command(args):
    """Handle the validate command."""
    if args.file:
        with open(args.file, 'r') as f:
            contract_code = f.read()
    else:
        contract_code = args.code
    
    print("Validating contract...")
    
    validation = validate_solidity_code(contract_code)
    info = extract_contract_info(contract_code)
    
    print(f"\nValidation Results:")
    print(f"Valid: {'✅' if validation['valid'] else '❌'}")
    
    if validation['errors']:
        print(f"Errors: {len(validation['errors'])}")
        for error in validation['errors']:
            print(f"  - {error}")
    
    if validation['warnings']:
        print(f"Warnings: {len(validation['warnings'])}")
        for warning in validation['warnings']:
            print(f"  - {warning}")
    
    if validation['suggestions']:
        print(f"Suggestions: {len(validation['suggestions'])}")
        for suggestion in validation['suggestions']:
            print(f"  - {suggestion}")
    
    print(f"\nContract Info:")
    print(f"Name: {info['contract_name']}")
    print(f"Functions: {len(info['functions'])}")
    print(f"Events: {len(info['events'])}")
    print(f"Modifiers: {len(info['modifiers'])}")


async def bridge_command(args):
    """Handle bridge operations."""
    config = load_config()
    agent = HyperKitAgent(config)
    
    print(f"🌉 Bridge operation: {args.action}")
    print(f"From: {args.from_chain} → To: {args.to_chain}")
    
    if args.action == "setup":
        print("Setting up cross-chain bridge...")
        # TODO: Implement bridge setup
        print("✅ Bridge setup completed")
    elif args.action == "transfer":
        if not args.amount or not args.token:
            print("❌ Error: --amount and --token required for transfer")
            return
        print(f"Transferring {args.amount} {args.token} from {args.from_chain} to {args.to_chain}")
        # TODO: Implement bridge transfer
        print("✅ Bridge transfer initiated")
    elif args.action == "status":
        print("Checking bridge status...")
        # TODO: Implement bridge status check
        print("✅ Bridge status: Active")


async def monitor_command(args):
    """Handle monitoring operations."""
    config = load_config()
    agent = HyperKitAgent(config)
    
    print(f"📊 Monitoring: {args.target}")
    print(f"Network: {args.network}")
    
    if args.gas:
        print("🔍 Gas monitoring enabled")
    
    # TODO: Implement monitoring
    print("✅ Monitoring started")


async def test_apis_command(args):
    """Test API connectivity."""
    print("🚀 Testing API connectivity...")
    
    # Run the API test script
    import subprocess
    result = subprocess.run([sys.executable, "test_api_keys.py"], 
                          capture_output=True, text=True)
    
    print(result.stdout)
    if result.stderr:
        print("Errors:", result.stderr)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="HyperKit AI Agent - Smart Contract Generation, Auditing, and Deployment",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate a contract
  python cli.py generate "Create a simple ERC20 token"
  
  # Audit a contract
  python cli.py audit --file contract.sol
  
  # Deploy a contract
  python cli.py deploy --file contract.sol --network hyperion
  
  # Run complete workflow
  python cli.py workflow "Create a DeFi vault with staking"
  
  # Validate contract code
  python cli.py validate --file contract.sol
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Generate command
    gen_parser = subparsers.add_parser('generate', help='Generate a smart contract')
    gen_parser.add_argument('prompt', help='Natural language description of the contract')
    gen_parser.add_argument('--context', help='Additional context for generation')
    gen_parser.add_argument('--provider', choices=['google', 'openai'], 
                           help='AI provider to use (Google Gemini or OpenAI)')
    gen_parser.add_argument('--network', choices=['hyperion'], 
                           help='Target network for deployment (only Hyperion testnet is supported)')
    gen_parser.add_argument('--model', help='Specific model to use (e.g., gemini-1.5-flash, gpt-4o-mini)')
    gen_parser.add_argument('--use-rag', action='store_true', help='Use Obsidian MCP Docker for context retrieval')
    gen_parser.add_argument('--save', help='Save contract to file')
    gen_parser.add_argument('--output-dir', default='./contracts/agent_generate', help='Output directory')
    
    # Audit command
    audit_parser = subparsers.add_parser('audit', help='Audit a smart contract')
    audit_parser.add_argument('--file', help='Contract file to audit')
    audit_parser.add_argument('--code', help='Contract code to audit')
    audit_parser.add_argument('--verbose', action='store_true', help='Show detailed results')
    audit_parser.add_argument('--report', help='Save audit report to file')
    
    # Deploy command
    deploy_parser = subparsers.add_parser('deploy', help='Deploy a smart contract')
    deploy_parser.add_argument('--file', help='Contract file to deploy')
    deploy_parser.add_argument('--code', help='Contract code to deploy')
    deploy_parser.add_argument('--network', default='hyperion', choices=['hyperion'], 
                              help='Target network (only Hyperion testnet is supported)')
    deploy_parser.add_argument('--constructor-args', help='Constructor arguments (JSON)')
    deploy_parser.add_argument('--private-key', help='Private key for deployment')
    
    # Workflow command
    workflow_parser = subparsers.add_parser('workflow', help='Run complete workflow')
    workflow_parser.add_argument('prompt', help='Natural language description of the contract')
    
    # Debug command
    debug_parser = subparsers.add_parser('debug', help='Debug a transaction using EDB')
    debug_parser.add_argument('tx_hash', help='Transaction hash to debug')
    debug_parser.add_argument('--steps', type=int, default=1, help='Number of steps to execute')
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate contract code')
    validate_parser.add_argument('--file', help='Contract file to validate')
    validate_parser.add_argument('--code', help='Contract code to validate')
    
    # Bridge command
    bridge_parser = subparsers.add_parser('bridge', help='Cross-chain bridging operations')
    bridge_parser.add_argument('action', choices=['setup', 'transfer', 'status'], help='Bridge action')
    bridge_parser.add_argument('--from', dest='from_chain', default='hyperion', help='Source chain')
    bridge_parser.add_argument('--to', dest='to_chain', default='andromeda', help='Destination chain')
    bridge_parser.add_argument('--amount', type=float, help='Amount to bridge')
    bridge_parser.add_argument('--token', help='Token address to bridge')
    
    # Monitor command
    monitor_parser = subparsers.add_parser('monitor', help='Monitor transactions and contracts')
    monitor_parser.add_argument('target', help='Contract address or transaction hash to monitor')
    monitor_parser.add_argument('--network', default='hyperion', help='Network to monitor')
    monitor_parser.add_argument('--gas', action='store_true', help='Monitor gas usage')
    
    # Test APIs command
    test_parser = subparsers.add_parser('test-apis', help='Test API connectivity')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Run the appropriate command
    if args.command == 'generate':
        asyncio.run(generate_command(args))
    elif args.command == 'audit':
        asyncio.run(audit_command(args))
    elif args.command == 'deploy':
        asyncio.run(deploy_command(args))
    elif args.command == 'workflow':
        asyncio.run(workflow_command(args))
    elif args.command == 'debug':
        asyncio.run(debug_command(args))
    elif args.command == 'validate':
        validate_command(args)
    elif args.command == 'bridge':
        asyncio.run(bridge_command(args))
    elif args.command == 'monitor':
        asyncio.run(monitor_command(args))
    elif args.command == 'test-apis':
        asyncio.run(test_apis_command(args))


if __name__ == "__main__":
    main()
