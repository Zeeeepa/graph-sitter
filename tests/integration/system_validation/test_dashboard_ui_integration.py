"""
Dashboard and UI Integration Testing Suite

Tests Linear & GitHub dashboard functionality, UI responsiveness,
real-time updates, notifications, and cross-browser compatibility.
"""

import pytest
import asyncio
import time
from typing import Dict, List, Any, Optional
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import json


class TestDashboardUIIntegration:
    """Test suite for dashboard and UI integration validation."""

    @pytest.fixture
    def mock_linear_client(self):
        """Mock Linear API client for testing."""
        mock_client = Mock()
        
        # Mock Linear API responses
        mock_client.get_issues.return_value = {
            "data": {
                "issues": {
                    "nodes": [
                        {
                            "id": "issue_1",
                            "title": "Test Issue 1",
                            "state": {"name": "In Progress"},
                            "assignee": {"name": "Test User"},
                            "createdAt": "2024-01-01T00:00:00Z"
                        },
                        {
                            "id": "issue_2", 
                            "title": "Test Issue 2",
                            "state": {"name": "Done"},
                            "assignee": {"name": "Test User 2"},
                            "createdAt": "2024-01-02T00:00:00Z"
                        }
                    ]
                }
            }
        }
        
        mock_client.create_issue.return_value = {
            "data": {
                "issueCreate": {
                    "issue": {
                        "id": "new_issue_123",
                        "title": "New Test Issue",
                        "url": "https://linear.app/test/issue/new_issue_123"
                    }
                }
            }
        }
        
        return mock_client

    @pytest.fixture
    def mock_github_client(self):
        """Mock GitHub API client for testing."""
        mock_client = Mock()
        
        # Mock GitHub API responses
        mock_client.get_repositories.return_value = [
            {
                "id": 1,
                "name": "test-repo-1",
                "full_name": "org/test-repo-1",
                "private": False,
                "html_url": "https://github.com/org/test-repo-1"
            },
            {
                "id": 2,
                "name": "test-repo-2", 
                "full_name": "org/test-repo-2",
                "private": True,
                "html_url": "https://github.com/org/test-repo-2"
            }
        ]
        
        mock_client.get_pull_requests.return_value = [
            {
                "id": 1,
                "number": 123,
                "title": "Test PR 1",
                "state": "open",
                "user": {"login": "test-user"},
                "html_url": "https://github.com/org/repo/pull/123"
            }
        ]
        
        return mock_client

    @pytest.fixture
    def mock_websocket_server(self):
        """Mock WebSocket server for real-time testing."""
        mock_server = Mock()
        mock_server.clients = set()
        
        async def mock_broadcast(message):
            for client in mock_server.clients:
                await client.send(json.dumps(message))
        
        mock_server.broadcast = mock_broadcast
        return mock_server

    def test_linear_dashboard_integration(self, mock_linear_client):
        """Test Linear dashboard functionality."""
        with patch('graph_sitter.integrations.linear.LinearClient', return_value=mock_linear_client):
            from graph_sitter.dashboard import LinearDashboard
            
            dashboard = LinearDashboard()
            
            # Test issue fetching
            issues = dashboard.get_issues()
            assert len(issues) == 2
            assert issues[0]["title"] == "Test Issue 1"
            assert issues[1]["state"]["name"] == "Done"
            
            # Test issue creation
            new_issue = dashboard.create_issue(
                title="Dashboard Test Issue",
                description="Created from dashboard test"
            )
            assert new_issue["id"] == "new_issue_123"
            assert "url" in new_issue
            
            # Verify API calls
            mock_linear_client.get_issues.assert_called_once()
            mock_linear_client.create_issue.assert_called_once()

    def test_github_dashboard_integration(self, mock_github_client):
        """Test GitHub dashboard functionality."""
        with patch('graph_sitter.integrations.github.GitHubClient', return_value=mock_github_client):
            from graph_sitter.dashboard import GitHubDashboard
            
            dashboard = GitHubDashboard()
            
            # Test repository fetching
            repos = dashboard.get_repositories()
            assert len(repos) == 2
            assert repos[0]["name"] == "test-repo-1"
            assert repos[1]["private"] is True
            
            # Test pull request fetching
            prs = dashboard.get_pull_requests("org/test-repo-1")
            assert len(prs) == 1
            assert prs[0]["number"] == 123
            assert prs[0]["state"] == "open"
            
            # Verify API calls
            mock_github_client.get_repositories.assert_called_once()
            mock_github_client.get_pull_requests.assert_called_once()

    def test_unified_dashboard_integration(self, mock_linear_client, mock_github_client):
        """Test unified dashboard combining Linear and GitHub data."""
        with patch('graph_sitter.integrations.linear.LinearClient', return_value=mock_linear_client), \
             patch('graph_sitter.integrations.github.GitHubClient', return_value=mock_github_client):
            
            from graph_sitter.dashboard import UnifiedDashboard
            
            dashboard = UnifiedDashboard()
            
            # Test unified data fetching
            unified_data = dashboard.get_unified_view()
            
            assert "linear_issues" in unified_data
            assert "github_repos" in unified_data
            assert "github_prs" in unified_data
            
            assert len(unified_data["linear_issues"]) == 2
            assert len(unified_data["github_repos"]) == 2
            assert len(unified_data["github_prs"]) == 1
            
            # Test cross-platform linking
            linked_data = dashboard.link_issues_to_prs()
            assert "linked_items" in linked_data

    def test_ui_responsiveness(self):
        """Test UI responsiveness across different screen sizes."""
        from graph_sitter.dashboard.ui import ResponsiveUI
        
        ui = ResponsiveUI()
        
        # Test different viewport sizes
        viewports = [
            {"width": 320, "height": 568},   # Mobile
            {"width": 768, "height": 1024},  # Tablet
            {"width": 1920, "height": 1080}, # Desktop
            {"width": 2560, "height": 1440}  # Large Desktop
        ]
        
        for viewport in viewports:
            layout = ui.get_responsive_layout(viewport["width"], viewport["height"])
            
            assert "columns" in layout
            assert "sidebar_width" in layout
            assert "content_width" in layout
            
            # Verify responsive behavior
            if viewport["width"] < 768:
                assert layout["columns"] == 1  # Single column on mobile
            elif viewport["width"] < 1200:
                assert layout["columns"] == 2  # Two columns on tablet
            else:
                assert layout["columns"] >= 3  # Multiple columns on desktop

    def test_real_time_updates(self, mock_websocket_server):
        """Test real-time updates and notifications."""
        with patch('graph_sitter.dashboard.websocket.WebSocketServer', return_value=mock_websocket_server):
            from graph_sitter.dashboard import RealTimeDashboard
            
            dashboard = RealTimeDashboard()
            
            # Mock WebSocket client
            mock_client = AsyncMock()
            mock_websocket_server.clients.add(mock_client)
            
            async def test_real_time_flow():
                # Test issue update notification
                await dashboard.notify_issue_update({
                    "type": "issue_updated",
                    "issue_id": "issue_1",
                    "changes": {"state": "Done"}
                })
                
                # Test PR update notification
                await dashboard.notify_pr_update({
                    "type": "pr_updated", 
                    "pr_id": 123,
                    "changes": {"state": "merged"}
                })
                
                # Verify notifications were sent
                assert mock_client.send.call_count == 2
                
                # Verify message content
                calls = mock_client.send.call_args_list
                issue_message = json.loads(calls[0][0][0])
                pr_message = json.loads(calls[1][0][0])
                
                assert issue_message["type"] == "issue_updated"
                assert pr_message["type"] == "pr_updated"
            
            # Run async test
            asyncio.run(test_real_time_flow())

    def test_notification_system(self):
        """Test notification system functionality."""
        from graph_sitter.dashboard.notifications import NotificationManager
        
        manager = NotificationManager()
        
        # Test notification creation
        notification = manager.create_notification(
            type="info",
            title="Test Notification",
            message="This is a test notification",
            priority="medium"
        )
        
        assert notification["id"] is not None
        assert notification["type"] == "info"
        assert notification["title"] == "Test Notification"
        assert notification["timestamp"] is not None
        
        # Test notification queuing
        manager.queue_notification(notification)
        queued_notifications = manager.get_queued_notifications()
        
        assert len(queued_notifications) == 1
        assert queued_notifications[0]["id"] == notification["id"]
        
        # Test notification delivery
        delivered = manager.deliver_notifications()
        assert len(delivered) == 1
        
        # Queue should be empty after delivery
        remaining = manager.get_queued_notifications()
        assert len(remaining) == 0

    def test_cross_browser_compatibility(self):
        """Test cross-browser compatibility."""
        from graph_sitter.dashboard.compatibility import BrowserCompatibility
        
        compatibility = BrowserCompatibility()
        
        # Test different browser user agents
        browsers = [
            {
                "name": "Chrome",
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            },
            {
                "name": "Firefox", 
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0"
            },
            {
                "name": "Safari",
                "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15"
            },
            {
                "name": "Edge",
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59"
            }
        ]
        
        for browser in browsers:
            features = compatibility.get_supported_features(browser["user_agent"])
            
            assert "websockets" in features
            assert "local_storage" in features
            assert "css_grid" in features
            assert "es6_modules" in features
            
            # All modern browsers should support these features
            assert features["websockets"] is True
            assert features["local_storage"] is True

    def test_dashboard_performance(self, mock_linear_client, mock_github_client):
        """Test dashboard performance under load."""
        with patch('graph_sitter.integrations.linear.LinearClient', return_value=mock_linear_client), \
             patch('graph_sitter.integrations.github.GitHubClient', return_value=mock_github_client):
            
            from graph_sitter.dashboard import PerformanceDashboard
            
            dashboard = PerformanceDashboard()
            
            # Test load time
            start_time = time.time()
            dashboard.load_all_data()
            load_time = time.time() - start_time
            
            assert load_time < 2.0  # Should load within 2 seconds
            
            # Test concurrent requests
            start_time = time.time()
            
            async def concurrent_requests():
                tasks = []
                for i in range(10):
                    task = asyncio.create_task(dashboard.async_get_data(f"request_{i}"))
                    tasks.append(task)
                
                results = await asyncio.gather(*tasks)
                return results
            
            results = asyncio.run(concurrent_requests())
            concurrent_time = time.time() - start_time
            
            assert len(results) == 10
            assert concurrent_time < 5.0  # Should handle 10 concurrent requests within 5 seconds

    def test_dashboard_caching(self, mock_linear_client):
        """Test dashboard caching mechanisms."""
        with patch('graph_sitter.integrations.linear.LinearClient', return_value=mock_linear_client):
            from graph_sitter.dashboard import CachedDashboard
            
            dashboard = CachedDashboard()
            
            # First request - should hit API
            start_time = time.time()
            data1 = dashboard.get_cached_issues()
            first_request_time = time.time() - start_time
            
            # Second request - should hit cache
            start_time = time.time()
            data2 = dashboard.get_cached_issues()
            second_request_time = time.time() - start_time
            
            # Verify data is the same
            assert data1 == data2
            
            # Cache should be faster
            assert second_request_time < first_request_time
            
            # Verify API was only called once
            assert mock_linear_client.get_issues.call_count == 1

    def test_dashboard_error_handling(self, mock_linear_client):
        """Test dashboard error handling."""
        # Mock API failure
        mock_linear_client.get_issues.side_effect = Exception("API Error")
        
        with patch('graph_sitter.integrations.linear.LinearClient', return_value=mock_linear_client):
            from graph_sitter.dashboard import RobustDashboard
            
            dashboard = RobustDashboard()
            
            # Test graceful error handling
            result = dashboard.safe_get_issues()
            
            assert result["status"] == "error"
            assert "error_message" in result
            assert result["fallback_data"] is not None

    def test_dashboard_accessibility(self):
        """Test dashboard accessibility features."""
        from graph_sitter.dashboard.accessibility import AccessibilityChecker
        
        checker = AccessibilityChecker()
        
        # Test ARIA labels
        aria_compliance = checker.check_aria_compliance()
        assert aria_compliance["score"] >= 0.8  # Should have good ARIA compliance
        
        # Test keyboard navigation
        keyboard_nav = checker.check_keyboard_navigation()
        assert keyboard_nav["tab_order"] is True
        assert keyboard_nav["focus_indicators"] is True
        
        # Test color contrast
        contrast_check = checker.check_color_contrast()
        assert contrast_check["meets_wcag_aa"] is True

    def test_dashboard_data_export(self, mock_linear_client, mock_github_client):
        """Test dashboard data export functionality."""
        with patch('graph_sitter.integrations.linear.LinearClient', return_value=mock_linear_client), \
             patch('graph_sitter.integrations.github.GitHubClient', return_value=mock_github_client):
            
            from graph_sitter.dashboard import DataExporter
            
            exporter = DataExporter()
            
            # Test CSV export
            csv_data = exporter.export_to_csv("issues")
            assert csv_data is not None
            assert "id,title,state" in csv_data  # Should contain headers
            
            # Test JSON export
            json_data = exporter.export_to_json("repositories")
            assert isinstance(json_data, str)
            parsed_data = json.loads(json_data)
            assert isinstance(parsed_data, list)
            
            # Test PDF export (mock)
            pdf_data = exporter.export_to_pdf("dashboard_summary")
            assert pdf_data is not None
            assert len(pdf_data) > 0

    def test_dashboard_customization(self):
        """Test dashboard customization features."""
        from graph_sitter.dashboard.customization import DashboardCustomizer
        
        customizer = DashboardCustomizer()
        
        # Test widget configuration
        widget_config = {
            "issues_widget": {"position": {"x": 0, "y": 0}, "size": {"width": 6, "height": 4}},
            "repos_widget": {"position": {"x": 6, "y": 0}, "size": {"width": 6, "height": 4}},
            "prs_widget": {"position": {"x": 0, "y": 4}, "size": {"width": 12, "height": 6}}
        }
        
        customizer.save_layout(widget_config)
        loaded_config = customizer.load_layout()
        
        assert loaded_config == widget_config
        
        # Test theme customization
        theme = {
            "primary_color": "#007bff",
            "secondary_color": "#6c757d",
            "background_color": "#ffffff",
            "text_color": "#212529"
        }
        
        customizer.save_theme(theme)
        loaded_theme = customizer.load_theme()
        
        assert loaded_theme == theme

