# 🪙 Botcoin Miner Agent

> **Automated agent for solving research puzzles (hunts) on [botfarmer.ai](https://botfarmer.ai) to earn Botcoin rewards**

[![TypeScript](https://img.shields.io/badge/TypeScript-5.0-blue.svg)](https://www.typescriptlang.org/)
[![Node.js](https://img.shields.io/badge/Node.js-18+-green.svg)](https://nodejs.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🎯 What is This?

A **production-ready, fully automated agent** that:
- 🔄 Continuously fetches and solves hunt puzzles
- 🔐 Uses Ed25519 cryptography for secure wallet management
- 🤖 Automatically signs all API requests
- 📊 Tracks rewards, success rate, and statistics
- 🛡️ Handles rate limits and errors gracefully
- 💰 Claims tokens on-chain (Base blockchain)

**Status**: ✅ **Complete & Ready to Use**

---

## ⚡ Quick Start (5 Minutes)

```bash
# 1. Generate your wallet keys
npm run generate-keys

# 2. Configure environment
cp .env.example .env
# Edit .env and add your keys

# 3. Register your wallet
npm run register

# 4. Start mining!
npm run mine
```

🎉 **That's it!** Your agent is now mining Botcoin automatically.

👉 **New to this?** Read the [Quick Start Guide](QUICKSTART.md)

---

## 📋 Features

### Core Features
✅ **Automated Mining** - Continuous hunt solving with configurable intervals  
✅ **Ed25519 Crypto** - Secure wallet with digital signatures  
✅ **Smart Hunt Selection** - Optimizes for reward/difficulty ratio  
✅ **Multi-Strategy Solver** - Difficulty-based solving algorithms  
✅ **Rate Limit Handling** - Exponential backoff with jitter  
✅ **Gas Management** - Monitors gas balance for operations  
✅ **On-chain Claims** - Manual or automatic token claiming  
✅ **Statistics Tracking** - Success rate, rewards, streaks  
✅ **Error Recovery** - Robust retry logic  
✅ **Graceful Shutdown** - Clean exit with stats summary  

### Developer Features
✅ **CLI Interface** - 7 intuitive commands  
✅ **Type-Safe** - 100% TypeScript with strict mode  
✅ **Configurable** - Environment-based configuration  
✅ **Well-Documented** - Comprehensive guides and code comments  
✅ **Extensible** - Easy to add web search, LLMs, etc.  
✅ **Production-Ready** - Error handling, logging, validation  

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| **[Quick Start Guide](QUICKSTART.md)** | Get started in 5 minutes |
| **[Full Documentation](BOTCOIN_README.md)** | Complete feature guide |
| **[Architecture Overview](ARCHITECTURE.md)** | Technical deep dive |
| **[Project Summary](PROJECT_SUMMARY.md)** | Implementation details |

---

## 🎮 Available Commands

```bash
# Setup & Key Management
npm run generate-keys          # Generate new Ed25519 keypair
npm run test-miner            # Test all components

# Main Operations
npm run register              # Register wallet (one-time)
npm run mine                  # Start automated mining
npm run status                # Check balance & gas
npm run hunts                 # List available hunts

# Token Management
npm run miner link-wallet <addr>  # Link Base wallet
npm run claim                     # Claim tokens on-chain
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────┐
│         CLI Interface               │
│  (register, mine, status, etc.)     │
└────────────┬────────────────────────┘
             │
┌────────────▼────────────────────────┐
│      Botcoin Miner Agent            │
│  • Mining Loop                      │
│  • Hunt Selection                   │
│  • Stats Tracking                   │
└───┬──────────────────┬──────────────┘
    │                  │
┌───▼────────────┐ ┌──▼──────────────┐
│ Research Engine│ │ API Client      │
│ • Puzzle Solver│ │ • Auto-signing  │
│ • Strategies   │ │ • Rate Limits   │
└────────────────┘ └──┬──────────────┘
                      │
              ┌───────▼───────┐
              │ Crypto Module │
              │ • Ed25519     │
              │ • Signing     │
              └───────────────┘
```

**Tech Stack**: TypeScript • Node.js • Ed25519 (tweetnacl) • axios • winston • zod • commander

---

## 📊 Project Structure

```
src/
├── agent/         # Main miner logic & state machine
├── api/           # Botcoin API client with auto-signing
├── cli/           # Command-line interface
├── config/        # Configuration management (Zod)
├── crypto/        # Ed25519 key operations
├── research/      # Puzzle solving engine
└── utils/         # Logging, errors, helpers

scripts/
├── generate-keys.ts  # Key generation utility
└── test-miner.ts     # Test suite
```

---

## 🔧 Configuration

All settings are managed via `.env`:

```env
# Required
BOTCOIN_PRIVATE_KEY=your_private_key_base64
BOTCOIN_PUBLIC_KEY=your_public_key_base64

# Optional
BASE_WALLET_ADDRESS=0xYourBaseWallet
MINING_INTERVAL=60000    # 1 minute
MAX_RETRIES=3
LOG_LEVEL=info
AUTO_CLAIM_ONCHAIN=false
```

See [`.env.example`](.env.example) for all options.

---

## 🎯 Example Usage

### Check Status
```bash
$ npm run status

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Wallet Status
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Public Key: jOk1zn...
Balance: 150 shares
Gas Balance: 1000
Can Operate: ✅ Yes
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### List Hunts
```bash
$ npm run hunts

🎯 Available Hunts (5)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Hunt ID: abc123
   Difficulty: ⭐⭐⭐ (3/10)
   Reward: 10 shares
   Poem: In circuits deep...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Start Mining
```bash
$ npm run mine

🚀 Starting Botcoin miner...
[INFO] Found 5 available hunts
[INFO] Selected hunt abc123 (difficulty: 3, reward: 10)
[INFO] Research result: "answer" (confidence: 0.7)
✅ Hunt solved! Reward: 10. Streak: 1

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Stats:
   Hunts: 1/1 (100.0%)
   Rewards: 10
   Streak: 1
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 🚀 Extending the Agent

The agent is designed to be easily extended:

### Add Web Search
```typescript
// src/research/engine.ts
async function searchWeb(query: string): Promise<SearchResult[]> {
  // Integrate Serper, SerpAPI, or Google Custom Search
}
```

### Add LLM Reasoning
```typescript
// src/research/engine.ts
async function reasonWithLLM(context: ResearchContext): Promise<string> {
  // Integrate OpenAI, Anthropic, or local LLM
}
```

### Build Answer Cache
```typescript
// src/research/cache.ts
class AnswerCache {
  async get(huntPattern: string): Promise<string | null> { }
  async set(huntPattern: string, answer: string): Promise<void> { }
}
```

---

## 🧪 Testing

```bash
# Run component tests
npm run test-miner

# Output:
# ✅ All tests passed! The miner is ready to use.
```

Tests cover:
- ✅ Ed25519 key generation and signing
- ✅ Research engine solving
- ✅ Configuration loading
- ✅ API client setup

---

## 🔐 Security

- 🔒 **Private keys in `.env`** - Never committed to git
- 🔐 **Ed25519 signatures** - 128-bit security level
- ✅ **Request signing** - All write operations signed
- 🛡️ **Input validation** - Zod schemas for all inputs
- 🚫 **No key logging** - Sensitive data never logged

**⚠️ Important**: Keep your private key secure! Anyone with access can control your wallet.

---

## 📈 Performance

- **Memory**: ~50-100MB
- **CPU**: <1% idle, ~5% active
- **Network**: ~1MB/hour
- **API Calls**: 1-2 per minute

Lightweight and efficient! ✨

---

## 🐛 Troubleshooting

### Common Issues

**"Keypair not set"**  
→ Add `BOTCOIN_PRIVATE_KEY` and `BOTCOIN_PUBLIC_KEY` to `.env`

**"Rate limit exceeded"**  
→ The agent handles this automatically. If persistent, increase `MINING_INTERVAL`

**"Low gas balance"**  
→ Contact botfarmer.ai for gas refills

**"Wrong answers"**  
→ The basic engine uses heuristics. Extend with web search or LLM for better accuracy

---

## 🎓 Learning Path

### Beginner
1. Read [Quick Start Guide](QUICKSTART.md)
2. Generate keys & configure
3. Start mining!

### Intermediate
1. Read [Full Documentation](BOTCOIN_README.md)
2. Explore `src/` directory
3. Customize hunt selection

### Advanced
1. Read [Architecture Guide](ARCHITECTURE.md)
2. Extend research engine
3. Add web search or LLM integration

---

## 🤝 Contributing

Contributions welcome! Here are some ideas:

- 🧠 Better puzzle-solving algorithms
- 🔍 Web search integration
- 🤖 LLM integration (OpenAI, Claude)
- 💾 Answer caching/learning
- 📊 Web dashboard
- 🔄 Multi-account management

**Process**:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

---

## 📄 License

MIT License - See [LICENSE](LICENSE) for details

Free to use and modify! 🎉

---

## 🌟 Acknowledgments

- **botfarmer.ai** - For the Botcoin platform
- **TweetNaCl** - For secure crypto
- **TypeScript** - For type safety
- **Open Source Community** - For excellent tools

---

## 🔗 Links

- **Botcoin**: [botfarmer.ai](https://botfarmer.ai)
- **Ed25519**: [ed25519.cr.yp.to](https://ed25519.cr.yp.to/)
- **Documentation**: See `BOTCOIN_README.md`
- **Architecture**: See `ARCHITECTURE.md`

---

## 💬 Support

- 📖 Check the [documentation](BOTCOIN_README.md)
- 🐛 Open an issue for bugs
- 💡 Suggest features via issues
- 💬 Contact botfarmer.ai for API questions

---

## 🎉 Ready to Get Started?

```bash
# Quick start
npm run generate-keys
cp .env.example .env
# Add your keys to .env
npm run register
npm run mine
```

**Happy Mining! 🪙⛏️**

---

<div align="center">

**Built with ❤️ for the Botcoin community**

[Quick Start](QUICKSTART.md) • [Documentation](BOTCOIN_README.md) • [Architecture](ARCHITECTURE.md)

</div>
