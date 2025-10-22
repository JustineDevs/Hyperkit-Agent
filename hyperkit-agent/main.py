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
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("hyperkit-agent.log"), logging.StreamHandler()],
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

            print("\n" + "=" * 50)
            print("HYPERKIT AI AGENT RESULT")
            print("=" * 50)
            print(json.dumps(result, indent=2))
            print("=" * 50)
        else:
            # Interactive mode
            print("HyperKit AI Agent - Interactive Mode")
            print("Type 'quit' to exit")
            print("-" * 40)

            while True:
                try:
                    prompt = input("\nEnter your smart contract request: ").strip()

                    if prompt.lower() in ["quit", "exit", "q"]:
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
    """Load configuration using the new configuration system."""
    from core.config.loader import get_config
    
    config_loader = get_config()
    return config_loader.to_dict()


if __name__ == "__main__":
    asyncio.run(main())
