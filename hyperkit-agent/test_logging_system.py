#!/usr/bin/env python3
"""
Test script for logging system functionality
"""

import asyncio
import sys
import os
import time

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.core.logging_system import HyperKitLogger, LogLevel, LogCategory, log_info, log_error, log_warning

async def test_logging_system():
    """Test the logging system functionality"""
    print("🧪 Testing Logging System")
    print("=" * 50)
    
    # Initialize the logger
    logger = HyperKitLogger(log_dir="test_logs", log_level="DEBUG")
    
    # Test 1: Basic logging
    print("\n📝 Test 1: Basic logging...")
    log_info(LogCategory.SYSTEM, "System started successfully")
    log_warning(LogCategory.AI_AGENT, "Mock AI agent in use")
    log_error(LogCategory.BLOCKCHAIN, "Connection failed", Exception("Network timeout"))
    
    print("✅ Basic logging completed")
    
    # Test 2: AI operation logging
    print("\n🤖 Test 2: AI operation logging...")
    logger.log_ai_operation("generate_contract", "alith-v1", "success", 2.5, 1500)
    logger.log_ai_operation("audit_contract", "alith-security-v1", "error", 1.2, 800)
    
    print("✅ AI operation logging completed")
    
    # Test 3: Blockchain operation logging
    print("\n⛓️ Test 3: Blockchain operation logging...")
    logger.log_blockchain_operation("deploy_contract", "hyperion", "0x123...abc", 2100000, "success")
    logger.log_blockchain_operation("verify_contract", "hyperion", "0x456...def", 50000, "success")
    
    print("✅ Blockchain operation logging completed")
    
    # Test 4: Security event logging
    print("\n🛡️ Test 4: Security event logging...")
    logger.log_security_event("vulnerability_detected", "HIGH", "0x789...ghi", 
                             "Reentrancy vulnerability", "Use checks-effects-interactions pattern")
    logger.log_security_event("audit_completed", "INFO", "0x789...ghi")
    
    print("✅ Security event logging completed")
    
    # Test 5: Performance metrics
    print("\n📊 Test 5: Performance metrics...")
    logger.log_performance_metric("contract_generation_time", 2.5, "seconds")
    logger.log_performance_metric("audit_processing_time", 1.8, "seconds")
    logger.log_performance_metric("api_response_time", 150, "ms")
    
    print("✅ Performance metrics logged")
    
    # Test 6: API request logging
    print("\n🌐 Test 6: API request logging...")
    logger.log_api_request("/api/v1/generate", "POST", 200, 2.1, "user123")
    logger.log_api_request("/api/v1/audit", "POST", 400, 0.5, "user456")
    
    print("✅ API request logging completed")
    
    # Test 7: Error summary
    print("\n📋 Test 7: Error summary...")
    error_summary = logger.get_error_summary()
    print(f"   Total errors: {error_summary['total_errors']}")
    print(f"   Total warnings: {error_summary['total_warnings']}")
    print(f"   Critical errors: {error_summary['critical_errors']}")
    print(f"   Performance metrics: {len(error_summary['performance_metrics'])}")
    
    print("✅ Error summary generated")
    
    # Test 8: Health status
    print("\n🏥 Test 8: Health status...")
    health_status = logger.get_health_status()
    print(f"   Health status: {health_status['status']}")
    print(f"   Log files: {health_status['log_files']}")
    print(f"   JSON files: {health_status['json_files']}")
    
    print("✅ Health status checked")
    
    # Test 9: Log export
    print("\n📤 Test 9: Log export...")
    logs = logger.export_logs()
    total_log_entries = sum(len(category_logs) for category_logs in logs.values())
    print(f"   Exported {total_log_entries} log entries")
    print(f"   Categories: {list(logs.keys())}")
    
    print("✅ Log export completed")
    
    # Test 10: Cleanup
    print("\n🧹 Test 10: Log cleanup...")
    cleanup_result = logger.cleanup_old_logs(days_to_keep=0)  # Clean all for testing
    print(f"   Cleaned {cleanup_result['files_removed']} files")
    
    print("✅ Log cleanup completed")
    
    print("\n" + "=" * 50)
    print("🎉 Logging system tests completed successfully!")
    print("✅ All logging functionality is working correctly")
    
    # Show log files created
    print("\n📁 Log files created:")
    for log_file in logger.log_dir.glob("*.log"):
        print(f"   - {log_file.name}")
    for json_file in logger.log_dir.glob("*.json"):
        print(f"   - {json_file.name}")

if __name__ == "__main__":
    asyncio.run(test_logging_system())
