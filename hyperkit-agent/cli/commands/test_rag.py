"""
RAG Testing CLI Command

Test IPFS RAG connections and functionality.
"""

import asyncio
import json
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from services.rag.enhanced_retriever import get_rag_retriever

console = Console()


async def test_rag_connections():
    """Test all RAG connections and display results."""
    
    console.print(Panel.fit("Testing RAG Connections (IPFS Pinata Only)", style="bold blue"))
    
    # Test 1: Enhanced RAG Retriever
    console.print("\n1. Testing Enhanced RAG Retriever...")
    try:
        retriever = get_rag_retriever()
        connection_results = await retriever.test_connections()
        
        # Create results table
        table = Table(title="RAG Connection Status")
        table.add_column("Source", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Details", style="yellow")
        
        for source, status in connection_results.items():
            status_text = status["status"]
            details = ""
            
            if "error" in status:
                details = status["error"]
            elif "file_count" in status:
                details = f"{status['file_count']} files"
            elif "note" in status:
                details = status["note"]
            
            table.add_row(source.title(), status_text, details)
        
        console.print(table)
        
    except Exception as e:
        console.print(f"   Enhanced Retriever: FAIL ERROR - {e}")
    
    # Test 2: Content Retrieval
    console.print("\n2. Testing Content Retrieval...")
    try:
        retriever = get_rag_retriever()
        test_content = await retriever.retrieve("smart contract security", max_results=3)
        
        console.print(f"   Content Length: {len(test_content)} characters")
        console.print(f"   Has Content: {'PASS' if len(test_content) > 100 else 'FAIL'}")
        
        if len(test_content) > 200:
            preview = test_content[:200] + "..."
        else:
            preview = test_content
        
        console.print(Panel(preview, title="Content Preview", style="dim"))
        
    except Exception as e:
        console.print(f"   Content Retrieval: FAIL ERROR - {e}")


def test_rag_command():
    """CLI command to test RAG connections."""
    try:
        asyncio.run(test_rag_connections())
    except KeyboardInterrupt:
        console.print("\nFAIL Test interrupted by user")
    except Exception as e:
        console.print(f"\nTest failed: {e}")


if __name__ == "__main__":
    test_rag_command()