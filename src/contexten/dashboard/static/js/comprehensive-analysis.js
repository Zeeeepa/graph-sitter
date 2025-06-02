// Comprehensive Analysis Dashboard JavaScript
// Enhanced with Linear, GitHub, Prefect, and Graph-sitter integration

// Global state for comprehensive analysis
let comprehensiveAnalysisState = {
    activeAnalyses: {},
    analysisHistory: [],
    integrationStatus: {},
    systemHealth: {}
};

// Initialize comprehensive analysis features
document.addEventListener('DOMContentLoaded', function() {
    initializeComprehensiveAnalysis();
});

function initializeComprehensiveAnalysis() {
    console.log('Initializing Comprehensive Analysis Dashboard...');
    
    // Setup analysis type buttons
    setupAnalysisButtons();
    
    // Setup integration sync buttons
    setupIntegrationButtons();
    
    // Setup real-time updates
    setupRealTimeUpdates();
    
    // Load initial data
    loadIntegrationStatus();
    loadSystemHealth();
    loadAnalysisHistory();
    
    console.log('Comprehensive Analysis Dashboard initialized');
}

function setupAnalysisButtons() {
    // Dead Code Analysis
    const deadCodeBtn = document.getElementById('run-dead-code-analysis');
    if (deadCodeBtn) {
        deadCodeBtn.addEventListener('click', () => runAnalysis('dead_code'));
    }
    
    // Code Quality Analysis
    const codeQualityBtn = document.getElementById('run-code-quality-analysis');
    if (codeQualityBtn) {
        codeQualityBtn.addEventListener('click', () => runAnalysis('code_quality'));
    }
    
    // Security Analysis
    const securityBtn = document.getElementById('run-security-analysis');
    if (securityBtn) {
        securityBtn.addEventListener('click', () => runAnalysis('security'));
    }
    
    // Performance Analysis
    const performanceBtn = document.getElementById('run-performance-analysis');
    if (performanceBtn) {
        performanceBtn.addEventListener('click', () => runAnalysis('performance'));
    }
    
    // Comprehensive Analysis
    const comprehensiveBtn = document.getElementById('run-comprehensive-analysis');
    if (comprehensiveBtn) {
        comprehensiveBtn.addEventListener('click', runComprehensiveAnalysis);
    }
}

function setupIntegrationButtons() {
    // Linear Integration
    const linearSyncBtn = document.getElementById('sync-linear-integration');
    if (linearSyncBtn) {
        linearSyncBtn.addEventListener('click', () => syncIntegration('linear'));
    }
    
    // GitHub Integration
    const githubSyncBtn = document.getElementById('sync-github-integration');
    if (githubSyncBtn) {
        githubSyncBtn.addEventListener('click', () => syncIntegration('github'));
    }
    
    // Prefect Integration
    const prefectSyncBtn = document.getElementById('sync-prefect-integration');
    if (prefectSyncBtn) {
        prefectSyncBtn.addEventListener('click', () => syncIntegration('prefect'));
    }
}

function setupRealTimeUpdates() {
    // Update every 30 seconds
    setInterval(() => {
        loadIntegrationStatus();
        loadSystemHealth();
        updateActiveAnalysesFromServer();
    }, 30000);
}

async function runAnalysis(analysisType) {
    try {
        showLoadingSpinner('analysis-results');
        
        const projectPath = getCurrentProjectPath();
        if (!projectPath) {
            showNotification('Please select a project first', 'warning');
            return;
        }
        
        const response = await fetch(`/api/analysis/${analysisType.replace('_', '-')}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                project_path: projectPath,
                options: getAnalysisOptions(analysisType)
            })
        });
        
        if (!response.ok) {
            throw new Error(`Analysis failed: ${response.statusText}`);
        }
        
        const result = await response.json();
        
        // Track the analysis
        comprehensiveAnalysisState.activeAnalyses[result.analysis_id] = {
            id: result.analysis_id,
            type: analysisType,
            status: 'running',
            started_at: new Date().toISOString(),
            project_path: projectPath,
            progress: 0
        };
        
        // Start monitoring this analysis
        monitorAnalysis(result.analysis_id);
        
        showNotification(`${getAnalysisDisplayName(analysisType)} analysis started`, 'success');
        updateActiveAnalysesDisplay();
        
    } catch (error) {
        console.error(`Error running ${analysisType} analysis:`, error);
        showNotification(`Failed to start ${analysisType} analysis: ${error.message}`, 'error');
    } finally {
        hideLoadingSpinner('analysis-results');
    }
}

async function runComprehensiveAnalysis() {
    try {
        showLoadingSpinner('comprehensive-analysis-results');
        
        const projectPath = getCurrentProjectPath();
        if (!projectPath) {
            showNotification('Please select a project first', 'warning');
            return;
        }
        
        const analysisTypes = [
            'dead_code',
            'code_quality',
            'security',
            'performance',
            'dependencies',
            'linear_integration',
            'github_integration',
            'prefect_workflows'
        ];
        
        const response = await fetch('/api/analysis/comprehensive', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                project_path: projectPath,
                analysis_types: analysisTypes,
                options: {
                    comprehensive: true,
                    include_recommendations: true,
                    generate_report: true
                }
            })
        });
        
        if (!response.ok) {
            throw new Error(`Comprehensive analysis failed: ${response.statusText}`);
        }
        
        const result = await response.json();
        
        // Track the comprehensive analysis
        comprehensiveAnalysisState.activeAnalyses[result.analysis_id] = {
            id: result.analysis_id,
            type: 'comprehensive',
            status: 'running',
            started_at: new Date().toISOString(),
            project_path: projectPath,
            analysis_types: analysisTypes,
            progress: 0
        };
        
        // Start monitoring this analysis
        monitorAnalysis(result.analysis_id);
        
        showNotification('Comprehensive analysis started', 'success');
        updateActiveAnalysesDisplay();
        
    } catch (error) {
        console.error('Error running comprehensive analysis:', error);
        showNotification(`Failed to start comprehensive analysis: ${error.message}`, 'error');
    } finally {
        hideLoadingSpinner('comprehensive-analysis-results');
    }
}

async function monitorAnalysis(analysisId) {
    const checkInterval = 5000; // Check every 5 seconds
    
    const checkStatus = async () => {
        try {
            const response = await fetch(`/api/analysis/${analysisId}/status`);
            if (!response.ok) {
                throw new Error(`Failed to get analysis status: ${response.statusText}`);
            }
            
            const status = await response.json();
            
            // Update local state
            if (comprehensiveAnalysisState.activeAnalyses[analysisId]) {
                comprehensiveAnalysisState.activeAnalyses[analysisId] = {
                    ...comprehensiveAnalysisState.activeAnalyses[analysisId],
                    ...status
                };
            }
            
            // Update UI
            updateAnalysisProgress(analysisId, status);
            
            // Check if analysis is complete
            if (status.status === 'completed') {
                await handleAnalysisCompletion(analysisId);
                return; // Stop monitoring
            } else if (status.status === 'failed') {
                handleAnalysisFailure(analysisId, status.error);
                return; // Stop monitoring
            }
            
            // Continue monitoring
            setTimeout(checkStatus, checkInterval);
            
        } catch (error) {
            console.error(`Error monitoring analysis ${analysisId}:`, error);
            // Continue monitoring despite errors
            setTimeout(checkStatus, checkInterval);
        }
    };
    
    // Start monitoring
    setTimeout(checkStatus, checkInterval);
}

async function handleAnalysisCompletion(analysisId) {
    try {
        // Get analysis results
        const response = await fetch(`/api/analysis/${analysisId}/results`);
        if (!response.ok) {
            throw new Error(`Failed to get analysis results: ${response.statusText}`);
        }
        
        const results = await response.json();
        
        // Update state
        const analysis = comprehensiveAnalysisState.activeAnalyses[analysisId];
        if (analysis) {
            analysis.status = 'completed';
            analysis.completed_at = new Date().toISOString();
            analysis.results = results;
            
            // Move to history
            comprehensiveAnalysisState.analysisHistory.unshift(analysis);
            delete comprehensiveAnalysisState.activeAnalyses[analysisId];
        }
        
        // Update UI
        updateActiveAnalysesDisplay();
        updateAnalysisHistoryDisplay();
        displayAnalysisResults(analysisId, results);
        
        showNotification(`Analysis ${analysisId} completed successfully`, 'success');
        
    } catch (error) {
        console.error(`Error handling analysis completion for ${analysisId}:`, error);
        showNotification(`Error retrieving results for analysis ${analysisId}`, 'error');
    }
}

function handleAnalysisFailure(analysisId, error) {
    const analysis = comprehensiveAnalysisState.activeAnalyses[analysisId];
    if (analysis) {
        analysis.status = 'failed';
        analysis.error = error;
        analysis.completed_at = new Date().toISOString();
        
        // Move to history
        comprehensiveAnalysisState.analysisHistory.unshift(analysis);
        delete comprehensiveAnalysisState.activeAnalyses[analysisId];
    }
    
    updateActiveAnalysesDisplay();
    updateAnalysisHistoryDisplay();
    
    showNotification(`Analysis ${analysisId} failed: ${error}`, 'error');
}

async function syncIntegration(integrationType) {
    try {
        showLoadingSpinner(`${integrationType}-integration-status`);
        
        const response = await fetch(`/api/integrations/${integrationType}/sync`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            throw new Error(`${integrationType} sync failed: ${response.statusText}`);
        }
        
        const result = await response.json();
        
        showNotification(`${integrationType} integration sync started`, 'success');
        
        // Refresh integration status
        await loadIntegrationStatus();
        
    } catch (error) {
        console.error(`Error syncing ${integrationType} integration:`, error);
        showNotification(`Failed to sync ${integrationType} integration: ${error.message}`, 'error');
    } finally {
        hideLoadingSpinner(`${integrationType}-integration-status`);
    }
}

async function loadIntegrationStatus() {
    try {
        const response = await fetch('/api/integrations/status');
        if (!response.ok) {
            throw new Error(`Failed to load integration status: ${response.statusText}`);
        }
        
        const status = await response.json();
        comprehensiveAnalysisState.integrationStatus = status;
        
        updateIntegrationStatusDisplay(status);
        
    } catch (error) {
        console.error('Error loading integration status:', error);
    }
}

async function loadSystemHealth() {
    try {
        const response = await fetch('/api/analysis/system/health');
        if (!response.ok) {
            throw new Error(`Failed to load system health: ${response.statusText}`);
        }
        
        const health = await response.json();
        comprehensiveAnalysisState.systemHealth = health;
        
        updateSystemHealthDisplay(health);
        
    } catch (error) {
        console.error('Error loading system health:', error);
    }
}

async function loadAnalysisHistory() {
    try {
        const response = await fetch('/api/analysis/history?limit=20');
        if (!response.ok) {
            throw new Error(`Failed to load analysis history: ${response.statusText}`);
        }
        
        const data = await response.json();
        comprehensiveAnalysisState.analysisHistory = data.analyses || [];
        
        updateAnalysisHistoryDisplay();
        
    } catch (error) {
        console.error('Error loading analysis history:', error);
    }
}

function updateActiveAnalysesDisplay() {
    const container = document.getElementById('active-analyses');
    if (!container) return;
    
    const activeAnalyses = Object.values(comprehensiveAnalysisState.activeAnalyses);
    
    if (activeAnalyses.length === 0) {
        container.innerHTML = `
            <div class="text-center text-muted p-4">
                <i class="fas fa-search fa-3x mb-3"></i>
                <p>No active analyses</p>
                <button class="btn btn-primary" onclick="runComprehensiveAnalysis()">
                    <i class="fas fa-play me-2"></i>Start Analysis
                </button>
            </div>
        `;
        return;
    }
    
    container.innerHTML = activeAnalyses.map(analysis => createAnalysisCard(analysis)).join('');
}

function createAnalysisCard(analysis) {
    const progressPercent = analysis.progress || 0;
    const statusColor = getAnalysisStatusColor(analysis.status);
    
    return `
        <div class="analysis-card card mb-3 ${analysis.status}">
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-start mb-3">
                    <div>
                        <h6 class="card-title mb-1">${getAnalysisDisplayName(analysis.type)}</h6>
                        <p class="text-muted mb-1">${analysis.project_path}</p>
                        <small class="text-muted">Started ${formatTime(analysis.started_at)}</small>
                    </div>
                    <div class="d-flex align-items-center">
                        <div class="progress-ring me-3">
                            <svg width="40" height="40">
                                <circle cx="20" cy="20" r="15" fill="none" stroke="#e9ecef" stroke-width="3"/>
                                <circle cx="20" cy="20" r="15" fill="none" stroke="var(--bs-primary)" 
                                        stroke-width="3" stroke-dasharray="94.2" 
                                        stroke-dashoffset="${94.2 - (94.2 * progressPercent / 100)}"
                                        transform="rotate(-90 20 20)"/>
                            </svg>
                            <span class="progress-text">${Math.round(progressPercent)}%</span>
                        </div>
                        <div class="dropdown">
                            <button class="btn btn-sm btn-outline-secondary" type="button" data-bs-toggle="dropdown">
                                <i class="fas fa-ellipsis-v"></i>
                            </button>
                            <ul class="dropdown-menu">
                                <li><a class="dropdown-item" href="#" onclick="viewAnalysisDetails('${analysis.id}')">
                                    <i class="fas fa-eye me-2"></i>View Details
                                </a></li>
                                <li><a class="dropdown-item text-danger" href="#" onclick="cancelAnalysis('${analysis.id}')">
                                    <i class="fas fa-stop me-2"></i>Cancel Analysis
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
                    <span class="badge bg-${statusColor}">${analysis.status}</span>
                    <div class="text-end">
                        <small class="text-muted">
                            ${analysis.analysis_types ? `${analysis.analysis_types.length} types` : ''}
                        </small>
                    </div>
                </div>
                
                ${analysis.error ? `
                    <div class="alert alert-danger mt-2 mb-0" role="alert">
                        <small><i class="fas fa-exclamation-triangle me-1"></i>${analysis.error}</small>
                    </div>
                ` : ''}
            </div>
        </div>
    `;
}

function updateIntegrationStatusDisplay(status) {
    // Update Linear status
    updateIntegrationCard('linear', status.integrations?.linear || false);
    
    // Update GitHub status
    updateIntegrationCard('github', status.integrations?.github || false);
    
    // Update Prefect status
    updateIntegrationCard('prefect', status.integrations?.prefect || false);
}

function updateIntegrationCard(integration, isAvailable) {
    const card = document.getElementById(`${integration}-integration-card`);
    if (!card) return;
    
    const statusBadge = card.querySelector('.integration-status');
    const syncButton = card.querySelector('.sync-button');
    
    if (statusBadge) {
        statusBadge.className = `badge integration-status ${isAvailable ? 'bg-success' : 'bg-danger'}`;
        statusBadge.textContent = isAvailable ? 'Available' : 'Unavailable';
    }
    
    if (syncButton) {
        syncButton.disabled = !isAvailable;
    }
}

function updateSystemHealthDisplay(health) {
    const container = document.getElementById('system-health-display');
    if (!container) return;
    
    container.innerHTML = `
        <div class="row">
            <div class="col-md-3">
                <div class="health-metric">
                    <h6>Active Analyses</h6>
                    <span class="metric-value">${health.active_analyses || 0}</span>
                </div>
            </div>
            <div class="col-md-3">
                <div class="health-metric">
                    <h6>Completed</h6>
                    <span class="metric-value">${health.completed_analyses || 0}</span>
                </div>
            </div>
            <div class="col-md-3">
                <div class="health-metric">
                    <h6>Integrations</h6>
                    <span class="metric-value">${Object.values(health.integrations || {}).filter(Boolean).length}/3</span>
                </div>
            </div>
            <div class="col-md-3">
                <div class="health-metric">
                    <h6>System Health</h6>
                    <span class="badge bg-success">Healthy</span>
                </div>
            </div>
        </div>
    `;
}

function updateAnalysisHistoryDisplay() {
    const container = document.getElementById('analysis-history');
    if (!container) return;
    
    const history = comprehensiveAnalysisState.analysisHistory.slice(0, 10); // Show last 10
    
    if (history.length === 0) {
        container.innerHTML = '<p class="text-muted text-center">No analysis history</p>';
        return;
    }
    
    container.innerHTML = history.map(analysis => `
        <div class="history-item d-flex justify-content-between align-items-center mb-2 p-2 border rounded">
            <div>
                <h6 class="mb-1">${getAnalysisDisplayName(analysis.type)}</h6>
                <small class="text-muted">${formatTime(analysis.completed_at || analysis.started_at)}</small>
            </div>
            <div>
                <span class="badge bg-${getAnalysisStatusColor(analysis.status)}">${analysis.status}</span>
                ${analysis.results ? `
                    <button class="btn btn-sm btn-outline-primary ms-2" onclick="viewAnalysisResults('${analysis.id}')">
                        <i class="fas fa-eye"></i>
                    </button>
                ` : ''}
            </div>
        </div>
    `).join('');
}

function displayAnalysisResults(analysisId, results) {
    const modal = document.getElementById('analysisResultsModal');
    if (!modal) return;
    
    const modalBody = modal.querySelector('.modal-body');
    const modalTitle = modal.querySelector('.modal-title');
    
    const analysis = comprehensiveAnalysisState.analysisHistory.find(a => a.id === analysisId);
    
    modalTitle.textContent = `Analysis Results: ${getAnalysisDisplayName(analysis?.type || 'Unknown')}`;
    
    modalBody.innerHTML = `
        <div class="analysis-results">
            <div class="mb-3">
                <h6>Analysis Summary</h6>
                <p class="text-muted">Completed: ${formatTime(analysis?.completed_at)}</p>
            </div>
            
            <div class="results-content">
                ${formatAnalysisResults(results)}
            </div>
        </div>
    `;
    
    const bootstrapModal = new bootstrap.Modal(modal);
    bootstrapModal.show();
}

function formatAnalysisResults(results) {
    if (!results || typeof results !== 'object') {
        return '<p class="text-muted">No results available</p>';
    }
    
    let html = '';
    
    for (const [key, value] of Object.entries(results)) {
        html += `
            <div class="result-section mb-3">
                <h6>${key.replace('_', ' ').toUpperCase()}</h6>
                <div class="result-content">
                    ${formatResultValue(value)}
                </div>
            </div>
        `;
    }
    
    return html;
}

function formatResultValue(value) {
    if (typeof value === 'object' && value !== null) {
        return `<pre class="bg-light p-2 rounded"><code>${JSON.stringify(value, null, 2)}</code></pre>`;
    } else {
        return `<p>${value}</p>`;
    }
}

// Utility functions
function getCurrentProjectPath() {
    // Get the currently selected project path
    return currentProject?.full_name || '.';
}

function getAnalysisOptions(analysisType) {
    // Return analysis-specific options
    const options = {
        dead_code: {
            include_tests: true,
            exclude_patterns: ['__pycache__', '*.pyc', '.git']
        },
        code_quality: {
            include_metrics: ['complexity', 'maintainability', 'duplication'],
            threshold: 'medium'
        },
        security: {
            include_dependencies: true,
            severity_threshold: 'medium'
        },
        performance: {
            include_profiling: false,
            analyze_imports: true
        }
    };
    
    return options[analysisType] || {};
}

function getAnalysisDisplayName(type) {
    const names = {
        'dead_code': 'Dead Code Analysis',
        'code_quality': 'Code Quality Analysis',
        'security': 'Security Analysis',
        'performance': 'Performance Analysis',
        'dependencies': 'Dependency Analysis',
        'linear_integration': 'Linear Integration',
        'github_integration': 'GitHub Integration',
        'prefect_workflows': 'Prefect Workflows',
        'comprehensive': 'Comprehensive Analysis'
    };
    
    return names[type] || type.replace('_', ' ').toUpperCase();
}

function getAnalysisStatusColor(status) {
    const colors = {
        'running': 'primary',
        'completed': 'success',
        'failed': 'danger',
        'cancelled': 'warning'
    };
    
    return colors[status] || 'secondary';
}

function updateAnalysisProgress(analysisId, status) {
    // Update progress in the UI
    const card = document.querySelector(`[data-analysis-id="${analysisId}"]`);
    if (card) {
        const progressBar = card.querySelector('.progress-bar');
        const progressText = card.querySelector('.progress-text');
        const statusBadge = card.querySelector('.badge');
        
        if (progressBar) {
            progressBar.style.width = `${status.progress || 0}%`;
        }
        
        if (progressText) {
            progressText.textContent = `${Math.round(status.progress || 0)}%`;
        }
        
        if (statusBadge) {
            statusBadge.className = `badge bg-${getAnalysisStatusColor(status.status)}`;
            statusBadge.textContent = status.status;
        }
    }
}

async function updateActiveAnalysesFromServer() {
    // Refresh active analyses from server
    for (const analysisId of Object.keys(comprehensiveAnalysisState.activeAnalyses)) {
        try {
            const response = await fetch(`/api/analysis/${analysisId}/status`);
            if (response.ok) {
                const status = await response.json();
                comprehensiveAnalysisState.activeAnalyses[analysisId] = {
                    ...comprehensiveAnalysisState.activeAnalyses[analysisId],
                    ...status
                };
            }
        } catch (error) {
            console.error(`Error updating analysis ${analysisId}:`, error);
        }
    }
    
    updateActiveAnalysesDisplay();
}

function viewAnalysisDetails(analysisId) {
    // Show detailed view of analysis
    const analysis = comprehensiveAnalysisState.activeAnalyses[analysisId] || 
                    comprehensiveAnalysisState.analysisHistory.find(a => a.id === analysisId);
    
    if (analysis) {
        console.log('Analysis details:', analysis);
        // Could open a modal or navigate to a detailed view
    }
}

function viewAnalysisResults(analysisId) {
    const analysis = comprehensiveAnalysisState.analysisHistory.find(a => a.id === analysisId);
    if (analysis && analysis.results) {
        displayAnalysisResults(analysisId, analysis.results);
    }
}

function cancelAnalysis(analysisId) {
    if (confirm('Are you sure you want to cancel this analysis?')) {
        // Implement analysis cancellation
        console.log('Cancelling analysis:', analysisId);
        // Would make API call to cancel the analysis
    }
}

// Export functions for global access
window.comprehensiveAnalysis = {
    runAnalysis,
    runComprehensiveAnalysis,
    syncIntegration,
    viewAnalysisDetails,
    viewAnalysisResults,
    cancelAnalysis
};

