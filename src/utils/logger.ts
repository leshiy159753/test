import winston from 'winston';

/**
 * Centralized logging utility using Winston
 */
export const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp({ format: 'YYYY-MM-DD HH:mm:ss' }),
    winston.format.errors({ stack: true }),
    winston.format.printf(({ timestamp, level, message, stack }) => {
      return `${timestamp} [${level.toUpperCase()}]: ${message}${stack ? '\n' + stack : ''}`;
    })
  ),
  transports: [
    new winston.transports.Console({
      format: winston.format.combine(
        winston.format.colorize(),
        winston.format.printf(({ timestamp, level, message, stack }) => {
          return `${timestamp} [${level}]: ${message}${stack ? '\n' + stack : ''}`;
        })
      ),
    }),
  ],
});

/**
 * Helper to create module-specific loggers
 */
export function createLogger(module: string) {
  return {
    debug: (message: string, meta?: any) => logger.debug(`[${module}] ${message}`, meta),
    info: (message: string, meta?: any) => logger.info(`[${module}] ${message}`, meta),
    warn: (message: string, meta?: any) => logger.warn(`[${module}] ${message}`, meta),
    error: (message: string, error?: any) => {
      if (error instanceof Error) {
        logger.error(`[${module}] ${message}`, { error: error.message, stack: error.stack });
      } else {
        logger.error(`[${module}] ${message}`, error);
      }
    },
  };
}
