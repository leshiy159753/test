import { Command } from 'commander';
import { loadConfig, validateKeysPresent } from '../config';
import { BotcoinMiner } from '../agent/miner';
import { BotcoinApiClient } from '../api/client';
import { loadKeypair, uint8ArrayToBase64 } from '../crypto/keys';
import { logger } from '../utils/logger';

/**
 * Register command
 */
export async function registerCommand(): Promise<void> {
  try {
    const config = loadConfig();
    validateKeysPresent(config);

    const miner = new BotcoinMiner(config);
    await miner.register();
  } catch (error) {
    logger.error('Registration failed', error);
    process.exit(1);
  }
}

/**
 * Start mining command
 */
export async function mineCommand(): Promise<void> {
  try {
    const config = loadConfig();
    validateKeysPresent(config);

    const miner = new BotcoinMiner(config);
    
    // Handle graceful shutdown
    process.on('SIGINT', () => {
      logger.info('\nReceived SIGINT, shutting down gracefully...');
      miner.stop();
      setTimeout(() => {
        logger.info('Stats:');
        console.log(JSON.stringify(miner.getStats(), null, 2));
        process.exit(0);
      }, 1000);
    });

    process.on('SIGTERM', () => {
      logger.info('\nReceived SIGTERM, shutting down gracefully...');
      miner.stop();
      setTimeout(() => process.exit(0), 1000);
    });

    await miner.start();
  } catch (error) {
    logger.error('Mining failed', error);
    process.exit(1);
  }
}

/**
 * Status command - check balance and gas
 */
export async function statusCommand(): Promise<void> {
  try {
    const config = loadConfig();
    validateKeysPresent(config);

    const keypair = loadKeypair(config.privateKey!, config.publicKey!);
    const client = new BotcoinApiClient(config.apiUrl);
    client.setKeypair(keypair);

    logger.info('Fetching status...');
    
    const [balance, gas] = await Promise.all([
      client.getBalance(),
      client.getGasBalance(),
    ]);

    console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    console.log('📊 Wallet Status');
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    console.log(`Public Key: ${uint8ArrayToBase64(keypair.publicKey)}`);
    console.log(`\nBalance: ${balance.balance} shares`);
    if (balance.pendingRewards) {
      console.log(`Pending Rewards: ${balance.pendingRewards}`);
    }
    console.log(`\nGas Balance: ${gas.gasBalance}`);
    console.log(`Gas Required: ${gas.gasRequired}`);
    console.log(`Can Operate: ${gas.canOperate ? '✅ Yes' : '❌ No'}`);
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');
  } catch (error) {
    logger.error('Failed to fetch status', error);
    process.exit(1);
  }
}

/**
 * List hunts command
 */
export async function huntsCommand(): Promise<void> {
  try {
    const config = loadConfig();
    validateKeysPresent(config);

    const keypair = loadKeypair(config.privateKey!, config.publicKey!);
    const client = new BotcoinApiClient(config.apiUrl);
    client.setKeypair(keypair);

    logger.info('Fetching available hunts...');
    const hunts = await client.getHunts();

    if (hunts.length === 0) {
      console.log('\n📭 No hunts available\n');
      return;
    }

    console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    console.log(`🎯 Available Hunts (${hunts.length})`);
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    
    hunts.forEach((hunt, i) => {
      console.log(`\n${i + 1}. Hunt ID: ${hunt.id}`);
      console.log(`   Difficulty: ${'⭐'.repeat(hunt.difficulty)} (${hunt.difficulty}/10)`);
      console.log(`   Reward: ${hunt.reward} shares`);
      if (hunt.poem) {
        console.log(`   Poem: ${hunt.poem.substring(0, 100)}...`);
      }
      if (hunt.description) {
        console.log(`   Description: ${hunt.description}`);
      }
    });
    
    console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');
  } catch (error) {
    logger.error('Failed to fetch hunts', error);
    process.exit(1);
  }
}

/**
 * Link wallet command
 */
export async function linkWalletCommand(address: string): Promise<void> {
  try {
    const config = loadConfig();
    validateKeysPresent(config);

    const miner = new BotcoinMiner(config);
    await miner.linkWallet(address);
  } catch (error) {
    logger.error('Failed to link wallet', error);
    process.exit(1);
  }
}

/**
 * Claim on-chain command
 */
export async function claimCommand(): Promise<void> {
  try {
    const config = loadConfig();
    validateKeysPresent(config);

    const keypair = loadKeypair(config.privateKey!, config.publicKey!);
    const client = new BotcoinApiClient(config.apiUrl);
    client.setKeypair(keypair);

    logger.info('Claiming tokens on-chain...');
    const response = await client.claimOnchain();

    if (response.success) {
      console.log('\n✅ Successfully claimed tokens!');
      console.log(`Amount: ${response.amount}`);
      console.log(`TX Hash: ${response.txHash}\n`);
    } else {
      console.log(`\n❌ Claim failed: ${response.message}\n`);
    }
  } catch (error) {
    logger.error('Failed to claim tokens', error);
    process.exit(1);
  }
}
