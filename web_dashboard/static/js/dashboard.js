/**
 * Tunisia Intelligence Dashboard JavaScript
 * Handles real-time updates, user interactions, and data visualization
 */

class TunisiaIntelligenceDashboard {
    constructor() {
        this.socket = null;
        this.lastData = null;
        this.isConnected = false;
        this.charts = {};
        this.updateInterval = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        
        this.init();
    }
    
    init() {
        console.log('Initializing Tunisia Intelligence Dashboard');
        this.initializeSocket();
        this.setupEventListeners();
        this.loadInitialData();
        this.startPeriodicUpdates();
    }
    
    initializeSocket() {
        try {
            this.socket = io({
                transports: ['websocket', 'polling'],
                timeout: 10000,
                reconnection: true,
                reconnectionDelay: 2000,
                reconnectionAttempts: this.maxReconnectAttempts
            });
            
            this.socket.on('connect', () => {
                console.log('Connected to dashboard server');
                this.isConnected = true;
                this.reconnectAttempts = 0;
                this.updateConnectionStatus();
                this.socket.emit('request_update');
            });
            
            this.socket.on('disconnect', (reason) => {
                console.log('Disconnected from dashboard server:', reason);
                this.isConnected = false;
                this.updateConnectionStatus();
            });
            
            this.socket.on('status', (data) => {
                console.log('Received status update:', data);
                this.lastData = data;
                this.updateDashboard(data);
            });
            
        } catch (error) {
            console.error('Failed to initialize socket connection:', error);
            this.showNotification('Failed to initialize real-time connection', 'error');
        }
    }
    
    setupEventListeners() {
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.pauseUpdates();
            } else {
                this.resumeUpdates();
            }
        });
        
        document.addEventListener('keydown', (event) => {
            if (event.ctrlKey || event.metaKey) {
                switch (event.key) {
                    case 'r':
                        event.preventDefault();
                        this.refreshAll();
                        break;
                    case 'l':
                        event.preventDefault();
                        this.refreshLogs();
                        break;
                }
            }
        });
    }
    
    loadInitialData() {
        this.refreshLogs();
        this.loadConfiguration();
        
        if (this.socket && this.isConnected) {
            this.socket.emit('request_update');
        } else {
            this.fetchStatus();
        }
    }
    
    startPeriodicUpdates() {
        this.updateInterval = setInterval(() => {
            if (this.socket && this.isConnected) {
                this.socket.emit('request_update');
            } else {
                this.fetchStatus();
            }
        }, 10000);
        
        setInterval(() => this.refreshLogs(), 30000);
        setInterval(() => this.updateCharts(), 60000);
    }
    
    pauseUpdates() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }
    }
    
    resumeUpdates() {
        if (!this.updateInterval) {
            this.startPeriodicUpdates();
        }
    }
    
    updateConnectionStatus() {
        const statusEl = document.getElementById('connectionStatus');
        if (!statusEl) return;
        
        if (this.isConnected) {
            statusEl.className = 'connection-status connected';
            statusEl.innerHTML = '<i class="fas fa-circle"></i> Connected';
        } else {
            statusEl.className = 'connection-status disconnected';
            statusEl.innerHTML = '<i class="fas fa-circle"></i> Disconnected';
        }
    }
    
    updateDashboard(data) {
        try {
            this.updateSystemMetrics(data);
            this.updatePipelineCards(data);
            this.updateControllerStatus(data);
            this.updateAlerts(data);
            this.updateCharts();
            
            const updateTimeEl = document.getElementById('updateTime');
            if (updateTimeEl) {
                updateTimeEl.textContent = new Date().toLocaleTimeString();
            }
            
        } catch (error) {
            console.error('Error updating dashboard:', error);
            this.showNotification('Error updating dashboard display', 'error');
        }
    }
    
    updateSystemMetrics(data) {
        const health = data.system_health || {};
        const healthEl = document.getElementById('systemHealth');
        if (healthEl) {
            const healthStatus = health.status || 'unknown';
            const statusIcon = this.getHealthIcon(healthStatus);
            healthEl.innerHTML = `${statusIcon} ${healthStatus.toUpperCase()}`;
        }
        
        const pipelines = data.pipelines || {};
        const activePipelines = Object.values(pipelines).filter(p => p.enabled).length;
        const activePipelinesEl = document.getElementById('activePipelines');
        if (activePipelinesEl) {
            activePipelinesEl.textContent = activePipelines;
        }
        
        const alerts = data.active_alerts || [];
        const activeAlertsEl = document.getElementById('activeAlerts');
        if (activeAlertsEl) {
            activeAlertsEl.textContent = alerts.length;
        }
        
        const controller = data.controller || {};
        const currentCycleEl = document.getElementById('currentCycle');
        if (currentCycleEl) {
            currentCycleEl.textContent = controller.current_cycle || '--';
        }
    }
    
    getHealthIcon(status) {
        const icons = {
            'healthy': '<span class="status-indicator status-healthy"></span>',
            'warning': '<span class="status-indicator status-warning"></span>',
            'critical': '<span class="status-indicator status-critical"></span>',
            'unknown': '<span class="status-indicator status-unknown"></span>'
        };
        return icons[status] || icons['unknown'];
    }
    
    updatePipelineCards(data) {
        const pipelines = data.pipelines || {};
        const container = document.getElementById('pipelineCards');
        if (!container) return;
        
        container.innerHTML = '';
        
        Object.entries(pipelines).forEach(([name, pipeline]) => {
            const card = this.createPipelineCard(name, pipeline);
            container.appendChild(card);
        });
    }
    
    createPipelineCard(name, pipeline) {
        const card = document.createElement('div');
        card.className = 'col-md-6 col-lg-3 mb-3';
        
        const enabledClass = pipeline.enabled ? 'enabled' : 'disabled';
        const statusIcon = pipeline.enabled ? 'fa-check-circle text-success' : 'fa-times-circle text-danger';
        const modeColor = this.getModeColor(pipeline.mode);
        
        const summary = this.lastData?.pipeline_summaries?.[name] || {};
        const successRate = summary.total_runs > 0 ? 
            ((summary.total_processed || 0) / ((summary.total_processed || 0) + (summary.total_failed || 0)) * 100).toFixed(1) : 
            '--';
        
        card.innerHTML = `
            <div class="card pipeline-card ${enabledClass} fade-in">
                <div class="card-body text-center">
                    <h6 class="card-title">
                        <i class="fas ${statusIcon}"></i>
                        ${pipeline.display_name}
                    </h6>
                    <p class="card-text">
                        <small class="text-muted">Mode: <span class="badge ${modeColor}">${pipeline.mode}</span></small>
                    </p>
                    <div class="mb-2">
                        <small class="text-muted">
                            Success Rate: <strong>${successRate}%</strong><br>
                            Last 24h: ${summary.total_processed || 0} processed
                        </small>
                    </div>
                    <button class="btn btn-sm btn-primary btn-pipeline" 
                            onclick="dashboard.executePipeline('${name}')"
                            ${!pipeline.enabled ? 'disabled' : ''}>
                        <i class="fas fa-play"></i> Run
                    </button>
                </div>
            </div>
        `;
        
        return card;
    }
    
    getModeColor(mode) {
        const colors = {
            'disabled': 'bg-secondary',
            'manual': 'bg-warning',
            'scheduled': 'bg-success',
            'continuous': 'bg-primary',
            'batch': 'bg-info'
        };
        return colors[mode] || 'bg-secondary';
    }
    
    updateControllerStatus(data) {
        const controller = data.controller || {};
        const statusEl = document.getElementById('controllerStatus');
        if (!statusEl) return;
        
        if (controller.running) {
            if (controller.paused) {
                statusEl.className = 'badge bg-warning';
                statusEl.innerHTML = '<i class="fas fa-pause"></i> Paused';
            } else {
                statusEl.className = 'badge bg-success';
                statusEl.innerHTML = '<i class="fas fa-play"></i> Running';
            }
        } else {
            statusEl.className = 'badge bg-secondary';
            statusEl.innerHTML = '<i class="fas fa-stop"></i> Stopped';
        }
    }
    
    updateAlerts(data) {
        const alerts = data.active_alerts || [];
        const container = document.getElementById('alertsContainer');
        if (!container) return;
        
        if (alerts.length === 0) {
            container.innerHTML = '<div class="text-muted text-center p-4"><i class="fas fa-check-circle fa-2x mb-2"></i><br>No active alerts</div>';
            return;
        }
        
        container.innerHTML = '';
        
        const sortedAlerts = alerts.sort((a, b) => {
            const severityOrder = { 'critical': 0, 'error': 1, 'warning': 2, 'info': 3 };
            const severityDiff = severityOrder[a.level] - severityOrder[b.level];
            if (severityDiff !== 0) return severityDiff;
            return new Date(b.timestamp) - new Date(a.timestamp);
        });
        
        sortedAlerts.forEach(alert => {
            const alertEl = this.createAlertElement(alert);
            container.appendChild(alertEl);
        });
    }
    
    createAlertElement(alert) {
        const alertEl = document.createElement('div');
        alertEl.className = `alert-item alert-${alert.level} slide-in`;
        
        const timeAgo = this.getTimeAgo(new Date(alert.timestamp));
        const levelIcon = this.getAlertIcon(alert.level);
        
        alertEl.innerHTML = `
            <div class="d-flex justify-content-between align-items-start">
                <div class="flex-grow-1">
                    <div class="d-flex align-items-center mb-1">
                        ${levelIcon}
                        <strong class="me-2">${alert.source}</strong>
                        <span class="badge bg-${this.getAlertBadgeColor(alert.level)} badge-sm">
                            ${alert.level.toUpperCase()}
                        </span>
                    </div>
                    <div class="mb-1">${alert.message}</div>
                    <small class="text-muted">
                        <i class="fas fa-clock"></i> ${timeAgo}
                    </small>
                </div>
            </div>
        `;
        
        return alertEl;
    }
    
    getAlertIcon(level) {
        const icons = {
            'critical': '<i class="fas fa-exclamation-triangle text-danger"></i>',
            'error': '<i class="fas fa-exclamation-circle text-warning"></i>',
            'warning': '<i class="fas fa-exclamation text-warning"></i>',
            'info': '<i class="fas fa-info-circle text-info"></i>'
        };
        return icons[level] || icons['info'];
    }
    
    getAlertBadgeColor(level) {
        const colors = {
            'critical': 'danger',
            'error': 'warning',
            'warning': 'warning',
            'info': 'info'
        };
        return colors[level] || 'secondary';
    }
    
    getTimeAgo(date) {
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);
        
        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
        return `${diffDays}d ago`;
    }
    
    updateCharts() {
        this.updateSystemResourcesChart();
        this.updatePipelinePerformanceChart();
    }
    
    async updateSystemResourcesChart() {
        try {
            const response = await fetch('/api/metrics/chart/system_resources');
            const chartData = await response.json();
            
            if (!chartData.error) {
                const layout = {
                    ...chartData.layout,
                    paper_bgcolor: 'rgba(0,0,0,0)',
                    plot_bgcolor: 'rgba(0,0,0,0)',
                    font: { family: 'Segoe UI, sans-serif' }
                };
                
                Plotly.newPlot('systemResourcesChart', chartData.data, layout, {
                    responsive: true,
                    displayModeBar: false
                });
            }
        } catch (error) {
            console.error('Error loading system resources chart:', error);
        }
    }
    
    async updatePipelinePerformanceChart() {
        try {
            const response = await fetch('/api/metrics/chart/pipeline_performance');
            const chartData = await response.json();
            
            if (!chartData.error) {
                const layout = {
                    ...chartData.layout,
                    paper_bgcolor: 'rgba(0,0,0,0)',
                    plot_bgcolor: 'rgba(0,0,0,0)',
                    font: { family: 'Segoe UI, sans-serif' }
                };
                
                Plotly.newPlot('pipelinePerformanceChart', chartData.data, layout, {
                    responsive: true,
                    displayModeBar: false
                });
            }
        } catch (error) {
            console.error('Error loading pipeline performance chart:', error);
        }
    }
    
    async fetchStatus() {
        try {
            const response = await fetch('/api/status');
            const data = await response.json();
            this.lastData = data;
            this.updateDashboard(data);
        } catch (error) {
            console.error('Error fetching status:', error);
            this.showNotification('Failed to fetch system status', 'error');
        }
    }
    
    async executePipeline(pipelineName) {
        this.showLoading(`Executing ${pipelineName} pipeline...`);
        
        try {
            const response = await fetch(`/api/pipeline/${pipelineName}/execute`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            
            const data = await response.json();
            this.hideLoading();
            
            if (data.success) {
                this.showNotification(`${pipelineName} pipeline executed successfully`, 'success');
                this.requestUpdate();
            } else {
                this.showNotification(`Failed to execute ${pipelineName}: ${data.message}`, 'error');
            }
        } catch (error) {
            this.hideLoading();
            this.showNotification(`Error executing ${pipelineName}: ${error.message}`, 'error');
        }
    }
    
    async controlController(action) {
        this.showLoading(`${action}ing controller...`);
        
        try {
            const response = await fetch(`/api/controller/${action}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            
            const data = await response.json();
            this.hideLoading();
            
            if (data.success) {
                this.showNotification(`Controller ${action}ed successfully`, 'success');
                this.requestUpdate();
            } else {
                this.showNotification(`Failed to ${action} controller: ${data.message}`, 'error');
            }
        } catch (error) {
            this.hideLoading();
            this.showNotification(`Error ${action}ing controller: ${error.message}`, 'error');
        }
    }
    
    async refreshLogs() {
        try {
            const response = await fetch('/api/logs');
            const data = await response.json();
            
            const container = document.getElementById('logsContainer');
            if (container) {
                if (data.logs && data.logs.length > 0) {
                    const formattedLogs = data.logs.map(line => {
                        return this.formatLogLine(line);
                    }).join('\n');
                    
                    container.innerHTML = formattedLogs;
                    container.scrollTop = container.scrollHeight;
                } else {
                    container.innerHTML = '<div class="text-muted">No logs available</div>';
                }
            }
        } catch (error) {
            console.error('Error loading logs:', error);
            const container = document.getElementById('logsContainer');
            if (container) {
                container.innerHTML = '<div class="text-danger">Error loading logs</div>';
            }
        }
    }
    
    formatLogLine(line) {
        if (line.includes('ERROR')) {
            return `<span style="color: #ff6b6b;">${line}</span>`;
        } else if (line.includes('WARNING')) {
            return `<span style="color: #feca57;">${line}</span>`;
        } else if (line.includes('INFO')) {
            return `<span style="color: #48dbfb;">${line}</span>`;
        } else if (line.includes('SUCCESS') || line.includes('✅')) {
            return `<span style="color: #1dd1a1;">${line}</span>`;
        }
        return line;
    }
    
    async loadConfiguration() {
        try {
            const response = await fetch('/api/config');
            const config = await response.json();
            this.configuration = config;
        } catch (error) {
            console.error('Error loading configuration:', error);
        }
    }
    
    showLoading(message = 'Processing...') {
        const spinner = document.getElementById('loadingSpinner');
        if (spinner) {
            spinner.style.display = 'block';
            const messageEl = spinner.querySelector('div:last-child');
            if (messageEl) {
                messageEl.textContent = message;
            }
        }
    }
    
    hideLoading() {
        const spinner = document.getElementById('loadingSpinner');
        if (spinner) {
            spinner.style.display = 'none';
        }
    }
    
    showNotification(message, type = 'info', duration = 5000) {
        const alertClass = type === 'success' ? 'alert-success' : 
                          type === 'error' ? 'alert-danger' : 
                          type === 'warning' ? 'alert-warning' : 'alert-info';
        
        const icon = type === 'success' ? 'fa-check-circle' : 
                    type === 'error' ? 'fa-exclamation-circle' : 
                    type === 'warning' ? 'fa-exclamation-triangle' : 'fa-info-circle';
        
        const alertHtml = `
            <div class="alert ${alertClass} alert-dismissible fade show position-fixed" 
                 style="top: 80px; right: 20px; z-index: 9999; min-width: 300px;" role="alert">
                <i class="fas ${icon} me-2"></i>
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', alertHtml);
        
        setTimeout(() => {
            const alert = document.querySelector('.alert:last-of-type');
            if (alert) {
                alert.remove();
            }
        }, duration);
    }
    
    requestUpdate() {
        if (this.socket && this.isConnected) {
            this.socket.emit('request_update');
        } else {
            this.fetchStatus();
        }
    }
    
    refreshAll() {
        this.showNotification('Refreshing dashboard...', 'info', 2000);
        this.requestUpdate();
        this.refreshLogs();
        this.updateCharts();
    }
}

// Global dashboard instance
let dashboard;

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('Initializing Tunisia Intelligence Dashboard');
    dashboard = new TunisiaIntelligenceDashboard();
});

// Global functions for HTML onclick handlers
function executePipeline(pipelineName) {
    if (dashboard) {
        dashboard.executePipeline(pipelineName);
    }
}

function controlController(action) {
    if (dashboard) {
        dashboard.controlController(action);
    }
}

function refreshLogs() {
    if (dashboard) {
        dashboard.refreshLogs();
    }
}
