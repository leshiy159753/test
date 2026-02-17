import { z } from 'zod';
import { ConfigError } from '../utils/errors';
import dotenv from 'dotenv';

// Load environment variables
dotenv.config();

/**
 * Configuration schema using Zod for validation
 */
const configSchema = z.object({
  // Botcoin API configuration
  apiUrl: z.string().url().default('https://botfarmer.ai'),
  
  // Ed25519 keys (base64 encoded)
  privateKey: z.string().optional(),
  publicKey: z.string().optional(),
  
  // Base blockchain wallet address
  baseWalletAddress: z.string().optional(),
  
  // Agent configuration
  miningInterval: z.number().min(1000).default(60000), // 1 minute
  maxRetries: z.number().min(1).max(10).default(3),
  
  // Logging
  logLevel: z.enum(['debug', 'info', 'warn', 'error']).default('info'),
  
  // Research configuration (if using AI for puzzle solving)
  openaiApiKey: z.string().optional(),
  
  // Feature flags
  autoRegister: z.boolean().default(false),
  autoClaimOnchain: z.boolean().default(false),
});

export type Config = z.infer<typeof configSchema>;

/**
 * Load and validate configuration from environment variables
 */
export function loadConfig(): Config {
  try {
    const rawConfig = {
      apiUrl: process.env.BOTCOIN_API_URL || 'https://botfarmer.ai',
      privateKey: process.env.BOTCOIN_PRIVATE_KEY,
      publicKey: process.env.BOTCOIN_PUBLIC_KEY,
      baseWalletAddress: process.env.BASE_WALLET_ADDRESS,
      miningInterval: process.env.MINING_INTERVAL ? parseInt(process.env.MINING_INTERVAL) : 60000,
      maxRetries: process.env.MAX_RETRIES ? parseInt(process.env.MAX_RETRIES) : 3,
      logLevel: process.env.LOG_LEVEL || 'info',
      openaiApiKey: process.env.OPENAI_API_KEY,
      autoRegister: process.env.AUTO_REGISTER === 'true',
      autoClaimOnchain: process.env.AUTO_CLAIM_ONCHAIN === 'true',
    };

    return configSchema.parse(rawConfig);
  } catch (error) {
    if (error instanceof z.ZodError) {
      const messages = error.issues.map((issue) => `${issue.path.join('.')}: ${issue.message}`).join(', ');
      throw new ConfigError(`Configuration validation failed: ${messages}`);
    }
    throw error;
  }
}

/**
 * Validate that required keys are present for operations
 */
export function validateKeysPresent(config: Config): void {
  if (!config.privateKey || !config.publicKey) {
    throw new ConfigError('BOTCOIN_PRIVATE_KEY and BOTCOIN_PUBLIC_KEY must be set. Run "npm run generate-keys" to create new keys.');
  }
}
