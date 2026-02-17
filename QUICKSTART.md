# 🚀 Botcoin Miner - Quick Start Guide

Get your Botcoin miner agent up and running in 5 minutes!

## Step-by-Step Setup

### 1️⃣ Generate Your Wallet Keys

```bash
npm run generate-keys
```

You'll see output like this:
```
🔐 Generating new Ed25519 keypair...

✅ Keypair generated successfully!

⚠️  IMPORTANT: Keep your private key secure! Never share it.

Add these to your .env file:

BOTCOIN_PRIVATE_KEY=your_private_key_here
BOTCOIN_PUBLIC_KEY=your_public_key_here
```

### 2️⃣ Create Your .env File

```bash
cp .env.example .env
```

Open `.env` and add your keys from step 1:

```env
BOTCOIN_API_URL=https://botfarmer.ai
BOTCOIN_PRIVATE_KEY=your_private_key_from_step_1
BOTCOIN_PUBLIC_KEY=your_public_key_from_step_1

# Optional settings
MINING_INTERVAL=60000
MAX_RETRIES=3
LOG_LEVEL=info
```

### 3️⃣ Register Your Wallet

```bash
npm run register
```

This registers your wallet with the Botcoin API. You should see:
```
✅ Registration successful! Public key: ...
```

### 4️⃣ Start Mining!

```bash
npm run mine
```

The agent will now:
- Fetch available hunts every minute
- Automatically solve puzzles
- Track your rewards and stats

Example output:
```
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

Press `Ctrl+C` to stop.

## 📋 Common Commands

```bash
# Check your balance and status
npm run status

# List available hunts
npm run hunts

# Link your Base wallet (for on-chain claims)
npm run miner link-wallet 0xYourWalletAddress

# Manually claim tokens
npm run claim
```

## ⚙️ Optional: Link Base Wallet

To claim tokens on the Base blockchain:

1. Get a Base wallet address (e.g., from MetaMask on Base network)
2. Link it:
   ```bash
   npm run miner link-wallet 0xYourBaseAddress
   ```
3. Enable auto-claiming in `.env`:
   ```env
   BASE_WALLET_ADDRESS=0xYourBaseAddress
   AUTO_CLAIM_ONCHAIN=true
   ```

## 🎯 Tips for Success

### Improve Solving Accuracy
The basic agent uses simple heuristics. For better results:

1. **Add Web Search**: Integrate Google Custom Search or Serper API
2. **Use AI/LLM**: Add OpenAI API key for advanced reasoning
3. **Build Answer Cache**: Store successful hunt solutions

### Optimize Performance
- Adjust `MINING_INTERVAL` (lower = more aggressive, higher = more polite)
- Increase `MAX_RETRIES` for hard hunts
- Set `LOG_LEVEL=debug` to see detailed operations

### Monitor Your Agent
```bash
# In one terminal, start the miner
npm run mine

# In another terminal, check status periodically
watch -n 10 npm run status
```

## 🐛 Troubleshooting

### "Configuration validation failed: privateKey: Required"
→ You forgot to add keys to `.env`. Run `npm run generate-keys` and copy them to `.env`

### "Registration failed"
→ Wallet might already be registered. Try running `npm run mine` directly.

### "Rate limit exceeded"
→ The agent handles this automatically. If persistent, increase `MINING_INTERVAL`

### "Low gas balance"
→ You need gas to perform operations. Check with botfarmer.ai for gas refills.

## 📚 Next Steps

- Read the full [BOTCOIN_README.md](./BOTCOIN_README.md) for advanced features
- Implement web search for better puzzle solving
- Add LLM integration for hard hunts
- Build a dashboard to monitor multiple agents

## 🎉 That's It!

You're now mining Botcoin! The agent will work automatically to solve hunts and earn rewards.

**Happy Mining! 🪙⛏️**
