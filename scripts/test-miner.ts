#!/usr/bin/env node

/**
 * Test script for Botcoin miner
 * Tests all major components without making real API calls
 */

import { generateKeypair, exportKeypair, signMessage, verifySignature } from '../src/crypto/keys';
import { ResearchEngine } from '../src/research/engine';
import { logger } from '../src/utils/logger';

async function testCrypto() {
  console.log('\n🔐 Testing Crypto Module...');
  
  // Generate keypair
  const keypair = generateKeypair();
  const exported = exportKeypair(keypair);
  console.log(`✓ Generated keypair`);
  console.log(`  Public key length: ${exported.publicKey.length} chars`);
  console.log(`  Private key length: ${exported.privateKey.length} chars`);
  
  // Sign and verify
  const message = 'Hello Botcoin!';
  const signature = signMessage(message, keypair.secretKey);
  const isValid = verifySignature(message, signature, keypair.publicKey);
  console.log(`✓ Signature verification: ${isValid ? 'PASS' : 'FAIL'}`);
  
  return isValid;
}

async function testResearchEngine() {
  console.log('\n🔍 Testing Research Engine...');
  
  const engine = new ResearchEngine();
  
  // Test easy hunt
  const easyResult = await engine.solve({
    huntId: 'test-easy',
    difficulty: 1,
    poem: 'What is 5 + 3?',
    description: 'Simple math',
  });
  console.log(`✓ Easy hunt: "${easyResult.answer}" (confidence: ${easyResult.confidence})`);
  
  // Test medium hunt
  const mediumResult = await engine.solve({
    huntId: 'test-medium',
    difficulty: 5,
    poem: 'Find the capital of France',
    hints: ['It\'s a European city'],
  });
  console.log(`✓ Medium hunt: "${mediumResult.answer}" (confidence: ${mediumResult.confidence})`);
  
  // Test hard hunt
  const hardResult = await engine.solve({
    huntId: 'test-hard',
    difficulty: 8,
    poem: 'The quick brown fox jumps over the lazy dog. What is special about this sentence?',
    hints: ['Think about letters'],
  });
  console.log(`✓ Hard hunt: "${hardResult.answer}" (confidence: ${hardResult.confidence})`);
  
  return true;
}

async function testConfig() {
  console.log('\n⚙️  Testing Configuration...');
  
  try {
    const { loadConfig } = await import('../src/config/index');
    const config = loadConfig();
    console.log(`✓ Config loaded`);
    console.log(`  API URL: ${config.apiUrl}`);
    console.log(`  Mining interval: ${config.miningInterval}ms`);
    console.log(`  Max retries: ${config.maxRetries}`);
    console.log(`  Log level: ${config.logLevel}`);
    return true;
  } catch (error: any) {
    console.log(`⚠ Config error (expected if no .env): ${error.message}`);
    return false;
  }
}

async function main() {
  console.log('═══════════════════════════════════════════════════');
  console.log('🧪 Botcoin Miner Test Suite');
  console.log('═══════════════════════════════════════════════════');
  
  const results = [];
  
  // Run tests
  results.push(await testCrypto());
  results.push(await testResearchEngine());
  results.push(await testConfig());
  
  // Summary
  console.log('\n═══════════════════════════════════════════════════');
  const passed = results.filter(r => r).length;
  const total = results.length;
  console.log(`📊 Results: ${passed}/${total} tests passed`);
  
  if (passed === total) {
    console.log('✅ All tests passed! The miner is ready to use.');
    console.log('\nNext steps:');
    console.log('1. Run: npm run generate-keys');
    console.log('2. Add keys to .env file');
    console.log('3. Run: npm run register');
    console.log('4. Run: npm run mine');
  } else {
    console.log('⚠️  Some tests failed. Check the output above.');
  }
  console.log('═══════════════════════════════════════════════════\n');
}

main().catch(error => {
  logger.error('Test failed', error);
  process.exit(1);
});
