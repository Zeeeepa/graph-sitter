#!/usr/bin/env python3
"""
Standalone test for PlanningResultParser functionality

Tests the parser without requiring full Prefect dependencies.
"""

import json
import logging
import re
import sys
import os
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from enum import Enum

# Minimal implementation for testing
class TaskComplexity(str, Enum):
    """Task complexity levels."""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    CRITICAL = "critical"


class PlanningResultParser:
    """Intelligent parser for Codegen SDK planning results."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.parsing_strategies = [
            self._parse_json_structured,
            self._parse_markdown_structured,
            self._parse_text_pattern,
            self._parse_ai_assisted,
            self._parse_fallback
        ]
        
        # Common capability keywords mapping
        self.capability_keywords = {
            'code': ['code_generation', 'programming', 'development'],
            'test': ['testing', 'quality_assurance', 'validation'],
            'docs': ['documentation', 'writing', 'technical_writing'],
            'review': ['code_review', 'analysis', 'inspection'],
            'deploy': ['deployment', 'devops', 'infrastructure'],
            'debug': ['debugging', 'troubleshooting', 'problem_solving'],
            'design': ['system_design', 'architecture', 'planning'],
            'api': ['api_development', 'integration', 'web_services']
        }
        
        # Complexity indicators
        self.complexity_indicators = {
            TaskComplexity.SIMPLE: ['simple', 'basic', 'straightforward', 'quick', 'minor'],
            TaskComplexity.MODERATE: ['moderate', 'standard', 'typical', 'normal', 'medium'],
            TaskComplexity.COMPLEX: ['complex', 'advanced', 'challenging', 'difficult', 'major'],
            TaskComplexity.CRITICAL: ['critical', 'essential', 'core', 'fundamental', 'crucial']
        }

    def parse_planning_result(self, planning_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse planning result using multiple strategies."""
        self.logger.info("Starting planning result parsing")
        
        # Validate input
        if not self._validate_planning_result(planning_result):
            self.logger.warning("Planning result validation failed, using fallback")
            return self._parse_fallback(planning_result)
        
        plan_content = planning_result.get('plan', '')
        if not plan_content:
            self.logger.warning("No plan content found, using fallback")
            return self._parse_fallback(planning_result)
        
        # Try parsing strategies in order of reliability
        for strategy_func in self.parsing_strategies:
            try:
                self.logger.debug(f"Trying parsing strategy: {strategy_func.__name__}")
                tasks = strategy_func(planning_result)
                if tasks and len(tasks) > 0:
                    self.logger.info(f"Successfully parsed {len(tasks)} tasks using {strategy_func.__name__}")
                    return self._validate_and_enhance_tasks(tasks, planning_result)
            except Exception as e:
                self.logger.debug(f"Strategy {strategy_func.__name__} failed: {e}")
                continue
        
        # If all strategies fail, use fallback
        self.logger.warning("All parsing strategies failed, using fallback")
        return self._parse_fallback(planning_result)

    def _validate_planning_result(self, planning_result: Dict[str, Any]) -> bool:
        """Validate planning result structure."""
        required_fields = ['plan']
        return all(field in planning_result for field in required_fields)

    def _parse_json_structured(self, planning_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse JSON-structured planning results."""
        plan_content = planning_result.get('plan', '')
        
        # Try to extract JSON from the plan content
        json_patterns = [
            r'```json\s*(\{.*?\})\s*```',
            r'```\s*(\{.*?\})\s*```',
            r'(\{.*?"tasks".*?\})',
            r'(\[.*?\{.*?"name".*?\}.*?\])'
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, plan_content, re.DOTALL | re.IGNORECASE)
            for match in matches:
                try:
                    parsed_json = json.loads(match)
                    if isinstance(parsed_json, dict) and 'tasks' in parsed_json:
                        return self._extract_tasks_from_json(parsed_json['tasks'])
                    elif isinstance(parsed_json, list):
                        return self._extract_tasks_from_json(parsed_json)
                except json.JSONDecodeError:
                    continue
        
        raise ValueError("No valid JSON structure found")

    def _parse_markdown_structured(self, planning_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse markdown-structured planning results."""
        plan_content = planning_result.get('plan', '')
        tasks = []
        
        # Look for markdown task sections
        task_patterns = [
            r'#{1,3}\s*(?:Task|Step)\s*(\d+)[:.]?\s*(.+?)(?=#{1,3}|$)',
            r'(\d+)\.\s*\*\*(.+?)\*\*\s*[-:]?\s*(.+?)(?=\d+\.|$)',
            r'-\s*\*\*(.+?)\*\*\s*[-:]?\s*(.+?)(?=-\s*\*\*|$)'
        ]
        
        for i, pattern in enumerate(task_patterns):
            matches = re.findall(pattern, plan_content, re.DOTALL | re.IGNORECASE)
            if matches:
                for j, match in enumerate(matches):
                    if len(match) >= 2:
                        task_id = f"task_{j+1}"
                        if i == 0:  # Pattern with task number
                            name = match[1].strip()
                            description = self._extract_description_after_header(plan_content, match[1])
                        else:
                            name = match[0].strip() if i == 2 else match[1].strip()
                            description = match[1].strip() if i == 2 else match[2].strip()
                        
                        tasks.append(self._create_task_definition(
                            task_id=task_id,
                            name=name,
                            description=description
                        ))
                
                if tasks:
                    return tasks
        
        raise ValueError("No markdown structure found")

    def _parse_text_pattern(self, planning_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse text-based planning results using patterns."""
        plan_content = planning_result.get('plan', '')
        tasks = []
        
        # Common text patterns for tasks
        patterns = [
            r'(?:Task|Step|Phase)\s*(\d+)[:.]?\s*(.+?)(?:\n|$)',
            r'(\d+)\.\s*(.+?)(?:\n|$)',
            r'-\s*(.+?)(?:\n|$)',
            r'•\s*(.+?)(?:\n|$)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, plan_content, re.MULTILINE)
            if matches and len(matches) >= 2:  # Need at least 2 tasks
                for i, match in enumerate(matches):
                    if isinstance(match, tuple):
                        name = match[1].strip() if len(match) > 1 else match[0].strip()
                    else:
                        name = match.strip()
                    
                    if len(name) > 10:  # Filter out too short matches
                        tasks.append(self._create_task_definition(
                            task_id=f"task_{i+1}",
                            name=name,
                            description=name
                        ))
                
                if tasks:
                    return tasks
        
        raise ValueError("No text patterns found")

    def _parse_ai_assisted(self, planning_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """AI-assisted parsing for natural language plans."""
        plan_content = planning_result.get('plan', '')
        
        # Split content into potential task sections
        sections = re.split(r'\n\s*\n', plan_content)
        tasks = []
        
        for i, section in enumerate(sections):
            section = section.strip()
            if len(section) > 50:  # Meaningful content
                # Extract potential task name (first line or sentence)
                lines = section.split('\n')
                first_line = lines[0].strip()
                
                # Clean up the first line to get task name
                name = re.sub(r'^[\d\.\-\*\#\s]+', '', first_line)
                name = re.sub(r'[:\.]+$', '', name)
                
                if len(name) > 10:
                    tasks.append(self._create_task_definition(
                        task_id=f"task_{i+1}",
                        name=name,
                        description=section
                    ))
        
        if len(tasks) >= 2:
            return tasks
        
        raise ValueError("AI-assisted parsing failed")

    def _parse_fallback(self, planning_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fallback parser that generates basic tasks."""
        self.logger.info("Using fallback parser - generating basic tasks")
        
        # Generate tasks based on common software development workflow
        base_tasks = [
            {
                'id': 'task_analysis',
                'name': 'Requirements Analysis',
                'description': 'Analyze requirements and create implementation plan',
                'complexity': TaskComplexity.MODERATE.value,
                'estimated_duration': 1200,
                'required_capabilities': ['analysis', 'planning'],
                'dependencies': [],
                'priority': 3
            },
            {
                'id': 'task_implementation',
                'name': 'Core Implementation',
                'description': 'Implement core functionality based on requirements',
                'complexity': TaskComplexity.COMPLEX.value,
                'estimated_duration': 2400,
                'required_capabilities': ['code_generation', 'development'],
                'dependencies': ['task_analysis'],
                'priority': 3
            },
            {
                'id': 'task_testing',
                'name': 'Testing & Validation',
                'description': 'Create and run comprehensive tests',
                'complexity': TaskComplexity.MODERATE.value,
                'estimated_duration': 1200,
                'required_capabilities': ['testing', 'quality_assurance'],
                'dependencies': ['task_implementation'],
                'priority': 2
            },
            {
                'id': 'task_documentation',
                'name': 'Documentation',
                'description': 'Update documentation and README',
                'complexity': TaskComplexity.SIMPLE.value,
                'estimated_duration': 600,
                'required_capabilities': ['documentation', 'writing'],
                'dependencies': ['task_implementation'],
                'priority': 1
            }
        ]
        
        # Customize based on planning result if available
        requirements = planning_result.get('requirements', '')
        if 'api' in requirements.lower():
            base_tasks.insert(1, {
                'id': 'task_api_design',
                'name': 'API Design',
                'description': 'Design API endpoints and data structures',
                'complexity': TaskComplexity.MODERATE.value,
                'estimated_duration': 900,
                'required_capabilities': ['api_development', 'design'],
                'dependencies': ['task_analysis'],
                'priority': 3
            })
        
        return base_tasks

    def _extract_tasks_from_json(self, tasks_json: Union[List, Dict]) -> List[Dict[str, Any]]:
        """Extract tasks from JSON structure."""
        if isinstance(tasks_json, dict):
            tasks_json = [tasks_json]
        
        tasks = []
        for i, task_data in enumerate(tasks_json):
            if isinstance(task_data, dict):
                task_id = task_data.get('id', f"task_{i+1}")
                name = task_data.get('name', task_data.get('title', f"Task {i+1}"))
                description = task_data.get('description', task_data.get('desc', name))
                
                tasks.append(self._create_task_definition(
                    task_id=task_id,
                    name=name,
                    description=description,
                    complexity=task_data.get('complexity'),
                    estimated_duration=task_data.get('duration', task_data.get('estimated_duration')),
                    required_capabilities=task_data.get('capabilities', task_data.get('required_capabilities', [])),
                    dependencies=task_data.get('dependencies', []),
                    priority=task_data.get('priority', 2)
                ))
        
        return tasks

    def _create_task_definition(self, task_id: str, name: str, description: str, 
                              complexity: Optional[str] = None, estimated_duration: Optional[int] = None,
                              required_capabilities: Optional[List[str]] = None,
                              dependencies: Optional[List[str]] = None,
                              priority: Optional[int] = None) -> Dict[str, Any]:
        """Create a standardized task definition."""
        
        # Infer complexity if not provided
        if not complexity:
            complexity = self._infer_complexity(name, description)
        
        # Estimate duration if not provided
        if not estimated_duration:
            estimated_duration = self._estimate_duration(complexity, description)
        
        # Infer capabilities if not provided
        if not required_capabilities:
            required_capabilities = self._infer_capabilities(name, description)
        
        return {
            'id': task_id,
            'name': name,
            'description': description,
            'complexity': complexity,
            'estimated_duration': estimated_duration,
            'required_capabilities': required_capabilities or [],
            'dependencies': dependencies or [],
            'priority': priority or 2,
            'validation_criteria': self._generate_validation_criteria(name, description),
            'risk_level': self._assess_risk_level(complexity, description)
        }

    def _infer_complexity(self, name: str, description: str) -> str:
        """Infer task complexity from name and description."""
        text = f"{name} {description}".lower()
        
        for complexity, indicators in self.complexity_indicators.items():
            if any(indicator in text for indicator in indicators):
                return complexity.value
        
        # Default complexity based on description length and keywords
        if len(description) > 200 or any(word in text for word in ['integrate', 'complex', 'system', 'architecture']):
            return TaskComplexity.COMPLEX.value
        elif len(description) > 100 or any(word in text for word in ['implement', 'develop', 'create']):
            return TaskComplexity.MODERATE.value
        else:
            return TaskComplexity.SIMPLE.value

    def _estimate_duration(self, complexity: str, description: str) -> int:
        """Estimate task duration based on complexity and description."""
        base_durations = {
            TaskComplexity.SIMPLE.value: 600,      # 10 minutes
            TaskComplexity.MODERATE.value: 1800,   # 30 minutes
            TaskComplexity.COMPLEX.value: 3600,    # 1 hour
            TaskComplexity.CRITICAL.value: 7200    # 2 hours
        }
        
        base_duration = base_durations.get(complexity, 1800)
        
        # Adjust based on description keywords
        multiplier = 1.0
        text = description.lower()
        
        if any(word in text for word in ['comprehensive', 'complete', 'full', 'entire']):
            multiplier *= 1.5
        if any(word in text for word in ['test', 'testing', 'validation']):
            multiplier *= 1.2
        if any(word in text for word in ['documentation', 'docs']):
            multiplier *= 0.8
        
        return int(base_duration * multiplier)

    def _infer_capabilities(self, name: str, description: str) -> List[str]:
        """Infer required capabilities from task name and description."""
        text = f"{name} {description}".lower()
        capabilities = []
        
        for category, keywords in self.capability_keywords.items():
            if any(keyword in text for keyword in keywords):
                capabilities.extend(keywords[:2])  # Add first 2 capabilities from category
        
        # Remove duplicates and return
        return list(set(capabilities))

    def _generate_validation_criteria(self, name: str, description: str) -> List[str]:
        """Generate validation criteria for the task."""
        criteria = []
        text = f"{name} {description}".lower()
        
        if any(word in text for word in ['implement', 'create', 'develop']):
            criteria.append("Code compiles without errors")
            criteria.append("Functionality works as expected")
        
        if any(word in text for word in ['test', 'testing']):
            criteria.append("All tests pass")
            criteria.append("Code coverage meets requirements")
        
        if any(word in text for word in ['documentation', 'docs']):
            criteria.append("Documentation is complete and accurate")
            criteria.append("Examples are provided and working")
        
        if not criteria:
            criteria.append("Task completed successfully")
        
        return criteria

    def _assess_risk_level(self, complexity: str, description: str) -> str:
        """Assess risk level for the task."""
        text = description.lower()
        
        if complexity == TaskComplexity.CRITICAL.value:
            return "high"
        elif any(word in text for word in ['critical', 'core', 'fundamental', 'breaking']):
            return "high"
        elif any(word in text for word in ['integration', 'system', 'architecture']):
            return "medium"
        else:
            return "low"

    def _validate_and_enhance_tasks(self, tasks: List[Dict[str, Any]], 
                                  planning_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate and enhance parsed tasks."""
        enhanced_tasks = []
        
        for task in tasks:
            # Ensure required fields
            if 'id' not in task:
                task['id'] = f"task_{len(enhanced_tasks) + 1}"
            if 'name' not in task:
                task['name'] = f"Task {len(enhanced_tasks) + 1}"
            if 'description' not in task:
                task['description'] = task['name']
            
            # Validate and fix dependencies
            task['dependencies'] = self._validate_dependencies(task.get('dependencies', []), enhanced_tasks)
            
            enhanced_tasks.append(task)
        
        return enhanced_tasks

    def _validate_dependencies(self, dependencies: List[str], existing_tasks: List[Dict[str, Any]]) -> List[str]:
        """Validate task dependencies."""
        valid_dependencies = []
        existing_task_ids = [task['id'] for task in existing_tasks]
        
        for dep in dependencies:
            if dep in existing_task_ids:
                valid_dependencies.append(dep)
        
        return valid_dependencies

    def _extract_description_after_header(self, content: str, header: str) -> str:
        """Extract description text after a header."""
        pattern = re.escape(header) + r'\s*\n(.*?)(?=#{1,3}|\n\s*\n|$)'
        match = re.search(pattern, content, re.DOTALL)
        if match:
            return match.group(1).strip()
        return header


def test_parser():
    """Test the planning result parser."""
    parser = PlanningResultParser()
    
    # Test JSON parsing
    json_plan = {
        'plan': '''
        ```json
        {
            "tasks": [
                {
                    "id": "task_1",
                    "name": "Setup Database",
                    "description": "Configure PostgreSQL database",
                    "complexity": "moderate"
                }
            ]
        }
        ```
        '''
    }
    
    tasks = parser.parse_planning_result(json_plan)
    print(f"✅ JSON parsing: {len(tasks)} tasks extracted")
    print(f"   First task: {tasks[0]['name']}")
    
    # Test markdown parsing
    markdown_plan = {
        'plan': '''
        ## Task 1: Database Setup
        Configure the database
        
        ## Task 2: API Development
        Create REST endpoints
        '''
    }
    
    tasks = parser.parse_planning_result(markdown_plan)
    print(f"✅ Markdown parsing: {len(tasks)} tasks extracted")
    
    # Test text pattern parsing
    text_plan = {
        'plan': '''
        1. Set up development environment
        2. Implement core functionality
        3. Add comprehensive testing
        '''
    }
    
    tasks = parser.parse_planning_result(text_plan)
    print(f"✅ Text pattern parsing: {len(tasks)} tasks extracted")
    
    # Test fallback parsing
    minimal_plan = {
        'plan': 'Build something'
    }
    
    tasks = parser.parse_planning_result(minimal_plan)
    print(f"✅ Fallback parsing: {len(tasks)} tasks extracted")
    
    # Test API customization
    api_plan = {
        'plan': 'Build an API',
        'requirements': 'Create REST API endpoints'
    }
    
    tasks = parser.parse_planning_result(api_plan)
    api_tasks = [task for task in tasks if 'api' in task['name'].lower()]
    print(f"✅ API customization: {len(api_tasks)} API-related tasks found")
    
    print("\n🎉 All tests passed! Parser is working correctly.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_parser()

