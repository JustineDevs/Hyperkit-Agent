"""
Production Mode Validator

Enforces strict production requirements and fails fast when dependencies are missing.
No silent fallbacks to mock implementations.
"""

import os
import logging
import subprocess
import sys
from typing import Dict, Any, List, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

class ProductionModeValidator:
    """Validates that all production dependencies are available and functional"""
    
    def __init__(self):
        self.required_dependencies = {
            'alith_sdk': {
                'package': 'alith',
                'version': '>=0.12.0',
                'test_function': self._test_alith_sdk,
                'critical': True
            },
            'foundry': {
                'command': 'forge',
                'test_function': self._test_foundry,
                'critical': True
            },
            'web3_connection': {
                'test_function': self._test_web3_connection,
                'critical': True
            },
            'ai_providers': {
                'test_function': self._test_ai_providers,
                'critical': True
            },
            'private_key': {
                'env_var': 'DEFAULT_PRIVATE_KEY',
                'test_function': self._test_private_key,
                'critical': True
            },
            'hyperion_rpc': {
                'env_var': 'HYPERION_RPC_URL',
                'test_function': self._test_hyperion_rpc,
                'critical': True
            }
        }
        
        self.validation_results = {}
        self.production_mode = False
    
    def validate_production_mode(self) -> Dict[str, Any]:
        """
        Validate all production dependencies.
        Returns comprehensive validation results.
        """
        logger.info("🔍 BRUTAL PRODUCTION MODE VALIDATION")
        logger.info("=" * 60)
        
        all_passed = True
        critical_failures = []
        warnings = []
        
        for dep_name, dep_config in self.required_dependencies.items():
            logger.info(f"Validating {dep_name}...")
            
            try:
                result = dep_config['test_function']()
                self.validation_results[dep_name] = result
                
                if result['status'] == 'success':
                    logger.info(f"✅ {dep_name}: {result.get('message', 'OK')}")
                elif result['status'] == 'warning':
                    logger.warning(f"⚠️ {dep_name}: {result.get('message', 'WARNING')}")
                    warnings.append(f"{dep_name}: {result.get('message', 'WARNING')}")
                else:
                    logger.error(f"❌ {dep_name}: {result.get('message', 'FAILED')}")
                    if dep_config.get('critical', False):
                        critical_failures.append(f"{dep_name}: {result.get('message', 'FAILED')}")
                        all_passed = False
                    else:
                        warnings.append(f"{dep_name}: {result.get('message', 'FAILED')}")
                        
            except Exception as e:
                logger.error(f"❌ {dep_name}: Validation error - {e}")
                if dep_config.get('critical', False):
                    critical_failures.append(f"{dep_name}: Validation error - {e}")
                    all_passed = False
        
        self.production_mode = all_passed
        
        if not all_passed:
            logger.error("🚨 CRITICAL FAILURES DETECTED - PRODUCTION MODE DISABLED")
            logger.error("=" * 60)
            for failure in critical_failures:
                logger.error(f"❌ {failure}")
            logger.error("=" * 60)
            logger.error("SYSTEM WILL RUN IN SAFE MODE ONLY")
            logger.error("Fix critical dependencies before attempting production operations")
        else:
            logger.info("✅ ALL CRITICAL DEPENDENCIES VALIDATED - PRODUCTION MODE ENABLED")
        
        # Store critical failures for later use
        self.critical_failures = critical_failures
        
        if warnings:
            logger.warning("⚠️ WARNINGS:")
            for warning in warnings:
                logger.warning(f"  • {warning}")
        
        return {
            'production_mode': self.production_mode,
            'critical_failures': critical_failures,
            'warnings': warnings,
            'validation_results': self.validation_results
        }
    
    def _test_alith_sdk(self) -> Dict[str, Any]:
        """Test Alith SDK availability and functionality"""
        try:
            import alith
            version = getattr(alith, '__version__', 'unknown')
            
            # Test if it's the real Alith SDK, not a mock
            # Check for core classes: Agent, LazAIClient, Tool
            required_classes = ['Agent', 'LazAIClient', 'Tool']
            missing_classes = [cls for cls in required_classes if not hasattr(alith, cls)]
            
            if missing_classes:
                return {
                    'status': 'error',
                    'message': f'Alith package found but missing required classes: {", ".join(missing_classes)}'
                }
            
            # Test basic functionality
            try:
                # Try to create an agent instance to verify it's functional
                agent = alith.Agent()
                
                # Test that agent has expected attributes
                if hasattr(agent, 'model') and hasattr(agent, 'name'):
                    return {
                        'status': 'success',
                        'message': f'Real Alith SDK {version} available and functional'
                    }
                else:
                    return {
                        'status': 'error',
                        'message': 'Alith Agent created but missing expected attributes'
                    }
            except Exception as e:
                return {
                    'status': 'error',
                    'message': f'Alith SDK installed but not functional: {e}'
                }
        except ImportError:
            return {
                'status': 'error',
                'message': 'Alith SDK not installed - install with: pip install alith>=0.12.0'
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Alith SDK error: {e}'
            }
    
    def _test_foundry(self) -> Dict[str, Any]:
        """Test Foundry installation and functionality"""
        try:
            result = subprocess.run(['forge', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                version = result.stdout.strip()
                return {
                    'status': 'success',
                    'message': f'Foundry {version} available'
                }
            else:
                return {
                    'status': 'error',
                    'message': f'Foundry command failed: {result.stderr}'
                }
        except FileNotFoundError:
            return {
                'status': 'error',
                'message': 'Foundry not found - install with: curl -L https://foundry.paradigm.xyz | bash'
            }
        except subprocess.TimeoutExpired:
            return {
                'status': 'error',
                'message': 'Foundry command timeout'
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Foundry test error: {e}'
            }
    
    def _test_web3_connection(self) -> Dict[str, Any]:
        """Test Web3 connection to Hyperion testnet"""
        try:
            from web3 import Web3
            rpc_url = os.getenv('HYPERION_RPC_URL')
            if not rpc_url:
                return {
                    'status': 'error',
                    'message': 'HYPERION_RPC_URL not set in environment'
                }
            
            w3 = Web3(Web3.HTTPProvider(rpc_url))
            if w3.is_connected():
                latest_block = w3.eth.block_number
                return {
                    'status': 'success',
                    'message': f'Connected to Hyperion testnet (block {latest_block})'
                }
            else:
                return {
                    'status': 'error',
                    'message': 'Failed to connect to Hyperion testnet'
                }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Web3 connection error: {e}'
            }
    
    def _test_ai_providers(self) -> Dict[str, Any]:
        """Test AI provider availability"""
        providers = []
        
        # Test OpenAI
        if os.getenv('OPENAI_API_KEY'):
            providers.append('OpenAI')
        
        # Test Google
        if os.getenv('GOOGLE_API_KEY'):
            providers.append('Google')
        
        # Test Anthropic
        if os.getenv('ANTHROPIC_API_KEY'):
            providers.append('Anthropic')
        
        if providers:
            return {
                'status': 'success',
                'message': f'AI providers available: {", ".join(providers)}'
            }
        else:
            return {
                'status': 'error',
                'message': 'No AI provider API keys configured'
            }
    
    def _test_private_key(self) -> Dict[str, Any]:
        """Test private key availability"""
        private_key = os.getenv('DEFAULT_PRIVATE_KEY')
        if not private_key:
            return {
                'status': 'error',
                'message': 'DEFAULT_PRIVATE_KEY not set in environment'
            }
        
        try:
            from eth_account import Account
            account = Account.from_key(private_key)
            return {
                'status': 'success',
                'message': f'Private key valid (address: {account.address})'
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Invalid private key: {e}'
            }
    
    def _test_hyperion_rpc(self) -> Dict[str, Any]:
        """Test Hyperion RPC URL"""
        rpc_url = os.getenv('HYPERION_RPC_URL')
        if not rpc_url:
            return {
                'status': 'error',
                'message': 'HYPERION_RPC_URL not set in environment'
            }
        
        if 'hyperion-testnet.metisdevops.link' in rpc_url:
            return {
                'status': 'success',
                'message': 'Hyperion RPC URL configured correctly'
            }
        else:
            return {
                'status': 'warning',
                'message': 'RPC URL may not be Hyperion testnet'
            }
    
    def enforce_production_mode(self, operation: str) -> None:
        """
        Enforce production mode for critical operations.
        Raises exception if not in production mode.
        """
        if not self.production_mode:
            critical_failures = getattr(self, 'critical_failures', [])
            error_msg = f"""
🚨 PRODUCTION MODE REQUIRED FOR: {operation}

The system is currently running in SAFE MODE due to missing critical dependencies.

CRITICAL FAILURES:
{chr(10).join([f"❌ {failure}" for failure in critical_failures]) if critical_failures else "❌ No critical failures detected - check validation results"}

To enable production mode:
1. Install missing dependencies
2. Configure required environment variables
3. Run: hyperagent status --validate

SYSTEM WILL NOT PERFORM: {operation}
"""
            raise RuntimeError(error_msg)
    
    def get_status_summary(self) -> str:
        """Get human-readable status summary"""
        if self.production_mode:
            return "🟢 PRODUCTION MODE - All systems operational"
        else:
            critical_count = len(self.validation_results.get('critical_failures', []))
            return f"🔴 SAFE MODE - {critical_count} critical dependencies missing"


# Global validator instance
_production_validator = None

def get_production_validator() -> ProductionModeValidator:
    """Get global production validator instance"""
    global _production_validator
    if _production_validator is None:
        _production_validator = ProductionModeValidator()
    return _production_validator

def validate_production_mode() -> Dict[str, Any]:
    """Validate production mode and return results"""
    validator = get_production_validator()
    return validator.validate_production_mode()

def enforce_production_mode(operation: str) -> None:
    """Enforce production mode for critical operations"""
    validator = get_production_validator()
    # Always run validation to ensure we have the latest state
    validator.validate_production_mode()
    validator.enforce_production_mode(operation)

def is_production_mode() -> bool:
    """Check if system is in production mode"""
    validator = get_production_validator()
    return validator.production_mode
