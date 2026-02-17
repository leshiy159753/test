"""
Shared configuration module for AgentCoin mining tools.

Handles environment variables, Web3 connection, and contract setup.
"""

import os
import sys
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

from dotenv import load_dotenv
from eth_account import Account
from web3 import Web3
from web3.contract import Contract


# Load environment variables from .env file
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)


# Contract addresses - Base chain defaults
DEFAULT_RPC_URL = "https://mainnet.base.org"
DEFAULT_PROBLEM_MANAGER = "0x1234567890123456789012345678901234567890"
DEFAULT_AGENT_REGISTRY = "0x0987654321098765432109876543210987654321"
DEFAULT_REWARD_DISTRIBUTOR = "0xabcdefabcdefabcdefabcdefabcdefabcdefabcd"


@dataclass
class Config:
    """Configuration class for AgentCoin mining."""
    
    private_key: str
    rpc_url: str
    problem_manager_address: str
    agent_registry_address: str
    reward_distributor_address: str
    
    # Web3 and contract instances (initialized after validation)
    w3: Optional[Web3] = None
    account: Optional[Account] = None
    problem_manager: Optional[Contract] = None
    agent_registry: Optional[Contract] = None
    reward_distributor: Optional[Contract] = None
    
    def __post_init__(self):
        """Initialize Web3 connection and contracts after validation."""
        self._init_web3()
        self._load_contracts()
    
    def _init_web3(self) -> None:
        """Initialize Web3 connection."""
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        
        if not self.w3.is_connected():
            raise ConnectionError(
                f"Failed to connect to Base chain at {self.rpc_url}. "
                "Please check your RPC URL and network connection."
            )
        
        # Initialize account from private key
        self.account = Account.from_key(self.private_key)
    
    def _load_contracts(self) -> None:
        """Load contract ABIs and create contract instances."""
        abis_dir = Path(__file__).parent / "abis"
        
        # Load ProblemManager contract
        pm_abi_path = abis_dir / "problem_manager.json"
        with open(pm_abi_path) as f:
            import json
            pm_abi = json.load(f)
        
        self.problem_manager = self.w3.eth.contract(
            address=Web3.to_checksum_address(self.problem_manager_address),
            abi=pm_abi
        )
        
        # Load AgentRegistry contract
        ar_abi_path = abis_dir / "agent_registry.json"
        with open(ar_abi_path) as f:
            ar_abi = json.load(f)
        
        self.agent_registry = self.w3.eth.contract(
            address=Web3.to_checksum_address(self.agent_registry_address),
            abi=ar_abi
        )
        
        # Load RewardDistributor contract
        rd_abi_path = abis_dir / "reward_distributor.json"
        with open(rd_abi_path) as f:
            rd_abi = json.load(f)
        
        self.reward_distributor = self.w3.eth.contract(
            address=Web3.to_checksum_address(self.reward_distributor_address),
            abi=rd_abi
        )
    
    @property
    def address(self) -> str:
        """Get the agent's wallet address."""
        if not self.account:
            raise RuntimeError("Account not initialized")
        return self.account.address
    
    def get_agent_id(self) -> Optional[int]:
        """Get the agent ID from the registry."""
        try:
            agent_id = self.agent_registry.functions.agentIdByAddress(
                self.address
            ).call()
            return agent_id if agent_id > 0 else None
        except Exception:
            return None
    
    def get_eth_balance(self) -> float:
        """Get wallet ETH balance (for gas)."""
        if not self.w3:
            raise RuntimeError("Web3 not initialized")
        balance_wei = self.w3.eth.get_balance(self.address)
        return self.w3.from_wei(balance_wei, 'ether')


def load_config(
    private_key: Optional[str] = None,
    rpc_url: Optional[str] = None,
    problem_manager: Optional[str] = None,
    agent_registry: Optional[str] = None,
    reward_distributor: Optional[str] = None
) -> Config:
    """
    Load configuration from environment variables and/or CLI arguments.
    
    CLI arguments take precedence over environment variables.
    
    Args:
        private_key: Private key for signing transactions (overrides env var)
        rpc_url: RPC URL for Base chain connection (overrides env var)
        problem_manager: ProblemManager contract address (overrides env var)
        agent_registry: AgentRegistry contract address (overrides env var)
        reward_distributor: RewardDistributor contract address (overrides env var)
    
    Returns:
        Config: Initialized configuration object
    
    Raises:
        ValueError: If required configuration is missing
        ConnectionError: If unable to connect to the blockchain
    """
    # Get private key (required)
    key = private_key or os.getenv("AGC_PRIVATE_KEY")
    if not key:
        raise ValueError(
            "Private key is required. Set AGC_PRIVATE_KEY environment variable "
            "or pass --private-key argument."
        )
    
    # Clean up private key (remove 0x prefix if present)
    key = key.strip()
    if key.startswith("0x"):
        key = key[2:]
    
    # Validate private key format
    if len(key) != 64:
        raise ValueError(
            f"Invalid private key length: {len(key)} characters. "
            "Expected 64 hex characters (32 bytes)."
        )
    
    # Get other configuration values
    rpc = rpc_url or os.getenv("AGC_RPC_URL", DEFAULT_RPC_URL)
    pm = problem_manager or os.getenv(
        "PROBLEM_MANAGER_ADDRESS", DEFAULT_PROBLEM_MANAGER
    )
    ar = agent_registry or os.getenv(
        "AGENT_REGISTRY_ADDRESS", DEFAULT_AGENT_REGISTRY
    )
    rd = reward_distributor or os.getenv(
        "REWARD_DISTRIBUTOR_ADDRESS", DEFAULT_REWARD_DISTRIBUTOR
    )
    
    return Config(
        private_key=key,
        rpc_url=rpc,
        problem_manager_address=pm,
        agent_registry_address=ar,
        reward_distributor_address=rd
    )


def validate_config(config: Config) -> bool:
    """
    Validate that the configuration is working properly.
    
    Args:
        config: Configuration object to validate
    
    Returns:
        bool: True if configuration is valid
    """
    try:
        # Check Web3 connection
        if not config.w3 or not config.w3.is_connected():
            print("❌ Web3 connection failed")
            return False
        print(f"✓ Connected to {config.rpc_url}")
        
        # Check account
        if not config.account:
            print("❌ Account not initialized")
            return False
        print(f"✓ Account loaded: {config.address}")
        
        # Check ETH balance
        eth_balance = config.get_eth_balance()
        print(f"✓ ETH Balance: {eth_balance:.6f} ETH")
        if eth_balance < 0.001:
            print("⚠️  Warning: Low ETH balance for gas fees")
        
        # Check agent registration
        agent_id = config.get_agent_id()
        if agent_id:
            print(f"✓ Agent registered with ID: {agent_id}")
        else:
            print("⚠️  Agent not registered in registry")
        
        # Check contract connections
        try:
            # Try to call a view function on each contract
            config.problem_manager.functions.getCurrentProblem().call()
            print("✓ ProblemManager contract accessible")
        except Exception as e:
            print(f"⚠️  ProblemManager contract issue: {e}")
        
        try:
            config.reward_distributor.functions.getPendingRewards(
                config.address
            ).call()
            print("✓ RewardDistributor contract accessible")
        except Exception as e:
            print(f"⚠️  RewardDistributor contract issue: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration validation failed: {e}")
        return False


if __name__ == "__main__":
    # Test configuration loading
    try:
        config = load_config()
        validate_config(config)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
