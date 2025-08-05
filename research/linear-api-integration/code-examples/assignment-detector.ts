/**
 * Assignment Detection and Orchestration System
 * Monitors Linear issue assignments and triggers autonomous workflows
 */

import { EventEmitter } from 'events';
import { OptimizedLinearClient } from './linear-client';

interface AssignmentEvent {
  issueId: string;
  issueIdentifier: string;
  teamId: string;
  previousAssignee?: string;
  newAssignee: string;
  timestamp: number;
  issueData: any;
}

interface AssignmentRule {
  id: string;
  name: string;
  teamId?: string;
  assigneePattern?: RegExp;
  conditions?: {
    priority?: number[];
    labels?: string[];
    stateType?: string[];
    titlePattern?: RegExp;
  };
  actions: AssignmentAction[];
  enabled: boolean;
}

interface AssignmentAction {
  type: 'notify' | 'auto_start' | 'escalate' | 'assign_reviewer' | 'create_branch' | 'trigger_workflow';
  config: any;
  delay?: number; // Delay in milliseconds
}

interface WorkflowContext {
  assignment: AssignmentEvent;
  rule: AssignmentRule;
  linearClient: OptimizedLinearClient;
}

export class AssignmentDetector extends EventEmitter {
  private rules: Map<string, AssignmentRule> = new Map();
  private activeWorkflows: Map<string, NodeJS.Timeout> = new Map();

  constructor(private linearClient: OptimizedLinearClient) {
    super();
    this.setupDefaultRules();
  }

  /**
   * Setup default assignment rules
   */
  private setupDefaultRules(): void {
    // Auto-start rule for development issues
    this.addRule({
      id: 'auto-start-dev',
      name: 'Auto-start development issues',
      conditions: {
        labels: ['development', 'feature', 'bug'],
        stateType: ['backlog', 'triage']
      },
      actions: [
        {
          type: 'auto_start',
          config: { targetState: 'In Progress' }
        },
        {
          type: 'notify',
          config: { 
            message: 'Issue automatically moved to In Progress',
            channels: ['slack', 'email']
          }
        }
      ],
      enabled: true
    });

    // High priority escalation rule
    this.addRule({
      id: 'high-priority-escalation',
      name: 'Escalate high priority issues',
      conditions: {
        priority: [1, 2] // Urgent and High priority
      },
      actions: [
        {
          type: 'notify',
          config: {
            message: 'High priority issue assigned',
            channels: ['slack'],
            urgent: true
          }
        },
        {
          type: 'assign_reviewer',
          config: { reviewerRole: 'tech_lead' },
          delay: 3600000 // 1 hour delay
        }
      ],
      enabled: true
    });

    // Autonomous development trigger
    this.addRule({
      id: 'autonomous-dev-trigger',
      name: 'Trigger autonomous development',
      assigneePattern: /^(codegen|ai-agent|bot-)/i,
      conditions: {
        labels: ['autonomous', 'ai-ready'],
        stateType: ['backlog']
      },
      actions: [
        {
          type: 'create_branch',
          config: { branchPrefix: 'codegen' }
        },
        {
          type: 'trigger_workflow',
          config: { 
            workflow: 'autonomous-development',
            parameters: { mode: 'full-auto' }
          }
        }
      ],
      enabled: true
    });
  }

  /**
   * Add assignment rule
   */
  public addRule(rule: AssignmentRule): void {
    this.rules.set(rule.id, rule);
    this.emit('ruleAdded', rule);
  }

  /**
   * Remove assignment rule
   */
  public removeRule(ruleId: string): void {
    this.rules.delete(ruleId);
    this.emit('ruleRemoved', ruleId);
  }

  /**
   * Update assignment rule
   */
  public updateRule(ruleId: string, updates: Partial<AssignmentRule>): void {
    const rule = this.rules.get(ruleId);
    if (rule) {
      const updatedRule = { ...rule, ...updates };
      this.rules.set(ruleId, updatedRule);
      this.emit('ruleUpdated', updatedRule);
    }
  }

  /**
   * Get all rules
   */
  public getRules(): AssignmentRule[] {
    return Array.from(this.rules.values());
  }

  /**
   * Process assignment event
   */
  public async processAssignment(event: AssignmentEvent): Promise<void> {
    try {
      this.emit('assignmentDetected', event);

      // Find applicable rules
      const applicableRules = await this.findApplicableRules(event);
      
      if (applicableRules.length === 0) {
        this.emit('noRulesApplied', event);
        return;
      }

      // Execute rules
      for (const rule of applicableRules) {
        await this.executeRule(event, rule);
      }

    } catch (error) {
      this.emit('assignmentProcessingError', { event, error });
    }
  }

  /**
   * Find rules applicable to assignment event
   */
  private async findApplicableRules(event: AssignmentEvent): Promise<AssignmentRule[]> {
    const applicableRules: AssignmentRule[] = [];

    for (const rule of this.rules.values()) {
      if (!rule.enabled) continue;

      try {
        const isApplicable = await this.isRuleApplicable(event, rule);
        if (isApplicable) {
          applicableRules.push(rule);
        }
      } catch (error) {
        this.emit('ruleEvaluationError', { rule, event, error });
      }
    }

    return applicableRules;
  }

  /**
   * Check if rule is applicable to assignment event
   */
  private async isRuleApplicable(event: AssignmentEvent, rule: AssignmentRule): Promise<boolean> {
    // Check team restriction
    if (rule.teamId && rule.teamId !== event.teamId) {
      return false;
    }

    // Check assignee pattern
    if (rule.assigneePattern) {
      const assignee = await this.linearClient.getUser(event.newAssignee);
      if (!rule.assigneePattern.test(assignee.name || assignee.email || '')) {
        return false;
      }
    }

    // Check conditions
    if (rule.conditions) {
      const issue = event.issueData;

      // Priority check
      if (rule.conditions.priority && !rule.conditions.priority.includes(issue.priority)) {
        return false;
      }

      // Labels check
      if (rule.conditions.labels) {
        const issueLabels = issue.labels?.nodes?.map((l: any) => l.name) || [];
        const hasRequiredLabel = rule.conditions.labels.some(label => 
          issueLabels.includes(label)
        );
        if (!hasRequiredLabel) {
          return false;
        }
      }

      // State type check
      if (rule.conditions.stateType && !rule.conditions.stateType.includes(issue.state.type)) {
        return false;
      }

      // Title pattern check
      if (rule.conditions.titlePattern && !rule.conditions.titlePattern.test(issue.title)) {
        return false;
      }
    }

    return true;
  }

  /**
   * Execute assignment rule
   */
  private async executeRule(event: AssignmentEvent, rule: AssignmentRule): Promise<void> {
    this.emit('ruleExecutionStarted', { event, rule });

    const context: WorkflowContext = {
      assignment: event,
      rule,
      linearClient: this.linearClient
    };

    try {
      for (const action of rule.actions) {
        if (action.delay && action.delay > 0) {
          // Schedule delayed action
          const timeoutId = setTimeout(async () => {
            await this.executeAction(action, context);
            this.activeWorkflows.delete(`${event.issueId}-${rule.id}-${action.type}`);
          }, action.delay);

          this.activeWorkflows.set(`${event.issueId}-${rule.id}-${action.type}`, timeoutId);
        } else {
          // Execute immediately
          await this.executeAction(action, context);
        }
      }

      this.emit('ruleExecutionCompleted', { event, rule });

    } catch (error) {
      this.emit('ruleExecutionError', { event, rule, error });
    }
  }

  /**
   * Execute individual action
   */
  private async executeAction(action: AssignmentAction, context: WorkflowContext): Promise<void> {
    const { assignment, linearClient } = context;

    switch (action.type) {
      case 'notify':
        await this.executeNotifyAction(action, context);
        break;

      case 'auto_start':
        await this.executeAutoStartAction(action, context);
        break;

      case 'escalate':
        await this.executeEscalateAction(action, context);
        break;

      case 'assign_reviewer':
        await this.executeAssignReviewerAction(action, context);
        break;

      case 'create_branch':
        await this.executeCreateBranchAction(action, context);
        break;

      case 'trigger_workflow':
        await this.executeTriggerWorkflowAction(action, context);
        break;

      default:
        this.emit('unknownActionType', { action, context });
    }
  }

  /**
   * Execute notify action
   */
  private async executeNotifyAction(action: AssignmentAction, context: WorkflowContext): Promise<void> {
    const { assignment } = context;
    const { config } = action;

    const notification = {
      type: 'assignment',
      issueId: assignment.issueId,
      issueIdentifier: assignment.issueIdentifier,
      assignee: assignment.newAssignee,
      message: config.message,
      channels: config.channels || ['slack'],
      urgent: config.urgent || false,
      timestamp: Date.now()
    };

    this.emit('notificationTriggered', notification);
  }

  /**
   * Execute auto-start action
   */
  private async executeAutoStartAction(action: AssignmentAction, context: WorkflowContext): Promise<void> {
    const { assignment, linearClient } = context;
    const { config } = action;

    try {
      // Get team states
      const team = await linearClient.getTeam(assignment.teamId);
      const states = await team.states();
      
      // Find target state
      const targetState = states.nodes.find(state => 
        state.name.toLowerCase().includes(config.targetState.toLowerCase()) ||
        state.type === 'started'
      );

      if (targetState) {
        await linearClient.updateIssue(assignment.issueId, {
          stateId: targetState.id
        });

        this.emit('issueAutoStarted', {
          issueId: assignment.issueId,
          previousState: assignment.issueData.state.name,
          newState: targetState.name
        });
      }

    } catch (error) {
      this.emit('autoStartError', { assignment, error });
    }
  }

  /**
   * Execute escalate action
   */
  private async executeEscalateAction(action: AssignmentAction, context: WorkflowContext): Promise<void> {
    const { assignment } = context;
    const { config } = action;

    const escalation = {
      issueId: assignment.issueId,
      issueIdentifier: assignment.issueIdentifier,
      reason: config.reason || 'Automatic escalation',
      escalateTo: config.escalateTo,
      timestamp: Date.now()
    };

    this.emit('escalationTriggered', escalation);
  }

  /**
   * Execute assign reviewer action
   */
  private async executeAssignReviewerAction(action: AssignmentAction, context: WorkflowContext): Promise<void> {
    const { assignment, linearClient } = context;
    const { config } = action;

    try {
      // Find reviewer based on role or specific user
      const reviewer = await this.findReviewer(assignment.teamId, config.reviewerRole);
      
      if (reviewer) {
        // Add comment mentioning reviewer
        await linearClient.createComment(assignment.issueId, {
          body: `@${reviewer.name} has been assigned as reviewer for this issue.`
        });

        this.emit('reviewerAssigned', {
          issueId: assignment.issueId,
          reviewer: reviewer.id,
          role: config.reviewerRole
        });
      }

    } catch (error) {
      this.emit('reviewerAssignmentError', { assignment, error });
    }
  }

  /**
   * Execute create branch action
   */
  private async executeCreateBranchAction(action: AssignmentAction, context: WorkflowContext): Promise<void> {
    const { assignment } = context;
    const { config } = action;

    const branchRequest = {
      issueId: assignment.issueId,
      issueIdentifier: assignment.issueIdentifier,
      branchName: `${config.branchPrefix || 'feature'}/${assignment.issueIdentifier.toLowerCase()}`,
      baseBranch: config.baseBranch || 'main',
      timestamp: Date.now()
    };

    this.emit('branchCreationRequested', branchRequest);
  }

  /**
   * Execute trigger workflow action
   */
  private async executeTriggerWorkflowAction(action: AssignmentAction, context: WorkflowContext): Promise<void> {
    const { assignment } = context;
    const { config } = action;

    const workflowTrigger = {
      workflow: config.workflow,
      issueId: assignment.issueId,
      issueIdentifier: assignment.issueIdentifier,
      parameters: {
        ...config.parameters,
        assignee: assignment.newAssignee,
        teamId: assignment.teamId
      },
      timestamp: Date.now()
    };

    this.emit('workflowTriggered', workflowTrigger);
  }

  /**
   * Find reviewer for team and role
   */
  private async findReviewer(teamId: string, role: string): Promise<any> {
    // This would integrate with your team management system
    // For now, return a placeholder
    return { id: 'reviewer-id', name: 'Tech Lead' };
  }

  /**
   * Cancel active workflows for issue
   */
  public cancelWorkflows(issueId: string): void {
    for (const [key, timeoutId] of this.activeWorkflows.entries()) {
      if (key.startsWith(issueId)) {
        clearTimeout(timeoutId);
        this.activeWorkflows.delete(key);
      }
    }
  }

  /**
   * Get active workflows
   */
  public getActiveWorkflows(): string[] {
    return Array.from(this.activeWorkflows.keys());
  }

  /**
   * Cleanup resources
   */
  public cleanup(): void {
    for (const timeoutId of this.activeWorkflows.values()) {
      clearTimeout(timeoutId);
    }
    this.activeWorkflows.clear();
  }
}

// Usage example
export async function createAssignmentDetector(linearClient: OptimizedLinearClient): Promise<AssignmentDetector> {
  const detector = new AssignmentDetector(linearClient);

  // Set up event listeners
  detector.on('assignmentDetected', (event) => {
    console.log(`Assignment detected: ${event.issueIdentifier} → ${event.newAssignee}`);
  });

  detector.on('workflowTriggered', (trigger) => {
    console.log(`Workflow triggered: ${trigger.workflow} for ${trigger.issueIdentifier}`);
    // Integrate with your workflow orchestration system
  });

  detector.on('notificationTriggered', (notification) => {
    console.log(`Notification: ${notification.message}`);
    // Send to notification service
  });

  detector.on('branchCreationRequested', (request) => {
    console.log(`Branch creation requested: ${request.branchName}`);
    // Integrate with Git service
  });

  detector.on('escalationTriggered', (escalation) => {
    console.log(`Escalation triggered for ${escalation.issueIdentifier}`);
    // Send to escalation service
  });

  return detector;
}

