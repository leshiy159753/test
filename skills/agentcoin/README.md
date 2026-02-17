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

## License

MIT - See project root for details.
