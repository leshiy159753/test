# 🏗️ Botcoin Miner - Architecture Overview

This document explains the internal architecture and design decisions of the Botcoin miner agent.

## 📐 System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         CLI Interface                        │
│  (Commander.js - User commands: mine, register, status)     │
└─────────────────┬───────────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────────┐
│                      Botcoin Miner Agent                     │
│  • State Machine (IDLE → FETCHING → SOLVING → CLAIMING)     │
│  • Mining Loop (continuous operation)                       │
│  • Stats Tracking (success rate, rewards, streaks)          │
│  • Error Recovery & Retry Logic                             │
└───────┬──────────────────────┬──────────────────────────────┘
        │                      │
┌───────▼──────────┐   ┌───────▼──────────────────────────────┐
│  Research Engine │   │     Botcoin API Client               │
│  • Puzzle Solver │   │  • HTTP Client (axios)               │
│  • Clue Extract  │   │  • Auto-signing (Ed25519)            │
│  • Strategies    │   │  • Rate Limit Handling               │
│  • Confidence    │   │  • Error Management                  │
└──────────────────┘   └──────────┬───────────────────────────┘
                                  │
                    ┌─────────────▼─────────────────┐
                    │      Crypto Module            │
                    │  • Ed25519 Key Management     │
                    │  • Message Signing            │
                    │  • Signature Verification     │
                    └───────────────────────────────┘
```

## 🧩 Core Components

### 1. Configuration Layer (`src/config/`)

**Purpose**: Centralized configuration with validation

**Key Features**:
- Environment variable loading with `dotenv`
- Schema validation using `Zod`
- Type-safe configuration
- Required field validation

**Files**:
- `index.ts` - Configuration schema and loader

**Design Pattern**: Singleton with lazy loading

### 2. Cryptography Layer (`src/crypto/`)

**Purpose**: Ed25519 cryptographic operations

**Key Features**:
- Keypair generation (random or from seed)
- Message signing with private key
- Signature verification
- Base64 encoding/decoding

**Files**:
- `keys.ts` - All crypto operations

**Library**: `tweetnacl` - Audited, battle-tested crypto library

**Security Considerations**:
- Private keys are 64 bytes (512 bits)
- Public keys are 32 bytes (256 bits)
- Signatures are 64 bytes
- Uses Ed25519 (curve25519-based)

### 3. API Client Layer (`src/api/`)

**Purpose**: Communication with Botcoin API

**Key Features**:
- RESTful HTTP client
- Automatic request signing
- Response parsing and validation
- Error handling with retries
- Rate limit detection

**Files**:
- `client.ts` - HTTP client with signing
- `types.ts` - TypeScript type definitions

**Design Pattern**: Repository pattern with interceptors

**Endpoints**:
```typescript
GET  /api/register/challenge     // Get math challenge
POST /api/register               // Register wallet
GET  /api/hunts                  // List available hunts
POST /api/hunts/pick             // Pick a hunt (signed)
POST /api/hunts/solve            // Submit answer (signed)
POST /api/link-wallet            // Link Base wallet (signed)
POST /api/claim-onchain          // Claim tokens (signed)
GET  /api/gas                    // Check gas balance
GET  /api/balance/:publicKey     // Check balance
```

**Signing Process**:
1. Create payload object
2. Stringify payload to JSON
3. Sign JSON string with private key
4. Add signature + public key to request
5. Send to API

### 4. Research Engine (`src/research/`)

**Purpose**: Solve hunt puzzles

**Key Features**:
- Clue extraction from poems/descriptions
- Multi-strategy solving (difficulty-based)
- Confidence scoring
- Extensible architecture for AI integration

**Files**:
- `engine.ts` - Core solving logic
- `types.ts` - Research type definitions

**Solving Strategies**:

#### Easy (Difficulty 1-2)
- Direct pattern matching
- Math expression evaluation
- Keyword extraction
- Quote detection

#### Medium (Difficulty 3-5)
- Context-aware clue extraction
- Multi-source verification
- *Extensible*: Web search integration

#### Hard (Difficulty 6-10)
- Complex pattern analysis
- *Extensible*: LLM reasoning
- Cryptic clue interpretation

**Extension Points**:
```typescript
// Add web search
async function searchWeb(query: string): Promise<SearchResult[]> {
  // Integrate Serper, SerpAPI, or Google Custom Search
}

// Add LLM reasoning
async function reasonWithLLM(context: ResearchContext): Promise<string> {
  // Integrate OpenAI, Anthropic, or local LLM
}
```

### 5. Agent Core (`src/agent/`)

**Purpose**: Main orchestration and mining loop

**Key Features**:
- State machine management
- Continuous mining loop
- Hunt selection algorithm
- Stats tracking
- Graceful shutdown

**Files**:
- `miner.ts` - Main agent class
- `types.ts` - Agent state types

**State Machine**:
```
IDLE → FETCHING_HUNTS → PICKING_HUNT → RESEARCHING → SOLVING → [CLAIMING] → IDLE
                                                                     ↓
                                                                   ERROR
```

**Hunt Selection Algorithm**:
```typescript
score = reward / max(difficulty, 1)
selected = hunts.sort_by(score, descending).first()
```

This balances:
- High rewards (more attractive)
- Low difficulty (easier to solve)

**Stats Tracking**:
- Total hunts attempted
- Total hunts solved
- Success rate
- Total rewards
- Current streak
- Total errors
- Uptime

### 6. CLI Interface (`src/cli/`)

**Purpose**: User-facing command-line interface

**Key Features**:
- Intuitive commands
- Help documentation
- Graceful shutdown (SIGINT/SIGTERM)
- Pretty output formatting

**Files**:
- `index.ts` - Command definitions
- `commands.ts` - Command implementations

**Library**: `Commander.js` - Feature-rich CLI framework

**Commands**:
- `register` - One-time wallet registration
- `mine` - Start continuous mining
- `status` - Check balances and gas
- `hunts` - List available puzzles
- `link-wallet` - Connect Base wallet
- `claim` - Manual token claim

### 7. Utilities (`src/utils/`)

**Purpose**: Shared utilities

**Files**:
- `logger.ts` - Winston-based logging
- `errors.ts` - Custom error types
- `sleep.ts` - Async delays & backoff

**Logging Levels**:
- `debug` - Detailed operation logs
- `info` - Normal operations
- `warn` - Warnings (non-fatal)
- `error` - Errors (recoverable or fatal)

**Error Hierarchy**:
```
Error
└── BotcoinError
    ├── CryptoError
    ├── ApiError
    │   └── RateLimitError
    ├── ResearchError
    └── ConfigError
```

## 🔄 Data Flow

### Mining Cycle Flow

```
1. START CYCLE
   ├─> Check balance & gas
   └─> Log current status

2. FETCH HUNTS
   ├─> GET /api/hunts
   └─> Parse hunt list

3. SELECT HUNT
   ├─> Calculate scores (reward/difficulty)
   ├─> Sort by score
   └─> Pick top hunt

4. PICK HUNT
   ├─> Create signed request
   ├─> POST /api/hunts/pick
   └─> Validate response

5. RESEARCH & SOLVE
   ├─> Extract clues from poem/description
   ├─> Apply solving strategy (difficulty-based)
   ├─> Calculate confidence
   └─> Generate answer

6. SUBMIT ANSWER
   ├─> Create signed request
   ├─> POST /api/hunts/solve
   └─> Handle response
       ├─> If correct: Update stats, log success
       └─> If wrong: Retry (up to MAX_RETRIES)

7. OPTIONAL: CLAIM
   ├─> Check balance threshold
   ├─> POST /api/claim-onchain (if enabled)
   └─> Log transaction

8. SLEEP
   └─> Wait MINING_INTERVAL before next cycle
```

### Request Signing Flow

```
1. Create Payload
   {
     huntId: "abc123",
     answer: "solution"
   }

2. Stringify
   '{"huntId":"abc123","answer":"solution"}'

3. Sign with Private Key
   signature = sign(privateKey, stringifiedPayload)

4. Encode to Base64
   signatureBase64 = base64(signature)
   publicKeyBase64 = base64(publicKey)

5. Create Signed Request
   {
     huntId: "abc123",
     answer: "solution",
     signature: signatureBase64,
     publicKey: publicKeyBase64
   }

6. Send to API
   POST /api/hunts/solve
```

## 🛡️ Error Handling Strategy

### Retry Logic

**Rate Limits** (429):
- Parse `Retry-After` header
- Wait specified duration
- Retry request

**Network Errors**:
- Exponential backoff: `delay = min(1000 * 2^attempt, 30000) + random(1000)`
- Max retries: 3 (configurable)
- Log each attempt

**API Errors**:
- 4xx: Log error, don't retry (client issue)
- 5xx: Log error, retry with backoff (server issue)

**Cryptographic Errors**:
- Fail fast (no retry)
- Log full error
- Exit process

### Graceful Shutdown

```typescript
process.on('SIGINT', () => {
  logger.info('Shutting down...');
  miner.stop();
  // Print final stats
  console.log(JSON.stringify(miner.getStats(), null, 2));
  process.exit(0);
});
```

## 📊 Performance Considerations

### Memory Usage
- **Light**: ~50-100MB typical
- No large data structures
- Streaming API responses

### CPU Usage
- **Minimal**: < 1% idle
- **Peaks**: During crypto operations (signing)

### Network Usage
- **Bandwidth**: < 1MB per hour (mostly JSON)
- **Requests**: ~60-120 per hour (depending on interval)

### Optimization Opportunities

1. **Hunt Caching**: Cache hunt details to reduce API calls
2. **Answer Database**: Store successful answers for pattern recognition
3. **Parallel Research**: Research multiple clues concurrently
4. **Request Batching**: Batch multiple operations in single request
5. **Connection Pooling**: Reuse HTTP connections

## 🔐 Security Architecture

### Key Storage
- Private keys in `.env` (not in code)
- `.env` in `.gitignore`
- Base64 encoding (not encryption)

**⚠️ For Production**:
- Use hardware security modules (HSM)
- Encrypt keys at rest
- Use key management services (AWS KMS, etc.)

### Signature Security
- Ed25519: 128-bit security level
- Deterministic signatures (no nonce issues)
- Resistant to timing attacks

### API Security
- All write operations require signature
- Public key in request (server verifies)
- Replay attack mitigation (server-side)

## 🧪 Testing Strategy

### Unit Tests (Planned)
```typescript
// Crypto
test('generateKeypair creates valid keys')
test('signMessage produces verifiable signature')

// Research
test('solveEasy handles math expressions')
test('extractClues finds patterns')

// API Client
test('signPayload creates valid signature')
test('handleError manages rate limits')
```

### Integration Tests (Planned)
```typescript
test('register workflow')
test('hunt solving workflow')
test('claim workflow')
```

### Manual Testing
- `npm run test-miner` - Component tests
- `npm run generate-keys` - Crypto test
- `npm run miner -- --help` - CLI test

## 🚀 Deployment Options

### Local Development
```bash
npm run mine
```

### Background Process (Linux)
```bash
# Using systemd
sudo systemctl start botcoin-miner

# Using PM2
pm2 start "npm run mine" --name botcoin-miner
```

### Docker (Example)
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
CMD ["npm", "run", "mine"]
```

### Cloud Deployment
- **AWS Lambda**: Scheduled miner (cron)
- **Heroku**: 24/7 dyno
- **DigitalOcean**: Droplet with systemd
- **Railway/Render**: Container deployment

## 📈 Scaling Considerations

### Horizontal Scaling
- Run multiple instances with different wallets
- Coordinate via shared database
- Load balance hunt selection

### Vertical Scaling
- Increase mining interval for more throughput
- Parallel hunt solving
- GPU acceleration for crypto (optional)

## 🔮 Future Enhancements

### Phase 1: Better Solving
- [ ] Web search integration
- [ ] OpenAI/Claude integration
- [ ] Answer caching database
- [ ] Machine learning model

### Phase 2: Monitoring
- [ ] Web dashboard
- [ ] Prometheus metrics
- [ ] Alert notifications (Slack/Discord)
- [ ] Performance analytics

### Phase 3: Multi-Account
- [ ] Account manager
- [ ] Automatic key rotation
- [ ] Profit optimization

### Phase 4: Advanced Features
- [ ] Hunt difficulty prediction
- [ ] Dynamic strategy selection
- [ ] Collaborative solving (multiple agents)
- [ ] Adversarial hunt generation

## 📚 Further Reading

- [Ed25519 Signature Scheme](https://ed25519.cr.yp.to/)
- [TweetNaCl Documentation](https://github.com/dchest/tweetnacl-js)
- [Commander.js Guide](https://github.com/tj/commander.js)
- [Winston Logging](https://github.com/winstonjs/winston)
- [Zod Validation](https://github.com/colinhacks/zod)

---

**Built with ❤️ for the Botcoin community**
