"""
Analysis Reporting

Generates comprehensive reports from performance analysis and evaluation results.
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import asdict

from .optimization import OptimizationRecommendation
from .performance import PerformanceTrend, BottleneckAnalysis


class AnalysisReporter:
    """
    Generates comprehensive analysis reports in various formats.
    """
    
    def __init__(self):
        """Initialize the analysis reporter."""
        self.logger = logging.getLogger(__name__)
    
    async def generate_comprehensive_report(
        self,
        session_id: str,
        analysis_results: Dict[str, Any],
        recommendations: List[OptimizationRecommendation],
        format_type: str = 'json'
    ) -> str:
        """Generate a comprehensive analysis report."""
        try:
            report_data = {
                'report_metadata': {
                    'session_id': session_id,
                    'generated_at': datetime.now().isoformat(),
                    'report_type': 'comprehensive_analysis',
                    'format': format_type
                },
                'executive_summary': await self._generate_executive_summary(analysis_results),
                'performance_analysis': analysis_results,
                'optimization_recommendations': [asdict(rec) for rec in recommendations],
                'detailed_findings': await self._generate_detailed_findings(analysis_results),
                'action_plan': await self._generate_action_plan(recommendations)
            }
            
            if format_type == 'json':
                return json.dumps(report_data, indent=2)
            elif format_type == 'markdown':
                return await self._generate_markdown_report(report_data)
            elif format_type == 'html':
                return await self._generate_html_report(report_data)
            else:
                return json.dumps(report_data, indent=2)
            
        except Exception as e:
            self.logger.error("Failed to generate comprehensive report: %s", str(e))
            return f"Error generating report: {str(e)}"
    
    async def _generate_executive_summary(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate executive summary of the analysis."""
        try:
            summary = {
                'overall_performance_score': analysis_results.get('performance_score', 0.0),
                'total_evaluations': analysis_results.get('total_evaluations', 0),
                'components_analyzed': 0,
                'critical_issues': 0,
                'optimization_opportunities': 0,
                'key_findings': []
            }
            
            # Count components
            component_summary = analysis_results.get('component_summary', {})
            summary['components_analyzed'] = len(component_summary)
            
            # Count critical issues
            bottlenecks = analysis_results.get('bottleneck_analysis', [])
            summary['critical_issues'] = len([b for b in bottlenecks if b.get('severity') == 'critical'])
            
            # Count optimization opportunities
            opportunities = analysis_results.get('optimization_opportunities', [])
            summary['optimization_opportunities'] = len(opportunities)
            
            # Generate key findings
            if summary['overall_performance_score'] > 0.8:
                summary['key_findings'].append("Overall system performance is excellent")
            elif summary['overall_performance_score'] > 0.6:
                summary['key_findings'].append("Overall system performance is good with room for improvement")
            else:
                summary['key_findings'].append("Overall system performance needs significant improvement")
            
            if summary['critical_issues'] > 0:
                summary['key_findings'].append(f"{summary['critical_issues']} critical issues require immediate attention")
            
            if summary['optimization_opportunities'] > 0:
                summary['key_findings'].append(f"{summary['optimization_opportunities']} optimization opportunities identified")
            
            return summary
            
        except Exception as e:
            self.logger.error("Failed to generate executive summary: %s", str(e))
            return {'error': str(e)}
    
    async def _generate_detailed_findings(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate detailed findings from analysis results."""
        try:
            findings = {
                'performance_trends': [],
                'bottleneck_details': [],
                'component_comparisons': {},
                'statistical_insights': {}
            }
            
            # Process performance trends
            trends = analysis_results.get('performance_trends', [])
            for trend in trends:
                if isinstance(trend, dict):
                    findings['performance_trends'].append({
                        'component': trend.get('component_name', 'Unknown'),
                        'trend': trend.get('trend_direction', 'stable'),
                        'strength': trend.get('trend_strength', 0.0),
                        'confidence': trend.get('confidence', 0.0),
                        'interpretation': self._interpret_trend(trend)
                    })
            
            # Process bottleneck details
            bottlenecks = analysis_results.get('bottleneck_analysis', [])
            for bottleneck in bottlenecks:
                if isinstance(bottleneck, dict):
                    findings['bottleneck_details'].append({
                        'component': bottleneck.get('component_name', 'Unknown'),
                        'type': bottleneck.get('bottleneck_type', 'unknown'),
                        'severity': bottleneck.get('severity', 'low'),
                        'impact': bottleneck.get('impact_score', 0.0),
                        'description': bottleneck.get('description', ''),
                        'priority': self._calculate_priority(bottleneck)
                    })
            
            # Process component comparisons
            comparisons = analysis_results.get('comparative_analysis', {})
            findings['component_comparisons'] = comparisons
            
            # Generate statistical insights
            findings['statistical_insights'] = await self._generate_statistical_insights(analysis_results)
            
            return findings
            
        except Exception as e:
            self.logger.error("Failed to generate detailed findings: %s", str(e))
            return {'error': str(e)}
    
    def _interpret_trend(self, trend: Dict[str, Any]) -> str:
        """Interpret a performance trend."""
        direction = trend.get('trend_direction', 'stable')
        strength = trend.get('trend_strength', 0.0)
        confidence = trend.get('confidence', 0.0)
        
        if direction == 'stable':
            return "Performance is stable with no significant trend"
        elif direction == 'improving':
            if strength > 0.7:
                return f"Strong improvement trend (confidence: {confidence:.1%})"
            elif strength > 0.4:
                return f"Moderate improvement trend (confidence: {confidence:.1%})"
            else:
                return f"Slight improvement trend (confidence: {confidence:.1%})"
        else:  # declining
            if strength > 0.7:
                return f"Strong decline trend - requires immediate attention (confidence: {confidence:.1%})"
            elif strength > 0.4:
                return f"Moderate decline trend - monitor closely (confidence: {confidence:.1%})"
            else:
                return f"Slight decline trend - investigate if continues (confidence: {confidence:.1%})"
    
    def _calculate_priority(self, bottleneck: Dict[str, Any]) -> str:
        """Calculate priority for a bottleneck."""
        severity = bottleneck.get('severity', 'low')
        impact = bottleneck.get('impact_score', 0.0)
        
        if severity == 'critical' or impact > 0.8:
            return 'immediate'
        elif severity == 'high' or impact > 0.6:
            return 'high'
        elif severity == 'medium' or impact > 0.4:
            return 'medium'
        else:
            return 'low'
    
    async def _generate_statistical_insights(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate statistical insights from analysis results."""
        try:
            insights = {
                'data_quality': 'good',
                'confidence_level': 0.8,
                'sample_size_adequacy': 'adequate',
                'variance_analysis': {},
                'correlation_strength': 'moderate'
            }
            
            # Analyze sample size
            total_evaluations = analysis_results.get('total_evaluations', 0)
            if total_evaluations < 10:
                insights['sample_size_adequacy'] = 'insufficient'
                insights['confidence_level'] = 0.3
            elif total_evaluations < 50:
                insights['sample_size_adequacy'] = 'limited'
                insights['confidence_level'] = 0.6
            else:
                insights['sample_size_adequacy'] = 'adequate'
                insights['confidence_level'] = 0.8
            
            # Analyze component summary for variance
            component_summary = analysis_results.get('component_summary', {})
            variances = []
            for component_data in component_summary.values():
                if isinstance(component_data, dict) and 'effectiveness' in component_data:
                    variance = component_data['effectiveness'].get('variance', 0.0)
                    variances.append(variance)
            
            if variances:
                avg_variance = sum(variances) / len(variances)
                if avg_variance < 0.1:
                    insights['variance_analysis']['level'] = 'low'
                    insights['variance_analysis']['interpretation'] = 'Consistent performance across evaluations'
                elif avg_variance < 0.3:
                    insights['variance_analysis']['level'] = 'moderate'
                    insights['variance_analysis']['interpretation'] = 'Some variability in performance'
                else:
                    insights['variance_analysis']['level'] = 'high'
                    insights['variance_analysis']['interpretation'] = 'High variability indicates unstable performance'
            
            return insights
            
        except Exception as e:
            self.logger.error("Failed to generate statistical insights: %s", str(e))
            return {'error': str(e)}
    
    async def _generate_action_plan(self, recommendations: List[OptimizationRecommendation]) -> Dict[str, Any]:
        """Generate an action plan from recommendations."""
        try:
            action_plan = {
                'immediate_actions': [],
                'short_term_actions': [],
                'long_term_actions': [],
                'resource_requirements': {},
                'success_metrics': []
            }
            
            # Categorize recommendations by priority and effort
            for rec in recommendations:
                action_item = {
                    'title': rec.title,
                    'component': rec.component_name,
                    'description': rec.description,
                    'steps': rec.implementation_steps,
                    'effort': rec.effort_level,
                    'impact': rec.expected_impact
                }
                
                if rec.priority in ['critical', 'high']:
                    action_plan['immediate_actions'].append(action_item)
                elif rec.priority == 'medium':
                    action_plan['short_term_actions'].append(action_item)
                else:
                    action_plan['long_term_actions'].append(action_item)
                
                # Collect success metrics
                action_plan['success_metrics'].extend(rec.success_metrics)
            
            # Estimate resource requirements
            effort_counts = {'low': 0, 'medium': 0, 'high': 0}
            for rec in recommendations:
                effort_counts[rec.effort_level] = effort_counts.get(rec.effort_level, 0) + 1
            
            action_plan['resource_requirements'] = {
                'estimated_effort_distribution': effort_counts,
                'recommended_team_size': max(1, len(recommendations) // 3),
                'estimated_timeline_weeks': effort_counts['low'] + effort_counts['medium'] * 2 + effort_counts['high'] * 4
            }
            
            # Remove duplicate success metrics
            action_plan['success_metrics'] = list(set(action_plan['success_metrics']))
            
            return action_plan
            
        except Exception as e:
            self.logger.error("Failed to generate action plan: %s", str(e))
            return {'error': str(e)}
    
    async def _generate_markdown_report(self, report_data: Dict[str, Any]) -> str:
        """Generate a markdown format report."""
        try:
            md_content = []
            
            # Title and metadata
            metadata = report_data['report_metadata']
            md_content.append(f"# OpenEvolve Integration Analysis Report")
            md_content.append(f"**Session ID:** {metadata['session_id']}")
            md_content.append(f"**Generated:** {metadata['generated_at']}")
            md_content.append("")
            
            # Executive Summary
            summary = report_data['executive_summary']
            md_content.append("## Executive Summary")
            md_content.append(f"- **Overall Performance Score:** {summary['overall_performance_score']:.3f}")
            md_content.append(f"- **Total Evaluations:** {summary['total_evaluations']}")
            md_content.append(f"- **Components Analyzed:** {summary['components_analyzed']}")
            md_content.append(f"- **Critical Issues:** {summary['critical_issues']}")
            md_content.append(f"- **Optimization Opportunities:** {summary['optimization_opportunities']}")
            md_content.append("")
            
            # Key Findings
            md_content.append("### Key Findings")
            for finding in summary.get('key_findings', []):
                md_content.append(f"- {finding}")
            md_content.append("")
            
            # Detailed Findings
            findings = report_data['detailed_findings']
            md_content.append("## Detailed Analysis")
            
            # Performance Trends
            md_content.append("### Performance Trends")
            for trend in findings.get('performance_trends', []):
                md_content.append(f"- **{trend['component']}:** {trend['interpretation']}")
            md_content.append("")
            
            # Bottlenecks
            md_content.append("### Identified Bottlenecks")
            for bottleneck in findings.get('bottleneck_details', []):
                md_content.append(f"- **{bottleneck['component']}** ({bottleneck['severity']}): {bottleneck['description']}")
            md_content.append("")
            
            # Recommendations
            md_content.append("## Optimization Recommendations")
            recommendations = report_data['optimization_recommendations']
            
            for i, rec in enumerate(recommendations, 1):
                md_content.append(f"### {i}. {rec['title']}")
                md_content.append(f"**Priority:** {rec['priority']} | **Effort:** {rec['effort_level']}")
                md_content.append(f"**Description:** {rec['description']}")
                md_content.append("**Implementation Steps:**")
                for step in rec['implementation_steps']:
                    md_content.append(f"- {step}")
                md_content.append(f"**Expected Impact:** {rec['expected_impact']}")
                md_content.append("")
            
            # Action Plan
            action_plan = report_data['action_plan']
            md_content.append("## Action Plan")
            
            if action_plan.get('immediate_actions'):
                md_content.append("### Immediate Actions (Critical/High Priority)")
                for action in action_plan['immediate_actions']:
                    md_content.append(f"- {action['title']}")
            
            if action_plan.get('short_term_actions'):
                md_content.append("### Short-term Actions (Medium Priority)")
                for action in action_plan['short_term_actions']:
                    md_content.append(f"- {action['title']}")
            
            if action_plan.get('long_term_actions'):
                md_content.append("### Long-term Actions (Low Priority)")
                for action in action_plan['long_term_actions']:
                    md_content.append(f"- {action['title']}")
            
            return "\n".join(md_content)
            
        except Exception as e:
            self.logger.error("Failed to generate markdown report: %s", str(e))
            return f"Error generating markdown report: {str(e)}"
    
    async def _generate_html_report(self, report_data: Dict[str, Any]) -> str:
        """Generate an HTML format report."""
        try:
            # Basic HTML template
            html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>OpenEvolve Integration Analysis Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
        .section {{ margin: 20px 0; }}
        .metric {{ display: inline-block; margin: 10px; padding: 10px; background-color: #e8f4f8; border-radius: 3px; }}
        .critical {{ color: #d32f2f; }}
        .high {{ color: #f57c00; }}
        .medium {{ color: #1976d2; }}
        .low {{ color: #388e3c; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>OpenEvolve Integration Analysis Report</h1>
        <p><strong>Session ID:</strong> {report_data['report_metadata']['session_id']}</p>
        <p><strong>Generated:</strong> {report_data['report_metadata']['generated_at']}</p>
    </div>
    
    <div class="section">
        <h2>Executive Summary</h2>
        <div class="metric">Performance Score: {report_data['executive_summary']['overall_performance_score']:.3f}</div>
        <div class="metric">Total Evaluations: {report_data['executive_summary']['total_evaluations']}</div>
        <div class="metric">Components: {report_data['executive_summary']['components_analyzed']}</div>
        <div class="metric critical">Critical Issues: {report_data['executive_summary']['critical_issues']}</div>
    </div>
    
    <div class="section">
        <h2>Optimization Recommendations</h2>
        <table>
            <tr>
                <th>Priority</th>
                <th>Component</th>
                <th>Title</th>
                <th>Expected Impact</th>
            </tr>
"""
            
            for rec in report_data['optimization_recommendations']:
                priority_class = rec['priority']
                html_content += f"""
            <tr>
                <td class="{priority_class}">{rec['priority']}</td>
                <td>{rec['component_name']}</td>
                <td>{rec['title']}</td>
                <td>{rec['expected_impact']}</td>
            </tr>
"""
            
            html_content += """
        </table>
    </div>
</body>
</html>
"""
            
            return html_content
            
        except Exception as e:
            self.logger.error("Failed to generate HTML report: %s", str(e))
            return f"<html><body>Error generating HTML report: {str(e)}</body></html>"

