"""
CLI Commands for Template Operations
"""

import click
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


@click.group()
def template():
    """Smart contract template operations"""
    pass


@template.command()
def list():
    """List all available templates"""
    from services.templates.template_engine import TemplateEngine
    
    engine = TemplateEngine()
    templates = engine.list_templates()
    
    if not templates:
        click.echo("No templates found")
        return
    
    click.echo(f"📚 Available Templates: {len(templates)}\n")
    
    # Group by category
    by_category = {}
    for tmpl in templates:
        category = tmpl.get('category', 'general')
        if category not in by_category:
            by_category[category] = []
        by_category[category].append(tmpl)
    
    # Display by category
    for category, tmpls in sorted(by_category.items()):
        click.echo(f"  {category.upper()}")
        for tmpl in tmpls:
            click.echo(f"    • {tmpl['name']}")
            if tmpl.get('description'):
                click.echo(f"      {tmpl['description']}")
        click.echo()


@template.command()
@click.argument('template_name')
def show(template_name):
    """Show template details and required variables"""
    from services.templates.template_engine import TemplateEngine
    
    engine = TemplateEngine()
    templates = engine.list_templates()
    
    # Find template
    tmpl = next((t for t in templates if t['name'] == template_name), None)
    
    if not tmpl:
        click.echo(f"❌ Template not found: {template_name}", err=True)
        return
    
    click.echo(f"📄 Template: {tmpl['name']}\n")
    click.echo(f"Description: {tmpl.get('description', 'No description')}")
    click.echo(f"Category: {tmpl.get('category', 'general')}")
    click.echo(f"\nRequired Variables:")
    
    for var in tmpl.get('variables', []):
        click.echo(f"  • {var}")


@template.command()
@click.argument('template_name')
@click.argument('output_file')
@click.option('--var', '-v', multiple=True, help='Variable: name=value')
@click.option('--vars-file', type=click.Path(exists=True), help='JSON file with variables')
@click.option('--no-validate', is_flag=True, help='Skip variable validation')
def generate(template_name, output_file, var, vars_file, no_validate):
    """
    Generate contract from template
    
    Examples:
      hyperagent template generate ERC20 MyToken.sol -v token_name=MyToken -v token_symbol=MTK
      
      hyperagent template generate ERC20 MyToken.sol --vars-file vars.json
    """
    from services.templates.template_engine import TemplateEngine
    
    logger.info(f"Generating contract from template: {template_name}")
    
    # Collect variables
    variables = {}
    
    # Load from file if provided
    if vars_file:
        with open(vars_file, 'r') as f:
            variables.update(json.load(f))
    
    # Add command-line variables (override file)
    for v in var:
        if '=' not in v:
            click.echo(f"⚠️  Warning: Invalid variable format: {v}", err=True)
            continue
        
        key, value = v.split('=', 1)
        # Try to parse as JSON for complex types
        try:
            variables[key] = json.loads(value)
        except json.JSONDecodeError:
            variables[key] = value
    
    click.echo(f"📝 Generating contract from template: {template_name}")
    click.echo(f"📤 Output: {output_file}")
    click.echo(f"🔧 Variables: {len(variables)}")
    
    # Generate contract
    try:
        engine = TemplateEngine()
        contract_code = engine.generate(
            template_name=template_name,
            variables=variables,
            validate=not no_validate
        )
        
        # Write output
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(contract_code, encoding='utf-8')
        
        click.echo(f"\n✅ Contract generated successfully!")
        click.echo(f"📂 Saved to: {output_file}")
        click.echo(f"📊 Size: {len(contract_code)} characters")
    
    except ValueError as e:
        click.echo(f"\n❌ Validation error: {e}", err=True)
        raise click.Abort()
    
    except Exception as e:
        logger.error(f"Template generation failed: {e}", exc_info=True)
        click.echo(f"\n❌ Error: {e}", err=True)
        raise click.Abort()


@template.command()
@click.argument('name')
@click.argument('template_file', type=click.Path(exists=True))
@click.option('--description', '-d', help='Template description')
@click.option('--category', '-c', default='general', help='Template category')
def create(name, template_file, description, category):
    """Create a new template from file"""
    from services.templates.template_engine import TemplateEngine
    
    logger.info(f"Creating template: {name}")
    
    # Load template content
    template_path = Path(template_file)
    content = template_path.read_text(encoding='utf-8')
    
    # Prepare metadata
    metadata = {
        'description': description or f"Custom template: {name}",
        'category': category,
        'variables': []  # Auto-detect or manually specify
    }
    
    # Create template
    engine = TemplateEngine()
    engine.create_template(name, content, metadata)
    
    click.echo(f"✅ Template created: {name}")
    click.echo(f"📁 Category: {category}")
    click.echo(f"💡 Tip: Add @variable comments to define required variables")


# Add to main CLI
if __name__ == '__main__':
    template()

