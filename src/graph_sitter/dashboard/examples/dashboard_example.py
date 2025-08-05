#!/usr/bin/env python3
"""
Linear & GitHub Dashboard Example

This script demonstrates how to use the dashboard programmatically
and showcases the main features and integrations.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the src directory to the Python path
src_path = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(src_path))

from graph_sitter.dashboard.services import (
    GitHubService, 
    LinearService, 
    RequirementsService, 
    ChatService, 
    WebhookService
)
from graph_sitter.dashboard.utils.config import DashboardConfig
from graph_sitter.dashboard.utils.logger import configure_dashboard_logging


async def main():
    """Main example function demonstrating dashboard capabilities."""
    
    print("🚀 Linear & GitHub Dashboard Example")
    print("=" * 50)
    
    # Configure logging
    configure_dashboard_logging("INFO")
    
    # Load configuration
    config = DashboardConfig.from_env()
    
    # Check configuration
    missing_keys = config.get_missing_keys()
    if missing_keys:
        print(f"⚠️  Missing API keys: {', '.join(missing_keys)}")
        print("Please set the following environment variables:")
        for key in missing_keys:
            env_var = key.upper().replace("_TOKEN", "_ACCESS_TOKEN")
            print(f"  - {env_var}")
        print()
    
    # Initialize services
    services = {}
    
    if config.github_token:
        services['github'] = GitHubService(config.github_token)
        print("✅ GitHub service initialized")
    else:
        print("❌ GitHub service not available (no token)")
    
    if config.linear_token:
        services['linear'] = LinearService(config.linear_token)
        print("✅ Linear service initialized")
    else:
        print("❌ Linear service not available (no token)")
    
    if config.anthropic_api_key:
        services['chat'] = ChatService(config.anthropic_api_key)
        print("✅ Chat service initialized")
    else:
        print("❌ Chat service not available (no API key)")
    
    if config.github_token:
        services['requirements'] = RequirementsService(config.github_token)
        print("✅ Requirements service initialized")
    
    services['webhook'] = WebhookService()
    print("✅ Webhook service initialized")
    
    print()
    
    # Demonstrate GitHub integration
    if 'github' in services:
        await demo_github_integration(services['github'], config)
    
    # Demonstrate Linear integration
    if 'linear' in services:
        await demo_linear_integration(services['linear'])
    
    # Demonstrate Requirements management
    if 'requirements' in services:
        await demo_requirements_management(services['requirements'])
    
    # Demonstrate Chat interface
    if 'chat' in services:
        await demo_chat_interface(services['chat'])
    
    # Demonstrate Webhook configuration
    await demo_webhook_configuration(services['webhook'])
    
    print("🎉 Dashboard example completed!")


async def demo_github_integration(github_service: GitHubService, config: DashboardConfig):
    """Demonstrate GitHub integration capabilities."""
    print("📊 GitHub Integration Demo")
    print("-" * 30)
    
    try:
        # Fetch projects
        print("Fetching GitHub projects...")
        projects = await github_service.get_all_projects(
            organization=config.github_organization,
            include_forks=False,
            include_archived=False
        )
        
        print(f"Found {len(projects)} projects")
        
        # Show top 5 projects
        if projects:
            print("\nTop 5 projects:")
            for i, project in enumerate(projects[:5]):
                print(f"  {i+1}. {project.name} ({project.primary_language}) - ⭐ {project.stars_count}")
                
            # Demonstrate project details
            first_project = projects[0]
            print(f"\nProject details for '{first_project.name}':")
            print(f"  - Description: {first_project.description}")
            print(f"  - URL: {first_project.url}")
            print(f"  - Stars: {first_project.stars_count}")
            print(f"  - Forks: {first_project.forks_count}")
            print(f"  - Open Issues: {first_project.open_issues_count}")
            
            # Get branches
            print(f"\nFetching branches for '{first_project.name}'...")
            branches = await github_service.get_project_branches(first_project.full_name)
            print(f"Found {len(branches)} branches:")
            for branch in branches[:3]:  # Show first 3
                print(f"  - {branch.name} {'(default)' if branch.is_default else ''}")
                
            # Get pull requests
            print(f"\nFetching pull requests for '{first_project.name}'...")
            prs = await github_service.get_project_pull_requests(first_project.full_name)
            print(f"Found {len(prs)} open pull requests:")
            for pr in prs[:3]:  # Show first 3
                print(f"  - #{pr.number}: {pr.title} by {pr.author}")
        
    except Exception as e:
        print(f"Error in GitHub demo: {e}")
    
    print()


async def demo_linear_integration(linear_service: LinearService):
    """Demonstrate Linear integration capabilities."""
    print("📋 Linear Integration Demo")
    print("-" * 30)
    
    try:
        # Fetch teams
        print("Fetching Linear teams...")
        teams = await linear_service.get_teams()
        print(f"Found {len(teams)} teams:")
        
        for team in teams[:3]:  # Show first 3
            print(f"  - {team['name']} ({team['key']})")
            if team.get('activeCycle'):
                cycle = team['activeCycle']
                print(f"    Active cycle: {cycle['name']}")
        
        # Fetch issues
        if teams:
            first_team = teams[0]
            print(f"\nFetching issues for team '{first_team['name']}'...")
            issues = await linear_service.get_issues(
                team_id=first_team['id'],
                limit=5
            )
            print(f"Found {len(issues)} issues:")
            
            for issue in issues:
                print(f"  - {issue['identifier']}: {issue['title']}")
                print(f"    Status: {issue['state']['name']}")
                if issue.get('assignee'):
                    print(f"    Assignee: {issue['assignee']['name']}")
        
        # Fetch projects
        print(f"\nFetching Linear projects...")
        projects = await linear_service.get_projects()
        print(f"Found {len(projects)} projects:")
        
        for project in projects[:3]:  # Show first 3
            print(f"  - {project['name']}: {project['state']}")
            if project.get('lead'):
                print(f"    Lead: {project['lead']['name']}")
        
    except Exception as e:
        print(f"Error in Linear demo: {e}")
    
    print()


async def demo_requirements_management(requirements_service: RequirementsService):
    """Demonstrate requirements management capabilities."""
    print("📝 Requirements Management Demo")
    print("-" * 30)
    
    try:
        # Get available templates
        print("Available requirements templates:")
        templates = await requirements_service.get_requirements_templates()
        
        for template in templates:
            print(f"  - {template.name}: {template.description}")
            print(f"    Sections: {', '.join(template.sections)}")
        
        # Example: Check if a project has requirements
        example_project = "example/project"  # This would be a real project ID
        print(f"\nChecking requirements for project '{example_project}'...")
        
        requirements = await requirements_service.get_requirements(example_project)
        if requirements:
            print(f"  ✅ Requirements found (version {requirements.version})")
            print(f"  - Title: {requirements.title}")
            print(f"  - Status: {requirements.status}")
            print(f"  - Functional requirements: {len(requirements.functional_requirements)}")
            print(f"  - Non-functional requirements: {len(requirements.non_functional_requirements)}")
        else:
            print(f"  ❌ No requirements found for this project")
        
    except Exception as e:
        print(f"Error in requirements demo: {e}")
    
    print()


async def demo_chat_interface(chat_service: ChatService):
    """Demonstrate AI chat interface capabilities."""
    print("💬 AI Chat Interface Demo")
    print("-" * 30)
    
    try:
        # Create a chat session
        print("Creating chat session...")
        session = await chat_service.create_session(
            project_id="example/project",
            context={"demo": True}
        )
        print(f"Created session: {session.session_id}")
        
        # Send a test message
        print("\nSending test message...")
        test_message = "What are the key considerations for a web application project?"
        response = await chat_service.send_message(
            session.session_id,
            test_message,
            include_code_analysis=False
        )
        
        print(f"User: {test_message}")
        print(f"AI: {response}")
        
        # Get code analysis
        print(f"\nGetting code analysis...")
        analysis = await chat_service.get_code_analysis("example/project")
        if analysis:
            print(f"Analysis summary: {analysis['summary']}")
            print(f"Recommendations: {len(analysis['recommendations'])}")
        
        # Generate requirements prompt
        print(f"\nGenerating requirements prompt...")
        prompt = await chat_service.generate_requirements_prompt(
            "example/project",
            "A web application for project management"
        )
        print(f"Generated prompt (first 200 chars): {prompt[:200]}...")
        
        # Clean up session
        await chat_service.clear_session(session.session_id)
        print("Session cleaned up")
        
    except Exception as e:
        print(f"Error in chat demo: {e}")
    
    print()


async def demo_webhook_configuration(webhook_service: WebhookService):
    """Demonstrate webhook configuration capabilities."""
    print("🔗 Webhook Configuration Demo")
    print("-" * 30)
    
    try:
        from graph_sitter.dashboard.models.webhook import WebhookEventType
        
        # Register a webhook
        print("Registering webhook configuration...")
        config = await webhook_service.register_webhook(
            project_id="example/project",
            webhook_url="https://example.com/webhook",
            events=[WebhookEventType.PULL_REQUEST, WebhookEventType.PUSH],
            secret="demo-secret"
        )
        
        print(f"Webhook registered:")
        print(f"  - Project: {config.project_id}")
        print(f"  - URL: {config.webhook_url}")
        print(f"  - Events: {[e.value for e in config.events]}")
        print(f"  - Active: {config.active}")
        
        # Get webhook configuration
        print(f"\nRetrieving webhook configuration...")
        retrieved_config = await webhook_service.get_webhook_config("example/project")
        if retrieved_config:
            print(f"Configuration found for project: {retrieved_config.project_id}")
        
        # Simulate webhook event processing
        print(f"\nSimulating GitHub webhook event...")
        test_payload = {
            "action": "opened",
            "repository": {
                "id": 12345,
                "full_name": "example/project"
            },
            "sender": {
                "login": "demo-user"
            },
            "pull_request": {
                "number": 1,
                "title": "Test PR"
            }
        }
        
        test_headers = {
            "X-GitHub-Event": "pull_request"
        }
        
        event = await webhook_service.process_github_webhook(
            test_payload, 
            test_headers, 
            "example/project"
        )
        
        if event:
            print(f"Webhook event processed:")
            print(f"  - Event ID: {event.id}")
            print(f"  - Type: {event.event_type}")
            print(f"  - Action: {event.action}")
            print(f"  - Repository: {event.repository_name}")
        
        # Clean up
        await webhook_service.unregister_webhook("example/project")
        print("Webhook configuration cleaned up")
        
    except Exception as e:
        print(f"Error in webhook demo: {e}")
    
    print()


if __name__ == "__main__":
    # Check if required environment variables are set
    required_vars = ["GITHUB_ACCESS_TOKEN"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"  - {var}")
        print("\nPlease set these variables and try again.")
        sys.exit(1)
    
    # Run the example
    asyncio.run(main())

