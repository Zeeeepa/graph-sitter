// Contexten Dashboard JavaScript

// Global variables
let currentProject = null;
let integrationStatus = {};
let chatThreadId = null;
let activeAgents = {};
let monitoringInterval = null;

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    console.log('Contexten Dashboard loaded');
    
    // Check for any initialization tasks
    checkIntegrationStatus();
    startMonitoring();
    
    // Start advanced monitoring
    startAdvancedMonitoring();
    
    // Load recent analyses from localStorage
    const recentAnalyses = JSON.parse(localStorage.getItem('recentAIAnalyses') || '[]');
    if (recentAnalyses.length > 0) {
        updateRecentAnalyses({ task_type: '', target: '', confidence_score: 0 }); // Trigger display update
    }
});

// Chat functionality
async function sendMessage() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();
    
    if (!message) return;
    
    // Add user message to chat
    addMessageToChat(message, 'user');
    input.value = '';
    
    // Show typing indicator
    showTypingIndicator();
    
    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                thread_id: chatThreadId,
                project_id: currentProject?.full_name
            })
        });
        
        const data = await response.json();
        
        // Remove typing indicator
        hideTypingIndicator();
        
        if (response.ok) {
            // Add assistant response
            addMessageToChat(data.response, 'assistant');
            chatThreadId = data.thread_id;
            
            // If the response includes a plan, show it
            if (data.plan) {
                showPlan(data.plan);
            }
            
            // If agents were created, update the agents panel
            if (data.agents) {
                updateActiveAgents(data.agents);
            }
        } else {
            addMessageToChat('Sorry, I encountered an error. Please try again.', 'assistant');
        }
    } catch (error) {
        console.error('Error sending message:', error);
        hideTypingIndicator();
        addMessageToChat('Sorry, I encountered an error. Please try again.', 'assistant');
    }
}

function addMessageToChat(message, sender) {
    const messagesContainer = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message`;
    
    const now = new Date();
    const timeString = now.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
    
    if (sender === 'user') {
        messageDiv.innerHTML = `
            <div class="message-content">
                <strong>You:</strong> ${message}
            </div>
            <div class="message-time">${timeString}</div>
        `;
    } else {
        messageDiv.innerHTML = `
            <div class="message-content">
                <i class="fas fa-robot me-2"></i>
                <strong>AI Assistant:</strong> ${message}
            </div>
            <div class="message-time">${timeString}</div>
        `;
    }
    
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function showTypingIndicator() {
    const messagesContainer = document.getElementById('chat-messages');
    const typingDiv = document.createElement('div');
    typingDiv.id = 'typing-indicator';
    typingDiv.className = 'typing-indicator';
    typingDiv.innerHTML = `
        <i class="fas fa-robot me-2"></i>
        <span>AI Assistant is thinking</span>
        <div class="typing-dots ms-2">
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
        </div>
    `;
    
    messagesContainer.appendChild(typingDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function hideTypingIndicator() {
    const typingIndicator = document.getElementById('typing-indicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
}

function handleChatKeyPress(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
}

function clearChat() {
    const messagesContainer = document.getElementById('chat-messages');
    messagesContainer.innerHTML = `
        <div class="message assistant-message">
            <div class="message-content">
                <i class="fas fa-robot me-2"></i>
                <strong>AI Assistant:</strong> Hello! I'm here to help you create structured plans for your projects. 
                Describe what you'd like to accomplish, and I'll create a comprehensive implementation plan with Linear issues and GitHub integration.
            </div>
            <div class="message-time">${new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</div>
        </div>
    `;
    chatThreadId = null;
}

function toggleChat() {
    const chatCard = document.querySelector('.col-md-8 .card');
    const toggleButton = document.getElementById('chat-toggle');
    
    if (chatCard.classList.contains('chat-expanded')) {
        chatCard.classList.remove('chat-expanded');
        toggleButton.innerHTML = '<i class="fas fa-expand"></i> Expand';
    } else {
        chatCard.classList.add('chat-expanded');
        toggleButton.innerHTML = '<i class="fas fa-compress"></i> Minimize';
    }
}

// Project management functions
async function loadProjects() {
    try {
        const response = await fetch('/api/projects');
        const data = await response.json();
        
        const projectsList = document.getElementById('projects-list');
        if (data.projects && data.projects.length > 0) {
            projectsList.innerHTML = data.projects.map(project => `
                <div class="project-item mb-2 p-2 border rounded" onclick="selectProject('${project.full_name}', '${project.name}')">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <h6 class="mb-1">${project.name}</h6>
                            <small class="text-muted">${project.description || 'No description'}</small>
                        </div>
                        <div>
                            <span class="badge bg-secondary">${project.language || 'Unknown'}</span>
                        </div>
                    </div>
                </div>
            `).join('');
        } else {
            projectsList.innerHTML = '<p class="text-muted">No projects found</p>';
        }
    } catch (error) {
        console.error('Error loading projects:', error);
        showAlert('Failed to load projects', 'danger');
    }
}

function selectProject(fullName, name) {
    currentProject = { full_name: fullName, name: name };
    
    // Update project display
    const projectsList = document.getElementById('projects-list');
    projectsList.innerHTML = `
        <div class="selected-project p-3 border rounded bg-light">
            <h6><i class="fas fa-folder-open me-2"></i>${name}</h6>
            <small class="text-muted">${fullName}</small>
            <div class="mt-2">
                <button class="btn btn-outline-danger btn-sm" onclick="clearProjectSelection()">
                    <i class="fas fa-times"></i> Clear
                </button>
            </div>
        </div>
    `;
    
    // Add message to chat about project selection
    addMessageToChat(`Selected project: ${name}. You can now describe what you'd like to accomplish with this project.`, 'assistant');
}

function clearProjectSelection() {
    currentProject = null;
    document.getElementById('projects-list').innerHTML = `
        <div class="text-center text-muted">
            <i class="fas fa-folder fa-2x mb-2"></i>
            <p>Click "Load Projects" to see your repositories</p>
        </div>
    `;
}

// Agent management
function updateActiveAgents(agents) {
    const agentsContainer = document.getElementById('active-agents');
    
    if (agents && agents.length > 0) {
        agentsContainer.innerHTML = agents.map(agent => `
            <div class="agent-card">
                <div class="agent-status">
                    <div class="d-flex align-items-center">
                        <div class="agent-status-indicator agent-status-${agent.status}"></div>
                        <div>
                            <h6 class="mb-0">${agent.name}</h6>
                            <small class="text-muted">${agent.type}</small>
                        </div>
                    </div>
                    <button class="btn btn-outline-danger btn-sm" onclick="stopAgent('${agent.id}')">
                        <i class="fas fa-stop"></i>
                    </button>
                </div>
                <div class="mt-2">
                    <small class="text-muted">${agent.description}</small>
                </div>
            </div>
        `).join('');
        
        // Store active agents
        activeAgents = agents.reduce((acc, agent) => {
            acc[agent.id] = agent;
            return acc;
        }, {});
    } else {
        agentsContainer.innerHTML = `
            <div class="text-center text-muted">
                <i class="fas fa-robot fa-2x mb-2"></i>
                <p>No active agents</p>
            </div>
        `;
    }
}

async function stopAgent(agentId) {
    try {
        const response = await fetch(`/api/agents/${agentId}/stop`, {
            method: 'POST'
        });
        
        if (response.ok) {
            // Remove agent from active agents
            delete activeAgents[agentId];
            updateActiveAgents(Object.values(activeAgents));
            showAlert('Agent stopped successfully', 'success');
        } else {
            showAlert('Failed to stop agent', 'danger');
        }
    } catch (error) {
        console.error('Error stopping agent:', error);
        showAlert('Failed to stop agent', 'danger');
    }
}

// Monitoring functions
function startMonitoring() {
    // Start monitoring for real-time updates
    monitoringInterval = setInterval(updateMonitoringData, 10000); // Update every 10 seconds
    updateMonitoringData(); // Initial update
}

async function updateMonitoringData() {
    try {
        const response = await fetch('/api/monitoring/status');
        if (response.ok) {
            const data = await response.json();
            
            // Update monitoring counts
            document.getElementById('linear-issues-count').textContent = data.linear_issues || 0;
            document.getElementById('pr-count').textContent = data.pull_requests || 0;
            document.getElementById('comments-count').textContent = data.comments || 0;
            document.getElementById('branches-count').textContent = data.branches || 0;
            
            // Update activity feed
            if (data.recent_activity && data.recent_activity.length > 0) {
                updateActivityFeed(data.recent_activity);
            }
        }
    } catch (error) {
        console.error('Error updating monitoring data:', error);
    }
}

function updateActivityFeed(activities) {
    const activityFeed = document.getElementById('activity-feed');
    
    if (activities.length > 0) {
        activityFeed.innerHTML = activities.map(activity => `
            <div class="activity-item">
                <div class="activity-icon">
                    <i class="${getActivityIcon(activity.type)} text-${getActivityColor(activity.type)}"></i>
                </div>
                <div class="activity-content">
                    <div>${activity.description}</div>
                    <div class="activity-time">${formatTime(activity.timestamp)}</div>
                </div>
            </div>
        `).join('');
    }
}

function getActivityIcon(type) {
    const icons = {
        'linear_issue': 'fas fa-tasks',
        'pull_request': 'fas fa-code-branch',
        'comment': 'fas fa-comment',
        'branch': 'fas fa-git-alt',
        'agent': 'fas fa-robot'
    };
    return icons[type] || 'fas fa-circle';
}

function getActivityColor(type) {
    const colors = {
        'linear_issue': 'primary',
        'pull_request': 'success',
        'comment': 'warning',
        'branch': 'info',
        'agent': 'secondary'
    };
    return colors[type] || 'secondary';
}

function formatTime(timestamp) {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now - date;
    
    if (diff < 60000) return 'Just now';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
    return date.toLocaleDateString();
}

// Advanced Analytics Functions
async function refreshAnalytics() {
    try {
        showLoadingOverlay('analytics');
        
        const response = await fetch('/api/analytics/refresh', {
            method: 'POST'
        });
        
        if (response.ok) {
            const data = await response.json();
            updateAnalyticsDisplay(data);
            showAlert('Analytics refreshed successfully', 'success');
        } else {
            showAlert('Failed to refresh analytics', 'danger');
        }
    } catch (error) {
        console.error('Error refreshing analytics:', error);
        showAlert('Failed to refresh analytics', 'danger');
    } finally {
        hideLoadingOverlay('analytics');
    }
}

async function runComprehensiveAnalysis() {
    if (!currentProject) {
        showAlert('Please select a project first', 'warning');
        return;
    }
    
    try {
        showLoadingOverlay('analytics');
        
        const response = await fetch('/api/analytics/comprehensive', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                project_id: currentProject.full_name,
                analysis_type: 'comprehensive'
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            updateAnalyticsDisplay(data);
            updateInsightsPanel(data.insights);
            showAlert('Comprehensive analysis completed', 'success');
        } else {
            showAlert('Analysis failed', 'danger');
        }
    } catch (error) {
        console.error('Error running analysis:', error);
        showAlert('Analysis failed', 'danger');
    } finally {
        hideLoadingOverlay('analytics');
    }
}

function updateAnalyticsDisplay(data) {
    // Update metric values
    document.getElementById('health-score').textContent = data.health_score?.toFixed(1) || '--';
    document.getElementById('risk-score').textContent = data.risk_score?.toFixed(1) || '--';
    document.getElementById('quality-score').textContent = data.quality_score?.toFixed(1) || '--';
    document.getElementById('debt-score').textContent = data.debt_score?.toFixed(0) || '--';
    
    // Add updating animation
    document.querySelectorAll('.metric-value').forEach(el => {
        el.classList.add('updating');
        setTimeout(() => el.classList.remove('updating'), 1000);
    });
}

function updateInsightsPanel(insights) {
    const insightsPanel = document.getElementById('ai-insights');
    
    if (insights && insights.length > 0) {
        insightsPanel.innerHTML = insights.map(insight => `
            <div class="insight-item ${getInsightSeverity(insight)}">
                <div class="d-flex justify-content-between align-items-start">
                    <div>
                        <strong>${insight.title || 'Insight'}</strong>
                        <p class="mb-0 mt-1">${insight.description}</p>
                    </div>
                    <span class="badge bg-secondary">${insight.confidence || 'High'}</span>
                </div>
            </div>
        `).join('');
    } else {
        insightsPanel.innerHTML = `
            <div class="text-center text-muted">
                <i class="fas fa-brain fa-2x mb-2"></i>
                <p>No insights available</p>
            </div>
        `;
    }
}

function getInsightSeverity(insight) {
    const severity = insight.severity?.toLowerCase() || 'info';
    const severityMap = {
        'critical': 'danger',
        'high': 'danger',
        'medium': 'warning',
        'low': 'success',
        'info': ''
    };
    return severityMap[severity] || '';
}

// Workflow Automation Functions
async function startFeatureWorkflow() {
    if (!currentProject) {
        showAlert('Please select a project first', 'warning');
        return;
    }
    
    const requirements = prompt('Describe the feature you want to develop:');
    if (!requirements) return;
    
    try {
        const response = await fetch('/api/workflows/execute', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                workflow_type: 'feature_development',
                project_id: currentProject.full_name,
                requirements: {
                    description: requirements,
                    type: 'feature'
                }
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            showAlert('Feature development workflow started', 'success');
            updateActiveWorkflows();
        } else {
            showAlert('Failed to start workflow', 'danger');
        }
    } catch (error) {
        console.error('Error starting workflow:', error);
        showAlert('Failed to start workflow', 'danger');
    }
}

async function startBugfixWorkflow() {
    if (!currentProject) {
        showAlert('Please select a project first', 'warning');
        return;
    }
    
    const bugDescription = prompt('Describe the bug you want to fix:');
    if (!bugDescription) return;
    
    try {
        const response = await fetch('/api/workflows/execute', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                workflow_type: 'bug_fix',
                project_id: currentProject.full_name,
                requirements: {
                    description: bugDescription,
                    type: 'bug'
                }
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            showAlert('Bug fix workflow started', 'success');
            updateActiveWorkflows();
        } else {
            showAlert('Failed to start workflow', 'danger');
        }
    } catch (error) {
        console.error('Error starting workflow:', error);
        showAlert('Failed to start workflow', 'danger');
    }
}

async function startCodeReview() {
    if (!currentProject) {
        showAlert('Please select a project first', 'warning');
        return;
    }
    
    const prNumber = prompt('Enter PR number for review (or leave empty for latest):');
    
    try {
        const response = await fetch('/api/workflows/execute', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                workflow_type: 'code_review',
                project_id: currentProject.full_name,
                requirements: {
                    pr_number: prNumber || null,
                    type: 'review'
                }
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            showAlert('Code review workflow started', 'success');
            updateActiveWorkflows();
        } else {
            showAlert('Failed to start workflow', 'danger');
        }
    } catch (error) {
        console.error('Error starting workflow:', error);
        showAlert('Failed to start workflow', 'danger');
    }
}

async function updateActiveWorkflows() {
    try {
        const response = await fetch('/api/workflows/active');
        if (response.ok) {
            const data = await response.json();
            displayActiveWorkflows(data.workflows);
        }
    } catch (error) {
        console.error('Error updating workflows:', error);
    }
}

function displayActiveWorkflows(workflows) {
    const container = document.getElementById('active-workflows');
    
    if (workflows && workflows.length > 0) {
        container.innerHTML = `
            <h6>Active Workflows</h6>
            ${workflows.map(workflow => `
                <div class="workflow-item">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <h6 class="mb-1">${workflow.name}</h6>
                            <small class="text-muted">${workflow.description}</small>
                        </div>
                        <div class="workflow-status">
                            <span class="badge bg-${getWorkflowStatusColor(workflow.status)}">${workflow.status}</span>
                            <button class="btn btn-outline-danger btn-sm" onclick="cancelWorkflow('${workflow.id}')">
                                <i class="fas fa-stop"></i>
                            </button>
                        </div>
                    </div>
                    <div class="workflow-progress">
                        <div class="progress">
                            <div class="progress-bar" style="width: ${workflow.progress}%"></div>
                        </div>
                        <small class="text-muted">${workflow.progress}% complete</small>
                    </div>
                </div>
            `).join('')}
        `;
    } else {
        container.innerHTML = `
            <h6>Active Workflows</h6>
            <div class="text-center text-muted">
                <i class="fas fa-cogs fa-2x mb-2"></i>
                <p>No active workflows</p>
            </div>
        `;
    }
}

function getWorkflowStatusColor(status) {
    const statusColors = {
        'running': 'primary',
        'completed': 'success',
        'failed': 'danger',
        'paused': 'warning',
        'pending': 'secondary'
    };
    return statusColors[status] || 'secondary';
}

async function cancelWorkflow(workflowId) {
    try {
        const response = await fetch(`/api/workflows/${workflowId}/cancel`, {
            method: 'POST'
        });
        
        if (response.ok) {
            showAlert('Workflow cancelled', 'success');
            updateActiveWorkflows();
        } else {
            showAlert('Failed to cancel workflow', 'danger');
        }
    } catch (error) {
        console.error('Error cancelling workflow:', error);
        showAlert('Failed to cancel workflow', 'danger');
    }
}

// Enhanced AI Functions
async function runAIAnalysis() {
    const taskType = document.getElementById('ai-task-type').value;
    const target = document.getElementById('ai-target').value.trim();
    const instructions = document.getElementById('ai-instructions').value.trim();
    const contextText = document.getElementById('ai-context').value.trim();
    
    if (!target || !instructions) {
        showAlert('Please provide target and instructions', 'warning');
        return;
    }
    
    let context = {};
    if (contextText) {
        try {
            context = JSON.parse(contextText);
        } catch (e) {
            showAlert('Invalid JSON in context field', 'warning');
            return;
        }
    }
    
    try {
        showLoadingOverlay('ai-results');
        
        const response = await fetch('/api/ai/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                task_type: taskType,
                target: target,
                instructions: instructions,
                context: context,
                project_id: currentProject?.full_name
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            displayAIResults(data);
            updateRecentAnalyses(data);
            showAlert('AI analysis completed', 'success');
        } else {
            showAlert('AI analysis failed', 'danger');
        }
    } catch (error) {
        console.error('Error running AI analysis:', error);
        showAlert('AI analysis failed', 'danger');
    } finally {
        hideLoadingOverlay('ai-results');
    }
}

function displayAIResults(result) {
    const resultsPanel = document.getElementById('ai-results');
    
    resultsPanel.innerHTML = `
        <div class="ai-result-item">
            <div class="ai-result-header">
                <h6>${result.task_type.replace('_', ' ').toUpperCase()}</h6>
                <div class="ai-confidence-score">
                    <span>Confidence:</span>
                    <div class="confidence-bar">
                        <div class="confidence-fill" style="width: ${result.confidence_score * 100}%"></div>
                    </div>
                    <span>${(result.confidence_score * 100).toFixed(0)}%</span>
                </div>
            </div>
            
            <div class="ai-analysis">
                <h6>Analysis:</h6>
                <p>${result.analysis}</p>
            </div>
            
            ${result.code_changes ? `
                <div class="ai-code-changes mt-3">
                    <h6>Generated Code:</h6>
                    <pre><code>${result.code_changes}</code></pre>
                </div>
            ` : ''}
            
            ${result.suggestions && result.suggestions.length > 0 ? `
                <div class="ai-suggestions">
                    <h6>Suggestions:</h6>
                    ${result.suggestions.map(suggestion => `
                        <div class="ai-suggestion">${suggestion}</div>
                    `).join('')}
                </div>
            ` : ''}
            
            <div class="mt-3">
                <small class="text-muted">
                    Generated in ${result.generation_time?.toFixed(2)}s
                </small>
            </div>
        </div>
    `;
}

function updateRecentAnalyses(result) {
    const recentContainer = document.getElementById('recent-ai-analyses');
    
    // Get existing analyses or initialize empty array
    let recentAnalyses = JSON.parse(localStorage.getItem('recentAIAnalyses') || '[]');
    
    // Add new analysis
    recentAnalyses.unshift({
        id: Date.now(),
        task_type: result.task_type,
        target: result.target,
        confidence: result.confidence_score,
        timestamp: new Date().toISOString()
    });
    
    // Keep only last 10
    recentAnalyses = recentAnalyses.slice(0, 10);
    
    // Save to localStorage
    localStorage.setItem('recentAIAnalyses', JSON.stringify(recentAnalyses));
    
    // Update display
    if (recentAnalyses.length > 0) {
        recentContainer.innerHTML = recentAnalyses.map(analysis => `
            <div class="analysis-item" onclick="loadAnalysis('${analysis.id}')">
                <div>
                    <strong>${analysis.task_type.replace('_', ' ')}</strong>
                    <br>
                    <small class="text-muted">${analysis.target}</small>
                </div>
                <div class="text-end">
                    <small>${(analysis.confidence * 100).toFixed(0)}%</small>
                    <br>
                    <small class="text-muted">${formatTime(analysis.timestamp)}</small>
                </div>
            </div>
        `).join('');
    }
}

// System Performance Functions
async function updateSystemPerformance() {
    try {
        const response = await fetch('/api/system/performance');
        if (response.ok) {
            const data = await response.json();
            updatePerformanceDisplay(data);
        }
    } catch (error) {
        console.error('Error updating system performance:', error);
    }
}

function updatePerformanceDisplay(data) {
    // Update orchestrator health
    const healthElement = document.getElementById('orchestrator-health');
    healthElement.textContent = data.orchestrator_health || 'Unknown';
    healthElement.className = `badge bg-${getHealthColor(data.orchestrator_health)}`;
    
    // Update active tasks
    document.getElementById('active-tasks-count').textContent = data.active_tasks || 0;
    
    // Update success rate
    document.getElementById('success-rate').textContent = `${data.success_rate?.toFixed(1) || 0}%`;
    
    // Update response time
    document.getElementById('avg-response-time').textContent = `${data.avg_response_time || 0}ms`;
}

function getHealthColor(health) {
    const healthColors = {
        'healthy': 'success',
        'degraded': 'warning',
        'unhealthy': 'danger'
    };
    return healthColors[health?.toLowerCase()] || 'secondary';
}

// Utility Functions
function showLoadingOverlay(containerId) {
    const container = document.getElementById(containerId);
    if (container) {
        const overlay = document.createElement('div');
        overlay.className = 'loading-overlay';
        overlay.innerHTML = '<div class="loading-spinner-large"></div>';
        container.style.position = 'relative';
        container.appendChild(overlay);
    }
}

function hideLoadingOverlay(containerId) {
    const container = document.getElementById(containerId);
    if (container) {
        const overlay = container.querySelector('.loading-overlay');
        if (overlay) {
            overlay.remove();
        }
    }
}

function showWorkflowTemplates() {
    // TODO: Implement workflow templates modal
    showAlert('Workflow templates coming soon!', 'info');
}

function createCustomWorkflow() {
    // TODO: Implement custom workflow creation
    showAlert('Custom workflow creation coming soon!', 'info');
}

// Enhanced monitoring with advanced features
function startAdvancedMonitoring() {
    // Update analytics every 2 minutes
    setInterval(updateSystemPerformance, 120000);
    
    // Update workflows every 30 seconds
    setInterval(updateActiveWorkflows, 30000);
    
    // Initial updates
    updateSystemPerformance();
    updateActiveWorkflows();
}

// Initialize advanced features
document.addEventListener('DOMContentLoaded', function() {
    console.log('Contexten Dashboard loaded');
    
    // Check for any initialization tasks
    checkIntegrationStatus();
    startMonitoring();
    
    // Start advanced monitoring
    startAdvancedMonitoring();
    
    // Load recent analyses from localStorage
    const recentAnalyses = JSON.parse(localStorage.getItem('recentAIAnalyses') || '[]');
    if (recentAnalyses.length > 0) {
        updateRecentAnalyses({ task_type: '', target: '', confidence_score: 0 }); // Trigger display update
    }
});

// Auto-refresh functionality
setInterval(checkIntegrationStatus, 30000); // Check every 30 seconds
