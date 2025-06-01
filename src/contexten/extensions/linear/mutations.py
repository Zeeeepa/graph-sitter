"""
Linear GraphQL Mutations

This module contains all GraphQL mutations for the Linear API.
"""

# Issue Mutations
CREATE_ISSUE = """
mutation CreateIssue($input: IssueCreateInput!) {
  issueCreate(input: $input) {
    success
    issue {
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
    lastSyncId
  }
}
"""

UPDATE_ISSUE = """
mutation UpdateIssue($id: String!, $input: IssueUpdateInput!) {
  issueUpdate(id: $id, input: $input) {
    success
    issue {
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
    lastSyncId
  }
}
"""

DELETE_ISSUE = """
mutation DeleteIssue($id: String!) {
  issueDelete(id: $id) {
    success
    lastSyncId
  }
}
"""

ARCHIVE_ISSUE = """
mutation ArchiveIssue($id: String!) {
  issueArchive(id: $id) {
    success
    issue {
      id
      identifier
      title
      archivedAt
    }
    lastSyncId
  }
}
"""

UNARCHIVE_ISSUE = """
mutation UnarchiveIssue($id: String!) {
  issueUnarchive(id: $id) {
    success
    issue {
      id
      identifier
      title
      archivedAt
    }
    lastSyncId
  }
}
"""

# Comment Mutations
CREATE_COMMENT = """
mutation CreateComment($input: CommentCreateInput!) {
  commentCreate(input: $input) {
    success
    comment {
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
      issue {
        id
        identifier
        title
      }
      parent {
        id
        body
      }
    }
    lastSyncId
  }
}
"""

UPDATE_COMMENT = """
mutation UpdateComment($id: String!, $input: CommentUpdateInput!) {
  commentUpdate(id: $id, input: $input) {
    success
    comment {
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
    }
    lastSyncId
  }
}
"""

DELETE_COMMENT = """
mutation DeleteComment($id: String!) {
  commentDelete(id: $id) {
    success
    lastSyncId
  }
}
"""

# Project Mutations
CREATE_PROJECT = """
mutation CreateProject($input: ProjectCreateInput!) {
  projectCreate(input: $input) {
    success
    project {
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
      slugId
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
      }
      members {
        nodes {
          id
          name
          displayName
          avatarUrl
        }
      }
    }
    lastSyncId
  }
}
"""

UPDATE_PROJECT = """
mutation UpdateProject($id: String!, $input: ProjectUpdateInput!) {
  projectUpdate(id: $id, input: $input) {
    success
    project {
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
    }
    lastSyncId
  }
}
"""

DELETE_PROJECT = """
mutation DeleteProject($id: String!) {
  projectDelete(id: $id) {
    success
    lastSyncId
  }
}
"""

ARCHIVE_PROJECT = """
mutation ArchiveProject($id: String!) {
  projectArchive(id: $id) {
    success
    project {
      id
      name
      state
      completedAt
    }
    lastSyncId
  }
}
"""

# Team Mutations
CREATE_TEAM = """
mutation CreateTeam($input: TeamCreateInput!) {
  teamCreate(input: $input) {
    success
    team {
      id
      name
      key
      description
      icon
      color
      private
      createdAt
      updatedAt
      organization {
        id
        name
      }
    }
    lastSyncId
  }
}
"""

UPDATE_TEAM = """
mutation UpdateTeam($id: String!, $input: TeamUpdateInput!) {
  teamUpdate(id: $id, input: $input) {
    success
    team {
      id
      name
      key
      description
      icon
      color
      private
      updatedAt
    }
    lastSyncId
  }
}
"""

DELETE_TEAM = """
mutation DeleteTeam($id: String!) {
  teamDelete(id: $id) {
    success
    lastSyncId
  }
}
"""

# Team Membership Mutations
CREATE_TEAM_MEMBERSHIP = """
mutation CreateTeamMembership($input: TeamMembershipCreateInput!) {
  teamMembershipCreate(input: $input) {
    success
    teamMembership {
      id
      user {
        id
        name
        displayName
        email
      }
      team {
        id
        name
        key
      }
      owner
      sortOrder
    }
    lastSyncId
  }
}
"""

UPDATE_TEAM_MEMBERSHIP = """
mutation UpdateTeamMembership($id: String!, $input: TeamMembershipUpdateInput!) {
  teamMembershipUpdate(id: $id, input: $input) {
    success
    teamMembership {
      id
      user {
        id
        name
        displayName
      }
      team {
        id
        name
        key
      }
      owner
      sortOrder
    }
    lastSyncId
  }
}
"""

DELETE_TEAM_MEMBERSHIP = """
mutation DeleteTeamMembership($id: String!) {
  teamMembershipDelete(id: $id) {
    success
    lastSyncId
  }
}
"""

# Label Mutations
CREATE_ISSUE_LABEL = """
mutation CreateIssueLabel($input: IssueLabelCreateInput!) {
  issueLabelCreate(input: $input) {
    success
    issueLabel {
      id
      name
      color
      description
      isGroup
      team {
        id
        name
        key
      }
      creator {
        id
        name
        displayName
      }
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
    lastSyncId
  }
}
"""

UPDATE_ISSUE_LABEL = """
mutation UpdateIssueLabel($id: String!, $input: IssueLabelUpdateInput!) {
  issueLabelUpdate(id: $id, input: $input) {
    success
    issueLabel {
      id
      name
      color
      description
      isGroup
      team {
        id
        name
        key
      }
    }
    lastSyncId
  }
}
"""

DELETE_ISSUE_LABEL = """
mutation DeleteIssueLabel($id: String!) {
  issueLabelDelete(id: $id) {
    success
    lastSyncId
  }
}
"""

# Workflow State Mutations
CREATE_WORKFLOW_STATE = """
mutation CreateWorkflowState($input: WorkflowStateCreateInput!) {
  workflowStateCreate(input: $input) {
    success
    workflowState {
      id
      name
      color
      type
      description
      position
      team {
        id
        name
        key
      }
    }
    lastSyncId
  }
}
"""

UPDATE_WORKFLOW_STATE = """
mutation UpdateWorkflowState($id: String!, $input: WorkflowStateUpdateInput!) {
  workflowStateUpdate(id: $id, input: $input) {
    success
    workflowState {
      id
      name
      color
      type
      description
      position
      team {
        id
        name
        key
      }
    }
    lastSyncId
  }
}
"""

DELETE_WORKFLOW_STATE = """
mutation DeleteWorkflowState($id: String!) {
  workflowStateDelete(id: $id) {
    success
    lastSyncId
  }
}
"""

# Cycle Mutations
CREATE_CYCLE = """
mutation CreateCycle($input: CycleCreateInput!) {
  cycleCreate(input: $input) {
    success
    cycle {
      id
      name
      number
      description
      startsAt
      endsAt
      team {
        id
        name
        key
      }
    }
    lastSyncId
  }
}
"""

UPDATE_CYCLE = """
mutation UpdateCycle($id: String!, $input: CycleUpdateInput!) {
  cycleUpdate(id: $id, input: $input) {
    success
    cycle {
      id
      name
      number
      description
      startsAt
      endsAt
      completedAt
      autoArchivedAt
      team {
        id
        name
        key
      }
    }
    lastSyncId
  }
}
"""

ARCHIVE_CYCLE = """
mutation ArchiveCycle($id: String!) {
  cycleArchive(id: $id) {
    success
    cycle {
      id
      name
      number
      completedAt
      autoArchivedAt
    }
    lastSyncId
  }
}
"""

# Webhook Mutations
CREATE_WEBHOOK = """
mutation CreateWebhook($input: WebhookCreateInput!) {
  webhookCreate(input: $input) {
    success
    webhook {
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
    lastSyncId
  }
}
"""

UPDATE_WEBHOOK = """
mutation UpdateWebhook($id: String!, $input: WebhookUpdateInput!) {
  webhookUpdate(id: $id, input: $input) {
    success
    webhook {
      id
      label
      url
      enabled
      secret
      resourceTypes
      updatedAt
      team {
        id
        name
        key
      }
    }
    lastSyncId
  }
}
"""

DELETE_WEBHOOK = """
mutation DeleteWebhook($id: String!) {
  webhookDelete(id: $id) {
    success
    lastSyncId
  }
}
"""

# Attachment Mutations
CREATE_ATTACHMENT = """
mutation CreateAttachment($input: AttachmentCreateInput!) {
  attachmentCreate(input: $input) {
    success
    attachment {
      id
      title
      url
      subtitle
      metadata
      createdAt
      updatedAt
      creator {
        id
        name
        displayName
      }
      issue {
        id
        identifier
        title
      }
    }
    lastSyncId
  }
}
"""

UPDATE_ATTACHMENT = """
mutation UpdateAttachment($id: String!, $input: AttachmentUpdateInput!) {
  attachmentUpdate(id: $id, input: $input) {
    success
    attachment {
      id
      title
      url
      subtitle
      metadata
      updatedAt
      issue {
        id
        identifier
        title
      }
    }
    lastSyncId
  }
}
"""

DELETE_ATTACHMENT = """
mutation DeleteAttachment($id: String!) {
  attachmentDelete(id: $id) {
    success
    lastSyncId
  }
}
"""

# Issue Relation Mutations
CREATE_ISSUE_RELATION = """
mutation CreateIssueRelation($input: IssueRelationCreateInput!) {
  issueRelationCreate(input: $input) {
    success
    issueRelation {
      id
      type
      issue {
        id
        identifier
        title
      }
      relatedIssue {
        id
        identifier
        title
      }
    }
    lastSyncId
  }
}
"""

UPDATE_ISSUE_RELATION = """
mutation UpdateIssueRelation($id: String!, $input: IssueRelationUpdateInput!) {
  issueRelationUpdate(id: $id, input: $input) {
    success
    issueRelation {
      id
      type
      issue {
        id
        identifier
        title
      }
      relatedIssue {
        id
        identifier
        title
      }
    }
    lastSyncId
  }
}
"""

DELETE_ISSUE_RELATION = """
mutation DeleteIssueRelation($id: String!) {
  issueRelationDelete(id: $id) {
    success
    lastSyncId
  }
}
"""

# User Settings Mutations
UPDATE_USER = """
mutation UpdateUser($id: String!, $input: UserUpdateInput!) {
  userUpdate(id: $id, input: $input) {
    success
    user {
      id
      name
      displayName
      email
      avatarUrl
      timezone
      updatedAt
    }
    lastSyncId
  }
}
"""

# Organization Mutations
UPDATE_ORGANIZATION = """
mutation UpdateOrganization($input: OrganizationUpdateInput!) {
  organizationUpdate(input: $input) {
    success
    organization {
      id
      name
      urlKey
      logoUrl
      updatedAt
      gitBranchFormat
      gitLinkbackMessagesEnabled
      gitPublicLinkbackMessagesEnabled
      roadmapEnabled
      projectUpdatesReminderFrequency
    }
    lastSyncId
  }
}
"""

# Export all mutations
LINEAR_MUTATIONS = {
    "CREATE_ISSUE": CREATE_ISSUE,
    "UPDATE_ISSUE": UPDATE_ISSUE,
    "DELETE_ISSUE": DELETE_ISSUE,
    "ARCHIVE_ISSUE": ARCHIVE_ISSUE,
    "UNARCHIVE_ISSUE": UNARCHIVE_ISSUE,
    "CREATE_COMMENT": CREATE_COMMENT,
    "UPDATE_COMMENT": UPDATE_COMMENT,
    "DELETE_COMMENT": DELETE_COMMENT,
    "CREATE_PROJECT": CREATE_PROJECT,
    "UPDATE_PROJECT": UPDATE_PROJECT,
    "DELETE_PROJECT": DELETE_PROJECT,
    "ARCHIVE_PROJECT": ARCHIVE_PROJECT,
    "CREATE_TEAM": CREATE_TEAM,
    "UPDATE_TEAM": UPDATE_TEAM,
    "DELETE_TEAM": DELETE_TEAM,
    "CREATE_TEAM_MEMBERSHIP": CREATE_TEAM_MEMBERSHIP,
    "UPDATE_TEAM_MEMBERSHIP": UPDATE_TEAM_MEMBERSHIP,
    "DELETE_TEAM_MEMBERSHIP": DELETE_TEAM_MEMBERSHIP,
    "CREATE_ISSUE_LABEL": CREATE_ISSUE_LABEL,
    "UPDATE_ISSUE_LABEL": UPDATE_ISSUE_LABEL,
    "DELETE_ISSUE_LABEL": DELETE_ISSUE_LABEL,
    "CREATE_WORKFLOW_STATE": CREATE_WORKFLOW_STATE,
    "UPDATE_WORKFLOW_STATE": UPDATE_WORKFLOW_STATE,
    "DELETE_WORKFLOW_STATE": DELETE_WORKFLOW_STATE,
    "CREATE_CYCLE": CREATE_CYCLE,
    "UPDATE_CYCLE": UPDATE_CYCLE,
    "ARCHIVE_CYCLE": ARCHIVE_CYCLE,
    "CREATE_WEBHOOK": CREATE_WEBHOOK,
    "UPDATE_WEBHOOK": UPDATE_WEBHOOK,
    "DELETE_WEBHOOK": DELETE_WEBHOOK,
    "CREATE_ATTACHMENT": CREATE_ATTACHMENT,
    "UPDATE_ATTACHMENT": UPDATE_ATTACHMENT,
    "DELETE_ATTACHMENT": DELETE_ATTACHMENT,
    "CREATE_ISSUE_RELATION": CREATE_ISSUE_RELATION,
    "UPDATE_ISSUE_RELATION": UPDATE_ISSUE_RELATION,
    "DELETE_ISSUE_RELATION": DELETE_ISSUE_RELATION,
    "UPDATE_USER": UPDATE_USER,
    "UPDATE_ORGANIZATION": UPDATE_ORGANIZATION,
}

