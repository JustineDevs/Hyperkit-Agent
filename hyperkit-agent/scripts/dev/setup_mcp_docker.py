#!/usr/bin/env python3
"""
DEPRECATED: MCP Docker Setup Script for HyperKit AI Agent

⚠️  WARNING: This script is DEPRECATED and no longer used.
   Obsidian RAG integration has been completely removed.
   IPFS Pinata is now the exclusive RAG backend.
   
   This script is kept for reference only and should not be used.
   See docs/RAG_TEMPLATES/UPLOAD_PROCESS.md for current RAG setup.
"""

import os
import sys
import subprocess
import time
import requests
from pathlib import Path

def check_docker_running():
    """Check if Docker is running."""
    try:
        result = subprocess.run(["docker", "ps"], capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False

def build_mcp_image():
    """Build the MCP Docker image."""
    print("🔨 Building MCP Docker image...")
    try:
        result = subprocess.run([
            "docker", "build", 
            "-f", "Dockerfile.mcp", 
            "-t", "mcp/obsidian", 
            "."
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("  ✅ MCP Docker image built successfully")
            return True
        else:
            print(f"  ❌ Failed to build image: {result.stderr}")
            return False
    except Exception as e:
        print(f"  ❌ Error building image: {e}")
        return False

def start_mcp_container():
    """Start the MCP Docker container."""
    print("🚀 Starting MCP Docker container...")
    
    # Check if container already exists
    try:
        result = subprocess.run([
            "docker", "ps", "-a", "--filter", "name=obsidian-mcp", "--format", "{{.Names}}"
        ], capture_output=True, text=True)
        
        if "obsidian-mcp" in result.stdout:
            print("  📦 Container already exists, removing...")
            subprocess.run(["docker", "rm", "-f", "obsidian-mcp"], capture_output=True)
    except Exception:
        pass
    
    # Start new container
    try:
        # Get API key from environment or use a default for testing
        api_key = os.getenv("OBSIDIAN_MCP_API_KEY", "test-key")
        
        env_vars = {
            "OBSIDIAN_HOST": "host.docker.internal",
            "OBSIDIAN_API_KEY": api_key,
            "OBSIDIAN_MCP_API_KEY": api_key,
            "VAULT_PATH": "/vault"
        }
        
        env_args = []
        for key, value in env_vars.items():
            env_args.extend(["-e", f"{key}={value}"])
        
        result = subprocess.run([
            "docker", "run", "-d",
            "--name", "obsidian-mcp",
            "-p", "27125:27125",
            *env_args,
            "mcp/obsidian"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("  ✅ MCP Docker container started successfully")
            return True
        else:
            print(f"  ❌ Failed to start container: {result.stderr}")
            return False
    except Exception as e:
        print(f"  ❌ Error starting container: {e}")
        return False

def wait_for_mcp_api():
    """Wait for MCP API to be ready."""
    print("⏳ Waiting for MCP API to be ready...")
    
    max_attempts = 30
    for attempt in range(max_attempts):
        try:
            response = requests.get("http://127.0.0.1:27125/health", timeout=2)
            if response.status_code == 200:
                print("  ✅ MCP API is ready")
                return True
        except requests.exceptions.RequestException:
            pass
        
        print(f"  ⏳ Attempt {attempt + 1}/{max_attempts}...")
        time.sleep(2)
    
    print("  ❌ MCP API did not become ready")
    return False

def test_mcp_connection():
    """Test MCP connection."""
    print("🔌 Testing MCP connection...")
    
    try:
        api_key = os.getenv("OBSIDIAN_MCP_API_KEY", "test-key")
        headers = {"Authorization": f"Bearer {api_key}"}
        response = requests.get("http://127.0.0.1:27124/", headers=headers, timeout=5)
        
        if response.status_code == 200:
            print("  ✅ MCP connection successful")
            return True
        else:
            print(f"  ❌ MCP connection failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"  ❌ MCP connection error: {e}")
        return False

def main():
    """Main setup function."""
    print("🚀 Setting up MCP Docker for HyperKit AI Agent...")
    print("=" * 60)
    
    # Check Docker
    if not check_docker_running():
        print("❌ Docker is not running. Please start Docker Desktop and try again.")
        return False
    
    # Build image
    if not build_mcp_image():
        print("❌ Failed to build MCP Docker image.")
        return False
    
    # Start container
    if not start_mcp_container():
        print("❌ Failed to start MCP Docker container.")
        return False
    
    # Wait for API
    if not wait_for_mcp_api():
        print("❌ MCP API did not become ready.")
        return False
    
    # Test connection
    if not test_mcp_connection():
        print("❌ MCP connection test failed.")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 MCP Docker setup completed successfully!")
    print("=" * 60)
    print("\n📋 Next Steps:")
    print("1. Test the integration:")
    print("   python test_api_keys.py")
    print("\n2. Run the agent:")
    print("   python cli.py generate 'Create an ERC20 token' --use-rag")
    print("\n3. Check container status:")
    print("   docker ps")
    print("\n4. View container logs:")
    print("   docker logs obsidian-mcp")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
