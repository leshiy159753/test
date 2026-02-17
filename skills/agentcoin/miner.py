#!/usr/bin/env python3
"""
AgentCoin Auto-Miner Daemon

Automatically fetches problems, solves them, and submits answers on-chain.

Usage:
    python miner.py [--interval SECONDS] [--one-shot]
    python miner.py --help
"""

import argparse
import json
import logging
import re
import sys
import time
from dataclasses import dataclass
from typing import Optional, Tuple

import requests
from web3.exceptions import ContractLogicError

from config import load_config, validate_config, Config


# Setup logging with timestamps and colors
class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for different log levels."""
    
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'
    }
    
    def format(self, record):
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        record.levelname = f"{color}{record.levelname}{self.COLORS['RESET']}"
        return super().format(record)


# Configure logging
handler = logging.StreamHandler()
handler.setFormatter(ColoredFormatter(
    '%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
))
logger = logging.getLogger('agentcoin-miner')
logger.setLevel(logging.INFO)
logger.addHandler(handler)


API_BASE_URL = "https://api.agentcoin.site/api"
DEFAULT_INTERVAL = 300  # 5 minutes
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds


@dataclass
class Problem:
    """Represents a mining problem."""
    id: int
    text: str
    difficulty: int
    reward: str
    agent_id_placeholder: str = "{AGENT_ID}"
    
    @classmethod
    def from_api(cls, data: dict) -> 'Problem':
        """Create Problem from API response."""
        return cls(
            id=data.get('id', 0),
            text=data.get('text', ''),
            difficulty=data.get('difficulty', 1),
            reward=data.get('reward', '0')
        )
    
    def personalize(self, agent_id: int) -> str:
        """Replace AGENT_ID placeholder with actual agent ID."""
        return self.text.replace(self.agent_id_placeholder, str(agent_id))


class ProblemSolver:
    """Solver for AgentCoin math and logic problems."""
    
    # Safe operators for eval
    SAFE_OPERATORS = {
        '+': lambda x, y: x + y,
        '-': lambda x, y: x - y,
        '*': lambda x, y: x * y,
        '/': lambda x, y: x / y if y != 0 else 0,
        '**': lambda x, y: x ** y,
        '//': lambda x, y: x // y if y != 0 else 0,
        '%': lambda x, y: x % y if y != 0 else 0,
    }
    
    def __init__(self):
        self.solved_count = 0
        self.failed_count = 0
    
    def solve(self, problem_text: str, agent_id: int) -> Optional[str]:
        """
        Solve a problem given its text.
        
        Args:
            problem_text: The problem text (with AGENT_ID already replaced)
            agent_id: The agent ID for personalization
        
        Returns:
            str: The answer, or None if unable to solve
        """
        logger.debug(f"Solving problem: {problem_text[:80]}...")
        
        # Try different solving strategies
        answer = None
        
        # Strategy 1: Simple math expression
        answer = self._solve_math_expression(problem_text)
        if answer:
            return answer
        
        # Strategy 2: Pattern-based logic problems
        answer = self._solve_pattern_problem(problem_text)
        if answer:
            return answer
        
        # Strategy 3: Counting/sequence problems
        answer = self._solve_sequence_problem(problem_text)
        if answer:
            return answer
        
        logger.warning(f"Unable to solve problem: {problem_text[:100]}...")
        self.failed_count += 1
        return None
    
    def _solve_math_expression(self, text: str) -> Optional[str]:
        """
        Extract and solve a math expression from problem text.
        
        Uses safe evaluation with limited operators.
        """
        # Look for expressions like "Calculate: 2 + 2" or "What is 5 * 3?"
        patterns = [
            r'(?:calculate|what is|compute|solve)[\s:]*(\d+[\s\+\-\*\/\%\^\d\s\.]+\d)',
            r'(\d+[\s\+\-\*\/\%\^\d\s\.]+\d)\s*(?:\?|=)',
            r'([\d\s\+\-\*\/\%\^\.]+\d)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                expr = match.group(1).strip()
                try:
                    # Replace ^ with ** for Python compatibility
                    expr = expr.replace('^', '**')
                    # Use safe evaluation
                    result = self._safe_eval(expr)
                    if result is not None:
                        self.solved_count += 1
                        return str(int(result)) if result == int(result) else str(result)
                except Exception as e:
                    logger.debug(f"Math evaluation failed for '{expr}': {e}")
                    continue
        
        return None
    
    def _safe_eval(self, expr: str) -> Optional[float]:
        """
        Safely evaluate a mathematical expression.
        
        Only allows basic arithmetic operations.
        """
        # Remove any non-math characters
        expr = re.sub(r'[^\d\+\-\*\/\%\(\)\.\s]', '', expr)
        
        if not expr:
            return None
        
        try:
            # Use ast.literal_eval for simple cases, or restricted eval
            import ast
            
            # Parse the expression
            tree = ast.parse(expr, mode='eval')
            
            # Validate only safe operations
            allowed_nodes = (
                ast.Expression, ast.BinOp, ast.UnaryOp, ast.Num,
                ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod,
                ast.Pow, ast.FloorDiv, ast.USub, ast.UAdd
            )
            
            for node in ast.walk(tree):
                if not isinstance(node, allowed_nodes):
                    logger.debug(f"Disallowed node type: {type(node)}")
                    return None
            
            # Evaluate safely
            result = eval(compile(tree, '<string>', 'eval'), {"__builtins__": {}}, {})
            return float(result)
            
        except Exception as e:
            logger.debug(f"Safe eval failed: {e}")
            return None
    
    def _solve_pattern_problem(self, text: str) -> Optional[str]:
        """Solve pattern-based logic problems."""
        # Common patterns: Fibonacci, prime numbers, factorials
        
        # Check for Fibonacci references
        fib_patterns = [
            r'fibonacci\s+(?:number|sequence)\s*(?:at\s+position\s*)?(\d+)',
            r'(\d+)(?:st|nd|rd|th)?\s+fibonacci',
        ]
        for pattern in fib_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                n = int(match.group(1))
                result = self._fibonacci(n)
                self.solved_count += 1
                return str(result)
        
        # Check for factorial
        fact_pattern = r'(\d+)!|factorial\s+of\s+(\d+)'
        match = re.search(fact_pattern, text, re.IGNORECASE)
        if match:
            n = int(match.group(1) or match.group(2))
            result = self._factorial(n)
            self.solved_count += 1
            return str(result)
        
        # Check for prime-related questions
        prime_pattern = r'(\d+)(?:st|nd|rd|th)?\s+prime'
        match = re.search(prime_pattern, text, re.IGNORECASE)
        if match:
            n = int(match.group(1))
            result = self._nth_prime(n)
            self.solved_count += 1
            return str(result)
        
        return None
    
    def _solve_sequence_problem(self, text: str) -> Optional[str]:
        """Solve sequence and counting problems."""
        # Count occurrences of specific characters/patterns
        count_patterns = [
            r'how many\s+(\w+)\s+in\s+["\']?([^"\']+)["\']?',
            r'count\s+(?:the\s+)?(\w+)\s+(?:in\s+)?["\']?([^"\']+)["\']?',
        ]
        
        for pattern in count_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                char_type = match.group(1).lower()
                target = match.group(2)
                
                if char_type in ['digit', 'digits', 'number', 'numbers']:
                    count = sum(c.isdigit() for c in target)
                elif char_type in ['letter', 'letters', 'char', 'chars', 'character']:
                    count = sum(c.isalpha() for c in target)
                elif char_type in ['vowel', 'vowels']:
                    count = sum(c.lower() in 'aeiou' for c in target)
                elif char_type in ['consonant', 'consonants']:
                    count = sum(c.isalpha() and c.lower() not in 'aeiou' for c in target)
                else:
                    count = target.count(char_type)
                
                self.solved_count += 1
                return str(count)
        
        return None
    
    def _fibonacci(self, n: int) -> int:
        """Calculate nth Fibonacci number."""
        if n <= 0:
            return 0
        if n == 1:
            return 1
        a, b = 0, 1
        for _ in range(2, n + 1):
            a, b = b, a + b
        return b
    
    def _factorial(self, n: int) -> int:
        """Calculate factorial."""
        if n < 0:
            return 0
        result = 1
        for i in range(2, n + 1):
            result *= i
        return result
    
    def _nth_prime(self, n: int) -> int:
        """Find the nth prime number."""
        if n <= 0:
            return 0
        count = 0
        num = 2
        while True:
            if self._is_prime(num):
                count += 1
                if count == n:
                    return num
            num += 1
    
    def _is_prime(self, num: int) -> bool:
        """Check if a number is prime."""
        if num < 2:
            return False
        for i in range(2, int(num ** 0.5) + 1):
            if num % i == 0:
                return False
        return True
    
    def get_stats(self) -> dict:
        """Get solver statistics."""
        total = self.solved_count + self.failed_count
        success_rate = (self.solved_count / total * 100) if total > 0 else 0
        return {
            'solved': self.solved_count,
            'failed': self.failed_count,
            'success_rate': success_rate
        }


class AutoMiner:
    """Auto-mining daemon for AgentCoin."""
    
    def __init__(self, config: Config, interval: int = DEFAULT_INTERVAL):
        self.config = config
        self.interval = interval
        self.solver = ProblemSolver()
        self.running = False
        self.submissions = 0
        self.successful_submissions = 0
    
    def fetch_current_problem(self) -> Optional[Problem]:
        """
        Fetch the current problem from API.
        
        Returns:
            Problem object or None if no active problem
        """
        url = f"{API_BASE_URL}/problem/current"
        
        for attempt in range(MAX_RETRIES):
            try:
                logger.debug(f"Fetching problem from {url}")
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                
                # Handle different response formats
                if isinstance(data, dict):
                    if data.get('active', True):
                        return Problem.from_api(data)
                    else:
                        logger.info("No active problem currently")
                        return None
                else:
                    logger.warning(f"Unexpected API response format: {type(data)}")
                    return None
                    
            except requests.exceptions.RequestException as e:
                logger.warning(f"API request failed (attempt {attempt + 1}/{MAX_RETRIES}): {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY * (attempt + 1))  # Exponential backoff
                else:
                    logger.error("Max retries exceeded for API request")
                    return None
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse API response: {e}")
                return None
    
    def submit_on_chain(self, problem_id: int, answer: str) -> bool:
        """
        Submit answer on-chain.
        
        Args:
            problem_id: Problem ID
            answer: Answer to submit
        
        Returns:
            bool: True if submission was successful
        """
        try:
            logger.info(f"📤 Submitting answer for problem #{problem_id}")
            
            # Build transaction
            tx = self.config.problem_manager.functions.submitAnswer(
                problem_id,
                answer
            ).build_transaction({
                'from': self.config.address,
                'nonce': self.config.w3.eth.get_transaction_count(self.config.address),
                'gas': 300000,
                'maxFeePerGas': self.config.w3.to_wei('0.1', 'gwei'),
                'maxPriorityFeePerGas': self.config.w3.to_wei('0.01', 'gwei'),
                'chainId': 8453,
            })
            
            # Sign transaction
            signed_tx = self.config.w3.eth.account.sign_transaction(
                tx, self.config.private_key
            )
            
            # Send transaction
            tx_hash = self.config.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            tx_hash_hex = tx_hash.hex()
            logger.info(f"   Transaction sent: {tx_hash_hex[:20]}...")
            
            # Wait for receipt
            receipt = self.config.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            
            if receipt['status'] == 1:
                logger.info(f"✅ Transaction confirmed in block {receipt['blockNumber']}")
                self.successful_submissions += 1
                return True
            else:
                logger.error(f"❌ Transaction failed (status: {receipt['status']})")
                return False
                
        except ContractLogicError as e:
            logger.error(f"❌ Contract error: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Error submitting transaction: {e}")
            return False
        finally:
            self.submissions += 1
    
    def run_single_iteration(self) -> bool:
        """
        Run a single mining iteration.
        
        Returns:
            bool: True if successful submission, False otherwise
        """
        # Fetch problem
        problem = self.fetch_current_problem()
        if not problem:
            return False
        
        logger.info(f"📋 Found problem #{problem.id} (difficulty: {problem.difficulty})")
        logger.debug(f"   Text: {problem.text[:100]}...")
        
        # Get agent ID for personalization
        agent_id = self.config.get_agent_id() or 0
        
        # Personalize problem text
        personalized_text = problem.personalize(agent_id)
        
        # Solve problem
        answer = self.solver.solve(personalized_text, agent_id)
        if not answer:
            logger.warning("❌ Could not solve problem, skipping")
            return False
        
        logger.info(f"💡 Solved: {answer}")
        
        # Submit on-chain
        return self.submit_on_chain(problem.id, answer)
    
    def run(self, one_shot: bool = False) -> None:
        """
        Run the auto-miner daemon.
        
        Args:
            one_shot: If True, run once and exit; otherwise loop forever
        """
        logger.info("=" * 60)
        logger.info("      AGENTCOIN AUTO-MINER STARTED")
        logger.info("=" * 60)
        logger.info(f"Address: {self.config.address}")
        logger.info(f"Agent ID: {self.config.get_agent_id() or 'Not registered'}")
        logger.info(f"Interval: {self.interval} seconds")
        logger.info("-" * 60)
        
        self.running = True
        
        try:
            while self.running:
                # Run iteration
                try:
                    self.run_single_iteration()
                except Exception as e:
                    logger.error(f"Error in mining iteration: {e}")
                
                # Show stats
                stats = self.solver.get_stats()
                logger.info(
                    f"📊 Stats: {self.successful_submissions}/{self.submissions} "
                    f"tx successful | Solver: {stats['solved']}/{stats['solved'] + stats['failed']} "
                    f"({stats['success_rate']:.1f}%)"
                )
                
                if one_shot:
                    logger.info("One-shot mode, exiting")
                    break
                
                # Wait before next iteration
                logger.info(f"⏳ Waiting {self.interval}s before next check...")
                time.sleep(self.interval)
                
        except KeyboardInterrupt:
            logger.info("\n⚠️  Interrupted by user, shutting down...")
        finally:
            self.running = False
            self._print_final_stats()
    
    def _print_final_stats(self) -> None:
        """Print final statistics."""
        logger.info("=" * 60)
        logger.info("      MINING SESSION COMPLETE")
        logger.info("=" * 60)
        logger.info(f"Total submissions: {self.submissions}")
        logger.info(f"Successful: {self.successful_submissions}")
        solver_stats = self.solver.get_stats()
        logger.info(f"Problems solved: {solver_stats['solved']}")
        logger.info(f"Problems failed: {solver_stats['failed']}")
        logger.info(f"Solver accuracy: {solver_stats['success_rate']:.1f}%")
        logger.info("=" * 60)


def create_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser."""
    parser = argparse.ArgumentParser(
        description="AgentCoin Auto-Miner - Automated AGC mining daemon",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                           # Run with default settings (5 min interval)
  %(prog)s --interval 60             # Check every 60 seconds
  %(prog)s --one-shot                # Run once and exit
  %(prog)s --private-key 0x...       # Override private key
        """
    )
    
    parser.add_argument(
        '--interval',
        type=int,
        default=DEFAULT_INTERVAL,
        help=f'Mining check interval in seconds (default: {DEFAULT_INTERVAL})'
    )
    parser.add_argument(
        '--one-shot',
        action='store_true',
        help='Run once and exit instead of looping'
    )
    parser.add_argument(
        '--private-key',
        help='Private key for transaction signing (overrides env var)'
    )
    parser.add_argument(
        '--rpc-url',
        help='RPC URL for Base chain (overrides env var)'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    return parser


def main() -> int:
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    try:
        # Load configuration
        config = load_config(
            private_key=args.private_key,
            rpc_url=args.rpc_url
        )
        
        # Validate configuration
        if not validate_config(config):
            logger.error("Configuration validation failed. Please check your settings.")
            return 1
        
        # Check ETH balance
        eth_balance = config.get_eth_balance()
        if eth_balance < 0.001:
            logger.warning(f"Low ETH balance ({eth_balance:.6f}), may not have enough for gas")
        
        # Create and run miner
        miner = AutoMiner(config, interval=args.interval)
        miner.run(one_shot=args.one_shot)
        
        return 0
        
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        return 1
    except ConnectionError as e:
        logger.error(f"Connection error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
