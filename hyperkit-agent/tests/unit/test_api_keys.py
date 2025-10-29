#!/usr/bin/env python3
"""
API Key Validation Script for HyperKit AI Agent
Tests all API keys used in the system for validity and connectivity
"""

import os
import sys
import requests
from dotenv import load_dotenv
from typing import Tuple, List
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_google_api() -> Tuple[str, str, bool]:
    """Test Google Gemini API key validity."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key or api_key == "your_google_api_key_here":
        return ("GOOGLE_API_KEY", "not set or using placeholder", False)
    
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            models = response.json().get('models', [])
            model_names = [model.get('name', '') for model in models]
            return ("GOOGLE_API_KEY", f"working (found {len(models)} models)", True)
        elif response.status_code == 403:
            return ("GOOGLE_API_KEY", "invalid API key", False)
        elif response.status_code == 429:
            return ("GOOGLE_API_KEY", "rate limited", False)
        else:
            return ("GOOGLE_API_KEY", f"error {response.status_code}: {response.text[:100]}", False)
    except requests.exceptions.RequestException as e:
        return ("GOOGLE_API_KEY", f"connection error: {str(e)[:100]}", False)


def test_openai_api() -> Tuple[str, str, bool]:
    """Test OpenAI API key validity."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "your_openai_api_key_here":
        return ("OPENAI_API_KEY", "not set or using placeholder", False)
    
    try:
        headers = {"Authorization": f"Bearer {api_key}"}
        response = requests.get("https://api.openai.com/v1/models", headers=headers, timeout=10)
        
        if response.status_code == 200:
            models = response.json().get('data', [])
            model_names = [model.get('id', '') for model in models]
            return ("OPENAI_API_KEY", f"working (found {len(models)} models)", True)
        elif response.status_code == 401:
            return ("OPENAI_API_KEY", "invalid API key", False)
        elif response.status_code == 429:
            return ("OPENAI_API_KEY", "rate limited", False)
        else:
            return ("OPENAI_API_KEY", f"error {response.status_code}: {response.text[:100]}", False)
    except requests.exceptions.RequestException as e:
        return ("OPENAI_API_KEY", f"connection error: {str(e)[:100]}", False)


# DEPRECATED: Obsidian MCP API test removed - Obsidian RAG is deprecated
# IPFS Pinata RAG is now the exclusive RAG backend
# This test function is kept for backward compatibility but always returns "deprecated"
def test_obsidian_mcp_api() -> Tuple[str, str, bool]:
    """DEPRECATED: Obsidian MCP API - use IPFS Pinata RAG instead."""
    return ("OBSIDIAN_MCP_API_KEY", "deprecated - use PINATA_API_KEY instead", False)


def test_langsmith_api() -> Tuple[str, str, bool]:
    """Test LangSmith API key validity."""
    api_key = os.getenv("LANGSMITH_API_KEY")
    if not api_key or api_key == "your_langsmith_api_key_here":
        return ("LANGSMITH_API_KEY", "not set or using placeholder (optional)", False)
    
    try:
        headers = {"Authorization": f"Bearer {api_key}"}
        # Use the correct LangSmith API endpoint
        response = requests.get("https://api.smith.langchain.com/api/v1/projects", headers=headers, timeout=10)
        
        if response.status_code == 200:
            projects = response.json().get('projects', [])
            return ("LANGSMITH_API_KEY", f"working (found {len(projects)} projects)", True)
        elif response.status_code == 401:
            return ("LANGSMITH_API_KEY", "invalid API key", False)
        elif response.status_code == 403:
            return ("LANGSMITH_API_KEY", "forbidden", False)
        elif response.status_code == 404:
            return ("LANGSMITH_API_KEY", "endpoint not found - check API key format", False)
        else:
            return ("LANGSMITH_API_KEY", f"error {response.status_code}: {response.text[:100]}", False)
    except requests.exceptions.RequestException as e:
        return ("LANGSMITH_API_KEY", f"connection error: {str(e)[:100]}", False)


def test_hyperion_rpc() -> Tuple[str, str, bool]:
    """Test Hyperion testnet RPC connectivity."""
    rpc_url = os.getenv("HYPERION_RPC_URL", "https://hyperion-testnet.metisdevops.link")
    
    try:
        payload = {
            "jsonrpc": "2.0",
            "method": "eth_chainId",
            "params": [],
            "id": 1
        }
        response = requests.post(rpc_url, json=payload, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if 'result' in data:
                chain_id = int(data['result'], 16)
                return ("HYPERION_RPC", f"working (chain ID: {chain_id})", True)
            else:
                return ("HYPERION_RPC", f"error: {data.get('error', 'Unknown error')}", False)
        else:
            return ("HYPERION_RPC", f"error {response.status_code}: {response.text[:100]}", False)
    except requests.exceptions.RequestException as e:
        return ("HYPERION_RPC", f"connection error: {str(e)[:100]}", False)


# DEPRECATED: Docker test removed - Docker/MCP deprecated
# Docker is no longer required for Hyperion-only operation
def test_docker_availability() -> Tuple[str, str, bool]:
    """DEPRECATED: Docker removed - not required."""
    return ("DOCKER", "deprecated - not required for Hyperion-only operation", False)


def print_results(results: List[Tuple[str, str, bool]]) -> None:
    """Print formatted results."""
    print("\n" + "=" * 80)
    print("🔐 API KEY VALIDATION RESULTS")
    print("=" * 80)
    
    working_count = 0
    total_count = len(results)
    
    for name, status, is_working in results:
        status_icon = "✅" if is_working else "❌"
        print(f"{status_icon} {name:<25} {status}")
        if is_working:
            working_count += 1
    
    print("=" * 80)
    print(f"📊 SUMMARY: {working_count}/{total_count} APIs working")
    
    if working_count == total_count:
        print("🎉 All APIs are working correctly!")
    elif working_count > 0:
        print("⚠️  Some APIs are not working. Check the errors above.")
    else:
        print("❌ No APIs are working. Please check your configuration.")
    
    print("=" * 80)


def main():
    """Main function to run all API tests."""
    print("🚀 Starting API Key Validation for HyperKit AI Agent...")
    
    # Load environment variables
    load_dotenv()
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("❌ .env file not found. Please create one from env.example")
        return False
    
    # Run all tests
    tests = [
        test_google_api,
        test_openai_api,
        test_obsidian_mcp_api,
        test_langsmith_api,
        test_hyperion_rpc,
        test_docker_availability
    ]
    
    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            logger.error(f"Error running {test_func.__name__}: {e}")
            results.append((test_func.__name__.replace('test_', '').upper(), f"test error: {str(e)[:100]}", False))
    
    # Print results
    print_results(results)
    
    # Return success status
    working_count = sum(1 for _, _, is_working in results if is_working)
    return working_count > 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
