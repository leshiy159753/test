#!/usr/bin/env python3
"""
BLOKS Agent Mint CLI

Performs a full NFT mint via the BLOKS Agent Mint API:

    1. Checks the current mint phase (whitelist / public / closed).
    2. Requests and solves a Proof-of-Work challenge (SHA-256, leading zero bits).
    3. Verifies the solution and receives a mint token.
    4. Mints the NFT — including an EIP-191 wallet signature when in whitelist phase.

Usage:
    python bloks_mint.py [options]
    python bloks_mint.py --help

Examples:
    # Minimal — reads config from .env
    python bloks_mint.py

    # Override key and project via CLI
    python bloks_mint.py --private-key 0xABC... --project-id my-project

    # Dry-run: solve PoW but do NOT submit the mint
    python bloks_mint.py --dry-run

    # Custom WL message + verbose logging
    python bloks_mint.py --wl-message "BLOKS WL: 0xYourAddress" --verbose
"""

import argparse
import logging
import sys
from typing import Optional

from bloks_config import load_bloks_config
from bloks_client import BloksMintClient


# ---------------------------------------------------------------------------
# Logging setup  (same style as miner.py)
# ---------------------------------------------------------------------------

class _ColoredFormatter(logging.Formatter):
    _COLORS = {
        "DEBUG": "\033[36m",
        "INFO": "\033[32m",
        "WARNING": "\033[33m",
        "ERROR": "\033[31m",
        "CRITICAL": "\033[35m",
        "RESET": "\033[0m",
    }

    def format(self, record: logging.LogRecord) -> str:
        color = self._COLORS.get(record.levelname, self._COLORS["RESET"])
        reset = self._COLORS["RESET"]
        record.levelname = f"{color}{record.levelname}{reset}"
        return super().format(record)


def _setup_logging(verbose: bool) -> logging.Logger:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        _ColoredFormatter(
            "%(asctime)s | %(levelname)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    log = logging.getLogger("bloks-mint")
    log.setLevel(logging.DEBUG if verbose else logging.INFO)
    log.addHandler(handler)
    return log


# ---------------------------------------------------------------------------
# CLI parser
# ---------------------------------------------------------------------------

def _create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bloks_mint.py",
        description=(
            "BLOKS Agent Mint CLI — "
            "PoW challenge/verify/mint with optional whitelist signature."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--private-key",
        metavar="HEX",
        help=(
            "Wallet private key (64 hex chars, 0x prefix optional). "
            "Overrides AGC_PRIVATE_KEY env var."
        ),
    )
    parser.add_argument(
        "--api-base-url",
        metavar="URL",
        help=(
            "BLOKS API base URL. "
            "Overrides BLOKS_API_BASE_URL env var "
            "(default: https://api.bloks.io/agent-mint)."
        ),
    )
    parser.add_argument(
        "--project-id",
        metavar="ID",
        help="BLOKS project / collection ID. Overrides BLOKS_PROJECT_ID env var.",
    )
    parser.add_argument(
        "--chain-id",
        type=int,
        metavar="INT",
        help="EVM chain ID (default: 8453 Base). Overrides BLOKS_CHAIN_ID env var.",
    )
    parser.add_argument(
        "--wl-message",
        metavar="MSG",
        default=None,
        help=(
            "Custom whitelist message to sign (EIP-191). "
            "Defaults to 'BLOKS Whitelist Mint: <address>'."
        ),
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=3,
        metavar="N",
        help="HTTP retry limit per API call (default: 3).",
    )
    parser.add_argument(
        "--retry-delay",
        type=float,
        default=2.0,
        metavar="SEC",
        help="Base back-off delay in seconds between retries (default: 2.0).",
    )
    parser.add_argument(
        "--one-shot",
        action="store_true",
        help="Alias for the default behaviour (run once and exit). Kept for script parity.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Solve PoW and verify, but do NOT send the final mint request. "
            "Useful for testing config without spending gas / minting."
        ),
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable DEBUG-level logging.",
    )

    return parser


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    """
    CLI entry point.

    Returns:
        Exit code (0 = success, 1 = error, 130 = interrupted).
    """
    parser = _create_parser()
    args = parser.parse_args()

    log = _setup_logging(args.verbose)

    try:
        # --- Load config -------------------------------------------------
        config = load_bloks_config(
            private_key=args.private_key,
            api_base_url=args.api_base_url,
            project_id=args.project_id,
            chain_id=args.chain_id,
            max_retries=args.max_retries,
            retry_delay=args.retry_delay,
        )

        log.info("=" * 60)
        log.info("        BLOKS AGENT MINT")
        log.info("=" * 60)
        log.info("Wallet address : %s", config.wallet_address)
        log.info("Project ID     : %s", config.project_id)
        log.info("Chain ID       : %s", config.chain_id)
        log.info("API base URL   : %s", config.api_base_url)
        if args.dry_run:
            log.info("Mode           : DRY RUN (no mint transaction)")
        log.info("-" * 60)

        # --- Run mint flow -----------------------------------------------
        client = BloksMintClient(config)
        result = client.run_mint_flow(
            dry_run=args.dry_run,
            whitelist_message=args.wl_message,
        )

        if result is None:
            if args.dry_run:
                log.info("[DRY RUN] Flow completed — mint step skipped.")
            else:
                log.warning("Mint not performed (phase may be closed).")
            return 0

        log.info("=" * 60)
        log.info("        MINT COMPLETE")
        log.info("=" * 60)
        if result.tx_hash:
            log.info("Transaction : %s", result.tx_hash)
        if result.token_id is not None:
            log.info("Token ID    : %s", result.token_id)
        log.info("=" * 60)
        return 0

    except ValueError as exc:
        log.error("Configuration error: %s", exc)
        return 1
    except KeyboardInterrupt:
        log.info("Interrupted by user.")
        return 130
    except Exception as exc:  # pylint: disable=broad-except
        log.error("Unexpected error: %s", exc, exc_info=args.verbose)
        return 1


if __name__ == "__main__":
    sys.exit(main())
