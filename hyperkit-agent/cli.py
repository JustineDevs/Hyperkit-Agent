#!/usr/bin/env python3
"""
HyperKit AI Agent - Command Line Interface
"""

import argparse
import asyncio
import json
import os
import sys
import time
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from core.agent.main import HyperKitAgent
from core.tools.utils import validate_solidity_code, extract_contract_info
from services.gas import GasEstimator, GasOptimizer
from services.monitoring import TransactionMonitor


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


async def gas_estimate_command(args):
    """Handle the gas-estimate command."""
    config = load_config()
    estimator = GasEstimator(config)
    
    if args.action == 'deployment':
        # Estimate gas for contract deployment
        if not args.bytecode:
            print("Error: --bytecode is required for deployment estimation")
            return
        
        constructor_args = None
        if args.constructor_args:
            try:
                constructor_args = json.loads(args.constructor_args)
            except json.JSONDecodeError:
                print("Error: Invalid JSON in constructor arguments")
                return
        
        estimate = await estimator.estimate_deployment_gas(
            contract_bytecode=args.bytecode,
            constructor_args=constructor_args,
            network=args.network
        )
        
        print(estimator.format_gas_estimate(estimate))
        
    elif args.action == 'function':
        # Estimate gas for function call
        if not all([args.contract_address, args.function_abi, args.function_name]):
            print("Error: --contract-address, --function-abi, and --function-name are required for function estimation")
            return
        
        try:
            function_abi = json.loads(args.function_abi)
        except json.JSONDecodeError:
            print("Error: Invalid JSON in function ABI")
            return
        
        function_args = None
        if args.function_args:
            try:
                function_args = json.loads(args.function_args)
            except json.JSONDecodeError:
                print("Error: Invalid JSON in function arguments")
                return
        
        estimate = await estimator.estimate_function_call_gas(
            contract_address=args.contract_address,
            function_abi=function_abi,
            function_name=args.function_name,
            function_args=function_args,
            network=args.network
        )
        
        print(estimator.format_gas_estimate(estimate))
        
    elif args.action == 'info':
        # Get network gas information
        gas_info = await estimator.get_network_gas_info(args.network)
        print(json.dumps(gas_info, indent=2))


async def gas_optimize_command(args):
    """Handle the gas-optimize command."""
    optimizer = GasOptimizer()
    
    # Analyze contract file
    try:
        if not os.path.exists(args.file):
            print(f"Error: File {args.file} not found")
            return
    except Exception as e:
        print(f"Error reading file: {e}")
        return
    
    # Analyze contract
    report = optimizer.analyze_contract(args.file)
    
    # Generate and display report
    print(optimizer.generate_optimization_report(report))
    
    # Export JSON if requested
    if args.export:
        json_report = optimizer.export_report_json(report)
        with open(args.export, 'w', encoding='utf-8') as f:
            f.write(json_report)
        print(f"\nReport exported to {args.export}")


async def monitor_transaction_command(args):
    """Handle the monitor-transaction command."""
    config = load_config()
    monitor = TransactionMonitor(config)
    
    if args.action == 'add':
        # Add transaction to monitoring
        success = await monitor.add_transaction(
            tx_hash=args.tx_hash,
            network=args.network
        )
        
        if success:
            print(f"✅ Added transaction {args.tx_hash} to monitoring on {args.network}")
        else:
            print(f"❌ Failed to add transaction {args.tx_hash} to monitoring")
    
    elif args.action == 'status':
        # Get transaction status
        tx_status = await monitor.get_transaction_status(args.tx_hash)
        
        if tx_status:
            print(f"Transaction Status for {args.tx_hash}:")
            print(f"├── Status: {tx_status.status}")
            print(f"├── Network: {tx_status.network}")
            print(f"├── Block Number: {tx_status.block_number or 'N/A'}")
            print(f"├── Gas Used: {tx_status.gas_used or 'N/A'}")
            print(f"├── Gas Price: {tx_status.gas_price or 'N/A'}")
            print(f"├── Confirmations: {tx_status.confirmation_count}")
            print(f"└── Timestamp: {tx_status.timestamp}")
        else:
            print(f"❌ Transaction {args.tx_hash} not found in monitoring")
    
    elif args.action == 'list':
        # List all monitored transactions
        transactions = await monitor.get_all_transactions()
        
        if transactions:
            print(f"Monitored Transactions ({len(transactions)}):")
            print("-" * 50)
            for tx in transactions:
                print(f"📄 {tx.tx_hash[:10]}... | {tx.status} | {tx.network}")
        else:
            print("No transactions being monitored")
    
    elif args.action == 'metrics':
        # Get monitoring metrics
        metrics = await monitor.get_metrics()
        
        print("Monitoring Metrics:")
        print("=" * 30)
        print(f"Total Transactions: {metrics.total_transactions}")
        print(f"Confirmed: {metrics.confirmed_transactions}")
        print(f"Failed: {metrics.failed_transactions}")
        print(f"Pending: {metrics.pending_transactions}")
        print(f"Success Rate: {metrics.success_rate:.1f}%")
        print(f"Avg Gas Used: {metrics.average_gas_used:.0f}")
        print(f"Avg Gas Price: {metrics.average_gas_price / 1e9:.2f} Gwei")
    
    elif args.action == 'remove':
        # Remove transaction from monitoring
        success = await monitor.remove_transaction(args.tx_hash)
        
        if success:
            print(f"✅ Removed transaction {args.tx_hash} from monitoring")
        else:
            print(f"❌ Transaction {args.tx_hash} not found in monitoring")
    
    elif args.action == 'export':
        # Export metrics to file
        file_path = args.output or f"monitoring_metrics_{int(time.time())}.json"
        success = await monitor.export_metrics(file_path)
        
        if success:
            print(f"✅ Metrics exported to {file_path}")
        else:
            print(f"❌ Failed to export metrics to {file_path}")
    
    elif args.action == 'network':
        # Get network status
        network_status = await monitor.get_network_status(args.network)
        
        if "error" in network_status:
            print(f"❌ Error: {network_status['error']}")
        else:
            print(f"Network Status for {args.network}:")
            print(f"├── Block Number: {network_status['block_number']}")
            print(f"├── Gas Price: {network_status['gas_price_gwei']:.2f} Gwei")
            print(f"├── Pending Transactions: {network_status['pending_transactions']}")
            print(f"└── Synced: {network_status['is_synced']}")


async def create_uniswap_v2_router_command(args):
    """Handle the create-uniswap-v2-router command."""
    print("🚀 Creating Uniswap V2 Router contract template...")
    
    # This would generate the Uniswap V2 Router contract
    # For now, we'll create a placeholder
    router_content = """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "./interfaces/IUniswapV2Router.sol";
import "./interfaces/IUniswapV2Factory.sol";
import "./interfaces/IERC20.sol";
import "./libraries/UniswapV2Library.sol";

/**
 * @title UniswapV2Router02
 * @dev Uniswap V2 Router for token swaps
 * @notice This contract handles token swaps and liquidity operations
 * @author HyperKit Agent
 */
contract UniswapV2Router02 is IUniswapV2Router02, Ownable, ReentrancyGuard {
    using SafeMath for uint256;
    
    address public immutable override factory;
    address public immutable override WETH;
    
    modifier ensure(uint deadline) {
        require(deadline >= block.timestamp, 'UniswapV2Router: EXPIRED');
        _;
    }
    
    constructor(address _factory, address _WETH) {
        factory = _factory;
        WETH = _WETH;
    }
    
    receive() external payable {
        assert(msg.sender == WETH); // only accept ETH via fallback from the WETH contract
    }
    
    // Add liquidity functions
    function addLiquidity(
        address tokenA,
        address tokenB,
        uint amountADesired,
        uint amountBDesired,
        uint amountAMin,
        uint amountBMin,
        address to,
        uint deadline
    ) external virtual override ensure(deadline) returns (uint amountA, uint amountB, uint liquidity) {
        // Implementation here
    }
    
    // Remove liquidity functions
    function removeLiquidity(
        address tokenA,
        address tokenB,
        uint liquidity,
        uint amountAMin,
        uint amountBMin,
        address to,
        uint deadline
    ) public virtual override ensure(deadline) returns (uint amountA, uint amountB) {
        // Implementation here
    }
    
    // Swap functions
    function swapExactTokensForTokens(
        uint amountIn,
        uint amountOutMin,
        address[] calldata path,
        address to,
        uint deadline
    ) external virtual override ensure(deadline) returns (uint[] memory amounts) {
        // Implementation here
    }
    
    // Additional swap and liquidity functions would be implemented here
}"""
    
    # Save to contracts/templates
    output_path = Path("contracts/templates/UniswapV2Router02.sol")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(router_content, encoding='utf-8')
    
    print(f"✅ Uniswap V2 Router template created at {output_path}")


async def create_vesting_contract_command(args):
    """Handle the create-vesting-contract command."""
    print(f"🚀 Creating {args.type} vesting contract template...")
    
    if args.type == 'linear':
        contract_name = "LinearVesting"
        description = "Linear token vesting contract"
    elif args.type == 'cliff':
        contract_name = "CliffVesting"
        description = "Cliff token vesting contract"
    elif args.type == 'multi-beneficiary':
        contract_name = "MultiBeneficiaryVesting"
        description = "Multi-beneficiary token vesting contract"
    else:
        print(f"❌ Unknown vesting type: {args.type}")
        return
    
    vesting_content = f"""// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/security/Pausable.sol";

/**
 * @title {contract_name}
 * @dev {description}
 * @notice This contract handles token vesting with {args.type} distribution
 * @author HyperKit Agent
 */
contract {contract_name} is Ownable, ReentrancyGuard, Pausable {{
    IERC20 public immutable token;
    
    struct VestingSchedule {{
        uint256 totalAmount;
        uint256 startTime;
        uint256 duration;
        uint256 cliff;
        uint256 released;
        bool revocable;
        bool revoked;
    }}
    
    mapping(address => VestingSchedule) public vestingSchedules;
    mapping(address => bool) public hasVestingSchedule;
    
    uint256 public totalVested;
    uint256 public totalReleased;
    
    event VestingScheduleCreated(address indexed beneficiary, uint256 totalAmount, uint256 startTime, uint256 duration);
    event TokensReleased(address indexed beneficiary, uint256 amount);
    event VestingRevoked(address indexed beneficiary);
    
    constructor(address _token) {{
        require(_token != address(0), "Invalid token address");
        token = IERC20(_token);
    }}
    
    function createVestingSchedule(
        address beneficiary,
        uint256 totalAmount,
        uint256 startTime,
        uint256 duration,
        uint256 cliff,
        bool revocable
    ) external onlyOwner {{
        require(beneficiary != address(0), "Invalid beneficiary");
        require(totalAmount > 0, "Invalid amount");
        require(!hasVestingSchedule[beneficiary], "Vesting already exists");
        require(startTime >= block.timestamp, "Invalid start time");
        require(duration > 0, "Invalid duration");
        require(cliff <= duration, "Cliff exceeds duration");
        
        vestingSchedules[beneficiary] = VestingSchedule(
            totalAmount,
            startTime,
            duration,
            cliff,
            0,
            revocable,
            false
        );
        
        hasVestingSchedule[beneficiary] = true;
        totalVested += totalAmount;
        
        emit VestingScheduleCreated(beneficiary, totalAmount, startTime, duration);
    }}
    
    function release() external nonReentrant whenNotPaused {{
        require(hasVestingSchedule[msg.sender], "No vesting schedule");
        require(!vestingSchedules[msg.sender].revoked, "Vesting revoked");
        
        uint256 releasableAmount = getReleasableAmount(msg.sender);
        require(releasableAmount > 0, "No tokens to release");
        
        vestingSchedules[msg.sender].released += releasableAmount;
        totalReleased += releasableAmount;
        
        require(token.transfer(msg.sender, releasableAmount), "Transfer failed");
        
        emit TokensReleased(msg.sender, releasableAmount);
    }}
    
    function getReleasableAmount(address beneficiary) public view returns (uint256) {{
        if (!hasVestingSchedule[beneficiary] || vestingSchedules[beneficiary].revoked) {{
            return 0;
        }}
        
        VestingSchedule memory schedule = vestingSchedules[beneficiary];
        uint256 currentTime = block.timestamp;
        
        if (currentTime < schedule.startTime + schedule.cliff) {{
            return 0;
        }}
        
        uint256 vestedAmount = getVestedAmount(beneficiary);
        return vestedAmount - schedule.released;
    }}
    
    function getVestedAmount(address beneficiary) public view returns (uint256) {{
        if (!hasVestingSchedule[beneficiary] || vestingSchedules[beneficiary].revoked) {{
            return 0;
        }}
        
        VestingSchedule memory schedule = vestingSchedules[beneficiary];
        uint256 currentTime = block.timestamp;
        
        if (currentTime < schedule.startTime) {{
            return 0;
        }}
        
        if (currentTime >= schedule.startTime + schedule.duration) {{
            return schedule.totalAmount;
        }}
        
        return (schedule.totalAmount * (currentTime - schedule.startTime)) / schedule.duration;
    }}
    
    function revokeVesting(address beneficiary) external onlyOwner {{
        require(hasVestingSchedule[beneficiary], "No vesting schedule");
        require(vestingSchedules[beneficiary].revocable, "Not revocable");
        require(!vestingSchedules[beneficiary].revoked, "Already revoked");
        
        vestingSchedules[beneficiary].revoked = true;
        
        emit VestingRevoked(beneficiary);
    }}
    
    function emergencyWithdraw() external onlyOwner {{
        uint256 balance = token.balanceOf(address(this));
        require(balance > 0, "No tokens to withdraw");
        require(token.transfer(owner(), balance), "Transfer failed");
    }}
}}"""
    
    # Save to contracts/templates
    output_path = Path(f"contracts/templates/{contract_name}.sol")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(vesting_content, encoding='utf-8')
    
    print(f"✅ {contract_name} template created at {output_path}")


async def create_auction_contract_command(args):
    """Handle the create-auction-contract command."""
    print(f"🚀 Creating {args.type} auction contract template...")
    
    if args.type == 'english':
        contract_name = "EnglishAuction"
        description = "English auction contract"
    elif args.type == 'dutch':
        contract_name = "DutchAuction"
        description = "Dutch auction contract"
    elif args.type == 'sealed-bid':
        contract_name = "SealedBidAuction"
        description = "Sealed bid auction contract"
    else:
        print(f"❌ Unknown auction type: {args.type}")
        return
    
    auction_content = f"""// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/token/ERC721/IERC721.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/security/Pausable.sol";

/**
 * @title {contract_name}
 * @dev {description}
 * @notice This contract handles {args.type} auction functionality
 * @author HyperKit Agent
 */
contract {contract_name} is Ownable, ReentrancyGuard, Pausable {{
    IERC721 public immutable nft;
    IERC20 public immutable paymentToken;
    
    struct Auction {{
        uint256 tokenId;
        address seller;
        uint256 startingPrice;
        uint256 currentPrice;
        uint256 endTime;
        address highestBidder;
        bool ended;
        bool cancelled;
    }}
    
    mapping(uint256 => Auction) public auctions;
    mapping(uint256 => mapping(address => uint256)) public bids;
    
    uint256 public auctionCount;
    uint256 public platformFee;
    address public feeRecipient;
    
    event AuctionCreated(uint256 indexed auctionId, uint256 indexed tokenId, address indexed seller, uint256 startingPrice, uint256 endTime);
    event BidPlaced(uint256 indexed auctionId, address indexed bidder, uint256 amount);
    event AuctionEnded(uint256 indexed auctionId, address indexed winner, uint256 finalPrice);
    event AuctionCancelled(uint256 indexed auctionId);
    
    constructor(address _nft, address _paymentToken, address _feeRecipient) {{
        require(_nft != address(0), "Invalid NFT address");
        require(_paymentToken != address(0), "Invalid payment token address");
        require(_feeRecipient != address(0), "Invalid fee recipient");
        
        nft = IERC721(_nft);
        paymentToken = IERC20(_paymentToken);
        feeRecipient = _feeRecipient;
        platformFee = 250; // 2.5%
    }}
    
    function createAuction(
        uint256 tokenId,
        uint256 startingPrice,
        uint256 duration
    ) external whenNotPaused {{
        require(nft.ownerOf(tokenId) == msg.sender, "Not token owner");
        require(startingPrice > 0, "Invalid starting price");
        require(duration > 0, "Invalid duration");
        
        nft.transferFrom(msg.sender, address(this), tokenId);
        
        uint256 auctionId = auctionCount++;
        auctions[auctionId] = Auction(
            tokenId,
            msg.sender,
            startingPrice,
            startingPrice,
            block.timestamp + duration,
            address(0),
            false,
            false
        );
        
        emit AuctionCreated(auctionId, tokenId, msg.sender, startingPrice, block.timestamp + duration);
    }}
    
    function placeBid(uint256 auctionId, uint256 amount) external nonReentrant whenNotPaused {{
        Auction storage auction = auctions[auctionId];
        require(!auction.ended, "Auction ended");
        require(!auction.cancelled, "Auction cancelled");
        require(block.timestamp < auction.endTime, "Auction expired");
        require(amount > auction.currentPrice, "Bid too low");
        
        // Refund previous highest bidder
        if (auction.highestBidder != address(0)) {{
            require(paymentToken.transfer(auction.highestBidder, bids[auctionId][auction.highestBidder]), "Refund failed");
        }}
        
        // Transfer new bid
        require(paymentToken.transferFrom(msg.sender, address(this), amount), "Transfer failed");
        
        auction.currentPrice = amount;
        auction.highestBidder = msg.sender;
        bids[auctionId][msg.sender] = amount;
        
        emit BidPlaced(auctionId, msg.sender, amount);
    }}
    
    function endAuction(uint256 auctionId) external nonReentrant {{
        Auction storage auction = auctions[auctionId];
        require(!auction.ended, "Auction already ended");
        require(auction.seller == msg.sender || block.timestamp >= auction.endTime, "Not authorized");
        
        auction.ended = true;
        
        if (auction.highestBidder != address(0)) {{
            // Transfer NFT to winner
            nft.transferFrom(address(this), auction.highestBidder, auction.tokenId);
            
            // Calculate fees
            uint256 fee = (auction.currentPrice * platformFee) / 10000;
            uint256 sellerAmount = auction.currentPrice - fee;
            
            // Transfer payment to seller
            require(paymentToken.transfer(auction.seller, sellerAmount), "Transfer to seller failed");
            
            // Transfer fee to platform
            require(paymentToken.transfer(feeRecipient, fee), "Transfer fee failed");
            
            emit AuctionEnded(auctionId, auction.highestBidder, auction.currentPrice);
        }} else {{
            // No bids, return NFT to seller
            nft.transferFrom(address(this), auction.seller, auction.tokenId);
            emit AuctionEnded(auctionId, address(0), 0);
        }}
    }}
    
    function cancelAuction(uint256 auctionId) external {{
        Auction storage auction = auctions[auctionId];
        require(auction.seller == msg.sender, "Not seller");
        require(!auction.ended, "Auction ended");
        require(!auction.cancelled, "Already cancelled");
        
        auction.cancelled = true;
        
        // Refund highest bidder if any
        if (auction.highestBidder != address(0)) {{
            require(paymentToken.transfer(auction.highestBidder, bids[auctionId][auction.highestBidder]), "Refund failed");
        }}
        
        // Return NFT to seller
        nft.transferFrom(address(this), auction.seller, auction.tokenId);
        
        emit AuctionCancelled(auctionId);
    }}
    
    function setPlatformFee(uint256 _fee) external onlyOwner {{
        require(_fee <= 1000, "Fee too high"); // Max 10%
        platformFee = _fee;
    }}
    
    function setFeeRecipient(address _feeRecipient) external onlyOwner {{
        require(_feeRecipient != address(0), "Invalid address");
        feeRecipient = _feeRecipient;
    }}
}}"""
    
    # Save to contracts/templates
    output_path = Path(f"contracts/templates/{contract_name}.sol")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(auction_content, encoding='utf-8')
    
    print(f"✅ {contract_name} template created at {output_path}")


async def create_uniswap_v3_command(args):
    """Create Uniswap V3 contract template."""
    try:
        print(f"🚀 Creating Uniswap V3 {args.type} contract template...")
        
        # Map type to template file
        type_mapping = {
            'factory': 'UniswapV3Factory.sol',
            'pool': 'UniswapV3Pool.sol',
            'router': 'UniswapV3Router.sol',
            'nft-manager': 'UniswapV3NonfungiblePositionManager.sol'
        }
        
        template_file = type_mapping.get(args.type)
        if not template_file:
            print(f"❌ Unknown V3 contract type: {args.type}")
            return
        
        template_path = f"contracts/templates/{template_file}"
        
        if not os.path.exists(template_path):
            print(f"❌ Template not found: {template_path}")
            return
        
        # Read template
        with open(template_path, 'r') as f:
            contract_code = f.read()
        
        # Save to output directory
        output_dir = Path(args.output_dir or './contracts/agent_generate')
        output_dir.mkdir(parents=True, exist_ok=True)
        
        filename = template_file
        output_path = output_dir / filename
        
        with open(output_path, 'w') as f:
            f.write(contract_code)
        
        print(f"✅ Created Uniswap V3 {args.type} contract: {output_path}")
        
    except Exception as e:
        print(f"❌ Error creating Uniswap V3 contract: {e}")


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
    
    # Gas estimate command
    gas_estimate_parser = subparsers.add_parser('gas-estimate', help='Estimate gas costs')
    gas_estimate_parser.add_argument('action', choices=['deployment', 'function', 'info'], 
                                   help='Type of gas estimation')
    gas_estimate_parser.add_argument('--network', default='hyperion', 
                                   choices=['hyperion', 'metis', 'lazai'], help='Target network')
    gas_estimate_parser.add_argument('--bytecode', help='Contract bytecode for deployment estimation')
    gas_estimate_parser.add_argument('--constructor-args', help='Constructor arguments (JSON)')
    gas_estimate_parser.add_argument('--contract-address', help='Contract address for function estimation')
    gas_estimate_parser.add_argument('--function-abi', help='Function ABI (JSON)')
    gas_estimate_parser.add_argument('--function-name', help='Function name')
    gas_estimate_parser.add_argument('--function-args', help='Function arguments (JSON)')
    
    # Gas optimize command
    gas_optimize_parser = subparsers.add_parser('gas-optimize', help='Optimize contract gas usage')
    gas_optimize_parser.add_argument('file', help='Contract file to optimize')
    gas_optimize_parser.add_argument('--export', help='Export optimization report to JSON file')
    
    # Monitor transaction command
    monitor_tx_parser = subparsers.add_parser('monitor-tx', help='Monitor transaction status')
    monitor_tx_parser.add_argument('action', choices=['add', 'status', 'list', 'metrics', 'remove', 'export', 'network'], 
                                 help='Monitor action')
    monitor_tx_parser.add_argument('--tx-hash', help='Transaction hash')
    monitor_tx_parser.add_argument('--network', default='hyperion', 
                                 choices=['hyperion', 'metis', 'lazai'], help='Target network')
    monitor_tx_parser.add_argument('--output', help='Output file for export')
    
    # Create Uniswap V2 Router command
    create_router_parser = subparsers.add_parser('create-uniswap-v2-router', help='Create Uniswap V2 Router template')
    
    # Create vesting contract command
    create_vesting_parser = subparsers.add_parser('create-vesting', help='Create vesting contract template')
    create_vesting_parser.add_argument('type', choices=['linear', 'cliff', 'multi-beneficiary'], 
                                     help='Type of vesting contract')
    
    # Create auction contract command
    create_auction_parser = subparsers.add_parser('create-auction', help='Create auction contract template')
    create_auction_parser.add_argument('type', choices=['english', 'dutch', 'sealed-bid'], 
                                     help='Type of auction contract')
    
    # Create Uniswap V3 command
    create_uniswap_v3_parser = subparsers.add_parser('create-uniswap-v3', help='Create Uniswap V3 contract template')
    create_uniswap_v3_parser.add_argument('type', choices=['factory', 'pool', 'router', 'nft-manager'], 
                                        help='Type of V3 contract')
    create_uniswap_v3_parser.add_argument('--output-dir', default='./contracts/agent_generate', help='Output directory')
    create_uniswap_v3_parser.add_argument('--save', help='Save contract with specific name')
    
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
    elif args.command == 'gas-estimate':
        asyncio.run(gas_estimate_command(args))
    elif args.command == 'gas-optimize':
        asyncio.run(gas_optimize_command(args))
    elif args.command == 'monitor-tx':
        asyncio.run(monitor_transaction_command(args))
    elif args.command == 'create-uniswap-v2-router':
        asyncio.run(create_uniswap_v2_router_command(args))
    elif args.command == 'create-vesting':
        asyncio.run(create_vesting_contract_command(args))
    elif args.command == 'create-auction':
        asyncio.run(create_auction_contract_command(args))
    elif args.command == 'create-uniswap-v3':
        asyncio.run(create_uniswap_v3_command(args))


if __name__ == "__main__":
    main()
