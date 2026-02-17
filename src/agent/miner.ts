import { BotcoinApiClient } from '../api/client';
import { ResearchEngine } from '../research/engine';
import { loadKeypair } from '../crypto/keys';
import { createLogger } from '../utils/logger';
import { sleep, exponentialBackoff } from '../utils/sleep';
import { RateLimitError, ApiError } from '../utils/errors';
import { AgentState, AgentStats, MinerConfig } from './types';
import { Hunt } from '../api/types';
import { Config } from '../config';

const logger = createLogger('Miner');

/**
 * Main Botcoin miner agent
 */
export class BotcoinMiner {
  private apiClient: BotcoinApiClient;
  private researchEngine: ResearchEngine;
  private state: AgentState = AgentState.IDLE;
  private stats: AgentStats;
  private config: MinerConfig;
  private isRunning: boolean = false;

  constructor(appConfig: Config) {
    this.apiClient = new BotcoinApiClient(appConfig.apiUrl);
    this.researchEngine = new ResearchEngine();
    
    this.config = {
      miningInterval: appConfig.miningInterval,
      maxRetries: appConfig.maxRetries,
      autoClaimOnchain: appConfig.autoClaimOnchain,
      minConfidenceThreshold: 0.6,
    };

    this.stats = {
      totalHuntsAttempted: 0,
      totalHuntsSolved: 0,
      totalRewards: 0,
      totalErrors: 0,
      currentStreak: 0,
      startTime: new Date(),
      uptime: 0,
    };

    // Load keypair if available
    if (appConfig.privateKey && appConfig.publicKey) {
      const keypair = loadKeypair(appConfig.privateKey, appConfig.publicKey);
      this.apiClient.setKeypair(keypair);
      logger.info('Miner initialized with keypair');
    } else {
      logger.warn('Miner initialized without keypair - some operations will fail');
    }
  }

  /**
   * Start mining loop
   */
  async start(): Promise<void> {
    if (this.isRunning) {
      logger.warn('Miner is already running');
      return;
    }

    this.isRunning = true;
    logger.info('🚀 Starting Botcoin miner...');
    logger.info(`Mining interval: ${this.config.miningInterval}ms`);

    while (this.isRunning) {
      try {
        await this.miningCycle();
        
        // Update uptime
        this.stats.uptime = Date.now() - this.stats.startTime.getTime();
        
        // Wait before next cycle
        logger.debug(`Waiting ${this.config.miningInterval}ms before next cycle`);
        await sleep(this.config.miningInterval);
      } catch (error) {
        this.stats.totalErrors++;
        
        if (error instanceof RateLimitError) {
          const waitTime = (error.retryAfter || 60) * 1000;
          logger.warn(`Rate limited. Waiting ${waitTime}ms`);
          await sleep(waitTime);
        } else {
          logger.error('Error in mining cycle', error);
          // Exponential backoff on errors
          const backoff = exponentialBackoff(Math.min(this.stats.totalErrors, 5));
          logger.debug(`Backing off for ${backoff}ms`);
          await sleep(backoff);
        }
      }
    }

    logger.info('Miner stopped');
  }

  /**
   * Stop mining
   */
  stop(): void {
    logger.info('Stopping miner...');
    this.isRunning = false;
  }

  /**
   * Single mining cycle
   */
  private async miningCycle(): Promise<void> {
    // 1. Check balance and gas
    await this.checkStatus();

    // 2. Get available hunts
    this.setState(AgentState.FETCHING_HUNTS);
    const hunts = await this.apiClient.getHunts();
    
    if (hunts.length === 0) {
      logger.info('No hunts available');
      return;
    }

    logger.info(`Found ${hunts.length} available hunts`);

    // 3. Select best hunt
    const hunt = this.selectHunt(hunts);
    logger.info(`Selected hunt ${hunt.id} (difficulty: ${hunt.difficulty}, reward: ${hunt.reward})`);

    // 4. Pick the hunt
    this.setState(AgentState.PICKING_HUNT);
    const pickResponse = await this.apiClient.pickHunt(hunt.id);
    
    if (!pickResponse.success) {
      logger.warn(`Failed to pick hunt: ${pickResponse.message}`);
      return;
    }

    // 5. Research and solve
    await this.solveHunt(hunt);

    // 6. Auto-claim if enabled and sufficient balance
    if (this.config.autoClaimOnchain) {
      await this.attemptClaim();
    }
  }

  /**
   * Solve a hunt with retries
   */
  private async solveHunt(hunt: Hunt): Promise<void> {
    this.stats.totalHuntsAttempted++;

    for (let attempt = 0; attempt < this.config.maxRetries; attempt++) {
      try {
        logger.info(`Attempt ${attempt + 1}/${this.config.maxRetries} for hunt ${hunt.id}`);

        // Research the answer
        this.setState(AgentState.RESEARCHING);
        const researchResult = await this.researchEngine.solve({
          huntId: hunt.id,
          difficulty: hunt.difficulty,
          poem: hunt.poem,
          description: hunt.description,
          hints: hunt.hints,
        });

        logger.info(`Research result: "${researchResult.answer}" (confidence: ${researchResult.confidence})`);
        logger.debug(`Reasoning: ${researchResult.reasoning}`);

        // Check confidence threshold
        if (!this.researchEngine.shouldSubmit(researchResult, this.config.minConfidenceThreshold)) {
          logger.warn(`Low confidence (${researchResult.confidence}), but submitting anyway`);
        }

        // Submit answer
        this.setState(AgentState.SOLVING);
        const solveResponse = await this.apiClient.solveHunt(hunt.id, researchResult.answer);

        if (solveResponse.correct) {
          this.stats.totalHuntsSolved++;
          this.stats.totalRewards += solveResponse.reward || 0;
          this.stats.currentStreak++;
          logger.info(`✅ Hunt solved! Reward: ${solveResponse.reward}. Streak: ${this.stats.currentStreak}`);
          this.printStats();
          return;
        }

        logger.warn(`❌ Wrong answer. Attempts remaining: ${solveResponse.attemptsRemaining}`);
        
        if (solveResponse.attemptsRemaining === 0) {
          this.stats.currentStreak = 0;
          logger.error('No attempts remaining for this hunt');
          return;
        }

        // Wait before next attempt
        await sleep(2000);
      } catch (error) {
        logger.error(`Error solving hunt (attempt ${attempt + 1})`, error);
        
        if (attempt === this.config.maxRetries - 1) {
          this.stats.currentStreak = 0;
          throw error;
        }
        
        // Backoff between attempts
        await sleep(exponentialBackoff(attempt));
      }
    }

    this.stats.currentStreak = 0;
    logger.error(`Failed to solve hunt after ${this.config.maxRetries} attempts`);
  }

  /**
   * Select best hunt from available options
   */
  private selectHunt(hunts: Hunt[]): Hunt {
    // Strategy: Balance difficulty and reward
    // Score = reward / difficulty
    const scored = hunts.map(hunt => ({
      hunt,
      score: hunt.reward / Math.max(hunt.difficulty, 1),
    }));

    scored.sort((a, b) => b.score - a.score);
    
    logger.debug(`Hunt scores: ${scored.slice(0, 3).map(s => `${s.hunt.id}:${s.score.toFixed(2)}`).join(', ')}`);
    
    return scored[0].hunt;
  }

  /**
   * Check balance and gas status
   */
  private async checkStatus(): Promise<void> {
    try {
      const [balance, gas] = await Promise.all([
        this.apiClient.getBalance(),
        this.apiClient.getGasBalance(),
      ]);

      logger.debug(`Balance: ${balance.balance} shares, Gas: ${gas.gasBalance}`);

      if (!gas.canOperate) {
        logger.warn(`⚠️  Low gas balance: ${gas.gasBalance} (required: ${gas.gasRequired})`);
      }
    } catch (error) {
      logger.error('Failed to check status', error);
    }
  }

  /**
   * Attempt to claim tokens on-chain
   */
  private async attemptClaim(): Promise<void> {
    try {
      const balance = await this.apiClient.getBalance();
      
      // Only claim if we have sufficient balance (e.g., > 100 shares)
      const MIN_CLAIM_THRESHOLD = 100;
      if (balance.balance < MIN_CLAIM_THRESHOLD) {
        logger.debug(`Balance ${balance.balance} below claim threshold ${MIN_CLAIM_THRESHOLD}`);
        return;
      }

      this.setState(AgentState.CLAIMING);
      logger.info('Attempting to claim tokens on-chain...');
      
      const claimResponse = await this.apiClient.claimOnchain();
      
      if (claimResponse.success) {
        logger.info(`✅ Successfully claimed ${claimResponse.amount} tokens!`);
        logger.info(`TX Hash: ${claimResponse.txHash}`);
      }
    } catch (error) {
      logger.error('Failed to claim tokens', error);
    }
  }

  /**
   * Set agent state
   */
  private setState(state: AgentState): void {
    this.state = state;
    logger.debug(`State: ${state}`);
  }

  /**
   * Get current stats
   */
  getStats(): AgentStats {
    return { ...this.stats };
  }

  /**
   * Print stats summary
   */
  private printStats(): void {
    const successRate = this.stats.totalHuntsAttempted > 0
      ? ((this.stats.totalHuntsSolved / this.stats.totalHuntsAttempted) * 100).toFixed(1)
      : '0.0';

    logger.info('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    logger.info(`📊 Stats:`);
    logger.info(`   Hunts: ${this.stats.totalHuntsSolved}/${this.stats.totalHuntsAttempted} (${successRate}%)`);
    logger.info(`   Rewards: ${this.stats.totalRewards}`);
    logger.info(`   Streak: ${this.stats.currentStreak}`);
    logger.info(`   Errors: ${this.stats.totalErrors}`);
    logger.info('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  }

  /**
   * Register wallet (one-time operation)
   */
  async register(): Promise<void> {
    logger.info('Starting registration...');
    this.setState(AgentState.REGISTERING);

    // Get challenge
    const challenge = await this.apiClient.getChallenge();
    logger.info(`Registration challenge: ${challenge.challenge}`);

    // Solve challenge (simple math)
    const solution = eval(challenge.challenge).toString();
    logger.debug(`Challenge solution: ${solution}`);

    // Submit registration
    const response = await this.apiClient.register(solution);
    
    if (response.success) {
      logger.info(`✅ Registration successful! Public key: ${response.publicKey}`);
    } else {
      logger.error(`❌ Registration failed: ${response.message}`);
      throw new ApiError('Registration failed');
    }

    this.setState(AgentState.IDLE);
  }

  /**
   * Link Base wallet
   */
  async linkWallet(baseAddress: string): Promise<void> {
    logger.info(`Linking Base wallet: ${baseAddress}`);
    const response = await this.apiClient.linkWallet(baseAddress);
    
    if (response.success) {
      logger.info('✅ Wallet linked successfully');
    } else {
      logger.error(`❌ Failed to link wallet: ${response.message}`);
    }
  }
}
