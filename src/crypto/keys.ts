import nacl from 'tweetnacl';
import { CryptoError } from '../utils/errors';
import { createLogger } from '../utils/logger';

const logger = createLogger('Crypto');

/**
 * Ed25519 keypair wrapper
 */
export interface Keypair {
  publicKey: Uint8Array;
  secretKey: Uint8Array;
}

/**
 * Generate a new Ed25519 keypair
 */
export function generateKeypair(): Keypair {
  try {
    const keypair = nacl.sign.keyPair();
    logger.info('Generated new Ed25519 keypair');
    return keypair;
  } catch (error) {
    throw new CryptoError(`Failed to generate keypair: ${error}`);
  }
}

/**
 * Generate keypair from seed (32 bytes)
 */
export function keypairFromSeed(seed: Uint8Array): Keypair {
  if (seed.length !== 32) {
    throw new CryptoError('Seed must be exactly 32 bytes');
  }
  
  try {
    const keypair = nacl.sign.keyPair.fromSeed(seed);
    logger.debug('Generated keypair from seed');
    return keypair;
  } catch (error) {
    throw new CryptoError(`Failed to generate keypair from seed: ${error}`);
  }
}

/**
 * Load keypair from base64-encoded strings
 */
export function loadKeypair(privateKeyBase64: string, publicKeyBase64: string): Keypair {
  try {
    const secretKey = base64ToUint8Array(privateKeyBase64);
    const publicKey = base64ToUint8Array(publicKeyBase64);
    
    // Validate key sizes
    if (secretKey.length !== 64) {
      throw new CryptoError(`Invalid private key length: expected 64 bytes, got ${secretKey.length}`);
    }
    if (publicKey.length !== 32) {
      throw new CryptoError(`Invalid public key length: expected 32 bytes, got ${publicKey.length}`);
    }
    
    logger.info('Loaded keypair from base64 strings');
    return { secretKey, publicKey };
  } catch (error) {
    if (error instanceof CryptoError) throw error;
    throw new CryptoError(`Failed to load keypair: ${error}`);
  }
}

/**
 * Sign a message with the private key
 */
export function signMessage(message: string | Uint8Array, secretKey: Uint8Array): Uint8Array {
  try {
    const messageBytes = typeof message === 'string' ? new TextEncoder().encode(message) : message;
    const signature = nacl.sign.detached(messageBytes, secretKey);
    logger.debug(`Signed message of ${messageBytes.length} bytes`);
    return signature;
  } catch (error) {
    throw new CryptoError(`Failed to sign message: ${error}`);
  }
}

/**
 * Verify a signature
 */
export function verifySignature(message: string | Uint8Array, signature: Uint8Array, publicKey: Uint8Array): boolean {
  try {
    const messageBytes = typeof message === 'string' ? new TextEncoder().encode(message) : message;
    return nacl.sign.detached.verify(messageBytes, signature, publicKey);
  } catch (error) {
    throw new CryptoError(`Failed to verify signature: ${error}`);
  }
}

/**
 * Convert Uint8Array to base64
 */
export function uint8ArrayToBase64(bytes: Uint8Array): string {
  return Buffer.from(bytes).toString('base64');
}

/**
 * Convert base64 to Uint8Array
 */
export function base64ToUint8Array(base64: string): Uint8Array {
  return new Uint8Array(Buffer.from(base64, 'base64'));
}

/**
 * Export keypair to base64 strings for storage
 */
export function exportKeypair(keypair: Keypair): { privateKey: string; publicKey: string } {
  return {
    privateKey: uint8ArrayToBase64(keypair.secretKey),
    publicKey: uint8ArrayToBase64(keypair.publicKey),
  };
}

/**
 * Generate random hex string (for testing)
 */
export function randomHex(length: number): string {
  const bytes = nacl.randomBytes(length);
  return Buffer.from(bytes).toString('hex');
}
