# Contexten CICD Dashboard

A comprehensive web interface for managing autonomous CICD flows and codebase analysis using the Codegen SDK.

## Features

### 🚀 Autonomous CICD Flows
- **Flow Creation**: Create custom CICD flows with specific requirements
- **Project Selection**: Select and pin GitHub projects from dropdown
- **Real-time Progress**: Monitor flow execution with live progress tracking
- **Flow Control**: Pause, resume, or cancel flows as needed
- **Multiple Projects**: Support for managing flows across multiple projects simultaneously

### 📊 Dashboard Overview
- **Statistics**: Real-time stats on active projects, running flows, and success rates
- **Recent Activity**: Timeline view of recent flow activities and completions
- **System Status**: Monitor health of orchestrator, GitHub, and Linear integrations
- **Quick Actions**: Fast access to common operations

### 🔧 Project Management
- **GitHub Integration**: Load and manage GitHub repositories
- **Project Pinning**: Pin frequently used projects for quick access
- **Project Actions**: Analyze projects, create flows, and view project-specific flows
- **Custom Projects**: Add custom GitHub repositories manually

### 📈 Analytics & Monitoring
- **Performance Charts**: Visualize flow success rates and execution times
- **Activity Distribution**: See breakdown of flow types and usage patterns
- **Export Data**: Export dashboard data for external analysis
- **Real-time Updates**: Auto-refresh data every 30 seconds

### ⚙️ Configuration
- **Codegen SDK**: Configure organization ID and API token
- **Flow Settings**: Set default timeouts and notification preferences
- **System Settings**: Manage dashboard behavior and preferences

## Getting Started

### Prerequisites
- Python 3.8+
- FastAPI
- Codegen SDK
- GitHub access token
- Linear API access (optional)

### Environment Variables
```bash
# Required for Codegen SDK integration
CODEGEN_ORG_ID=your_organization_id_here
CODEGEN_TOKEN=your_api_token_here

# Optional dashboard configuration
DASHBOARD_HOST=0.0.0.0
DASHBOARD_PORT=8080
DASHBOARD_DEBUG=false
DASHBOARD_SECRET_KEY=your_secret_key_here
```

### Installation
1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set environment variables:
```bash
export CODEGEN_ORG_ID="your_org_id"
export CODEGEN_TOKEN="your_token"
```

3. Start the dashboard:
```bash
python -m src.contexten.dashboard.app
```

4. Open your browser to `http://localhost:8080`

## Usage

### Creating a CICD Flow

1. **Select Project**: 
   - Navigate to the Projects tab
   - Click "Load Projects" to fetch your GitHub repositories
   - Select a project by clicking on it
   - Optionally pin the project for quick access

2. **Create Flow**:
   - Click "Create Flow" button or use the project's context menu
   - Fill in the flow details:
     - **Name**: Descriptive name for your flow
     - **Project**: Pre-selected or choose from dropdown
     - **Type**: Analysis, Testing, Deployment, Security, or Custom
     - **Requirements**: Detailed description of what you want to accomplish
     - **Priority**: Low, Medium, High, or Urgent
     - **Notifications**: Enable/disable completion notifications

3. **Monitor Progress**:
   - Switch to the Flows tab to see active flows
   - Watch real-time progress updates
   - View detailed flow information
   - Control flow execution (pause/cancel)

### Flow Types

#### Code Analysis
Comprehensive codebase analysis including:
- Code quality assessment
- Security vulnerability scanning
- Performance bottleneck identification
- Technical debt analysis
- Best practices compliance

#### Automated Testing
- Test suite execution
- Coverage analysis
- Test result reporting
- Regression testing
- Performance testing

#### Deployment
- Automated deployment to staging/production
- Health checks and validation
- Rollback capabilities
- Environment configuration

#### Security Scanning
- Vulnerability assessment
- Dependency security analysis
- Code security review
- Compliance checking

#### Custom Flows
- User-defined requirements
- Flexible execution based on specific needs
- Integration with existing tools and processes

### Project Management

#### Pinning Projects
- Pin frequently used projects for quick access
- Pinned projects appear in the sidebar
- Easy unpinning when no longer needed

#### Project Actions
- **Analyze**: Start comprehensive project analysis
- **Create Flow**: Launch new CICD flow for the project
- **View Flows**: See all flows associated with the project
- **GitHub Link**: Direct link to the repository

### Dashboard Navigation

#### Tabs
- **Dashboard**: Overview with stats and recent activity
- **Projects**: Project management and selection
- **Flows**: Active flow monitoring and control
- **Analytics**: Performance charts and insights
- **Settings**: Configuration and preferences

#### Real-time Updates
- Dashboard automatically refreshes every 30 seconds
- Flow progress updates in real-time
- System status monitoring
- Notification system for important events

## API Endpoints

### Dashboard Data
- `GET /api/dashboard/overview` - Get dashboard statistics
- `GET /api/system/status` - Get system health status

### Flow Management
- `POST /api/flows/create` - Create new flow
- `GET /api/flows/active` - Get active flows
- `POST /api/flows/{id}/pause` - Pause flow
- `POST /api/flows/{id}/cancel` - Cancel flow
- `GET /api/flows/{id}/details` - Get flow details

### Project Management
- `GET /api/projects` - Get available projects
- `POST /api/projects/add` - Add custom project
- `POST /api/projects/analyze` - Start project analysis
- `GET /api/projects/{name}/flows` - Get project flows

### Analytics
- `GET /api/analytics/dashboard` - Get analytics data
- `GET /api/export/dashboard-data` - Export dashboard data

### Settings
- `POST /api/settings/save` - Save configuration

## Integration with Codegen SDK

The dashboard integrates seamlessly with the Codegen SDK to execute flows:

```python
from codegen import Agent

# Initialize agent with your credentials
agent = Agent(org_id="your_org_id", token="your_token")

# Execute flow based on requirements
task = agent.run(prompt=flow_prompt)

# Monitor progress
while task.status not in ["completed", "failed"]:
    task.refresh()
    # Update flow progress in dashboard
```

## Customization

### Adding New Flow Types
1. Update the flow type dropdown in the HTML template
2. Add handling logic in the `create_flow_prompt()` function
3. Implement specific execution logic for the new type

### Custom Styling
- Modify `static/css/dashboard.css` for visual customization
- Update CSS variables for color scheme changes
- Add custom animations and transitions

### Additional Integrations
- Extend the dashboard to support other version control systems
- Add integration with additional project management tools
- Implement custom notification channels

## Troubleshooting

### Common Issues

1. **Codegen SDK not configured**
   - Ensure `CODEGEN_ORG_ID` and `CODEGEN_TOKEN` are set
   - Verify credentials are valid
   - Check network connectivity

2. **Projects not loading**
   - Verify GitHub access permissions
   - Check GitHub API rate limits
   - Ensure repository access is granted

3. **Flows not starting**
   - Check Codegen SDK configuration
   - Verify project permissions
   - Review flow requirements format

### Debug Mode
Enable debug mode for detailed logging:
```bash
export DASHBOARD_DEBUG=true
```

### Logs
Check application logs for detailed error information:
```bash
tail -f dashboard.log
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue in the GitHub repository
- Check the documentation
- Contact the development team

## Roadmap

### Upcoming Features
- [ ] Advanced flow templates
- [ ] Flow scheduling and automation
- [ ] Integration with more CI/CD platforms
- [ ] Enhanced analytics and reporting
- [ ] Mobile-responsive design improvements
- [ ] Multi-user support with role-based access
- [ ] Webhook integrations
- [ ] Custom dashboard widgets
- [ ] Flow dependency management
- [ ] Advanced notification system

