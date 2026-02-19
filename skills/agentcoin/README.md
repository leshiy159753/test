# AgentCoin Mining Skill

Python tools for mining AGC tokens on the Base chain. This skill provides both a CLI tool for manual operations and an auto-mining daemon that fetches problems, solves them, and submits answers on-chain.

## Features

- 🚀 **Auto-Miner Daemon** - Automatically fetch, solve, and submit problem answers
- 🔧 **CLI Tool** - Manual submit, claim, and status commands
- 🛡️ **Safe Problem Solving** - Math expression evaluation with safety checks
- 📊 **Detailed Logging** - Colored output with timestamps and statistics
- ⚙️ **Configurable** - Environment variables and CLI arguments

## Installation

1. Navigate to the skill directory:
```bash
cd skills/agentcoin
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Create environment file:
```bash
cp .env.example .env
```

4. Edit `.env` and add your private key:
```bash
AGC_PRIVATE_KEY=your_private_key_here  # 64 hex characters
```

## Usage

### Quick Start (Auto-Miner)

Run the auto-mining daemon with default settings (5-minute intervals):

```bash
# Via npm script (from project root)
npm run mine

# Or directly
cd skills/agentcoin && python3 miner.py
```

### CLI Tool

Manual operations via the CLI:

```bash
# Via npm script
npm run mine:cli -- <command>

# Or directly
python3 mine.py <command>
```

#### Commands

**Submit an answer:**
```bash
python3 mine.py submit <problem_id> <answer>
# Example: python3 mine.py submit 42 "12345"
```

**Claim rewards:**
```bash
python3 mine.py claim
```

**Check status:**
```bash
python3 mine.py status
```

### Auto-Miner Options

```bash
# Custom check interval (in seconds)
python3 miner.py --interval 60

# Run once and exit
python3 miner.py --one-shot

# Verbose logging
python3 miner.py --verbose

# Override private key via CLI
python3 miner.py --private-key 0x...
```

## Configuration

All configuration is done via environment variables (in `.env` file) or CLI arguments.

### Required

| Variable | Description |
|----------|-------------|
| `AGC_PRIVATE_KEY` | Your wallet private key (64 hex chars) |

### Optional

| Variable | Default | Description |
|----------|---------|-------------|
| `AGC_RPC_URL` | `https://mainnet.base.org` | Base chain RPC endpoint |
| `PROBLEM_MANAGER_ADDRESS` | (see `.env.example`) | ProblemManager contract address |
| `AGENT_REGISTRY_ADDRESS` | (see `.env.example`) | AgentRegistry contract address |
| `REWARD_DISTRIBUTOR_ADDRESS` | (see `.env.example`) | RewardDistributor contract address |

## Problem Solving

The auto-miner includes a problem solver that handles:

- **Math expressions** - Addition, subtraction, multiplication, division, powers
- **Fibonacci numbers** - Find nth Fibonacci number
- **Factorials** - Calculate n!
- **Prime numbers** - Find nth prime
- **Pattern counting** - Count digits, letters, vowels, etc.

Problems containing `{AGENT_ID}` will be automatically personalized with your agent ID before solving.

## Project Structure

```
skills/agentcoin/
├── __init__.py              # Package marker
├── config.py                # Web3 configuration and contract setup
├── mine.py                  # CLI tool for manual operations
├── miner.py                 # Auto-mining daemon
├── requirements.txt         # Python dependencies
├── .env.example             # Environment template
├── README.md               # This file
└── abis/
    ├── problem_manager.json    # ProblemManager ABI
    ├── agent_registry.json     # AgentRegistry ABI
    └── reward_distributor.json # RewardDistributor ABI
```

## Safety & Security

⚠️ **Important:**

- Never commit `.env` files containing private keys
- Use dedicated mining wallets (don't use primary wallets)
- Ensure sufficient ETH for gas fees on Base chain
- Review transaction details before confirming

## Troubleshooting

### "Failed to connect to Base chain"
- Check your RPC URL is correct
- Verify internet connection
- Try a different RPC provider (Infura, Alchemy, etc.)

### "Insufficient ETH for gas"
- Base chain requires ETH for transaction fees
- Ensure your wallet has at least 0.001 ETH

### "Agent not registered"
- You may need to register your agent in the AgentRegistry first
- Check the AgentRegistry contract for registration functions

### Low solver success rate
- The solver handles common math and logic problems
- Complex problems may require manual submission via CLI

---

## BLOKS Agent Mint

Mint NFTs via the **BLOKS Agent Mint API** using a full PoW challenge/verify/mint flow.

### How it works

```
get_mint_phase()
       │
       ├─ "closed"    → exit (nothing to do)
       ├─ "whitelist" → sign EIP-191 message, include in mint payload
       └─ "public"    → proceed without signature
       │
get_pow_challenge()   ← request SHA-256 challenge + difficulty target
       │
solve_pow()           ← brute-force nonce locally (pure Python, no deps)
       │
verify_pow()          ← exchange solved nonce for a one-time mint token
       │
mint()                ← POST mint (+ WL signature when in whitelist phase)
```

### Configuration

Add the following to your `.env` file (see `.env.example`):

| Variable | Required | Default | Description |
|---|---|---|---|
| `AGC_PRIVATE_KEY` | ✅ | — | Wallet private key (shared with AGC mining) |
| `BLOKS_PROJECT_ID` | ✅ | — | BLOKS project / collection ID |
| `BLOKS_API_BASE_URL` | ❌ | `https://api.bloks.io/agent-mint` | API root URL |
| `BLOKS_CHAIN_ID` | ❌ | `8453` | EVM chain ID (Base mainnet) |

### Running the minter

**Via npm (from project root):**
```bash
# Full mint
npm run mint:bloks

# Dry-run — solve PoW but skip the mint transaction
npm run mint:bloks:dry
```

**Directly:**
```bash
cd skills/agentcoin

# Minimal — reads everything from .env
python3 bloks_mint.py

# Override config via CLI
python3 bloks_mint.py \
  --private-key 0xYOURKEY \
  --project-id my-collection \
  --chain-id 8453

# Dry-run with verbose logging
python3 bloks_mint.py --dry-run --verbose

# Custom whitelist message (if the project uses a non-default format)
python3 bloks_mint.py --wl-message "MyProject WL: 0xYourAddress"
```

### CLI Options

| Flag | Description |
|---|---|
| `--private-key HEX` | Wallet private key (overrides env var) |
| `--api-base-url URL` | BLOKS API base URL (overrides env var) |
| `--project-id ID` | BLOKS project ID (overrides env var) |
| `--chain-id INT` | EVM chain ID (overrides env var) |
| `--wl-message MSG` | Custom EIP-191 whitelist message to sign |
| `--max-retries N` | HTTP retries per call (default: 3) |
| `--retry-delay SEC` | Base back-off delay in seconds (default: 2.0) |
| `--dry-run` | Stop before the mint step (test PoW only) |
| `-v / --verbose` | Enable DEBUG-level logging |

### Whitelist signing

When `get_mint_phase()` returns `"whitelist"`, the client automatically:

1. Constructs the signing message:
   `"BLOKS Whitelist Mint: <checksummed_wallet_address>"`
2. Signs it with `eth_account.messages.encode_defunct` (EIP-191 personal sign).
3. Adds `whitelistSignature` and `whitelistAddress` fields to the mint payload.

Pass `--wl-message "..."` if the project requires a custom message format.

### Programmatic usage

```python
from bloks_config import load_bloks_config
from bloks_client import BloksMintClient

config = load_bloks_config(project_id="my-collection")
client = BloksMintClient(config)

# Full flow
result = client.run_mint_flow()
if result:
    print(f"Minted! tx={result.tx_hash} tokenId={result.token_id}")

# Step-by-step
phase     = client.get_mint_phase()
challenge = client.get_pow_challenge()
solution  = client.solve_pow(challenge)
token     = client.verify_pow(solution)
result    = client.mint(token, phase)
```

### Project structure (updated)

```
skills/agentcoin/
├── __init__.py              # Package marker + public exports
├── config.py                # Web3 / AGC mining configuration
├── bloks_config.py          # NEW — BLOKS-specific config dataclass
├── bloks_client.py          # NEW — BLOKS API client (phase/PoW/mint)
├── bloks_mint.py            # NEW — CLI entry point for BLOKS minting
├── mine.py                  # CLI tool for manual AGC operations
├── miner.py                 # Auto-mining daemon
├── requirements.txt         # Python dependencies
├── .env.example             # Environment template (now includes BLOKS vars)
├── README.md                # This file
└── abis/
    ├── problem_manager.json
    ├── agent_registry.json
    └── reward_distributor.json
```

## License

MIT - See project root for details.
