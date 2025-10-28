"""
Report Aggregation for Batch Audits

Aggregates multiple audit results into summary statistics and insights.
"""

import logging
from typing import Dict, Any, List
from collections import defaultdict

logger = logging.getLogger(__name__)


class ReportAggregator:
    """Aggregates multiple audit reports into summary statistics"""
    
    def aggregate(self, audit_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Aggregate multiple audit results into summary.
        
        Args:
            audit_results: List of individual audit results
            
        Returns:
            Aggregated summary with statistics and insights
        """
        if not audit_results:
            return {
                'total_contracts': 0,
                'message': 'No audit results to aggregate'
            }
        
        logger.info(f"Aggregating {len(audit_results)} audit results")
        
        # Initialize aggregation structures
        severity_counts = defaultdict(int)
        tool_usage = defaultdict(int)
        finding_types = defaultdict(int)
        total_findings = 0
        all_findings = []
        
        # Aggregate data
        for result in audit_results:
            # Count severity levels
            severity = result.get('severity', 'unknown')
            severity_counts[severity] += 1
            
            # Count tools used
            tools_used = result.get('tools_used', [])
            for tool in tools_used:
                tool_usage[tool] += 1
            
            # Aggregate findings
            findings = result.get('findings', [])
            total_findings += len(findings)
            all_findings.extend(findings)
            
            # Count finding types
            for finding in findings:
                finding_type = finding.get('type', 'unknown')
                finding_types[finding_type] += 1
        
        # Calculate statistics
        avg_findings_per_contract = total_findings / len(audit_results)
        
        # Identify most common issues
        top_issues = sorted(
            finding_types.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        # Calculate risk distribution
        risk_distribution = {
            'critical': severity_counts.get('critical', 0),
            'high': severity_counts.get('high', 0),
            'medium': severity_counts.get('medium', 0),
            'low': severity_counts.get('low', 0),
            'info': severity_counts.get('info', 0),
            'safe': severity_counts.get('safe', 0)
        }
        
        # Calculate overall risk score
        risk_score = self._calculate_risk_score(risk_distribution, len(audit_results))
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            severity_counts,
            finding_types,
            len(audit_results)
        )
        
        summary = {
            'total_contracts': len(audit_results),
            'total_findings': total_findings,
            'avg_findings_per_contract': round(avg_findings_per_contract, 2),
            'severity_distribution': dict(severity_counts),
            'risk_distribution': risk_distribution,
            'risk_score': risk_score,
            'tool_usage': dict(tool_usage),
            'top_issues': [
                {'type': issue, 'count': count} 
                for issue, count in top_issues
            ],
            'recommendations': recommendations,
            'summary_text': self._generate_summary_text(
                len(audit_results),
                risk_distribution,
                risk_score
            )
        }
        
        logger.info(f"Aggregation complete: Risk score {risk_score}/100")
        
        return summary
    
    def _calculate_risk_score(
        self,
        risk_distribution: Dict[str, int],
        total_contracts: int
    ) -> float:
        """
        Calculate overall risk score (0-100).
        Higher score = higher risk
        """
        weights = {
            'critical': 50,
            'high': 30,
            'medium': 15,
            'low': 5,
            'info': 1,
            'safe': 0
        }
        
        weighted_sum = sum(
            count * weights.get(severity, 0)
            for severity, count in risk_distribution.items()
        )
        
        # Normalize to 0-100 scale
        max_possible = total_contracts * weights['critical']
        risk_score = (weighted_sum / max_possible * 100) if max_possible > 0 else 0
        
        return round(min(risk_score, 100), 2)
    
    def _generate_recommendations(
        self,
        severity_counts: Dict[str, int],
        finding_types: Dict[str, int],
        total_contracts: int
    ) -> List[str]:
        """Generate actionable recommendations based on findings"""
        recommendations = []
        
        # Critical/High severity recommendations
        if severity_counts.get('critical', 0) > 0:
            recommendations.append(
                f"🔴 URGENT: {severity_counts['critical']} contracts with CRITICAL issues - "
                "Address immediately before deployment"
            )
        
        if severity_counts.get('high', 0) > 0:
            recommendations.append(
                f"⚠️  {severity_counts['high']} contracts with HIGH severity issues - "
                "Resolve before mainnet deployment"
            )
        
        # Medium severity recommendations
        if severity_counts.get('medium', 0) > total_contracts * 0.5:
            recommendations.append(
                f"📋 {severity_counts['medium']} contracts with MEDIUM issues - "
                "Review and fix where possible"
            )
        
        # Common issue recommendations
        top_issues = sorted(finding_types.items(), key=lambda x: x[1], reverse=True)[:3]
        if top_issues:
            issue_names = [issue[0] for issue in top_issues]
            recommendations.append(
                f"🔍 Most common issues: {', '.join(issue_names)} - "
                "Consider systematic fixes across all contracts"
            )
        
        # General recommendations
        safe_count = severity_counts.get('safe', 0)
        if safe_count == total_contracts:
            recommendations.append(
                "✅ All contracts passed security audit - Ready for deployment"
            )
        elif safe_count / total_contracts > 0.7:
            recommendations.append(
                f"✅ Majority of contracts ({safe_count}/{total_contracts}) are secure - "
                "Focus on fixing remaining issues"
            )
        
        return recommendations
    
    def _generate_summary_text(
        self,
        total_contracts: int,
        risk_distribution: Dict[str, int],
        risk_score: float
    ) -> str:
        """Generate human-readable summary text"""
        critical = risk_distribution.get('critical', 0)
        high = risk_distribution.get('high', 0)
        safe = risk_distribution.get('safe', 0)
        
        if risk_score >= 70:
            risk_level = "HIGH RISK"
            emoji = "🔴"
        elif risk_score >= 40:
            risk_level = "MEDIUM RISK"
            emoji = "🟡"
        else:
            risk_level = "LOW RISK"
            emoji = "🟢"
        
        summary = f"{emoji} {risk_level} (Score: {risk_score}/100)\n\n"
        summary += f"Audited {total_contracts} contracts:\n"
        summary += f"- {critical} with CRITICAL issues\n"
        summary += f"- {high} with HIGH severity issues\n"
        summary += f"- {safe} contracts are secure\n"
        
        if critical > 0 or high > 0:
            summary += f"\n⚠️  Action required for {critical + high} contracts before deployment"
        else:
            summary += "\n✅ No critical issues found"
        
        return summary

