/**
 * Async sleep utility
 */
export function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Exponential backoff with jitter
 */
export function exponentialBackoff(attempt: number, baseDelay: number = 1000, maxDelay: number = 30000): number {
  const delay = Math.min(baseDelay * Math.pow(2, attempt), maxDelay);
  const jitter = Math.random() * 1000;
  return delay + jitter;
}
