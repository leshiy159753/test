"""
BLOKS Mint configuration module.

Reads BLOKS-specific environment variables and provides a typed dataclass
alongside the existing AgentCoin Config, reusing the same private key /
eth_account setup without duplicating Web3 connection logic.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from eth_account import Account

# Reuse the same .env file that the main config loads
_env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=_env_path, override=False)

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
DEFAULT_BLOKS_API_BASE_URL = "https://api.bloks.io/agent-mint"


@dataclass
class BloksConfig:
    """
    Configuration for the BLOKS Agent Mint flow.

    Attributes:
        private_key:     Raw hex private key (no 0x prefix) used for signing.
        wallet_address:  Derived checksummed wallet address.
        account:         eth_account Account object for EIP-191 signing.
        api_base_url:    Root URL of the BLOKS Agent Mint API.
        project_id:      BLOKS project / collection identifier.
        chain_id:        EVM chain ID where the NFT lives (default: 8453 Base).
        max_retries:     How many times to retry failed HTTP calls.
        retry_delay:     Base delay (seconds) between retries (exponential back-off).
    """

    private_key: str
    api_base_url: str
    project_id: str
    chain_id: int = 8453
    max_retries: int = 3
    retry_delay: float = 2.0

    # Derived / injected after construction
    account: Optional[Account] = field(default=None, repr=False)
    wallet_address: str = field(default="", repr=True)

    def __post_init__(self) -> None:
        """Derive account and wallet address from private key."""
        self.account = Account.from_key(self.private_key)
        self.wallet_address = self.account.address


def load_bloks_config(
    private_key: Optional[str] = None,
    api_base_url: Optional[str] = None,
    project_id: Optional[str] = None,
    chain_id: Optional[int] = None,
    max_retries: int = 3,
    retry_delay: float = 2.0,
) -> BloksConfig:
    """
    Build a :class:`BloksConfig` from environment variables and/or CLI overrides.

    CLI arguments take precedence over environment variables.

    Args:
        private_key:   Hex private key (overrides ``AGC_PRIVATE_KEY`` env var).
        api_base_url:  BLOKS API base URL (overrides ``BLOKS_API_BASE_URL``).
        project_id:    BLOKS project ID (overrides ``BLOKS_PROJECT_ID``).
        chain_id:      EVM chain ID (overrides ``BLOKS_CHAIN_ID``).
        max_retries:   Number of HTTP retries.
        retry_delay:   Base seconds between retries.

    Returns:
        BloksConfig: Fully initialised configuration object.

    Raises:
        ValueError: If required configuration values are missing or invalid.
    """
    # ---- private key (required) -------------------------------------------
    raw_key = private_key or os.getenv("AGC_PRIVATE_KEY", "")
    if not raw_key:
        raise ValueError(
            "Private key is required. Set AGC_PRIVATE_KEY in .env "
            "or pass --private-key."
        )

    raw_key = raw_key.strip()
    if raw_key.startswith("0x") or raw_key.startswith("0X"):
        raw_key = raw_key[2:]

    if len(raw_key) != 64:
        raise ValueError(
            f"Invalid private key length ({len(raw_key)} chars). "
            "Expected 64 hex characters (32 bytes)."
        )

    # ---- API base URL -------------------------------------------------------
    base_url = (
        api_base_url
        or os.getenv("BLOKS_API_BASE_URL", DEFAULT_BLOKS_API_BASE_URL)
    ).rstrip("/")

    # ---- project ID (required) ----------------------------------------------
    pid = project_id or os.getenv("BLOKS_PROJECT_ID", "")
    if not pid:
        raise ValueError(
            "BLOKS project ID is required. Set BLOKS_PROJECT_ID in .env "
            "or pass --project-id."
        )

    # ---- chain ID -----------------------------------------------------------
    if chain_id is None:
        env_chain = os.getenv("BLOKS_CHAIN_ID", "8453")
        try:
            chain_id = int(env_chain)
        except ValueError:
            raise ValueError(
                f"BLOKS_CHAIN_ID must be an integer, got: {env_chain!r}"
            )

    return BloksConfig(
        private_key=raw_key,
        api_base_url=base_url,
        project_id=pid,
        chain_id=chain_id,
        max_retries=max_retries,
        retry_delay=retry_delay,
    )
