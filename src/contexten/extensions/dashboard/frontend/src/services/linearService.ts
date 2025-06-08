import { Task, Plan } from '../types/dashboard';

export interface LinearIssue {
  id: string;
  title: string;
  description: string;
  state: {
    id: string;
    name: string;
    type: string;
  };
  assignee: {
    id: string;
    name: string;
    email: string;
  } | null;
  estimate: number | null;
  startedAt: string | null;
  completedAt: string | null;
  createdAt: string;
  updatedAt: string;
  parent: {
    id: string;
  } | null;
  children: {
    nodes: {
      id: string;
    }[];
  };
}

export interface LinearTeam {
  id: string;
  name: string;
  key: string;
}

export interface LinearUser {
  id: string;
  name: string;
  email: string;
}

export interface LinearWorkflowState {
  id: string;
  name: string;
  type: string;
  team: {
    id: string;
  };
}

export class LinearService {
  private token: string;
  private baseUrl = 'https://api.linear.app/graphql';

  constructor(token: string) {
    this.token = token;
  }

  private async request<T>(query: string, variables: any = {}): Promise<T> {
    const response = await fetch(this.baseUrl, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        query,
        variables,
      }),
    });

    if (!response.ok) {
      throw new Error(`Linear API error: ${response.statusText}`);
    }

    const json = await response.json();
    if (json.errors) {
      throw new Error(`Linear GraphQL error: ${json.errors[0].message}`);
    }

    return json.data;
  }

  async getTeams(): Promise<LinearTeam[]> {
    const query = `
      query {
        teams {
          nodes {
            id
            name
            key
          }
        }
      }
    `;

    const data = await this.request<{ teams: { nodes: LinearTeam[] } }>(query);
    return data.teams.nodes;
  }

  async getTeamIssues(teamId: string): Promise<LinearIssue[]> {
    const query = `
      query($teamId: ID!) {
        team(id: $teamId) {
          issues {
            nodes {
              id
              title
              description
              state {
                id
                name
                type
              }
              assignee {
                id
                name
                email
              }
              estimate
              startedAt
              completedAt
              createdAt
              updatedAt
              parent {
                id
              }
              children {
                nodes {
                  id
                }
              }
            }
          }
        }
      }
    `;

    const data = await this.request<{ team: { issues: { nodes: LinearIssue[] } } }>(query, { teamId });
    return data.team.issues.nodes;
  }

  async createIssue(teamId: string, title: string, description: string, assigneeId?: string): Promise<LinearIssue> {
    const query = `
      mutation($input: IssueCreateInput!) {
        issueCreate(input: $input) {
          issue {
            id
            title
            description
            state {
              id
              name
              type
            }
            assignee {
              id
              name
              email
            }
            estimate
            startedAt
            completedAt
            createdAt
            updatedAt
          }
        }
      }
    `;

    const data = await this.request<{ issueCreate: { issue: LinearIssue } }>(query, {
      input: {
        teamId,
        title,
        description,
        assigneeId,
      },
    });

    return data.issueCreate.issue;
  }

  async updateIssue(issueId: string, updates: Partial<LinearIssue>): Promise<LinearIssue> {
    const query = `
      mutation($id: ID!, $input: IssueUpdateInput!) {
        issueUpdate(id: $id, input: $input) {
          issue {
            id
            title
            description
            state {
              id
              name
              type
            }
            assignee {
              id
              name
              email
            }
            estimate
            startedAt
            completedAt
            createdAt
            updatedAt
          }
        }
      }
    `;

    const data = await this.request<{ issueUpdate: { issue: LinearIssue } }>(query, {
      id: issueId,
      input: updates,
    });

    return data.issueUpdate.issue;
  }

  async convertToTask(issue: LinearIssue): Promise<Task> {
    return {
      id: issue.id,
      title: issue.title,
      description: issue.description,
      status: this.mapStateToStatus(issue.state.type),
      assignee: issue.assignee?.name,
      estimatedHours: issue.estimate || 0,
      actualHours: 0, // This would need to be calculated from time tracking data
      dependencies: issue.children.nodes.map(n => n.id),
      createdAt: new Date(issue.createdAt),
      updatedAt: new Date(issue.updatedAt),
    };
  }

  async createPlanFromIssues(teamId: string, projectId: string, title: string): Promise<Plan> {
    const issues = await this.getTeamIssues(teamId);
    const tasks = await Promise.all(issues.map(i => this.convertToTask(i)));

    return {
      id: `plan-${Date.now()}`,
      projectId,
      title,
      description: `Plan generated from Linear team ${teamId}`,
      tasks,
      status: 'in_progress',
      createdAt: new Date(),
      updatedAt: new Date(),
    };
  }

  private mapStateToStatus(stateType: string): Task['status'] {
    switch (stateType) {
      case 'backlog':
      case 'unstarted':
        return 'pending';
      case 'started':
      case 'in_progress':
        return 'in_progress';
      case 'completed':
      case 'done':
        return 'completed';
      case 'canceled':
        return 'error';
      default:
        return 'pending';
    }
  }

  async getUsers(): Promise<LinearUser[]> {
    const query = `
      query {
        users {
          nodes {
            id
            name
            email
          }
        }
      }
    `;

    const data = await this.request<{ users: { nodes: LinearUser[] } }>(query);
    return data.users.nodes;
  }

  async getWorkflowStates(teamId: string): Promise<LinearWorkflowState[]> {
    const query = `
      query($teamId: ID!) {
        team(id: $teamId) {
          states {
            nodes {
              id
              name
              type
              team {
                id
              }
            }
          }
        }
      }
    `;

    const data = await this.request<{ team: { states: { nodes: LinearWorkflowState[] } } }>(query, { teamId });
    return data.team.states.nodes;
  }
}

