"""
AgentCoin Mining Skill

Python tools for mining AGC tokens on Base chain.
Includes CLI tools, auto-mining daemon, and BLOKS Agent Mint client.
"""

__version__ = "1.1.0"
__author__ = "AgentCoin"

# Public re-exports for programmatic use
from bloks_config import BloksConfig, load_bloks_config  # noqa: F401
from bloks_client import BloksMintClient, MintResult     # noqa: F401
