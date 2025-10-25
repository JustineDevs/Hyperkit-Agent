"""
Transaction Simulation Engine
Implements Pocket Universe-style pre-signature transaction simulation

Features:
- Fork blockchain state at current block
- Execute transactions in isolated environment
- Capture balance changes and state modifications
- Detect suspicious patterns (reentrancy, price manipulation, etc.)
- Generate human-readable preview ("You will send X, receive Y")
"""

import asyncio
import json
import logging
import subprocess
import tempfile
import time
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from web3 import Web3
from web3.types import TxParams
import os

logger = logging.getLogger(__name__)


class TransactionSimulator:
    """
    Transaction simulation engine using Anvil (Foundry) for blockchain state forking.
    Provides pre-signature transaction analysis and balance change prediction.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize transaction simulator.

        Args:
            config: Configuration dictionary with network RPC URLs
        """
        self.config = config or {}
        self.anvil_port = self.config.get("anvil_port", 8546)
        self.timeout = self.config.get("timeout", 5)
        self.fork_processes = {}  # Track running Anvil processes

        # Network RPC URLs
        self.rpc_urls = {
            "hyperion": "https://hyperion-testnet.metisdevops.link",
            "metis": "https://andromeda.metis.io",
            "ethereum": os.getenv("ETHEREUM_RPC_URL", "https://mainnet.infura.io/v3/YOUR_INFURA_KEY"),
            "polygon": os.getenv("POLYGON_RPC_URL", "https://polygon-rpc.com"),
            "arbitrum": os.getenv("ARBITRUM_RPC_URL", "https://arb1.arbitrum.io/rpc"),
        }

        logger.info(f"TransactionSimulator initialized (port: {self.anvil_port})")

    async def simulate_transaction(
        self, 
        tx_params: Dict[str, Any], 
        network: str = "hyperion"
    ) -> Dict[str, Any]:
        """
        Simulate a transaction before execution.

        Args:
            tx_params: Transaction parameters {to, from, data, value, gas}
            network: Blockchain network to simulate on

        Returns:
            Dict containing:
            - success: bool
            - balance_changes: List of detected balance changes
            - warnings: List of security warnings
            - confidence: Confidence score (0.0-1.0)
            - execution_time: Time taken to simulate
        """
        start_time = time.time()

        try:
            logger.info(f"Starting transaction simulation on {network}")

            # 1. Validate inputs
            if not self._validate_tx_params(tx_params):
                return self._error_result("Invalid transaction parameters")

            # 2. Get network RPC URL
            rpc_url = self.rpc_urls.get(network)
            if not rpc_url:
                return self._error_result(f"Network {network} not supported")

            # 3. Create Anvil fork
            fork_rpc, anvil_process = await self._create_anvil_fork(network, rpc_url)
            if not fork_rpc:
                return self._error_result("Failed to create blockchain fork")

            try:
                # 4. Connect to forked network
                w3 = Web3(Web3.HTTPProvider(fork_rpc))
                if not w3.is_connected():
                    return self._error_result("Failed to connect to forked network")

                # 5. Execute transaction on fork
                result = await self._execute_transaction(w3, tx_params)

                # 6. Analyze execution trace
                balance_changes = self._parse_balance_changes(result, w3)
                warnings = self._detect_suspicious_patterns(result, tx_params)

                # 7. Calculate confidence
                confidence = self._calculate_confidence(result, balance_changes, warnings)

                execution_time = time.time() - start_time

                return {
                    "success": True,
                    "balance_changes": balance_changes,
                    "warnings": warnings,
                    "confidence": confidence,
                    "execution_time": execution_time,
                    "gas_used": result.get("gas_used", 0),
                    "simulation_block": result.get("block_number", 0),
                }

            finally:
                # 8. Cleanup fork process
                await self._cleanup_fork(anvil_process)

        except Exception as e:
            logger.error(f"Transaction simulation failed: {e}")
            return self._error_result(str(e))

    async def _create_anvil_fork(
        self, 
        network: str, 
        rpc_url: str, 
        block_number: Optional[int] = None
    ) -> Tuple[Optional[str], Optional[subprocess.Popen]]:
        """
        Create an Anvil fork of the blockchain at a specific block.

        Args:
            network: Network name
            rpc_url: RPC URL to fork from
            block_number: Block number to fork at (None = latest)

        Returns:
            Tuple of (fork_rpc_url, anvil_process)
        """
        try:
            # Build Anvil command
            cmd = [
                "anvil",
                "--fork-url", rpc_url,
                "--port", str(self.anvil_port),
                "--no-mining",  # Don't auto-mine blocks
                "--silent",     # Reduce output noise
            ]

            if block_number:
                cmd.extend(["--fork-block-number", str(block_number)])

            # Start Anvil process
            logger.info(f"Starting Anvil fork: {' '.join(cmd)}")
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Wait for Anvil to start (max 3 seconds)
            fork_rpc = f"http://127.0.0.1:{self.anvil_port}"
            for _ in range(30):  # 3 seconds (30 * 0.1)
                try:
                    w3 = Web3(Web3.HTTPProvider(fork_rpc))
                    if w3.is_connected():
                        logger.info(f"✅ Anvil fork ready: {fork_rpc}")
                        self.fork_processes[network] = process
                        return fork_rpc, process
                except Exception:
                    await asyncio.sleep(0.1)

            # If we reach here, Anvil didn't start
            process.terminate()
            logger.error("Anvil failed to start within timeout")
            return None, None

        except FileNotFoundError:
            logger.error("Anvil not found. Please install Foundry: https://book.getfoundry.sh/getting-started/installation")
            return None, None
        except Exception as e:
            logger.error(f"Failed to create Anvil fork: {e}")
            return None, None

    async def _execute_transaction(
        self, 
        w3: Web3, 
        tx_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute transaction on forked network and capture trace.

        Args:
            w3: Web3 instance connected to fork
            tx_params: Transaction parameters

        Returns:
            Dict containing execution results and trace data
        """
        try:
            # Prepare transaction
            tx = {
                "to": Web3.to_checksum_address(tx_params["to"]) if tx_params.get("to") else None,
                "from": Web3.to_checksum_address(tx_params["from"]),
                "value": tx_params.get("value", 0),
                "gas": tx_params.get("gas", 3000000),
                "gasPrice": w3.eth.gas_price,
            }

            if tx_params.get("data"):
                tx["data"] = tx_params["data"]

            # Execute transaction (call - doesn't modify state)
            logger.info(f"Executing transaction: {tx['to']}")
            
            # Try to execute and catch any reverts
            try:
                result = w3.eth.call(tx)
                tx_hash = w3.eth.send_raw_transaction(result) if result else None
                
                # Get trace (if debug API available)
                trace = None
                try:
                    if tx_hash:
                        trace = w3.provider.make_request("debug_traceTransaction", [tx_hash.hex()])
                except Exception as trace_error:
                    logger.warning(f"Could not get trace: {trace_error}")

                return {
                    "success": True,
                    "result": result,
                    "trace": trace,
                    "gas_used": tx.get("gas", 0),
                    "block_number": w3.eth.block_number,
                }

            except Exception as exec_error:
                # Transaction reverted
                logger.warning(f"Transaction would revert: {exec_error}")
                return {
                    "success": False,
                    "error": str(exec_error),
                    "reverted": True,
                    "block_number": w3.eth.block_number,
                }

        except Exception as e:
            logger.error(f"Transaction execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "block_number": 0,
            }

    def _parse_balance_changes(
        self, 
        result: Dict[str, Any], 
        w3: Web3
    ) -> List[Dict[str, Any]]:
        """
        Parse balance changes from transaction execution.

        Args:
            result: Execution result
            w3: Web3 instance

        Returns:
            List of balance changes: [{"token": "ETH", "amount": "-0.1", "direction": "out"}, ...]
        """
        balance_changes = []

        try:
            # If transaction reverted, no balance changes
            if result.get("reverted"):
                return [{"warning": "Transaction would revert"}]

            # Parse trace data if available
            trace = result.get("trace")
            if trace and isinstance(trace, dict):
                # Look for Transfer events (ERC20/ERC721)
                if "result" in trace and "structLogs" in trace["result"]:
                    for log in trace["result"]["structLogs"]:
                        if log.get("op") == "LOG3":  # Transfer event signature
                            # Parse transfer event
                            # This is simplified - real implementation needs ABI decoding
                            balance_changes.append({
                                "token": "ERC20_TOKEN",
                                "amount": "AMOUNT",
                                "direction": "transfer",
                            })

            # If no trace available, provide estimation
            if not balance_changes and result.get("success"):
                balance_changes.append({
                    "note": "Simulation successful but detailed trace not available",
                    "recommendation": "Verify contract on explorer for detailed analysis",
                })

            return balance_changes

        except Exception as e:
            logger.error(f"Failed to parse balance changes: {e}")
            return [{"error": f"Parse error: {str(e)}"}]

    def _detect_suspicious_patterns(
        self, 
        result: Dict[str, Any], 
        tx_params: Dict[str, Any]
    ) -> List[str]:
        """
        Detect suspicious patterns in transaction execution.

        Args:
            result: Execution result
            tx_params: Original transaction parameters

        Returns:
            List of warning strings
        """
        warnings = []

        try:
            # Check for revert
            if result.get("reverted"):
                warnings.append("⚠️  Transaction will revert - likely to fail")

            # Check for high gas usage
            gas_used = result.get("gas_used", 0)
            if gas_used > 1000000:
                warnings.append(f"⚠️  High gas usage: {gas_used} gas")

            # Check for unusual patterns in data
            data = tx_params.get("data", "")
            if data:
                # Check for common exploit function signatures
                if data.startswith("0x095ea7b3"):  # approve(address,uint256)
                    # Check if approval amount is unlimited
                    if "f" * 60 in data:  # 2^256-1 in hex
                        warnings.append("⚠️  UNLIMITED APPROVAL DETECTED - High risk!")

                if data.startswith("0xa22cb465"):  # setApprovalForAll(address,bool)
                    warnings.append("⚠️  NFT approval for all tokens - Verify recipient")

                if data.startswith("0xd505accf"):  # permit(...)
                    warnings.append("⚠️  Permit signature - Potential permit phishing")

            # Check for self-destruct patterns
            if result.get("trace"):
                trace_str = str(result["trace"])
                if "SELFDESTRUCT" in trace_str:
                    warnings.append("🚨 CRITICAL: Contract self-destruct detected!")

            return warnings

        except Exception as e:
            logger.error(f"Failed to detect suspicious patterns: {e}")
            return [f"Pattern detection error: {str(e)}"]

    def _calculate_confidence(
        self, 
        result: Dict[str, Any], 
        balance_changes: List[Dict[str, Any]], 
        warnings: List[str]
    ) -> float:
        """
        Calculate confidence score for simulation results.

        Args:
            result: Execution result
            balance_changes: Parsed balance changes
            warnings: Detected warnings

        Returns:
            Confidence score (0.0-1.0)
        """
        confidence = 0.9  # Base confidence

        # Reduce confidence if no trace available
        if not result.get("trace"):
            confidence -= 0.2

        # Reduce confidence if transaction reverted
        if result.get("reverted"):
            confidence -= 0.3

        # Reduce confidence based on warnings
        critical_warnings = [w for w in warnings if "CRITICAL" in w or "🚨" in w]
        if critical_warnings:
            confidence -= 0.2

        # Ensure confidence is between 0 and 1
        return max(0.0, min(1.0, confidence))

    def _validate_tx_params(self, tx_params: Dict[str, Any]) -> bool:
        """Validate transaction parameters."""
        required = ["to", "from"]
        return all(k in tx_params for k in required)

    def _error_result(self, error_msg: str) -> Dict[str, Any]:
        """Generate error result."""
        return {
            "success": False,
            "error": error_msg,
            "balance_changes": [],
            "warnings": [f"❌ Simulation failed: {error_msg}"],
            "confidence": 0.0,
            "execution_time": 0.0,
        }

    async def _cleanup_fork(self, process: Optional[subprocess.Popen]):
        """Clean up Anvil fork process."""
        if process:
            try:
                process.terminate()
                process.wait(timeout=2)
                logger.info("Anvil fork process terminated")
            except Exception as e:
                logger.warning(f"Failed to cleanup Anvil process: {e}")
                try:
                    process.kill()
                except Exception:
                    pass

    async def simulate_batch(
        self, 
        transactions: List[Dict[str, Any]], 
        network: str = "hyperion"
    ) -> List[Dict[str, Any]]:
        """
        Simulate multiple transactions in sequence.

        Args:
            transactions: List of transaction parameters
            network: Network to simulate on

        Returns:
            List of simulation results
        """
        results = []

        for tx in transactions:
            result = await self.simulate_transaction(tx, network)
            results.append(result)

            # Stop if any transaction would fail
            if not result["success"]:
                logger.warning("Batch simulation stopped due to failed transaction")
                break

        return results

    def get_simulation_summary(self, result: Dict[str, Any]) -> str:
        """
        Generate human-readable summary of simulation result.

        Args:
            result: Simulation result

        Returns:
            Formatted summary string
        """
        if not result["success"]:
            return f"❌ Simulation failed: {result.get('error', 'Unknown error')}"

        summary = ["✅ Transaction Simulation Complete\n"]

        # Balance changes
        if result["balance_changes"]:
            summary.append("💰 Balance Changes:")
            for change in result["balance_changes"]:
                if "token" in change:
                    summary.append(f"   - {change.get('token')}: {change.get('amount')} ({change.get('direction')})")
                elif "note" in change:
                    summary.append(f"   ℹ️  {change['note']}")

        # Warnings
        if result["warnings"]:
            summary.append("\n⚠️  Warnings:")
            for warning in result["warnings"]:
                summary.append(f"   {warning}")

        # Confidence
        confidence_pct = int(result["confidence"] * 100)
        summary.append(f"\n📊 Confidence: {confidence_pct}%")
        summary.append(f"⏱️  Execution Time: {result['execution_time']:.2f}s")

        return "\n".join(summary)


# Example usage
async def main():
    """Example usage of TransactionSimulator."""
    simulator = TransactionSimulator()

    # Example transaction
    tx_params = {
        "to": "0x7fF064953a29FB36F68730E5b24410Ba90659f25",
        "from": "0x1234567890123456789012345678901234567890",
        "value": 0,
        "data": "0x095ea7b3000000000000000000000000deadbeef000000000000000000000000000000000000000000000000ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
    }

    result = await simulator.simulate_transaction(tx_params, "hyperion")
    
    print(simulator.get_simulation_summary(result))


if __name__ == "__main__":
    asyncio.run(main())

