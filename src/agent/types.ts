/**
 * Agent state types
 */

export enum AgentState {
  IDLE = 'idle',
  REGISTERING = 'registering',
  FETCHING_HUNTS = 'fetching_hunts',
  PICKING_HUNT = 'picking_hunt',
  RESEARCHING = 'researching',
  SOLVING = 'solving',
  CLAIMING = 'claiming',
  ERROR = 'error',
}

export interface AgentStats {
  totalHuntsAttempted: number;
  totalHuntsSolved: number;
  totalRewards: number;
  totalErrors: number;
  currentStreak: number;
  startTime: Date;
  uptime: number;
}

export interface MinerConfig {
  miningInterval: number;
  maxRetries: number;
  autoClaimOnchain: boolean;
  minConfidenceThreshold: number;
}
