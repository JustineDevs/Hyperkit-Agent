"""
RAG Template Fetcher
Fetches and caches templates from IPFS based on CID registry
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import httpx
import hashlib

logger = logging.getLogger(__name__)


class RAGTemplateFetcher:
    """
    Fetches RAG templates from IPFS based on CID registry.
    Supports caching, offline mode, and graceful fallbacks.
    """
    
    def __init__(self, registry_path: Optional[str] = None, cache_dir: Optional[str] = None):
        """
        Initialize RAG template fetcher.
        
        Args:
            registry_path: Path to cid-registry.json (default: docs/RAG_TEMPLATES/cid-registry.json)
            cache_dir: Directory for caching templates (default: artifacts/rag_templates/)
        """
        self.project_root = Path(__file__).parent.parent.parent.parent
        
        # Set registry path
        if registry_path:
            self.registry_path = Path(registry_path)
        else:
            self.registry_path = self.project_root / "docs" / "RAG_TEMPLATES" / "cid-registry.json"
        
        # Set cache directory
        if cache_dir:
            self.cache_dir = Path(cache_dir)
        else:
            self.cache_dir = self.project_root / "artifacts" / "rag_templates"
        
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Load registry
        self.registry = self._load_registry()
        
        # Cache for fetched templates
        self._template_cache: Dict[str, Dict[str, Any]] = {}
        
        logger.info(f"RAG Template Fetcher initialized with {len(self.registry.get('templates', {}))} templates")
    
    def _load_registry(self) -> Dict[str, Any]:
        """Load CID registry from JSON file."""
        try:
            if not self.registry_path.exists():
                logger.warning(f"Registry file not found: {self.registry_path}")
                return {"templates": {}, "metadata": {}}
            
            with open(self.registry_path, 'r', encoding='utf-8') as f:
                registry = json.load(f)
            
            logger.info(f"Loaded registry with {len(registry.get('templates', {}))} templates")
            return registry
            
        except Exception as e:
            logger.error(f"Failed to load registry: {e}")
            return {"templates": {}, "metadata": {}}
    
    async def get_template(self, template_name: str, use_cache: bool = True, 
                          offline_mode: bool = False) -> Optional[str]:
        """
        Fetch a template by name.
        
        Args:
            template_name: Name of the template (e.g., 'erc20-template')
            use_cache: Whether to use cached version if available
            offline_mode: If True, only use cache, don't fetch from IPFS
            
        Returns:
            Template content as string, or None if not found
        """
        # Check cache first
        if use_cache and template_name in self._template_cache:
            logger.info(f"Using cached template: {template_name}")
            return self._template_cache[template_name]['content']
        
        # Check disk cache
        cache_file = self.cache_dir / f"{template_name}.txt"
        if use_cache and cache_file.exists():
            try:
                content = cache_file.read_text(encoding='utf-8')
                self._template_cache[template_name] = {
                    'content': content,
                    'cached': True
                }
                logger.info(f"Loaded from disk cache: {template_name}")
                return content
            except Exception as e:
                logger.warning(f"Failed to read cache file: {e}")
        
        # Get template metadata from registry
        if template_name not in self.registry.get('templates', {}):
            logger.error(f"Template not found in registry: {template_name}")
            return None
        
        template_data = self.registry['templates'][template_name]
        
        # Check if template is uploaded
        if not template_data.get('uploaded', False):
            logger.warning(f"Template not uploaded yet: {template_name}")
            return None
        
        # Get CID
        cid = template_data.get('cid')
        if not cid:
            logger.error(f"No CID for template: {template_name}")
            return None
        
        # Fetch from IPFS (unless offline)
        if not offline_mode:
            content = await self._fetch_from_ipfs(cid)
            if content:
                # Cache it
                self._template_cache[template_name] = {
                    'content': content,
                    'cid': cid,
                    'cached': False
                }
                
                # Save to disk cache
                try:
                    cache_file.write_text(content, encoding='utf-8')
                    logger.info(f"Cached template to disk: {template_name}")
                except Exception as e:
                    logger.warning(f"Failed to cache to disk: {e}")
                
                return content
        
        # Offline mode fallback
        if offline_mode:
            logger.warning(f"Offline mode - template not in cache: {template_name}")
            return None
        
        return None
    
    async def _fetch_from_ipfs(self, cid: str) -> Optional[str]:
        """
        Fetch content from IPFS via gateway.
        
        Args:
            cid: IPFS CID
            
        Returns:
            Content as string, or None if fetch failed
        """
        # Try multiple gateways
        gateways = [
            f"https://gateway.pinata.cloud/ipfs/{cid}",
            f"https://ipfs.io/ipfs/{cid}",
            f"https://cloudflare-ipfs.com/ipfs/{cid}",
            f"https://dweb.link/ipfs/{cid}"
        ]
        
        for gateway_url in gateways:
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(gateway_url)
                    if response.status_code == 200:
                        logger.info(f"Successfully fetched from {gateway_url}")
                        return response.text
            except Exception as e:
                logger.debug(f"Gateway failed {gateway_url}: {e}")
                continue
        
        logger.error(f"Failed to fetch from all gateways: {cid}")
        return None
    
    def list_templates(self) -> List[Dict[str, Any]]:
        """
        List all available templates from registry.
        
        Returns:
            List of template metadata dicts
        """
        templates = []
        for name, data in self.registry.get('templates', {}).items():
            templates.append({
                'name': name,
                'description': data.get('description', ''),
                'category': data.get('category', ''),
                'uploaded': data.get('uploaded', False),
                'cid': data.get('cid', ''),
                'gateway_url': data.get('gateway_url', '')
            })
        
        return templates
    
    def get_template_version(self, template_name: str, version: Optional[str] = None) -> Optional[str]:
        """
        Get a specific version of a template.
        
        Args:
            template_name: Base name of the template (e.g., 'erc20-template')
            version: Specific version (e.g., 'v2', 'latest'). If None, gets latest.
            
        Returns:
            Versioned template name, or None if not found
        """
        if version is None or version == 'latest':
            # Get the latest version
            versions = self._get_template_versions(template_name)
            if versions:
                return max(versions, key=lambda v: self._parse_version(v))
            return template_name
        
        # Check if specific version exists
        versioned_name = f"{template_name}-{version}"
        if versioned_name in self.registry.get('templates', {}):
            return versioned_name
        
        return None
    
    def _get_template_versions(self, template_name: str) -> List[str]:
        """
        Get all versions of a template.
        
        Args:
            template_name: Base template name
            
        Returns:
            List of versioned template names
        """
        versions = []
        for name in self.registry.get('templates', {}):
            if name == template_name or name.startswith(f"{template_name}-"):
                versions.append(name)
        return versions
    
    def _parse_version(self, version_string: str) -> tuple:
        """
        Parse version string for comparison.
        
        Args:
            version_string: Version string (e.g., 'v2', 'v1.1', 'latest')
            
        Returns:
            Tuple for version comparison
        """
        if version_string == 'latest':
            return (999, 999, 999)
        
        # Extract version number
        if version_string.startswith('v'):
            version_string = version_string[1:]
        
        try:
            parts = version_string.split('.')
            return tuple(int(part) for part in parts)
        except ValueError:
            return (0, 0, 0)
    
    async def get_template_with_version(self, template_name: str, version: Optional[str] = None, 
                                 use_cache: bool = True, offline_mode: bool = False) -> Optional[str]:
        """
        Get template content with version support.
        
        Args:
            template_name: Base template name
            version: Specific version or None for latest
            use_cache: Whether to use cache
            offline_mode: If True, only use cache
            
        Returns:
            Template content, or None if not found
        """
        # Get the correct versioned template name
        versioned_name = self.get_template_version(template_name, version)
        if not versioned_name:
            logger.warning(f"No version found for template: {template_name} (version: {version})")
            return None
        
        # Fetch the template
        return await self.get_template(versioned_name, use_cache, offline_mode)
    
    def list_template_versions(self, template_name: str) -> List[Dict[str, Any]]:
        """
        List all versions of a template.
        
        Args:
            template_name: Base template name
            
        Returns:
            List of version metadata
        """
        versions = []
        for name in self._get_template_versions(template_name):
            template_data = self.registry.get('templates', {}).get(name)
            if template_data:
                version_info = {
                    'name': name,
                    'version': name.replace(f"{template_name}-", "") if name != template_name else 'latest',
                    'description': template_data.get('description', ''),
                    'uploaded': template_data.get('uploaded', False),
                    'upload_date': template_data.get('upload_date', ''),
                    'deprecated': template_data.get('deprecated', False)
                }
                versions.append(version_info)
        
        # Sort by version
        versions.sort(key=lambda v: self._parse_version(v['version']), reverse=True)
        return versions
    
    def deprecate_template_version(self, template_name: str, version: str) -> bool:
        """
        Mark a template version as deprecated.
        
        Args:
            template_name: Base template name
            version: Version to deprecate
            
        Returns:
            True if successful
        """
        versioned_name = f"{template_name}-{version}"
        if versioned_name in self.registry.get('templates', {}):
            self.registry['templates'][versioned_name]['deprecated'] = True
            logger.info(f"Deprecated template version: {versioned_name}")
            return True
        
        logger.warning(f"Template version not found for deprecation: {versioned_name}")
        return False
    
    def get_template_info(self, template_name: str) -> Optional[Dict[str, Any]]:
        """
        Get template metadata from registry.
        
        Args:
            template_name: Name of the template
            
        Returns:
            Template metadata dict, or None if not found
        """
        return self.registry.get('templates', {}).get(template_name)
    
    def get_templates_with_metadata(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Get templates with rich metadata filtering.
        
        Args:
            filters: Optional filters for templates
                - category: Filter by category
                - author: Filter by author
                - tags: List of tags to match
                - code_standards: Filter by code standards
                - last_reviewed_after: Filter by last review date
                - deprecated: Include/exclude deprecated templates
        
        Returns:
            List of templates matching filters
        """
        templates = []
        
        for name, data in self.registry.get('templates', {}).items():
            template_info = {
                'name': name,
                'description': data.get('description', ''),
                'category': data.get('category', ''),
                'uploaded': data.get('uploaded', False),
                'cid': data.get('cid', ''),
                'gateway_url': data.get('gateway_url', ''),
                'author': data.get('author', 'Unknown'),
                'last_reviewed': data.get('last_reviewed', ''),
                'tags': data.get('tags', []),
                'code_standards': data.get('code_standards', []),
                'deprecated': data.get('deprecated', False),
                'upload_date': data.get('upload_date', ''),
                'version': data.get('version', 'latest')
            }
            
            # Apply filters
            if filters:
                if not self._matches_filters(template_info, filters):
                    continue
            
            templates.append(template_info)
        
        return templates
    
    def _matches_filters(self, template_info: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """
        Check if template matches given filters.
        
        Args:
            template_info: Template metadata
            filters: Filter criteria
            
        Returns:
            True if template matches filters
        """
        # Category filter
        if 'category' in filters and template_info['category'] != filters['category']:
            return False
        
        # Author filter
        if 'author' in filters and filters['author'].lower() not in template_info['author'].lower():
            return False
        
        # Tags filter (any tag must match)
        if 'tags' in filters:
            filter_tags = set(tag.lower() for tag in filters['tags'])
            template_tags = set(tag.lower() for tag in template_info['tags'])
            if not filter_tags.intersection(template_tags):
                return False
        
        # Code standards filter
        if 'code_standards' in filters:
            filter_standards = set(std.lower() for std in filters['code_standards'])
            template_standards = set(std.lower() for std in template_info['code_standards'])
            if not filter_standards.intersection(template_standards):
                return False
        
        # Last reviewed filter
        if 'last_reviewed_after' in filters:
            try:
                from datetime import datetime
                filter_date = datetime.fromisoformat(filters['last_reviewed_after'].replace('Z', '+00:00'))
                template_date = datetime.fromisoformat(template_info['last_reviewed'].replace('Z', '+00:00'))
                if template_date < filter_date:
                    return False
            except (ValueError, TypeError):
                # Skip date filter if parsing fails
                pass
        
        # Deprecated filter
        if 'deprecated' in filters:
            if template_info['deprecated'] != filters['deprecated']:
                return False
        
        return True
    
    def search_templates(self, query: str, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Search templates by query string.
        
        Args:
            query: Search query
            filters: Optional additional filters
            
        Returns:
            List of matching templates
        """
        query_lower = query.lower()
        matching_templates = []
        
        for name, data in self.registry.get('templates', {}).items():
            template_info = {
                'name': name,
                'description': data.get('description', ''),
                'category': data.get('category', ''),
                'uploaded': data.get('uploaded', False),
                'cid': data.get('cid', ''),
                'gateway_url': data.get('gateway_url', ''),
                'author': data.get('author', 'Unknown'),
                'last_reviewed': data.get('last_reviewed', ''),
                'tags': data.get('tags', []),
                'code_standards': data.get('code_standards', []),
                'deprecated': data.get('deprecated', False),
                'upload_date': data.get('upload_date', ''),
                'version': data.get('version', 'latest')
            }
            
            # Check if query matches any field
            matches = (
                query_lower in name.lower() or
                query_lower in template_info['description'].lower() or
                query_lower in template_info['category'].lower() or
                query_lower in template_info['author'].lower() or
                any(query_lower in tag.lower() for tag in template_info['tags']) or
                any(query_lower in std.lower() for std in template_info['code_standards'])
            )
            
            if matches:
                # Apply additional filters
                if filters and not self._matches_filters(template_info, filters):
                    continue
                
                matching_templates.append(template_info)
        
        return matching_templates
    
    def get_template_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about templates in the registry.
        
        Returns:
            Dictionary with template statistics
        """
        templates = self.registry.get('templates', {})
        
        stats = {
            'total_templates': len(templates),
            'uploaded_templates': sum(1 for t in templates.values() if t.get('uploaded', False)),
            'deprecated_templates': sum(1 for t in templates.values() if t.get('deprecated', False)),
            'categories': {},
            'authors': {},
            'tags': {},
            'code_standards': {}
        }
        
        # Count by category
        for template in templates.values():
            category = template.get('category', 'Unknown')
            stats['categories'][category] = stats['categories'].get(category, 0) + 1
            
            # Count by author
            author = template.get('author', 'Unknown')
            stats['authors'][author] = stats['authors'].get(author, 0) + 1
            
            # Count tags
            for tag in template.get('tags', []):
                stats['tags'][tag] = stats['tags'].get(tag, 0) + 1
            
            # Count code standards
            for std in template.get('code_standards', []):
                stats['code_standards'][std] = stats['code_standards'].get(std, 0) + 1
        
        return stats
    
    def get_templates_by_category(self, category: str) -> List[Dict[str, Any]]:
        """
        Get all templates in a specific category.
        
        Args:
            category: Category name (e.g., 'contracts', 'audits', 'prompts')
            
        Returns:
            List of template names in the category
        """
        templates = []
        for name, data in self.registry.get('templates', {}).items():
            if data.get('category') == category:
                templates.append({
                    'name': name,
                    'description': data.get('description', ''),
                    'uploaded': data.get('uploaded', False)
                })
        
        return templates
    
    def is_template_available(self, template_name: str) -> bool:
        """
        Check if template is available in registry and uploaded.
        
        Args:
            template_name: Name of the template
            
        Returns:
            True if template is available and uploaded
        """
        template = self.registry.get('templates', {}).get(template_name)
        if not template:
            return False
        return template.get('uploaded', False)
    
    def refresh_registry(self) -> bool:
        """
        Reload registry from file.
        
        Returns:
            True if successful
        """
        try:
            self.registry = self._load_registry()
            logger.info("Registry refreshed successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to refresh registry: {e}")
            return False
    
    def clear_cache(self, template_name: Optional[str] = None) -> bool:
        """
        Clear cache for a template or all templates.
        
        Args:
            template_name: Name of template to clear, or None to clear all
            
        Returns:
            True if successful
        """
        try:
            if template_name:
                # Clear specific template
                self._template_cache.pop(template_name, None)
                cache_file = self.cache_dir / f"{template_name}.txt"
                if cache_file.exists():
                    cache_file.unlink()
                logger.info(f"Cleared cache for: {template_name}")
            else:
                # Clear all
                self._template_cache.clear()
                for cache_file in self.cache_dir.glob("*.txt"):
                    cache_file.unlink()
                logger.info("Cleared all cached templates")
            
            return True
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            return False


# Global instance
_fetcher_instance: Optional[RAGTemplateFetcher] = None

def get_template_fetcher() -> RAGTemplateFetcher:
    """
    Get or create global RAG template fetcher instance.
    
    Returns:
        RAGTemplateFetcher instance
    """
    global _fetcher_instance
    
    if _fetcher_instance is None:
        _fetcher_instance = RAGTemplateFetcher()
    
    return _fetcher_instance


async def get_template(template_name: str, use_cache: bool = True, 
                      offline_mode: bool = False) -> Optional[str]:
    """
    Convenience function to get a template.
    
    Args:
        template_name: Name of the template
        use_cache: Whether to use cache
        offline_mode: If True, only use cache
        
    Returns:
        Template content, or None if not found
    """
    fetcher = get_template_fetcher()
    return await fetcher.get_template(template_name, use_cache, offline_mode)


def list_templates() -> List[Dict[str, Any]]:
    """
    Convenience function to list all templates.
    
    Returns:
        List of template metadata dicts
    """
    fetcher = get_template_fetcher()
    return fetcher.list_templates()


def get_templates_by_category(category: str) -> List[Dict[str, Any]]:
    """
    Convenience function to get templates by category.
    
    Args:
        category: Category name
        
    Returns:
        List of templates in category
    """
    fetcher = get_template_fetcher()
    return fetcher.get_templates_by_category(category)

