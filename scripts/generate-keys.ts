#!/usr/bin/env node

import { generateKeypair, exportKeypair } from '../src/crypto/keys';

/**
 * Generate new Ed25519 keypair for Botcoin
 */
function main() {
  console.log('🔐 Generating new Ed25519 keypair...\n');

  const keypair = generateKeypair();
  const exported = exportKeypair(keypair);

  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log('✅ Keypair generated successfully!');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log('\n⚠️  IMPORTANT: Keep your private key secure! Never share it.\n');
  console.log('Add these to your .env file:\n');
  console.log(`BOTCOIN_PRIVATE_KEY=${exported.privateKey}`);
  console.log(`BOTCOIN_PUBLIC_KEY=${exported.publicKey}`);
  console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');
}

main();
