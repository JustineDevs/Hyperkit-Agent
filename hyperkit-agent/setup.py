"""
HyperKit AI Agent - Setup Configuration
Includes MCP Docker and Obsidian integration setup
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from setuptools import setup, find_packages, Command

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [
        line.strip() for line in fh if line.strip() and not line.startswith("#")
    ]


class SetupMCPIntegration(Command):
    """Command to set up MCP Docker integration."""
    description = "Set up MCP Docker integration for Obsidian"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        """Run MCP integration setup."""
        print("🚀 Setting up MCP Integration for HyperKit Agent...")
        print("=" * 60)

        # Check Docker
        if not self.check_docker_installed():
            print("\n❌ Docker is required for MCP integration.")
            print("Please install Docker Desktop and try again.")
            return

        # Build and start MCP Docker container
        try:
            import subprocess
            import sys
            
            result = subprocess.run([sys.executable, "setup_mcp_docker.py"], 
                                  capture_output=True, text=True)
            
            print(result.stdout)
            if result.stderr:
                print("Errors:")
                print(result.stderr)
            
            if result.returncode == 0:
                print("\n✅ MCP Docker setup completed successfully!")
            else:
                print("\n❌ MCP Docker setup failed. Check the output above.")
                
        except Exception as e:
            print(f"❌ Error running MCP Docker setup: {e}")
            print("Please run 'python setup_mcp_docker.py' manually.")

    def check_docker_installed(self):
        """Check if Docker is installed and running."""
        print("🐳 Checking Docker installation...")
        try:
            result = subprocess.run(["docker", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"  ✅ Docker installed: {result.stdout.strip()}")
            else:
                print("  ❌ Docker not found")
                return False
        except FileNotFoundError:
            print("  ❌ Docker not found")
            return False

        try:
            result = subprocess.run(["docker", "info"], capture_output=True, text=True)
            if result.returncode == 0:
                print("  ✅ Docker daemon is running")
                return True
            else:
                print("  ❌ Docker daemon is not running")
                return False
        except Exception as e:
            print(f"  ❌ Docker daemon check failed: {e}")
            return False

    def pull_mcp_obsidian_image(self):
        """Pull the MCP Obsidian Docker image."""
        print("📦 Pulling MCP Obsidian Docker image...")
        try:
            result = subprocess.run(
                ["docker", "pull", "mcp/obsidian"], capture_output=True, text=True
            )
            if result.returncode == 0:
                print("  ✅ MCP Obsidian image pulled successfully")
                return True
            else:
                print(f"  ❌ Failed to pull image: {result.stderr}")
                return False
        except Exception as e:
            print(f"  ❌ Error pulling image: {e}")
            return False

    def create_mcp_config(self):
        """Create MCP configuration file."""
        print("⚙️  Creating MCP configuration...")
        config = {
            "mcpServers": {
                "obsidian": {
                    "command": "docker",
                    "args": [
                        "run",
                        "-i",
                        "--rm",
                        "-e",
                        "OBSIDIAN_HOST",
                        "-e",
                        "OBSIDIAN_API_KEY",
                        "mcp/obsidian",
                    ],
                    "env": {
                        "OBSIDIAN_HOST": "host.docker.internal",
                        "OBSIDIAN_API_KEY": "YOUR_OBSIDIAN_API_KEY",
                    },
                }
            }
        }
        config_file = Path("mcp_config.json")
        with open(config_file, "w") as f:
            json.dump(config, f, indent=2)
        print(f"  ✅ Created: {config_file}")

    def create_env_update(self):
        """Create environment variable update instructions."""
        print("📝 Environment configuration...")
        env_content = """
# Add these to your .env file for MCP integration:

# MCP Configuration
MCP_ENABLED=true
MCP_CONFIG_PATH=mcp_config.json
OBSIDIAN_MCP_API_KEY=your_obsidian_api_key_here

# Docker Configuration
DOCKER_ENABLED=true
OBSIDIAN_HOST=host.docker.internal
"""
        env_file = Path("mcp_env_additions.txt")
        with open(env_file, "w") as f:
            env_file.write_text(env_content)
        print(f"  ✅ Created: {env_file}")

    def print_mcp_instructions(self):
        """Print MCP setup instructions."""
        print("\n" + "=" * 60)
        print("🎉 MCP INTEGRATION SETUP COMPLETE!")
        print("=" * 60)
        print("\n📋 Next Steps:")
        print("\n1. Update MCP Configuration:")
        print("   - Edit mcp_config.json")
        print("   - Replace 'YOUR_OBSIDIAN_API_KEY' with your actual API key")
        print("\n2. Update Environment Variables:")
        print("   - Add the contents of mcp_env_additions.txt to your .env file")
        print("   - Set your actual Obsidian API key")
        print("\n3. Test the Integration:")
        print("   - Run: python cli.py generate 'Create an ERC20 token' --use-rag")
        print("\n✨ Your HyperKit Agent now supports MCP integration!")


class SetupObsidianIntegration(Command):
    """Command to set up Obsidian vault integration."""
    description = "Set up Obsidian vault integration"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass


class TestAPIKeys(Command):
    """Command to test all API keys."""
    description = "Test all API keys for validity and connectivity"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        """Run API key validation."""
        print("🔐 Testing API Keys for HyperKit AI Agent...")
        print("=" * 60)
        
        try:
            # Import and run the test script
            import subprocess
            import sys
            
            result = subprocess.run([sys.executable, "test_api_keys.py"], 
                                  capture_output=True, text=True)
            
            print(result.stdout)
            if result.stderr:
                print("Errors:")
                print(result.stderr)
            
            if result.returncode == 0:
                print("\n✅ API key validation completed successfully!")
            else:
                print("\n❌ Some API keys failed validation. Check the output above.")
                
        except Exception as e:
            print(f"❌ Error running API key tests: {e}")
            print("Please run 'python test_api_keys.py' manually.")


class SetupObsidianIntegration(Command):
    """Command to set up Obsidian vault integration."""
    description = "Set up Obsidian vault integration"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        """Run Obsidian integration setup."""
        print("🚀 Setting up Obsidian Integration for HyperKit Agent...")
        print("=" * 60)

        # Create vault structure
        vault_path = self.create_vault_structure()
        self.create_initial_files(vault_path)
        self.create_env_file(vault_path)
        self.create_git_repo(vault_path)
        self.print_obsidian_instructions(vault_path)

    def create_vault_structure(self):
        """Create the Obsidian vault folder structure."""
        print("📁 Creating Obsidian vault structure...")
        vault_path = Path.home() / "Downloads" / "Hyperkit"
        folders = ["Contracts", "Audits", "Templates", "Prompts"]

        vault_path.mkdir(parents=True, exist_ok=True)
        for folder in folders:
            folder_path = vault_path / folder
            folder_path.mkdir(exist_ok=True)
            print(f"  ✅ Created folder: {folder_path}")

        obsidian_dir = vault_path / ".obsidian"
        obsidian_dir.mkdir(exist_ok=True)
        config = {
            "appearance": {"theme": "moonstone"},
            "corePlugins": {"fileExplorer": True, "search": True, "graph": True},
        }
        config_file = obsidian_dir / "app.json"
        with open(config_file, "w") as f:
            json.dump(config, f, indent=2)
        print(f"  ✅ Created Obsidian configuration: {config_file}")
        return vault_path

    def create_initial_files(self, vault_path):
        """Create initial knowledge base files."""
        print("📝 Creating initial knowledge base files...")
        
        # Contract templates
        contract_files = {
            "ERC20-Template.md": """# ERC20 Token Template

## Basic Implementation
```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract BasicToken is ERC20, Ownable {
    constructor(string memory name, string memory symbol, uint256 initialSupply) 
        ERC20(name, symbol) 
        Ownable(msg.sender) 
    {
        _mint(msg.sender, initialSupply);
    }
}
```

## Security Best Practices
- Use OpenZeppelin implementations
- Implement proper access controls
- Add reentrancy guards
- Validate all inputs
""",
            "ERC721-Template.md": """# ERC721 NFT Template

## Basic Implementation
```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract BasicNFT is ERC721, Ownable {
    constructor() ERC721("BasicNFT", "BNFT") {}
    
    function mint(address to, uint256 tokenId) public onlyOwner {
        _safeMint(to, tokenId);
    }
}
```

## Advanced Features
- Enumerable NFTs
- Metadata extensions
- Pausable functionality
- Royalty system
""",
        }

        contracts_dir = vault_path / "Contracts"
        for filename, content in contract_files.items():
            file_path = contracts_dir / filename
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"  ✅ Created: {file_path}")

        # Audit checklists
        audit_files = {
            "Security-Checklist.md": """# Security Audit Checklist

## Pre-Audit
- [ ] Code review completed
- [ ] Unit tests written
- [ ] Integration tests completed
- [ ] Dependencies audited

## Common Vulnerabilities
- [ ] Reentrancy protection
- [ ] Access control validation
- [ ] Integer overflow/underflow
- [ ] Front-running protection
- [ ] Oracle manipulation

## DeFi Specific
- [ ] Flash loan attacks
- [ ] Price manipulation
- [ ] Liquidity attacks
- [ ] MEV protection
""",
        }

        audits_dir = vault_path / "Audits"
        for filename, content in audit_files.items():
            file_path = audits_dir / filename
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"  ✅ Created: {file_path}")

    def create_env_file(self, vault_path):
        """Create or update .env file with Obsidian configuration."""
        print("⚙️  Creating environment configuration...")
        env_file = Path(".env")
        env_content = f"""# HyperKit AI Agent Configuration

# AI Provider API Keys (Cloud-Based)
GOOGLE_API_KEY=your_google_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# MCP Configuration
MCP_ENABLED=true
MCP_CONFIG_PATH=mcp_config.json
OBSIDIAN_MCP_API_KEY=your_obsidian_api_key_here

# Docker Configuration
DOCKER_ENABLED=true
OBSIDIAN_HOST=host.docker.internal

# Blockchain Configuration (Hyperion Focus)
DEFAULT_NETWORK=hyperion
HYPERION_RPC_URL=https://hyperion-testnet.metisdevops.link
HYPERION_CHAIN_ID=133717
HYPERION_EXPLORER_URL=https://hyperion-testnet-explorer.metisdevops.link

# Wallet Configuration
DEFAULT_PRIVATE_KEY=your_wallet_private_key_here

# Security Tools
SLITHER_ENABLED=true
MYTHRIL_ENABLED=true
EDB_ENABLED=true

# Logging
LOG_LEVEL=INFO
"""
        with open(env_file, "w") as f:
            f.write(env_content)
        print(f"  ✅ Created: {env_file}")

    def create_git_repo(self, vault_path):
        """Initialize Git repository for the vault."""
        print("📦 Initializing Git repository...")
        try:
            subprocess.run(["git", "init"], cwd=vault_path, check=True)
            gitignore_content = """# Obsidian
.obsidian/workspace.json
.obsidian/workspace-mobile.json
.obsidian/hotkeys.json
.obsidian/appearance.json
.obsidian/core-plugins.json
.obsidian/community-plugins.json
.obsidian/plugins/
.obsidian/themes/
.obsidian/snippets/

# OS
.DS_Store
Thumbs.db

# Temporary files
*.tmp
*.temp
"""
            gitignore_file = vault_path / ".gitignore"
            with open(gitignore_file, "w") as f:
                f.write(gitignore_content)
            subprocess.run(["git", "add", "."], cwd=vault_path, check=True)
            subprocess.run(
                ["git", "commit", "-m", "Initial HyperKit vault setup"],
                cwd=vault_path,
                check=True,
            )
            print("  ✅ Git repository initialized")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("  ❌ Git initialization failed (optional)")

    def print_obsidian_instructions(self, vault_path):
        """Print Obsidian setup instructions."""
        print("\n" + "=" * 60)
        print("🎉 OBSIDIAN VAULT SETUP COMPLETE!")
        print("=" * 60)
        print("\n📋 Next Steps:")
        print(f"\n1. Open Obsidian:")
        print(f"   - Launch Obsidian")
        print(f"   - Click 'Open folder as vault'")
        print(f"   - Select: {vault_path}")
        print(f"   - Name it 'HyperKit'")
        print("\n2. Update Environment Variables:")
        print("   - Edit the .env file in your project")
        print("   - Add your API keys")
        print("\n3. Test the Integration:")
        print("   - Run: python cli.py generate 'Create an ERC20 token' --use-rag")
        print("\n✨ Your HyperKit Agent is now integrated with Obsidian!")


setup(
    name="hyperkit-agent",
    version="1.2.3",
    author="HyperKit Team",
    author_email="team@hyperionkit.xyz",
    description="HyperKit AI Agent - Smart Contract Generation, Auditing, and Deployment",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/JustineDevs/Hyperkit-Agent",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "isort>=5.12.0",
            "mypy>=1.0.0",
            "pre-commit>=3.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "hyperkit-agent=main:main",
        ],
    },
    cmdclass={
        "setup-mcp": SetupMCPIntegration,
        "setup-obsidian": SetupObsidianIntegration,
        "test-apis": TestAPIKeys,
    },
    include_package_data=True,
    package_data={
        "": ["*.md", "*.txt", "*.yml", "*.yaml"],
    },
)
