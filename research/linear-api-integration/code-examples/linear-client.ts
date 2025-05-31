/**
 * Linear API Client Implementation
 * Optimized for autonomous development pipeline integration
 */

import { LinearClient, Issue, Team, User, IssueCreateInput, IssueUpdateInput } from '@linear/sdk';
import { EventEmitter } from 'events';

interface LinearClientConfig {
  apiKey?: string;
  accessToken?: string;
  rateLimitBuffer?: number;
  retryAttempts?: number;
  cacheEnabled?: boolean;
}

interface RateLimitInfo {
  limit: number;
  remaining: number;
  resetTime: number;
}

export class OptimizedLinearClient extends EventEmitter {
  private client: LinearClient;
  private rateLimitInfo: RateLimitInfo | null = null;
  private requestQueue: Array<() => Promise<any>> = [];
  private processing = false;
  private cache = new Map<string, { data: any; expiry: number }>();
  
  constructor(private config: LinearClientConfig) {
    super();
    
    if (config.apiKey) {
      this.client = new LinearClient({ apiKey: config.apiKey });
    } else if (config.accessToken) {
      this.client = new LinearClient({ accessToken: config.accessToken });
    } else {
      throw new Error('Either apiKey or accessToken must be provided');
    }
  }

  /**
   * Execute request with rate limiting and retry logic
   */
  private async executeWithRateLimit<T>(operation: () => Promise<T>): Promise<T> {
    return new Promise((resolve, reject) => {
      this.requestQueue.push(async () => {
        try {
          const result = await this.executeWithRetry(operation);
          resolve(result);
        } catch (error) {
          reject(error);
        }
      });
      
      this.processQueue();
    });
  }

  /**
   * Process request queue with rate limiting
   */
  private async processQueue() {
    if (this.processing || this.requestQueue.length === 0) {
      return;
    }

    this.processing = true;

    while (this.requestQueue.length > 0) {
      // Check rate limit
      if (this.rateLimitInfo && this.rateLimitInfo.remaining <= (this.config.rateLimitBuffer || 10)) {
        const waitTime = this.rateLimitInfo.resetTime - Date.now();
        if (waitTime > 0) {
          await this.sleep(waitTime);
        }
      }

      const operation = this.requestQueue.shift()!;
      await operation();
      
      // Small delay between requests
      await this.sleep(100);
    }

    this.processing = false;
  }

  /**
   * Execute operation with retry logic
   */
  private async executeWithRetry<T>(operation: () => Promise<T>): Promise<T> {
    const maxRetries = this.config.retryAttempts || 3;
    let lastError: Error;

    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        const result = await operation();
        
        // Extract rate limit info from response headers if available
        this.updateRateLimitInfo(result);
        
        return result;
      } catch (error: any) {
        lastError = error;
        
        if (this.isRetryableError(error) && attempt < maxRetries) {
          const delay = Math.pow(2, attempt) * 1000; // Exponential backoff
          await this.sleep(delay);
          continue;
        }
        
        throw error;
      }
    }

    throw lastError!;
  }

  /**
   * Check if error is retryable
   */
  private isRetryableError(error: any): boolean {
    // Rate limiting
    if (error.status === 429) return true;
    
    // Server errors
    if (error.status >= 500) return true;
    
    // Network errors
    if (error.code === 'ECONNRESET' || error.code === 'ETIMEDOUT') return true;
    
    return false;
  }

  /**
   * Update rate limit information
   */
  private updateRateLimitInfo(response: any) {
    // This would be extracted from response headers in a real implementation
    // Linear API provides these headers: X-RateLimit-Requests-*
    if (response.headers) {
      this.rateLimitInfo = {
        limit: parseInt(response.headers['x-ratelimit-requests-limit'] || '1500'),
        remaining: parseInt(response.headers['x-ratelimit-requests-remaining'] || '1500'),
        resetTime: parseInt(response.headers['x-ratelimit-requests-reset'] || '0') * 1000
      };
      
      this.emit('rateLimitUpdate', this.rateLimitInfo);
    }
  }

  /**
   * Get cached data or fetch from API
   */
  private async getCached<T>(key: string, fetcher: () => Promise<T>, ttl: number = 300000): Promise<T> {
    if (!this.config.cacheEnabled) {
      return await fetcher();
    }

    const cached = this.cache.get(key);
    if (cached && cached.expiry > Date.now()) {
      return cached.data;
    }

    const data = await fetcher();
    this.cache.set(key, {
      data,
      expiry: Date.now() + ttl
    });

    return data;
  }

  /**
   * Invalidate cache entries
   */
  public invalidateCache(pattern?: string) {
    if (pattern) {
      for (const key of this.cache.keys()) {
        if (key.includes(pattern)) {
          this.cache.delete(key);
        }
      }
    } else {
      this.cache.clear();
    }
  }

  /**
   * Sleep utility
   */
  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  // Public API methods

  /**
   * Get current user information
   */
  async getCurrentUser(): Promise<User> {
    return this.executeWithRateLimit(() => 
      this.getCached('current-user', () => this.client.viewer)
    );
  }

  /**
   * Get team information with caching
   */
  async getTeam(teamId: string): Promise<Team> {
    return this.executeWithRateLimit(() =>
      this.getCached(`team:${teamId}`, () => this.client.team(teamId))
    );
  }

  /**
   * Get issue with optimized query
   */
  async getIssue(issueId: string): Promise<Issue> {
    return this.executeWithRateLimit(() =>
      this.client.issue(issueId)
    );
  }

  /**
   * Create issue with validation
   */
  async createIssue(input: IssueCreateInput): Promise<Issue> {
    // Validate required fields
    if (!input.title || !input.teamId) {
      throw new Error('Title and teamId are required for issue creation');
    }

    return this.executeWithRateLimit(async () => {
      const result = await this.client.issueCreate(input);
      
      if (!result.success) {
        throw new Error(`Failed to create issue: ${result.error}`);
      }

      // Invalidate relevant cache entries
      this.invalidateCache(`team:${input.teamId}`);
      
      this.emit('issueCreated', result.issue);
      return result.issue!;
    });
  }

  /**
   * Update issue with optimistic updates
   */
  async updateIssue(issueId: string, input: IssueUpdateInput): Promise<Issue> {
    return this.executeWithRateLimit(async () => {
      const result = await this.client.issueUpdate(issueId, input);
      
      if (!result.success) {
        throw new Error(`Failed to update issue: ${result.error}`);
      }

      // Invalidate cache
      this.invalidateCache(`issue:${issueId}`);
      
      this.emit('issueUpdated', result.issue);
      return result.issue!;
    });
  }

  /**
   * Batch update multiple issues
   */
  async batchUpdateIssues(updates: Array<{ id: string; input: IssueUpdateInput }>): Promise<Issue[]> {
    const results: Issue[] = [];
    const batchSize = 5; // Process in small batches to respect rate limits

    for (let i = 0; i < updates.length; i += batchSize) {
      const batch = updates.slice(i, i + batchSize);
      const batchPromises = batch.map(update => this.updateIssue(update.id, update.input));
      
      const batchResults = await Promise.all(batchPromises);
      results.push(...batchResults);
      
      // Small delay between batches
      if (i + batchSize < updates.length) {
        await this.sleep(1000);
      }
    }

    return results;
  }

  /**
   * Search issues with optimized filtering
   */
  async searchIssues(teamId: string, filters: {
    assigneeId?: string;
    stateType?: string;
    updatedSince?: Date;
    limit?: number;
  } = {}): Promise<Issue[]> {
    return this.executeWithRateLimit(async () => {
      const team = await this.getTeam(teamId);
      
      const issueFilter: any = {};
      
      if (filters.assigneeId) {
        issueFilter.assignee = { id: { eq: filters.assigneeId } };
      }
      
      if (filters.stateType) {
        issueFilter.state = { type: { eq: filters.stateType } };
      }
      
      if (filters.updatedSince) {
        issueFilter.updatedAt = { gte: filters.updatedSince };
      }

      const issues = await team.issues({
        filter: issueFilter,
        orderBy: 'updatedAt',
        first: filters.limit || 50
      });

      return issues.nodes;
    });
  }

  /**
   * Get rate limit status
   */
  getRateLimitInfo(): RateLimitInfo | null {
    return this.rateLimitInfo;
  }

  /**
   * Health check
   */
  async healthCheck(): Promise<boolean> {
    try {
      await this.getCurrentUser();
      return true;
    } catch (error) {
      this.emit('healthCheckFailed', error);
      return false;
    }
  }
}

// Usage example
export async function createLinearClient(config: LinearClientConfig): Promise<OptimizedLinearClient> {
  const client = new OptimizedLinearClient(config);
  
  // Set up event listeners
  client.on('rateLimitUpdate', (info) => {
    console.log(`Rate limit: ${info.remaining}/${info.limit} remaining`);
  });
  
  client.on('issueCreated', (issue) => {
    console.log(`Issue created: ${issue.identifier} - ${issue.title}`);
  });
  
  client.on('issueUpdated', (issue) => {
    console.log(`Issue updated: ${issue.identifier}`);
  });
  
  // Verify connection
  const isHealthy = await client.healthCheck();
  if (!isHealthy) {
    throw new Error('Failed to connect to Linear API');
  }
  
  return client;
}

