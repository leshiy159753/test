#!/usr/bin/env python3
"""
AgentCoin Mining CLI Tool

Manual CLI for submitting answers, claiming rewards, and checking status.

Usage:
    python mine.py submit <problem_id> <answer> [--private-key KEY] [--rpc-url URL]
    python mine.py claim [--private-key KEY] [--rpc-url URL]
    python mine.py status [--private-key KEY] [--rpc-url URL]
    python mine.py --help
"""

import argparse
import sys
from decimal import Decimal
from typing import Optional

from web3.exceptions import ContractLogicError, TransactionNotFound

from config import load_config, validate_config, Config


def format_wei(wei_value: int) -> str:
    """Format wei value to human-readable AGC."""
    from web3 import Web3
    agc = Web3.from_wei(wei_value, 'ether')
    return f"{agc:.6f} AGC"


def submit_answer(
    config: Config,
    problem_id: int,
    answer: str,
    dry_run: bool = False
) -> bool:
    """
    Submit an answer for a problem.
    
    Args:
        config: Configuration object
        problem_id: ID of the problem to solve
        answer: The answer string to submit
        dry_run: If True, only simulate the transaction
    
    Returns:
        bool: True if submission was successful
    """
    try:
        print(f"📤 Submitting answer for problem #{problem_id}")
        print(f"   Answer: {answer}")
        
        # Build transaction
        tx = config.problem_manager.functions.submitAnswer(
            problem_id,
            answer
        ).build_transaction({
            'from': config.address,
            'nonce': config.w3.eth.get_transaction_count(config.address),
            'gas': 300000,
            'maxFeePerGas': config.w3.to_wei('0.1', 'gwei'),
            'maxPriorityFeePerGas': config.w3.to_wei('0.01', 'gwei'),
            'chainId': 8453,  # Base mainnet chain ID
        })
        
        if dry_run:
            print("   [DRY RUN] Transaction would be:")
            print(f"   To: {tx.get('to')}")
            print(f"   Data: {tx.get('data', 'N/A')[:100]}...")
            return True
        
        # Sign transaction
        signed_tx = config.w3.eth.account.sign_transaction(tx, config.private_key)
        
        # Send transaction
        print("   Sending transaction...")
        tx_hash = config.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        tx_hash_hex = tx_hash.hex()
        print(f"   Transaction hash: {tx_hash_hex}")
        
        # Wait for receipt
        print("   Waiting for confirmation...")
        receipt = config.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        
        if receipt['status'] == 1:
            print(f"✅ Transaction successful!")
            print(f"   Block: {receipt['blockNumber']}")
            print(f"   Gas used: {receipt['gasUsed']}")
            return True
        else:
            print(f"❌ Transaction failed (status: {receipt['status']})")
            return False
            
    except ContractLogicError as e:
        print(f"❌ Contract error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error submitting answer: {e}")
        return False


def claim_rewards(config: Config, dry_run: bool = False) -> bool:
    """
    Claim pending rewards from RewardDistributor.
    
    Args:
        config: Configuration object
        dry_run: If True, only simulate the transaction
    
    Returns:
        bool: True if claim was successful
    """
    try:
        # Check pending rewards first
        pending = config.reward_distributor.functions.getPendingRewards(
            config.address
        ).call()
        
        if pending == 0:
            print("ℹ️  No pending rewards to claim")
            return True
        
        print(f"💰 Claiming {format_wei(pending)}...")
        
        # Build transaction
        tx = config.reward_distributor.functions.claimRewards().build_transaction({
            'from': config.address,
            'nonce': config.w3.eth.get_transaction_count(config.address),
            'gas': 200000,
            'maxFeePerGas': config.w3.to_wei('0.1', 'gwei'),
            'maxPriorityFeePerGas': config.w3.to_wei('0.01', 'gwei'),
            'chainId': 8453,
        })
        
        if dry_run:
            print("   [DRY RUN] Transaction would be:")
            print(f"   To: {tx.get('to')}")
            return True
        
        # Sign and send
        signed_tx = config.w3.eth.account.sign_transaction(tx, config.private_key)
        tx_hash = config.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        
        print(f"   Transaction hash: {tx_hash.hex()}")
        print("   Waiting for confirmation...")
        
        receipt = config.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        
        if receipt['status'] == 1:
            print(f"✅ Rewards claimed successfully!")
            print(f"   Block: {receipt['blockNumber']}")
            print(f"   Gas used: {receipt['gasUsed']}")
            return True
        else:
            print(f"❌ Claim failed")
            return False
            
    except Exception as e:
        print(f"❌ Error claiming rewards: {e}")
        return False


def show_status(config: Config) -> None:
    """Display current mining status."""
    print("\n" + "=" * 50)
    print("          AGENTCOIN MINING STATUS")
    print("=" * 50)
    
    # Agent info
    agent_id = config.get_agent_id()
    print(f"\n👤 Agent Information:")
    print(f"   Address: {config.address}")
    print(f"   Agent ID: {agent_id if agent_id else 'Not registered'}")
    
    # Wallet balances
    eth_balance = config.get_eth_balance()
    print(f"\n💳 Wallet Balance:")
    print(f"   ETH: {eth_balance:.6f} (for gas fees)")
    
    # Rewards
    try:
        pending = config.reward_distributor.functions.getPendingRewards(
            config.address
        ).call()
        claimed = config.reward_distributor.functions.totalClaimed(
            config.address
        ).call()
        
        print(f"\n🏆 Rewards:")
        print(f"   Pending: {format_wei(pending)}")
        print(f"   Total Claimed: {format_wei(claimed)}")
    except Exception as e:
        print(f"\n⚠️  Could not fetch rewards: {e}")
    
    # Current problem
    try:
        problem = config.problem_manager.functions.getCurrentProblem().call()
        if problem and problem[4]:  # active field
            print(f"\n📋 Current Problem:")
            print(f"   ID: {problem[0]}")
            print(f"   Difficulty: {problem[2]}")
            print(f"   Reward: {format_wei(problem[3])}")
            print(f"   Deadline: Block {problem[5]}")
            # Truncate long problem text
            text = problem[1]
            if len(text) > 60:
                text = text[:57] + "..."
            print(f"   Text: {text}")
        else:
            print(f"\n📋 No active problem currently")
    except Exception as e:
        print(f"\n⚠️  Could not fetch current problem: {e}")
    
    print("\n" + "=" * 50 + "\n")


def create_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser."""
    parser = argparse.ArgumentParser(
        description="AgentCoin Mining CLI - Manual operations for AGC mining",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s submit 42 "12345" --private-key 0x...
  %(prog)s claim
  %(prog)s status --rpc-url https://base.llamarpc.com
        """
    )
    
    # Global options
    parser.add_argument(
        '--private-key',
        help='Private key for transaction signing (overrides env var)'
    )
    parser.add_argument(
        '--rpc-url',
        help='RPC URL for Base chain (overrides env var)'
    )
    parser.add_argument(
        '--problem-manager',
        help='ProblemManager contract address (overrides env var)'
    )
    parser.add_argument(
        '--agent-registry',
        help='AgentRegistry contract address (overrides env var)'
    )
    parser.add_argument(
        '--reward-distributor',
        help='RewardDistributor contract address (overrides env var)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Simulate transactions without sending them'
    )
    
    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Submit command
    submit_parser = subparsers.add_parser(
        'submit',
        help='Submit an answer for a problem'
    )
    submit_parser.add_argument(
        'problem_id',
        type=int,
        help='ID of the problem to solve'
    )
    submit_parser.add_argument(
        'answer',
        help='The answer to submit'
    )
    
    # Claim command
    subparsers.add_parser(
        'claim',
        help='Claim pending rewards'
    )
    
    # Status command
    subparsers.add_parser(
        'status',
        help='Show mining status'
    )
    
    return parser


def main() -> int:
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    try:
        # Load configuration
        config = load_config(
            private_key=args.private_key,
            rpc_url=args.rpc_url,
            problem_manager=args.problem_manager,
            agent_registry=args.agent_registry,
            reward_distributor=args.reward_distributor
        )
        
        # For status command, show even if validation has warnings
        if args.command == 'status':
            validate_config(config)
            show_status(config)
            return 0
        
        # For other commands, ensure config is valid
        if not validate_config(config):
            print("\n❌ Configuration validation failed. Please check your settings.")
            return 1
        
        # Execute command
        if args.command == 'submit':
            success = submit_answer(
                config,
                args.problem_id,
                args.answer,
                dry_run=args.dry_run
            )
            return 0 if success else 1
            
        elif args.command == 'claim':
            success = claim_rewards(config, dry_run=args.dry_run)
            return 0 if success else 1
            
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        return 1
    except ConnectionError as e:
        print(f"❌ Connection error: {e}")
        return 1
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        return 130
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
