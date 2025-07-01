#!/usr/bin/env python3
"""
Orchestrator Integration Example - Contexten + Codegen SDK + Autogenlib

This example demonstrates how the contexten orchestrator integrates with the
Codegen SDK + Autogenlib system for autonomous development workflows.
"""

import asyncio
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

# Mock imports for demonstration
# from contexten.extensions.codegen import CodegenAutogenIntegration
# from contexten.extensions.events import Event, EventResult
# from contexten.extensions.linear import LinearIntegration
# from contexten.extensions.github import GitHubIntegration


@dataclass
class TaskRequest:
    """Represents a development task request"""
    id: str
    title: str
    description: str
    priority: str
    assignee: str
    context: Dict[str, Any]
    created_at: datetime


@dataclass
class TaskResult:
    """Represents the result of a completed task"""
    task_id: str
    status: str
    generated_code: str
    files_modified: List[str]
    pr_url: Optional[str]
    execution_time: float
    method_used: str


class MockCodegenAutogenIntegration:
    """Mock integration for demonstration"""
    
    def __init__(self, config):
        self.config = config
        self._performance_stats = {
            "requests_processed": 0,
            "average_response_time": 1.2,
            "success_rate": 0.95
        }
    
    async def initialize(self):
        print("🚀 Initializing Codegen+Autogenlib integration...")
    
    async def generate_with_context(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate code with context enhancement"""
        await asyncio.sleep(0.8)  # Simulate processing
        
        self._performance_stats["requests_processed"] += 1
        
        return {
            "generated_code": f"# Generated for: {prompt}\nclass GeneratedClass:\n    pass",
            "files_modified": ["src/generated/new_feature.py"],
            "context_used": bool(kwargs.get('codebase_context')),
            "generation_time": 0.8,
            "method": "autogenlib" if not kwargs.get('use_codegen_agent') else "codegen_sdk"
        }
    
    async def run_agent_task(self, task_description: str, **kwargs) -> Dict[str, Any]:
        """Run complex agent task"""
        await asyncio.sleep(2.5)  # Simulate longer processing for complex tasks
        
        return {
            "result": f"Completed: {task_description}",
            "pr_url": "https://github.com/org/repo/pull/123",
            "files_modified": ["src/auth/login.py", "tests/test_auth.py"],
            "execution_time": 2.5,
            "method": "codegen_sdk_agent"
        }
    
    async def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        return self._performance_stats


class ContextenOrchestrator:
    """Main orchestrator class integrating all components"""
    
    def __init__(self):
        self.codegen_integration = None
        self.linear_integration = None
        self.github_integration = None
        self.task_queue = asyncio.Queue()
        self.active_tasks = {}
        self.completed_tasks = []
    
    async def initialize(self):
        """Initialize all integrations"""
        print("🎯 Initializing Contexten Orchestrator...")
        
        # Initialize Codegen+Autogenlib integration
        from research.examples.basic_integration import CodegenAutogenConfig
        config = CodegenAutogenConfig.from_env()
        self.codegen_integration = MockCodegenAutogenIntegration(config)
        await self.codegen_integration.initialize()
        
        # Mock other integrations
        print("📋 Linear integration initialized")
        print("🐙 GitHub integration initialized")
        print("✅ Orchestrator ready!")
    
    async def handle_linear_issue_assignment(self, issue_data: Dict[str, Any]) -> TaskResult:
        """Handle Linear issue assignment event"""
        print(f"\n📋 Processing Linear issue: {issue_data['title']}")
        
        # Create task request
        task = TaskRequest(
            id=issue_data['id'],
            title=issue_data['title'],
            description=issue_data['description'],
            priority=issue_data.get('priority', 'medium'),
            assignee=issue_data.get('assignee', 'codegen-bot'),
            context=issue_data.get('context', {}),
            created_at=datetime.now()
        )
        
        # Add to task queue
        await self.task_queue.put(task)
        
        # Process task
        result = await self._process_task(task)
        
        # Update Linear issue
        await self._update_linear_issue(task.id, result)
        
        return result
    
    async def handle_github_pr_review_request(self, pr_data: Dict[str, Any]) -> TaskResult:
        """Handle GitHub PR review request"""
        print(f"\n🐙 Processing PR review: {pr_data['title']}")
        
        # Create task for PR review
        task = TaskRequest(
            id=f"pr_{pr_data['number']}",
            title=f"Review PR: {pr_data['title']}",
            description=f"Review and provide feedback on PR #{pr_data['number']}",
            priority="high",
            assignee="codegen-bot",
            context={
                "pr_number": pr_data['number'],
                "files_changed": pr_data.get('files_changed', []),
                "diff": pr_data.get('diff', "")
            },
            created_at=datetime.now()
        )
        
        # Process PR review task
        result = await self._process_pr_review_task(task)
        
        # Post review comments
        await self._post_pr_review(pr_data['number'], result)
        
        return result
    
    async def handle_slack_code_request(self, message_data: Dict[str, Any]) -> TaskResult:
        """Handle Slack code generation request"""
        print(f"\n💬 Processing Slack request: {message_data['text'][:50]}...")
        
        # Create task from Slack message
        task = TaskRequest(
            id=f"slack_{message_data['timestamp']}",
            title="Slack Code Request",
            description=message_data['text'],
            priority="medium",
            assignee="codegen-bot",
            context={
                "channel": message_data.get('channel', 'general'),
                "user": message_data.get('user', 'unknown'),
                "thread_ts": message_data.get('thread_ts')
            },
            created_at=datetime.now()
        )
        
        # Process task with quick response
        result = await self._process_quick_task(task)
        
        # Send response to Slack
        await self._send_slack_response(message_data['channel'], result)
        
        return result
    
    async def _process_task(self, task: TaskRequest) -> TaskResult:
        """Process a development task using appropriate method"""
        print(f"🔄 Processing task: {task.title}")
        
        # Determine complexity and choose method
        is_complex = self._is_complex_task(task)
        
        if is_complex:
            # Use Codegen SDK agent for complex tasks
            print("🤖 Using Codegen SDK agent for complex task")
            result = await self.codegen_integration.run_agent_task(
                task_description=task.description,
                context=task.context
            )
            
            return TaskResult(
                task_id=task.id,
                status="completed",
                generated_code=result.get("result", ""),
                files_modified=result.get("files_modified", []),
                pr_url=result.get("pr_url"),
                execution_time=result.get("execution_time", 0),
                method_used=result.get("method", "codegen_sdk")
            )
        else:
            # Use autogenlib for simpler tasks
            print("⚡ Using autogenlib for quick generation")
            result = await self.codegen_integration.generate_with_context(
                prompt=task.description,
                codebase_context=task.context,
                use_codegen_agent=False
            )
            
            return TaskResult(
                task_id=task.id,
                status="completed",
                generated_code=result.get("generated_code", ""),
                files_modified=result.get("files_modified", []),
                pr_url=None,
                execution_time=result.get("generation_time", 0),
                method_used=result.get("method", "autogenlib")
            )
    
    async def _process_pr_review_task(self, task: TaskRequest) -> TaskResult:
        """Process PR review task"""
        print("🔍 Analyzing PR for review...")
        
        # Use Codegen SDK for PR analysis
        result = await self.codegen_integration.run_agent_task(
            task_description=f"Review PR and provide detailed feedback: {task.description}",
            context=task.context
        )
        
        return TaskResult(
            task_id=task.id,
            status="completed",
            generated_code="",  # No code generation for reviews
            files_modified=[],
            pr_url=None,
            execution_time=result.get("execution_time", 0),
            method_used="codegen_sdk_review"
        )
    
    async def _process_quick_task(self, task: TaskRequest) -> TaskResult:
        """Process quick task for immediate response"""
        print("⚡ Processing quick task...")
        
        # Use autogenlib for quick generation
        result = await self.codegen_integration.generate_with_context(
            prompt=task.description,
            codebase_context=task.context,
            use_codegen_agent=False
        )
        
        return TaskResult(
            task_id=task.id,
            status="completed",
            generated_code=result.get("generated_code", ""),
            files_modified=result.get("files_modified", []),
            pr_url=None,
            execution_time=result.get("generation_time", 0),
            method_used="autogenlib_quick"
        )
    
    def _is_complex_task(self, task: TaskRequest) -> bool:
        """Determine if task requires Codegen SDK agent"""
        complex_keywords = [
            "refactor", "architecture", "migrate", "implement feature",
            "create pr", "fix bug", "add tests", "deploy", "review"
        ]
        
        description_lower = task.description.lower()
        return any(keyword in description_lower for keyword in complex_keywords)
    
    async def _update_linear_issue(self, issue_id: str, result: TaskResult):
        """Update Linear issue with task result"""
        print(f"📋 Updating Linear issue {issue_id}")
        print(f"   Status: {result.status}")
        print(f"   Files modified: {len(result.files_modified)}")
        if result.pr_url:
            print(f"   PR created: {result.pr_url}")
    
    async def _post_pr_review(self, pr_number: int, result: TaskResult):
        """Post review comments on GitHub PR"""
        print(f"🐙 Posting review on PR #{pr_number}")
        print(f"   Review completed in {result.execution_time:.1f}s")
    
    async def _send_slack_response(self, channel: str, result: TaskResult):
        """Send response to Slack channel"""
        print(f"💬 Sending response to #{channel}")
        print(f"   Generated code: {len(result.generated_code)} characters")
        print(f"   Response time: {result.execution_time:.1f}s")
    
    async def start_task_processor(self):
        """Start background task processor"""
        print("🔄 Starting task processor...")
        
        while True:
            try:
                # Process tasks from queue
                task = await asyncio.wait_for(self.task_queue.get(), timeout=1.0)
                
                # Add to active tasks
                self.active_tasks[task.id] = task
                
                # Process task
                result = await self._process_task(task)
                
                # Move to completed tasks
                self.completed_tasks.append(result)
                del self.active_tasks[task.id]
                
                print(f"✅ Task {task.id} completed")
                
            except asyncio.TimeoutError:
                # No tasks in queue, continue
                continue
            except Exception as e:
                print(f"❌ Task processing error: {e}")
    
    async def get_orchestrator_stats(self) -> Dict[str, Any]:
        """Get orchestrator performance statistics"""
        codegen_stats = await self.codegen_integration.get_performance_stats()
        
        return {
            "active_tasks": len(self.active_tasks),
            "completed_tasks": len(self.completed_tasks),
            "queue_size": self.task_queue.qsize(),
            "codegen_stats": codegen_stats,
            "success_rate": 0.95,
            "average_task_time": 1.8
        }


async def demo_orchestrator_workflow():
    """Demonstrate complete orchestrator workflow"""
    
    print("🎯 Contexten Orchestrator Integration Demo")
    print("=" * 60)
    
    # Initialize orchestrator
    orchestrator = ContextenOrchestrator()
    await orchestrator.initialize()
    
    # Start background task processor
    processor_task = asyncio.create_task(orchestrator.start_task_processor())
    
    # Simulate various events
    print("\n🎬 Simulating development workflow events...")
    
    # 1. Linear issue assignment
    linear_issue = {
        "id": "LIN-123",
        "title": "Implement user authentication",
        "description": "Create a secure user authentication system with JWT tokens",
        "priority": "high",
        "assignee": "codegen-bot",
        "context": {
            "module": "auth",
            "requirements": ["JWT", "bcrypt", "rate limiting"]
        }
    }
    
    result1 = await orchestrator.handle_linear_issue_assignment(linear_issue)
    print(f"✅ Linear task completed: {result1.method_used} in {result1.execution_time:.1f}s")
    
    # 2. GitHub PR review request
    pr_data = {
        "number": 456,
        "title": "Add email validation",
        "files_changed": ["src/auth/validation.py", "tests/test_validation.py"],
        "diff": "... diff content ..."
    }
    
    result2 = await orchestrator.handle_github_pr_review_request(pr_data)
    print(f"✅ PR review completed: {result2.method_used} in {result2.execution_time:.1f}s")
    
    # 3. Slack code request
    slack_message = {
        "text": "Generate a function to validate email addresses with regex",
        "channel": "dev-team",
        "user": "developer1",
        "timestamp": "1234567890"
    }
    
    result3 = await orchestrator.handle_slack_code_request(slack_message)
    print(f"✅ Slack request completed: {result3.method_used} in {result3.execution_time:.1f}s")
    
    # Wait a moment for background processing
    await asyncio.sleep(1)
    
    # Get performance statistics
    stats = await orchestrator.get_orchestrator_stats()
    
    print("\n📊 Orchestrator Performance Statistics:")
    print(f"   - Active tasks: {stats['active_tasks']}")
    print(f"   - Completed tasks: {stats['completed_tasks']}")
    print(f"   - Success rate: {stats['success_rate']*100:.1f}%")
    print(f"   - Average task time: {stats['average_task_time']:.1f}s")
    print(f"   - Codegen requests: {stats['codegen_stats']['requests_processed']}")
    
    # Cancel background task
    processor_task.cancel()
    
    print("\n✅ Orchestrator demo completed successfully!")


async def demo_event_driven_patterns():
    """Demonstrate event-driven integration patterns"""
    
    print("\n" + "=" * 60)
    print("🔄 Event-Driven Integration Patterns")
    print("=" * 60)
    
    # Simulate event-driven workflow
    events = [
        {"type": "linear.issue.assigned", "data": {"id": "LIN-001", "title": "Fix login bug"}},
        {"type": "github.pr.opened", "data": {"number": 789, "title": "Feature: OAuth integration"}},
        {"type": "slack.mention", "data": {"text": "Create a REST API endpoint", "channel": "api-team"}},
        {"type": "github.push", "data": {"branch": "main", "files": ["src/api/auth.py"]}},
    ]
    
    orchestrator = ContextenOrchestrator()
    await orchestrator.initialize()
    
    print("\n🎬 Processing events...")
    
    for event in events:
        print(f"\n📨 Event: {event['type']}")
        
        if event['type'] == 'linear.issue.assigned':
            result = await orchestrator.handle_linear_issue_assignment(event['data'])
        elif event['type'] == 'github.pr.opened':
            result = await orchestrator.handle_github_pr_review_request(event['data'])
        elif event['type'] == 'slack.mention':
            result = await orchestrator.handle_slack_code_request(event['data'])
        else:
            print(f"   ⏭️  Event type not handled in demo")
            continue
        
        print(f"   ✅ Processed in {result.execution_time:.1f}s using {result.method_used}")
    
    print("\n🔄 Event-driven processing completed!")


async def main():
    """Main demo runner"""
    
    try:
        # Run orchestrator workflow demo
        await demo_orchestrator_workflow()
        
        # Run event-driven patterns demo
        await demo_event_driven_patterns()
        
        print("\n" + "=" * 60)
        print("🎉 All orchestrator integration demos completed!")
        print("🚀 Ready for production deployment!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        print("🔧 Check configuration and try again")


if __name__ == "__main__":
    # Run the orchestrator integration demo
    asyncio.run(main())

