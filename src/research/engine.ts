import { createLogger } from '../utils/logger';
import { ResearchError } from '../utils/errors';
import { ResearchContext, ResearchResult } from './types';

const logger = createLogger('Research');

/**
 * Research engine for solving hunt puzzles
 * 
 * This is a basic implementation that uses pattern matching and heuristics.
 * For production, you would integrate with:
 * - Web search APIs (Serper, SerpAPI, Google Custom Search)
 * - LLM APIs (OpenAI, Anthropic) for reasoning
 * - Knowledge bases or databases
 */
export class ResearchEngine {
  /**
   * Solve a hunt puzzle
   */
  async solve(context: ResearchContext): Promise<ResearchResult> {
    logger.info(`Solving hunt ${context.huntId} (difficulty: ${context.difficulty})`);

    try {
      // Step 1: Extract clues from poem/description
      const clues = this.extractClues(context);
      logger.debug(`Extracted clues: ${JSON.stringify(clues)}`);

      // Step 2: Apply solving strategies based on difficulty
      const answer = await this.applySolvingStrategy(context, clues);

      // Step 3: Validate and format answer
      const formattedAnswer = this.formatAnswer(answer);

      return {
        answer: formattedAnswer,
        confidence: 0.7, // Confidence score (0-1)
        reasoning: `Applied strategy for difficulty ${context.difficulty}`,
        sources: [],
      };
    } catch (error) {
      logger.error(`Failed to solve hunt ${context.huntId}`, error);
      throw new ResearchError(`Failed to solve hunt: ${error}`);
    }
  }

  /**
   * Extract clues from poem/description/hints
   */
  private extractClues(context: ResearchContext): string[] {
    const clues: string[] = [];

    // Extract from poem
    if (context.poem) {
      // Look for capitalized words, numbers, quotes
      const capitalWords = context.poem.match(/\b[A-Z][a-z]+\b/g) || [];
      const numbers = context.poem.match(/\b\d+\b/g) || [];
      const quoted = context.poem.match(/"([^"]+)"/g) || [];
      
      clues.push(...capitalWords, ...numbers, ...quoted);
    }

    // Extract from description
    if (context.description) {
      // Similar extraction logic
      const words = context.description.match(/\b[A-Z][a-z]+\b/g) || [];
      clues.push(...words);
    }

    // Add hints
    if (context.hints) {
      clues.push(...context.hints);
    }

    return [...new Set(clues)]; // Remove duplicates
  }

  /**
   * Apply solving strategy based on difficulty
   */
  private async applySolvingStrategy(context: ResearchContext, clues: string[]): Promise<string> {
    logger.debug(`Applying strategy for difficulty ${context.difficulty}`);

    // Difficulty-based strategies
    if (context.difficulty <= 2) {
      // Easy: Direct pattern matching
      return this.solveEasy(context, clues);
    } else if (context.difficulty <= 5) {
      // Medium: Requires research
      return await this.solveMedium(context, clues);
    } else {
      // Hard: Complex reasoning
      return await this.solveHard(context, clues);
    }
  }

  /**
   * Solve easy puzzles (difficulty 1-2)
   */
  private solveEasy(context: ResearchContext, clues: string[]): string {
    logger.debug('Using easy strategy');

    // Look for obvious patterns
    const text = [context.poem, context.description].filter(Boolean).join(' ');

    // Check for math expressions
    const mathMatch = text.match(/(\d+)\s*[\+\-\*\/]\s*(\d+)/);
    if (mathMatch) {
      const result = eval(mathMatch[0]);
      logger.debug(`Math expression found: ${mathMatch[0]} = ${result}`);
      return result.toString();
    }

    // Check for direct questions with simple answers
    if (text.toLowerCase().includes('what is')) {
      // Extract potential answer after "what is"
      const match = text.match(/what is\s+([^\?\.]+)/i);
      if (match) {
        return match[1].trim();
      }
    }

    // Default: return first clue
    return clues[0] || 'unknown';
  }

  /**
   * Solve medium puzzles (difficulty 3-5)
   * Would use web search here in production
   */
  private async solveMedium(context: ResearchContext, clues: string[]): Promise<string> {
    logger.debug('Using medium strategy');

    // In production, you would:
    // 1. Search the web for clues
    // 2. Extract potential answers from search results
    // 3. Rank answers by relevance
    
    // For now, use heuristics
    const text = [context.poem, context.description].filter(Boolean).join(' ');

    // Look for patterns like "find the X" or "what is the Y"
    const findMatch = text.match(/find (?:the )?(\w+)/i);
    if (findMatch) {
      logger.debug(`Found "find" pattern: ${findMatch[1]}`);
      return findMatch[1];
    }

    // Look for quoted answers
    const quotedMatch = text.match(/"([^"]+)"/);
    if (quotedMatch) {
      logger.debug(`Found quoted text: ${quotedMatch[1]}`);
      return quotedMatch[1];
    }

    // Return most prominent clue
    return clues[0] || 'unknown';
  }

  /**
   * Solve hard puzzles (difficulty 6-10)
   * Would use LLM reasoning here in production
   */
  private async solveHard(context: ResearchContext, clues: string[]): Promise<string> {
    logger.debug('Using hard strategy');

    // In production, you would:
    // 1. Feed poem + clues to LLM
    // 2. Ask LLM to reason about the answer
    // 3. Verify answer with web search
    // 4. Return most confident answer

    // For now, use advanced heuristics
    const text = [context.poem, context.description, ...(context.hints || [])].filter(Boolean).join(' ');

    // Look for cryptic clues, anagrams, etc.
    logger.warn('Hard puzzle detected - may require manual intervention');

    // Return hint if available
    if (context.hints && context.hints.length > 0) {
      return context.hints[0];
    }

    return clues[0] || 'unknown';
  }

  /**
   * Format answer (trim, lowercase, etc.)
   */
  private formatAnswer(answer: string): string {
    return answer.trim().toLowerCase();
  }

  /**
   * Check if we have enough confidence to submit
   */
  shouldSubmit(result: ResearchResult, threshold: number = 0.6): boolean {
    return result.confidence >= threshold;
  }
}
