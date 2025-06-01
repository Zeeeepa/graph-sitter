// Contexten Dashboard JavaScript
// Enhanced with comprehensive code analysis context and real-time monitoring

class CodeAnalysisDashboard {
    constructor(options = {}) {
        this.apiEndpoint = options.apiEndpoint || '/api/dashboard';
        this.realTimeEnabled = options.realTimeEnabled || true;
        this.refreshInterval = options.refreshInterval || 30000;
        this.charts = {};
        this.websocket = null;
        this.currentSection = 'overview';
        
        // Real-time monitoring data
        this.qualityMetrics = [];
        this.alerts = [];
        this.fileChanges = [];
        
        this.bindEvents();
    }

    initialize() {
        console.log('Initializing Code Analysis Dashboard...');
        
        // Initialize navigation
        this.initializeNavigation();
        
        // Load initial data
        this.loadDashboardData();
        
        // Initialize charts
        this.initializeCharts();
        
        // Setup real-time monitoring
        if (this.realTimeEnabled) {
            this.setupRealTimeMonitoring();
        }
        
        // Setup periodic refresh
        this.setupPeriodicRefresh();
        
        console.log('Code Analysis Dashboard initialized successfully');
    }

    bindEvents() {
        // Navigation events
        document.addEventListener('click', (e) => {
            if (e.target.matches('.nav-link')) {
                e.preventDefault();
                const section = e.target.getAttribute('href').substring(1);
                this.showSection(section);
            }
        });

        // Refresh button
        document.getElementById('refresh-data')?.addEventListener('click', () => {
            this.refreshData();
        });

        // Export button
        document.getElementById('export-report')?.addEventListener('click', () => {
            this.exportReport();
        });
    }

    initializeNavigation() {
        const navLinks = document.querySelectorAll('.nav-link');
        navLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                
                // Remove active class from all links
                navLinks.forEach(l => l.classList.remove('active'));
                
                // Add active class to clicked link
                link.classList.add('active');
                
                // Show corresponding section
                const section = link.getAttribute('href').substring(1);
                this.showSection(section);
            });
        });
    }

    showSection(sectionId) {
        // Hide all sections
        document.querySelectorAll('.dashboard-section').forEach(section => {
            section.style.display = 'none';
        });
        
        // Show selected section
        const targetSection = document.getElementById(sectionId);
        if (targetSection) {
            targetSection.style.display = 'block';
            this.currentSection = sectionId;
            
            // Load section-specific data
            this.loadSectionData(sectionId);
        }
    }

    async loadDashboardData() {
        try {
            const response = await fetch(`${this.apiEndpoint}/data`);
            const data = await response.json();
            
            this.updateOverviewMetrics(data);
            this.updateRecentAlerts(data.alerts || []);
            
        } catch (error) {
            console.error('Failed to load dashboard data:', error);
            this.showError('Failed to load dashboard data');
        }
    }

    async loadSectionData(sectionId) {
        try {
            const response = await fetch(`${this.apiEndpoint}/section/${sectionId}`);
            const data = await response.json();
            
            switch (sectionId) {
                case 'code-quality':
                    this.updateCodeQualitySection(data);
                    break;
                case 'architecture':
                    this.updateArchitectureSection(data);
                    break;
                case 'dependencies':
                    this.updateDependenciesSection(data);
                    break;
                case 'security':
                    this.updateSecuritySection(data);
                    break;
                case 'performance':
                    this.updatePerformanceSection(data);
                    break;
                case 'real-time':
                    this.updateRealTimeSection(data);
                    break;
                case 'alerts':
                    this.updateAlertsSection(data);
                    break;
            }
            
        } catch (error) {
            console.error(`Failed to load ${sectionId} data:`, error);
        }
    }

    updateOverviewMetrics(data) {
        // Update metric cards
        this.updateElement('health-score', data.health_score?.toFixed(2) || '0.85');
        this.updateElement('tech-debt', data.technical_debt_score?.toFixed(2) || '0.35');
        this.updateElement('complexity-score', data.complexity_score?.toFixed(2) || '0.65');
        this.updateElement('test-coverage', `${((data.test_coverage || 0.78) * 100).toFixed(1)}%`);
        
        // Update progress bars
        this.updateProgressBar('health-score', data.health_score || 0.85);
        this.updateProgressBar('tech-debt', data.technical_debt_score || 0.35);
        this.updateProgressBar('complexity-score', data.complexity_score || 0.65);
        this.updateProgressBar('test-coverage', data.test_coverage || 0.78);
        
        // Update quality trends chart
        if (this.charts.qualityTrends) {
            this.updateQualityTrendsChart(data.quality_trends || []);
        }
    }

    updateCodeQualitySection(data) {
        // Update quality metrics chart
        if (this.charts.qualityMetrics) {
            this.updateQualityMetricsChart(data.metrics || {});
        }
        
        // Update code issues list
        this.updateCodeIssuesList(data.issues || []);
        
        // Update file-level quality table
        this.updateFileQualityTable(data.file_quality || []);
    }

    updateArchitectureSection(data) {
        // Update dependency graph
        this.updateDependencyGraph(data.dependency_graph || {});
        
        // Update architecture metrics
        this.updateArchitectureMetrics(data.metrics || {});
    }

    updateDependenciesSection(data) {
        // Update circular dependencies
        this.updateCircularDependencies(data.circular_dependencies || []);
        
        // Update dependency health chart
        if (this.charts.dependencyHealth) {
            this.updateDependencyHealthChart(data.dependency_health || {});
        }
    }

    updateSecuritySection(data) {
        // Update security issues
        this.updateSecurityIssues(data.security_issues || []);
        
        // Update security score chart
        if (this.charts.securityScore) {
            this.updateSecurityScoreChart(data.security_score || {});
        }
    }

    updatePerformanceSection(data) {
        // Update performance metrics chart
        if (this.charts.performanceMetrics) {
            this.updatePerformanceMetricsChart(data.metrics || {});
        }
        
        // Update performance bottlenecks
        this.updatePerformanceBottlenecks(data.bottlenecks || []);
    }

    updateRealTimeSection(data) {
        // Update live metrics chart
        if (this.charts.liveMetrics) {
            this.updateLiveMetricsChart(data.live_metrics || []);
        }
        
        // Update file changes
        this.updateFileChanges(data.file_changes || []);
    }

    updateAlertsSection(data) {
        // Update alerts table
        this.updateAlertsTable(data.alerts || []);
    }

    initializeCharts() {
        // Quality Trends Chart
        this.initializeQualityTrendsChart();
        
        // Quality Metrics Chart
        this.initializeQualityMetricsChart();
        
        // Dependency Health Chart
        this.initializeDependencyHealthChart();
        
        // Security Score Chart
        this.initializeSecurityScoreChart();
        
        // Performance Metrics Chart
        this.initializePerformanceMetricsChart();
        
        // Live Metrics Chart
        this.initializeLiveMetricsChart();
    }

    initializeQualityTrendsChart() {
        const ctx = document.getElementById('qualityTrendsChart');
        if (!ctx) return;

        this.charts.qualityTrends = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'Health Score',
                        data: [],
                        borderColor: 'rgb(75, 192, 192)',
                        backgroundColor: 'rgba(75, 192, 192, 0.2)',
                        tension: 0.1
                    },
                    {
                        label: 'Technical Debt',
                        data: [],
                        borderColor: 'rgb(255, 99, 132)',
                        backgroundColor: 'rgba(255, 99, 132, 0.2)',
                        tension: 0.1
                    },
                    {
                        label: 'Complexity',
                        data: [],
                        borderColor: 'rgb(54, 162, 235)',
                        backgroundColor: 'rgba(54, 162, 235, 0.2)',
                        tension: 0.1
                    }
                ]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Quality Metrics Over Time'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 1
                    }
                }
            }
        });
    }

    initializeQualityMetricsChart() {
        const ctx = document.getElementById('qualityMetricsChart');
        if (!ctx) return;

        this.charts.qualityMetrics = new Chart(ctx, {
            type: 'radar',
            data: {
                labels: ['Health', 'Maintainability', 'Complexity', 'Documentation', 'Test Coverage', 'Security'],
                datasets: [{
                    label: 'Current Scores',
                    data: [0.85, 0.75, 0.65, 0.70, 0.78, 0.82],
                    borderColor: 'rgb(54, 162, 235)',
                    backgroundColor: 'rgba(54, 162, 235, 0.2)',
                    pointBackgroundColor: 'rgb(54, 162, 235)',
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: 'rgb(54, 162, 235)'
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Quality Metrics Radar'
                    }
                },
                scales: {
                    r: {
                        beginAtZero: true,
                        max: 1
                    }
                }
            }
        });
    }

    initializeDependencyHealthChart() {
        const ctx = document.getElementById('dependencyHealthChart');
        if (!ctx) return;

        this.charts.dependencyHealth = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Healthy', 'Warning', 'Critical'],
                datasets: [{
                    data: [70, 20, 10],
                    backgroundColor: [
                        'rgb(75, 192, 192)',
                        'rgb(255, 205, 86)',
                        'rgb(255, 99, 132)'
                    ]
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Dependency Health Status'
                    }
                }
            }
        });
    }

    initializeSecurityScoreChart() {
        const ctx = document.getElementById('securityScoreChart');
        if (!ctx) return;

        this.charts.securityScore = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Authentication', 'Authorization', 'Data Protection', 'Input Validation', 'Error Handling'],
                datasets: [{
                    label: 'Security Score',
                    data: [0.9, 0.8, 0.85, 0.75, 0.88],
                    backgroundColor: 'rgba(75, 192, 192, 0.6)',
                    borderColor: 'rgb(75, 192, 192)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Security Assessment by Category'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 1
                    }
                }
            }
        });
    }

    initializePerformanceMetricsChart() {
        const ctx = document.getElementById('performanceMetricsChart');
        if (!ctx) return;

        this.charts.performanceMetrics = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'Response Time (ms)',
                        data: [],
                        borderColor: 'rgb(255, 99, 132)',
                        backgroundColor: 'rgba(255, 99, 132, 0.2)',
                        yAxisID: 'y'
                    },
                    {
                        label: 'Memory Usage (MB)',
                        data: [],
                        borderColor: 'rgb(54, 162, 235)',
                        backgroundColor: 'rgba(54, 162, 235, 0.2)',
                        yAxisID: 'y1'
                    }
                ]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Performance Metrics'
                    }
                },
                scales: {
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        grid: {
                            drawOnChartArea: false,
                        },
                    }
                }
            }
        });
    }

    initializeLiveMetricsChart() {
        const ctx = document.getElementById('liveMetricsChart');
        if (!ctx) return;

        this.charts.liveMetrics = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'Health Score',
                        data: [],
                        borderColor: 'rgb(75, 192, 192)',
                        backgroundColor: 'rgba(75, 192, 192, 0.2)',
                        tension: 0.1
                    }
                ]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Live Quality Metrics'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 1
                    }
                },
                animation: {
                    duration: 0
                }
            }
        });
    }

    setupRealTimeMonitoring() {
        // Setup WebSocket connection for real-time updates
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/dashboard`;
        
        this.websocket = new WebSocket(wsUrl);
        
        this.websocket.onopen = () => {
            console.log('Real-time monitoring connected');
            this.updateMonitoringStatus('Live', 'success');
        };
        
        this.websocket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleRealTimeUpdate(data);
        };
        
        this.websocket.onclose = () => {
            console.log('Real-time monitoring disconnected');
            this.updateMonitoringStatus('Disconnected', 'danger');
            
            // Attempt to reconnect after 5 seconds
            setTimeout(() => {
                this.setupRealTimeMonitoring();
            }, 5000);
        };
        
        this.websocket.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.updateMonitoringStatus('Error', 'danger');
        };
    }

    handleRealTimeUpdate(data) {
        switch (data.type) {
            case 'quality_metrics':
                this.updateRealTimeMetrics(data.payload);
                break;
            case 'alert':
                this.addAlert(data.payload);
                break;
            case 'file_change':
                this.addFileChange(data.payload);
                break;
            case 'analysis_complete':
                this.handleAnalysisComplete(data.payload);
                break;
        }
    }

    updateRealTimeMetrics(metrics) {
        // Update live metrics chart
        if (this.charts.liveMetrics && this.currentSection === 'real-time') {
            const chart = this.charts.liveMetrics;
            const now = new Date().toLocaleTimeString();
            
            chart.data.labels.push(now);
            chart.data.datasets[0].data.push(metrics.health_score);
            
            // Keep only last 20 data points
            if (chart.data.labels.length > 20) {
                chart.data.labels.shift();
                chart.data.datasets[0].data.shift();
            }
            
            chart.update('none');
        }
        
        // Update overview metrics if on overview section
        if (this.currentSection === 'overview') {
            this.updateOverviewMetrics(metrics);
        }
    }

    addAlert(alert) {
        this.alerts.unshift(alert);
        
        // Update recent alerts in overview
        this.updateRecentAlerts(this.alerts.slice(0, 5));
        
        // Update alerts table if on alerts section
        if (this.currentSection === 'alerts') {
            this.updateAlertsTable(this.alerts);
        }
        
        // Show notification
        this.showNotification(alert.message, alert.severity);
    }

    addFileChange(change) {
        this.fileChanges.unshift(change);
        
        // Update file changes list if on real-time section
        if (this.currentSection === 'real-time') {
            this.updateFileChanges(this.fileChanges.slice(0, 10));
        }
    }

    setupPeriodicRefresh() {
        setInterval(() => {
            if (!this.websocket || this.websocket.readyState !== WebSocket.OPEN) {
                this.refreshData();
            }
        }, this.refreshInterval);
    }

    async refreshData() {
        console.log('Refreshing dashboard data...');
        await this.loadDashboardData();
        await this.loadSectionData(this.currentSection);
    }

    async exportReport() {
        try {
            const response = await fetch(`${this.apiEndpoint}/export`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    format: 'pdf',
                    sections: ['overview', 'code-quality', 'architecture', 'security']
                })
            });
            
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `code-analysis-report-${new Date().toISOString().split('T')[0]}.pdf`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
            }
        } catch (error) {
            console.error('Failed to export report:', error);
            this.showError('Failed to export report');
        }
    }

    // Utility methods
    updateElement(id, value) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
    }

    updateProgressBar(id, value) {
        const element = document.getElementById(id);
        if (element) {
            const progressBar = element.parentElement.querySelector('.progress-bar');
            if (progressBar) {
                progressBar.style.width = `${value * 100}%`;
            }
        }
    }

    updateMonitoringStatus(status, type) {
        const statusElement = document.getElementById('monitoring-status');
        if (statusElement) {
            statusElement.textContent = status;
            statusElement.className = `badge bg-${type}`;
        }
    }

    showNotification(message, severity) {
        // Create and show a toast notification
        const toast = document.createElement('div');
        toast.className = `alert alert-${severity === 'critical' ? 'danger' : severity === 'warning' ? 'warning' : 'info'} alert-dismissible fade show position-fixed`;
        toast.style.top = '20px';
        toast.style.right = '20px';
        toast.style.zIndex = '9999';
        toast.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(toast);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (toast.parentElement) {
                toast.parentElement.removeChild(toast);
            }
        }, 5000);
    }

    showError(message) {
        this.showNotification(message, 'danger');
    }

    // Data update methods for different sections
    updateRecentAlerts(alerts) {
        const container = document.getElementById('recent-alerts');
        if (!container) return;
        
        container.innerHTML = alerts.map(alert => `
            <div class="alert alert-${alert.severity === 'critical' ? 'danger' : alert.severity === 'warning' ? 'warning' : 'info'} alert-sm">
                <strong>${alert.severity.toUpperCase()}</strong>: ${alert.message}
                <small class="d-block text-muted">${new Date(alert.timestamp).toLocaleString()}</small>
            </div>
        `).join('');
    }

    updateCodeIssuesList(issues) {
        const container = document.getElementById('code-issues-list');
        if (!container) return;
        
        container.innerHTML = issues.map(issue => `
            <div class="card mb-2">
                <div class="card-body p-3">
                    <h6 class="card-title">${issue.title}</h6>
                    <p class="card-text small">${issue.description}</p>
                    <span class="badge bg-${issue.severity === 'high' ? 'danger' : issue.severity === 'medium' ? 'warning' : 'info'}">${issue.severity}</span>
                    <span class="badge bg-secondary">${issue.file}</span>
                </div>
            </div>
        `).join('');
    }

    updateFileQualityTable(fileQuality) {
        const tbody = document.querySelector('#file-quality-table tbody');
        if (!tbody) return;
        
        tbody.innerHTML = fileQuality.map(file => `
            <tr>
                <td><code>${file.path}</code></td>
                <td>
                    <div class="progress">
                        <div class="progress-bar bg-${file.quality_score > 0.8 ? 'success' : file.quality_score > 0.6 ? 'warning' : 'danger'}" 
                             style="width: ${file.quality_score * 100}%">${(file.quality_score * 100).toFixed(1)}%</div>
                    </div>
                </td>
                <td>${file.complexity}</td>
                <td>${file.maintainability}</td>
                <td><span class="badge bg-danger">${file.issues}</span></td>
                <td>
                    <button class="btn btn-sm btn-outline-primary" onclick="viewFileDetails('${file.path}')">
                        <i class="fas fa-eye"></i>
                    </button>
                </td>
            </tr>
        `).join('');
    }

    updateDependencyGraph(graphData) {
        // Implementation for dependency graph visualization using D3.js
        const container = document.getElementById('dependency-graph');
        if (!container) return;
        
        // Clear previous graph
        container.innerHTML = '';
        
        // Create SVG
        const svg = d3.select(container)
            .append('svg')
            .attr('width', '100%')
            .attr('height', '100%');
        
        // Add graph visualization logic here
        // This would be a complex D3.js implementation
    }

    updateArchitectureMetrics(metrics) {
        const container = document.getElementById('architecture-metrics');
        if (!container) return;
        
        container.innerHTML = `
            <div class="metric-item mb-3">
                <h6>Modules</h6>
                <div class="h4">${metrics.modules || 0}</div>
            </div>
            <div class="metric-item mb-3">
                <h6>Coupling</h6>
                <div class="progress">
                    <div class="progress-bar bg-info" style="width: ${(metrics.coupling || 0.5) * 100}%"></div>
                </div>
            </div>
            <div class="metric-item mb-3">
                <h6>Cohesion</h6>
                <div class="progress">
                    <div class="progress-bar bg-success" style="width: ${(metrics.cohesion || 0.7) * 100}%"></div>
                </div>
            </div>
        `;
    }

    updateCircularDependencies(dependencies) {
        const container = document.getElementById('circular-dependencies');
        if (!container) return;
        
        if (dependencies.length === 0) {
            container.innerHTML = '<div class="alert alert-success">No circular dependencies found!</div>';
        } else {
            container.innerHTML = dependencies.map(dep => `
                <div class="alert alert-warning">
                    <strong>Circular dependency detected:</strong><br>
                    ${dep.cycle.join(' → ')}
                </div>
            `).join('');
        }
    }

    updateSecurityIssues(issues) {
        const container = document.getElementById('security-issues');
        if (!container) return;
        
        container.innerHTML = issues.map(issue => `
            <div class="card mb-2">
                <div class="card-body p-3">
                    <h6 class="card-title">${issue.title}</h6>
                    <p class="card-text small">${issue.description}</p>
                    <span class="badge bg-${issue.severity === 'critical' ? 'danger' : issue.severity === 'high' ? 'warning' : 'info'}">${issue.severity}</span>
                    <span class="badge bg-secondary">${issue.category}</span>
                </div>
            </div>
        `).join('');
    }

    updatePerformanceBottlenecks(bottlenecks) {
        const container = document.getElementById('performance-bottlenecks');
        if (!container) return;
        
        container.innerHTML = bottlenecks.map(bottleneck => `
            <div class="card mb-2">
                <div class="card-body p-3">
                    <h6 class="card-title">${bottleneck.function}</h6>
                    <p class="card-text small">${bottleneck.file}:${bottleneck.line}</p>
                    <span class="badge bg-warning">${bottleneck.impact}</span>
                </div>
            </div>
        `).join('');
    }

    updateFileChanges(changes) {
        const container = document.getElementById('file-changes');
        if (!container) return;
        
        container.innerHTML = changes.map(change => `
            <div class="d-flex justify-content-between align-items-center mb-2 p-2 border rounded">
                <div>
                    <small class="text-muted">${change.file}</small><br>
                    <span class="badge bg-${change.type === 'modified' ? 'warning' : change.type === 'added' ? 'success' : 'danger'}">${change.type}</span>
                </div>
                <small class="text-muted">${new Date(change.timestamp).toLocaleTimeString()}</small>
            </div>
        `).join('');
    }

    updateAlertsTable(alerts) {
        const tbody = document.querySelector('#alerts-table tbody');
        if (!tbody) return;
        
        tbody.innerHTML = alerts.map(alert => `
            <tr>
                <td><span class="badge bg-${alert.severity === 'critical' ? 'danger' : alert.severity === 'warning' ? 'warning' : 'info'}">${alert.severity}</span></td>
                <td>${alert.type}</td>
                <td>${alert.message}</td>
                <td>${new Date(alert.timestamp).toLocaleString()}</td>
                <td>
                    <button class="btn btn-sm btn-outline-primary" onclick="acknowledgeAlert('${alert.id}')">
                        <i class="fas fa-check"></i>
                    </button>
                </td>
            </tr>
        `).join('');
    }
}

// Global functions
function viewFileDetails(filePath) {
    // Implementation for viewing file details
    console.log('Viewing details for:', filePath);
}

function acknowledgeAlert(alertId) {
    // Implementation for acknowledging alerts
    console.log('Acknowledging alert:', alertId);
}

// Initialize dashboard when DOM is loaded
console.log('Contexten Dashboard loaded');

