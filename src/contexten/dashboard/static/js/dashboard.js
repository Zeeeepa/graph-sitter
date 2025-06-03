// Contexten Dashboard JavaScript - Enhanced CICD Version

// Global variables
let currentProject = null;
let integrationStatus = {};
let chatThreadId = null;
let activeAgents = {};
let monitoringInterval = null;
let pinnedProjects = JSON.parse(localStorage.getItem('pinnedProjects') || '[]');
let activeFlows = {};
let dashboardData = {};
let currentTab = 'dashboard';

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    console.log('Contexten CICD Dashboard loaded');
    initializeDashboard();
});

// Dashboard initialization
function initializeDashboard() {
    // Setup tab navigation
    setupTabNavigation();
    
    // Load initial data
    loadDashboardData();
    loadPinnedProjects();
    
    // Start monitoring
    startMonitoring();
    startAdvancedMonitoring();
    
    // Setup event listeners
    setupEventListeners();
    
    // Load settings
    loadSettings();
    
    console.log('Dashboard initialized successfully');
}

// Tab navigation setup
function setupTabNavigation() {
    const navLinks = document.querySelectorAll('.sidebar .nav-link');
    const tabContents = document.querySelectorAll('.tab-content');
    
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Remove active class from all links and tabs
            navLinks.forEach(l => l.classList.remove('active'));
            tabContents.forEach(t => t.classList.remove('active'));
            
            // Add active class to clicked link
            this.classList.add('active');
            
            // Show corresponding tab
            const tabId = this.getAttribute('data-tab');
            const tabContent = document.getElementById(tabId);
            if (tabContent) {
                tabContent.classList.add('active');
                currentTab = tabId;
                
                // Load tab-specific data
                loadTabData(tabId);
            }
        });
    });
}

// Load tab-specific data
function loadTabData(tabId) {
    switch(tabId) {
        case 'dashboard':
            loadSystemStatus();
            loadQuickStats();
            loadActiveFlows();
            break;
        case 'projects':
            loadProjectsList();
            loadPinnedProjects();
            break;
        case 'flows':
            loadFlowsList();
            loadFlowAnalytics();
            break;
        case 'analysis':
            loadAnalysisHistory();
            break;
        case 'integrations':
            loadIntegrationsStatus();
            break;
        case 'monitoring':
            loadMonitoringData();
            loadSystemHealth();
            break;
        case 'settings':
            loadSettingsForm();
            break;
    }
}

// API helper functions
async function apiCall(endpoint, options = {}) {
    try {
        const response = await fetch(endpoint, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        if (!response.ok) {
            throw new Error(`API call failed: ${response.status} ${response.statusText}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API call error:', error);
        throw error;
    }
}

// System status functions
async function loadSystemStatus() {
    try {
        const statusElement = document.getElementById('system-status');
        if (!statusElement) return;
        
        statusElement.innerHTML = '<div class="loading">Loading system status...</div>';
        
        const health = await apiCall('/api/comprehensive/system/health');
        
        statusElement.innerHTML = `
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem;">
                <div class="status-card">
                    <h4>Overall Status</h4>
                    <div class="status-indicator status-${health.overall_status === 'healthy' ? 'online' : 'offline'}"></div>
                    <span>${health.overall_status}</span>
                </div>
                <div class="status-card">
                    <h4>API Response</h4>
                    <span>${health.services.api.response_time}</span>
                </div>
                <div class="status-card">
                    <h4>Active Flows</h4>
                    <span>${health.metrics.active_flows}</span>
                </div>
                <div class="status-card">
                    <h4>Memory Usage</h4>
                    <span>${health.metrics.memory_usage}</span>
                </div>
            </div>
        `;
    } catch (error) {
        console.error('Failed to load system status:', error);
        document.getElementById('system-status').innerHTML = '<div class="error">Failed to load system status</div>';
    }
}

async function loadQuickStats() {
    try {
        const statsElement = document.getElementById('quick-stats');
        if (!statsElement) return;
        
        statsElement.innerHTML = '<div class="loading">Loading statistics...</div>';
        
        const analytics = await apiCall('/api/comprehensive/analytics/overview');
        
        statsElement.innerHTML = `
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1rem;">
                <div class="stat-card">
                    <h4>Projects</h4>
                    <div class="stat-value">${analytics.summary.total_projects}</div>
                </div>
                <div class="stat-card">
                    <h4>Active Flows</h4>
                    <div class="stat-value">${analytics.summary.active_flows}</div>
                </div>
                <div class="stat-card">
                    <h4>Success Rate</h4>
                    <div class="stat-value">${analytics.trends.flow_success_rate}%</div>
                </div>
                <div class="stat-card">
                    <h4>Avg Time</h4>
                    <div class="stat-value">${analytics.trends.average_completion_time}</div>
                </div>
            </div>
        `;
    } catch (error) {
        console.error('Failed to load quick stats:', error);
        document.getElementById('quick-stats').innerHTML = '<div class="error">Failed to load statistics</div>';
    }
}

// Load dashboard overview data
async function loadDashboardData() {
    try {
        const response = await fetch('/api/dashboard/overview');
        if (response.ok) {
            dashboardData = await response.json();
            updateDashboardStats();
            updateRecentActivity();
        }
    } catch (error) {
        console.error('Error loading dashboard data:', error);
        showNotification('Failed to load dashboard data', 'error');
    }
}

// Update dashboard statistics
function updateDashboardStats() {
    document.getElementById('active-projects-count').textContent = dashboardData.active_projects || 0;
    document.getElementById('running-flows-count').textContent = dashboardData.running_flows || 0;
    document.getElementById('completed-today-count').textContent = dashboardData.completed_today || 0;
    document.getElementById('success-rate').textContent = `${dashboardData.success_rate || 0}%`;
}

// Update recent activity timeline
function updateRecentActivity() {
    const container = document.getElementById('recent-activity');
    const activities = dashboardData.recent_activity || [];
    
    if (activities.length === 0) {
        container.innerHTML = '<p class="text-muted text-center">No recent activity</p>';
        return;
    }
    
    container.innerHTML = activities.map(activity => `
        <div class="timeline-item ${activity.status}">
            <div class="d-flex justify-content-between align-items-start">
                <div>
                    <h6 class="mb-1">${activity.title}</h6>
                    <p class="text-muted mb-1">${activity.description}</p>
                    <small class="text-muted">${formatTime(activity.timestamp)}</small>
                </div>
                <span class="badge bg-${getStatusColor(activity.status)}">${activity.status}</span>
            </div>
        </div>
    `).join('');
}

// Project management functions
async function loadProjects() {
    try {
        showLoadingSpinner('projects-grid');
        
        const response = await fetch('/api/projects');
        const data = await response.json();
        
        const projectsGrid = document.getElementById('projects-grid');
        if (data.projects && data.projects.length > 0) {
            projectsGrid.innerHTML = data.projects.map(project => createProjectCard(project)).join('');
        } else {
            projectsGrid.innerHTML = `
                <div class="col-12">
                    <div class="text-center text-muted p-4">
                        <i class="fas fa-folder-open fa-3x mb-3"></i>
                        <h5>No projects found</h5>
                        <p>Connect your GitHub repositories to get started</p>
                        <button class="btn btn-primary" onclick="connectGitHub()">
                            <i class="fab fa-github me-2"></i>Connect GitHub
                        </button>
                    </div>
                </div>
            `;
        }
    } catch (error) {
        console.error('Error loading projects:', error);
        showNotification('Failed to load projects', 'error');
    }
}

// Create project card HTML
function createProjectCard(project) {
    const isPinned = pinnedProjects.includes(project.full_name);
    const isSelected = currentProject && currentProject.full_name === project.full_name;
    
    return `
        <div class="col-md-6 col-lg-4 mb-3">
            <div class="project-card card h-100 ${isPinned ? 'pinned' : ''} ${isSelected ? 'selected' : ''}" 
                 onclick="selectProject('${project.full_name}', '${project.name}')">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-start mb-2">
                        <h6 class="card-title mb-0">${project.name}</h6>
                        <div class="dropdown">
                            <button class="btn btn-sm btn-outline-secondary" type="button" 
                                    data-bs-toggle="dropdown" onclick="event.stopPropagation()">
                                <i class="fas fa-ellipsis-v"></i>
                            </button>
                            <ul class="dropdown-menu">
                                <li>
                                    <a class="dropdown-item" href="#" onclick="event.stopPropagation(); togglePin('${project.full_name}')">
                                        <i class="fas fa-thumbtack me-2"></i>
                                        ${isPinned ? 'Unpin' : 'Pin'} Project
                                    </a>
                                </li>
                                <li>
                                    <a class="dropdown-item" href="#" onclick="event.stopPropagation(); createFlowForProject('${project.full_name}')">
                                        <i class="fas fa-play me-2"></i>
                                        Create Flow
                                    </a>
                                </li>
                                <li>
                                    <a class="dropdown-item" href="${project.html_url}" target="_blank" onclick="event.stopPropagation()">
                                        <i class="fab fa-github me-2"></i>
                                        View on GitHub
                                    </a>
                                </li>
                            </ul>
                        </div>
                    </div>
                    <p class="card-text text-muted small">${project.description || 'No description available'}</p>
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            ${project.language ? `<span class="badge bg-secondary">${project.language}</span>` : ''}
                            ${isPinned ? '<i class="fas fa-thumbtack text-warning ms-2"></i>' : ''}
                        </div>
                        <small class="text-muted">${formatTime(project.updated_at)}</small>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// Project selection and management
function selectProject(fullName, name) {
    currentProject = { full_name: fullName, name: name };
    
    // Update project cards visual state
    document.querySelectorAll('.project-card').forEach(card => {
        card.classList.remove('selected');
    });
    event.currentTarget.classList.add('selected');
    
    // Update project actions panel
    updateProjectActions();
    
    // Show notification
    showNotification(`Selected project: ${name}`, 'success');
}

// Update project actions panel
function updateProjectActions() {
    const actionsContainer = document.getElementById('project-actions');
    
    if (!currentProject) {
        actionsContainer.innerHTML = '<p class="text-muted text-center">Select a project to see actions</p>';
        return;
    }
    
    actionsContainer.innerHTML = `
        <button class="btn btn-primary" onclick="createFlowForProject('${currentProject.full_name}')">
            <i class="fas fa-play me-2"></i>Create Flow
        </button>
        <button class="btn btn-outline-info" onclick="analyzeProject('${currentProject.full_name}')">
            <i class="fas fa-search me-2"></i>Analyze Project
        </button>
        <button class="btn btn-outline-success" onclick="viewProjectFlows('${currentProject.full_name}')">
            <i class="fas fa-list me-2"></i>View Flows
        </button>
        <button class="btn btn-outline-warning" onclick="togglePin('${currentProject.full_name}')">
            <i class="fas fa-thumbtack me-2"></i>
            ${pinnedProjects.includes(currentProject.full_name) ? 'Unpin' : 'Pin'} Project
        </button>
    `;
}

// Pin/unpin project
function togglePin(projectFullName) {
    const index = pinnedProjects.indexOf(projectFullName);
    
    if (index > -1) {
        pinnedProjects.splice(index, 1);
        showNotification('Project unpinned', 'info');
    } else {
        pinnedProjects.push(projectFullName);
        showNotification('Project pinned', 'success');
    }
    
    localStorage.setItem('pinnedProjects', JSON.stringify(pinnedProjects));
    loadPinnedProjects();
    
    // Update project cards if on projects tab
    if (currentTab === 'projects') {
        loadProjects();
    }
}

// Load and display pinned projects
function loadPinnedProjects() {
    const container = document.getElementById('pinned-projects');
    
    if (pinnedProjects.length === 0) {
        container.innerHTML = '<p class="text-muted text-center">No pinned projects</p>';
        return;
    }
    
    container.innerHTML = pinnedProjects.map(projectName => `
        <div class="d-flex justify-content-between align-items-center mb-2 p-2 bg-light rounded">
            <div>
                <small class="fw-bold">${projectName.split('/')[1]}</small>
                <br>
                <small class="text-muted">${projectName}</small>
            </div>
            <button class="btn btn-sm btn-outline-danger" onclick="togglePin('${projectName}')">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `).join('');
}

// Flow management functions
async function loadActiveFlows() {
    try {
        const response = await fetch('/api/flows/active');
        if (response.ok) {
            const data = await response.json();
            activeFlows = data.flows || {};
            updateActiveFlowsDisplay();
        }
    } catch (error) {
        console.error('Error loading active flows:', error);
        showNotification('Failed to load active flows', 'error');
    }
}

// Update active flows display
function updateActiveFlowsDisplay() {
    const container = document.getElementById('active-flows');
    const flows = Object.values(activeFlows);
    
    if (flows.length === 0) {
        container.innerHTML = `
            <div class="text-center text-muted p-4">
                <i class="fas fa-play-circle fa-3x mb-3"></i>
                <h5>No active flows</h5>
                <p>Create a new flow to get started</p>
                <button class="btn btn-primary" onclick="createNewFlow()">
                    <i class="fas fa-plus me-2"></i>Create Flow
                </button>
            </div>
        `;
        return;
    }
    
    container.innerHTML = flows.map(flow => createFlowCard(flow)).join('');
}

// Create flow card HTML
function createFlowCard(flow) {
    const progressPercent = flow.progress || 0;
    const statusColor = getStatusColor(flow.status);
    
    return `
        <div class="flow-card card mb-3 ${flow.status}">
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-start mb-3">
                    <div>
                        <h6 class="card-title mb-1">${flow.name}</h6>
                        <p class="text-muted mb-1">${flow.project_name}</p>
                        <small class="text-muted">${flow.type} • Started ${formatTime(flow.created_at)}</small>
                    </div>
                    <div class="d-flex align-items-center">
                        <div class="progress-ring me-3">
                            <svg width="60" height="60">
                                <circle cx="30" cy="30" r="25" stroke="#e9ecef" stroke-width="4" fill="transparent"/>
                                <circle cx="30" cy="30" r="25" stroke="${getProgressColor(flow.status)}" stroke-width="4" 
                                        fill="transparent" stroke-dasharray="${157 * progressPercent / 100} 157" 
                                        stroke-linecap="round" transform="rotate(-90 30 30)"/>
                                <text x="30" y="35" text-anchor="middle" font-size="12" fill="#666">
                                    ${Math.round(progressPercent)}%
                                </text>
                            </svg>
                        </div>
                        <div class="dropdown">
                            <button class="btn btn-sm btn-outline-secondary" type="button" data-bs-toggle="dropdown">
                                <i class="fas fa-ellipsis-v"></i>
                            </button>
                            <ul class="dropdown-menu">
                                <li><a class="dropdown-item" href="#" onclick="viewFlowDetails('${flow.id}')">
                                    <i class="fas fa-eye me-2"></i>View Details
                                </a></li>
                                <li><a class="dropdown-item" href="#" onclick="pauseFlow('${flow.id}')">
                                    <i class="fas fa-pause me-2"></i>Pause Flow
                                </a></li>
                                <li><a class="dropdown-item text-danger" href="#" onclick="cancelFlow('${flow.id}')">
                                    <i class="fas fa-stop me-2"></i>Cancel Flow
                                </a></li>
                            </ul>
                        </div>
                    </div>
                </div>
                
                <div class="mb-3">
                    <div class="progress" style="height: 6px;">
                        <div class="progress-bar bg-${statusColor}" style="width: ${progressPercent}%"></div>
                    </div>
                </div>
                
                <div class="d-flex justify-content-between align-items-center">
                    <span class="badge bg-${statusColor}">${flow.status}</span>
                    <div class="text-end">
                        <small class="text-muted">
                            ${flow.current_step || 'Initializing...'}
                        </small>
                    </div>
                </div>
                
                ${flow.error ? `
                    <div class="alert alert-danger mt-2 mb-0" role="alert">
                        <small><i class="fas fa-exclamation-triangle me-1"></i>${flow.error}</small>
                    </div>
                ` : ''}
            </div>
        </div>
    `;
}

// Create new flow
function createNewFlow() {
    // Populate project dropdown in modal
    populateProjectDropdown();
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('flowModal'));
    modal.show();
}

// Create flow for specific project
function createFlowForProject(projectFullName) {
    // Set the project in the form
    currentProject = { full_name: projectFullName };
    
    // Show modal and pre-select project
    createNewFlow();
    
    // Pre-select the project in dropdown
    setTimeout(() => {
        const projectSelect = document.getElementById('flow-project');
        projectSelect.value = projectFullName;
    }, 100);
}

// Populate project dropdown
async function populateProjectDropdown() {
    try {
        const response = await fetch('/api/projects');
        const data = await response.json();
        
        const select = document.getElementById('flow-project');
        select.innerHTML = '<option value="">Choose a project...</option>';
        
        if (data.projects) {
            data.projects.forEach(project => {
                const option = document.createElement('option');
                option.value = project.full_name;
                option.textContent = `${project.name} (${project.full_name})`;
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Error loading projects for dropdown:', error);
    }
}

// Start flow
async function startFlow() {
    const form = document.getElementById('flow-form');
    const formData = new FormData(form);
    
    const flowData = {
        name: formData.get('flow-name') || document.getElementById('flow-name').value,
        project: document.getElementById('flow-project').value,
        type: document.getElementById('flow-type').value,
        requirements: document.getElementById('flow-requirements').value,
        priority: document.getElementById('flow-priority').value,
        notifications: document.getElementById('flow-notifications').checked
    };
    
    // Validate required fields
    if (!flowData.name || !flowData.project || !flowData.type || !flowData.requirements) {
        showNotification('Please fill in all required fields', 'error');
        return;
    }
    
    try {
        const response = await fetch('/api/flows/create', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(flowData)
        });
        
        if (response.ok) {
            const result = await response.json();
            
            // Close modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('flowModal'));
            modal.hide();
            
            // Clear form
            form.reset();
            
            // Show success notification
            showNotification(`Flow "${flowData.name}" started successfully!`, 'success');
            
            // Refresh flows if on flows tab
            if (currentTab === 'flows') {
                loadActiveFlows();
            }
            
            // Update dashboard stats
            loadDashboardData();
            
        } else {
            const error = await response.json();
            showNotification(`Failed to start flow: ${error.message}`, 'error');
        }
    } catch (error) {
        console.error('Error starting flow:', error);
        showNotification('Failed to start flow', 'error');
    }
}

// Flow control functions
async function pauseFlow(flowId) {
    try {
        const response = await fetch(`/api/flows/${flowId}/pause`, {
            method: 'POST'
        });
        
        if (response.ok) {
            showNotification('Flow paused', 'info');
            loadActiveFlows();
        } else {
            showNotification('Failed to pause flow', 'error');
        }
    } catch (error) {
        console.error('Error pausing flow:', error);
        showNotification('Failed to pause flow', 'error');
    }
}

async function cancelFlow(flowId) {
    if (!confirm('Are you sure you want to cancel this flow? This action cannot be undone.')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/flows/${flowId}/cancel`, {
            method: 'POST'
        });
        
        if (response.ok) {
            showNotification('Flow cancelled', 'warning');
            loadActiveFlows();
            loadDashboardData(); // Update stats
        } else {
            showNotification('Failed to cancel flow', 'error');
        }
    } catch (error) {
        console.error('Error cancelling flow:', error);
        showNotification('Failed to cancel flow', 'error');
    }
}

async function viewFlowDetails(flowId) {
    try {
        const response = await fetch(`/api/flows/${flowId}/details`);
        if (response.ok) {
            const flowDetails = await response.json();
            showFlowDetailsModal(flowDetails);
        } else {
            showNotification('Failed to load flow details', 'error');
        }
    } catch (error) {
        console.error('Error loading flow details:', error);
        showNotification('Failed to load flow details', 'error');
    }
}

// Analytics functions
async function loadAnalytics() {
    try {
        const response = await fetch('/api/analytics/dashboard');
        if (response.ok) {
            const analyticsData = await response.json();
            updateAnalyticsCharts(analyticsData);
        }
    } catch (error) {
        console.error('Error loading analytics:', error);
        showNotification('Failed to load analytics', 'error');
    }
}

function updateAnalyticsCharts(data) {
    // Performance Chart
    const performanceCtx = document.getElementById('performance-chart');
    if (performanceCtx) {
        new Chart(performanceCtx, {
            type: 'line',
            data: {
                labels: data.performance.labels || [],
                datasets: [{
                    label: 'Success Rate',
                    data: data.performance.success_rate || [],
                    borderColor: '#28a745',
                    backgroundColor: 'rgba(40, 167, 69, 0.1)',
                    tension: 0.4
                }, {
                    label: 'Average Duration (min)',
                    data: data.performance.avg_duration || [],
                    borderColor: '#007bff',
                    backgroundColor: 'rgba(0, 123, 255, 0.1)',
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }
    
    // Activity Chart
    const activityCtx = document.getElementById('activity-chart');
    if (activityCtx) {
        new Chart(activityCtx, {
            type: 'doughnut',
            data: {
                labels: data.activity.labels || [],
                datasets: [{
                    data: data.activity.values || [],
                    backgroundColor: [
                        '#28a745',
                        '#007bff', 
                        '#ffc107',
                        '#dc3545',
                        '#6c757d'
                    ]
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }
}

// Settings functions
function loadSettings() {
    // Load settings from localStorage or API
    const settings = JSON.parse(localStorage.getItem('dashboardSettings') || '{}');
    
    if (settings.codegenOrgId) {
        document.getElementById('codegen-org-id').value = settings.codegenOrgId;
    }
    if (settings.flowTimeout) {
        document.getElementById('flow-timeout').value = settings.flowTimeout;
    }
    if (settings.notificationPrefs) {
        document.getElementById('notification-prefs').value = settings.notificationPrefs;
    }
}

function saveSettings() {
    const settings = {
        codegenOrgId: document.getElementById('codegen-org-id').value,
        codegenToken: document.getElementById('codegen-token').value,
        flowTimeout: document.getElementById('flow-timeout').value,
        notificationPrefs: document.getElementById('notification-prefs').value
    };
    
    // Save to localStorage (excluding sensitive token)
    const settingsToStore = { ...settings };
    delete settingsToStore.codegenToken;
    localStorage.setItem('dashboardSettings', JSON.stringify(settingsToStore));
    
    // Send to backend
    fetch('/api/settings/save', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(settings)
    }).then(response => {
        if (response.ok) {
            showNotification('Settings saved successfully', 'success');
        } else {
            showNotification('Failed to save settings', 'error');
        }
    }).catch(error => {
        console.error('Error saving settings:', error);
        showNotification('Failed to save settings', 'error');
    });
}

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
    if (!timestamp) return 'Unknown';
    
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now - date;
    
    // Less than 1 minute
    if (diff < 60000) {
        return 'Just now';
    }
    
    // Less than 1 hour
    if (diff < 3600000) {
        const minutes = Math.floor(diff / 60000);
        return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
    }
    
    // Less than 1 day
    if (diff < 86400000) {
        const hours = Math.floor(diff / 3600000);
        return `${hours} hour${hours > 1 ? 's' : ''} ago`;
    }
    
    // More than 1 day
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
    console.log('Contexten CICD Dashboard loaded');
    
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

// Event listeners setup
function setupEventListeners() {
    // Settings form submission
    const settingsForm = document.getElementById('settings-form');
    if (settingsForm) {
        settingsForm.addEventListener('submit', function(e) {
            e.preventDefault();
            saveSettings();
        });
    }
    
    // Refresh dashboard button
    const refreshBtn = document.querySelector('[onclick="refreshDashboard()"]');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', refreshDashboard);
    }
    
    // Auto-refresh every 30 seconds
    setInterval(() => {
        if (currentTab === 'dashboard') {
            loadDashboardData();
        } else if (currentTab === 'flows') {
            loadActiveFlows();
        }
    }, 30000);
}

// Dashboard refresh
function refreshDashboard() {
    showNotification('Refreshing dashboard...', 'info');
    
    // Reload current tab data
    loadTabData(currentTab);
    
    // Update system status
    updateSystemStatus();
}

// System status update
async function updateSystemStatus() {
    try {
        const response = await fetch('/api/system/status');
        if (response.ok) {
            const status = await response.json();
            
            document.getElementById('orchestrator-status').textContent = status.orchestrator || 'Unknown';
            document.getElementById('github-status').textContent = status.github || 'Unknown';
            document.getElementById('linear-status').textContent = status.linear || 'Unknown';
            
            // Update status indicators
            updateStatusIndicators(status);
        }
    } catch (error) {
        console.error('Error updating system status:', error);
    }
}

function updateStatusIndicators(status) {
    const indicators = document.querySelectorAll('.status-indicator');
    indicators.forEach((indicator, index) => {
        const services = ['orchestrator', 'github', 'linear'];
        const service = services[index];
        
        if (status[service] === 'Connected' || status[service] === 'Healthy') {
            indicator.className = 'status-indicator bg-success me-2';
        } else if (status[service] === 'Degraded' || status[service] === 'Warning') {
            indicator.className = 'status-indicator bg-warning me-2';
        } else {
            indicator.className = 'status-indicator bg-danger me-2';
        }
    });
}

// Additional project functions
async function analyzeProject(projectFullName) {
    showNotification('Starting project analysis...', 'info');
    
    try {
        const response = await fetch('/api/projects/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                project: projectFullName,
                analysis_type: 'comprehensive'
            })
        });
        
        if (response.ok) {
            const result = await response.json();
            showNotification('Project analysis started successfully', 'success');
            
            // If on flows tab, refresh to show new analysis flow
            if (currentTab === 'flows') {
                setTimeout(() => loadActiveFlows(), 1000);
            }
        } else {
            showNotification('Failed to start project analysis', 'error');
        }
    } catch (error) {
        console.error('Error analyzing project:', error);
        showNotification('Failed to start project analysis', 'error');
    }
}

async function viewProjectFlows(projectFullName) {
    try {
        const response = await fetch(`/api/projects/${encodeURIComponent(projectFullName)}/flows`);
        if (response.ok) {
            const data = await response.json();
            showProjectFlowsModal(data);
        } else {
            showNotification('Failed to load project flows', 'error');
        }
    } catch (error) {
        console.error('Error loading project flows:', error);
        showNotification('Failed to load project flows', 'error');
    }
}

// Export data functionality
async function exportData() {
    try {
        const response = await fetch('/api/export/dashboard-data');
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `dashboard-export-${new Date().toISOString().split('T')[0]}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            
            showNotification('Data exported successfully', 'success');
        } else {
            showNotification('Failed to export data', 'error');
        }
    } catch (error) {
        console.error('Error exporting data:', error);
        showNotification('Failed to export data', 'error');
    }
}

// Connect GitHub functionality
function connectGitHub() {
    window.location.href = '/auth/github';
}

// Add custom project
function addCustomProject() {
    const projectUrl = prompt('Enter GitHub repository URL (e.g., https://github.com/owner/repo):');
    if (projectUrl) {
        // Extract owner/repo from URL
        const match = projectUrl.match(/github\.com\/([^\/]+)\/([^\/]+)/);
        if (match) {
            const fullName = `${match[1]}/${match[2]}`;
            addProjectToList(fullName);
        } else {
            showNotification('Invalid GitHub URL format', 'error');
        }
    }
}

async function addProjectToList(projectFullName) {
    try {
        const response = await fetch('/api/projects/add', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                project: projectFullName
            })
        });
        
        if (response.ok) {
            showNotification('Project added successfully', 'success');
            loadProjects(); // Refresh projects list
        } else {
            const error = await response.json();
            showNotification(`Failed to add project: ${error.message}`, 'error');
        }
    } catch (error) {
        console.error('Error adding project:', error);
        showNotification('Failed to add project', 'error');
    }
}

// View analytics
function viewAnalytics() {
    // Switch to analytics tab
    const analyticsTab = document.querySelector('[data-tab="analytics"]');
    if (analyticsTab) {
        analyticsTab.click();
    }
}

// Utility functions
function showNotification(message, type = 'info') {
    const toastContainer = document.getElementById('toast-container');
    const toastId = 'toast-' + Date.now();
    
    const toastHtml = `
        <div id="${toastId}" class="toast notification-toast" role="alert">
            <div class="toast-header">
                <i class="fas fa-${getNotificationIcon(type)} me-2 text-${type}"></i>
                <strong class="me-auto">Notification</strong>
                <button type="button" class="btn-close" data-bs-dismiss="toast"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        </div>
    `;
    
    toastContainer.insertAdjacentHTML('beforeend', toastHtml);
    
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement, {
        autohide: true,
        delay: type === 'error' ? 8000 : 5000
    });
    
    toast.show();
    
    // Remove toast element after it's hidden
    toastElement.addEventListener('hidden.bs.toast', () => {
        toastElement.remove();
    });
}

function getNotificationIcon(type) {
    const icons = {
        'success': 'check-circle',
        'error': 'exclamation-triangle',
        'warning': 'exclamation-circle',
        'info': 'info-circle'
    };
    return icons[type] || 'info-circle';
}

function getStatusColor(status) {
    const colors = {
        'running': 'primary',
        'completed': 'success',
        'failed': 'danger',
        'paused': 'warning',
        'pending': 'secondary',
        'cancelled': 'dark'
    };
    return colors[status] || 'secondary';
}

function getProgressColor(status) {
    const colors = {
        'running': '#007bff',
        'completed': '#28a745',
        'failed': '#dc3545',
        'paused': '#ffc107',
        'pending': '#6c757d'
    };
    return colors[status] || '#6c757d';
}

function showLoadingSpinner(containerId) {
    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = `
            <div class="text-center p-4">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="mt-2 text-muted">Loading...</p>
            </div>
        `;
    }
}
