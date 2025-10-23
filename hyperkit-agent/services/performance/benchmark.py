#!/usr/bin/env python3
"""
Performance Benchmarking Service
Comprehensive performance testing and optimization for HyperKit Agent
Follows .cursor/rules for production-ready implementation
"""

import asyncio
import time
import psutil
import memory_profiler
import cProfile
import pstats
import io
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import json
import logging
from pathlib import Path
import statistics
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

logger = logging.getLogger(__name__)

@dataclass
class BenchmarkResult:
    """Represents a benchmark result."""
    name: str
    duration: float
    memory_usage: float
    cpu_usage: float
    success: bool
    error: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class PerformanceMetrics:
    """Represents performance metrics."""
    avg_duration: float
    min_duration: float
    max_duration: float
    std_duration: float
    avg_memory: float
    max_memory: float
    avg_cpu: float
    max_cpu: float
    success_rate: float
    total_tests: int
    failed_tests: int

class PerformanceBenchmark:
    """Comprehensive performance benchmarking system."""
    
    def __init__(self, output_dir: str = "./benchmarks"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.results: List[BenchmarkResult] = []
        self.start_time = None
        self.end_time = None
        
    async def benchmark_function(self, 
                               func: Callable, 
                               name: str, 
                               iterations: int = 1,
                               *args, **kwargs) -> BenchmarkResult:
        """Benchmark a single function."""
        logger.info(f"Benchmarking {name} with {iterations} iterations")
        
        durations = []
        memory_usage = []
        cpu_usage = []
        success_count = 0
        error = None
        
        for i in range(iterations):
            try:
                # Start monitoring
                process = psutil.Process()
                start_memory = process.memory_info().rss / 1024 / 1024  # MB
                start_cpu = process.cpu_percent()
                start_time = time.time()
                
                # Execute function
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                
                # End monitoring
                end_time = time.time()
                end_memory = process.memory_info().rss / 1024 / 1024  # MB
                end_cpu = process.cpu_percent()
                
                duration = end_time - start_time
                memory = end_memory - start_memory
                cpu = end_cpu - start_cpu
                
                durations.append(duration)
                memory_usage.append(memory)
                cpu_usage.append(cpu)
                success_count += 1
                
            except Exception as e:
                error = str(e)
                logger.error(f"Benchmark {name} iteration {i} failed: {e}")
        
        # Calculate metrics
        avg_duration = statistics.mean(durations) if durations else 0
        avg_memory = statistics.mean(memory_usage) if memory_usage else 0
        avg_cpu = statistics.mean(cpu_usage) if cpu_usage else 0
        
        result = BenchmarkResult(
            name=name,
            duration=avg_duration,
            memory_usage=avg_memory,
            cpu_usage=avg_cpu,
            success=success_count > 0,
            error=error if success_count == 0 else None,
            metadata={
                "iterations": iterations,
                "successful_iterations": success_count,
                "durations": durations,
                "memory_usage": memory_usage,
                "cpu_usage": cpu_usage
            }
        )
        
        self.results.append(result)
        return result
    
    async def benchmark_contract_generation(self, 
                                          generator, 
                                          prompts: List[str],
                                          iterations: int = 5) -> List[BenchmarkResult]:
        """Benchmark contract generation performance."""
        results = []
        
        for prompt in prompts:
            result = await self.benchmark_function(
                generator.generate_contract,
                f"contract_generation_{prompt[:20]}",
                iterations,
                prompt
            )
            results.append(result)
        
        return results
    
    async def benchmark_contract_auditing(self, 
                                        auditor, 
                                        contract_codes: List[str],
                                        iterations: int = 5) -> List[BenchmarkResult]:
        """Benchmark contract auditing performance."""
        results = []
        
        for i, code in enumerate(contract_codes):
            result = await self.benchmark_function(
                auditor.audit_contract,
                f"contract_auditing_{i}",
                iterations,
                code
            )
            results.append(result)
        
        return results
    
    async def benchmark_contract_deployment(self, 
                                          deployer, 
                                          contract_codes: List[str],
                                          network: str = "hyperion",
                                          iterations: int = 3) -> List[BenchmarkResult]:
        """Benchmark contract deployment performance."""
        results = []
        
        for i, code in enumerate(contract_codes):
            result = await self.benchmark_function(
                deployer.deploy_contract,
                f"contract_deployment_{i}",
                iterations,
                code,
                network
            )
            results.append(result)
        
        return results
    
    async def benchmark_ai_providers(self, 
                                   generator, 
                                   prompt: str,
                                   providers: List[str],
                                   iterations: int = 3) -> List[BenchmarkResult]:
        """Benchmark AI provider performance."""
        results = []
        
        for provider in providers:
            result = await self.benchmark_function(
                generator.generate_contract,
                f"ai_provider_{provider}",
                iterations,
                prompt,
                provider
            )
            results.append(result)
        
        return results
    
    async def benchmark_network_operations(self, 
                                         deployer, 
                                         networks: List[str],
                                         iterations: int = 5) -> List[BenchmarkResult]:
        """Benchmark network operations performance."""
        results = []
        
        for network in networks:
            result = await self.benchmark_function(
                deployer.get_network_info,
                f"network_info_{network}",
                iterations,
                network
            )
            results.append(result)
        
        return results
    
    def calculate_metrics(self, results: List[BenchmarkResult]) -> PerformanceMetrics:
        """Calculate performance metrics from results."""
        if not results:
            return PerformanceMetrics(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
        
        durations = [r.duration for r in results if r.success]
        memory_usage = [r.memory_usage for r in results if r.success]
        cpu_usage = [r.cpu_usage for r in results if r.success]
        
        success_count = sum(1 for r in results if r.success)
        total_count = len(results)
        
        return PerformanceMetrics(
            avg_duration=statistics.mean(durations) if durations else 0,
            min_duration=min(durations) if durations else 0,
            max_duration=max(durations) if durations else 0,
            std_duration=statistics.stdev(durations) if len(durations) > 1 else 0,
            avg_memory=statistics.mean(memory_usage) if memory_usage else 0,
            max_memory=max(memory_usage) if memory_usage else 0,
            avg_cpu=statistics.mean(cpu_usage) if cpu_usage else 0,
            max_cpu=max(cpu_usage) if cpu_usage else 0,
            success_rate=success_count / total_count if total_count > 0 else 0,
            total_tests=total_count,
            failed_tests=total_count - success_count
        )
    
    def generate_report(self, results: List[BenchmarkResult]) -> str:
        """Generate a comprehensive performance report."""
        metrics = self.calculate_metrics(results)
        
        report = []
        report.append("# Performance Benchmark Report")
        report.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"**Total Tests:** {metrics.total_tests}")
        report.append(f"**Success Rate:** {metrics.success_rate:.2%}")
        report.append("")
        
        # Summary metrics
        report.append("## 📊 Summary Metrics")
        report.append(f"- **Average Duration:** {metrics.avg_duration:.3f}s")
        report.append(f"- **Min Duration:** {metrics.min_duration:.3f}s")
        report.append(f"- **Max Duration:** {metrics.max_duration:.3f}s")
        report.append(f"- **Std Deviation:** {metrics.std_duration:.3f}s")
        report.append(f"- **Average Memory:** {metrics.avg_memory:.2f} MB")
        report.append(f"- **Max Memory:** {metrics.max_memory:.2f} MB")
        report.append(f"- **Average CPU:** {metrics.avg_cpu:.2f}%")
        report.append(f"- **Max CPU:** {metrics.max_cpu:.2f}%")
        report.append("")
        
        # Individual results
        report.append("## 📋 Individual Results")
        for result in results:
            status = "✅" if result.success else "❌"
            report.append(f"### {status} {result.name}")
            report.append(f"- **Duration:** {result.duration:.3f}s")
            report.append(f"- **Memory:** {result.memory_usage:.2f} MB")
            report.append(f"- **CPU:** {result.cpu_usage:.2f}%")
            if result.error:
                report.append(f"- **Error:** {result.error}")
            report.append("")
        
        # Performance analysis
        report.append("## 🔍 Performance Analysis")
        
        # Fastest operations
        successful_results = [r for r in results if r.success]
        if successful_results:
            fastest = min(successful_results, key=lambda x: x.duration)
            slowest = max(successful_results, key=lambda x: x.duration)
            
            report.append(f"- **Fastest Operation:** {fastest.name} ({fastest.duration:.3f}s)")
            report.append(f"- **Slowest Operation:** {slowest.name} ({slowest.duration:.3f}s)")
            report.append("")
        
        # Memory analysis
        if successful_results:
            memory_efficient = min(successful_results, key=lambda x: x.memory_usage)
            memory_intensive = max(successful_results, key=lambda x: x.memory_usage)
            
            report.append(f"- **Most Memory Efficient:** {memory_efficient.name} ({memory_efficient.memory_usage:.2f} MB)")
            report.append(f"- **Most Memory Intensive:** {memory_intensive.name} ({memory_intensive.memory_usage:.2f} MB)")
            report.append("")
        
        # Recommendations
        report.append("## 💡 Recommendations")
        
        if metrics.avg_duration > 10:
            report.append("- ⚠️ **Performance Issue:** Average duration is high. Consider optimization.")
        
        if metrics.max_memory > 1000:
            report.append("- ⚠️ **Memory Issue:** High memory usage detected. Consider memory optimization.")
        
        if metrics.success_rate < 0.9:
            report.append("- ⚠️ **Reliability Issue:** Low success rate. Check error handling.")
        
        if metrics.std_duration > metrics.avg_duration * 0.5:
            report.append("- ⚠️ **Consistency Issue:** High variance in performance. Check for race conditions.")
        
        report.append("")
        report.append("---")
        report.append("*Generated by HyperKit Agent Performance Benchmark*")
        
        return "\n".join(report)
    
    def generate_charts(self, results: List[BenchmarkResult]) -> None:
        """Generate performance charts."""
        if not results:
            return
        
        # Set up the plotting style
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
        
        # Create figure with subplots
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('HyperKit Agent Performance Benchmark', fontsize=16)
        
        # Duration chart
        successful_results = [r for r in results if r.success]
        if successful_results:
            names = [r.name for r in successful_results]
            durations = [r.duration for r in successful_results]
            
            axes[0, 0].bar(names, durations)
            axes[0, 0].set_title('Operation Duration')
            axes[0, 0].set_ylabel('Duration (seconds)')
            axes[0, 0].tick_params(axis='x', rotation=45)
        
        # Memory usage chart
        if successful_results:
            memory_usage = [r.memory_usage for r in successful_results]
            
            axes[0, 1].bar(names, memory_usage)
            axes[0, 1].set_title('Memory Usage')
            axes[0, 1].set_ylabel('Memory (MB)')
            axes[0, 1].tick_params(axis='x', rotation=45)
        
        # CPU usage chart
        if successful_results:
            cpu_usage = [r.cpu_usage for r in successful_results]
            
            axes[1, 0].bar(names, cpu_usage)
            axes[1, 0].set_title('CPU Usage')
            axes[1, 0].set_ylabel('CPU (%)')
            axes[1, 0].tick_params(axis='x', rotation=45)
        
        # Success rate chart
        success_rates = []
        for result in results:
            if result.metadata and 'iterations' in result.metadata:
                success_rate = result.metadata['successful_iterations'] / result.metadata['iterations']
                success_rates.append(success_rate)
            else:
                success_rates.append(1.0 if result.success else 0.0)
        
        axes[1, 1].bar(names, success_rates)
        axes[1, 1].set_title('Success Rate')
        axes[1, 1].set_ylabel('Success Rate')
        axes[1, 1].set_ylim(0, 1)
        axes[1, 1].tick_params(axis='x', rotation=45)
        
        # Adjust layout and save
        plt.tight_layout()
        chart_path = self.output_dir / f"performance_charts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Performance charts saved to {chart_path}")
    
    def save_results(self, results: List[BenchmarkResult]) -> None:
        """Save benchmark results to files."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save JSON results
        json_path = self.output_dir / f"benchmark_results_{timestamp}.json"
        with open(json_path, 'w') as f:
            json.dump([asdict(r) for r in results], f, indent=2)
        
        # Save CSV results
        csv_path = self.output_dir / f"benchmark_results_{timestamp}.csv"
        df = pd.DataFrame([asdict(r) for r in results])
        df.to_csv(csv_path, index=False)
        
        # Generate and save report
        report = self.generate_report(results)
        report_path = self.output_dir / f"benchmark_report_{timestamp}.md"
        with open(report_path, 'w') as f:
            f.write(report)
        
        # Generate charts
        self.generate_charts(results)
        
        logger.info(f"Benchmark results saved to {self.output_dir}")
    
    async def run_comprehensive_benchmark(self, 
                                        generator, 
                                        auditor, 
                                        deployer,
                                        test_data: Dict[str, Any]) -> List[BenchmarkResult]:
        """Run a comprehensive benchmark suite."""
        logger.info("Starting comprehensive performance benchmark")
        
        all_results = []
        
        # Benchmark contract generation
        if 'prompts' in test_data:
            gen_results = await self.benchmark_contract_generation(
                generator, 
                test_data['prompts']
            )
            all_results.extend(gen_results)
        
        # Benchmark contract auditing
        if 'contract_codes' in test_data:
            audit_results = await self.benchmark_contract_auditing(
                auditor, 
                test_data['contract_codes']
            )
            all_results.extend(audit_results)
        
        # Benchmark AI providers
        if 'ai_providers' in test_data and 'test_prompt' in test_data:
            provider_results = await self.benchmark_ai_providers(
                generator, 
                test_data['test_prompt'],
                test_data['ai_providers']
            )
            all_results.extend(provider_results)
        
        # Benchmark network operations
        if 'networks' in test_data:
            network_results = await self.benchmark_network_operations(
                deployer, 
                test_data['networks']
            )
            all_results.extend(network_results)
        
        # Save results
        self.save_results(all_results)
        
        logger.info(f"Comprehensive benchmark completed. {len(all_results)} tests executed.")
        return all_results

# Example usage and test data
async def main():
    """Example usage of the performance benchmark."""
    benchmark = PerformanceBenchmark()
    
    # Example test data
    test_data = {
        'prompts': [
            "Create a simple ERC20 token",
            "Create a DeFi vault contract",
            "Create a governance contract",
            "Create an NFT contract",
            "Create a staking contract"
        ],
        'contract_codes': [
            "pragma solidity ^0.8.0; contract Test1 { string public name = \"Test1\"; }",
            "pragma solidity ^0.8.0; contract Test2 { string public name = \"Test2\"; }",
            "pragma solidity ^0.8.0; contract Test3 { string public name = \"Test3\"; }"
        ],
        'ai_providers': ['openai', 'google', 'anthropic'],
        'test_prompt': "Create a simple ERC20 token",
        'networks': ['hyperion', 'metis', 'lazai']
    }
    
    # Run benchmark (would need actual instances)
    # results = await benchmark.run_comprehensive_benchmark(generator, auditor, deployer, test_data)
    
    print("Performance benchmark system ready!")

if __name__ == "__main__":
    asyncio.run(main())
