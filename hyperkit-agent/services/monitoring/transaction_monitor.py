"""
Transaction Monitoring Service
Monitors blockchain transactions and provides real-time status updates
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)


@dataclass
class TransactionStatus:
    """Transaction status information"""

    tx_hash: str
    status: str  # 'pending', 'confirmed', 'failed', 'dropped'
    block_number: Optional[int]
    gas_used: Optional[int]
    gas_price: Optional[int]
    from_address: str
    to_address: Optional[str]
    value: int
    timestamp: datetime
    confirmations: int
    error_message: Optional[str] = None


@dataclass
class MonitoringConfig:
    """Configuration for transaction monitoring"""

    rpc_url: str
    confirmation_blocks: int = 12
    check_interval: int = 5  # seconds
    max_retries: int = 100
    timeout: int = 300  # seconds


class TransactionMonitor:
    """
    Monitors blockchain transactions and provides real-time updates
    """

    def __init__(self, config: MonitoringConfig):
        self.config = config
        self.monitored_transactions: Dict[str, TransactionStatus] = {}
        self.callbacks: Dict[str, List[Callable]] = {}
        self.is_monitoring = False
        self.monitor_task: Optional[asyncio.Task] = None

        logger.info("TransactionMonitor initialized")

    async def start_monitoring(self):
        """Start the monitoring loop"""
        if self.is_monitoring:
            logger.warning("Monitoring already started")
            return

        self.is_monitoring = True
        self.monitor_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Transaction monitoring started")

    async def stop_monitoring(self):
        """Stop the monitoring loop"""
        self.is_monitoring = False
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("Transaction monitoring stopped")

    async def monitor_transaction(
        self, tx_hash: str, callbacks: Optional[List[Callable]] = None
    ) -> TransactionStatus:
        """
        Start monitoring a transaction

        Args:
            tx_hash: Transaction hash to monitor
            callbacks: List of callback functions to call on status updates

        Returns:
            Initial transaction status
        """
        try:
            from web3 import Web3

            w3 = Web3(Web3.HTTPProvider(self.config.rpc_url))

            # Get initial transaction data
            tx_data = w3.eth.get_transaction(tx_hash)
            receipt = w3.eth.get_transaction_receipt(tx_hash)

            # Determine initial status
            if receipt.status == 1:
                status = "confirmed"
                block_number = receipt.blockNumber
                gas_used = receipt.gasUsed
            else:
                status = "failed"
                block_number = receipt.blockNumber
                gas_used = receipt.gasUsed

            # Create transaction status
            tx_status = TransactionStatus(
                tx_hash=tx_hash,
                status=status,
                block_number=block_number,
                gas_used=gas_used,
                gas_price=tx_data.gasPrice,
                from_address=tx_data["from"],
                to_address=tx_data.to,
                value=tx_data.value,
                timestamp=datetime.now(),
                confirmations=0,
            )

            # Store transaction status
            self.monitored_transactions[tx_hash] = tx_status

            # Register callbacks
            if callbacks:
                self.callbacks[tx_hash] = callbacks

            logger.info(f"Started monitoring transaction: {tx_hash}")
            return tx_status

        except Exception as e:
            logger.error(f"Failed to start monitoring transaction {tx_hash}: {e}")
            raise

    async def get_transaction_status(self, tx_hash: str) -> Optional[TransactionStatus]:
        """
        Get current status of a monitored transaction

        Args:
            tx_hash: Transaction hash

        Returns:
            Transaction status or None if not found
        """
        return self.monitored_transactions.get(tx_hash)

    async def stop_monitoring_transaction(self, tx_hash: str):
        """
        Stop monitoring a specific transaction

        Args:
            tx_hash: Transaction hash to stop monitoring
        """
        if tx_hash in self.monitored_transactions:
            del self.monitored_transactions[tx_hash]
            if tx_hash in self.callbacks:
                del self.callbacks[tx_hash]
            logger.info(f"Stopped monitoring transaction: {tx_hash}")

    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.is_monitoring:
            try:
                await self._check_all_transactions()
                await asyncio.sleep(self.config.check_interval)
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(self.config.check_interval)

    async def _check_all_transactions(self):
        """Check status of all monitored transactions"""
        if not self.monitored_transactions:
            return

        try:
            from web3 import Web3

            w3 = Web3(Web3.HTTPProvider(self.config.rpc_url))
            current_block = w3.eth.block_number

            for tx_hash, tx_status in list(self.monitored_transactions.items()):
                try:
                    await self._check_transaction_status(
                        tx_hash, tx_status, w3, current_block
                    )
                except Exception as e:
                    logger.error(f"Error checking transaction {tx_hash}: {e}")

        except Exception as e:
            logger.error(f"Error in _check_all_transactions: {e}")

    async def _check_transaction_status(
        self, tx_hash: str, tx_status: TransactionStatus, w3, current_block: int
    ):
        """Check status of a specific transaction"""
        try:
            # Get transaction receipt
            receipt = w3.eth.get_transaction_receipt(tx_hash)

            # Update confirmations
            if tx_status.block_number:
                confirmations = current_block - tx_status.block_number + 1
                tx_status.confirmations = confirmations

                # Check if transaction is confirmed
                if confirmations >= self.config.confirmation_blocks:
                    if tx_status.status != "confirmed":
                        tx_status.status = "confirmed"
                        await self._notify_callbacks(tx_hash, tx_status)
                        logger.info(
                            f"Transaction {tx_hash} confirmed with {confirmations} confirmations"
                        )

                # Check if transaction failed
                if receipt.status == 0:
                    if tx_status.status != "failed":
                        tx_status.status = "failed"
                        tx_status.error_message = "Transaction failed"
                        await self._notify_callbacks(tx_hash, tx_status)
                        logger.warning(f"Transaction {tx_hash} failed")

        except Exception as e:
            # Transaction might not be mined yet
            if "not found" in str(e).lower():
                # Check if transaction has been pending too long
                if (datetime.now() - tx_status.timestamp).seconds > self.config.timeout:
                    tx_status.status = "dropped"
                    tx_status.error_message = "Transaction dropped (timeout)"
                    await self._notify_callbacks(tx_hash, tx_status)
                    logger.warning(f"Transaction {tx_hash} dropped due to timeout")
            else:
                logger.error(f"Error checking transaction {tx_hash}: {e}")

    async def _notify_callbacks(self, tx_hash: str, tx_status: TransactionStatus):
        """Notify registered callbacks of status update"""
        if tx_hash in self.callbacks:
            for callback in self.callbacks[tx_hash]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(tx_hash, tx_status)
                    else:
                        callback(tx_hash, tx_status)
                except Exception as e:
                    logger.error(f"Error in callback for transaction {tx_hash}: {e}")

    def register_callback(self, tx_hash: str, callback: Callable):
        """
        Register a callback for a specific transaction

        Args:
            tx_hash: Transaction hash
            callback: Callback function
        """
        if tx_hash not in self.callbacks:
            self.callbacks[tx_hash] = []
        self.callbacks[tx_hash].append(callback)

    async def get_monitoring_summary(self) -> Dict[str, Any]:
        """
        Get summary of all monitored transactions

        Returns:
            Summary dictionary
        """
        total_transactions = len(self.monitored_transactions)
        confirmed = len(
            [
                tx
                for tx in self.monitored_transactions.values()
                if tx.status == "confirmed"
            ]
        )
        pending = len(
            [
                tx
                for tx in self.monitored_transactions.values()
                if tx.status == "pending"
            ]
        )
        failed = len(
            [tx for tx in self.monitored_transactions.values() if tx.status == "failed"]
        )
        dropped = len(
            [
                tx
                for tx in self.monitored_transactions.values()
                if tx.status == "dropped"
            ]
        )

        return {
            "total_transactions": total_transactions,
            "confirmed": confirmed,
            "pending": pending,
            "failed": failed,
            "dropped": dropped,
            "is_monitoring": self.is_monitoring,
            "monitored_hashes": list(self.monitored_transactions.keys()),
        }

    async def wait_for_confirmation(
        self, tx_hash: str, timeout: Optional[int] = None
    ) -> TransactionStatus:
        """
        Wait for a transaction to be confirmed

        Args:
            tx_hash: Transaction hash
            timeout: Timeout in seconds (None for no timeout)

        Returns:
            Final transaction status
        """
        if tx_hash not in self.monitored_transactions:
            await self.monitor_transaction(tx_hash)

        start_time = datetime.now()
        timeout_seconds = timeout or self.config.timeout

        while True:
            tx_status = self.monitored_transactions.get(tx_hash)
            if not tx_status:
                raise ValueError(f"Transaction {tx_hash} not found")

            if tx_status.status in ["confirmed", "failed", "dropped"]:
                return tx_status

            if (datetime.now() - start_time).seconds > timeout_seconds:
                tx_status.status = "dropped"
                tx_status.error_message = "Timeout waiting for confirmation"
                return tx_status

            await asyncio.sleep(self.config.check_interval)

    async def get_transaction_history(
        self, address: str, from_block: int = 0, to_block: str = "latest"
    ) -> List[Dict[str, Any]]:
        """
        Get transaction history for an address

        Args:
            address: Address to get history for
            from_block: Starting block number
            to_block: Ending block number or 'latest'

        Returns:
            List of transaction data
        """
        try:
            from web3 import Web3

            w3 = Web3(Web3.HTTPProvider(self.config.rpc_url))

            # Get transaction count
            tx_count = w3.eth.get_transaction_count(address)

            transactions = []

            # Get recent transactions (simplified approach)
            for i in range(max(0, tx_count - 10), tx_count):
                try:
                    tx = w3.eth.get_transaction_by_index(address, i)
                    if tx:
                        transactions.append(
                            {
                                "hash": tx.hash.hex(),
                                "from": tx["from"],
                                "to": tx.to,
                                "value": tx.value,
                                "gas": tx.gas,
                                "gas_price": tx.gasPrice,
                                "block_number": tx.blockNumber,
                                "transaction_index": tx.transactionIndex,
                            }
                        )
                except Exception as e:
                    logger.debug(
                        f"Error getting transaction {i} for address {address}: {e}"
                    )
                    continue

            return transactions

        except Exception as e:
            logger.error(f"Error getting transaction history for {address}: {e}")
            return []

    async def estimate_gas_price(self) -> Dict[str, int]:
        """
        Estimate current gas price

        Returns:
            Dictionary with gas price estimates
        """
        try:
            from web3 import Web3

            w3 = Web3(Web3.HTTPProvider(self.config.rpc_url))

            # Get current gas price
            current_gas_price = w3.eth.gas_price

            # Estimate gas price for different priority levels
            return {
                "slow": int(current_gas_price * 0.8),
                "standard": current_gas_price,
                "fast": int(current_gas_price * 1.2),
                "instant": int(current_gas_price * 1.5),
            }

        except Exception as e:
            logger.error(f"Error estimating gas price: {e}")
            return {
                "slow": 20000000000,  # 20 gwei
                "standard": 25000000000,  # 25 gwei
                "fast": 30000000000,  # 30 gwei
                "instant": 40000000000,  # 40 gwei
            }
