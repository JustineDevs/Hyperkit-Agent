#!/usr/bin/env python3
"""
Repository Health Dashboard
Tracks Real vs Partial vs Stub file counts, updates monthly
"""

import os
import json
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass


@dataclass
class FileHealthMetrics:
    """File health metrics"""
    total_files: int = 0
    real_files: int = 0
    partial_files: int = 0
    stub_files: int = 0
    documentation_files: int = 0
    test_files: int = 0
    config_files: int = 0
    script_files: int = 0


class RepoHealthDashboard:
    """Repository health dashboard and metrics tracker"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.metrics = FileHealthMetrics()
        self.health_report = {
            "timestamp": datetime.now().isoformat(),
            "overall_health_score": 0.0,
            "metrics": {},
            "recommendations": [],
            "trends": {}
        }
    
    def analyze_repository_health(self) -> Dict[str, Any]:
        """Analyze overall repository health"""
        
        print("Analyzing Repository Health...")
        print("=" * 60)
        
        # Analyze different file categories
        self._analyze_python_files()
        self._analyze_documentation_files()
        self._analyze_test_files()
        self._analyze_config_files()
        self._analyze_script_files()
        
        # Calculate health score
        self._calculate_health_score()
        
        # Generate recommendations
        self._generate_recommendations()
        
        # Save report
        self._save_health_report()
        
        return self.health_report
    
    def _analyze_python_files(self):
        """Analyze Python files for completeness"""
        python_files = list(self.project_root.rglob("*.py"))
        
        real_count = 0
        partial_count = 0
        stub_count = 0
        
        for py_file in python_files:
            if self._is_test_file(py_file):
                continue
                
            content = py_file.read_text(encoding='utf-8', errors='ignore')
            
            if self._is_real_implementation(content):
                real_count += 1
            elif self._is_partial_implementation(content):
                partial_count += 1
            else:
                stub_count += 1
        
        self.metrics.total_files += len(python_files)
        self.metrics.real_files += real_count
        self.metrics.partial_files += partial_count
        self.metrics.stub_files += stub_count
        
        self.health_report["metrics"]["python_files"] = {
            "total": len(python_files),
            "real": real_count,
            "partial": partial_count,
            "stub": stub_count,
            "completion_rate": (real_count / len(python_files)) * 100 if python_files else 0
        }
    
    def _analyze_documentation_files(self):
        """Analyze documentation files"""
        doc_files = list(self.project_root.rglob("*.md"))
        
        self.metrics.documentation_files = len(doc_files)
        self.metrics.total_files += len(doc_files)
        
        # Analyze documentation quality
        complete_docs = 0
        incomplete_docs = 0
        
        for doc_file in doc_files:
            content = doc_file.read_text(encoding='utf-8', errors='ignore')
            
            if self._is_complete_documentation(content):
                complete_docs += 1
            else:
                incomplete_docs += 1
        
        self.health_report["metrics"]["documentation"] = {
            "total": len(doc_files),
            "complete": complete_docs,
            "incomplete": incomplete_docs,
            "completion_rate": (complete_docs / len(doc_files)) * 100 if doc_files else 0
        }
    
    def _analyze_test_files(self):
        """Analyze test files"""
        test_files = []
        
        # Find test files (only files, not directories)
        for pattern in ["test_*.py", "*_test.py"]:
            test_files.extend(self.project_root.rglob(pattern))
        
        # Also check tests directory for Python files
        tests_dir = self.project_root / "tests"
        if tests_dir.exists() and tests_dir.is_dir():
            test_files.extend(tests_dir.rglob("*.py"))
        
        self.metrics.test_files = len(test_files)
        self.metrics.total_files += len(test_files)
        
        # Analyze test coverage
        test_coverage = self._estimate_test_coverage(test_files)
        
        self.health_report["metrics"]["tests"] = {
            "total": len(test_files),
            "estimated_coverage": test_coverage,
            "quality_score": min(test_coverage, 100)
        }
    
    def _analyze_config_files(self):
        """Analyze configuration files"""
        config_patterns = ["*.yaml", "*.yml", "*.json", "*.toml", "*.ini", "*.cfg", "*.env*"]
        config_files = []
        
        for pattern in config_patterns:
            config_files.extend(self.project_root.rglob(pattern))
        
        self.metrics.config_files = len(config_files)
        self.metrics.total_files += len(config_files)
        
        self.health_report["metrics"]["config_files"] = {
            "total": len(config_files),
            "types": self._categorize_config_files(config_files)
        }
    
    def _analyze_script_files(self):
        """Analyze script files"""
        script_patterns = ["*.sh", "*.bat", "*.ps1", "scripts/"]
        script_files = []
        
        for pattern in script_patterns:
            script_files.extend(self.project_root.rglob(pattern))
        
        self.metrics.script_files = len(script_files)
        self.metrics.total_files += len(script_files)
        
        self.health_report["metrics"]["scripts"] = {
            "total": len(script_files),
            "executable": self._count_executable_scripts(script_files)
        }
    
    def _is_real_implementation(self, content: str) -> bool:
        """Check if file contains real implementation"""
        # Check for actual implementation patterns
        implementation_patterns = [
            r"def\s+\w+.*:",
            r"class\s+\w+.*:",
            r"async\s+def\s+\w+.*:",
            r"return\s+",
            r"if\s+.*:",
            r"for\s+.*:",
            r"while\s+.*:",
            r"try:",
            r"except\s+.*:",
            r"raise\s+",
            r"import\s+\w+",
            r"from\s+\w+\s+import"
        ]
        
        pattern_count = sum(1 for pattern in implementation_patterns if re.search(pattern, content))
        
        # Check for stub patterns
        stub_patterns = [
            r"pass\s*$",
            r"raise\s+NotImplementedError",
            r"TODO",
            r"FIXME",
            r"XXX",
            r"placeholder",
            r"not implemented"
        ]
        
        stub_count = sum(1 for pattern in stub_patterns if re.search(pattern, content, re.IGNORECASE))
        
        # Real implementation if has implementation patterns and few stub patterns
        return pattern_count >= 3 and stub_count <= 2
    
    def _is_partial_implementation(self, content: str) -> bool:
        """Check if file contains partial implementation"""
        implementation_patterns = [
            r"def\s+\w+.*:",
            r"class\s+\w+.*:",
            r"return\s+",
            r"if\s+.*:"
        ]
        
        pattern_count = sum(1 for pattern in implementation_patterns if re.search(pattern, content))
        
        # Partial if has some implementation but not enough for "real"
        return 1 <= pattern_count < 3
    
    def _is_test_file(self, file_path: Path) -> bool:
        """Check if file is a test file"""
        test_indicators = [
            "test_",
            "_test.py",
            "/tests/",
            "pytest",
            "unittest"
        ]
        
        return any(indicator in str(file_path) for indicator in test_indicators)
    
    def _is_complete_documentation(self, content: str) -> bool:
        """Check if documentation is complete"""
        # Check for documentation completeness indicators
        completeness_patterns = [
            r"#\s+\w+",  # Headers
            r"##\s+\w+",  # Subheaders
            r"```",  # Code blocks
            r"http[s]?://",  # Links
            r"Last Updated",
            r"Version:",
            r"Status:"
        ]
        
        pattern_count = sum(1 for pattern in completeness_patterns if re.search(pattern, content))
        
        # Complete if has multiple documentation elements
        return pattern_count >= 5
    
    def _estimate_test_coverage(self, test_files: List[Path]) -> float:
        """Estimate test coverage based on test file analysis"""
        if not test_files:
            return 0.0
        
        total_tests = 0
        for test_file in test_files:
            try:
                if test_file.is_file():
                    content = test_file.read_text(encoding='utf-8', errors='ignore')
                    # Count test functions
                    test_functions = len(re.findall(r"def\s+test_\w+", content))
                    total_tests += test_functions
            except (PermissionError, OSError):
                # Skip files that can't be read
                continue
        
        # Rough estimation: assume each test covers some functionality
        # This is a simplified estimation
        estimated_coverage = min(total_tests * 5, 100)  # Max 100%
        return estimated_coverage
    
    def _categorize_config_files(self, config_files: List[Path]) -> Dict[str, int]:
        """Categorize configuration files by type"""
        categories = {}
        
        for config_file in config_files:
            ext = config_file.suffix.lower()
            categories[ext] = categories.get(ext, 0) + 1
        
        return categories
    
    def _count_executable_scripts(self, script_files: List[Path]) -> int:
        """Count executable script files"""
        executable_count = 0
        
        for script_file in script_files:
            if script_file.is_file():
                # Check if file has executable permissions (simplified check)
                try:
                    if os.access(script_file, os.X_OK):
                        executable_count += 1
                except:
                    pass
        
        return executable_count
    
    def _calculate_health_score(self):
        """Calculate overall repository health score"""
        if self.metrics.total_files == 0:
            self.health_report["overall_health_score"] = 0.0
            return
        
        # Weight different metrics
        implementation_score = (self.metrics.real_files / self.metrics.total_files) * 40
        documentation_score = min(self.metrics.documentation_files / 50, 1.0) * 30
        test_score = min(self.metrics.test_files / 20, 1.0) * 20
        config_score = min(self.metrics.config_files / 10, 1.0) * 10
        
        total_score = implementation_score + documentation_score + test_score + config_score
        self.health_report["overall_health_score"] = min(total_score, 100.0)
    
    def _generate_recommendations(self):
        """Generate health improvement recommendations"""
        recommendations = []
        
        # Implementation recommendations
        if self.metrics.stub_files > self.metrics.real_files:
            recommendations.append("High number of stub files detected - consider implementing core functionality")
        
        if self.metrics.partial_files > 0:
            recommendations.append("Partial implementations found - complete unfinished features")
        
        # Documentation recommendations
        if self.metrics.documentation_files < 20:
            recommendations.append("Low documentation count - add more comprehensive documentation")
        
        # Test recommendations
        if self.metrics.test_files < 10:
            recommendations.append("Insufficient test coverage - add more test files")
        
        # Overall recommendations
        health_score = self.health_report["overall_health_score"]
        if health_score < 50:
            recommendations.append("Overall health score is low - focus on core implementation and testing")
        elif health_score < 80:
            recommendations.append("Good progress - focus on documentation and edge cases")
        else:
            recommendations.append("Excellent repository health - maintain current standards")
        
        self.health_report["recommendations"] = recommendations
    
    def _save_health_report(self):
        """Save health report to file"""
        reports_dir = self.project_root / "hyperkit-agent" / "REPORTS"
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = reports_dir / f"repo_health_dashboard_{timestamp}.json"
        
        report_file.write_text(json.dumps(self.health_report, indent=2))
        
        print(f"Health report saved: {report_file}")
    
    def print_health_summary(self):
        """Print health summary to console"""
        print("\n" + "=" * 60)
        print("Repository Health Summary")
        print("=" * 60)
        
        print(f"Overall Health Score: {self.health_report['overall_health_score']:.1f}/100")
        print(f"Total Files Analyzed: {self.metrics.total_files}")
        print(f"Real Implementations: {self.metrics.real_files}")
        print(f"Partial Implementations: {self.metrics.partial_files}")
        print(f"Stub Files: {self.metrics.stub_files}")
        print(f"Documentation Files: {self.metrics.documentation_files}")
        print(f"Test Files: {self.metrics.test_files}")
        print(f"Config Files: {self.metrics.config_files}")
        print(f"Script Files: {self.metrics.script_files}")
        
        print("\nRecommendations:")
        for rec in self.health_report["recommendations"]:
            print(f"  - {rec}")
        
        print("=" * 60)


def main():
    """Main entry point"""
    project_root = Path(__file__).parent.parent.parent
    dashboard = RepoHealthDashboard(project_root)
    
    # Analyze repository health
    health_report = dashboard.analyze_repository_health()
    
    # Print summary
    dashboard.print_health_summary()
    
    return health_report


if __name__ == "__main__":
    main()
