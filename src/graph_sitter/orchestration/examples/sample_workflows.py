"""
Sample Workflows

Example workflow configurations for common use cases.
"""

from datetime import timedelta
from ..workflow.models import Workflow, WorkflowStep
from ..triggers.models import Trigger, TriggerCondition, TriggerAction, ConditionOperator, TriggerType


def create_pr_review_workflow() -> Workflow:
    """Create a comprehensive PR review workflow"""
    workflow = Workflow(
        id="comprehensive_pr_review",
        name="Comprehensive PR Review",
        description="Automated comprehensive review of GitHub pull requests",
        max_concurrent_executions=3,
        timeout=timedelta(minutes=30)
    )
    
    # Step 1: Fetch PR details
    fetch_pr = WorkflowStep(
        id="fetch_pr",
        name="Fetch PR Details",
        action="github.get_pr",
        parameters={
            "owner": "${repository.owner}",
            "repo": "${repository.name}",
            "pr_number": "${pr_number}"
        }
    )
    
    # Step 2: Analyze code changes
    analyze_code = WorkflowStep(
        id="analyze_code",
        name="Analyze Code Changes",
        action="codegen.analyze_pr",
        dependencies=["fetch_pr"],
        parameters={
            "pr_data": "${fetch_pr.result}",
            "analysis_depth": "comprehensive"
        },
        timeout=timedelta(minutes=10)
    )
    
    # Step 3: Check for security issues
    security_check = WorkflowStep(
        id="security_check",
        name="Security Analysis",
        action="codegen.security_scan",
        dependencies=["fetch_pr"],
        parameters={
            "pr_data": "${fetch_pr.result}",
            "scan_type": "full"
        },
        timeout=timedelta(minutes=5)
    )
    
    # Step 4: Performance analysis
    performance_check = WorkflowStep(
        id="performance_check",
        name="Performance Analysis",
        action="codegen.performance_analysis",
        dependencies=["analyze_code"],
        parameters={
            "code_analysis": "${analyze_code.result}",
            "baseline_metrics": "${repository.performance_baseline}"
        },
        timeout=timedelta(minutes=5)
    )
    
    # Step 5: Generate review comments
    generate_review = WorkflowStep(
        id="generate_review",
        name="Generate Review Comments",
        action="codegen.generate_review",
        dependencies=["analyze_code", "security_check", "performance_check"],
        parameters={
            "code_analysis": "${analyze_code.result}",
            "security_findings": "${security_check.result}",
            "performance_findings": "${performance_check.result}",
            "review_style": "constructive"
        }
    )
    
    # Step 6: Post review to GitHub
    post_review = WorkflowStep(
        id="post_review",
        name="Post Review to GitHub",
        action="github.create_review",
        dependencies=["generate_review"],
        parameters={
            "owner": "${repository.owner}",
            "repo": "${repository.name}",
            "pr_number": "${pr_number}",
            "review_data": "${generate_review.result}"
        },
        max_retries=2
    )
    
    # Step 7: Notify in Slack (optional)
    slack_notification = WorkflowStep(
        id="slack_notification",
        name="Slack Notification",
        action="slack.send_message",
        dependencies=["post_review"],
        parameters={
            "channel": "#code-reviews",
            "message": "🔍 Automated review completed for PR #${pr_number}: ${fetch_pr.result.title}"
        },
        condition="${notify_slack}",
        on_failure="skip"
    )
    
    # Add all steps to workflow
    for step in [fetch_pr, analyze_code, security_check, performance_check, 
                 generate_review, post_review, slack_notification]:
        workflow.add_step(step)
    
    return workflow


def create_issue_sync_workflow() -> Workflow:
    """Create a GitHub to Linear issue sync workflow"""
    workflow = Workflow(
        id="github_linear_sync",
        name="GitHub to Linear Issue Sync",
        description="Sync GitHub issues to Linear with proper mapping",
        max_concurrent_executions=5
    )
    
    # Step 1: Fetch GitHub issue
    fetch_issue = WorkflowStep(
        id="fetch_github_issue",
        name="Fetch GitHub Issue",
        action="github.get_issue",
        parameters={
            "owner": "${repository.owner}",
            "repo": "${repository.name}",
            "issue_number": "${issue_number}"
        }
    )
    
    # Step 2: Map labels to Linear
    map_labels = WorkflowStep(
        id="map_labels",
        name="Map Labels to Linear",
        action="linear.map_labels",
        dependencies=["fetch_github_issue"],
        parameters={
            "github_labels": "${fetch_github_issue.result.labels}",
            "mapping_config": "${label_mapping}"
        }
    )
    
    # Step 3: Determine priority
    determine_priority = WorkflowStep(
        id="determine_priority",
        name="Determine Priority",
        action="linear.calculate_priority",
        dependencies=["fetch_github_issue"],
        parameters={
            "issue_data": "${fetch_github_issue.result}",
            "priority_rules": "${priority_mapping}"
        }
    )
    
    # Step 4: Create Linear issue
    create_linear_issue = WorkflowStep(
        id="create_linear_issue",
        name="Create Linear Issue",
        action="linear.create_issue",
        dependencies=["fetch_github_issue", "map_labels", "determine_priority"],
        parameters={
            "title": "${fetch_github_issue.result.title}",
            "description": "Synced from GitHub: ${fetch_github_issue.result.html_url}\n\n${fetch_github_issue.result.body}",
            "team_id": "${linear_team_id}",
            "priority": "${determine_priority.result}",
            "labels": "${map_labels.result}"
        }
    )
    
    # Step 5: Link issues
    link_issues = WorkflowStep(
        id="link_issues",
        name="Link GitHub and Linear Issues",
        action="github.add_comment",
        dependencies=["create_linear_issue"],
        parameters={
            "owner": "${repository.owner}",
            "repo": "${repository.name}",
            "issue_number": "${issue_number}",
            "comment": "🔗 Linked to Linear: ${create_linear_issue.result.url}"
        }
    )
    
    # Add steps to workflow
    for step in [fetch_issue, map_labels, determine_priority, create_linear_issue, link_issues]:
        workflow.add_step(step)
    
    return workflow


def create_deployment_workflow() -> Workflow:
    """Create a deployment notification workflow"""
    workflow = Workflow(
        id="deployment_notifications",
        name="Deployment Notifications",
        description="Notify stakeholders about deployments across platforms"
    )
    
    # Step 1: Validate deployment
    validate_deployment = WorkflowStep(
        id="validate_deployment",
        name="Validate Deployment",
        action="deployment.validate",
        parameters={
            "environment": "${environment}",
            "version": "${version}",
            "health_checks": ["api", "database", "cache"]
        },
        timeout=timedelta(minutes=5)
    )
    
    # Step 2: Update Linear issues
    update_linear = WorkflowStep(
        id="update_linear_issues",
        name="Update Related Linear Issues",
        action="linear.update_deployed_issues",
        dependencies=["validate_deployment"],
        parameters={
            "version": "${version}",
            "environment": "${environment}",
            "deployment_status": "${validate_deployment.result.status}"
        },
        condition="${validate_deployment.result.success}"
    )
    
    # Step 3: Slack notification
    slack_notification = WorkflowStep(
        id="slack_deployment_notification",
        name="Slack Deployment Notification",
        action="slack.send_message",
        dependencies=["validate_deployment"],
        parameters={
            "channel": "#deployments",
            "message": "🚀 Deployment ${version} to ${environment}: ${validate_deployment.result.status}",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*Deployment Complete*\n• Version: `${version}`\n• Environment: `${environment}`\n• Status: ${validate_deployment.result.status}"
                    }
                }
            ]
        }
    )
    
    # Step 4: GitHub release (for production)
    create_release = WorkflowStep(
        id="create_github_release",
        name="Create GitHub Release",
        action="github.create_release",
        dependencies=["validate_deployment"],
        parameters={
            "owner": "${repository.owner}",
            "repo": "${repository.name}",
            "tag_name": "${version}",
            "name": "Release ${version}",
            "body": "Deployed to ${environment}\n\n${release_notes}"
        },
        condition="${environment} == 'production' and ${validate_deployment.result.success}"
    )
    
    # Add steps to workflow
    for step in [validate_deployment, update_linear, slack_notification, create_release]:
        workflow.add_step(step)
    
    return workflow


def create_sample_triggers() -> list[Trigger]:
    """Create sample triggers for common scenarios"""
    triggers = []
    
    # PR Review Trigger
    pr_review_trigger = Trigger(
        id="auto_pr_review",
        name="Automatic PR Review",
        description="Trigger comprehensive review when PR is opened",
        trigger_type=TriggerType.EVENT,
        event_types=["github.pr.opened"],
        platforms=["github"]
    )
    
    # Add conditions
    pr_review_trigger.add_condition(
        TriggerCondition(
            field="event.data.draft",
            operator=ConditionOperator.EQUALS,
            value=False
        )
    )
    
    pr_review_trigger.add_condition(
        TriggerCondition(
            field="event.data.base.ref",
            operator=ConditionOperator.IN_LIST,
            value=["main", "master", "develop"]
        )
    )
    
    # Add action
    pr_review_trigger.add_action(
        TriggerAction(
            action_type="workflow",
            parameters={
                "workflow_id": "comprehensive_pr_review",
                "pr_number": "${event.data.number}",
                "repository": "${event.data.repository}",
                "notify_slack": True
            }
        )
    )
    
    triggers.append(pr_review_trigger)
    
    # Issue Sync Trigger
    issue_sync_trigger = Trigger(
        id="github_linear_sync_trigger",
        name="GitHub to Linear Sync",
        description="Sync GitHub issues to Linear when labeled",
        trigger_type=TriggerType.EVENT,
        event_types=["github.issue.opened", "github.issue.labeled"],
        platforms=["github"]
    )
    
    issue_sync_trigger.add_condition(
        TriggerCondition(
            field="event.data.labels",
            operator=ConditionOperator.CONTAINS,
            value="sync-to-linear"
        )
    )
    
    issue_sync_trigger.add_action(
        TriggerAction(
            action_type="workflow",
            parameters={
                "workflow_id": "github_linear_sync",
                "issue_number": "${event.data.number}",
                "repository": "${event.data.repository}",
                "linear_team_id": "team_123",
                "label_mapping": {
                    "bug": "bug",
                    "enhancement": "feature",
                    "documentation": "docs"
                },
                "priority_mapping": {
                    "critical": 1,
                    "high": 2,
                    "medium": 3,
                    "low": 4
                }
            }
        )
    )
    
    triggers.append(issue_sync_trigger)
    
    # Deployment Trigger
    deployment_trigger = Trigger(
        id="deployment_notifications_trigger",
        name="Deployment Notifications",
        description="Notify about successful deployments",
        trigger_type=TriggerType.EVENT,
        event_types=["deployment.completed"],
        platforms=["deployment"]
    )
    
    deployment_trigger.add_condition(
        TriggerCondition(
            field="event.data.status",
            operator=ConditionOperator.EQUALS,
            value="success"
        )
    )
    
    deployment_trigger.add_action(
        TriggerAction(
            action_type="workflow",
            parameters={
                "workflow_id": "deployment_notifications",
                "environment": "${event.data.environment}",
                "version": "${event.data.version}",
                "repository": "${event.data.repository}",
                "release_notes": "${event.data.release_notes}"
            }
        )
    )
    
    triggers.append(deployment_trigger)
    
    return triggers


# Export sample configurations
SAMPLE_WORKFLOWS = [
    create_pr_review_workflow(),
    create_issue_sync_workflow(),
    create_deployment_workflow()
]

SAMPLE_TRIGGERS = create_sample_triggers()

