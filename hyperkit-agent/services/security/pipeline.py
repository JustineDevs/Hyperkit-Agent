"""
Security Analysis Pipeline
Orchestrates all security checks for comprehensive transaction analysis

Integrates:
- Transaction Simulation (Pocket Universe)
- Address Reputation (GoPlus Security)
- Phishing Detection (Scam Sniffer)
- Token Approval Tracking (Revoke.cash)
- ML Risk Scoring
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from .simulator import TransactionSimulator
from .reputation.database import ReputationDatabase
from .reputation.risk_calculator import RiskCalculator
from .phishing.detector import PhishingDetector
from .approvals.tracker import ApprovalTracker
from .ml.risk_scorer import MLRiskScorer

logger = logging.getLogger(__name__)


class SecurityAnalysisPipeline:
    """
    Comprehensive security analysis pipeline for wallet protection.
    
    Combines multiple security tools to provide layered protection against:
    - Phishing attacks
    - Wallet drainers
    - Approval exploits
    - MEV/sandwich attacks
    - Malicious contracts
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize security analysis pipeline.

        Args:
            config: Configuration dictionary with component settings
        """
        self.config = config or {}
        
        # Initialize all security components
        self.simulator = TransactionSimulator(self.config.get("simulation", {}))
        self.reputation_db = ReputationDatabase(self.config.get("reputation_seed_file"))
        self.risk_calculator = RiskCalculator(self.config.get("risk_weights"))
        self.phishing_detector = PhishingDetector()
        self.approval_tracker = ApprovalTracker()
        self.ml_scorer = MLRiskScorer(self.config.get("ml_model_path"))
        
        self.enabled_checks = self.config.get("enabled_checks", {
            "simulation": True,
            "reputation": True,
            "phishing": True,
            "approval": True,
            "ml": True
        })
        
        logger.info("SecurityAnalysisPipeline initialized with all components")

    async def analyze_transaction(
        self, 
        tx_params: Dict[str, Any], 
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Perform comprehensive security analysis of a transaction.

        Args:
            tx_params: Transaction parameters {to, from, data, value, network}
            context: Additional context {url, user_agent, referrer}

        Returns:
            {
                "risk_score": 0-100,
                "risk_level": "low/medium/high/critical",
                "recommendation": "allow/caution/warn/block",
                "warnings": [list of warning messages],
                "analysis_results": {detailed results from each component},
                "timestamp": analysis timestamp
            }
        """
        start_time = datetime.now()
        context = context or {}
        
        logger.info(f"Starting security analysis for transaction to: {tx_params.get('to', 'N/A')}")
        
        analysis_results = {
            "timestamp": start_time.isoformat(),
            "transaction": tx_params,
            "context": context,
            "checks_performed": [],
            "warnings": [],
            "scores": {}
        }
        
        try:
            # Run all enabled security checks in parallel for speed
            tasks = []
            
            if self.enabled_checks.get("simulation"):
                tasks.append(("simulation", self._run_simulation(tx_params)))
            
            if self.enabled_checks.get("reputation"):
                tasks.append(("reputation", self._run_reputation_check(tx_params)))
            
            if self.enabled_checks.get("phishing") and context.get("url"):
                tasks.append(("phishing", self._run_phishing_check(context["url"])))
            
            if self.enabled_checks.get("approval"):
                tasks.append(("approval", self._run_approval_check(tx_params)))
            
            if self.enabled_checks.get("ml"):
                tasks.append(("ml", self._run_ml_check(tx_params)))
            
            # Execute all checks concurrently
            check_names, check_tasks = zip(*tasks) if tasks else ([], [])
            if check_tasks:
                results = await asyncio.gather(*check_tasks, return_exceptions=True)
                
                for name, result in zip(check_names, results):
                    if isinstance(result, Exception):
                        logger.error(f"{name} check failed: {result}")
                        analysis_results[name] = {"error": str(result)}
                    else:
                        analysis_results[name] = result
                        analysis_results["checks_performed"].append(name)
                        
                        # Collect warnings
                        if result.get("warnings"):
                            analysis_results["warnings"].extend(result["warnings"])
            
            # Calculate aggregate risk score
            risk_analysis = self._calculate_aggregate_risk(analysis_results)
            
            # Add execution time
            execution_time = (datetime.now() - start_time).total_seconds()
            risk_analysis["execution_time"] = execution_time
            risk_analysis["analysis_results"] = analysis_results
            
            logger.info(f"Security analysis complete: {risk_analysis['risk_level']} risk ({execution_time:.2f}s)")
            
            return risk_analysis
            
        except Exception as e:
            logger.error(f"Security analysis pipeline failed: {e}")
            return self._error_result(str(e), analysis_results)

    async def _run_simulation(self, tx_params: Dict[str, Any]) -> Dict[str, Any]:
        """Run transaction simulation check"""
        try:
            network = tx_params.get("network", "hyperion")
            result = await self.simulator.simulate_transaction(tx_params, network)
            
            # Convert simulation result to score
            if result["success"]:
                # Lower score if warnings detected
                score = 100 - (len(result.get("warnings", [])) * 15)
                score = max(0, score)
            else:
                score = 80  # Failed simulation = suspicious
            
            return {
                "score": score,
                "confidence": result.get("confidence", 0.0),
                "warnings": result.get("warnings", []),
                "details": result
            }
            
        except Exception as e:
            logger.error(f"Simulation check failed: {e}")
            return {"score": 50, "confidence": 0.0, "error": str(e)}

    async def _run_reputation_check(self, tx_params: Dict[str, Any]) -> Dict[str, Any]:
        """Run address reputation check"""
        try:
            to_address = tx_params.get("to")
            if not to_address:
                return {"score": 0, "confidence": 0.0}
            
            rep_result = self.reputation_db.get_risk_score(to_address)
            
            return {
                "score": rep_result["risk_score"],
                "confidence": rep_result.get("confidence", 0.75),
                "labels": rep_result.get("labels", []),
                "warnings": [f"⚠️  Address labeled as: {', '.join(rep_result.get('labels', []))}"] if rep_result["risk_score"] > 70 else [],
                "details": rep_result
            }
            
        except Exception as e:
            logger.error(f"Reputation check failed: {e}")
            return {"score": 50, "confidence": 0.0, "error": str(e)}

    async def _run_phishing_check(self, url: str) -> Dict[str, Any]:
        """Run phishing URL check"""
        try:
            phish_result = self.phishing_detector.check_url(url)
            
            # Convert risk level to score
            risk_map = {"CRITICAL": 100, "HIGH": 80, "MEDIUM": 50, "LOW": 20, "UNKNOWN": 50}
            score = risk_map.get(phish_result["risk"], 50)
            
            warnings = []
            if score >= 80:
                warnings.append(f"🚨 PHISHING RISK: {phish_result['reason']}")
            
            return {
                "score": score,
                "confidence": phish_result.get("confidence", 0.70),
                "warnings": warnings,
                "details": phish_result
            }
            
        except Exception as e:
            logger.error(f"Phishing check failed: {e}")
            return {"score": 50, "confidence": 0.0, "error": str(e)}

    async def _run_approval_check(self, tx_params: Dict[str, Any]) -> Dict[str, Any]:
        """Run token approval check"""
        try:
            approval_result = self.approval_tracker.analyze_approval(tx_params)
            
            if not approval_result.get("is_approval"):
                return {"score": 0, "confidence": 1.0}
            
            # Unlimited approval = high risk
            if approval_result.get("is_unlimited"):
                return {
                    "score": 90,
                    "confidence": 0.95,
                    "warnings": ["🚨 UNLIMITED APPROVAL DETECTED - High risk of wallet draining!"],
                    "details": approval_result
                }
            
            return {
                "score": 40,
                "confidence": 0.85,
                "warnings": ["⚠️  Token approval requested - Verify spender address"],
                "details": approval_result
            }
            
        except Exception as e:
            logger.error(f"Approval check failed: {e}")
            return {"score": 50, "confidence": 0.0, "error": str(e)}

    async def _run_ml_check(self, tx_params: Dict[str, Any]) -> Dict[str, Any]:
        """Run ML-based risk scoring"""
        try:
            to_address = tx_params.get("to")
            if not to_address:
                return {"score": 0, "confidence": 0.0}
            
            ml_result = await self.ml_scorer.calculate_risk(to_address)
            
            return {
                "score": ml_result["ml_risk_score"],
                "confidence": ml_result.get("confidence", 0.80),
                "warnings": [],
                "details": ml_result
            }
            
        except Exception as e:
            logger.error(f"ML check failed: {e}")
            return {"score": 50, "confidence": 0.0, "error": str(e)}

    def _calculate_aggregate_risk(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate final aggregate risk score"""
        try:
            # Extract scores from each component
            scores = {}
            
            for check in ["simulation", "reputation", "phishing", "approval"]:
                if check in analysis_results and "score" in analysis_results[check]:
                    scores[check] = analysis_results[check]["score"]
            
            # Use risk calculator for weighted average
            if not scores:
                return self._default_risk_result(analysis_results)
            
            risk_result = self.risk_calculator.calculate(scores)
            
            # Add warnings
            risk_result["warnings"] = analysis_results.get("warnings", [])
            
            # Add detailed explanation
            risk_result["explanation"] = self._generate_explanation(risk_result, scores)
            
            return risk_result
            
        except Exception as e:
            logger.error(f"Risk aggregation failed: {e}")
            return self._default_risk_result(analysis_results)

    def _generate_explanation(self, risk_result: Dict, scores: Dict) -> str:
        """Generate human-readable explanation of risk assessment"""
        risk_level = risk_result["risk_level"]
        risk_score = risk_result["risk_score"]
        
        explanation = [f"Overall Risk: {risk_level.upper()} ({risk_score}/100)"]
        
        if scores.get("simulation", 0) > 70:
            explanation.append("• Transaction simulation detected suspicious patterns")
        
        if scores.get("reputation", 0) > 70:
            explanation.append("• Recipient address has negative reputation")
        
        if scores.get("phishing", 0) > 70:
            explanation.append("• Potential phishing site detected")
        
        if scores.get("approval", 0) > 70:
            explanation.append("• Risky token approval requested")
        
        return "\n".join(explanation)

    def _default_risk_result(self, analysis_results: Dict) -> Dict[str, Any]:
        """Generate default risk result when calculation fails"""
        return {
            "risk_score": 50,
            "risk_level": "medium",
            "recommendation": "caution",
            "warnings": analysis_results.get("warnings", []),
            "explanation": "Unable to calculate detailed risk score"
        }

    def _error_result(self, error_msg: str, analysis_results: Dict) -> Dict[str, Any]:
        """Generate error result"""
        return {
            "risk_score": 50,
            "risk_level": "unknown",
            "recommendation": "caution",
            "warnings": [f"❌ Analysis error: {error_msg}"],
            "explanation": "Security analysis encountered an error",
            "analysis_results": analysis_results,
            "error": error_msg
        }

    def get_analysis_summary(self, result: Dict[str, Any]) -> str:
        """
        Generate human-readable summary of security analysis.

        Args:
            result: Analysis result from analyze_transaction()

        Returns:
            Formatted summary string
        """
        lines = [
            "\n" + "="*60,
            "🔒 SECURITY ANALYSIS REPORT",
            "="*60,
            "",
            f"Risk Level: {result['risk_level'].upper()}",
            f"Risk Score: {result['risk_score']}/100",
            f"Recommendation: {result['recommendation'].upper()}",
            ""
        ]
        
        if result.get("warnings"):
            lines.append("⚠️  Warnings:")
            for warning in result["warnings"]:
                lines.append(f"   {warning}")
            lines.append("")
        
        if result.get("explanation"):
            lines.append("Analysis:")
            lines.append(f"   {result['explanation']}")
            lines.append("")
        
        if result.get("execution_time"):
            lines.append(f"⏱️  Analysis Time: {result['execution_time']:.2f}s")
        
        lines.append("="*60)
        
        return "\n".join(lines)


# Example usage
async def main():
    """Example usage of SecurityAnalysisPipeline"""
    pipeline = SecurityAnalysisPipeline()
    
    # Example transaction
    tx_params = {
        "to": "0x7fF064953a29FB36F68730E5b24410Ba90659f25",
        "from": "0x1234567890123456789012345678901234567890",
        "value": 0,
        "data": "0x095ea7b3000000000000000000000000deadbeeffffffffffffffffffffffffffffff",
        "network": "hyperion"
    }
    
    context = {
        "url": "https://uniswap.org",
        "user_agent": "Mozilla/5.0"
    }
    
    result = await pipeline.analyze_transaction(tx_params, context)
    
    print(pipeline.get_analysis_summary(result))
    
    # Decision logic
    if result["recommendation"] == "block":
        print("\n🚨 TRANSACTION BLOCKED - Critical security risk detected!")
    elif result["recommendation"] == "warn":
        print("\n⚠️  HIGH RISK - User confirmation required")
    elif result["recommendation"] == "caution":
        print("\n⚠️  MEDIUM RISK - Proceed with caution")
    else:
        print("\n✅ LOW RISK - Transaction appears safe")


if __name__ == "__main__":
    asyncio.run(main())

