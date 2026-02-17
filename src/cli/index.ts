#!/usr/bin/env node

import { Command } from 'commander';
import {
  registerCommand,
  mineCommand,
  statusCommand,
  huntsCommand,
  linkWalletCommand,
  claimCommand,
} from './commands';

const program = new Command();

program
  .name('botcoin-miner')
  .description('Botcoin miner agent for botfarmer.ai')
  .version('1.0.0');

program
  .command('register')
  .description('Register a new wallet with the Botcoin API')
  .action(registerCommand);

program
  .command('mine')
  .description('Start the mining agent (solve hunts automatically)')
  .action(mineCommand);

program
  .command('status')
  .description('Check wallet balance and gas status')
  .action(statusCommand);

program
  .command('hunts')
  .description('List available hunts')
  .action(huntsCommand);

program
  .command('link-wallet <address>')
  .description('Link a Base wallet address')
  .action(linkWalletCommand);

program
  .command('claim')
  .description('Claim tokens on-chain')
  .action(claimCommand);

program.parse();
