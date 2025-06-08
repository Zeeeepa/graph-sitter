#!/usr/bin/env python3
"""
Test suite for PlanningResultParser

Tests various parsing strategies and edge cases for Codegen SDK planning results.
"""

import json
import pytest
from typing import Dict, Any, List

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from contexten.extensions.prefect.workflow_pipeline import (
    PlanningResultParser, 
    TaskComplexity,
    ParsingStrategy
)


class TestPlanningResultParser:
    """Test cases for PlanningResultParser."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = PlanningResultParser()
    
    def test_json_structured_parsing(self):
        """Test parsing of JSON-structured planning results."""
        planning_result = {
            'plan': '''
            ```json
            {
                "tasks": [
                    {
                        "id": "task_1",
                        "name": "Setup Database",
                        "description": "Configure PostgreSQL database with initial schema",
                        "complexity": "moderate",
                        "estimated_duration": 1800,
                        "required_capabilities": ["database", "configuration"],
                        "dependencies": [],
                        "priority": 3
                    },
                    {
                        "id": "task_2", 
                        "name": "Implement API Endpoints",
                        "description": "Create REST API endpoints for user management",
                        "complexity": "complex",
                        "estimated_duration": 3600,
                        "required_capabilities": ["api_development", "programming"],
                        "dependencies": ["task_1"],
                        "priority": 3
                    }
                ]
            }
            ```
            '''
        }
        
        tasks = self.parser.parse_planning_result(planning_result)
        
        assert len(tasks) == 2
        assert tasks[0]['id'] == 'task_1'
        assert tasks[0]['name'] == 'Setup Database'
        assert tasks[0]['complexity'] == 'moderate'
        assert tasks[1]['dependencies'] == ['task_1']
    
    def test_markdown_structured_parsing(self):
        """Test parsing of markdown-structured planning results."""
        planning_result = {
            'plan': '''
            # Implementation Plan
            
            ## Task 1: Database Setup
            Configure the database schema and initial data
            
            ## Task 2: API Development  
            Implement REST API endpoints
            
            ## Task 3: Frontend Integration
            Connect frontend to backend APIs
            '''
        }
        
        tasks = self.parser.parse_planning_result(planning_result)
        
        assert len(tasks) >= 2
        assert any('Database Setup' in task['name'] for task in tasks)
        assert any('API Development' in task['name'] for task in tasks)
    
    def test_text_pattern_parsing(self):
        """Test parsing of text-based planning results."""
        planning_result = {
            'plan': '''
            1. Set up development environment
            2. Implement core functionality
            3. Add comprehensive testing
            4. Deploy to staging environment
            5. Perform user acceptance testing
            '''
        }
        
        tasks = self.parser.parse_planning_result(planning_result)
        
        assert len(tasks) >= 4
        assert any('development environment' in task['name'].lower() for task in tasks)
        assert any('testing' in task['name'].lower() for task in tasks)
    
    def test_ai_assisted_parsing(self):
        """Test AI-assisted parsing for natural language plans."""
        planning_result = {
            'plan': '''
            The implementation will start with setting up the basic infrastructure.
            We need to configure the database and establish the connection layer.
            
            Next, we'll implement the core business logic including user authentication
            and authorization mechanisms. This will involve creating secure endpoints
            and implementing proper session management.
            
            Finally, we'll add comprehensive testing and documentation to ensure
            the system is production-ready and maintainable.
            '''
        }
        
        tasks = self.parser.parse_planning_result(planning_result)
        
        assert len(tasks) >= 2
        # Should extract meaningful task names from the content
        assert all(len(task['name']) > 10 for task in tasks)
    
    def test_fallback_parsing(self):
        """Test fallback parsing when other strategies fail."""
        planning_result = {
            'plan': 'Invalid or minimal content'
        }
        
        tasks = self.parser.parse_planning_result(planning_result)
        
        # Should return default tasks
        assert len(tasks) >= 3
        assert any('analysis' in task['name'].lower() for task in tasks)
        assert any('implementation' in task['name'].lower() for task in tasks)
        assert any('testing' in task['name'].lower() for task in tasks)
    
    def test_complexity_inference(self):
        """Test complexity inference from task descriptions."""
        test_cases = [
            ("Simple update", "Update README file", TaskComplexity.SIMPLE),
            ("Moderate task", "Implement user authentication system", TaskComplexity.MODERATE),
            ("Complex integration", "Integrate complex microservices architecture", TaskComplexity.COMPLEX),
            ("Critical system", "Critical core system refactoring", TaskComplexity.CRITICAL)
        ]
        
        for name, description, expected_complexity in test_cases:
            complexity = self.parser._infer_complexity(name, description)
            assert complexity == expected_complexity.value
    
    def test_duration_estimation(self):
        """Test duration estimation based on complexity and content."""
        test_cases = [
            (TaskComplexity.SIMPLE.value, "Quick fix", 600),
            (TaskComplexity.MODERATE.value, "Standard implementation", 1800),
            (TaskComplexity.COMPLEX.value, "Complex system integration", 3600),
            (TaskComplexity.CRITICAL.value, "Critical infrastructure", 7200)
        ]
        
        for complexity, description, min_expected in test_cases:
            duration = self.parser._estimate_duration(complexity, description)
            assert duration >= min_expected * 0.8  # Allow some variance
            assert duration <= min_expected * 2.0   # But not too much
    
    def test_capability_inference(self):
        """Test capability inference from task descriptions."""
        test_cases = [
            ("Implement API endpoints", ["code_generation", "programming", "api_development"]),
            ("Write comprehensive tests", ["testing", "quality_assurance"]),
            ("Update documentation", ["documentation", "writing"]),
            ("Deploy to production", ["deployment", "devops"])
        ]
        
        for description, expected_capabilities in test_cases:
            capabilities = self.parser._infer_capabilities("Task", description)
            # Should contain at least some of the expected capabilities
            assert any(cap in capabilities for cap in expected_capabilities)
    
    def test_dependency_validation(self):
        """Test dependency validation and cleanup."""
        existing_tasks = [
            {'id': 'task_1', 'name': 'Task 1'},
            {'id': 'task_2', 'name': 'Task 2'}
        ]
        
        # Valid dependencies
        valid_deps = self.parser._validate_dependencies(['task_1', 'task_2'], existing_tasks)
        assert valid_deps == ['task_1', 'task_2']
        
        # Invalid dependencies should be filtered out
        invalid_deps = self.parser._validate_dependencies(['task_1', 'nonexistent'], existing_tasks)
        assert invalid_deps == ['task_1']
    
    def test_validation_criteria_generation(self):
        """Test generation of validation criteria."""
        test_cases = [
            ("Implement feature", "Code compiles without errors"),
            ("Add tests", "All tests pass"),
            ("Write docs", "Documentation is complete")
        ]
        
        for description, expected_criterion in test_cases:
            criteria = self.parser._generate_validation_criteria("Task", description)
            assert any(expected_criterion.lower() in criterion.lower() for criterion in criteria)
    
    def test_risk_assessment(self):
        """Test risk level assessment."""
        test_cases = [
            (TaskComplexity.SIMPLE.value, "Simple update", "low"),
            (TaskComplexity.MODERATE.value, "System integration", "medium"),
            (TaskComplexity.COMPLEX.value, "Architecture change", "medium"),
            (TaskComplexity.CRITICAL.value, "Core system", "high")
        ]
        
        for complexity, description, expected_risk in test_cases:
            risk = self.parser._assess_risk_level(complexity, description)
            assert risk == expected_risk
    
    def test_empty_planning_result(self):
        """Test handling of empty planning results."""
        planning_result = {}
        
        tasks = self.parser.parse_planning_result(planning_result)
        
        # Should fall back to default tasks
        assert len(tasks) >= 3
        assert all('id' in task for task in tasks)
        assert all('name' in task for task in tasks)
    
    def test_malformed_json_handling(self):
        """Test handling of malformed JSON in planning results."""
        planning_result = {
            'plan': '''
            ```json
            {
                "tasks": [
                    {
                        "id": "task_1",
                        "name": "Incomplete task"
                        // Missing closing brace
            ```
            '''
        }
        
        tasks = self.parser.parse_planning_result(planning_result)
        
        # Should fall back gracefully
        assert len(tasks) >= 1
    
    def test_api_requirement_customization(self):
        """Test customization based on API requirements."""
        planning_result = {
            'plan': 'Build an API system',
            'requirements': 'Create REST API endpoints for user management'
        }
        
        tasks = self.parser.parse_planning_result(planning_result)
        
        # Should include API-specific tasks
        task_names = [task['name'].lower() for task in tasks]
        assert any('api' in name for name in task_names)
    
    def test_task_enhancement_and_validation(self):
        """Test task enhancement and validation process."""
        raw_tasks = [
            {'name': 'Task without ID'},
            {'id': 'task_2'},  # Missing name
            {'id': 'task_3', 'name': 'Complete task', 'dependencies': ['task_1', 'nonexistent']}
        ]
        
        enhanced_tasks = self.parser._validate_and_enhance_tasks(raw_tasks, {})
        
        # Should have IDs for all tasks
        assert all('id' in task for task in enhanced_tasks)
        # Should have names for all tasks
        assert all('name' in task for task in enhanced_tasks)
        # Should clean up invalid dependencies
        assert enhanced_tasks[2]['dependencies'] == []  # No valid dependencies exist yet


class TestPlanningParserIntegration:
    """Integration tests for planning parser with real-world scenarios."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = PlanningResultParser()
    
    def test_complex_real_world_plan(self):
        """Test parsing of a complex, real-world planning result."""
        planning_result = {
            'plan': '''
            # E-commerce Platform Implementation Plan
            
            ## Phase 1: Foundation
            1. **Database Design** - Design and implement the core database schema
            2. **Authentication System** - Implement user registration and login
            3. **Basic API Framework** - Set up REST API structure
            
            ## Phase 2: Core Features  
            4. **Product Management** - CRUD operations for products
            5. **Shopping Cart** - Implement cart functionality
            6. **Order Processing** - Handle order creation and management
            
            ## Phase 3: Advanced Features
            7. **Payment Integration** - Integrate with payment providers
            8. **Inventory Management** - Track product inventory
            9. **Admin Dashboard** - Create administrative interface
            
            ## Phase 4: Quality & Deployment
            10. **Comprehensive Testing** - Unit, integration, and E2E tests
            11. **Performance Optimization** - Optimize database queries and API responses
            12. **Production Deployment** - Deploy to production environment
            ''',
            'requirements': 'Build a complete e-commerce platform with payment processing'
        }
        
        tasks = self.parser.parse_planning_result(planning_result)
        
        # Should extract multiple tasks
        assert len(tasks) >= 8
        
        # Should have proper task structure
        for task in tasks:
            assert 'id' in task
            assert 'name' in task
            assert 'description' in task
            assert 'complexity' in task
            assert 'estimated_duration' in task
            assert 'required_capabilities' in task
            assert isinstance(task['required_capabilities'], list)
        
        # Should infer appropriate complexities
        complexities = [task['complexity'] for task in tasks]
        assert TaskComplexity.SIMPLE.value in complexities
        assert TaskComplexity.MODERATE.value in complexities
        
        # Should have reasonable durations
        durations = [task['estimated_duration'] for task in tasks]
        assert all(300 <= duration <= 10800 for duration in durations)  # 5 min to 3 hours
    
    def test_multiple_parsing_strategies_fallback(self):
        """Test that parser tries multiple strategies and falls back appropriately."""
        # This should trigger multiple parsing attempts
        planning_result = {
            'plan': '''
            Some unstructured text that doesn't match any specific pattern.
            It mentions implementing features and adding tests.
            There's also documentation work to be done.
            '''
        }
        
        tasks = self.parser.parse_planning_result(planning_result)
        
        # Should still produce meaningful tasks via fallback
        assert len(tasks) >= 3
        assert all(task['name'] for task in tasks)
        assert all(task['description'] for task in tasks)


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])

