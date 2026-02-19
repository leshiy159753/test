#!/usr/bin/env python3
"""
BLOKS Agent Mint API Client

Minimal script to interact with BLOKS Agent Mint API:
1. Get challenge (PoW challenge)
2. Solve PoW (SHA-256 with prefix matching)
3. Verify solution
4. Mint agent

Optional whitelist signing with ed25519 (requires solders package).
"""

import argparse
import base64
import hashlib
import json
import sys
import time
from typing import Optional

import requests

# Optional: solders for whitelist signing
try:
    from solders.keypair import Keypair
    from solders.message import Message
    SOLDERS_AVAILABLE = True
except ImportError:
    SOLDERS_AVAILABLE = False


def solve_pow(prefix: str, target: str, progress_interval: int = 100000) -> Optional[str]:
    """
    Solve PoW by finding a nonce such that SHA256(prefix + nonce) starts with target.
    
    Args:
        prefix: The prefix from the challenge
        target: The target prefix for the hash
        progress_interval: Print progress every N iterations
        
    Returns:
        Nonce string that satisfies the PoW, or None if cancelled
    """
    nonce = 0
    target_bytes = target.encode() if isinstance(target, str) else target
    prefix_bytes = prefix.encode() if isinstance(prefix, str) else prefix
    
    print(f"Starting PoW: prefix={prefix}, target={target}")
    print(f"Searching for nonce... (Ctrl+C to stop)")
    
    start_time = time.time()
    
    while True:
        nonce_str = str(nonce)
        data = prefix_bytes + nonce_str.encode()
        hash_result = hashlib.sha256(data).hexdigest()
        
        if hash_result.startswith(target_bytes if isinstance(target_bytes, str) else target_bytes.decode()):
            elapsed = time.time() - start_time
            print(f"\n✓ PoW solved! nonce={nonce_str}, hash={hash_result[:16]}...")
            print(f"  Time: {elapsed:.2f}s, iterations: {nonce}")
            return nonce_str
        
        nonce += 1
        
        if nonce % progress_interval == 0:
            elapsed = time.time() - start_time
            rate = nonce / elapsed if elapsed > 0 else 0
            print(f"  Progress: {nonce:,} iterations, {rate:,.0f} ops/sec", end="\r")


def get_challenge(wallet: str, base_url: str) -> dict:
    """Get PoW challenge from BLOKS API."""
    print(f"\n[1/4] Getting challenge for wallet: {wallet}")
    
    url = f"{base_url}/api/challenge"
    params = {"wallet": wallet}
    
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    
    data = response.json()
    print(f"  Challenge received: id={data.get('id')}, target={data.get('target')}")
    print(f"  Expires at: {data.get('expiresAt')}")
    
    return data


def verify_solution(challenge: dict, nonce: str, base_url: str) -> dict:
    """Submit PoW solution for verification."""
    print(f"\n[2/4] Verifying solution...")
    
    url = f"{base_url}/api/verify"
    payload = {
        "id": challenge["id"],
        "prefix": challenge["prefix"],
        "target": challenge["target"],
        "nonce": nonce,
        "signature": challenge.get("signature"),
        "metadata": challenge.get("metadata"),
    }
    
    response = requests.post(url, json=payload, timeout=30)
    response.raise_for_status()
    
    data = response.json()
    print(f"  Verified! Token: {data.get('token', 'N/A')[:20]}...")
    
    return data


def mint_agent(
    wallet: str,
    token: str,
    base_url: str,
    signed_message: Optional[str] = None,
    wallet_signature: Optional[str] = None,
) -> dict:
    """Mint the agent with the verified token."""
    print(f"\n[4/4] Minting agent...")
    
    url = f"{base_url}/api/mint"
    payload = {
        "mode": "agent",
        "wallet": wallet,
        "token": token,
    }
    
    if signed_message and wallet_signature:
        payload["signedMessage"] = signed_message
        payload["walletSignature"] = wallet_signature
        print("  Including whitelist signature")
    
    response = requests.post(url, json=payload, timeout=60)
    response.raise_for_status()
    
    data = response.json()
    print(f"  Mint response: {json.dumps(data, indent=2)}")
    
    return data


def create_whitelist_signature(wallet: str, private_key: str) -> tuple:
    """
    Create whitelist signature for minting.
    
    Returns:
        Tuple of (signedMessage, walletSignature)
    """
    if not SOLDERS_AVAILABLE:
        print("  ⚠ WARNING: solders package not installed. Whitelist signing disabled.")
        print("  To enable, install: pip install solders")
        return None, None
    
    ts = int(time.time() * 1000)
    signed_message = f"BLOKS:wl-mint:{wallet}:{ts}"
    
    try:
        keypair = Keypair.from_base58_string(private_key)
        message = Message(signed_message.encode())
        signature = keypair.sign_message(message)
        
        wallet_signature = base64.b64encode(signature.to_bytes()).decode()
        
        print(f"  ✓ Whitelist signature created (timestamp: {ts})")
        return signed_message, wallet_signature
    except Exception as e:
        print(f"  ⚠ WARNING: Failed to create signature: {e}")
        return None, None


def main():
    parser = argparse.ArgumentParser(
        description="BLOKS Agent Mint API - Challenge → PoW → Verify → Mint",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic mint (no whitelist)
  python mint.py --wallet YOUR_WALLET_ADDRESS

  # Mint with whitelist signing
  python mint.py --wallet YOUR_WALLET --private-key YOUR_PRIVATE_KEY

  # Custom API endpoint
  python mint.py --wallet YOUR_WALLET --base-url https://testnet.bloks.art
        """,
    )
    
    parser.add_argument(
        "--wallet",
        required=True,
        help="Solana wallet address (base58)",
    )
    
    parser.add_argument(
        "--base-url",
        default="https://bloks.art",
        help="BLOKS API base URL (default: https://bloks.art)",
    )
    
    parser.add_argument(
        "--private-key",
        help="Private key for whitelist signing (base58). Requires 'solders' package.",
    )
    
    parser.add_argument(
        "--progress-interval",
        type=int,
        default=100000,
        help="Print progress every N iterations (default: 100000)",
    )
    
    args = parser.parse_args()
    
    print("=" * 50)
    print("BLOKS Agent Mint API Client")
    print("=" * 50)
    print(f"Wallet: {args.wallet}")
    print(f"Base URL: {args.base_url}")
    print(f"Whitelist signing: {'Yes' if args.private_key else 'No'}")
    
    if args.private_key and not SOLDERS_AVAILABLE:
        print("\n⚠ WARNING: --private-key specified but 'solders' is not installed.")
        print("  Install with: pip install solders")
        print("  Continuing without whitelist signature...\n")
    
    try:
        # Step 1: Get challenge
        challenge = get_challenge(args.wallet, args.base_url)
        
        # Step 2: Solve PoW
        nonce = solve_pow(
            challenge["prefix"],
            challenge["target"],
            progress_interval=args.progress_interval,
        )
        
        if nonce is None:
            print("ERROR: PoW not solved")
            sys.exit(1)
        
        # Step 3: Verify solution
        verify_result = verify_solution(challenge, nonce, args.base_url)
        token = verify_result.get("token")
        
        if not token:
            print("ERROR: No token in verify response")
            sys.exit(1)
        
        # Prepare whitelist signature if available
        signed_message = None
        wallet_signature = None
        
        if args.private_key:
            signed_message, wallet_signature = create_whitelist_signature(
                args.wallet,
                args.private_key,
            )
        
        # Step 4: Mint
        result = mint_agent(
            args.wallet,
            token,
            args.base_url,
            signed_message,
            wallet_signature,
        )
        
        print("\n" + "=" * 50)
        print("✓ Mint completed successfully!")
        print("=" * 50)
        
    except requests.exceptions.HTTPError as e:
        print(f"\n❌ HTTP Error: {e}")
        try:
            error_data = e.response.json()
            print(f"   Response: {json.dumps(error_data, indent=2)}")
        except:
            print(f"   Response: {e.response.text}")
        sys.exit(1)
        
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Request Error: {e}")
        sys.exit(1)
        
    except KeyboardInterrupt:
        print("\n\n⚠ Interrupted by user")
        sys.exit(130)


if __name__ == "__main__":
    main()
