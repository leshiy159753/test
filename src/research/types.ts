/**
 * Research engine types
 */

export interface ResearchContext {
  huntId: string;
  difficulty: number;
  poem?: string;
  description?: string;
  hints?: string[];
}

export interface ResearchResult {
  answer: string;
  confidence: number;
  reasoning: string;
  sources?: string[];
}

export interface SearchResult {
  title: string;
  snippet: string;
  url: string;
}
