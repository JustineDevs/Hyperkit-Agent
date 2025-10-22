"""
Enhanced Monitoring System
Real-time transaction and contract monitoring with analytics
"""

import asyncio
import json
import time
import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class MonitorType(Enum):
    TRANSACTION = "transaction"
    CONTRACT = "contract"
    GAS = "gas"
    EVENTS = "events"

@dataclass
class MonitorConfig:
    """Configuration for monitoring"""
    target: str
    monitor_type: MonitorType
    network: str = "hyperion"
    interval: int = 30  # seconds
    duration: Optional[int] = None  # None for indefinite
    gas_threshold: Optional[float] = None
    event_filters: Optional[List[str]] = None

@dataclass
class MonitorEvent:
    """Monitoring event data"""
    timestamp: datetime
    event_type: str
    data: Dict[str, Any]
    network: str
    target: str

class EnhancedMonitor:
    """Enhanced monitoring system for transactions and contracts"""
    
    def __init__(self):
        self.active_monitors: Dict[str, MonitorConfig] = {}
        self.monitor_tasks: Dict[str, asyncio.Task] = {}
        self.event_handlers: List[Callable] = []
        self.metrics = {
            "transactions_monitored": 0,
            "contracts_monitored": 0,
            "events_captured": 0,
            "gas_usage": [],
            "error_count": 0
        }
    
    async def start_monitoring(self, config: MonitorConfig) -> str:
        """
        Start monitoring a target
        
        Args:
            config: Monitoring configuration
            
        Returns:
            Monitor ID
        """
        monitor_id = f"{config.monitor_type.value}_{config.target}_{int(time.time())}"
        
        self.active_monitors[monitor_id] = config
        
        # Start monitoring task
        task = asyncio.create_task(self._monitor_loop(monitor_id, config))
        self.monitor_tasks[monitor_id] = task
        
        logger.info(f"Started monitoring {config.target} ({config.monitor_type.value})")
        return monitor_id
    
    async def stop_monitoring(self, monitor_id: str) -> bool:
        """
        Stop monitoring a target
        
        Args:
            monitor_id: Monitor ID to stop
            
        Returns:
            True if stopped successfully
        """
        if monitor_id in self.monitor_tasks:
            self.monitor_tasks[monitor_id].cancel()
            del self.monitor_tasks[monitor_id]
            del self.active_monitors[monitor_id]
            logger.info(f"Stopped monitoring {monitor_id}")
            return True
        return False
    
    async def _monitor_loop(self, monitor_id: str, config: MonitorConfig):
        """Main monitoring loop"""
        start_time = time.time()
        
        try:
            while True:
                # Check if monitoring should stop
                if config.duration and (time.time() - start_time) > config.duration:
                    logger.info(f"Monitoring duration reached for {monitor_id}")
                    break
                
                # Perform monitoring based on type
                if config.monitor_type == MonitorType.TRANSACTION:
                    await self._monitor_transaction(monitor_id, config)
                elif config.monitor_type == MonitorType.CONTRACT:
                    await self._monitor_contract(monitor_id, config)
                elif config.monitor_type == MonitorType.GAS:
                    await self._monitor_gas(monitor_id, config)
                elif config.monitor_type == MonitorType.EVENTS:
                    await self._monitor_events(monitor_id, config)
                
                # Wait for next interval
                await asyncio.sleep(config.interval)
                
        except asyncio.CancelledError:
            logger.info(f"Monitoring cancelled for {monitor_id}")
        except Exception as e:
            logger.error(f"Monitoring error for {monitor_id}: {e}")
            self.metrics["error_count"] += 1
        finally:
            # Cleanup
            if monitor_id in self.monitor_tasks:
                del self.monitor_tasks[monitor_id]
            if monitor_id in self.active_monitors:
                del self.active_monitors[monitor_id]
    
    async def _monitor_transaction(self, monitor_id: str, config: MonitorConfig):
        """Monitor transaction status and details"""
        try:
            # TODO: Implement actual transaction monitoring
            # This would query the blockchain for transaction status
            
            event_data = {
                "transaction_hash": config.target,
                "status": "pending",  # or "confirmed", "failed"
                "confirmations": 0,
                "gas_used": 0,
                "gas_price": 0,
                "block_number": None
            }
            
            await self._emit_event(MonitorEvent(
                timestamp=datetime.now(),
                event_type="transaction_update",
                data=event_data,
                network=config.network,
                target=config.target
            ))
            
            self.metrics["transactions_monitored"] += 1
            
        except Exception as e:
            logger.error(f"Transaction monitoring error: {e}")
    
    async def _monitor_contract(self, monitor_id: str, config: MonitorConfig):
        """Monitor contract state and events"""
        try:
            # TODO: Implement actual contract monitoring
            # This would query contract state and listen for events
            
            event_data = {
                "contract_address": config.target,
                "balance": "0",
                "nonce": 0,
                "code_hash": "0x...",
                "storage_changes": []
            }
            
            await self._emit_event(MonitorEvent(
                timestamp=datetime.now(),
                event_type="contract_update",
                data=event_data,
                network=config.network,
                target=config.target
            ))
            
            self.metrics["contracts_monitored"] += 1
            
        except Exception as e:
            logger.error(f"Contract monitoring error: {e}")
    
    async def _monitor_gas(self, monitor_id: str, config: MonitorConfig):
        """Monitor gas usage and optimization opportunities"""
        try:
            # TODO: Implement actual gas monitoring
            # This would track gas usage patterns and suggest optimizations
            
            gas_data = {
                "current_gas_price": 0,
                "average_gas_used": 0,
                "gas_efficiency": 0.0,
                "optimization_suggestions": []
            }
            
            if config.gas_threshold and gas_data["current_gas_price"] > config.gas_threshold:
                gas_data["alert"] = f"Gas price exceeds threshold: {gas_data['current_gas_price']}"
            
            self.metrics["gas_usage"].append(gas_data)
            
            await self._emit_event(MonitorEvent(
                timestamp=datetime.now(),
                event_type="gas_update",
                data=gas_data,
                network=config.network,
                target=config.target
            ))
            
        except Exception as e:
            logger.error(f"Gas monitoring error: {e}")
    
    async def _monitor_events(self, monitor_id: str, config: MonitorConfig):
        """Monitor contract events"""
        try:
            # TODO: Implement actual event monitoring
            # This would listen for specific contract events
            
            event_data = {
                "events_found": 0,
                "recent_events": [],
                "event_types": config.event_filters or []
            }
            
            await self._emit_event(MonitorEvent(
                timestamp=datetime.now(),
                event_type="events_update",
                data=event_data,
                network=config.network,
                target=config.target
            ))
            
            self.metrics["events_captured"] += 1
            
        except Exception as e:
            logger.error(f"Event monitoring error: {e}")
    
    async def _emit_event(self, event: MonitorEvent):
        """Emit monitoring event to handlers"""
        for handler in self.event_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                logger.error(f"Event handler error: {e}")
    
    def add_event_handler(self, handler: Callable):
        """Add event handler for monitoring events"""
        self.event_handlers.append(handler)
    
    def remove_event_handler(self, handler: Callable):
        """Remove event handler"""
        if handler in self.event_handlers:
            self.event_handlers.remove(handler)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get monitoring metrics"""
        return {
            **self.metrics,
            "active_monitors": len(self.active_monitors),
            "uptime": time.time(),
            "networks": list(set(config.network for config in self.active_monitors.values()))
        }
    
    def get_active_monitors(self) -> Dict[str, Dict[str, Any]]:
        """Get information about active monitors"""
        return {
            monitor_id: {
                "target": config.target,
                "type": config.monitor_type.value,
                "network": config.network,
                "interval": config.interval,
                "duration": config.duration
            }
            for monitor_id, config in self.active_monitors.items()
        }
    
    async def stop_all_monitoring(self):
        """Stop all active monitoring"""
        for monitor_id in list(self.monitor_tasks.keys()):
            await self.stop_monitoring(monitor_id)
    
    def get_gas_analytics(self) -> Dict[str, Any]:
        """Get gas usage analytics"""
        if not self.metrics["gas_usage"]:
            return {"message": "No gas data available"}
        
        gas_data = self.metrics["gas_usage"]
        
        return {
            "total_measurements": len(gas_data),
            "average_gas_price": sum(d.get("current_gas_price", 0) for d in gas_data) / len(gas_data),
            "average_gas_used": sum(d.get("average_gas_used", 0) for d in gas_data) / len(gas_data),
            "efficiency_trend": [d.get("gas_efficiency", 0) for d in gas_data[-10:]],  # Last 10 measurements
            "optimization_opportunities": len([d for d in gas_data if d.get("optimization_suggestions")])
        }

# Global instance
enhanced_monitor = EnhancedMonitor()
