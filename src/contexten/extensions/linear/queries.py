"""
Linear GraphQL Queries

This module contains all GraphQL queries for the Linear API.
"""

# Issue Queries
GET_ISSUE = """
query GetIssue($id: String!) {
  issue(id: $id) {
    id
    identifier
    title
    description
    priority
    estimate
    url
    createdAt
    updatedAt
    archivedAt
    completedAt
    canceledAt
    autoArchivedAt
    autoClosedAt
    dueDate
    sortOrder
    boardOrder
    subIssueSortOrder
    priorityLabel
    branchName
    customerTicketCount
    cycle {
      id
      name
      number
    }
    project {
      id
      name
      description
      url
      icon
      color
    }
    team {
      id
      name
      key
      description
      icon
      color
    }
    assignee {
      id
      name
      displayName
      email
      avatarUrl
      isMe
      isAdmin
      isGuest
    }
    creator {
      id
      name
      displayName
      email
      avatarUrl
    }
    state {
      id
      name
      color
      type
      description
    }
    parent {
      id
      identifier
      title
    }
    children {
      nodes {
        id
        identifier
        title
        state {
          name
          type
        }
      }
    }
    labels {
      nodes {
        id
        name
        color
        description
      }
    }
    comments {
      nodes {
        id
        body
        createdAt
        updatedAt
        user {
          id
          name
          displayName
          avatarUrl
        }
      }
    }
    attachments {
      nodes {
        id
        title
        url
        subtitle
        metadata
      }
    }
    relations {
      nodes {
        id
        type
        relatedIssue {
          id
          identifier
          title
        }
      }
    }
  }
}
"""

SEARCH_ISSUES = """
query SearchIssues($first: Int!, $filter: IssueFilter) {
  issues(first: $first, filter: $filter, orderBy: updatedAt) {
    nodes {
      id
      identifier
      title
      description
      priority
      estimate
      url
      createdAt
      updatedAt
      dueDate
      priorityLabel
      team {
        id
        name
        key
      }
      assignee {
        id
        name
        displayName
        avatarUrl
      }
      creator {
        id
        name
        displayName
      }
      state {
        id
        name
        color
        type
      }
      project {
        id
        name
        icon
        color
      }
      labels {
        nodes {
          id
          name
          color
        }
      }
      parent {
        id
        identifier
        title
      }
    }
    pageInfo {
      hasNextPage
      hasPreviousPage
      startCursor
      endCursor
    }
  }
}
"""

GET_ISSUES_BY_TEAM = """
query GetIssuesByTeam($teamId: String!, $first: Int!, $filter: IssueFilter) {
  team(id: $teamId) {
    issues(first: $first, filter: $filter, orderBy: updatedAt) {
      nodes {
        id
        identifier
        title
        description
        priority
        url
        createdAt
        updatedAt
        assignee {
          id
          name
          displayName
        }
        state {
          id
          name
          type
        }
        project {
          id
          name
        }
      }
      pageInfo {
        hasNextPage
        endCursor
      }
    }
  }
}
"""

# Project Queries
GET_PROJECTS = """
query GetProjects($first: Int!, $filter: ProjectFilter) {
  projects(first: $first, filter: $filter, orderBy: updatedAt) {
    nodes {
      id
      name
      description
      url
      icon
      color
      state
      progress
      scope
      createdAt
      updatedAt
      startDate
      targetDate
      completedAt
      canceledAt
      autoArchivedAt
      slugId
      sortOrder
      issueCountHistory
      completedIssueCountHistory
      scopeHistory
      completedScopeHistory
      lead {
        id
        name
        displayName
        avatarUrl
      }
      creator {
        id
        name
        displayName
      }
      team {
        id
        name
        key
        description
      }
      members {
        nodes {
          id
          name
          displayName
          avatarUrl
        }
      }
      issues {
        nodes {
          id
          identifier
          title
          state {
            name
            type
          }
        }
      }
      projectMilestones {
        nodes {
          id
          name
          description
          targetDate
        }
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
"""

GET_PROJECT = """
query GetProject($id: String!) {
  project(id: $id) {
    id
    name
    description
    url
    icon
    color
    state
    progress
    scope
    createdAt
    updatedAt
    startDate
    targetDate
    completedAt
    lead {
      id
      name
      displayName
      avatarUrl
    }
    team {
      id
      name
      key
    }
    members {
      nodes {
        id
        name
        displayName
        avatarUrl
      }
    }
    issues {
      nodes {
        id
        identifier
        title
        priority
        estimate
        state {
          name
          type
        }
        assignee {
          id
          name
          displayName
        }
      }
    }
  }
}
"""

# Team Queries
GET_TEAMS = """
query GetTeams($first: Int!) {
  teams(first: $first, orderBy: name) {
    nodes {
      id
      name
      key
      description
      icon
      color
      private
      issueEstimationType
      issueEstimationAllowZero
      issueEstimationExtended
      issueOrderingNoPriorityFirst
      issueSortOrderDefaultToBottom
      defaultIssueEstimate
      triageEnabled
      requirePriorityToLeaveTriage
      defaultTemplateForMembers {
        id
        name
      }
      defaultTemplateForNonMembers {
        id
        name
      }
      markedAsDuplicateWorkflow {
        id
        name
      }
      activeCycle {
        id
        name
        number
        startsAt
        endsAt
      }
      organization {
        id
        name
      }
      members {
        nodes {
          id
          name
          displayName
          email
          avatarUrl
          isMe
          isAdmin
          isGuest
        }
      }
      projects {
        nodes {
          id
          name
          state
        }
      }
      states {
        nodes {
          id
          name
          color
          type
          description
        }
      }
      labels {
        nodes {
          id
          name
          color
          description
        }
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
"""

GET_TEAM = """
query GetTeam($id: String!) {
  team(id: $id) {
    id
    name
    key
    description
    icon
    color
    private
    members {
      nodes {
        id
        name
        displayName
        email
        avatarUrl
        isMe
        isAdmin
        isGuest
      }
    }
    projects {
      nodes {
        id
        name
        description
        state
        progress
      }
    }
    states {
      nodes {
        id
        name
        color
        type
        description
      }
    }
    labels {
      nodes {
        id
        name
        color
        description
      }
    }
    activeCycle {
      id
      name
      number
      startsAt
      endsAt
    }
  }
}
"""

GET_TEAM_MEMBERS = """
query GetTeamMembers($teamId: String!, $first: Int!) {
  team(id: $teamId) {
    members(first: $first) {
      nodes {
        id
        name
        displayName
        email
        avatarUrl
        isMe
        isAdmin
        isGuest
        active
        createdAt
        lastSeen
        timezone
        organization {
          id
          name
        }
        teams {
          nodes {
            id
            name
            key
          }
        }
      }
      pageInfo {
        hasNextPage
        endCursor
      }
    }
  }
}
"""

# User Queries
GET_CURRENT_USER = """
query GetCurrentUser {
  viewer {
    id
    name
    displayName
    email
    avatarUrl
    isMe
    isAdmin
    isGuest
    active
    createdAt
    lastSeen
    timezone
    organization {
      id
      name
      urlKey
      logoUrl
      createdAt
      updatedAt
      userCount
      userCountInOrg
      periodUploadVolume
    }
    teams {
      nodes {
        id
        name
        key
        description
      }
    }
    assignedIssues {
      nodes {
        id
        identifier
        title
        priority
        state {
          name
          type
        }
        team {
          name
          key
        }
      }
    }
    createdIssues {
      nodes {
        id
        identifier
        title
        state {
          name
          type
        }
      }
    }
  }
}
"""

GET_USERS = """
query GetUsers($first: Int!, $filter: UserFilter) {
  users(first: $first, filter: $filter, orderBy: name) {
    nodes {
      id
      name
      displayName
      email
      avatarUrl
      isMe
      isAdmin
      isGuest
      active
      createdAt
      lastSeen
      timezone
      teams {
        nodes {
          id
          name
          key
        }
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
"""

# Comment Queries
GET_COMMENTS = """
query GetComments($issueId: String!, $first: Int!) {
  issue(id: $issueId) {
    comments(first: $first, orderBy: createdAt) {
      nodes {
        id
        body
        createdAt
        updatedAt
        editedAt
        user {
          id
          name
          displayName
          avatarUrl
        }
        issue {
          id
          identifier
          title
        }
        parent {
          id
          body
        }
        children {
          nodes {
            id
            body
            user {
              name
              displayName
            }
          }
        }
      }
      pageInfo {
        hasNextPage
        endCursor
      }
    }
  }
}
"""

# Workflow State Queries
GET_WORKFLOW_STATES = """
query GetWorkflowStates($teamId: String!) {
  team(id: $teamId) {
    states {
      nodes {
        id
        name
        color
        type
        description
        position
        team {
          id
          name
        }
      }
    }
  }
}
"""

# Label Queries
GET_LABELS = """
query GetLabels($teamId: String!) {
  team(id: $teamId) {
    labels {
      nodes {
        id
        name
        color
        description
        isGroup
        parent {
          id
          name
        }
        children {
          nodes {
            id
            name
            color
          }
        }
      }
    }
  }
}
"""

# Organization Queries
GET_ORGANIZATION = """
query GetOrganization {
  organization {
    id
    name
    urlKey
    logoUrl
    createdAt
    updatedAt
    userCount
    userCountInOrg
    periodUploadVolume
    allowedAuthServices
    gitBranchFormat
    gitLinkbackMessagesEnabled
    gitPublicLinkbackMessagesEnabled
    roadmapEnabled
    projectUpdatesReminderFrequency
    teams {
      nodes {
        id
        name
        key
      }
    }
    users {
      nodes {
        id
        name
        displayName
        email
        isAdmin
      }
    }
  }
}
"""

# Cycle Queries
GET_CYCLES = """
query GetCycles($teamId: String!, $first: Int!) {
  team(id: $teamId) {
    cycles(first: $first, orderBy: number) {
      nodes {
        id
        name
        number
        description
        startsAt
        endsAt
        completedAt
        autoArchivedAt
        progress
        completedIssueCountHistory
        completedScopeHistory
        issueCountHistory
        scopeHistory
        team {
          id
          name
          key
        }
        issues {
          nodes {
            id
            identifier
            title
            estimate
            state {
              name
              type
            }
          }
        }
      }
      pageInfo {
        hasNextPage
        endCursor
      }
    }
  }
}
"""

# Webhook Queries
GET_WEBHOOKS = """
query GetWebhooks($first: Int!) {
  webhooks(first: $first) {
    nodes {
      id
      label
      url
      enabled
      secret
      resourceTypes
      createdAt
      updatedAt
      creator {
        id
        name
        displayName
      }
      team {
        id
        name
        key
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
"""

# Export all queries
LINEAR_QUERIES = {
    "GET_ISSUE": GET_ISSUE,
    "SEARCH_ISSUES": SEARCH_ISSUES,
    "GET_ISSUES_BY_TEAM": GET_ISSUES_BY_TEAM,
    "GET_PROJECTS": GET_PROJECTS,
    "GET_PROJECT": GET_PROJECT,
    "GET_TEAMS": GET_TEAMS,
    "GET_TEAM": GET_TEAM,
    "GET_TEAM_MEMBERS": GET_TEAM_MEMBERS,
    "GET_CURRENT_USER": GET_CURRENT_USER,
    "GET_USERS": GET_USERS,
    "GET_COMMENTS": GET_COMMENTS,
    "GET_WORKFLOW_STATES": GET_WORKFLOW_STATES,
    "GET_LABELS": GET_LABELS,
    "GET_ORGANIZATION": GET_ORGANIZATION,
    "GET_CYCLES": GET_CYCLES,
    "GET_WEBHOOKS": GET_WEBHOOKS,
}

