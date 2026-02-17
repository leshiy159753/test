/**
 * Custom error types for the Botcoin miner
 */

export class BotcoinError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'BotcoinError';
  }
}

export class CryptoError extends BotcoinError {
  constructor(message: string) {
    super(message);
    this.name = 'CryptoError';
  }
}

export class ApiError extends BotcoinError {
  public statusCode?: number;
  public response?: any;

  constructor(message: string, statusCode?: number, response?: any) {
    super(message);
    this.name = 'ApiError';
    this.statusCode = statusCode;
    this.response = response;
  }
}

export class RateLimitError extends ApiError {
  public retryAfter?: number;

  constructor(message: string, retryAfter?: number) {
    super(message, 429);
    this.name = 'RateLimitError';
    this.retryAfter = retryAfter;
  }
}

export class ResearchError extends BotcoinError {
  constructor(message: string) {
    super(message);
    this.name = 'ResearchError';
  }
}

export class ConfigError extends BotcoinError {
  constructor(message: string) {
    super(message);
    this.name = 'ConfigError';
  }
}
