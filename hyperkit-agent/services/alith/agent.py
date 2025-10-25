"""
HyperKit Alith Agent Wrapper
Provides AI-powered smart contract security analysis using Alith SDK
"""
import logging
from typing import Dict, Any, Optional
import json

logger = logging.getLogger(__name__)

try:
    from alith import Agent
    ALITH_AVAILABLE = True
except ImportError:
    logger.warning("Alith SDK not installed. AI-powered auditing will be unavailable.")
    ALITH_AVAILABLE = False


class HyperKitAlithAgent:
    """Wrapper for Alith AI Agent with HyperKit-specific configuration"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Alith agent for smart contract analysis
        
        Args:
            config: Configuration dictionary with keys:
                   - model: LLM model name (default: "gpt-4o-mini")
                   - settlement: Enable on-chain settlement (default: False)
                   - preamble: Custom system prompt
        """
        if not ALITH_AVAILABLE:
            raise ImportError("Alith SDK is not installed. Install with: pip install alith")
        
        self.config = config or {}
        self.model = self.config.get("model", "gpt-4o-mini")
        self.settlement = self.config.get("settlement", False)
        
        try:
            self.agent = Agent(
                name="HyperKit Security Agent",
                model=self.model,
                preamble=self.config.get("preamble", self._default_preamble()),
                settlement=self.settlement
            )
            logger.info(f"✅ Alith Agent initialized (model={self.model}, settlement={self.settlement})")
        except Exception as e:
            logger.error(f"Failed to initialize Alith agent: {e}")
            raise
    
    def _default_preamble(self) -> str:
        """Default system prompt for security auditing"""
        return """You are an expert smart contract security auditor for the HyperKit Agent.

Your expertise includes:
- Solidity security analysis and vulnerability detection
- DeFi protocol auditing (lending, DEX, staking, governance)
- Gas optimization and best practices
- Common attack vectors (reentrancy, overflow, access control, etc.)
- ERC standard compliance

When analyzing contracts, always:
1. Identify vulnerabilities with severity levels (CRITICAL/HIGH/MEDIUM/LOW)
2. Explain the security impact of each issue
3. Provide specific code recommendations
4. Give an overall risk assessment (0-100 scale)

Prioritize security over gas optimization.
Provide clear, actionable recommendations.
"""
    
    async def audit_contract(self, contract_code: str) -> Dict[str, Any]:
        """
        Perform AI-powered security audit of smart contract
        
        Args:
            contract_code: Solidity source code to audit
            
        Returns:
            Dictionary containing:
            - vulnerabilities: List of detected issues
            - risk_score: Overall risk (0-100)
            - recommendations: List of fixes
            - confidence: Analysis confidence (0-1)
        """
        if not ALITH_AVAILABLE:
            return {
                "success": False,
                "error": "Alith SDK not available",
                "vulnerabilities": [],
                "risk_score": 0,
                "confidence": 0.0
            }
        
        try:
            prompt = f"""Perform a comprehensive security audit of this Solidity contract:

```solidity
{contract_code}
```

Analyze for:
1. **Critical vulnerabilities**: reentrancy, integer overflow/underflow, unchecked external calls
2. **High-severity issues**: access control, logic errors, gas griefing
3. **Medium-severity issues**: code quality, best practices, optimization
4. **Low-severity issues**: style, documentation

Provide your response in JSON format:
{{
  "vulnerabilities": [
    {{
      "severity": "CRITICAL|HIGH|MEDIUM|LOW",
      "title": "Issue title",
      "description": "Detailed explanation",
      "location": "Function or line reference",
      "recommendation": "How to fix"
    }}
  ],
  "risk_score": 0-100,
  "summary": "Overall assessment",
  "recommendations": ["List of fixes"]
}}
"""
            
            logger.info("Running Alith AI security analysis...")
            response = self.agent.prompt(prompt)
            
            # Parse AI response
            result = self._parse_audit_response(response)
            result["confidence"] = 0.85  # AI analysis confidence
            result["success"] = True
            
            logger.info(f"Alith analysis complete: Risk={result.get('risk_score')}/100")
            return result
            
        except Exception as e:
            logger.error(f"Alith audit failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "vulnerabilities": [],
                "risk_score": 0,
                "confidence": 0.0
            }
    
    def _parse_audit_response(self, response: str) -> Dict[str, Any]:
        """Parse AI response into structured format"""
        try:
            # Try to extract JSON from response
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
            elif "{" in response and "}" in response:
                json_start = response.find("{")
                json_end = response.rfind("}") + 1
                json_str = response[json_start:json_end]
            else:
                # Fallback: return raw response
                return {
                    "vulnerabilities": [],
                    "risk_score": 50,
                    "summary": response,
                    "recommendations": []
                }
            
            parsed = json.loads(json_str)
            return parsed
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse AI response as JSON: {e}")
            return {
                "vulnerabilities": [],
                "risk_score": 50,
                "summary": response,
                "recommendations": [],
                "parse_error": str(e)
            }
    
    async def query(self, question: str) -> str:
        """
        Natural language query about smart contracts or DeFi
        
        Args:
            question: Natural language question
            
        Returns:
            AI response string
        """
        if not ALITH_AVAILABLE:
            return "Alith SDK not available"
        
        try:
            response = self.agent.prompt(question)
            return response
        except Exception as e:
            logger.error(f"Alith query failed: {e}")
            return f"Error: {str(e)}"


def is_alith_available() -> bool:
    """Check if Alith SDK is installed and functional"""
    return ALITH_AVAILABLE

