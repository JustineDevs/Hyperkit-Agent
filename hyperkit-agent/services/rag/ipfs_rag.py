"""
IPFS Pinata RAG System for HyperKit Agent

IPFS Pinata is the exclusive RAG backend - no Obsidian, no MCP, no other RAG systems.
All RAG operations use IPFS Pinata via CID registry.
"""

import asyncio
import logging
import requests
import json
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

class IPFSRAG:
    """
    IPFS Pinata-based RAG system for HyperKit Agent.
    Retrieves and stores AI prompts, templates, and knowledge in IPFS via Pinata.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize IPFS RAG system with Pinata configuration."""
        import os
        self.config = config or {}
        # Check multiple locations for Pinata keys
        self.pinata_api_key = (
            self.config.get('PINATA_API_KEY') or
            self.config.get('storage', {}).get('pinata', {}).get('api_key') or
            self.config.get('pinata', {}).get('api_key') or
            os.getenv('PINATA_API_KEY')
        )
        self.pinata_secret_key = (
            self.config.get('PINATA_SECRET_KEY') or
            self.config.get('storage', {}).get('pinata', {}).get('secret_key') or
            self.config.get('pinata', {}).get('secret_key') or
            os.getenv('PINATA_SECRET_KEY') or
            os.getenv('PINATA_API_SECRET')  # Legacy support
        )
        self.pinata_enabled = bool(self.pinata_api_key and self.pinata_secret_key)
        
        # IPFS Gateways for retrieval
        self.gateways = [
            'https://gateway.pinata.cloud/ipfs/',
            'https://ipfs.io/ipfs/',
            'https://cloudflare-ipfs.com/ipfs/',
            'https://dweb.link/ipfs/'
        ]
        
        # CID Registry cache
        self.cid_registry = {}
        self._load_cid_registry()
        
        # Track last retrieved CID for template identification (per ideal workflow)
        self.last_retrieved_cid = None
        
        # Initialize template engine for auto-selection (Phase 4)
        self.template_engine = None
        try:
            from core.prompts.template_engine import TemplateEngine
            self.template_engine = TemplateEngine()
            logger.info("Template engine initialized for RAG auto-selection")
        except Exception as e:
            logger.debug(f"Template engine not available: {e}")
        
        if self.pinata_enabled:
            logger.info("IPFS RAG initialized with Pinata integration")
        else:
            # Production mode: Require Pinata for RAG operations
            logger.error("CRITICAL: Pinata API keys not configured")
            logger.error("IPFS Pinata RAG requires PINATA_API_KEY and PINATA_SECRET_KEY")
            logger.error("Get keys from: https://app.pinata.cloud/")
            logger.error("Add to .env file to enable RAG functionality")
            # Don't raise here - let retrieve() handle it per-operation
            # This allows system to start but RAG operations will fail
    
    def _load_cid_registry(self):
        """Load CID registry for prompt templates."""
        try:
            registry_path = Path("docs/RAG_TEMPLATES/cid-registry.json")
            if registry_path.exists():
                with open(registry_path, 'r', encoding='utf-8') as f:
                    self.cid_registry = json.load(f)
                logger.info(f"Loaded {len(self.cid_registry)} templates from CID registry")
        except Exception as e:
            logger.warning(f"Could not load CID registry: {e}")
    
    async def retrieve(
        self, 
        query: str, 
        max_results: int = 5,
        rag_scope: str = 'official-only'  # 'official-only' or 'opt-in-community'
    ) -> str:
        """
        Retrieve relevant context from IPFS based on query.
        
        Requires Pinata API keys to be configured for production operation.
        Prefers Team uploads for canonical contracts, enables Community querying
        based on rag_scope setting.
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            rag_scope: RAG fetch scope ('official-only' or 'opt-in-community')
            
        Returns:
            Combined context string from relevant IPFS documents
            
        Raises:
            RuntimeError: If Pinata is not configured
        """
        if not self.pinata_enabled:
            raise RuntimeError(
                "IPFS Pinata RAG requires Pinata API keys to be configured\n"
                "  Required: PINATA_API_KEY and PINATA_SECRET_KEY in .env\n"
                "  Get keys: https://app.pinata.cloud/\n"
                "  Fix: Add Pinata credentials to .env file\n"
                "  Note: RAG context retrieval requires Pinata configuration"
            )
        
        # Try template matching first (Phase 4)
        matched_template = None
        if self.template_engine:
            matched_template = self.template_engine.match_template(query)
            if matched_template:
                logger.info(f"📋 Matched template: {matched_template.name}")
        
        try:
            # Load dual-scope registries
            from services.storage.dual_scope_pinata import UploadScope
            
            team_results = []
            community_results = []
            
            # 1. Search Team registry (official, canonical contracts)
            team_registry = self._load_scope_registry(UploadScope.TEAM)
            for artifact_id, entry in team_registry.items():
                if self._is_relevant(query, entry.get('metadata', {})):
                    try:
                        cid = entry.get('cid')
                        content = await self._fetch_from_ipfs(cid)
                        if content:
                            # Track last retrieved CID (per ideal workflow: template identification)
                            self.last_retrieved_cid = cid
                            team_results.append({
                                'name': artifact_id,
                                'content': content,
                                'cid': cid,
                                'scope': 'team',
                                'relevance': self._calculate_relevance(query, content),
                                'quality_score': self._calculate_quality_score(entry)
                            })
                    except Exception as e:
                        logger.warning(f"Failed to fetch Team artifact {artifact_id}: {e}")
            
            # 2. Search Community registry if opt-in enabled
            if rag_scope == 'opt-in-community':
                community_registry = self._load_scope_registry(UploadScope.COMMUNITY)
                for artifact_id, entry in community_registry.items():
                    # Apply quality filtering for Community artifacts
                    quality_score = self._calculate_quality_score(entry)
                    if quality_score >= 0.5:  # Only include higher quality Community artifacts
                        if self._is_relevant(query, entry.get('metadata', {})):
                            try:
                                cid = entry.get('cid')
                                content = await self._fetch_from_ipfs(cid)
                                if content:
                                    # Track last retrieved CID (per ideal workflow)
                                    if not self.last_retrieved_cid:
                                        self.last_retrieved_cid = cid
                                    community_results.append({
                                        'name': artifact_id,
                                        'content': content,
                                        'cid': cid,
                                        'scope': 'community',
                                        'relevance': self._calculate_relevance(query, content),
                                        'quality_score': quality_score
                                    })
                            except Exception as e:
                                logger.warning(f"Failed to fetch Community artifact {artifact_id}: {e}")
            
            # 3. Also search legacy CID registry (for backward compatibility)
            legacy_results = []
            for name, metadata in self.cid_registry.items():
                if self._is_relevant(query, metadata):
                    try:
                        content = await self._fetch_from_ipfs(metadata.get('cid'))
                        if content:
                            legacy_results.append({
                                'name': name,
                                'content': content,
                                'cid': metadata.get('cid'),
                                'scope': 'legacy',
                                'relevance': self._calculate_relevance(query, content),
                                'quality_score': 1.0  # Legacy templates are considered high quality
                            })
                    except Exception as e:
                        logger.warning(f"Failed to fetch legacy template {name}: {e}")
            
            # 4. Combine and rank all results
            # Prefer Team > Legacy > Community (with quality filtering)
            all_results = team_results + legacy_results + community_results
            
            # Sort by: scope priority (team > legacy > community), then relevance, then quality
            def sort_key(r):
                scope_priority = {'team': 3, 'legacy': 2, 'community': 1}.get(r.get('scope', ''), 0)
                return (scope_priority, r.get('relevance', 0), r.get('quality_score', 0))
            
            all_results.sort(key=sort_key, reverse=True)
            
            # 5. Combine top results
            combined_context = "\n\n".join([
                f"## {r['name']} ({r.get('scope', 'unknown')})\n{r['content']}" 
                for r in all_results[:max_results]
            ])
            
            logger.info(f"RAG retrieval: {len(team_results)} Team, {len(community_results)} Community, {len(legacy_results)} Legacy")
            
            # Self-healing onboarding: If no results found, suggest storing new pattern
            if not combined_context and len(all_results) == 0:
                logger.info("💡 No RAG context found - this is a new prompt pattern")
                logger.info("💡 Consider storing this as a template for future use")
                # Store suggestion in metadata for later processing
                self._suggest_template_creation(query)
            
            # Combine with template if matched (Phase 4)
            if self.template_engine and matched_template:
                try:
                    template_context = matched_template.render(goal=query)
                    if combined_context:
                        return f"{template_context}\n\n## Additional Context from IPFS\n{combined_context}"
                    return template_context
                except Exception as e:
                    logger.warning(f"Template combination failed: {e}")
            
            return combined_context
            
        except Exception as e:
            logger.error(f"RAG retrieval failed: {e}")
            return ""
    
    def _load_scope_registry(self, scope) -> Dict[str, Any]:
        """Load registry for specific scope"""
        try:
            from services.storage.dual_scope_pinata import UploadScope
            from pathlib import Path
            
            registry_dir = Path("data/ipfs_registries")
            if scope == UploadScope.TEAM:
                registry_path = registry_dir / 'cid-registry-team.json'
            else:
                registry_path = registry_dir / 'cid-registry-community.json'
            
            if registry_path.exists():
                with open(registry_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.warning(f"Could not load {scope.value} registry: {e}")
            return {}
    
    def _calculate_quality_score(self, entry: Dict[str, Any]) -> float:
        """
        Calculate quality score for Community artifacts.
        Higher score = higher quality, more trustworthy.
        """
        score = 0.5  # Base score
        
        # Factors that increase quality:
        # - Compilation success
        if entry.get('metadata', {}).get('keyvalues', {}).get('compilation_success') == 'True':
            score += 0.2
        
        # - Audit passed (low severity)
        audit_severity = entry.get('metadata', {}).get('keyvalues', {}).get('audit_severity', 'unknown')
        if audit_severity == 'low':
            score += 0.2
        elif audit_severity == 'medium':
            score += 0.1
        
        # - Has reputation/upvotes (if implemented)
        upvotes = entry.get('metadata', {}).get('keyvalues', {}).get('upvotes', 0)
        if isinstance(upvotes, (int, float)) and upvotes > 0:
            score += min(0.1 * upvotes, 0.1)  # Max 0.1 for upvotes
        
        # - Not flagged
        flagged = entry.get('metadata', {}).get('keyvalues', {}).get('flagged', False)
        if flagged:
            score -= 0.5  # Heavy penalty for flagged content
        
        return max(0.0, min(1.0, score))  # Clamp between 0 and 1
    
    def _suggest_template_creation(self, query: str):
        """
        Suggest creating a template for a new prompt pattern.
        Stores suggestion for later processing.
        
        Args:
            query: User prompt that had no RAG match
        """
        try:
            from pathlib import Path
            suggestions_file = Path(".workflow_contexts") / "template_suggestions.json"
            suggestions_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Load existing suggestions
            suggestions = []
            if suggestions_file.exists():
                try:
                    with open(suggestions_file, 'r', encoding='utf-8') as f:
                        suggestions = json.load(f)
                except Exception:
                    suggestions = []
            
            # Add new suggestion
            suggestion = {
                "query": query[:200],  # Truncate for storage
                "timestamp": datetime.utcnow().isoformat(),
                "suggested": True,
                "processed": False
            }
            
            # Avoid duplicates
            if not any(s.get('query') == suggestion['query'] for s in suggestions):
                suggestions.append(suggestion)
                # Keep only last 50 suggestions
                if len(suggestions) > 50:
                    suggestions = suggestions[-50:]
                
                # Save suggestions
                with open(suggestions_file, 'w', encoding='utf-8') as f:
                    json.dump(suggestions, f, indent=2)
                
                logger.debug(f"Stored template suggestion for new prompt pattern")
        except Exception as e:
            logger.debug(f"Failed to store template suggestion: {e}")
    
    async def suggest_and_store_new_pattern(
        self,
        prompt: str,
        generated_contract: str,
        success: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Suggest and optionally store a new prompt pattern as a template.
        Called when a successful generation occurs with a novel prompt.
        
        Args:
            prompt: User prompt that generated the contract
            generated_contract: Generated contract code
            success: Whether generation was successful
            metadata: Optional metadata (contract type, compilation status, etc.)
            
        Returns:
            CID of stored template if stored, None otherwise
        """
        if not success:
            logger.debug("Skipping template storage for unsuccessful generation")
            return None
        
        if not self.pinata_enabled:
            logger.debug("Pinata not enabled - cannot store template")
            return None
        
        try:
            # Extract contract type from prompt or metadata
            contract_type = "Custom"
            if metadata:
                contract_type = metadata.get('contract_type') or metadata.get('category', 'Custom')
            else:
                prompt_lower = prompt.lower()
                if 'erc20' in prompt_lower or 'token' in prompt_lower:
                    contract_type = 'ERC20'
                elif 'erc721' in prompt_lower or 'nft' in prompt_lower:
                    contract_type = 'ERC721'
                elif 'defi' in prompt_lower or 'dex' in prompt_lower:
                    contract_type = 'DeFi'
                elif 'dao' in prompt_lower or 'governance' in prompt_lower:
                    contract_type = 'DAO'
            
            # Create template name
            template_name = f"{contract_type}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
            # Prepare template content (prompt + contract)
            template_content = f"""# Template: {contract_type}
# Generated: {datetime.utcnow().isoformat()}
# Prompt: {prompt[:500]}

{generated_contract}
"""
            
            # Prepare metadata
            template_metadata = {
                'description': f"Template for {contract_type} contracts",
                'tags': [contract_type.lower(), 'auto-generated', 'template'],
                'version': '1.0',
                'contract_type': contract_type,
                'prompt_pattern': prompt[:200],
                'auto_stored': True,
                **(metadata or {})
            }
            
            # Upload template
            cid = await self.upload_template(template_name, template_content, template_metadata)
            
            logger.info(f"✅ Auto-stored new template: {template_name} (CID: {cid})")
            logger.info(f"💡 This template will be available for future similar prompts")
            
            return cid
            
        except Exception as e:
            logger.warning(f"Failed to auto-store template: {e}")
            return None
    
    async def upload_template(self, name: str, content: str, metadata: Dict[str, Any] = None) -> str:
        """
        Upload a template to IPFS via Pinata.
        
        Args:
            name: Template name
            content: Template content
            metadata: Additional metadata
            
        Returns:
            CID of uploaded content
        """
        if not self.pinata_enabled:
            raise RuntimeError(
                "IPFS Pinata RAG requires Pinata API keys to upload templates\n"
                "  Required: PINATA_API_KEY and PINATA_SECRET_KEY in .env\n"
                "  Get keys: https://app.pinata.cloud/\n"
                "  Fix: Add Pinata credentials to .env file"
            )
        
        try:
            pinata_metadata = {
                'name': name,
                'description': metadata.get('description', ''),
                'tags': metadata.get('tags', []),
                'version': metadata.get('version', 'latest'),
                **(metadata or {})
            }
            
            # Upload to Pinata
            headers = {
                'pinata_api_key': self.pinata_api_key,
                'pinata_secret_api_key': self.pinata_secret_key
            }
            
            files = {'file': ('content', content)}
            
            metadata_header = json.dumps(pinata_metadata)
            
            response = requests.post(
                'https://api.pinata.cloud/pinning/pinFileToIPFS',
                files=files,
                headers={
                    **headers,
                    'pinata_metadata': metadata_header
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                cid = result.get('IpfsHash')
                
                # Update local registry cache
                self.cid_registry[name] = {
                    'cid': cid,
                    **pinata_metadata
                }
                
                logger.info(f"Uploaded template '{name}' to IPFS: {cid}")
                return cid
            else:
                logger.error(f"Pinata upload failed: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Template upload failed: {e}")
            return None
    
    async def _fetch_from_ipfs(self, cid: str) -> Optional[str]:
        """Fetch content from IPFS by CID."""
        for gateway in self.gateways:
            try:
                url = f"{gateway}{cid}"
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    return response.text
            except Exception as e:
                logger.warning(f"Gateway {gateway} failed: {e}")
                continue
        
        logger.error(f"Could not fetch CID {cid} from any gateway")
        return None
    
    def _is_relevant(self, query: str, metadata: Dict[str, Any]) -> bool:
        """Check if template is relevant to query."""
        query_lower = query.lower()
        
        # Check name
        name = metadata.get('name', '').lower()
        if query_lower in name:
            return True
        
        # Check tags
        tags = metadata.get('tags', [])
        for tag in tags:
            if query_lower in tag.lower():
                return True
        
        # Check description
        description = metadata.get('description', '').lower()
        if query_lower in description:
            return True
        
        return False
    
    def _calculate_relevance(self, query: str, content: str) -> float:
        """Calculate relevance score (simple keyword matching)."""
        query_words = query.lower().split()
        content_lower = content.lower()
        
        matches = sum(1 for word in query_words if word in content_lower)
        return matches / len(query_words) if query_words else 0
    
    async def get_template(self, name: str) -> Optional[str]:
        """Get a specific template by name."""
        if name in self.cid_registry:
            cid = self.cid_registry[name].get('cid')
            if cid:
                return await self._fetch_from_ipfs(cid)
        return None
    
    def get_available_templates(self) -> List[str]:
        """Get list of available template names."""
        return list(self.cid_registry.keys())
    
    async def test_connections(self) -> Dict[str, Any]:
        """Test IPFS Pinata RAG connections and return status."""
        results = {
            "status": "failed",
            "pinata_enabled": self.pinata_enabled,
            "cid_registry_loaded": bool(self.cid_registry),
            "template_count": len(self.cid_registry),
            "test_retrieve": "skipped",
            "test_upload": "skipped"
        }
        
        if self.pinata_enabled:
            # Test retrieval
            try:
                test_query = "smart contract"
                content = await self.retrieve(test_query, max_results=1)
                if content:
                    results["test_retrieve"] = "success"
                else:
                    results["test_retrieve"] = "success (no results)"
            except Exception as e:
                results["test_retrieve"] = f"failed ({str(e)[:50]})"
            
            # Test upload (only if Pinata enabled)
            try:
                test_cid = await self.upload_template(
                    "test_template",
                    "This is a test template",
                    {"description": "Test", "version": "test"}
                )
                if test_cid:
                    results["test_upload"] = "success"
                else:
                    results["test_upload"] = "failed (no CID)"
            except Exception as e:
                results["test_upload"] = f"failed ({str(e)[:50]})"
        
        # Determine overall status
        if self.pinata_enabled and self.cid_registry:
            if results["test_retrieve"] == "success" or results["test_retrieve"] == "success (no results)":
                results["status"] = "success"
            elif results["test_retrieve"] == "skipped":
                results["status"] = "partial_success"
            else:
                results["status"] = "failed"
        elif not self.pinata_enabled:
            results["status"] = "failed"
            results["error"] = "Pinata API keys not configured"
        elif not self.cid_registry:
            results["status"] = "partial_success"
            results["warning"] = "CID registry not loaded"
        
        return results


# Convenience function to create RAG instance
def get_ipfs_rag(config: Dict[str, Any] = None) -> IPFSRAG:
    """Get or create IPFS RAG instance."""
    return IPFSRAG(config)


async def test_ipfs_rag():
    """Test IPFS RAG system."""
    print("Testing IPFS RAG System...")
    
    try:
        # Create instance
        rag = IPFSRAG()
        
        # Test retrieval
        query = "smart contract generation"
        context = await rag.retrieve(query)
        
        print(f"Retrieved context length: {len(context)} characters")
        if context:
            print("IPFS RAG is working!")
            return True
        else:
            print("No context retrieved")
            return False
            
    except Exception as e:
        print(f"IPFS RAG test failed: {e}")
        return False
