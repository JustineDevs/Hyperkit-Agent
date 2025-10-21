#!/usr/bin/env python3
"""
HyperKit AI Agent - Command Line Interface
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from core.agent.main import HyperKitAgent
from core.tools.utils import validate_solidity_code, extract_contract_info


def load_config():
    """Load configuration from environment variables."""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    return {
        # AI Provider API Keys (Google Gemini Only)
        'GOOGLE_API_KEY': os.getenv('GOOGLE_API_KEY'),
        
        # Obsidian Integration
        'OBSIDIAN_VAULT_PATH': os.getenv('OBSIDIAN_VAULT_PATH', '~/hyperkit-kb'),
        
        # Blockchain Configuration
        'DEFAULT_PRIVATE_KEY': os.getenv('DEFAULT_PRIVATE_KEY'),
        'DEFAULT_NETWORK': os.getenv('DEFAULT_NETWORK', 'hyperion'),
        'networks': {
            'hyperion': os.getenv('HYPERION_RPC_URL', 'https://hyperion-testnet.metisdevops.link'),
            'polygon': os.getenv('POLYGON_RPC_URL', 'https://polygon-rpc.com'),
            'arbitrum': os.getenv('ARBITRUM_RPC_URL', 'https://arb1.arbitrum.io/rpc'),
            'ethereum': os.getenv('ETHEREUM_RPC_URL', 'https://mainnet.infura.io/v3/YOUR_PROJECT_ID')
        },
        
        # RAG Configuration
        'VECTORSTORE_PATH': os.getenv('VECTORSTORE_PATH', './data/vectordb'),
        'EMBEDDING_MODEL': os.getenv('EMBEDDING_MODEL', 'sentence-transformers/all-MiniLM-L6-v2'),
        
        # Security Tools
        'SLITHER_ENABLED': os.getenv('SLITHER_ENABLED', 'true'),
        'MYTHRIL_ENABLED': os.getenv('MYTHRIL_ENABLED', 'true'),
        'EDB_ENABLED': os.getenv('EDB_ENABLED', 'true'),
        
        # Logging
        'LOG_LEVEL': os.getenv('LOG_LEVEL', 'INFO')
    }


async def generate_command(args):
    """Handle the generate command."""
    config = load_config()
    
    # Configure for free models if requested
    if args.provider:
        if args.provider == 'google':
            print(f"Using Google Gemini")
        else:
            print(f"Only Google Gemini is supported. Using Google Gemini.")
    
    # Configure RAG
    if args.use_rag:
        config['OBSIDIAN_VAULT_PATH'] = os.path.expanduser('~/hyperkit-kb')
        print("Using Obsidian RAG for context retrieval")
    
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
        
        if args.save:
            from core.tools.utils import save_contract_to_file
            file_path = save_contract_to_file(
                result['contract_code'],
                args.save,
                args.output_dir or './contracts'
            )
            print(f"\nContract saved to: {file_path}")
    else:
        print(f"Generation failed: {result['error']}")
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
    
    print(f"Running complete workflow: {args.prompt}")
    
    result = await agent.run_workflow(args.prompt)
    
    print("\nWorkflow Results:")
    print("=" * 50)
    print(json.dumps(result, indent=2))
    print("=" * 50)
    
    if result['status'] == 'success':
        print("\n✅ Workflow completed successfully!")
    else:
        print(f"\n❌ Workflow failed: {result.get('error', 'Unknown error')}")
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
    gen_parser.add_argument('--provider', choices=['google'], 
                           help='AI provider to use (only Google Gemini is supported)')
    gen_parser.add_argument('--model', help='Specific model to use (e.g., llama3.1:8b, qwen2.5-coder:32b)')
    gen_parser.add_argument('--use-rag', action='store_true', help='Use Obsidian RAG for context retrieval')
    gen_parser.add_argument('--save', help='Save contract to file')
    gen_parser.add_argument('--output-dir', default='./contracts', help='Output directory')
    
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
    deploy_parser.add_argument('--network', default='hyperion', help='Target network')
    deploy_parser.add_argument('--constructor-args', help='Constructor arguments (JSON)')
    deploy_parser.add_argument('--private-key', help='Private key for deployment')
    
    # Workflow command
    workflow_parser = subparsers.add_parser('workflow', help='Run complete workflow')
    workflow_parser.add_argument('prompt', help='Natural language description of the contract')
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate contract code')
    validate_parser.add_argument('--file', help='Contract file to validate')
    validate_parser.add_argument('--code', help='Contract code to validate')
    
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
    elif args.command == 'validate':
        validate_command(args)


if __name__ == "__main__":
    main()
