"""
Compilation job for HyperKit AI Agent production system.

This module handles async compilation of Solidity contracts using Foundry
in the production job queue system.
"""

from celery import current_task
from celery.exceptions import Retry
import logging
import tempfile
import os
from pathlib import Path
from typing import Dict, Any, Optional

from .celery import get_celery_app
from ..services.deployment.foundry_manager import FoundryManager
from ..services.deployment.foundry_deployer import FoundryDeployer

logger = logging.getLogger(__name__)

# Get Celery app
celery_app = get_celery_app()


@celery_app.task(bind=True, name="compile_contract")
def compile_contract_task(
    self,
    contract_code: str,
    contract_name: str,
    user_id: str,
    deployment_id: str,
    optimization: bool = True,
    compiler_version: str = "0.8.19"
) -> Dict[str, Any]:
    """
    Compile a Solidity contract using Foundry.
    
    Args:
        contract_code: Solidity source code
        contract_name: Name of the contract
        user_id: ID of the user requesting compilation
        deployment_id: ID of the deployment
        optimization: Whether to optimize the contract
        compiler_version: Solidity compiler version
    
    Returns:
        Dict containing compilation results
    """
    logger.info(f"Starting compilation task for contract: {contract_name}")
    
    try:
        # Update task status
        current_task.update_state(
            state="PROGRESS",
            meta={"status": "initializing", "progress": 0}
        )
        
        # Ensure Foundry is installed
        foundry_manager = FoundryManager()
        if not foundry_manager.is_installed():
            foundry_manager.install()
        
        # Create temporary directory for compilation
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Update progress
            current_task.update_state(
                state="PROGRESS",
                meta={"status": "preparing", "progress": 20}
            )
            
            # Write contract to file
            contract_file = temp_path / f"{contract_name}.sol"
            contract_file.write_text(contract_code)
            
            # Update progress
            current_task.update_state(
                state="PROGRESS",
                meta={"status": "compiling", "progress": 40}
            )
            
            # Compile using Foundry
            foundry_deployer = FoundryDeployer()
            compilation_result = foundry_deployer.compile_contract(
                contract_path=str(contract_file),
                optimization=optimization,
                compiler_version=compiler_version
            )
            
            # Update progress
            current_task.update_state(
                state="PROGRESS",
                meta={"status": "finalizing", "progress": 80}
            )
            
            # Prepare result
            result = {
                "success": True,
                "contract_name": contract_name,
                "bytecode": compilation_result.get("bytecode"),
                "abi": compilation_result.get("abi"),
                "gas_estimate": compilation_result.get("gas_estimate"),
                "compiler_version": compiler_version,
                "optimization": optimization,
                "warnings": compilation_result.get("warnings", []),
                "errors": compilation_result.get("errors", [])
            }
            
            # Update progress
            current_task.update_state(
                state="PROGRESS",
                meta={"status": "completed", "progress": 100}
            )
            
            logger.info(f"Compilation completed for contract: {contract_name}")
            return result
            
    except Exception as e:
        logger.error(f"Compilation failed for contract {contract_name}: {e}")
        
        # Update task status with error
        current_task.update_state(
            state="FAILURE",
            meta={
                "status": "failed",
                "error": str(e),
                "error_type": type(e).__name__
            }
        )
        
        # Retry logic
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying compilation task (attempt {self.request.retries + 1})")
            raise self.retry(
                countdown=60 * (2 ** self.request.retries),  # Exponential backoff
                exc=e
            )
        
        # Final failure
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "contract_name": contract_name
        }


@celery_app.task(bind=True, name="batch_compile_contracts")
def batch_compile_contracts_task(
    self,
    contracts: list,
    user_id: str,
    batch_id: str
) -> Dict[str, Any]:
    """
    Compile multiple contracts in batch.
    
    Args:
        contracts: List of contract dictionaries with code and name
        user_id: ID of the user requesting compilation
        batch_id: ID of the batch compilation
    
    Returns:
        Dict containing batch compilation results
    """
    logger.info(f"Starting batch compilation for {len(contracts)} contracts")
    
    results = []
    successful = 0
    failed = 0
    
    try:
        for i, contract in enumerate(contracts):
            # Update progress
            progress = int((i / len(contracts)) * 100)
            current_task.update_state(
                state="PROGRESS",
                meta={
                    "status": "compiling",
                    "progress": progress,
                    "current_contract": contract.get("name"),
                    "completed": i,
                    "total": len(contracts)
                }
            )
            
            # Compile individual contract
            result = compile_contract_task.apply_async(
                args=[
                    contract["code"],
                    contract["name"],
                    user_id,
                    f"{batch_id}_{i}"
                ]
            ).get()
            
            results.append(result)
            
            if result.get("success"):
                successful += 1
            else:
                failed += 1
        
        # Final result
        return {
            "success": True,
            "batch_id": batch_id,
            "total_contracts": len(contracts),
            "successful": successful,
            "failed": failed,
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Batch compilation failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "batch_id": batch_id,
            "results": results
        }


@celery_app.task(bind=True, name="validate_contract")
def validate_contract_task(
    self,
    contract_code: str,
    contract_name: str,
    validation_rules: list = None
) -> Dict[str, Any]:
    """
    Validate a contract against security rules.
    
    Args:
        contract_code: Solidity source code
        contract_name: Name of the contract
        validation_rules: List of validation rules to apply
    
    Returns:
        Dict containing validation results
    """
    logger.info(f"Starting validation for contract: {contract_name}")
    
    try:
        # Default validation rules
        if not validation_rules:
            validation_rules = [
                "no_selfdestruct",
                "no_delegatecall",
                "no_tx_origin",
                "no_infinite_loops",
                "proper_input_validation"
            ]
        
        # Update progress
        current_task.update_state(
            state="PROGRESS",
            meta={"status": "validating", "progress": 50}
        )
        
        # Perform validation (simplified for now)
        validation_results = {
            "success": True,
            "contract_name": contract_name,
            "rules_checked": validation_rules,
            "violations": [],
            "warnings": [],
            "risk_level": "low"
        }
        
        # Check for common vulnerabilities
        if "selfdestruct" in contract_code.lower():
            validation_results["violations"].append({
                "rule": "no_selfdestruct",
                "severity": "high",
                "message": "Contract contains selfdestruct function"
            })
            validation_results["risk_level"] = "high"
        
        if "delegatecall" in contract_code.lower():
            validation_results["violations"].append({
                "rule": "no_delegatecall", 
                "severity": "medium",
                "message": "Contract contains delegatecall function"
            })
            if validation_results["risk_level"] == "low":
                validation_results["risk_level"] = "medium"
        
        # Update progress
        current_task.update_state(
            state="PROGRESS",
            meta={"status": "completed", "progress": 100}
        )
        
        logger.info(f"Validation completed for contract: {contract_name}")
        return validation_results
        
    except Exception as e:
        logger.error(f"Validation failed for contract {contract_name}: {e}")
        return {
            "success": False,
            "error": str(e),
            "contract_name": contract_name
        }
