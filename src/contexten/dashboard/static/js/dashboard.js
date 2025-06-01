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

// Utility functions
function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    const container = document.querySelector('.container');
    container.insertBefore(alertDiv, container.firstChild);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}

async function checkIntegrationStatus() {
    try {
        const response = await fetch('/api/integrations/status');
        if (response.ok) {
            integrationStatus = await response.json();
            updateIntegrationIndicators();
        }
    } catch (error) {
        console.error('Error checking integration status:', error);
    }
}

function updateIntegrationIndicators() {
    // Update integration status indicators in the UI
    // This would be called periodically to refresh status
    console.log('Integration status updated:', integrationStatus);
}

function handleApiError(error, context = '') {
    console.error(`API Error ${context}:`, error);
    showAlert(`An error occurred ${context}. Please try again.`, 'danger');
}

// Auto-refresh functionality
setInterval(checkIntegrationStatus, 30000); // Check every 30 seconds
