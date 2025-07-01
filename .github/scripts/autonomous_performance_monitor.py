#!/usr/bin/env python3
"""
Autonomous Performance Monitor with Codegen SDK Integration

This script monitors CI/CD performance, detects regressions, and automatically
optimizes workflows using AI-driven analysis and recommendations.
"""

import argparse
import asyncio
import json
import os
import sys
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from statistics import mean, median

import requests
from github import Github
from codegen import Agent


@dataclass
class PerformanceMetrics:
    """Performance metrics for CI/CD workflows"""
    workflow_name: str
    run_id: str
    duration_seconds: int
    job_durations: Dict[str, int]
    queue_time_seconds: int
    total_time_seconds: int
    success_rate: float
    resource_usage: Dict[str, Any]
    bottlenecks: List[str]
    timestamp: datetime


@dataclass
class PerformanceRegression:
    """Detected performance regression"""
    metric_name: str
    current_value: float
    baseline_value: float
    regression_percentage: float
    severity: str  # critical, high, medium, low
    affected_workflows: List[str]
    root_cause: str
    suggested_fix: str


class AutonomousPerformanceMonitor:
    """AI-powered CI/CD performance monitoring and optimization"""
    
    def __init__(self, codegen_org_id: str, codegen_token: str, github_token: str):
        self.codegen_agent = Agent(
            org_id=codegen_org_id,
            token=codegen_token
        )
        self.github = Github(github_token)
        self.repo = self.github.get_repo(os.environ.get('GITHUB_REPOSITORY', 'Zeeeepa/graph-sitter'))
        
        # Performance baselines
        self.baselines = {}
        self.performance_history = []
        
        # Optimization strategies
        self.optimization_strategies = {
            'test_parallelization': {
                'description': 'Optimize test parallelization',
                'impact': 'high',
                'complexity': 'medium'
            },
            'cache_optimization': {
                'description': 'Improve caching strategies',
                'impact': 'medium',
                'complexity': 'low'
            },
            'dependency_caching': {
                'description': 'Optimize dependency installation',
                'impact': 'medium',
                'complexity': 'low'
            },
            'workflow_restructuring': {
                'description': 'Restructure workflow jobs',
                'impact': 'high',
                'complexity': 'high'
            }
        }
    
    async def collect_performance_metrics(self, baseline_branch: str = 'develop') -> List[PerformanceMetrics]:
        """Collect comprehensive performance metrics"""
        
        print("📊 Collecting performance metrics...")
        
        metrics = []
        
        # Get recent workflow runs
        workflow_runs = list(self.repo.get_workflow_runs(
            branch=baseline_branch,
            status='completed'
        ))[:20]  # Last 20 runs
        
        for run in workflow_runs:
            try:
                metric = await self._analyze_workflow_run(run)
                if metric:
                    metrics.append(metric)
            except Exception as e:
                print(f"⚠️ Error analyzing run {run.id}: {e}")
        
        return metrics
    
    async def _analyze_workflow_run(self, workflow_run) -> Optional[PerformanceMetrics]:
        """Analyze a single workflow run for performance metrics"""
        
        try:
            # Calculate durations
            start_time = workflow_run.created_at
            end_time = workflow_run.updated_at
            total_duration = (end_time - start_time).total_seconds()
            
            # Get job-level metrics
            job_durations = {}
            queue_time = 0
            
            for job in workflow_run.jobs():
                if job.started_at and job.completed_at:
                    job_duration = (job.completed_at - job.started_at).total_seconds()
                    job_durations[job.name] = job_duration
                    
                    # Calculate queue time (time between creation and start)
                    if job.started_at:
                        job_queue_time = (job.started_at - workflow_run.created_at).total_seconds()
                        queue_time = max(queue_time, job_queue_time)
            
            # Detect bottlenecks
            bottlenecks = self._detect_bottlenecks(job_durations)
            
            return PerformanceMetrics(
                workflow_name=workflow_run.name,
                run_id=str(workflow_run.id),
                duration_seconds=int(total_duration),
                job_durations=job_durations,
                queue_time_seconds=int(queue_time),
                total_time_seconds=int(total_duration),
                success_rate=1.0 if workflow_run.conclusion == 'success' else 0.0,
                resource_usage={},  # Would need additional API calls to get this
                bottlenecks=bottlenecks,
                timestamp=workflow_run.created_at
            )
        
        except Exception as e:
            print(f"⚠️ Error analyzing workflow run: {e}")
            return None
    
    def _detect_bottlenecks(self, job_durations: Dict[str, int]) -> List[str]:
        """Detect performance bottlenecks in workflow jobs"""
        
        if not job_durations:
            return []
        
        bottlenecks = []
        avg_duration = mean(job_durations.values())
        
        for job_name, duration in job_durations.items():
            # Jobs taking significantly longer than average
            if duration > avg_duration * 2:
                bottlenecks.append(f"Slow job: {job_name} ({duration}s)")
        
        return bottlenecks
    
    async def detect_regressions(self, current_metrics: List[PerformanceMetrics], 
                               threshold_percentage: float = 20.0) -> List[PerformanceRegression]:
        """Detect performance regressions using AI analysis"""
        
        print("🔍 Detecting performance regressions...")
        
        if len(current_metrics) < 5:
            print("⚠️ Insufficient data for regression analysis")
            return []
        
        # Calculate baselines
        baselines = self._calculate_baselines(current_metrics)
        
        # Get recent metrics for comparison
        recent_metrics = current_metrics[:5]  # Last 5 runs
        current_averages = self._calculate_current_averages(recent_metrics)
        
        regressions = []
        
        # Check for duration regressions
        for workflow_name in baselines:
            baseline_duration = baselines[workflow_name]['duration']
            current_duration = current_averages.get(workflow_name, {}).get('duration', 0)
            
            if current_duration > baseline_duration * (1 + threshold_percentage / 100):
                regression_pct = ((current_duration - baseline_duration) / baseline_duration) * 100
                
                regression = PerformanceRegression(
                    metric_name=f"{workflow_name}_duration",
                    current_value=current_duration,
                    baseline_value=baseline_duration,
                    regression_percentage=regression_pct,
                    severity=self._classify_regression_severity(regression_pct),
                    affected_workflows=[workflow_name],
                    root_cause="To be analyzed",
                    suggested_fix="To be determined"
                )
                regressions.append(regression)
        
        # Use AI to analyze regressions
        if regressions:
            analyzed_regressions = await self._ai_analyze_regressions(regressions, current_metrics)
            return analyzed_regressions
        
        return []
    
    def _calculate_baselines(self, metrics: List[PerformanceMetrics]) -> Dict[str, Dict[str, float]]:
        """Calculate performance baselines from historical data"""
        
        baselines = {}
        
        # Group metrics by workflow
        workflow_metrics = {}
        for metric in metrics:
            if metric.workflow_name not in workflow_metrics:
                workflow_metrics[metric.workflow_name] = []
            workflow_metrics[metric.workflow_name].append(metric)
        
        # Calculate baselines for each workflow
        for workflow_name, metrics_list in workflow_metrics.items():
            durations = [m.duration_seconds for m in metrics_list]
            queue_times = [m.queue_time_seconds for m in metrics_list]
            
            baselines[workflow_name] = {
                'duration': median(durations),
                'queue_time': median(queue_times),
                'success_rate': mean([m.success_rate for m in metrics_list])
            }
        
        return baselines
    
    def _calculate_current_averages(self, recent_metrics: List[PerformanceMetrics]) -> Dict[str, Dict[str, float]]:
        """Calculate current performance averages"""
        
        current_averages = {}
        
        # Group by workflow
        workflow_metrics = {}
        for metric in recent_metrics:
            if metric.workflow_name not in workflow_metrics:
                workflow_metrics[metric.workflow_name] = []
            workflow_metrics[metric.workflow_name].append(metric)
        
        # Calculate averages
        for workflow_name, metrics_list in workflow_metrics.items():
            durations = [m.duration_seconds for m in metrics_list]
            queue_times = [m.queue_time_seconds for m in metrics_list]
            
            current_averages[workflow_name] = {
                'duration': mean(durations),
                'queue_time': mean(queue_times),
                'success_rate': mean([m.success_rate for m in metrics_list])
            }
        
        return current_averages
    
    def _classify_regression_severity(self, regression_percentage: float) -> str:
        """Classify regression severity based on percentage"""
        
        if regression_percentage >= 50:
            return "critical"
        elif regression_percentage >= 30:
            return "high"
        elif regression_percentage >= 15:
            return "medium"
        else:
            return "low"
    
    async def _ai_analyze_regressions(self, regressions: List[PerformanceRegression], 
                                    metrics: List[PerformanceMetrics]) -> List[PerformanceRegression]:
        """Use AI to analyze performance regressions and suggest fixes"""
        
        # Prepare data for AI analysis
        regression_data = []
        for reg in regressions:
            regression_data.append({
                'metric': reg.metric_name,
                'current_value': reg.current_value,
                'baseline_value': reg.baseline_value,
                'regression_percentage': reg.regression_percentage,
                'severity': reg.severity,
                'affected_workflows': reg.affected_workflows
            })
        
        # Get recent bottlenecks and patterns
        recent_bottlenecks = []
        for metric in metrics[:10]:  # Last 10 runs
            recent_bottlenecks.extend(metric.bottlenecks)
        
        analysis_prompt = f"""
Analyze these CI/CD performance regressions and provide actionable insights:

PERFORMANCE REGRESSIONS:
{json.dumps(regression_data, indent=2)}

RECENT BOTTLENECKS:
{json.dumps(recent_bottlenecks, indent=2)}

PROJECT CONTEXT:
- This is a Python library with Cython extensions
- Uses GitHub Actions with 8 parallel test groups
- Multi-platform builds (Ubuntu, macOS)
- Heavy use of caching for dependencies

For each regression, provide:
1. Root cause analysis
2. Specific fix recommendations
3. Prevention strategies
4. Impact assessment
5. Implementation priority

Respond in JSON format:
{{
    "analyses": [
        {{
            "metric": "metric_name",
            "root_cause": "detailed explanation",
            "suggested_fix": "specific actionable steps",
            "prevention_strategy": "how to prevent future regressions",
            "implementation_priority": "critical|high|medium|low",
            "estimated_improvement": "percentage or time saved"
        }}
    ],
    "overall_recommendations": [
        "recommendation1",
        "recommendation2"
    ]
}}
"""
        
        task = self.codegen_agent.run(prompt=analysis_prompt)
        
        # Wait for analysis
        while task.status not in ['completed', 'failed']:
            await asyncio.sleep(5)
            task.refresh()
        
        if task.status == 'failed':
            print(f"⚠️ AI regression analysis failed: {task.result}")
            return regressions
        
        # Parse AI analysis and update regressions
        try:
            import re
            json_match = re.search(r'\{.*\}', task.result, re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group())
                
                for i, regression in enumerate(regressions):
                    for analysis_item in analysis.get('analyses', []):
                        if analysis_item['metric'] == regression.metric_name:
                            regression.root_cause = analysis_item.get('root_cause', regression.root_cause)
                            regression.suggested_fix = analysis_item.get('suggested_fix', regression.suggested_fix)
                            break
        
        except (json.JSONDecodeError, KeyError) as e:
            print(f"⚠️ Failed to parse AI analysis: {e}")
        
        return regressions
    
    async def auto_optimize_performance(self, regressions: List[PerformanceRegression]) -> bool:
        """Automatically optimize CI/CD performance based on detected issues"""
        
        if not regressions:
            print("✅ No performance issues to optimize")
            return True
        
        print(f"🚀 Auto-optimizing {len(regressions)} performance issues...")
        
        # Create optimization prompt
        optimization_data = []
        for reg in regressions:
            optimization_data.append({
                'issue': reg.metric_name,
                'severity': reg.severity,
                'root_cause': reg.root_cause,
                'suggested_fix': reg.suggested_fix,
                'regression_percentage': reg.regression_percentage
            })
        
        optimization_prompt = f"""
Implement performance optimizations for these CI/CD issues:

PERFORMANCE ISSUES:
{json.dumps(optimization_data, indent=2)}

AVAILABLE OPTIMIZATION STRATEGIES:
{json.dumps(self.optimization_strategies, indent=2)}

Please implement the most impactful optimizations by:
1. Modifying GitHub Actions workflow files
2. Updating caching strategies
3. Optimizing test parallelization
4. Improving dependency management
5. Adding performance monitoring

Create a PR with title: "🚀 Auto-optimize CI/CD performance"

Focus on:
- High-impact, low-risk optimizations first
- Maintaining workflow reliability
- Adding performance monitoring
- Documenting changes clearly
"""
        
        task = self.codegen_agent.run(prompt=optimization_prompt)
        
        # Wait for optimization completion
        while task.status not in ['completed', 'failed']:
            await asyncio.sleep(10)
            task.refresh()
            print(f"⏳ Optimizing performance... Status: {task.status}")
        
        if task.status == 'completed':
            print(f"✅ Performance optimization completed: {task.result}")
            return True
        else:
            print(f"❌ Performance optimization failed: {task.result}")
            return False
    
    async def create_performance_report(self, metrics: List[PerformanceMetrics], 
                                      regressions: List[PerformanceRegression]) -> None:
        """Create a comprehensive performance report"""
        
        # Calculate summary statistics
        if metrics:
            avg_duration = mean([m.duration_seconds for m in metrics])
            avg_queue_time = mean([m.queue_time_seconds for m in metrics])
            success_rate = mean([m.success_rate for m in metrics])
        else:
            avg_duration = avg_queue_time = success_rate = 0
        
        issue_title = f"📊 CI/CD Performance Report - {datetime.now().strftime('%Y-%m-%d')}"
        
        issue_body = f"""
## Autonomous Performance Analysis Report

**Analysis Date:** {datetime.now().isoformat()}
**Metrics Analyzed:** {len(metrics)} workflow runs
**Regressions Detected:** {len(regressions)}

### Performance Summary
- **Average Duration:** {avg_duration:.1f} seconds
- **Average Queue Time:** {avg_queue_time:.1f} seconds
- **Success Rate:** {success_rate:.1%}

### Performance Regressions
"""
        
        for regression in regressions:
            issue_body += f"""
#### {regression.metric_name}
- **Severity:** {regression.severity.upper()}
- **Regression:** {regression.regression_percentage:.1f}% slower
- **Root Cause:** {regression.root_cause}
- **Suggested Fix:** {regression.suggested_fix}

"""
        
        if not regressions:
            issue_body += "\n✅ No performance regressions detected\n"
        
        issue_body += """
### Recommendations
1. Monitor performance trends continuously
2. Implement suggested optimizations
3. Add performance benchmarks to prevent regressions
4. Review resource usage patterns

---
*This report was generated by the Autonomous Performance Monitor*
"""
        
        # Create GitHub issue
        issue = self.repo.create_issue(
            title=issue_title,
            body=issue_body,
            labels=['performance', 'ci-cd', 'autonomous-analysis']
        )
        
        print(f"📊 Performance report created: {issue.html_url}")


async def main():
    parser = argparse.ArgumentParser(description='Autonomous Performance Monitor')
    parser.add_argument('--baseline-branch', default='develop')
    parser.add_argument('--alert-threshold', type=float, default=20.0)
    parser.add_argument('--auto-optimize', type=bool, default=False)
    
    args = parser.parse_args()
    
    # Get environment variables
    codegen_org_id = os.environ.get('CODEGEN_ORG_ID')
    codegen_token = os.environ.get('CODEGEN_TOKEN')
    github_token = os.environ.get('GITHUB_TOKEN')
    
    if not all([codegen_org_id, codegen_token, github_token]):
        print("❌ Missing required environment variables")
        sys.exit(1)
    
    # Initialize monitor
    monitor = AutonomousPerformanceMonitor(codegen_org_id, codegen_token, github_token)
    
    try:
        # Collect performance metrics
        metrics = await monitor.collect_performance_metrics(args.baseline_branch)
        
        print(f"📊 Collected {len(metrics)} performance metrics")
        
        # Detect regressions
        regressions = await monitor.detect_regressions(metrics, args.alert_threshold)
        
        if regressions:
            print(f"⚠️ Detected {len(regressions)} performance regressions")
            
            # Auto-optimize if enabled
            if args.auto_optimize:
                success = await monitor.auto_optimize_performance(regressions)
                if success:
                    print("🎉 Performance optimization completed!")
        else:
            print("✅ No performance regressions detected")
        
        # Create performance report
        await monitor.create_performance_report(metrics, regressions)
        
    except Exception as e:
        print(f"❌ Performance monitoring failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())

