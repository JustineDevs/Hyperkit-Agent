"""
Monitor Command Module
System monitoring and health functionality
"""

import click
import time
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

@click.group()
def monitor_group():
    """
    Monitor system health and performance
    
    ⚠️  WARNING: This command has partial implementation - some features may be limited.
    See docs/HONEST_STATUS.md for details.
    """
    from cli.utils.warnings import show_command_warning
    show_command_warning('monitor')
    pass

@monitor_group.command()
def health():
    """Check system health status"""
    console.print("System Health Check")
    
    try:
        from core.validation.production_validator import ProductionModeValidator
        
        validator = ProductionModeValidator()
        health_status = validator.validate_production_mode()
        
        # Display health status
        console.print(f"\nHealth Status:")
        
        # Check each component
        components = [
            ("Alith SDK", health_status.get('alith_sdk', {})),
            ("Foundry", health_status.get('foundry', {})),
            ("Web3 Connection", health_status.get('web3_connection', {})),
            ("AI Providers", health_status.get('ai_providers', {})),
            ("Private Key", health_status.get('private_key', {})),
            ("Hyperion RPC", health_status.get('hyperion_rpc', {}))
        ]
        
        for component_name, status in components:
            if status.get('status') == 'success':
                console.print(f"  PASS {component_name}: {status.get('message', 'OK')}")
            else:
                console.print(f"  FAIL {component_name}: {status.get('message', 'FAILED')}")
        
        # Overall status
        critical_failures = health_status.get('critical_failures', [])
        if critical_failures:
            console.print(f"\n🚨 CRITICAL FAILURES:")
            for failure in critical_failures:
                console.print(f"  • {failure}")
            console.print(f"\nWARN SYSTEM NOT READY FOR PRODUCTION")
        else:
            console.print(f"\nPASS ALL SYSTEMS OPERATIONAL")
            
    except Exception as e:
        console.print(f"Health check error: {e}", style="red")
        console.print(f"💡 This command requires production validator")

@monitor_group.command()
def metrics():
    """Display system metrics"""
    console.print("System Metrics")
    
    try:
        import psutil
        import os
        from pathlib import Path
        
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Process metrics
        process = psutil.Process(os.getpid())
        process_memory = process.memory_info()
        
        # Project metrics
        project_path = Path.cwd()
        project_size = sum(f.stat().st_size for f in project_path.rglob('*') if f.is_file())
        
        console.print(f"\n💻 System Resources:")
        console.print(f"  CPU Usage: {cpu_percent}%")
        console.print(f"  Memory Usage: {memory.percent}% ({memory.used // (1024**3)}GB / {memory.total // (1024**3)}GB)")
        console.print(f"  Disk Usage: {disk.percent}% ({disk.used // (1024**3)}GB / {disk.total // (1024**3)}GB)")
        
        console.print(f"\n🔧 Process Metrics:")
        console.print(f"  HyperAgent Memory: {process_memory.rss // (1024**2)}MB")
        console.print(f"  Project Size: {project_size // (1024**2)}MB")
        
        # Check log file sizes
        log_dir = Path("logs")
        if log_dir.exists():
            log_size = sum(f.stat().st_size for f in log_dir.rglob('*.log') if f.is_file())
            console.print(f"  Log Files: {log_size // (1024**2)}MB")
        
        console.print(f"\nMetrics retrieved successfully")
        
    except ImportError:
        console.print(f"psutil not available - install with: pip install psutil")
        console.print(f"💡 This command requires psutil for system metrics")
    except Exception as e:
        console.print(f"Metrics error: {e}", style="red")
        console.print(f"💡 This command requires system access")

@monitor_group.command()
@click.option('--watch', '-w', is_flag=True, help='Watch mode (continuous monitoring)')
def status(watch):
    """Show system status"""
    console.print("System Status")
    
    try:
        from core.validation.production_validator import ProductionModeValidator
        import time
        
        validator = ProductionModeValidator()
        
        if watch:
            console.print("👀 Watch mode enabled - Press Ctrl+C to stop")
            try:
                while True:
                    health_status = validator.validate_production_mode()
                    critical_failures = health_status.get('critical_failures', [])
                    
                    # Clear screen and show status
                    console.clear()
                    console.print(f"System Status - {time.strftime('%H:%M:%S')}")
                    
                    if critical_failures:
                        console.print(f"🚨 CRITICAL FAILURES: {len(critical_failures)}")
                        for failure in critical_failures:
                            console.print(f"  • {failure}")
                    else:
                        console.print(f"ALL SYSTEMS OPERATIONAL")
                    
                    time.sleep(5)  # Update every 5 seconds
            except KeyboardInterrupt:
                console.print(f"\n👋 Watch mode stopped")
        else:
            # Single status check
            health_status = validator.validate_production_mode()
            critical_failures = health_status.get('critical_failures', [])
            
            if critical_failures:
                console.print(f"🚨 CRITICAL FAILURES: {len(critical_failures)}")
                for failure in critical_failures:
                    console.print(f"  • {failure}")
            else:
                console.print(f"ALL SYSTEMS OPERATIONAL")
            
            console.print(f"Status updated")
            
    except Exception as e:
        console.print(f"Status error: {e}", style="red")
        console.print(f"💡 This command requires production validator")

@monitor_group.command()
def logs():
    """View system logs"""
    console.print("📝 System Logs")
    
    try:
        from pathlib import Path
        import os
        
        log_dir = Path("logs")
        if not log_dir.exists():
            console.print(f"No logs directory found")
            console.print(f"💡 Logs are created when the system runs")
            return
        
        # Find log files
        log_files = list(log_dir.glob("*.log"))
        if not log_files:
            console.print(f"No log files found in {log_dir}")
            return
        
        # Show recent log files
        console.print(f"\nLog Files:")
        for log_file in sorted(log_files, key=lambda x: x.stat().st_mtime, reverse=True)[:5]:
            size = log_file.stat().st_size
            mtime = log_file.stat().st_mtime
            console.print(f"  • {log_file.name} ({size // 1024}KB) - {time.ctime(mtime)}")
        
        # Show last few lines of the most recent log
        if log_files:
            latest_log = max(log_files, key=lambda x: x.stat().st_mtime)
            console.print(f"\n📄 Last 10 lines of {latest_log.name}:")
            console.print("─" * 50)
            
            try:
                with open(latest_log, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    for line in lines[-10:]:
                        console.print(line.rstrip())
            except Exception as e:
                console.print(f"Error reading log file: {e}")
        
        console.print(f"\nLogs displayed")
        
    except Exception as e:
        console.print(f"Logs error: {e}", style="red")
        console.print(f"💡 This command requires file system access")
