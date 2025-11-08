"""
Agent Memory System
Stores and queries past workflow contexts to avoid repeating failures and learn from successes.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class WorkflowMemoryEntry:
    """Single entry in agent memory"""
    workflow_id: str
    user_prompt: str
    timestamp: str
    success: bool
    error_patterns: List[str]
    successful_fixes: List[Dict[str, Any]]
    contract_type: Optional[str] = None
    rag_context_used: bool = False
    model_provider: Optional[str] = None


class AgentMemory:
    """
    Agent memory system that stores and queries past workflow contexts.
    Helps avoid repeating past failures and learn from successful patterns.
    """
    
    def __init__(self, workspace_dir: Path, max_entries: int = 100):
        """
        Initialize agent memory system.
        
        Args:
            workspace_dir: Base workspace directory
            max_entries: Maximum number of entries to keep in memory
        """
        self.workspace_dir = Path(workspace_dir)
        self.memory_dir = self.workspace_dir / ".workflow_contexts"
        self.memory_file = self.memory_dir / "agent_memory.json"
        self.max_entries = max_entries
        self.memory: List[WorkflowMemoryEntry] = []
        
        # Load existing memory
        self._load_memory()
    
    def _load_memory(self):
        """Load memory from disk"""
        if self.memory_file.exists():
            try:
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.memory = [
                        WorkflowMemoryEntry(**entry) for entry in data.get('entries', [])
                    ]
                logger.info(f"Loaded {len(self.memory)} entries from agent memory")
            except Exception as e:
                logger.warning(f"Failed to load agent memory: {e}")
                self.memory = []
        else:
            self.memory = []
    
    def _save_memory(self):
        """Save memory to disk"""
        try:
            self.memory_dir.mkdir(parents=True, exist_ok=True)
            data = {
                "version": "1.0",
                "last_updated": datetime.utcnow().isoformat(),
                "entries": [asdict(entry) for entry in self.memory]
            }
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            logger.debug(f"Saved {len(self.memory)} entries to agent memory")
        except Exception as e:
            logger.warning(f"Failed to save agent memory: {e}")
    
    def add_workflow(self, context: Dict[str, Any]):
        """
        Add a workflow context to memory.
        
        Args:
            context: WorkflowContext dictionary (from generate_diagnostic_bundle)
        """
        try:
            # Extract error patterns
            error_patterns = []
            for error in context.get('error_history', []):
                error_type = error.get('error_type', 'unknown')
                error_msg = error.get('error', '')
                if error_type and error_type != 'unknown':
                    error_patterns.append(error_type)
                # Extract key phrases from error messages
                if 'pragma' in error_msg.lower():
                    error_patterns.append('missing_pragma')
                if 'import' in error_msg.lower() and 'not found' in error_msg.lower():
                    error_patterns.append('missing_import')
                if 'shadow' in error_msg.lower():
                    error_patterns.append('variable_shadowing')
            
            # Extract successful fixes
            successful_fixes = []
            for error in context.get('error_history', []):
                if error.get('fix_successful', False):
                    successful_fixes.append({
                        'error_type': error.get('error_type'),
                        'fix_message': error.get('fix_message', ''),
                        'stage': error.get('stage')
                    })
            
            # Determine contract type from prompt or category
            contract_type = context.get('contract_info', {}).get('category')
            if not contract_type:
                prompt = context.get('user_prompt', '').lower()
                if 'erc20' in prompt or 'token' in prompt:
                    contract_type = 'ERC20'
                elif 'erc721' in prompt or 'nft' in prompt:
                    contract_type = 'ERC721'
                elif 'defi' in prompt or 'dex' in prompt:
                    contract_type = 'DeFi'
                elif 'dao' in prompt or 'governance' in prompt:
                    contract_type = 'DAO'
                else:
                    contract_type = 'Custom'
            
            entry = WorkflowMemoryEntry(
                workflow_id=context.get('workflow_id', 'unknown'),
                user_prompt=context.get('user_prompt', '')[:200],  # Truncate for storage
                timestamp=context.get('created_at', datetime.utcnow().isoformat()),
                success=not any(s.get('status') == 'error' for s in context.get('stages', [])),
                error_patterns=list(set(error_patterns)),  # Deduplicate
                successful_fixes=successful_fixes,
                contract_type=contract_type,
                rag_context_used=context.get('rag_status', {}).get('context_retrieved', False),
                model_provider=context.get('model_provider', 'unknown')
            )
            
            self.memory.append(entry)
            
            # Keep only last N entries
            if len(self.memory) > self.max_entries:
                self.memory = self.memory[-self.max_entries:]
            
            self._save_memory()
            logger.debug(f"Added workflow {entry.workflow_id} to agent memory")
            
        except Exception as e:
            logger.warning(f"Failed to add workflow to memory: {e}")
    
    def query_similar_errors(self, error_type: str, stage: str, limit: int = 5) -> List[WorkflowMemoryEntry]:
        """
        Query memory for similar errors and their fixes.
        
        Args:
            error_type: Type of error to search for
            stage: Stage where error occurred
            limit: Maximum number of results to return
            
        Returns:
            List of memory entries with similar errors
        """
        results = []
        for entry in reversed(self.memory):  # Search most recent first
            if error_type in entry.error_patterns:
                # Check if there was a successful fix
                for fix in entry.successful_fixes:
                    if fix.get('error_type') == error_type and fix.get('stage') == stage:
                        results.append(entry)
                        break
                if len(results) >= limit:
                    break
        
        return results
    
    def query_similar_prompts(self, prompt: str, limit: int = 5) -> List[WorkflowMemoryEntry]:
        """
        Query memory for similar prompts.
        
        Args:
            prompt: User prompt to search for
            limit: Maximum number of results to return
            
        Returns:
            List of memory entries with similar prompts
        """
        # Simple keyword-based similarity (could be enhanced with embeddings)
        prompt_lower = prompt.lower()
        prompt_keywords = set(prompt_lower.split())
        
        results = []
        for entry in reversed(self.memory):
            entry_prompt_lower = entry.user_prompt.lower()
            entry_keywords = set(entry_prompt_lower.split())
            
            # Calculate simple Jaccard similarity
            intersection = len(prompt_keywords & entry_keywords)
            union = len(prompt_keywords | entry_keywords)
            similarity = intersection / union if union > 0 else 0
            
            if similarity > 0.3:  # 30% keyword overlap
                results.append((entry, similarity))
        
        # Sort by similarity and return top N
        results.sort(key=lambda x: x[1], reverse=True)
        return [entry for entry, _ in results[:limit]]
    
    def get_successful_fixes_for_error(self, error_type: str, stage: str) -> List[Dict[str, Any]]:
        """
        Get all successful fixes for a specific error type and stage.
        
        Args:
            error_type: Type of error
            stage: Stage where error occurred
            
        Returns:
            List of successful fix strategies
        """
        fixes = []
        for entry in reversed(self.memory):
            for fix in entry.successful_fixes:
                if fix.get('error_type') == error_type and fix.get('stage') == stage:
                    fixes.append(fix)
        
        return fixes
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about stored memory"""
        if not self.memory:
            return {
                "total_entries": 0,
                "success_rate": 0.0,
                "common_error_types": {},
                "common_contract_types": {}
            }
        
        success_count = sum(1 for entry in self.memory if entry.success)
        error_types = {}
        contract_types = {}
        
        for entry in self.memory:
            for error_type in entry.error_patterns:
                error_types[error_type] = error_types.get(error_type, 0) + 1
            if entry.contract_type:
                contract_types[entry.contract_type] = contract_types.get(entry.contract_type, 0) + 1
        
        return {
            "total_entries": len(self.memory),
            "success_rate": success_count / len(self.memory) if self.memory else 0.0,
            "common_error_types": dict(sorted(error_types.items(), key=lambda x: x[1], reverse=True)[:10]),
            "common_contract_types": dict(sorted(contract_types.items(), key=lambda x: x[1], reverse=True)[:10])
        }

