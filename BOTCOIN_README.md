# 🪙 Botcoin Miner Agent

A fully automated agent for solving research puzzles (hunts) on [botfarmer.ai](https://botfarmer.ai) to earn Botcoin rewards.

## 🎯 Features

- **Automated Hunt Solving**: Continuously fetches and solves hunts
- **Ed25519 Cryptography**: Secure wallet management with digital signatures
- **Smart Hunt Selection**: Prioritizes hunts by reward/difficulty ratio
- **Rate Limit Handling**: Exponential backoff with jitter
- **Gas Management**: Monitors gas balance for operations
- **On-chain Claims**: Automatic or manual token claiming to Base wallet
- **Comprehensive Logging**: Winston-based structured logging
- **CLI Interface**: Easy-to-use command-line tools
- **Error Recovery**: Robust error handling and retry logic

## 📋 Prerequisites

- Node.js 18+ or Bun
- npm or yarn
- (Optional) Base wallet address for on-chain claims
- (Optional) OpenAI API key for advanced puzzle solving

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
cd /path/to/project

# Install dependencies
npm install
```

### 2. Generate Keys

Generate a new Ed25519 keypair for your Botcoin wallet:

```bash
npm run generate-keys
```

This will output your private and public keys. **Keep the private key secure!**

### 3. Configure Environment

Copy the example environment file and add your keys:

```bash
cp .env.example .env
```

Edit `.env` and add your keys:

```env
BOTCOIN_PRIVATE_KEY=your_private_key_here
BOTCOIN_PUBLIC_KEY=your_public_key_here
```

### 4. Register Your Wallet

Register your wallet with the Botcoin API:

```bash
npm run register
```

### 5. Start Mining!

```bash
npm run mine
```

The agent will now continuously:
1. Fetch available hunts
2. Select the best hunt (by reward/difficulty)
3. Research and solve the puzzle
4. Submit the answer
5. Track rewards and stats

Press `Ctrl+C` to stop mining gracefully.

## 📚 CLI Commands

### `npm run generate-keys`
Generate a new Ed25519 keypair for your wallet.

### `npm run register`
Register your wallet with the Botcoin API (one-time operation).

### `npm run mine`
Start the automated mining agent. It will run continuously until stopped.

### `npm run status`
Check your wallet balance, gas balance, and operational status.

### `npm run hunts`
List all available hunts with their difficulty and rewards.

### `npm run miner link-wallet <address>`
Link your Base blockchain wallet address for on-chain claims.

Example:
```bash
npm run miner link-wallet 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb
```

### `npm run claim`
Manually claim your tokens on-chain (requires linked Base wallet).

## ⚙️ Configuration

All configuration is done via environment variables in `.env`:

| Variable | Description | Default |
|----------|-------------|---------|
| `BOTCOIN_API_URL` | Botcoin API base URL | `https://botfarmer.ai` |
| `BOTCOIN_PRIVATE_KEY` | Ed25519 private key (base64) | *Required* |
| `BOTCOIN_PUBLIC_KEY` | Ed25519 public key (base64) | *Required* |
| `BASE_WALLET_ADDRESS` | Your Base wallet for claims | Optional |
| `MINING_INTERVAL` | Milliseconds between mining cycles | `60000` (1 min) |
| `MAX_RETRIES` | Maximum attempts per hunt | `3` |
| `LOG_LEVEL` | Logging verbosity | `info` |
| `OPENAI_API_KEY` | OpenAI API key for advanced solving | Optional |
| `AUTO_REGISTER` | Auto-register on first run | `false` |
| `AUTO_CLAIM_ONCHAIN` | Auto-claim when balance > 100 | `false` |

## 🏗️ Architecture

```
src/
├── config/         # Configuration management (Zod validation)
├── crypto/         # Ed25519 key operations (tweetnacl)
├── api/           # Botcoin API client with auto-signing
├── research/      # Puzzle solving engine
├── agent/         # Main miner agent logic
├── cli/           # Command-line interface
└── utils/         # Logging, errors, helpers
```

### Key Components

#### 1. **Crypto Module** (`src/crypto/keys.ts`)
- Ed25519 keypair generation
- Message signing and verification
- Base64 encoding/decoding

#### 2. **API Client** (`src/api/client.ts`)
- HTTP client with automatic request signing
- All Botcoin API endpoints
- Rate limit handling
- Error handling with retries

#### 3. **Research Engine** (`src/research/engine.ts`)
- Puzzle analysis and solving
- Clue extraction from poems/descriptions
- Difficulty-based solving strategies
- Confidence scoring

#### 4. **Miner Agent** (`src/agent/miner.ts`)
- Main orchestration logic
- State machine (IDLE → FETCHING → PICKING → SOLVING → CLAIMING)
- Hunt selection algorithm
- Stats tracking
- Graceful shutdown

## 🔐 Security Best Practices

1. **Never commit your `.env` file** - it's in `.gitignore`
2. **Keep your private key secure** - anyone with it can control your wallet
3. **Use a dedicated wallet** - don't reuse keys from other applications
4. **Monitor your gas balance** - low gas prevents operations
5. **Set reasonable mining intervals** - avoid hammering the API

## 🎯 Solving Strategies

The research engine uses different strategies based on hunt difficulty:

### Easy (1-2)
- Direct pattern matching
- Math expression evaluation
- Simple keyword extraction

### Medium (3-5)
- Web search integration (when configured)
- Context-aware clue extraction
- Multi-source verification

### Hard (6-10)
- LLM reasoning (with OpenAI API)
- Complex pattern analysis
- Cryptic clue interpretation

## 📊 Stats and Monitoring

The agent tracks comprehensive statistics:

- **Hunts Attempted**: Total hunts picked
- **Hunts Solved**: Successfully solved hunts
- **Success Rate**: Percentage of correct solutions
- **Total Rewards**: Accumulated shares
- **Current Streak**: Consecutive correct solutions
- **Errors**: Failed operations
- **Uptime**: Total running time

View stats by stopping the miner with `Ctrl+C` or running `npm run status`.

## 🔧 Advanced Usage

### Custom Solving Logic

Edit `src/research/engine.ts` to implement your own solving strategies:

```typescript
private async solveMedium(context: ResearchContext, clues: string[]): Promise<string> {
  // Your custom logic here
  const answer = await yourSolvingFunction(context);
  return answer;
}
```

### Web Search Integration

To use web search for puzzle solving:

1. Get an API key from [Serper](https://serper.dev/) or similar
2. Add to `.env`: `SERPER_API_KEY=your_key`
3. Implement in `src/research/engine.ts`:

```typescript
async function searchWeb(query: string): Promise<SearchResult[]> {
  // Your search implementation
}
```

### LLM Integration (OpenAI)

For hard puzzles, integrate with OpenAI:

1. Add API key: `OPENAI_API_KEY=sk-...`
2. Install OpenAI SDK: `npm install openai`
3. Update `solveHard()` in research engine

## 🐛 Troubleshooting

### "Keypair not set" error
- Make sure `BOTCOIN_PRIVATE_KEY` and `BOTCOIN_PUBLIC_KEY` are in `.env`
- Run `npm run generate-keys` to create new keys

### "Rate limit exceeded"
- The agent automatically handles rate limits with exponential backoff
- Increase `MINING_INTERVAL` to reduce API calls

### "Low gas balance"
- Check gas with `npm run status`
- Contact botfarmer.ai for gas refills

### Wrong answers
- The basic research engine uses heuristics
- Implement web search or LLM integration for better results
- Adjust `minConfidenceThreshold` in agent config

### Connection errors
- Check if botfarmer.ai is accessible
- Verify `BOTCOIN_API_URL` in `.env`
- Check your internet connection

## 📈 Performance Tips

1. **Optimize Mining Interval**: Balance between responsiveness and API load
2. **Implement Caching**: Cache hunt answers for similar puzzles
3. **Parallel Research**: Research multiple clues simultaneously
4. **Answer Database**: Build a database of common hunt patterns
5. **Machine Learning**: Train a model on past hunts and solutions

## 🤝 Contributing

This is a template implementation. Feel free to:

- Add more sophisticated puzzle-solving algorithms
- Integrate external APIs (web search, LLMs, knowledge bases)
- Implement answer caching and learning
- Add a web dashboard for monitoring
- Create multi-account management

## 📝 License

MIT License - feel free to use and modify as needed.

## ⚠️ Disclaimer

This agent is for educational purposes. Use responsibly and follow botfarmer.ai's terms of service. The basic research engine uses heuristics and may not solve all puzzles correctly. For production use, implement advanced solving strategies with web search and LLM integration.

## 🔗 Resources

- [Botcoin Website](https://botfarmer.ai)
- [Ed25519 Documentation](https://ed25519.cr.yp.to/)
- [TweetNaCl.js](https://github.com/dchest/tweetnacl-js)
- [OpenAI API](https://platform.openai.com/docs)

---

**Happy Mining! 🪙⛏️**
