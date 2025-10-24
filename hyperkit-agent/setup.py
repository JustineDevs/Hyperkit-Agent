#!/usr/bin/env python3
"""
Setup script for HyperKit AI Agent
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

# Read requirements
requirements = []
with open("requirements.txt", "r") as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="hyperkit-agent",
    version="2.0.1",
    author="HyperKit Team",
    author_email="team@hyperkit.ai",
    description="🚀 HyperKit AI Agent - Generate, audit, and deploy smart contracts with AI",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/hyperkit-ai/hyperkit-agent",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
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
    entry_points={
        "console_scripts": [
            "hyperagent=main:cli_main",
        ],
    },
    py_modules=["main"],
    include_package_data=True,
    package_data={
        "": ["*.yaml", "*.yml", "*.json", "*.md", "*.txt"],
    },
    keywords=[
        "ai", "artificial-intelligence", "blockchain", "ethereum", "smart-contracts",
        "defi", "web3", "solidity", "audit", "deployment", "hyperion", "metis", "lazai"
    ],
    project_urls={
        "Bug Reports": "https://github.com/hyperkit-ai/hyperkit-agent/issues",
        "Source": "https://github.com/hyperkit-ai/hyperkit-agent",
        "Documentation": "https://docs.hyperkit.ai",
    },
)