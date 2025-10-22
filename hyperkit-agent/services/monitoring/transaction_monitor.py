#!/usr/bin/env python3
"""
Transaction Monitoring Service
Provides comprehensive transaction monitoring and status tracking.
Follows .cursor/rules for production-ready implementation.
"""

import asyncio
import json
import logging
import time
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
import aiohttp
from web3 import Web3
from web3.exceptions import TransactionNotFound, BlockNotFound

logger = logging.getLogger(__name__)

@dataclass
class MonitoringConfig:
    """Configuration for transaction monitoring."""
    rpc_url: str = "https://hyperion-testnet.metisdevops.link"
    confirmation_blocks: int = 12
    check_interval: int = 5  # seconds
    enabled: bool = True
    max_retries: int = 3
    timeout: int = 10  # seconds
    networks: List[str] = None
    
    def __post_init__(self):
        if self.networks is None:
            self.networks = ["hyperion", "metis", "lazai"]

@dataclass
class TransactionStatus:
    """Represents transaction status information."""
    tx_hash: str
    status: str  # pending, confirmed, failed, dropped
    block_number: Optional[int] = None
    gas_used: Optional[int] = None
    gas_price: Optional[int] = None
    effective_gas_price: Optional[int] = None
    confirmation_count: int = 0
    timestamp: int = 0
    network: str = "unknown"
    error_message: Optional[str] = None
    receipt: Optional[Dict[str, Any]] = None

@dataclass
class MonitoringMetrics:
    """Represents monitoring metrics."""
    total_transactions: int = 0
    confirmed_transactions: int = 0
    failed_transactions: int = 0
    pending_transactions: int = 0
    average_gas_used: float = 0.0
    average_gas_price: float = 0.0
    success_rate: float = 0.0
    average_confirmation_time: float = 0.0

class TransactionMonitor:
    """Transaction monitoring service for smart contracts."""
    
    def __init__(self, config):
        """Initialize transaction monitor with configuration."""
        self.config = config
        
        # Handle both dict and MonitoringConfig objects
        if hasattr(config, 'networks'):
            self.networks = config.networks
            self.rpc_url = config.rpc_url
            self.confirmation_blocks = config.confirmation_blocks
            self.check_interval = config.check_interval
        else:
            self.networks = config.get("networks", {})
            self.rpc_url = config.get("rpc_url", "https://hyperion-testnet.metisdevops.link")
            self.confirmation_blocks = config.get("confirmation_blocks", 12)
            self.check_interval = config.get("check_interval", 5)
        
        self.web3_instances = {}
        self.monitored_transactions = {}
        self.metrics = MonitoringMetrics()
        self.callbacks = []
        self.running = False
        
        # Initialize Web3 instances
        self._initialize_web3_instances()
        
        # Additional monitoring configuration
        self.max_confirmations = self.confirmation_blocks
        self.timeout_duration = 300  # 5 minutes
        
    def _initialize_web3_instances(self):
        """Initialize Web3 instances for each supported network."""
        # Handle both list and dict formats
        if isinstance(self.networks, list):
            # If networks is a list, use the rpc_url from config
            if self.rpc_url:
                try:
                    self.web3_instances["hyperion"] = Web3(Web3.HTTPProvider(self.rpc_url))
                    logger.info(f"Initialized Web3 instance for hyperion")
                except Exception as e:
                    logger.error(f"Failed to initialize Web3 for hyperion: {e}")
        else:
            # If networks is a dict, iterate through it
            for network, network_config in self.networks.items():
                if network_config.get("enabled", False):
                    rpc_url = f"{network.upper()}_RPC_URL"
                    import os
                    rpc_url = os.getenv(rpc_url)
                    if rpc_url:
                        try:
                            self.web3_instances[network] = Web3(Web3.HTTPProvider(rpc_url))
                            logger.info(f"Initialized Web3 instance for {network}")
                        except Exception as e:
                            logger.error(f"Failed to initialize Web3 for {network}: {e}")
    
    async def start_monitoring(self):
        """Start the transaction monitoring service."""
        if self.running:
            logger.warning("Transaction monitoring is already running")
            return
        
        self.running = True
        logger.info("Starting transaction monitoring service")
        
        # Start monitoring loop
        asyncio.create_task(self._monitoring_loop())
    
    async def stop_monitoring(self):
        """Stop the transaction monitoring service."""
        self.running = False
        logger.info("Transaction monitoring service stopped")
    
    async def add_transaction(
        self, 
        tx_hash: str, 
        network: str = "hyperion",
        callback: Optional[Callable] = None
    ) -> bool:
        """
        Add a transaction to monitoring.
        
        Args:
            tx_hash: Transaction hash to monitor
            network: Network to monitor on
            callback: Optional callback function for status updates
            
        Returns:
            True if successfully added, False otherwise
        """
        if network not in self.web3_instances:
            logger.error(f"Network {network} not supported")
            return False
        
        if tx_hash in self.monitored_transactions:
            logger.warning(f"Transaction {tx_hash} is already being monitored")
            return True
        
        # Initialize transaction status
        tx_status = TransactionStatus(
            tx_hash=tx_hash,
            status="pending",
            network=network,
            timestamp=int(time.time())
        )
        
        self.monitored_transactions[tx_hash] = tx_status
        self.metrics.total_transactions += 1
        self.metrics.pending_transactions += 1
        
        if callback:
            self.callbacks.append(callback)
        
        logger.info(f"Added transaction {tx_hash} to monitoring on {network}")
        return True
    
    async def remove_transaction(self, tx_hash: str) -> bool:
        """Remove a transaction from monitoring."""
        if tx_hash in self.monitored_transactions:
            del self.monitored_transactions[tx_hash]
            logger.info(f"Removed transaction {tx_hash} from monitoring")
            return True
        return False
    
    async def get_transaction_status(self, tx_hash: str) -> Optional[TransactionStatus]:
        """Get current status of a monitored transaction."""
        return self.monitored_transactions.get(tx_hash)
    
    async def get_all_transactions(self) -> List[TransactionStatus]:
        """Get all monitored transactions."""
        return list(self.monitored_transactions.values())
    
    async def get_metrics(self) -> MonitoringMetrics:
        """Get current monitoring metrics."""
        return self.metrics
    
    async def _monitoring_loop(self):
        """Main monitoring loop."""
        while self.running:
            try:
                await self._check_all_transactions()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(self.check_interval)
    
    async def _check_all_transactions(self):
        """Check status of all monitored transactions."""
        for tx_hash, tx_status in list(self.monitored_transactions.items()):
            try:
                await self._check_transaction_status(tx_hash, tx_status)
            except Exception as e:
                logger.error(f"Error checking transaction {tx_hash}: {e}")
    
    async def _check_transaction_status(self, tx_hash: str, tx_status: TransactionStatus):
        """Check status of a specific transaction."""
        web3 = self.web3_instances[tx_status.network]
        
        try:
            # Get transaction receipt
            receipt = web3.eth.get_transaction_receipt(tx_hash)
            
            if receipt:
                # Transaction is confirmed
                tx_status.status = "confirmed"
                tx_status.block_number = receipt.blockNumber
                tx_status.gas_used = receipt.gasUsed
                tx_status.receipt = dict(receipt)
                
                # Calculate confirmations
                current_block = web3.eth.block_number
                tx_status.confirmation_count = current_block - receipt.blockNumber + 1
                
                # Update metrics
                self._update_metrics(tx_status)
                
                # Remove from monitoring if enough confirmations
                if tx_status.confirmation_count >= self.max_confirmations:
                    await self.remove_transaction(tx_hash)
                
                logger.info(f"Transaction {tx_hash} confirmed in block {receipt.blockNumber}")
                
            else:
                # Check if transaction exists in mempool
                try:
                    tx = web3.eth.get_transaction(tx_hash)
                    if tx:
                        tx_status.gas_price = tx.gasPrice
                        tx_status.status = "pending"
                    else:
                        tx_status.status = "dropped"
                        await self.remove_transaction(tx_hash)
                except TransactionNotFound:
                    tx_status.status = "dropped"
                    await self.remove_transaction(tx_hash)
        
        except Exception as e:
            logger.error(f"Error checking transaction {tx_hash}: {e}")
            tx_status.error_message = str(e)
    
    def _update_metrics(self, tx_status: TransactionStatus):
        """Update monitoring metrics based on transaction status."""
        if tx_status.status == "confirmed":
            self.metrics.confirmed_transactions += 1
            self.metrics.pending_transactions = max(0, self.metrics.pending_transactions - 1)
            
            if tx_status.gas_used:
                # Update average gas used
                total_gas = self.metrics.average_gas_used * (self.metrics.confirmed_transactions - 1)
                self.metrics.average_gas_used = (total_gas + tx_status.gas_used) / self.metrics.confirmed_transactions
            
            if tx_status.gas_price:
                # Update average gas price
                total_price = self.metrics.average_gas_price * (self.metrics.confirmed_transactions - 1)
                self.metrics.average_gas_price = (total_price + tx_status.gas_price) / self.metrics.confirmed_transactions
        
        elif tx_status.status == "failed":
            self.metrics.failed_transactions += 1
            self.metrics.pending_transactions = max(0, self.metrics.pending_transactions - 1)
        
        # Calculate success rate
        total_processed = self.metrics.confirmed_transactions + self.metrics.failed_transactions
        if total_processed > 0:
            self.metrics.success_rate = (self.metrics.confirmed_transactions / total_processed) * 100
    
    async def get_transaction_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get transaction history with optional limit."""
        transactions = []
        for tx_status in self.monitored_transactions.values():
            transactions.append(asdict(tx_status))
        
        # Sort by timestamp (newest first)
        transactions.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return transactions[:limit]
    
    async def export_metrics(self, file_path: str) -> bool:
        """Export metrics to JSON file."""
        try:
            metrics_data = {
                "timestamp": int(time.time()),
                "metrics": asdict(self.metrics),
                "transactions": await self.get_transaction_history()
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(metrics_data, f, indent=2)
            
            logger.info(f"Metrics exported to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export metrics: {e}")
            return False
    
    async def get_network_status(self, network: str) -> Dict[str, Any]:
        """Get network status information."""
        if network not in self.web3_instances:
            return {"error": f"Network {network} not supported"}
        
        try:
            web3 = self.web3_instances[network]
            
            # Get latest block
            latest_block = web3.eth.get_block('latest')
            
            # Get gas price
            gas_price = web3.eth.gas_price
            
            # Get pending transactions count
            pending_txs = len(self.monitored_transactions)
            
            return {
                "network": network,
                "block_number": latest_block.number,
                "gas_price_wei": gas_price,
                "gas_price_gwei": gas_price / 1e9,
                "pending_transactions": pending_txs,
                "is_synced": True,  # Assume synced for now
                "timestamp": int(time.time())
            }
            
        except Exception as e:
            logger.error(f"Failed to get network status for {network}: {e}")
            return {"error": str(e)}
    
    async def cleanup_old_transactions(self, max_age_hours: int = 24):
        """Clean up old completed transactions."""
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        to_remove = []
        for tx_hash, tx_status in self.monitored_transactions.items():
            if (tx_status.status in ["confirmed", "failed", "dropped"] and 
                current_time - tx_status.timestamp > max_age_seconds):
                to_remove.append(tx_hash)
        
        for tx_hash in to_remove:
            await self.remove_transaction(tx_hash)
        
        if to_remove:
            logger.info(f"Cleaned up {len(to_remove)} old transactions")

# Example usage and testing
async def main():
    """Example usage of TransactionMonitor."""
    config = {
        "networks": {
            "hyperion": {"enabled": True},
            "metis": {"enabled": True},
            "lazai": {"enabled": True}
        }
    }
    
    monitor = TransactionMonitor(config)
    
    # Start monitoring
    await monitor.start_monitoring()
    
    # Add some example transactions (these would be real transaction hashes)
    # await monitor.add_transaction("0x123...", "hyperion")
    
    # Get metrics
    metrics = await monitor.get_metrics()
    print(f"Monitoring metrics: {asdict(metrics)}")
    
    # Stop monitoring
    await monitor.stop_monitoring()

if __name__ == "__main__":
    asyncio.run(main())