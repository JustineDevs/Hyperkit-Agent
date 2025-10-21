"""
HyperKit AI Agent - Main Entry Point
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from core.agent.main import HyperKitAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('hyperkit-agent.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


async def main():
    """Main entry point for the HyperKit AI Agent."""
    try:
        logger.info("Starting HyperKit AI Agent...")
        
        # Load configuration
        config = load_config()
        
        # Initialize agent
        agent = HyperKitAgent(config)
        
        # Example usage
        if len(sys.argv) > 1:
            prompt = " ".join(sys.argv[1:])
            logger.info(f"Processing prompt: {prompt}")
            
            result = await agent.run_workflow(prompt)
            
            print("\n" + "="*50)
            print("HYPERKIT AI AGENT RESULT")
            print("="*50)
            print(json.dumps(result, indent=2))
            print("="*50)
        else:
            # Interactive mode
            print("HyperKit AI Agent - Interactive Mode")
            print("Type 'quit' to exit")
            print("-" * 40)
            
            while True:
                try:
                    prompt = input("\nEnter your smart contract request: ").strip()
                    
                    if prompt.lower() in ['quit', 'exit', 'q']:
                        break
                    
                    if not prompt:
                        continue
                    
                    print("\nProcessing...")
                    result = await agent.run_workflow(prompt)
                    
                    print("\nResult:")
                    print(json.dumps(result, indent=2))
                    
                except KeyboardInterrupt:
                    print("\nExiting...")
                    break
                except Exception as e:
                    logger.error(f"Error processing prompt: {e}")
                    print(f"Error: {e}")
        
        logger.info("HyperKit AI Agent finished")
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


def load_config():
    """Load configuration from environment variables."""
    import os
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    
    config = {
        'openai_api_key': os.getenv('OPENAI_API_KEY'),
        'anthropic_api_key': os.getenv('ANTHROPIC_API_KEY'),
        'google_api_key': os.getenv('GOOGLE_API_KEY'),
        'dashscope_api_key': os.getenv('DASHSCOPE_API_KEY'),
        'default_private_key': os.getenv('DEFAULT_PRIVATE_KEY'),
        'networks': {
            'hyperion': os.getenv('HYPERION_RPC_URL', 'https://hyperion-testnet.metisdevops.link'),
            'polygon': os.getenv('POLYGON_RPC_URL', 'https://polygon-rpc.com'),
            'arbitrum': os.getenv('ARBITRUM_RPC_URL', 'https://arb1.arbitrum.io/rpc'),
            'ethereum': os.getenv('ETHEREUM_RPC_URL', 'https://mainnet.infura.io/v3/YOUR_PROJECT_ID')
        },
        'vectorstore_path': os.getenv('VECTORSTORE_PATH', './data/vectordb'),
        'log_level': os.getenv('LOG_LEVEL', 'INFO')
    }
    
    return config


if __name__ == "__main__":
    asyncio.run(main())
