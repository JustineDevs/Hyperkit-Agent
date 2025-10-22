"""
MCP Server for Obsidian Integration
Provides HTTP API for Obsidian vault operations
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import asyncio
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import re

class ObsidianMCPServer:
    """MCP Server for Obsidian operations"""
    
    def __init__(self, vault_path: str = "/vault"):
        self.vault_path = Path(vault_path)
        self.obsidian_host = os.getenv("OBSIDIAN_HOST", "host.docker.internal")
        self.obsidian_api_key = os.getenv("OBSIDIAN_API_KEY")
        
    def search_notes(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search notes in the vault"""
        try:
            notes = []
            query_lower = query.lower()
            
            # Search through all markdown files
            for md_file in self.vault_path.rglob("*.md"):
                try:
                    content = md_file.read_text(encoding='utf-8')
                    if query_lower in content.lower():
                        notes.append({
                            "path": str(md_file.relative_to(self.vault_path)),
                            "name": md_file.stem,
                            "content": content[:500],  # First 500 chars
                            "size": len(content),
                            "modified": md_file.stat().st_mtime
                        })
                        
                        if len(notes) >= limit:
                            break
                            
                except Exception as e:
                    continue
            
            return notes
            
        except Exception as e:
            return []
    
    def get_note_content(self, note_path: str) -> Optional[str]:
        """Get full content of a note"""
        try:
            full_path = self.vault_path / note_path
            if full_path.exists() and full_path.suffix == '.md':
                return full_path.read_text(encoding='utf-8')
            return None
        except Exception:
            return None
    
    def get_all_notes(self) -> List[Dict[str, Any]]:
        """Get all notes in the vault"""
        try:
            notes = []
            for md_file in self.vault_path.rglob("*.md"):
                try:
                    content = md_file.read_text(encoding='utf-8')
                    notes.append({
                        "path": str(md_file.relative_to(self.vault_path)),
                        "name": md_file.stem,
                        "content": content[:200],  # First 200 chars
                        "size": len(content),
                        "modified": md_file.stat().st_mtime
                    })
                except Exception:
                    continue
            
            return notes
        except Exception:
            return []
    
    def get_note_metadata(self, note_path: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a note"""
        try:
            full_path = self.vault_path / note_path
            if not full_path.exists():
                return None
            
            content = full_path.read_text(encoding='utf-8')
            
            # Extract frontmatter
            frontmatter = {}
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    try:
                        import yaml
                        frontmatter = yaml.safe_load(parts[1]) or {}
                    except:
                        pass
            
            # Extract tags
            tags = re.findall(r'#(\w+)', content)
            
            # Extract links
            links = re.findall(r'\[\[([^\]]+)\]\]', content)
            
            return {
                "path": note_path,
                "name": full_path.stem,
                "size": len(content),
                "modified": full_path.stat().st_mtime,
                "frontmatter": frontmatter,
                "tags": list(set(tags)),
                "links": list(set(links))
            }
            
        except Exception:
            return None
    
    def get_vault_stats(self) -> Dict[str, Any]:
        """Get vault statistics"""
        try:
            total_notes = 0
            total_size = 0
            folders = set()
            
            for md_file in self.vault_path.rglob("*.md"):
                total_notes += 1
                total_size += md_file.stat().st_size
                folders.add(str(md_file.parent.relative_to(self.vault_path)))
            
            return {
                "total_notes": total_notes,
                "total_size": total_size,
                "total_folders": len(folders),
                "folders": list(folders),
                "vault_path": str(self.vault_path)
            }
            
        except Exception:
            return {"total_notes": 0, "total_size": 0, "total_folders": 0, "folders": []}
    
    def stream_notes(self, query: str = ""):
        """Stream notes as they are found"""
        try:
            for md_file in self.vault_path.rglob("*.md"):
                try:
                    content = md_file.read_text(encoding='utf-8')
                    
                    if not query or query.lower() in content.lower():
                        note_data = {
                            "path": str(md_file.relative_to(self.vault_path)),
                            "name": md_file.stem,
                            "content": content[:200],
                            "size": len(content),
                            "modified": md_file.stat().st_mtime
                        }
                        print(json.dumps(note_data))
                        
                except Exception:
                    continue
                    
        except Exception:
            pass

class MCPRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler for MCP server"""
    
    def __init__(self, *args, mcp_server=None, **kwargs):
        self.mcp_server = mcp_server
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET requests"""
        try:
            if self.path == '/':
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "OK", "message": "MCP Obsidian Server is running"}).encode())
                return
            
            elif self.path == '/health':
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "healthy"}).encode())
                return
            
            elif self.path == '/notes':
                notes = self.mcp_server.get_all_notes()
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(notes).encode())
                return
            
            elif self.path.startswith('/search'):
                # Parse query parameters
                parsed_url = urllib.parse.urlparse(self.path)
                query_params = urllib.parse.parse_qs(parsed_url.query)
                query = query_params.get('q', [''])[0]
                limit = int(query_params.get('limit', ['10'])[0])
                
                notes = self.mcp_server.search_notes(query, limit)
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(notes).encode())
                return
            
            elif self.path.startswith('/note/'):
                note_path = self.path[6:]  # Remove '/note/'
                content = self.mcp_server.get_note_content(note_path)
                
                if content:
                    self.send_response(200)
                    self.send_header('Content-type', 'text/markdown')
                    self.end_headers()
                    self.wfile.write(content.encode())
                else:
                    self.send_response(404)
                    self.end_headers()
                return
            
            elif self.path == '/stats':
                stats = self.mcp_server.get_vault_stats()
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(stats).encode())
                return
            
            else:
                self.send_response(404)
                self.end_headers()
                
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
    
    def do_POST(self):
        """Handle POST requests"""
        try:
            if self.path == '/search':
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode())
                
                query = data.get('query', '')
                limit = data.get('limit', 10)
                
                notes = self.mcp_server.search_notes(query, limit)
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(notes).encode())
                return
            
            else:
                self.send_response(404)
                self.end_headers()
                
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
    
    def log_message(self, format, *args):
        """Suppress default logging"""
        pass

def create_handler(mcp_server):
    """Create request handler with MCP server"""
    def handler(*args, **kwargs):
        return MCPRequestHandler(*args, mcp_server=mcp_server, **kwargs)
    return handler

def main():
    """Main function to run MCP server"""
    vault_path = os.getenv("VAULT_PATH", "/vault")
    
    # Create MCP server
    mcp_server = ObsidianMCPServer(vault_path)
    
    # Create HTTP server
    handler = create_handler(mcp_server)
    httpd = HTTPServer(('0.0.0.0', 27125), handler)
    
    print(f"MCP Obsidian server starting on port 27125")
    print(f"Vault path: {vault_path}")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("Shutting down MCP server...")
        httpd.shutdown()

if __name__ == "__main__":
    main()
