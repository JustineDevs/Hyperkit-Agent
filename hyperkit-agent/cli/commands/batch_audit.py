"""
CLI Commands for Batch Audit Operations
"""

import click
import asyncio
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


@click.group()
def batch_audit():
    """Batch audit operations"""
    pass


@batch_audit.command()
@click.argument('directory', type=click.Path(exists=True))
@click.option('--pattern', default='*.sol', help='File pattern to match (default: *.sol)')
@click.option('--format', 'formats', multiple=True, default=['json', 'html'], 
              help='Export formats: json, html, markdown, csv, pdf, excel')
@click.option('--output', '-o', default=None, help='Output directory')
@click.option('--aggregate/--no-aggregate', default=True, help='Create aggregated summary')
def directory(directory, pattern, formats, output, aggregate):
    """Audit all contracts in a directory"""
    from services.audit.batch_auditor import BatchAuditor
    
    logger.info(f"Starting batch audit of directory: {directory}")
    click.echo(f"🔍 Auditing contracts in: {directory}")
    click.echo(f"📁 Pattern: {pattern}")
    click.echo(f"📤 Export formats: {', '.join(formats)}")
    
    # Create batch auditor
    auditor = BatchAuditor()
    
    # Run audit
    try:
        results = asyncio.run(
            auditor.audit_directory(
                directory=directory,
                pattern=pattern,
                export_formats=list(formats),
                output_dir=output,
                aggregate=aggregate
            )
        )
        
        # Display summary
        click.echo("\n✅ Batch audit complete!")
        click.echo(f"Total contracts: {results['total_contracts']}")
        click.echo(f"Successful: {results['successful']}")
        click.echo(f"Failed: {results['failed']}")
        
        if results.get('summary'):
            summary = results['summary']
            click.echo(f"\nRisk Score: {summary.get('risk_score', 0)}/100")
            click.echo(f"Total Findings: {summary.get('total_findings', 0)}")
            
            recommendations = summary.get('recommendations', [])
            if recommendations:
                click.echo("\nRecommendations:")
                for rec in recommendations:
                    click.echo(f"  • {rec}")
        
        # Show output location
        if output:
            click.echo(f"\n📂 Reports saved to: {output}")
    
    except Exception as e:
        logger.error(f"Batch audit failed: {e}", exc_info=True)
        click.echo(f"\n❌ Error: {str(e)}", err=True)
        raise click.Abort()


@batch_audit.command()
@click.argument('contracts', nargs=-1, required=True)
@click.option('--format', 'formats', multiple=True, default=['json', 'html'],
              help='Export formats: json, html, markdown, csv, pdf, excel')
@click.option('--output', '-o', default=None, help='Output directory')
@click.option('--aggregate/--no-aggregate', default=True, help='Create aggregated summary')
def files(contracts, formats, output, aggregate):
    """Audit specific contract files"""
    from services.audit.batch_auditor import BatchAuditor
    
    logger.info(f"Starting batch audit of {len(contracts)} contracts")
    click.echo(f"🔍 Auditing {len(contracts)} contracts")
    click.echo(f"📤 Export formats: {', '.join(formats)}")
    
    # Prepare contract list
    contract_list = []
    for contract_path in contracts:
        path = Path(contract_path)
        if not path.exists():
            click.echo(f"⚠️  Warning: {contract_path} not found", err=True)
            continue
        
        contract_list.append({
            'name': path.stem,
            'path': str(path)
        })
    
    if not contract_list:
        click.echo("❌ No valid contracts found", err=True)
        raise click.Abort()
    
    # Create batch auditor
    auditor = BatchAuditor()
    
    # Run audit
    try:
        results = asyncio.run(
            auditor.audit_batch(
                contracts=contract_list,
                export_formats=list(formats),
                output_dir=output,
                aggregate=aggregate
            )
        )
        
        # Display summary
        click.echo("\n✅ Batch audit complete!")
        click.echo(f"Total contracts: {results['total_contracts']}")
        click.echo(f"Successful: {results['successful']}")
        click.echo(f"Failed: {results['failed']}")
        
        if results.get('summary'):
            summary = results['summary']
            click.echo(f"\nRisk Score: {summary.get('risk_score', 0)}/100")
            click.echo(f"Total Findings: {summary.get('total_findings', 0)}")
        
        # Show output location
        if output:
            click.echo(f"\n📂 Reports saved to: {output}")
    
    except Exception as e:
        logger.error(f"Batch audit failed: {e}", exc_info=True)
        click.echo(f"\n❌ Error: {str(e)}", err=True)
        raise click.Abort()


# Add to main CLI
if __name__ == '__main__':
    batch_audit()

