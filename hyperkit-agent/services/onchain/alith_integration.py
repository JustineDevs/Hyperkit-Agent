"""
Alith SDK Integration for HyperKit AI Agent
Provides onchain audit logging and registry functionality
"""

import json
import asyncio
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class AuditRecord:
    """Represents an onchain audit record"""
    contract_address: str
    audit_id: str
    auditor: str
    audit_date: str
    severity: str
    findings: List[Dict[str, Any]]
    tx_hash: str
    block_number: int

@dataclass
class AgentRegistry:
    """Represents an agent in the registry"""
    agent_id: str
    name: str
    capabilities: List[str]
    rating: float
    interactions: int
    creator: str
    created_at: str

class AlithIntegration:
    """Integration with Alith SDK for onchain operations"""
    
    def __init__(self, rpc_url: str = "https://hyperion-testnet.metisdevops.link"):
        self.rpc_url = rpc_url
        self.chain_id = 133717
        self.audit_registry_address = None
        self.agent_registry_address = None
        
        # Contract ABIs (simplified for demo)
        self.audit_registry_abi = [
            {
                "inputs": [
                    {"name": "contractAddress", "type": "address"},
                    {"name": "auditId", "type": "string"},
                    {"name": "auditor", "type": "string"},
                    {"name": "severity", "type": "string"},
                    {"name": "findings", "type": "string"}
                ],
                "name": "logAudit",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [{"name": "contractAddress", "type": "address"}],
                "name": "getAuditHistory",
                "outputs": [
                    {
                        "components": [
                            {"name": "auditId", "type": "string"},
                            {"name": "auditor", "type": "string"},
                            {"name": "auditDate", "type": "string"},
                            {"name": "severity", "type": "string"},
                            {"name": "findings", "type": "string"},
                            {"name": "txHash", "type": "string"},
                            {"name": "blockNumber", "type": "uint256"}
                        ],
                        "name": "audits",
                        "type": "tuple[]"
                    }
                ],
                "stateMutability": "view",
                "type": "function"
            }
        ]
        
        self.agent_registry_abi = [
            {
                "inputs": [
                    {"name": "name", "type": "string"},
                    {"name": "capabilities", "type": "string[]"}
                ],
                "name": "registerAgent",
                "outputs": [{"name": "agentId", "type": "uint256"}],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [
                    {"name": "agentId", "type": "uint256"},
                    {"name": "rating", "type": "uint256"}
                ],
                "name": "rateAgent",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [{"name": "agentId", "type": "uint256"}],
                "name": "getAgent",
                "outputs": [
                    {
                        "components": [
                            {"name": "name", "type": "string"},
                            {"name": "capabilities", "type": "string[]"},
                            {"name": "rating", "type": "uint256"},
                            {"name": "interactions", "type": "uint256"},
                            {"name": "creator", "type": "address"},
                            {"name": "createdAt", "type": "string"}
                        ],
                        "name": "agent",
                        "type": "tuple"
                    }
                ],
                "stateMutability": "view",
                "type": "function"
            }
        ]

    async def log_audit(self, contract_address: str, audit_results: Dict[str, Any], 
                       auditor: str = "HyperKit AI Agent") -> Dict[str, Any]:
        """
        Log audit results onchain
        
        Args:
            contract_address: Address of audited contract
            audit_results: Audit results dictionary
            auditor: Name of the auditor
            
        Returns:
            Transaction details
        """
        try:
            # Generate unique audit ID
            audit_id = f"audit_{contract_address[:8]}_{int(datetime.now().timestamp())}"
            
            # Prepare audit data
            audit_data = {
                "contract_address": contract_address,
                "audit_id": audit_id,
                "auditor": auditor,
                "audit_date": datetime.now().isoformat(),
                "severity": audit_results.get("severity", "unknown"),
                "findings": json.dumps(audit_results.get("findings", [])),
                "tx_hash": "pending",
                "block_number": 0
            }
            
            # In a real implementation, this would interact with the actual contract
            # For now, we'll simulate the transaction
            simulated_tx = await self._simulate_audit_logging(audit_data)
            
            # Update audit data with transaction details
            audit_data.update(simulated_tx)
            
            # Store locally for demo purposes
            await self._store_audit_record(audit_data)
            
            return {
                "success": True,
                "audit_id": audit_id,
                "tx_hash": simulated_tx["tx_hash"],
                "block_number": simulated_tx["block_number"],
                "contract_address": contract_address
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "contract_address": contract_address
            }

    async def get_audit_history(self, contract_address: str) -> List[Dict[str, Any]]:
        """
        Get audit history for a contract
        
        Args:
            contract_address: Address of the contract
            
        Returns:
            List of audit records
        """
        try:
            # In a real implementation, this would query the onchain registry
            # For now, we'll return stored records
            return await self._get_stored_audit_records(contract_address)
            
        except Exception as e:
            return [{"error": str(e), "status": "error"}]

    async def register_agent(self, name: str, capabilities: List[str], 
                           creator: str = "HyperKit AI Agent") -> Dict[str, Any]:
        """
        Register a new agent in the registry
        
        Args:
            name: Agent name
            capabilities: List of agent capabilities
            creator: Creator address
            
        Returns:
            Registration details
        """
        try:
            # Generate unique agent ID
            agent_id = f"agent_{name.lower().replace(' ', '_')}_{int(datetime.now().timestamp())}"
            
            # Prepare agent data
            agent_data = {
                "agent_id": agent_id,
                "name": name,
                "capabilities": capabilities,
                "rating": 0.0,
                "interactions": 0,
                "creator": creator,
                "created_at": datetime.now().isoformat()
            }
            
            # Simulate registration transaction
            simulated_tx = await self._simulate_agent_registration(agent_data)
            
            # Store locally
            await self._store_agent_record(agent_data)
            
            return {
                "success": True,
                "agent_id": agent_id,
                "tx_hash": simulated_tx["tx_hash"],
                "block_number": simulated_tx["block_number"]
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def rate_agent(self, agent_id: str, rating: float) -> Dict[str, Any]:
        """
        Rate an agent
        
        Args:
            agent_id: Agent ID to rate
            rating: Rating value (0-5)
            
        Returns:
            Rating transaction details
        """
        try:
            # Validate rating
            if not 0 <= rating <= 5:
                raise ValueError("Rating must be between 0 and 5")
            
            # Simulate rating transaction
            simulated_tx = await self._simulate_agent_rating(agent_id, rating)
            
            # Update stored agent record
            await self._update_agent_rating(agent_id, rating)
            
            return {
                "success": True,
                "agent_id": agent_id,
                "rating": rating,
                "tx_hash": simulated_tx["tx_hash"],
                "block_number": simulated_tx["block_number"]
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "agent_id": agent_id
            }

    async def get_agent(self, agent_id: str) -> Dict[str, Any]:
        """
        Get agent information
        
        Args:
            agent_id: Agent ID
            
        Returns:
            Agent information
        """
        try:
            return await self._get_stored_agent_record(agent_id)
            
        except Exception as e:
            return {"error": str(e), "status": "error"}

    async def list_agents(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        List registered agents
        
        Args:
            limit: Maximum number of agents to return
            
        Returns:
            List of agent records
        """
        try:
            return await self._get_stored_agents(limit)
            
        except Exception as e:
            return [{"error": str(e), "status": "error"}]

    async def _simulate_audit_logging(self, audit_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate audit logging transaction"""
        # In a real implementation, this would:
        # 1. Connect to Web3 provider
        # 2. Create contract instance
        # 3. Call logAudit function
        # 4. Wait for transaction confirmation
        
        return {
            "tx_hash": f"0x{audit_data['audit_id'].replace('_', '')[:64]}",
            "block_number": 12345,
            "gas_used": 50000,
            "status": "success"
        }

    async def _simulate_agent_registration(self, agent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate agent registration transaction"""
        return {
            "tx_hash": f"0x{agent_data['agent_id'].replace('_', '')[:64]}",
            "block_number": 12346,
            "gas_used": 75000,
            "status": "success"
        }

    async def _simulate_agent_rating(self, agent_id: str, rating: float) -> Dict[str, Any]:
        """Simulate agent rating transaction"""
        return {
            "tx_hash": f"0x{agent_id.replace('_', '')[:64]}",
            "block_number": 12347,
            "gas_used": 30000,
            "status": "success"
        }

    async def _store_audit_record(self, audit_data: Dict[str, Any]):
        """Store audit record locally (demo implementation)"""
        # In a real implementation, this would store in a database
        # For now, we'll use a simple file-based storage
        storage_file = "audit_records.json"
        
        try:
            with open(storage_file, "r") as f:
                records = json.load(f)
        except FileNotFoundError:
            records = []
        
        records.append(audit_data)
        
        with open(storage_file, "w") as f:
            json.dump(records, f, indent=2)

    async def _get_stored_audit_records(self, contract_address: str) -> List[Dict[str, Any]]:
        """Get stored audit records for a contract"""
        storage_file = "audit_records.json"
        
        try:
            with open(storage_file, "r") as f:
                records = json.load(f)
            
            # Filter by contract address
            return [record for record in records if record.get("contract_address") == contract_address]
            
        except FileNotFoundError:
            return []

    async def _store_agent_record(self, agent_data: Dict[str, Any]):
        """Store agent record locally (demo implementation)"""
        storage_file = "agent_records.json"
        
        try:
            with open(storage_file, "r") as f:
                records = json.load(f)
        except FileNotFoundError:
            records = []
        
        records.append(agent_data)
        
        with open(storage_file, "w") as f:
            json.dump(records, f, indent=2)

    async def _get_stored_agent_record(self, agent_id: str) -> Dict[str, Any]:
        """Get stored agent record"""
        storage_file = "agent_records.json"
        
        try:
            with open(storage_file, "r") as f:
                records = json.load(f)
            
            # Find agent by ID
            for record in records:
                if record.get("agent_id") == agent_id:
                    return record
            
            return {"error": "Agent not found", "status": "not_found"}
            
        except FileNotFoundError:
            return {"error": "No agents registered", "status": "not_found"}

    async def _get_stored_agents(self, limit: int) -> List[Dict[str, Any]]:
        """Get stored agent records with limit"""
        storage_file = "agent_records.json"
        
        try:
            with open(storage_file, "r") as f:
                records = json.load(f)
            
            # Sort by rating and return limited results
            sorted_records = sorted(records, key=lambda x: x.get("rating", 0), reverse=True)
            return sorted_records[:limit]
            
        except FileNotFoundError:
            return []

    async def _update_agent_rating(self, agent_id: str, rating: float):
        """Update agent rating"""
        storage_file = "agent_records.json"
        
        try:
            with open(storage_file, "r") as f:
                records = json.load(f)
            
            # Find and update agent
            for record in records:
                if record.get("agent_id") == agent_id:
                    old_rating = record.get("rating", 0)
                    old_interactions = record.get("interactions", 0)
                    
                    # Calculate new average rating
                    new_interactions = old_interactions + 1
                    new_rating = ((old_rating * old_interactions) + rating) / new_interactions
                    
                    record["rating"] = round(new_rating, 2)
                    record["interactions"] = new_interactions
                    break
            
            with open(storage_file, "w") as f:
                json.dump(records, f, indent=2)
                
        except FileNotFoundError:
            pass  # No agents to update

    async def get_contract_verification_status(self, contract_address: str) -> Dict[str, Any]:
        """
        Get contract verification status
        
        Args:
            contract_address: Contract address to check
            
        Returns:
            Verification status information
        """
        # In a real implementation, this would check the explorer API
        return {
            "contract_address": contract_address,
            "verified": True,
            "verification_date": datetime.now().isoformat(),
            "source_code_available": True,
            "abi_available": True,
            "explorer_url": f"https://hyperion-testnet-explorer.metisdevops.link/address/{contract_address}"
        }

    async def get_transaction_details(self, tx_hash: str) -> Dict[str, Any]:
        """
        Get transaction details
        
        Args:
            tx_hash: Transaction hash
            
        Returns:
            Transaction details
        """
        # In a real implementation, this would query the blockchain
        return {
            "tx_hash": tx_hash,
            "status": "success",
            "block_number": 12345,
            "gas_used": 50000,
            "gas_price": "20000000000",
            "from": "0x1234567890123456789012345678901234567890",
            "to": "0x0987654321098765432109876543210987654321",
            "value": "0",
            "explorer_url": f"https://hyperion-testnet-explorer.metisdevops.link/tx/{tx_hash}"
        }
