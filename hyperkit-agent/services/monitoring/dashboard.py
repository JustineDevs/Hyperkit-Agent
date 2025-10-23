#!/usr/bin/env python3
"""
Monitoring Dashboard Service
Real-time monitoring and alerting for HyperKit Agent
Follows .cursor/rules for production-ready implementation
"""

import asyncio
import time
import json
import logging
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
import psutil
import aiohttp
from aiohttp import web
import socketio
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from collections import deque
import threading
import queue

logger = logging.getLogger(__name__)

@dataclass
class MetricData:
    """Represents a metric data point."""
    timestamp: datetime
    name: str
    value: float
    tags: Dict[str, str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = {}

@dataclass
class AlertRule:
    """Represents an alert rule."""
    name: str
    metric: str
    condition: str  # '>', '<', '>=', '<=', '==', '!='
    threshold: float
    duration: int  # seconds
    enabled: bool = True
    message: str = ""

@dataclass
class Alert:
    """Represents an active alert."""
    rule: AlertRule
    triggered_at: datetime
    value: float
    resolved: bool = False
    resolved_at: Optional[datetime] = None

class MetricsCollector:
    """Collects and stores metrics data."""
    
    def __init__(self, max_size: int = 10000):
        self.metrics: Dict[str, deque] = {}
        self.max_size = max_size
        self.lock = threading.Lock()
    
    def add_metric(self, metric: MetricData):
        """Add a metric data point."""
        with self.lock:
            if metric.name not in self.metrics:
                self.metrics[metric.name] = deque(maxlen=self.max_size)
            
            self.metrics[metric.name].append(metric)
    
    def get_metrics(self, name: str, since: Optional[datetime] = None) -> List[MetricData]:
        """Get metrics for a specific name."""
        with self.lock:
            if name not in self.metrics:
                return []
            
            metrics = list(self.metrics[name])
            
            if since:
                metrics = [m for m in metrics if m.timestamp >= since]
            
            return metrics
    
    def get_latest_metric(self, name: str) -> Optional[MetricData]:
        """Get the latest metric for a specific name."""
        with self.lock:
            if name not in self.metrics or not self.metrics[name]:
                return None
            
            return self.metrics[name][-1]
    
    def get_metric_names(self) -> List[str]:
        """Get all metric names."""
        with self.lock:
            return list(self.metrics.keys())

class AlertManager:
    """Manages alerts and alert rules."""
    
    def __init__(self):
        self.rules: List[AlertRule] = []
        self.active_alerts: List[Alert] = []
        self.alert_history: List[Alert] = []
        self.lock = threading.Lock()
    
    def add_rule(self, rule: AlertRule):
        """Add an alert rule."""
        with self.lock:
            self.rules.append(rule)
    
    def remove_rule(self, rule_name: str):
        """Remove an alert rule."""
        with self.lock:
            self.rules = [r for r in self.rules if r.name != rule_name]
    
    def check_alerts(self, metrics_collector: MetricsCollector):
        """Check all alert rules against current metrics."""
        with self.lock:
            for rule in self.rules:
                if not rule.enabled:
                    continue
                
                latest_metric = metrics_collector.get_latest_metric(rule.metric)
                if not latest_metric:
                    continue
                
                # Check if alert should trigger
                should_trigger = self._evaluate_condition(
                    latest_metric.value, 
                    rule.condition, 
                    rule.threshold
                )
                
                if should_trigger:
                    # Check if alert is already active
                    active_alert = next(
                        (a for a in self.active_alerts if a.rule.name == rule.name and not a.resolved),
                        None
                    )
                    
                    if not active_alert:
                        # Create new alert
                        alert = Alert(
                            rule=rule,
                            triggered_at=datetime.now(),
                            value=latest_metric.value
                        )
                        self.active_alerts.append(alert)
                        self.alert_history.append(alert)
                        logger.warning(f"Alert triggered: {rule.name} - {rule.message}")
                
                else:
                    # Check if alert should be resolved
                    active_alert = next(
                        (a for a in self.active_alerts if a.rule.name == rule.name and not a.resolved),
                        None
                    )
                    
                    if active_alert:
                        active_alert.resolved = True
                        active_alert.resolved_at = datetime.now()
                        logger.info(f"Alert resolved: {rule.name}")
    
    def _evaluate_condition(self, value: float, condition: str, threshold: float) -> bool:
        """Evaluate a condition."""
        if condition == '>':
            return value > threshold
        elif condition == '<':
            return value < threshold
        elif condition == '>=':
            return value >= threshold
        elif condition == '<=':
            return value <= threshold
        elif condition == '==':
            return value == threshold
        elif condition == '!=':
            return value != threshold
        else:
            return False
    
    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts."""
        with self.lock:
            return [a for a in self.active_alerts if not a.resolved]
    
    def get_alert_history(self, since: Optional[datetime] = None) -> List[Alert]:
        """Get alert history."""
        with self.lock:
            if since:
                return [a for a in self.alert_history if a.triggered_at >= since]
            return self.alert_history

class SystemMonitor:
    """Monitors system resources."""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector
        self.running = False
        self.monitor_thread = None
    
    def start(self):
        """Start system monitoring."""
        if self.running:
            return
        
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        logger.info("System monitoring started")
    
    def stop(self):
        """Stop system monitoring."""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join()
        logger.info("System monitoring stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop."""
        while self.running:
            try:
                # CPU usage
                cpu_percent = psutil.cpu_percent(interval=1)
                self.metrics_collector.add_metric(MetricData(
                    timestamp=datetime.now(),
                    name="system.cpu_percent",
                    value=cpu_percent,
                    tags={"type": "system"}
                ))
                
                # Memory usage
                memory = psutil.virtual_memory()
                self.metrics_collector.add_metric(MetricData(
                    timestamp=datetime.now(),
                    name="system.memory_percent",
                    value=memory.percent,
                    tags={"type": "system"}
                ))
                
                self.metrics_collector.add_metric(MetricData(
                    timestamp=datetime.now(),
                    name="system.memory_used_mb",
                    value=memory.used / 1024 / 1024,
                    tags={"type": "system"}
                ))
                
                # Disk usage
                disk = psutil.disk_usage('/')
                self.metrics_collector.add_metric(MetricData(
                    timestamp=datetime.now(),
                    name="system.disk_percent",
                    value=disk.percent,
                    tags={"type": "system"}
                ))
                
                # Network I/O
                net_io = psutil.net_io_counters()
                self.metrics_collector.add_metric(MetricData(
                    timestamp=datetime.now(),
                    name="system.network_bytes_sent",
                    value=net_io.bytes_sent,
                    tags={"type": "system"}
                ))
                
                self.metrics_collector.add_metric(MetricData(
                    timestamp=datetime.now(),
                    name="system.network_bytes_recv",
                    value=net_io.bytes_recv,
                    tags={"type": "system"}
                ))
                
            except Exception as e:
                logger.error(f"Error in system monitoring: {e}")
            
            time.sleep(5)  # Monitor every 5 seconds

class ApplicationMonitor:
    """Monitors application-specific metrics."""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector
        self.request_count = 0
        self.error_count = 0
        self.start_time = datetime.now()
    
    def record_request(self, duration: float, success: bool):
        """Record a request metric."""
        self.request_count += 1
        if not success:
            self.error_count += 1
        
        self.metrics_collector.add_metric(MetricData(
            timestamp=datetime.now(),
            name="app.request_duration",
            value=duration,
            tags={"success": str(success)}
        ))
        
        self.metrics_collector.add_metric(MetricData(
            timestamp=datetime.now(),
            name="app.request_count",
            value=self.request_count,
            tags={"type": "counter"}
        ))
        
        if not success:
            self.metrics_collector.add_metric(MetricData(
                timestamp=datetime.now(),
                name="app.error_count",
                value=self.error_count,
                tags={"type": "counter"}
            ))
    
    def record_contract_generation(self, duration: float, success: bool, provider: str):
        """Record contract generation metric."""
        self.metrics_collector.add_metric(MetricData(
            timestamp=datetime.now(),
            name="app.contract_generation_duration",
            value=duration,
            tags={"success": str(success), "provider": provider}
        ))
    
    def record_contract_audit(self, duration: float, success: bool, severity: str):
        """Record contract audit metric."""
        self.metrics_collector.add_metric(MetricData(
            timestamp=datetime.now(),
            name="app.contract_audit_duration",
            value=duration,
            tags={"success": str(success), "severity": severity}
        ))
    
    def record_contract_deployment(self, duration: float, success: bool, network: str):
        """Record contract deployment metric."""
        self.metrics_collector.add_metric(MetricData(
            timestamp=datetime.now(),
            name="app.contract_deployment_duration",
            value=duration,
            tags={"success": str(success), "network": network}
        ))

class MonitoringDashboard:
    """Main monitoring dashboard service."""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8080):
        self.host = host
        self.port = port
        self.metrics_collector = MetricsCollector()
        self.alert_manager = AlertManager()
        self.system_monitor = SystemMonitor(self.metrics_collector)
        self.app_monitor = ApplicationMonitor(self.metrics_collector)
        self.app = web.Application()
        self.sio = socketio.AsyncServer(cors_allowed_origins="*")
        self.sio.attach(self.app)
        self.setup_routes()
        self.setup_alerts()
    
    def setup_routes(self):
        """Setup HTTP routes."""
        self.app.router.add_get('/', self.index_handler)
        self.app.router.add_get('/api/metrics', self.metrics_handler)
        self.app.router.add_get('/api/alerts', self.alerts_handler)
        self.app.router.add_get('/api/health', self.health_handler)
        self.app.router.add_get('/api/dashboard', self.dashboard_handler)
        self.app.router.add_static('/', path='static', name='static')
    
    def setup_alerts(self):
        """Setup default alert rules."""
        # CPU usage alert
        self.alert_manager.add_rule(AlertRule(
            name="high_cpu_usage",
            metric="system.cpu_percent",
            condition=">",
            threshold=80.0,
            duration=60,
            message="High CPU usage detected"
        ))
        
        # Memory usage alert
        self.alert_manager.add_rule(AlertRule(
            name="high_memory_usage",
            metric="system.memory_percent",
            condition=">",
            threshold=85.0,
            duration=60,
            message="High memory usage detected"
        ))
        
        # Disk usage alert
        self.alert_manager.add_rule(AlertRule(
            name="high_disk_usage",
            metric="system.disk_percent",
            condition=">",
            threshold=90.0,
            duration=300,
            message="High disk usage detected"
        ))
        
        # Error rate alert
        self.alert_manager.add_rule(AlertRule(
            name="high_error_rate",
            metric="app.error_count",
            condition=">",
            threshold=10.0,
            duration=300,
            message="High error rate detected"
        ))
    
    async def index_handler(self, request):
        """Serve the main dashboard page."""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>HyperKit Agent Dashboard</title>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
                .container { max-width: 1200px; margin: 0 auto; }
                .header { background: #2c3e50; color: white; padding: 20px; border-radius: 5px; margin-bottom: 20px; }
                .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
                .metric-card { background: white; padding: 20px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
                .metric-title { font-size: 18px; font-weight: bold; margin-bottom: 10px; }
                .metric-value { font-size: 24px; color: #2c3e50; }
                .alert { background: #e74c3c; color: white; padding: 10px; border-radius: 5px; margin: 10px 0; }
                .chart-container { position: relative; height: 300px; margin: 20px 0; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>HyperKit Agent Dashboard</h1>
                    <p>Real-time monitoring and metrics</p>
                </div>
                
                <div id="alerts"></div>
                
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-title">CPU Usage</div>
                        <div class="metric-value" id="cpu-usage">0%</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-title">Memory Usage</div>
                        <div class="metric-value" id="memory-usage">0%</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-title">Request Count</div>
                        <div class="metric-value" id="request-count">0</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-title">Error Count</div>
                        <div class="metric-value" id="error-count">0</div>
                    </div>
                </div>
                
                <div class="chart-container">
                    <canvas id="metrics-chart"></canvas>
                </div>
            </div>
            
            <script>
                const socket = io();
                const ctx = document.getElementById('metrics-chart').getContext('2d');
                const chart = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: [],
                        datasets: [{
                            label: 'CPU Usage',
                            data: [],
                            borderColor: 'rgb(75, 192, 192)',
                            tension: 0.1
                        }, {
                            label: 'Memory Usage',
                            data: [],
                            borderColor: 'rgb(255, 99, 132)',
                            tension: 0.1
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                            y: {
                                beginAtZero: true,
                                max: 100
                            }
                        }
                    }
                });
                
                socket.on('metrics', function(data) {
                    document.getElementById('cpu-usage').textContent = data.cpu_percent + '%';
                    document.getElementById('memory-usage').textContent = data.memory_percent + '%';
                    document.getElementById('request-count').textContent = data.request_count;
                    document.getElementById('error-count').textContent = data.error_count;
                    
                    chart.data.labels.push(new Date().toLocaleTimeString());
                    chart.data.datasets[0].data.push(data.cpu_percent);
                    chart.data.datasets[1].data.push(data.memory_percent);
                    
                    if (chart.data.labels.length > 20) {
                        chart.data.labels.shift();
                        chart.data.datasets[0].data.shift();
                        chart.data.datasets[1].data.shift();
                    }
                    
                    chart.update();
                });
                
                socket.on('alert', function(alert) {
                    const alertsDiv = document.getElementById('alerts');
                    const alertDiv = document.createElement('div');
                    alertDiv.className = 'alert';
                    alertDiv.textContent = alert.message;
                    alertsDiv.appendChild(alertDiv);
                    
                    setTimeout(() => {
                        alertDiv.remove();
                    }, 5000);
                });
            </script>
        </body>
        </html>
        """
        return web.Response(text=html, content_type='text/html')
    
    async def metrics_handler(self, request):
        """API endpoint for metrics."""
        metrics = {}
        for name in self.metrics_collector.get_metric_names():
            latest = self.metrics_collector.get_latest_metric(name)
            if latest:
                metrics[name] = {
                    'value': latest.value,
                    'timestamp': latest.timestamp.isoformat(),
                    'tags': latest.tags
                }
        
        return web.json_response(metrics)
    
    async def alerts_handler(self, request):
        """API endpoint for alerts."""
        active_alerts = self.alert_manager.get_active_alerts()
        alerts = []
        
        for alert in active_alerts:
            alerts.append({
                'name': alert.rule.name,
                'message': alert.rule.message,
                'triggered_at': alert.triggered_at.isoformat(),
                'value': alert.value,
                'threshold': alert.rule.threshold
            })
        
        return web.json_response(alerts)
    
    async def health_handler(self, request):
        """API endpoint for health check."""
        health = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'uptime': (datetime.now() - self.app_monitor.start_time).total_seconds(),
            'metrics_count': len(self.metrics_collector.get_metric_names()),
            'active_alerts': len(self.alert_manager.get_active_alerts())
        }
        
        return web.json_response(health)
    
    async def dashboard_handler(self, request):
        """API endpoint for dashboard data."""
        # Get recent metrics
        since = datetime.now() - timedelta(hours=1)
        metrics_data = {}
        
        for name in self.metrics_collector.get_metric_names():
            metrics = self.metrics_collector.get_metrics(name, since)
            if metrics:
                metrics_data[name] = [
                    {
                        'timestamp': m.timestamp.isoformat(),
                        'value': m.value,
                        'tags': m.tags
                    }
                    for m in metrics
                ]
        
        # Get alerts
        alerts = self.alert_manager.get_active_alerts()
        alerts_data = [
            {
                'name': alert.rule.name,
                'message': alert.rule.message,
                'triggered_at': alert.triggered_at.isoformat(),
                'value': alert.value
            }
            for alert in alerts
        ]
        
        dashboard_data = {
            'metrics': metrics_data,
            'alerts': alerts_data,
            'timestamp': datetime.now().isoformat()
        }
        
        return web.json_response(dashboard_data)
    
    async def start(self):
        """Start the monitoring dashboard."""
        self.system_monitor.start()
        
        # Start alert checking loop
        asyncio.create_task(self._alert_check_loop())
        
        # Start metrics broadcasting loop
        asyncio.create_task(self._metrics_broadcast_loop())
        
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()
        
        logger.info(f"Monitoring dashboard started on http://{self.host}:{self.port}")
    
    async def _alert_check_loop(self):
        """Alert checking loop."""
        while True:
            try:
                self.alert_manager.check_alerts(self.metrics_collector)
                await asyncio.sleep(10)  # Check every 10 seconds
            except Exception as e:
                logger.error(f"Error in alert checking: {e}")
    
    async def _metrics_broadcast_loop(self):
        """Metrics broadcasting loop."""
        while True:
            try:
                # Get latest metrics
                cpu_metric = self.metrics_collector.get_latest_metric("system.cpu_percent")
                memory_metric = self.metrics_collector.get_latest_metric("system.memory_percent")
                request_metric = self.metrics_collector.get_latest_metric("app.request_count")
                error_metric = self.metrics_collector.get_latest_metric("app.error_count")
                
                metrics_data = {
                    'cpu_percent': cpu_metric.value if cpu_metric else 0,
                    'memory_percent': memory_metric.value if memory_metric else 0,
                    'request_count': int(request_metric.value) if request_metric else 0,
                    'error_count': int(error_metric.value) if error_metric else 0
                }
                
                # Broadcast to connected clients
                await self.sio.emit('metrics', metrics_data)
                
                # Check for new alerts
                active_alerts = self.alert_manager.get_active_alerts()
                for alert in active_alerts:
                    if not hasattr(alert, 'broadcasted'):
                        await self.sio.emit('alert', {
                            'message': alert.rule.message,
                            'value': alert.value,
                            'threshold': alert.rule.threshold
                        })
                        alert.broadcasted = True
                
                await asyncio.sleep(5)  # Broadcast every 5 seconds
            except Exception as e:
                logger.error(f"Error in metrics broadcasting: {e}")

# Example usage
async def main():
    """Example usage of the monitoring dashboard."""
    dashboard = MonitoringDashboard()
    await dashboard.start()
    
    # Keep running
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down monitoring dashboard")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
