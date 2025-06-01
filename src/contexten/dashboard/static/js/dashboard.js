// Contexten Dashboard JavaScript

// Global variables
let currentProject = null;
let integrationStatus = {};

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    console.log('Contexten Dashboard loaded');
    
    // Check for any initialization tasks
    checkIntegrationStatus();
});

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

// Project management functions
function formatProjectCard(project) {
    return `
        <div class="project-item mb-2 p-3 border rounded" onclick="selectProject('${project.full_name}', '${project.name}')">
            <div class="d-flex justify-content-between align-items-center">
                <div>
                    <h6 class="mb-1">${project.name}</h6>
                    <small class="text-muted">${project.description || 'No description'}</small>
                </div>
                <div>
                    <span class="badge bg-secondary">${project.language || 'Unknown'}</span>
                    ${project.private ? '<span class="badge bg-warning">Private</span>' : '<span class="badge bg-success">Public</span>'}
                </div>
            </div>
        </div>
    `;
}

// Error handling
function handleApiError(error, context = '') {
    console.error(`API Error ${context}:`, error);
    showAlert(`An error occurred ${context}. Please try again.`, 'danger');
}

// Auto-refresh functionality
setInterval(checkIntegrationStatus, 30000); // Check every 30 seconds

