// Contexten Dashboard JavaScript

const { createApp } = Vue;

createApp({
    data() {
        return {
            // State
            projects: [],
            availableRepos: [],
            recentEvents: [],
            systemStatus: {},
            settings: {
                setup_status: { credentials: {} },
                notification_settings: {},
                extensions: {}
            },
            
            // UI State
            selectedProject: null,
            currentPlan: null,
            projectAnalysis: null,
            projectDeployment: null,
            activeTab: 'requirements',
            requirements: '',
            showRepoSelection: false,
            showSettings: false,
            
            // WebSocket
            websocket: null,
            
            // Loading states
            loading: {
                projects: false,
                repos: false,
                analysis: false,
                deployment: false,
                plan: false
            }
        };
    },
    
    async mounted() {
        await this.initialize();
    },
    
    beforeUnmount() {
        if (this.websocket) {
            this.websocket.close();
        }
    },
    
    methods: {
        async initialize() {
            console.log('🚀 Initializing dashboard...');
            
            // Load initial data
            await Promise.all([
                this.loadProjects(),
                this.loadSystemStatus(),
                this.loadSettings(),
                this.loadRecentEvents()
            ]);
            
            // Setup WebSocket
            this.setupWebSocket();
            
            // Setup periodic updates
            setInterval(() => {
                this.loadRecentEvents();
                this.loadSystemStatus();
            }, 30000); // Update every 30 seconds
            
            console.log('✅ Dashboard initialized');
        },
        
        async loadProjects() {
            try {
                this.loading.projects = true;
                const response = await axios.get('/api/projects/pinned');
                this.projects = response.data;
            } catch (error) {
                console.error('Failed to load projects:', error);
                this.showError('Failed to load projects');
            } finally {
                this.loading.projects = false;
            }
        },
        
        async loadSystemStatus() {
            try {
                const response = await axios.get('/api/status');
                this.systemStatus = response.data;
            } catch (error) {
                console.error('Failed to load system status:', error);
            }
        },
        
        async loadSettings() {
            try {
                const response = await axios.get('/api/settings');
                this.settings = response.data;
            } catch (error) {
                console.error('Failed to load settings:', error);
            }
        },
        
        async loadRecentEvents() {
            try {
                const response = await axios.get('/api/events?limit=20');
                this.recentEvents = response.data;
            } catch (error) {
                console.error('Failed to load events:', error);
            }
        },
        
        async discoverRepos() {
            try {
                this.loading.repos = true;
                this.showRepoSelection = true;
                const response = await axios.get('/api/repositories');
                this.availableRepos = response.data;
            } catch (error) {
                console.error('Failed to discover repositories:', error);
                this.showError('Failed to discover repositories. Check your GitHub token.');
            } finally {
                this.loading.repos = false;
            }
        },
        
        async pinRepository(repoUrl) {
            try {
                const response = await axios.post('/api/projects/pin', {
                    repo_url: repoUrl
                });
                
                this.projects.push(response.data);
                this.showRepoSelection = false;
                this.showSuccess('Project pinned successfully!');
                
                // Auto-analyze the project
                setTimeout(() => {
                    this.analyzeProjectById(response.data.project_id);
                }, 1000);
                
            } catch (error) {
                console.error('Failed to pin repository:', error);
                this.showError('Failed to pin repository');
            }
        },
        
        async unpinProject(projectId) {
            if (!confirm('Are you sure you want to unpin this project?')) {
                return;
            }
            
            try {
                await axios.post(`/api/projects/${projectId}/unpin`);
                this.projects = this.projects.filter(p => p.project_id !== projectId);
                this.showSuccess('Project unpinned successfully!');
            } catch (error) {
                console.error('Failed to unpin project:', error);
                this.showError('Failed to unpin project');
            }
        },
        
        async openProject(project) {
            this.selectedProject = project;
            this.activeTab = 'requirements';
            this.requirements = '';
            this.currentPlan = null;
            this.projectAnalysis = null;
            this.projectDeployment = null;
            
            // Load project data
            await Promise.all([
                this.loadProjectPlans(project.project_id),
                this.loadProjectAnalysis(project.project_id),
                this.loadProjectDeployment(project.project_id)
            ]);
        },
        
        closeProject() {
            this.selectedProject = null;
            this.currentPlan = null;
            this.projectAnalysis = null;
            this.projectDeployment = null;
        },
        
        async loadProjectPlans(projectId) {
            try {
                const response = await axios.get(`/api/projects/${projectId}/plans`);
                if (response.data.length > 0) {
                    this.currentPlan = response.data[response.data.length - 1]; // Get latest plan
                }
            } catch (error) {
                console.error('Failed to load project plans:', error);
            }
        },
        
        async loadProjectAnalysis(projectId) {
            try {
                const response = await axios.get(`/api/projects/${projectId}/analysis`);
                this.projectAnalysis = response.data;
            } catch (error) {
                // Analysis might not exist yet
                console.log('No analysis found for project');
            }
        },
        
        async loadProjectDeployment(projectId) {
            try {
                const response = await axios.get(`/api/projects/${projectId}/deployment`);
                this.projectDeployment = response.data;
            } catch (error) {
                // Deployment might not exist yet
                console.log('No deployment found for project');
            }
        },
        
        async generatePlan() {
            if (!this.requirements.trim()) {
                this.showError('Please enter requirements first');
                return;
            }
            
            try {
                this.loading.plan = true;
                const response = await axios.post(`/api/projects/${this.selectedProject.project_id}/plan`, {
                    requirements: this.requirements
                });
                
                this.currentPlan = response.data;
                this.activeTab = 'plan';
                this.showSuccess('Plan generated successfully!');
                
                // Update project in list
                const projectIndex = this.projects.findIndex(p => p.project_id === this.selectedProject.project_id);
                if (projectIndex !== -1) {
                    this.projects[projectIndex].current_plan_id = response.data.plan_id;
                    this.projects[projectIndex].status = 'planned';
                }
                
            } catch (error) {
                console.error('Failed to generate plan:', error);
                this.showError('Failed to generate plan');
            } finally {
                this.loading.plan = false;
            }
        },
        
        async startWorkflow() {
            try {
                await axios.post(`/api/projects/${this.selectedProject.project_id}/workflow/start`);
                this.selectedProject.flow_status = 'starting';
                this.showSuccess('Workflow started!');
                
                // Update project in list
                const projectIndex = this.projects.findIndex(p => p.project_id === this.selectedProject.project_id);
                if (projectIndex !== -1) {
                    this.projects[projectIndex].flow_status = 'starting';
                }
                
            } catch (error) {
                console.error('Failed to start workflow:', error);
                this.showError('Failed to start workflow');
            }
        },
        
        async stopWorkflow() {
            try {
                await axios.post(`/api/projects/${this.selectedProject.project_id}/workflow/stop`);
                this.selectedProject.flow_status = 'paused';
                this.showSuccess('Workflow paused!');
                
                // Update project in list
                const projectIndex = this.projects.findIndex(p => p.project_id === this.selectedProject.project_id);
                if (projectIndex !== -1) {
                    this.projects[projectIndex].flow_status = 'paused';
                }
                
            } catch (error) {
                console.error('Failed to stop workflow:', error);
                this.showError('Failed to stop workflow');
            }
        },
        
        async analyzeProject() {
            await this.analyzeProjectById(this.selectedProject.project_id);
        },
        
        async analyzeProjectById(projectId) {
            try {
                this.loading.analysis = true;
                const response = await axios.post(`/api/projects/${projectId}/analyze`);
                
                if (this.selectedProject && this.selectedProject.project_id === projectId) {
                    this.projectAnalysis = response.data;
                    this.activeTab = 'analysis';
                }
                
                this.showSuccess('Analysis completed!');
                
            } catch (error) {
                console.error('Failed to analyze project:', error);
                this.showError('Failed to analyze project');
            } finally {
                this.loading.analysis = false;
            }
        },
        
        async deployProject() {
            try {
                this.loading.deployment = true;
                const response = await axios.post(`/api/projects/${this.selectedProject.project_id}/deploy`);
                this.projectDeployment = response.data;
                this.showSuccess('Deployment started!');
                
            } catch (error) {
                console.error('Failed to deploy project:', error);
                this.showError('Failed to deploy project');
            } finally {
                this.loading.deployment = false;
            }
        },
        
        async updateNotificationSettings() {
            try {
                await axios.post('/api/settings/notifications', this.settings.notification_settings);
                this.showSuccess('Notification settings updated!');
            } catch (error) {
                console.error('Failed to update notification settings:', error);
                this.showError('Failed to update notification settings');
            }
        },
        
        async testSlack() {
            try {
                const response = await axios.post('/api/settings/test-slack');
                if (response.data.success) {
                    this.showSuccess('Slack test message sent!');
                } else {
                    this.showError('Slack test failed - check your webhook URL');
                }
            } catch (error) {
                console.error('Slack test failed:', error);
                this.showError('Slack test failed');
            }
        },
        
        setupWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws`;
            
            this.websocket = new WebSocket(wsUrl);
            
            this.websocket.onopen = () => {
                console.log('🔌 WebSocket connected');
            };
            
            this.websocket.onmessage = (event) => {
                try {
                    const eventData = JSON.parse(event.data);
                    this.handleRealtimeEvent(eventData);
                } catch (error) {
                    console.error('Failed to parse WebSocket message:', error);
                }
            };
            
            this.websocket.onclose = () => {
                console.log('🔌 WebSocket disconnected');
                // Attempt to reconnect after 5 seconds
                setTimeout(() => {
                    this.setupWebSocket();
                }, 5000);
            };
            
            this.websocket.onerror = (error) => {
                console.error('WebSocket error:', error);
            };
        },
        
        handleRealtimeEvent(eventData) {
            // Add to recent events
            this.recentEvents.unshift(eventData);
            if (this.recentEvents.length > 50) {
                this.recentEvents = this.recentEvents.slice(0, 50);
            }
            
            // Update project status if relevant
            if (eventData.project_id) {
                const project = this.projects.find(p => p.project_id === eventData.project_id);
                if (project) {
                    this.updateProjectFromEvent(project, eventData);
                }
                
                // Update selected project if it matches
                if (this.selectedProject && this.selectedProject.project_id === eventData.project_id) {
                    this.updateProjectFromEvent(this.selectedProject, eventData);
                }
            }
            
            // Show notifications for important events
            this.showEventNotification(eventData);
        },
        
        updateProjectFromEvent(project, eventData) {
            switch (eventData.event_type) {
                case 'workflow_started':
                    project.flow_status = 'running';
                    break;
                case 'workflow_completed':
                    project.flow_status = 'completed';
                    break;
                case 'workflow_failed':
                    project.flow_status = 'failed';
                    break;
                case 'analysis_completed':
                    project.status = 'analyzed';
                    break;
                case 'deployment_completed':
                    project.status = 'deployed';
                    break;
            }
        },
        
        showEventNotification(eventData) {
            const importantEvents = ['workflow_completed', 'workflow_failed', 'deployment_completed'];
            if (importantEvents.includes(eventData.event_type)) {
                const message = this.formatEventMessage(eventData);
                this.showInfo(message);
            }
        },
        
        formatEventMessage(eventData) {
            const messages = {
                'workflow_completed': '✅ Workflow completed successfully',
                'workflow_failed': '❌ Workflow failed',
                'deployment_completed': '🚀 Deployment completed',
                'analysis_completed': '🔍 Code analysis completed'
            };
            return messages[eventData.event_type] || `Event: ${eventData.event_type}`;
        },
        
        // Utility methods
        formatDate(dateString) {
            return new Date(dateString).toLocaleDateString();
        },
        
        formatTime(dateString) {
            return new Date(dateString).toLocaleTimeString();
        },
        
        formatUptime(seconds) {
            if (!seconds) return '0s';
            
            const hours = Math.floor(seconds / 3600);
            const minutes = Math.floor((seconds % 3600) / 60);
            const secs = Math.floor(seconds % 60);
            
            if (hours > 0) {
                return `${hours}h ${minutes}m`;
            } else if (minutes > 0) {
                return `${minutes}m ${secs}s`;
            } else {
                return `${secs}s`;
            }
        },
        
        formatEventType(eventType) {
            return eventType.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
        },
        
        getProjectProgress(project) {
            if (!this.currentPlan || project.project_id !== this.selectedProject?.project_id) {
                return 0;
            }
            
            const completedTasks = this.currentPlan.tasks.filter(t => t.status === 'completed').length;
            const totalTasks = this.currentPlan.tasks.length;
            
            return totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 100) : 0;
        },
        
        // Notification methods
        showSuccess(message) {
            this.showNotification(message, 'success');
        },
        
        showError(message) {
            this.showNotification(message, 'error');
        },
        
        showInfo(message) {
            this.showNotification(message, 'info');
        },
        
        showNotification(message, type = 'info') {
            // Simple notification system - could be enhanced with a proper toast library
            const notification = document.createElement('div');
            notification.className = `notification notification-${type}`;
            notification.textContent = message;
            notification.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                padding: 1rem 1.5rem;
                border-radius: 6px;
                color: white;
                font-weight: 500;
                z-index: 10000;
                max-width: 400px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                background: ${type === 'success' ? '#38a169' : type === 'error' ? '#e53e3e' : '#3182ce'};
            `;
            
            document.body.appendChild(notification);
            
            // Auto-remove after 5 seconds
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 5000);
            
            // Allow manual dismissal
            notification.addEventListener('click', () => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            });
        }
    }
}).mount('#app');

