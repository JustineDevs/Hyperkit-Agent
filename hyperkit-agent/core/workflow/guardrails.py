"""
Smart Guardrails & Escalation System
Implements guardrails, escalation, and user-friendly error messages.
"""

import logging
import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import os

logger = logging.getLogger(__name__)


class Guardrails:
    """
    Smart guardrails system that implements escalation, notifications,
    and user-friendly error messages after max retries.
    """
    
    def __init__(self, workspace_dir: Path, config: Optional[Dict[str, Any]] = None):
        """
        Initialize guardrails system.
        
        Args:
            workspace_dir: Base workspace directory
            config: Optional configuration dict with guardrail settings
        """
        self.workspace_dir = Path(workspace_dir)
        self.config = config or {}
        
        # Configuration with defaults
        self.max_retries_per_stage = self.config.get('max_retries_per_stage', 3)
        self.escalation_webhook_url = self.config.get('escalation_webhook_url')
        self.pause_on_max_retries = self.config.get('pause_on_max_retries', False)
        self.enable_escalation = self.config.get('enable_escalation', True)
    
    def check_retry_limit(self, stage: str, retry_count: int) -> bool:
        """
        Check if retry limit has been exceeded.
        
        Args:
            stage: Stage name
            retry_count: Current retry count
            
        Returns:
            True if limit exceeded, False otherwise
        """
        return retry_count >= self.max_retries_per_stage
    
    def escalate(self, stage: str, error: str, context: Dict[str, Any], diagnostic_path: Optional[Path] = None):
        """
        Escalate error after max retries exceeded.
        
        Args:
            stage: Stage that failed
            error: Error message
            context: Workflow context dictionary
            diagnostic_path: Path to diagnostic bundle
        """
        if not self.enable_escalation:
            return
        
        escalation_info = {
            "timestamp": datetime.utcnow().isoformat(),
            "stage": stage,
            "error": error,
            "workflow_id": context.get('workflow_id', 'unknown'),
            "retry_count": context.get('retry_attempts', {}).get(stage, 0),
            "diagnostic_bundle": str(diagnostic_path) if diagnostic_path else None,
            "user_prompt": context.get('user_prompt', '')[:200],  # Truncate
        }
        
        # Log escalation
        logger.error(f"🚨 ESCALATION: {stage} failed after {escalation_info['retry_count']} retries")
        logger.error(f"   Error: {error}")
        if diagnostic_path:
            logger.error(f"   Diagnostic bundle: {diagnostic_path}")
        
        # Save escalation log
        self._save_escalation_log(escalation_info)
        
        # Send webhook notification if configured
        if self.escalation_webhook_url:
            self._send_webhook_notification(escalation_info)
        
        # Pause if configured
        if self.pause_on_max_retries:
            logger.warning("⏸️  Workflow paused - manual review required")
            logger.warning("   Set pause_on_max_retries=false in config to disable")
    
    def get_user_friendly_error(self, stage: str, error: str, error_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate user-friendly error message with actionable suggestions.
        
        Args:
            stage: Stage that failed
            error: Error message
            error_type: Optional error type
            
        Returns:
            Dictionary with friendly message and suggestions
        """
        suggestions = []
        friendly_message = ""
        
        # Stage-specific suggestions
        if stage == "generation":
            friendly_message = "Contract generation failed. This might be due to:"
            suggestions = [
                "Check your prompt for typos or unclear requirements",
                "Try reformulating your prompt with more specific technical details",
                "Ensure you've specified the contract type (ERC20, ERC721, DeFi, etc.)",
                "Upload a sample template to IPFS for best results with similar contracts"
            ]
        elif stage == "compilation":
            friendly_message = "Contract compilation failed. Common issues:"
            suggestions = [
                "Check the diagnostic bundle for detailed compilation errors",
                "Verify all imports are using OpenZeppelin v5 compatible paths",
                "Ensure Solidity version is ^0.8.24 or compatible",
                "Check for variable shadowing or other Solidity syntax issues"
            ]
        elif stage == "dependency_resolution":
            friendly_message = "Dependency resolution failed. Try:"
            suggestions = [
                "Verify all required dependencies are available",
                "Check network connectivity if fetching from external sources",
                "Ensure Foundry remappings are correctly configured",
                "Review the diagnostic bundle for specific dependency errors"
            ]
        elif stage == "deployment":
            friendly_message = "Contract deployment failed. Possible causes:"
            suggestions = [
                "Check your wallet has sufficient funds for gas",
                "Verify the network RPC endpoint is accessible",
                "Ensure the contract compiled successfully before deployment",
                "Review deployment logs in the diagnostic bundle"
            ]
        else:
            friendly_message = f"Workflow stage '{stage}' failed."
            suggestions = [
                "Check the diagnostic bundle for detailed error information",
                "Review the error message above for specific issues",
                "Try running the workflow again with --verbose for more details"
            ]
        
        # Error-type specific suggestions
        if error_type:
            if 'pragma' in error_type.lower() or 'missing_pragma' in error_type.lower():
                suggestions.insert(0, "Ensure your prompt specifies 'pragma solidity ^0.8.24;' requirement")
            elif 'shadow' in error_type.lower():
                suggestions.insert(0, "Variable shadowing detected - ensure constructor parameters don't shadow state variables")
            elif 'import' in error_type.lower():
                suggestions.insert(0, "Import error - verify all OpenZeppelin imports use v5 paths")
        
        return {
            "friendly_message": friendly_message,
            "suggestions": suggestions,
            "error": error,
            "stage": stage,
            "help_text": "For more help, check the diagnostic bundle or documentation at docs/"
        }
    
    def _save_escalation_log(self, escalation_info: Dict[str, Any]):
        """Save escalation to log file"""
        try:
            escalation_dir = self.workspace_dir / "logs" / "escalations"
            escalation_dir.mkdir(parents=True, exist_ok=True)
            
            log_file = escalation_dir / f"escalation_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(escalation_info, f, indent=2)
            
            logger.debug(f"Escalation log saved: {log_file}")
        except Exception as e:
            logger.warning(f"Failed to save escalation log: {e}")
    
    def _send_webhook_notification(self, escalation_info: Dict[str, Any]):
        """Send webhook notification (Slack/Discord)"""
        try:
            import aiohttp
            import asyncio
            
            # Format webhook payload
            payload = {
                "text": f"🚨 HyperAgent Escalation: {escalation_info['stage']} failed",
                "attachments": [
                    {
                        "color": "danger",
                        "fields": [
                            {"title": "Stage", "value": escalation_info['stage'], "short": True},
                            {"title": "Workflow ID", "value": escalation_info['workflow_id'], "short": True},
                            {"title": "Error", "value": escalation_info['error'][:500], "short": False},
                            {"title": "Retry Count", "value": str(escalation_info['retry_count']), "short": True},
                        ]
                    }
                ]
            }
            
            # Send async webhook (non-blocking)
            async def send_webhook():
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.post(
                            self.escalation_webhook_url,
                            json=payload,
                            timeout=aiohttp.ClientTimeout(total=5)
                        ) as response:
                            if response.status == 200:
                                logger.info("✅ Webhook notification sent successfully")
                            else:
                                logger.warning(f"Webhook notification failed: {response.status}")
                except Exception as e:
                    logger.debug(f"Webhook notification error: {e}")
            
            # Try to send (don't block if it fails)
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If loop is running, schedule as task
                    asyncio.create_task(send_webhook())
                else:
                    loop.run_until_complete(send_webhook())
            except Exception as e:
                logger.debug(f"Failed to send webhook: {e}")
                
        except ImportError:
            logger.debug("aiohttp not available for webhook notifications")
        except Exception as e:
            logger.debug(f"Webhook notification failed: {e}")

