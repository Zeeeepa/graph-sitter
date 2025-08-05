/**
 * Linear Webhook Handler Implementation
 * Handles real-time events from Linear with proper security and error handling
 */

import express from 'express';
import crypto from 'crypto';
import { EventEmitter } from 'events';
import { Queue } from 'bull';
import Redis from 'ioredis';

interface WebhookPayload {
  action: 'create' | 'update' | 'delete';
  data: any;
  updatedFrom?: any;
  type: string;
  organizationId: string;
  webhookTimestamp: number;
  webhookId: string;
}

interface WebhookConfig {
  port: number;
  path: string;
  secret: string;
  redis?: {
    host: string;
    port: number;
    password?: string;
  };
  rateLimiting?: {
    windowMs: number;
    maxRequests: number;
  };
}

interface ProcessingResult {
  success: boolean;
  error?: string;
  processingTime: number;
}

export class LinearWebhookHandler extends EventEmitter {
  private app: express.Application;
  private eventQueue: Queue;
  private redis: Redis;
  private processingStats = {
    totalEvents: 0,
    successfulEvents: 0,
    failedEvents: 0,
    averageProcessingTime: 0
  };

  constructor(private config: WebhookConfig) {
    super();
    this.app = express();
    this.setupRedis();
    this.setupQueue();
    this.setupMiddleware();
    this.setupRoutes();
  }

  /**
   * Setup Redis connection
   */
  private setupRedis() {
    if (this.config.redis) {
      this.redis = new Redis(this.config.redis);
    } else {
      this.redis = new Redis(); // Default connection
    }

    this.redis.on('error', (error) => {
      this.emit('redisError', error);
    });
  }

  /**
   * Setup Bull queue for event processing
   */
  private setupQueue() {
    this.eventQueue = new Queue('linear-webhook-events', {
      redis: this.config.redis || { host: 'localhost', port: 6379 },
      defaultJobOptions: {
        removeOnComplete: 100,
        removeOnFail: 50,
        attempts: 3,
        backoff: {
          type: 'exponential',
          delay: 2000
        }
      }
    });

    // Process events
    this.eventQueue.process('webhook-event', 10, this.processWebhookEvent.bind(this));

    // Handle job events
    this.eventQueue.on('completed', (job, result: ProcessingResult) => {
      this.updateStats(result);
      this.emit('eventProcessed', { jobId: job.id, result });
    });

    this.eventQueue.on('failed', (job, error) => {
      this.updateStats({ success: false, error: error.message, processingTime: 0 });
      this.emit('eventFailed', { jobId: job.id, error });
    });
  }

  /**
   * Setup Express middleware
   */
  private setupMiddleware() {
    // Rate limiting
    if (this.config.rateLimiting) {
      const rateLimit = require('express-rate-limit');
      this.app.use(rateLimit({
        windowMs: this.config.rateLimiting.windowMs,
        max: this.config.rateLimiting.maxRequests,
        message: 'Too many webhook requests',
        standardHeaders: true,
        legacyHeaders: false
      }));
    }

    // Request size limiting
    this.app.use(express.raw({ 
      type: 'application/json',
      limit: '1mb'
    }));

    // Request logging
    this.app.use((req, res, next) => {
      const start = Date.now();
      res.on('finish', () => {
        const duration = Date.now() - start;
        this.emit('requestLog', {
          method: req.method,
          path: req.path,
          status: res.statusCode,
          duration,
          userAgent: req.get('User-Agent'),
          ip: req.ip
        });
      });
      next();
    });
  }

  /**
   * Setup webhook routes
   */
  private setupRoutes() {
    // Health check endpoint
    this.app.get('/health', (req, res) => {
      res.json({
        status: 'healthy',
        timestamp: new Date().toISOString(),
        stats: this.processingStats,
        queueStats: {
          waiting: this.eventQueue.waiting(),
          active: this.eventQueue.active(),
          completed: this.eventQueue.completed(),
          failed: this.eventQueue.failed()
        }
      });
    });

    // Main webhook endpoint
    this.app.post(this.config.path, async (req, res) => {
      try {
        const signature = req.headers['linear-signature'] as string;
        const timestamp = req.headers['linear-timestamp'] as string;
        const payload = req.body;

        // Verify webhook signature
        if (!this.verifySignature(payload, signature, timestamp)) {
          this.emit('securityViolation', {
            ip: req.ip,
            userAgent: req.get('User-Agent'),
            reason: 'Invalid signature'
          });
          return res.status(401).json({ error: 'Unauthorized' });
        }

        // Parse and validate payload
        const event = this.parseWebhookPayload(payload);
        if (!event) {
          return res.status(400).json({ error: 'Invalid payload' });
        }

        // Check for duplicate events
        const isDuplicate = await this.checkDuplicate(event);
        if (isDuplicate) {
          this.emit('duplicateEvent', event);
          return res.status(200).json({ status: 'duplicate', message: 'Event already processed' });
        }

        // Add to processing queue
        await this.eventQueue.add('webhook-event', event, {
          jobId: `${event.type}-${event.webhookId}-${event.webhookTimestamp}`,
          priority: this.getEventPriority(event)
        });

        // Store event for duplicate detection
        await this.storeEventSignature(event);

        this.emit('eventReceived', event);
        res.status(200).json({ status: 'accepted', eventId: event.webhookId });

      } catch (error) {
        this.emit('webhookError', error);
        res.status(500).json({ error: 'Internal server error' });
      }
    });
  }

  /**
   * Verify webhook signature
   */
  private verifySignature(payload: Buffer, signature: string, timestamp: string): boolean {
    try {
      // Check timestamp to prevent replay attacks
      const eventTime = parseInt(timestamp);
      const currentTime = Math.floor(Date.now() / 1000);
      const timeDiff = Math.abs(currentTime - eventTime);
      
      if (timeDiff > 300) { // 5 minutes tolerance
        return false;
      }

      // Verify signature
      const expectedSignature = crypto
        .createHmac('sha256', this.config.secret)
        .update(timestamp + '.')
        .update(payload)
        .digest('hex');

      return crypto.timingSafeEqual(
        Buffer.from(signature, 'hex'),
        Buffer.from(expectedSignature, 'hex')
      );
    } catch (error) {
      return false;
    }
  }

  /**
   * Parse webhook payload
   */
  private parseWebhookPayload(payload: Buffer): WebhookPayload | null {
    try {
      const event = JSON.parse(payload.toString());
      
      // Validate required fields
      if (!event.type || !event.data || !event.organizationId) {
        return null;
      }

      return {
        action: event.action || 'update',
        data: event.data,
        updatedFrom: event.updatedFrom,
        type: event.type,
        organizationId: event.organizationId,
        webhookTimestamp: event.webhookTimestamp || Date.now(),
        webhookId: event.webhookId || crypto.randomUUID()
      };
    } catch (error) {
      return null;
    }
  }

  /**
   * Check for duplicate events
   */
  private async checkDuplicate(event: WebhookPayload): Promise<boolean> {
    const key = `webhook:${event.type}:${event.data.id}:${event.webhookTimestamp}`;
    const exists = await this.redis.exists(key);
    return exists === 1;
  }

  /**
   * Store event signature for duplicate detection
   */
  private async storeEventSignature(event: WebhookPayload): Promise<void> {
    const key = `webhook:${event.type}:${event.data.id}:${event.webhookTimestamp}`;
    await this.redis.setex(key, 3600, '1'); // Store for 1 hour
  }

  /**
   * Get event priority for queue processing
   */
  private getEventPriority(event: WebhookPayload): number {
    // Higher priority for critical events
    switch (event.type) {
      case 'Issue':
        if (event.action === 'create') return 10;
        if (event.data.assigneeId) return 8; // Assignment changes
        return 5;
      case 'Comment':
        return 7;
      case 'Project':
        return 3;
      default:
        return 1;
    }
  }

  /**
   * Process webhook event
   */
  private async processWebhookEvent(job: any): Promise<ProcessingResult> {
    const startTime = Date.now();
    const event: WebhookPayload = job.data;

    try {
      // Emit event for processing by registered handlers
      this.emit('webhookEvent', event);
      
      // Specific event type handlers
      switch (event.type) {
        case 'Issue':
          await this.processIssueEvent(event);
          break;
        case 'Comment':
          await this.processCommentEvent(event);
          break;
        case 'Project':
          await this.processProjectEvent(event);
          break;
        default:
          this.emit('unknownEventType', event);
      }

      const processingTime = Date.now() - startTime;
      return { success: true, processingTime };

    } catch (error: any) {
      const processingTime = Date.now() - startTime;
      this.emit('processingError', { event, error });
      return { success: false, error: error.message, processingTime };
    }
  }

  /**
   * Process issue events
   */
  private async processIssueEvent(event: WebhookPayload): Promise<void> {
    const { action, data, updatedFrom } = event;

    switch (action) {
      case 'create':
        this.emit('issueCreated', data);
        break;
      case 'update':
        // Check for assignment changes
        if (updatedFrom?.assigneeId !== data.assigneeId) {
          this.emit('issueAssigned', {
            issue: data,
            previousAssignee: updatedFrom?.assigneeId,
            newAssignee: data.assigneeId
          });
        }

        // Check for status changes
        if (updatedFrom?.stateId !== data.stateId) {
          this.emit('issueStatusChanged', {
            issue: data,
            previousState: updatedFrom?.stateId,
            newState: data.stateId
          });
        }

        this.emit('issueUpdated', { data, updatedFrom });
        break;
      case 'delete':
        this.emit('issueDeleted', data);
        break;
    }
  }

  /**
   * Process comment events
   */
  private async processCommentEvent(event: WebhookPayload): Promise<void> {
    const { action, data } = event;

    switch (action) {
      case 'create':
        this.emit('commentCreated', data);
        break;
      case 'update':
        this.emit('commentUpdated', data);
        break;
      case 'delete':
        this.emit('commentDeleted', data);
        break;
    }
  }

  /**
   * Process project events
   */
  private async processProjectEvent(event: WebhookPayload): Promise<void> {
    const { action, data } = event;

    switch (action) {
      case 'create':
        this.emit('projectCreated', data);
        break;
      case 'update':
        this.emit('projectUpdated', data);
        break;
      case 'delete':
        this.emit('projectDeleted', data);
        break;
    }
  }

  /**
   * Update processing statistics
   */
  private updateStats(result: ProcessingResult): void {
    this.processingStats.totalEvents++;
    
    if (result.success) {
      this.processingStats.successfulEvents++;
    } else {
      this.processingStats.failedEvents++;
    }

    // Update average processing time
    const totalTime = this.processingStats.averageProcessingTime * (this.processingStats.totalEvents - 1);
    this.processingStats.averageProcessingTime = (totalTime + result.processingTime) / this.processingStats.totalEvents;
  }

  /**
   * Start the webhook server
   */
  public start(): Promise<void> {
    return new Promise((resolve) => {
      this.app.listen(this.config.port, () => {
        this.emit('serverStarted', { port: this.config.port, path: this.config.path });
        resolve();
      });
    });
  }

  /**
   * Stop the webhook server
   */
  public async stop(): Promise<void> {
    await this.eventQueue.close();
    await this.redis.disconnect();
  }

  /**
   * Get processing statistics
   */
  public getStats() {
    return {
      ...this.processingStats,
      queueStats: {
        waiting: this.eventQueue.waiting(),
        active: this.eventQueue.active(),
        completed: this.eventQueue.completed(),
        failed: this.eventQueue.failed()
      }
    };
  }
}

// Usage example
export async function createWebhookHandler(config: WebhookConfig): Promise<LinearWebhookHandler> {
  const handler = new LinearWebhookHandler(config);

  // Set up event listeners
  handler.on('issueAssigned', (data) => {
    console.log(`Issue ${data.issue.identifier} assigned to ${data.newAssignee}`);
    // Trigger autonomous development pipeline
  });

  handler.on('issueStatusChanged', (data) => {
    console.log(`Issue ${data.issue.identifier} status changed`);
    // Update external systems
  });

  handler.on('commentCreated', (comment) => {
    console.log(`New comment on issue ${comment.issueId}`);
    // Process commands or mentions
  });

  handler.on('securityViolation', (violation) => {
    console.error('Security violation detected:', violation);
    // Alert security team
  });

  handler.on('processingError', ({ event, error }) => {
    console.error(`Failed to process ${event.type} event:`, error);
    // Send to error tracking service
  });

  await handler.start();
  return handler;
}

