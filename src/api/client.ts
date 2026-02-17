import axios, { AxiosInstance, AxiosError } from 'axios';
import { ApiError, RateLimitError } from '../utils/errors';
import { createLogger } from '../utils/logger';
import { signMessage, uint8ArrayToBase64, Keypair } from '../crypto/keys';
import * as Types from './types';

const logger = createLogger('API');

/**
 * Botcoin API client with automatic request signing
 */
export class BotcoinApiClient {
  private client: AxiosInstance;
  private keypair: Keypair | null = null;

  constructor(private baseUrl: string) {
    this.client = axios.create({
      baseURL: baseUrl,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        return this.handleError(error);
      }
    );
  }

  /**
   * Set keypair for signing requests
   */
  setKeypair(keypair: Keypair): void {
    this.keypair = keypair;
    logger.info('Keypair configured for API client');
  }

  /**
   * Sign a payload and return signed request
   */
  private signPayload(payload: any): Types.SignedRequest {
    if (!this.keypair) {
      throw new ApiError('Keypair not set. Call setKeypair() first.');
    }

    const publicKeyBase64 = uint8ArrayToBase64(this.keypair.publicKey);
    
    // Create message to sign (JSON stringified payload without signature)
    const message = JSON.stringify(payload);
    const signature = signMessage(message, this.keypair.secretKey);
    const signatureBase64 = uint8ArrayToBase64(signature);

    return {
      ...payload,
      publicKey: publicKeyBase64,
      signature: signatureBase64,
    };
  }

  /**
   * Handle API errors
   */
  private handleError(error: AxiosError): never {
    if (error.response) {
      const status = error.response.status;
      const data = error.response.data as any;

      // Rate limiting
      if (status === 429) {
        const retryAfter = error.response.headers['retry-after'];
        const retrySeconds = retryAfter ? parseInt(retryAfter) : 60;
        logger.warn(`Rate limited. Retry after ${retrySeconds}s`);
        throw new RateLimitError(data?.message || 'Rate limit exceeded', retrySeconds);
      }

      // Client errors
      if (status >= 400 && status < 500) {
        logger.error(`Client error ${status}: ${data?.message || error.message}`);
        throw new ApiError(data?.message || `Client error: ${status}`, status, data);
      }

      // Server errors
      if (status >= 500) {
        logger.error(`Server error ${status}: ${data?.message || error.message}`);
        throw new ApiError(data?.message || `Server error: ${status}`, status, data);
      }
    }

    // Network errors
    if (error.code === 'ECONNABORTED') {
      logger.error('Request timeout');
      throw new ApiError('Request timeout', undefined, error);
    }

    logger.error(`Network error: ${error.message}`);
    throw new ApiError(`Network error: ${error.message}`, undefined, error);
  }

  /**
   * Get registration challenge
   */
  async getChallenge(): Promise<Types.Challenge> {
    logger.debug('Fetching registration challenge');
    const response = await this.client.get<Types.Challenge>('/api/register/challenge');
    return response.data;
  }

  /**
   * Register new wallet
   */
  async register(solution: string): Promise<Types.RegisterResponse> {
    if (!this.keypair) {
      throw new ApiError('Keypair not set');
    }

    const payload = {
      publicKey: uint8ArrayToBase64(this.keypair.publicKey),
      solution,
    };

    const signedRequest = this.signPayload(payload);
    logger.info('Registering wallet...');
    
    const response = await this.client.post<Types.RegisterResponse>('/api/register', signedRequest);
    logger.info(`Registration response: ${response.data.message}`);
    return response.data;
  }

  /**
   * Get available hunts
   */
  async getHunts(): Promise<Types.Hunt[]> {
    logger.debug('Fetching available hunts');
    const response = await this.client.get<Types.HuntsResponse>('/api/hunts');
    return response.data.hunts || [];
  }

  /**
   * Pick a hunt
   */
  async pickHunt(huntId: string): Promise<Types.PickHuntResponse> {
    const payload = { huntId };
    const signedRequest = this.signPayload(payload);
    
    logger.info(`Picking hunt: ${huntId}`);
    const response = await this.client.post<Types.PickHuntResponse>('/api/hunts/pick', signedRequest);
    return response.data;
  }

  /**
   * Submit hunt answer
   */
  async solveHunt(huntId: string, answer: string): Promise<Types.SolveHuntResponse> {
    const payload = { huntId, answer };
    const signedRequest = this.signPayload(payload);
    
    logger.info(`Submitting answer for hunt: ${huntId}`);
    const response = await this.client.post<Types.SolveHuntResponse>('/api/hunts/solve', signedRequest);
    
    if (response.data.correct) {
      logger.info(`✓ Correct answer! Reward: ${response.data.reward}`);
    } else {
      logger.warn(`✗ Wrong answer. Attempts remaining: ${response.data.attemptsRemaining}`);
    }
    
    return response.data;
  }

  /**
   * Link Base wallet address
   */
  async linkWallet(baseAddress: string): Promise<Types.LinkWalletResponse> {
    const payload = { baseAddress };
    const signedRequest = this.signPayload(payload);
    
    logger.info(`Linking Base wallet: ${baseAddress}`);
    const response = await this.client.post<Types.LinkWalletResponse>('/api/link-wallet', signedRequest);
    return response.data;
  }

  /**
   * Claim tokens on-chain
   */
  async claimOnchain(): Promise<Types.ClaimOnchainResponse> {
    const payload = {};
    const signedRequest = this.signPayload(payload);
    
    logger.info('Claiming tokens on-chain...');
    const response = await this.client.post<Types.ClaimOnchainResponse>('/api/claim-onchain', signedRequest);
    
    if (response.data.success) {
      logger.info(`✓ Claimed ${response.data.amount} tokens. TX: ${response.data.txHash}`);
    }
    
    return response.data;
  }

  /**
   * Check gas balance
   */
  async getGasBalance(): Promise<Types.GasResponse> {
    if (!this.keypair) {
      throw new ApiError('Keypair not set');
    }

    const publicKey = uint8ArrayToBase64(this.keypair.publicKey);
    logger.debug('Checking gas balance');
    
    const response = await this.client.get<Types.GasResponse>(`/api/gas?publicKey=${publicKey}`);
    return response.data;
  }

  /**
   * Get balance and shares
   */
  async getBalance(): Promise<Types.BalanceResponse> {
    if (!this.keypair) {
      throw new ApiError('Keypair not set');
    }

    const publicKey = uint8ArrayToBase64(this.keypair.publicKey);
    logger.debug('Fetching balance');
    
    const response = await this.client.get<Types.BalanceResponse>(`/api/balance/${publicKey}`);
    return response.data;
  }
}
