/**
 * Type definitions for Botcoin API
 */

// Registration challenge
export interface Challenge {
  challenge: string; // Math expression like "5 + 3"
}

export interface RegisterRequest {
  publicKey: string;
  solution: string;
  signature: string;
}

export interface RegisterResponse {
  success: boolean;
  message?: string;
  publicKey?: string;
}

// Hunt types
export interface Hunt {
  id: string;
  difficulty: number;
  reward: number;
  poem?: string;
  description?: string;
  hints?: string[];
  status?: 'available' | 'active' | 'completed' | 'failed';
}

export interface HuntsResponse {
  hunts: Hunt[];
}

export interface PickHuntRequest {
  huntId: string;
  publicKey: string;
  signature: string;
}

export interface PickHuntResponse {
  success: boolean;
  message?: string;
  hunt?: Hunt;
}

export interface SolveHuntRequest {
  huntId: string;
  answer: string;
  publicKey: string;
  signature: string;
}

export interface SolveHuntResponse {
  success: boolean;
  correct?: boolean;
  message?: string;
  reward?: number;
  attemptsRemaining?: number;
}

// Wallet operations
export interface LinkWalletRequest {
  baseAddress: string;
  publicKey: string;
  signature: string;
}

export interface LinkWalletResponse {
  success: boolean;
  message?: string;
}

export interface ClaimOnchainRequest {
  publicKey: string;
  signature: string;
}

export interface ClaimOnchainResponse {
  success: boolean;
  message?: string;
  txHash?: string;
  amount?: number;
}

// Balance and gas
export interface BalanceResponse {
  publicKey: string;
  balance: number;
  shares?: number;
  pendingRewards?: number;
}

export interface GasResponse {
  publicKey: string;
  gasBalance: number;
  gasRequired: number;
  canOperate: boolean;
}

// Signed request wrapper
export interface SignedRequest {
  publicKey: string;
  signature: string;
  [key: string]: any;
}
