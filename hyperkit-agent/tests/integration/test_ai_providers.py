"""
Integration tests for AI providers
Tests all configured AI providers for contract generation
"""

import pytest
import os
import asyncio
from unittest.mock import patch, AsyncMock
from services.generation.generator import ContractGenerator

class TestAIProviders:
    """Test AI provider integrations."""
    
    @pytest.fixture
    def generator(self):
        """Create contract generator instance."""
        return ContractGenerator()
    
    @pytest.mark.asyncio
    async def test_openai_provider(self, generator):
        """Test OpenAI provider integration."""
        if not os.getenv('OPENAI_API_KEY'):
            pytest.skip("OpenAI API key not configured")
        
        with patch('openai.AsyncOpenAI') as mock_client:
            mock_response = AsyncMock()
            mock_response.choices = [AsyncMock()]
            mock_response.choices[0].message.content = "pragma solidity ^0.8.0;\n\ncontract TestContract {\n    string public name = \"Test\";\n}"
            
            mock_client.return_value.chat.completions.create.return_value = mock_response
            
            result = await generator.generate_contract(
                "Create a simple ERC20 token",
                provider="openai"
            )
            
            assert result["status"] == "success"
            assert "contract_code" in result
            assert "pragma solidity" in result["contract_code"]
    
    @pytest.mark.asyncio
    async def test_anthropic_provider(self, generator):
        """Test Anthropic provider integration."""
        if not os.getenv('ANTHROPIC_API_KEY'):
            pytest.skip("Anthropic API key not configured")
        
        with patch('anthropic.AsyncAnthropic') as mock_client:
            mock_response = AsyncMock()
            mock_response.content = [AsyncMock()]
            mock_response.content[0].text = "pragma solidity ^0.8.0;\n\ncontract TestContract {\n    string public name = \"Test\";\n}"
            
            mock_client.return_value.messages.create.return_value = mock_response
            
            result = await generator.generate_contract(
                "Create a simple ERC20 token",
                provider="anthropic"
            )
            
            assert result["status"] == "success"
            assert "contract_code" in result
            assert "pragma solidity" in result["contract_code"]
    
    @pytest.mark.asyncio
    async def test_google_provider(self, generator):
        """Test Google Gemini provider integration."""
        if not os.getenv('GOOGLE_API_KEY'):
            pytest.skip("Google API key not configured")
        
        with patch('google.generativeai.GenerativeModel') as mock_model:
            mock_response = AsyncMock()
            mock_response.text = "pragma solidity ^0.8.0;\n\ncontract TestContract {\n    string public name = \"Test\";\n}"
            
            mock_model.return_value.generate_content_async.return_value = mock_response
            
            result = await generator.generate_contract(
                "Create a simple ERC20 token",
                provider="google"
            )
            
            assert result["status"] == "success"
            assert "contract_code" in result
            assert "pragma solidity" in result["contract_code"]
    
    @pytest.mark.asyncio
    async def test_deepseek_provider(self, generator):
        """Test DeepSeek provider integration."""
        if not os.getenv('DEEPSEEK_API_KEY'):
            pytest.skip("DeepSeek API key not configured")
        
        with patch('openai.AsyncOpenAI') as mock_client:
            mock_response = AsyncMock()
            mock_response.choices = [AsyncMock()]
            mock_response.choices[0].message.content = "pragma solidity ^0.8.0;\n\ncontract TestContract {\n    string public name = \"Test\";\n}"
            
            mock_client.return_value.chat.completions.create.return_value = mock_response
            
            result = await generator.generate_contract(
                "Create a simple ERC20 token",
                provider="deepseek"
            )
            
            assert result["status"] == "success"
            assert "contract_code" in result
            assert "pragma solidity" in result["contract_code"]
    
    @pytest.mark.asyncio
    async def test_xai_provider(self, generator):
        """Test xAI provider integration."""
        if not os.getenv('XAI_API_KEY'):
            pytest.skip("xAI API key not configured")
        
        with patch('openai.AsyncOpenAI') as mock_client:
            mock_response = AsyncMock()
            mock_response.choices = [AsyncMock()]
            mock_response.choices[0].message.content = "pragma solidity ^0.8.0;\n\ncontract TestContract {\n    string public name = \"Test\";\n}"
            
            mock_client.return_value.chat.completions.create.return_value = mock_response
            
            result = await generator.generate_contract(
                "Create a simple ERC20 token",
                provider="xai"
            )
            
            assert result["status"] == "success"
            assert "contract_code" in result
            assert "pragma solidity" in result["contract_code"]
    
    @pytest.mark.asyncio
    async def test_dashscope_provider(self, generator):
        """Test DashScope provider integration."""
        if not os.getenv('DASHSCOPE_API_KEY'):
            pytest.skip("DashScope API key not configured")
        
        with patch('dashscope.Generation') as mock_generation:
            mock_response = AsyncMock()
            mock_response.output = {"text": "pragma solidity ^0.8.0;\n\ncontract TestContract {\n    string public name = \"Test\";\n}"}
            
            mock_generation.call.return_value = mock_response
            
            result = await generator.generate_contract(
                "Create a simple ERC20 token",
                provider="dashscope"
            )
            
            assert result["status"] == "success"
            assert "contract_code" in result
            assert "pragma solidity" in result["contract_code"]
    
    @pytest.mark.asyncio
    async def test_provider_fallback(self, generator):
        """Test provider fallback mechanism."""
        with patch.object(generator, '_select_ai_provider') as mock_select:
            mock_select.return_value = "openai"
            
            with patch('openai.AsyncOpenAI') as mock_client:
                mock_response = AsyncMock()
                mock_response.choices = [AsyncMock()]
                mock_response.choices[0].message.content = "pragma solidity ^0.8.0;\n\ncontract TestContract {\n    string public name = \"Test\";\n}"
                
                mock_client.return_value.chat.completions.create.return_value = mock_response
                
                result = await generator.generate_contract(
                    "Create a simple ERC20 token"
                )
                
                assert result["status"] == "success"
                assert "contract_code" in result
    
    @pytest.mark.asyncio
    async def test_provider_error_handling(self, generator):
        """Test provider error handling."""
        with patch('openai.AsyncOpenAI') as mock_client:
            mock_client.return_value.chat.completions.create.side_effect = Exception("API Error")
            
            result = await generator.generate_contract(
                "Create a simple ERC20 token",
                provider="openai"
            )
            
            assert result["status"] == "error"
            assert "error" in result
    
    @pytest.mark.asyncio
    async def test_provider_timeout(self, generator):
        """Test provider timeout handling."""
        with patch('openai.AsyncOpenAI') as mock_client:
            mock_client.return_value.chat.completions.create.side_effect = asyncio.TimeoutError()
            
            result = await generator.generate_contract(
                "Create a simple ERC20 token",
                provider="openai"
            )
            
            assert result["status"] == "error"
            assert "timeout" in result["error"].lower()
    
    @pytest.mark.asyncio
    async def test_provider_rate_limit(self, generator):
        """Test provider rate limit handling."""
        with patch('openai.AsyncOpenAI') as mock_client:
            mock_client.return_value.chat.completions.create.side_effect = Exception("Rate limit exceeded")
            
            result = await generator.generate_contract(
                "Create a simple ERC20 token",
                provider="openai"
            )
            
            assert result["status"] == "error"
            assert "rate limit" in result["error"].lower()
    
    @pytest.mark.asyncio
    async def test_provider_authentication(self, generator):
        """Test provider authentication handling."""
        with patch('openai.AsyncOpenAI') as mock_client:
            mock_client.return_value.chat.completions.create.side_effect = Exception("Invalid API key")
            
            result = await generator.generate_contract(
                "Create a simple ERC20 token",
                provider="openai"
            )
            
            assert result["status"] == "error"
            assert "authentication" in result["error"].lower() or "api key" in result["error"].lower()
    
    @pytest.mark.asyncio
    async def test_provider_quota_exceeded(self, generator):
        """Test provider quota exceeded handling."""
        with patch('openai.AsyncOpenAI') as mock_client:
            mock_client.return_value.chat.completions.create.side_effect = Exception("Quota exceeded")
            
            result = await generator.generate_contract(
                "Create a simple ERC20 token",
                provider="openai"
            )
            
            assert result["status"] == "error"
            assert "quota" in result["error"].lower()
    
    @pytest.mark.asyncio
    async def test_provider_network_error(self, generator):
        """Test provider network error handling."""
        with patch('openai.AsyncOpenAI') as mock_client:
            mock_client.return_value.chat.completions.create.side_effect = Exception("Network error")
            
            result = await generator.generate_contract(
                "Create a simple ERC20 token",
                provider="openai"
            )
            
            assert result["status"] == "error"
            assert "network" in result["error"].lower()
    
    @pytest.mark.asyncio
    async def test_provider_retry_mechanism(self, generator):
        """Test provider retry mechanism."""
        with patch('openai.AsyncOpenAI') as mock_client:
            mock_client.return_value.chat.completions.create.side_effect = [
                Exception("Temporary error"),
                Exception("Temporary error"),
                Exception("Permanent error")
            ]
            
            result = await generator.generate_contract(
                "Create a simple ERC20 token",
                provider="openai"
            )
            
            assert result["status"] == "error"
            assert "permanent" in result["error"].lower()
    
    @pytest.mark.asyncio
    async def test_provider_response_validation(self, generator):
        """Test provider response validation."""
        with patch('openai.AsyncOpenAI') as mock_client:
            mock_response = AsyncMock()
            mock_response.choices = [AsyncMock()]
            mock_response.choices[0].message.content = "Invalid response"
            
            mock_client.return_value.chat.completions.create.return_value = mock_response
            
            result = await generator.generate_contract(
                "Create a simple ERC20 token",
                provider="openai"
            )
            
            assert result["status"] == "error"
            assert "invalid" in result["error"].lower()
    
    @pytest.mark.asyncio
    async def test_provider_empty_response(self, generator):
        """Test provider empty response handling."""
        with patch('openai.AsyncOpenAI') as mock_client:
            mock_response = AsyncMock()
            mock_response.choices = [AsyncMock()]
            mock_response.choices[0].message.content = ""
            
            mock_client.return_value.chat.completions.create.return_value = mock_response
            
            result = await generator.generate_contract(
                "Create a simple ERC20 token",
                provider="openai"
            )
            
            assert result["status"] == "error"
            assert "empty" in result["error"].lower()
    
    @pytest.mark.asyncio
    async def test_provider_malformed_response(self, generator):
        """Test provider malformed response handling."""
        with patch('openai.AsyncOpenAI') as mock_client:
            mock_response = AsyncMock()
            mock_response.choices = [AsyncMock()]
            mock_response.choices[0].message.content = None
            
            mock_client.return_value.chat.completions.create.return_value = mock_response
            
            result = await generator.generate_contract(
                "Create a simple ERC20 token",
                provider="openai"
            )
            
            assert result["status"] == "error"
            assert "malformed" in result["error"].lower()
    
    @pytest.mark.asyncio
    async def test_provider_concurrent_requests(self, generator):
        """Test provider concurrent request handling."""
        if not os.getenv('OPENAI_API_KEY'):
            pytest.skip("OpenAI API key not configured")
        
        with patch('openai.AsyncOpenAI') as mock_client:
            mock_response = AsyncMock()
            mock_response.choices = [AsyncMock()]
            mock_response.choices[0].message.content = "pragma solidity ^0.8.0;\n\ncontract TestContract {\n    string public name = \"Test\";\n}"
            
            mock_client.return_value.chat.completions.create.return_value = mock_response
            
            # Create multiple concurrent requests
            tasks = [
                generator.generate_contract("Create a simple ERC20 token", provider="openai")
                for _ in range(5)
            ]
            
            results = await asyncio.gather(*tasks)
            
            for result in results:
                assert result["status"] == "success"
                assert "contract_code" in result
    
    @pytest.mark.asyncio
    async def test_provider_memory_usage(self, generator):
        """Test provider memory usage."""
        if not os.getenv('OPENAI_API_KEY'):
            pytest.skip("OpenAI API key not configured")
        
        with patch('openai.AsyncOpenAI') as mock_client:
            mock_response = AsyncMock()
            mock_response.choices = [AsyncMock()]
            mock_response.choices[0].message.content = "pragma solidity ^0.8.0;\n\ncontract TestContract {\n    string public name = \"Test\";\n}"
            
            mock_client.return_value.chat.completions.create.return_value = mock_response
            
            # Generate multiple contracts to test memory usage
            for i in range(10):
                result = await generator.generate_contract(
                    f"Create contract {i}",
                    provider="openai"
                )
                assert result["status"] == "success"
    
    @pytest.mark.asyncio
    async def test_provider_performance(self, generator):
        """Test provider performance."""
        if not os.getenv('OPENAI_API_KEY'):
            pytest.skip("OpenAI API key not configured")
        
        with patch('openai.AsyncOpenAI') as mock_client:
            mock_response = AsyncMock()
            mock_response.choices = [AsyncMock()]
            mock_response.choices[0].message.content = "pragma solidity ^0.8.0;\n\ncontract TestContract {\n    string public name = \"Test\";\n}"
            
            mock_client.return_value.chat.completions.create.return_value = mock_response
            
            import time
            start_time = time.time()
            
            result = await generator.generate_contract(
                "Create a simple ERC20 token",
                provider="openai"
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            assert result["status"] == "success"
            assert duration < 30  # Should complete within 30 seconds
    
    @pytest.mark.asyncio
    async def test_provider_cost_tracking(self, generator):
        """Test provider cost tracking."""
        if not os.getenv('OPENAI_API_KEY'):
            pytest.skip("OpenAI API key not configured")
        
        with patch('openai.AsyncOpenAI') as mock_client:
            mock_response = AsyncMock()
            mock_response.choices = [AsyncMock()]
            mock_response.choices[0].message.content = "pragma solidity ^0.8.0;\n\ncontract TestContract {\n    string public name = \"Test\";\n}"
            mock_response.usage = {"total_tokens": 100, "prompt_tokens": 50, "completion_tokens": 50}
            
            mock_client.return_value.chat.completions.create.return_value = mock_response
            
            result = await generator.generate_contract(
                "Create a simple ERC20 token",
                provider="openai"
            )
            
            assert result["status"] == "success"
            assert "usage" in result
            assert result["usage"]["total_tokens"] == 100
