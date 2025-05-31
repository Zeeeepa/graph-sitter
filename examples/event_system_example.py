"""
Example usage of the Enhanced Event System
Core-7: Event System & Multi-Platform Integration
"""

import asyncio
import os
from datetime import datetime, timezone

from codegen.extensions.events.codegen_app import CodegenApp
from codegen.extensions.events.engine import EventPriority
from codegen.extensions.events.streaming import StreamFilter


async def main():
    """Example of using the enhanced event system."""
    
    # Configuration for the event system
    event_config = {
        'max_workers': 4,
        'queue_maxsize': 1000,
        'enable_correlation': True,
        'enable_streaming': True
    }
    
    # Database configuration (optional)
    database_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', '5432')),
        'database': os.getenv('DB_NAME', 'events'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', ''),
        'min_connections': 1,
        'max_connections': 10
    }
    
    # Create the enhanced CodegenApp
    app = CodegenApp(
        name="Enhanced Event System Example",
        event_config=event_config,
        database_config=database_config if all(database_config.values()) else None
    )
    
    # Example 1: Register custom event handlers
    @app.github.event("pull_request:opened")
    def handle_pr_opened(event):
        print(f"New PR opened: {event['pull_request']['title']}")
        
        # Submit a related deployment event
        app.submit_deployment_event(
            deployment_id=f"deploy-{event['pull_request']['number']}",
            environment="staging",
            status="pending",
            repository_name=event['repository']['full_name'],
            commit_sha=event['pull_request']['head']['sha'],
            branch_name=event['pull_request']['head']['ref']
        )
        
        return {"message": "PR opened event processed"}
    
    @app.linear.event("Issue")
    def handle_linear_issue(event):
        print(f"Linear issue event: {event.get('action', 'unknown')} - {event.get('data', {}).get('title', 'No title')}")
        return {"message": "Linear issue event processed"}
    
    @app.slack.event("app_mention")
    async def handle_slack_mention(event):
        print(f"Slack mention: {event.text}")
        
        # Example of submitting a custom high-priority event
        app.submit_custom_event(
            platform="internal",
            event_type="slack_mention_processed",
            payload={"original_event": event.text, "processed_at": datetime.now(timezone.utc).isoformat()},
            priority=EventPriority.HIGH
        )
        
        return {"message": "Slack mention processed"}
    
    # Example 2: Subscribe to event streams
    def event_logger(event):
        """Log all events for monitoring."""
        print(f"[EVENT LOG] {event.platform}.{event.event_type} from {event.source_name}")
    
    def high_priority_alert(event):
        """Handle high priority events."""
        print(f"[ALERT] High priority event: {event.platform}.{event.event_type}")
    
    # Subscribe to all events
    all_events_sub = app.subscribe_to_events(
        "all_events",
        event_logger,
        "example_logger"
    )
    
    # Subscribe to high priority events only
    high_priority_filter = {
        "custom_filters": {"priority": "high"}
    }
    high_priority_sub = app.subscribe_to_events(
        "high_priority",
        high_priority_alert,
        "alert_handler",
        high_priority_filter
    )
    
    # Example 3: Simulate some events
    print("Simulating events...")
    
    # Simulate a GitHub PR event
    github_event = {
        "action": "opened",
        "pull_request": {
            "number": 123,
            "title": "Add new feature",
            "head": {
                "sha": "abc123",
                "ref": "feature/new-feature"
            }
        },
        "repository": {
            "full_name": "example/repo",
            "id": 12345
        },
        "sender": {
            "login": "developer"
        }
    }
    
    await app.simulate_event("github", "pull_request:opened", github_event)
    
    # Simulate a Linear issue event
    linear_event = {
        "type": "Issue",
        "action": "create",
        "data": {
            "id": "issue-456",
            "title": "Fix bug in authentication",
            "teamId": "team-789",
            "team": {"name": "Backend Team"}
        },
        "updatedById": "user-123"
    }
    
    await app.simulate_event("linear", "Issue", linear_event)
    
    # Simulate a Slack mention event
    slack_event = {
        "type": "event_callback",
        "event": {
            "type": "app_mention",
            "text": "<@U123456> please review the PR",
            "user": "U789012",
            "channel": "C345678",
            "ts": "1234567890.123456"
        },
        "team_id": "T123456",
        "team_domain": "example"
    }
    
    await app.simulate_event("slack", "app_mention", slack_event)
    
    # Wait a bit for processing
    await asyncio.sleep(2)
    
    # Example 4: Check metrics and recent events
    print("\n=== Event Metrics ===")
    metrics = app.get_event_metrics()
    print(f"Processing metrics: {metrics['processing']}")
    print(f"Queue status: {metrics['queue']}")
    print(f"Streaming stats: {metrics['streaming']}")
    
    print("\n=== Recent Events ===")
    recent_events = app.get_recent_events(limit=10)
    for event in recent_events:
        print(f"- {event['platform']}.{event['event_type']} at {event['created_at']}")
    
    # Example 5: Submit deployment events
    print("\n=== Deployment Events ===")
    
    # Simulate deployment pipeline
    deployment_id = "deploy-123"
    repo_name = "example/repo"
    commit_sha = "abc123"
    
    # Deployment started
    app.submit_deployment_event(
        deployment_id=deployment_id,
        environment="production",
        status="in_progress",
        repository_name=repo_name,
        commit_sha=commit_sha,
        branch_name="main",
        deployment_url="https://deploy.example.com/123"
    )
    
    # Simulate some processing time
    await asyncio.sleep(1)
    
    # Deployment completed
    app.submit_deployment_event(
        deployment_id=deployment_id,
        environment="production",
        status="success",
        repository_name=repo_name,
        commit_sha=commit_sha,
        branch_name="main",
        deployment_url="https://deploy.example.com/123",
        log_url="https://logs.example.com/123"
    )
    
    # Wait for final processing
    await asyncio.sleep(2)
    
    # Final metrics
    print("\n=== Final Metrics ===")
    final_metrics = app.get_event_metrics()
    print(f"Total events processed: {final_metrics['processing'].get('events_processed', 0)}")
    print(f"Events failed: {final_metrics['processing'].get('events_failed', 0)}")
    
    # Cleanup
    app.unsubscribe_from_events(all_events_sub)
    app.unsubscribe_from_events(high_priority_sub)
    app.cleanup()
    
    print("\nExample completed!")


if __name__ == "__main__":
    asyncio.run(main())

