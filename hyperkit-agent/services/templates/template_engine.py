"""
Dynamic Smart Contract Template Engine

Scalable contract generation with variable injection and template management.
"""

import logging
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
from string import Template
import json

logger = logging.getLogger(__name__)


class TemplateEngine:
    """
    Dynamic template engine for smart contract generation.
    
    Features:
    - Variable injection with validation
    - Template inheritance
    - Conditional sections
    - Reusable components
    """
    
    def __init__(self, template_dir: Optional[str] = None):
        """
        Initialize template engine.
        
        Args:
            template_dir: Directory containing templates (default: ./templates)
        """
        if template_dir is None:
            template_dir = Path(__file__).parent / 'library'
        
        self.template_dir = Path(template_dir)
        self.template_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Template engine initialized with directory: {self.template_dir}")
    
    def generate(
        self,
        template_name: str,
        variables: Dict[str, Any],
        validate: bool = True
    ) -> str:
        """
        Generate contract from template with variable injection.
        
        Args:
            template_name: Name of template file (e.g., 'ERC20.sol.template')
            variables: Dictionary of variables to inject
            validate: Whether to validate required variables
            
        Returns:
            Generated contract code
        """
        logger.info(f"Generating contract from template: {template_name}")
        
        # Load template
        template_content = self._load_template(template_name)
        
        # Get template metadata
        metadata = self._extract_metadata(template_content)
        
        # Validate variables if requested
        if validate:
            self._validate_variables(variables, metadata)
        
        # Apply variable injection
        result = self._inject_variables(template_content, variables)
        
        # Process conditionals
        result = self._process_conditionals(result, variables)
        
        # Clean up
        result = self._cleanup(result)
        
        logger.info(f"Contract generated successfully: {len(result)} characters")
        
        return result
    
    def list_templates(self) -> List[Dict[str, Any]]:
        """
        List all available templates with metadata.
        
        Returns:
            List of template info dictionaries
        """
        templates = []
        
        for template_file in self.template_dir.rglob('*.template'):
            try:
                content = template_file.read_text(encoding='utf-8')
                metadata = self._extract_metadata(content)
                
                templates.append({
                    'name': template_file.stem,
                    'path': str(template_file),
                    'description': metadata.get('description', ''),
                    'variables': metadata.get('variables', []),
                    'category': metadata.get('category', 'general')
                })
            except Exception as e:
                logger.error(f"Error loading template {template_file}: {e}")
        
        return templates
    
    def create_template(
        self,
        name: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Create a new template.
        
        Args:
            name: Template name (without .template extension)
            content: Template content
            metadata: Template metadata (description, variables, etc.)
        """
        template_file = self.template_dir / f"{name}.sol.template"
        
        # Add metadata header
        if metadata:
            header = self._generate_metadata_header(metadata)
            content = header + "\n" + content
        
        template_file.write_text(content, encoding='utf-8')
        
        logger.info(f"Template created: {template_file}")
    
    def _load_template(self, template_name: str) -> str:
        """Load template content from file"""
        # Try exact name
        template_file = self.template_dir / template_name
        
        # Try with .template extension
        if not template_file.exists() and not template_name.endswith('.template'):
            template_file = self.template_dir / f"{template_name}.sol.template"
        
        # Try without .sol
        if not template_file.exists() and '.sol' in template_name:
            base_name = template_name.replace('.sol', '')
            template_file = self.template_dir / f"{base_name}.template"
        
        if not template_file.exists():
            raise FileNotFoundError(f"Template not found: {template_name}")
        
        return template_file.read_text(encoding='utf-8')
    
    def _extract_metadata(self, template_content: str) -> Dict[str, Any]:
        """
        Extract metadata from template comments.
        
        Format:
        // @template: <name>
        // @description: <description>
        // @variable: <name>: <type> - <description>
        // @category: <category>
        """
        metadata = {
            'variables': [],
            'description': '',
            'category': 'general'
        }
        
        lines = template_content.split('\n')
        for line in lines:
            line = line.strip()
            
            if line.startswith('// @description:'):
                metadata['description'] = line.split(':', 1)[1].strip()
            
            elif line.startswith('// @variable:'):
                var_info = line.split(':', 1)[1].strip()
                metadata['variables'].append(var_info)
            
            elif line.startswith('// @category:'):
                metadata['category'] = line.split(':', 1)[1].strip()
        
        return metadata
    
    def _validate_variables(self, variables: Dict[str, Any], metadata: Dict[str, Any]):
        """Validate that all required variables are provided"""
        # Extract required variable names from metadata
        required_vars = set()
        for var_info in metadata.get('variables', []):
            # Parse "name: type - description"
            parts = var_info.split(':')
            if parts:
                var_name = parts[0].strip()
                required_vars.add(var_name)
        
        # Check for missing variables
        provided_vars = set(variables.keys())
        missing = required_vars - provided_vars
        
        if missing:
            raise ValueError(f"Missing required variables: {', '.join(missing)}")
    
    def _inject_variables(self, template: str, variables: Dict[str, Any]) -> str:
        """
        Inject variables into template.
        
        Supports:
        - ${variable_name} - Simple substitution
        - ${variable_name|default_value} - With default
        - ${variable_name|upper} - With transformation
        """
        result = template
        
        # Process each variable
        for var_name, var_value in variables.items():
            # Simple substitution
            pattern = r'\$\{' + re.escape(var_name) + r'(?:\|[^}]*)?\}'
            
            def replace_func(match):
                full_match = match.group(0)
                
                # Check for transformations
                if '|' in full_match:
                    parts = full_match[2:-1].split('|')
                    transform = parts[1] if len(parts) > 1 else None
                    
                    if transform == 'upper':
                        return str(var_value).upper()
                    elif transform == 'lower':
                        return str(var_value).lower()
                    elif transform == 'capitalize':
                        return str(var_value).capitalize()
                    elif transform.startswith('default:'):
                        return str(var_value) if var_value else transform.split(':', 1)[1]
                
                return str(var_value)
            
            result = re.sub(pattern, replace_func, result)
        
        return result
    
    def _process_conditionals(self, template: str, variables: Dict[str, Any]) -> str:
        """
        Process conditional sections.
        
        Format:
        // @if ${variable_name}
        // ... content ...
        // @endif
        """
        lines = template.split('\n')
        result_lines = []
        skip_until = None
        
        for line in lines:
            stripped = line.strip()
            
            # Check for @if
            if stripped.startswith('// @if'):
                condition = stripped.split('// @if', 1)[1].strip()
                # Extract variable name
                var_match = re.search(r'\$\{(\w+)\}', condition)
                if var_match:
                    var_name = var_match.group(1)
                    if var_name not in variables or not variables.get(var_name):
                        skip_until = '// @endif'
                continue
            
            # Check for @endif
            if stripped.startswith('// @endif'):
                skip_until = None
                continue
            
            # Skip if in conditional block
            if skip_until:
                continue
            
            result_lines.append(line)
        
        return '\n'.join(result_lines)
    
    def _cleanup(self, template: str) -> str:
        """Clean up template artifacts"""
        # Remove template comments
        lines = [
            line for line in template.split('\n')
            if not line.strip().startswith('// @')
        ]
        
        # Remove multiple consecutive blank lines
        result = '\n'.join(lines)
        result = re.sub(r'\n\n\n+', '\n\n', result)
        
        return result.strip()
    
    def _generate_metadata_header(self, metadata: Dict[str, Any]) -> str:
        """Generate metadata header for template"""
        header = []
        
        if 'description' in metadata:
            header.append(f"// @description: {metadata['description']}")
        
        if 'category' in metadata:
            header.append(f"// @category: {metadata['category']}")
        
        for var_info in metadata.get('variables', []):
            header.append(f"// @variable: {var_info}")
        
        return '\n'.join(header)

