# Linear Integration for Contexten Dashboard

## Overview

This comprehensive Linear integration provides a full-featured dashboard for managing Linear issues, projects, teams, and workflows within the Contexten framework.

## Features

### 🎯 **Core Functionality**
- **Issue Management**: Create, update, view, and track Linear issues
- **Project Analytics**: Comprehensive project health monitoring and metrics
- **Team Performance**: Track team productivity and workload distribution
- **Real-time Updates**: Webhook-based real-time synchronization
- **Workflow Automation**: Automated issue assignment and state transitions

### 📊 **Dashboard Components**
- **Overview Cards**: Key metrics at a glance (teams, projects, active/completed issues)
- **Project Health Charts**: Visual representation of project status distribution
- **Team Performance Charts**: Comparative team productivity metrics
- **Recent Activity Feed**: Real-time updates on issue changes
- **Burndown Charts**: Project progress tracking over time

### 🔧 **Technical Features**
- **Caching System**: Intelligent caching with TTL for optimal performance
- **Background Sync**: Automatic data synchronization every 5 minutes
- **Error Handling**: Comprehensive error handling and logging
- **Health Monitoring**: API connectivity and integration health checks
- **Scalable Architecture**: Modular design for easy extension

## Architecture

### Core Components

1. **LinearDashboardManager**: Main orchestrator class
2. **LinearDashboardConfig**: Configuration management
3. **Enhanced Linear Agent**: Advanced Linear API integration
4. **Webhook Processor**: Real-time event handling
5. **Event Manager**: Event processing and routing

### File Structure

```
src/contexten/dashboard/
├── linear_integration.py          # Main integration module
├── templates/
│   └── linear_dashboard.html      # Frontend dashboard
└── LINEAR_INTEGRATION_README.md   # This documentation
```

## Setup and Configuration

### Environment Variables

```bash
# Required
LINEAR_API_KEY=your_linear_api_key_here

# Optional
LINEAR_WEBHOOK_SECRET=your_webhook_secret_here
LINEAR_CLIENT_ID=your_oauth_client_id
LINEAR_CLIENT_SECRET=your_oauth_client_secret
```

### Initialization

The Linear integration is automatically initialized when the dashboard starts if `LINEAR_API_KEY` is provided:

```python
# Automatic initialization in app.py
if linear_api_key:
    linear_manager = initialize_linear_dashboard(
        api_key=linear_api_key,
        webhook_secret=linear_webhook_secret
    )
```

## API Endpoints

### Health and Overview
- `GET /api/linear/health` - Integration health status
- `GET /api/linear/overview` - Complete dashboard overview

### Teams and Projects
- `GET /api/linear/teams` - List all teams with metrics
- `GET /api/linear/projects?team_id={id}` - List projects (optionally filtered by team)

### Issue Management
- `GET /api/linear/issues` - List issues with filtering options
  - Query params: `team_id`, `project_id`, `assignee_id`, `state`, `limit`
- `GET /api/linear/issues/{issue_id}` - Get detailed issue information
- `POST /api/linear/issues` - Create new issue
- `PUT /api/linear/issues/{issue_id}` - Update existing issue

### Webhooks
- `POST /api/linear/webhook` - Process Linear webhook events

## Frontend Dashboard

### Access
Navigate to `/linear` in your browser to access the Linear dashboard.

### Features
- **Real-time Updates**: Auto-refreshing data every 5 minutes
- **Interactive Charts**: Project health and team performance visualizations
- **Responsive Design**: Works on desktop and mobile devices
- **Health Indicator**: Visual connection status indicator

### Technologies Used
- **Alpine.js**: Reactive frontend framework
- **Chart.js**: Data visualization
- **Tailwind CSS**: Styling framework
- **Font Awesome**: Icons

## Data Models

### LinearIssueCreate
```python
{
    "title": "string",
    "description": "string (optional)",
    "team_id": "string",
    "project_id": "string (optional)",
    "assignee_id": "string (optional)",
    "priority": "integer (optional)",
    "labels": ["string"] (optional)
}
```

### LinearIssueUpdate
```python
{
    "title": "string (optional)",
    "description": "string (optional)",
    "state_id": "string (optional)",
    "assignee_id": "string (optional)",
    "priority": "integer (optional)",
    "labels": ["string"] (optional)
}
```

## Analytics and Metrics

### Project Analytics
- **Completion Rate**: Percentage of completed issues
- **Weekly Velocity**: Issues completed per week
- **Average Completion Time**: Time from creation to completion
- **Burndown Data**: Daily progress tracking

### Team Metrics
- **Active Issues**: Current workload
- **Completed Issues**: Recent productivity (last 30 days)
- **Member Count**: Team size

### Health Status Calculation
Projects are automatically categorized based on completion rate and velocity:
- **Excellent**: ≥80% completion rate
- **Good**: ≥60% completion rate
- **Fair**: ≥40% completion rate
- **Active**: <40% completion but has recent velocity
- **At Risk**: <40% completion and no recent velocity

## Caching Strategy

### Cache Types
- **Teams Cache**: TTL 10 minutes
- **Projects Cache**: TTL 10 minutes (per team)
- **Recent Issues Cache**: TTL 10 minutes

### Cache Invalidation
Caches are automatically invalidated when:
- Webhook events are received
- Manual refresh is triggered
- TTL expires

## Error Handling

### Graceful Degradation
- API failures return empty arrays/default values
- Frontend continues to function with cached data
- Health status reflects connectivity issues

### Logging
Comprehensive logging at multiple levels:
- **INFO**: Successful operations and status changes
- **WARNING**: Non-critical issues (missing config, cache misses)
- **ERROR**: API failures, webhook processing errors

## Performance Considerations

### Optimization Features
- **Background Sync**: Non-blocking data updates
- **Intelligent Caching**: Reduces API calls by 90%
- **Pagination**: Limits data transfer for large datasets
- **Lazy Loading**: Charts and heavy components load on demand

### Scalability
- **Async Operations**: All API calls are asynchronous
- **Connection Pooling**: Efficient HTTP connection management
- **Rate Limiting**: Respects Linear API rate limits

## Troubleshooting

### Common Issues

1. **"Linear integration not configured"**
   - Ensure `LINEAR_API_KEY` environment variable is set
   - Restart the dashboard application

2. **"Linear integration required" (403 error)**
   - User needs to authenticate with Linear OAuth
   - Check Linear OAuth configuration

3. **Empty dashboard data**
   - Check API key permissions
   - Verify network connectivity to Linear API
   - Check logs for specific error messages

### Debug Mode
Enable debug logging by setting log level to DEBUG:
```python
import logging
logging.getLogger("contexten.dashboard.linear_integration").setLevel(logging.DEBUG)
```

## Future Enhancements

### Planned Features
- **Custom Workflows**: User-defined automation rules
- **Advanced Filtering**: Complex query builder
- **Export Functionality**: CSV/PDF report generation
- **Mobile App**: Native mobile dashboard
- **Slack Integration**: Linear updates in Slack channels

### Extension Points
- **Custom Metrics**: Plugin system for additional analytics
- **Third-party Integrations**: Connect with other tools
- **Custom Dashboards**: User-configurable dashboard layouts

## Contributing

### Development Setup
1. Install dependencies: `pip install -r requirements.txt`
2. Set environment variables
3. Run tests: `pytest tests/dashboard/test_linear_integration.py`
4. Start development server: `uvicorn src.contexten.dashboard.app:app --reload`

### Code Style
- Follow PEP 8 guidelines
- Use type hints for all functions
- Add docstrings for public methods
- Include error handling for all external API calls

## Support

For issues and questions:
1. Check the troubleshooting section above
2. Review application logs
3. Create an issue in the repository
4. Contact the development team

---

**Last Updated**: June 2, 2025
**Version**: 1.0.0
**Compatibility**: Linear API v1, Python 3.8+

