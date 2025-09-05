/**
 * Reality Checker - Admin Dashboard JavaScript
 * Handles dashboard data loading, UI updates, and user interactions
 */

// Dashboard data management
let dashboardData = {};
let updateInterval;

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    loadDashboardData();
    startAutoRefresh();
    initializeKeyboardShortcuts();
});

/**
 * Load dashboard data from API
 */
async function loadDashboardData() {
    try {
        showLoading(true);
        hideError();

        console.log('🔍 Loading dashboard data...');

        // Fetch dashboard overview
        console.log('📊 Fetching dashboard overview...');
        const overviewResponse = await fetch('/api/dashboard/overview', {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            credentials: 'same-origin'
        });
        
        console.log('📊 Overview response status:', overviewResponse.status);
        
        if (!overviewResponse.ok) {
            const errorText = await overviewResponse.text();
            console.error('📊 Overview error response:', errorText);
            throw new Error(`Dashboard API Error ${overviewResponse.status}: ${errorText}`);
        }
        const overview = await overviewResponse.json();
        console.log('📊 Overview data:', overview);

        // Fetch health data
        console.log('🏥 Fetching health data...');
        const healthResponse = await fetch('/health/detailed', {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            credentials: 'same-origin'
        });
        
        console.log('🏥 Health response status:', healthResponse.status);
        const health = healthResponse.ok ? await healthResponse.json() : null;
        if (health) {
            console.log('🏥 Health data:', health);
        }

        // Fetch real-time metrics
        console.log('📈 Fetching metrics data...');
        const metricsResponse = await fetch('/api/metrics/realtime', {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            credentials: 'same-origin'
        });
        
        console.log('📈 Metrics response status:', metricsResponse.status);
        const metrics = metricsResponse.ok ? await metricsResponse.json() : null;
        if (metrics) {
            console.log('📈 Metrics data:', metrics);
        }

        // Fetch analytics trends for new sections
        console.log('📊 Fetching analytics trends...');
        const trendsResponse = await fetch('/api/analytics/trends', {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            credentials: 'same-origin'
        });
        
        console.log('📊 Trends response status:', trendsResponse.status);
        const trends = trendsResponse.ok ? await trendsResponse.json() : null;
        if (trends) {
            console.log('📊 Trends data:', trends);
        }

        // Fetch source breakdown
        console.log('📱 Fetching source breakdown...');
        const sourceResponse = await fetch('/api/analytics/source-breakdown', {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            credentials: 'same-origin'
        });
        
        console.log('📱 Source response status:', sourceResponse.status);
        const sourceData = sourceResponse.ok ? await sourceResponse.json() : null;
        if (sourceData) {
            console.log('📱 Source data:', sourceData);
        }

        // Update dashboard with fetched data
        console.log('🔄 Updating dashboard display...');
        dashboardData = { overview, health, metrics, trends, sourceData };
        updateDashboardUI();
        showLiveIndicator();
        
        console.log('✅ Dashboard loaded successfully!');
        
    } catch (error) {
        console.error('❌ Failed to load dashboard data:', error);
        console.error('❌ Error details:', {
            name: error.name,
            message: error.message,
            stack: error.stack
        });
        handleFetchError(error);
    } finally {
        showLoading(false);
    }
}

/**
 * Update UI elements with dashboard data
 */
function updateDashboardUI() {
    const { overview, health, metrics, trends, sourceData } = dashboardData;
    
    // Update quick stats from overview
    updateElement('systemStatus', health?.status || 'Unknown');
    updateElement('systemUptime', '99.9%');
    updateElement('totalRequests', formatNumber(overview?.total_requests || 0));
    updateElement('requestsToday', formatNumber(overview?.requests_today || 0));
    updateElement('errorRate', `${(overview?.error_rate || 0).toFixed(1)}%`);
    updateElement('successRate', `${(overview?.success_rate || 0).toFixed(1)}%`);
    updateElement('activeUsers', formatNumber(overview?.active_users || 0));
    updateElement('peakHour', overview?.peak_hour || '--');

    // Update performance metrics from overview and metrics
    updateElement('avgResponseTime', `${(overview?.avg_response_time || 0).toFixed(0)}ms`);
    updateElement('throughput', `${metrics?.requests_per_minute || 0}/min`);
    updateElement('cpuUsage', `${(metrics?.cpu_usage || 0).toFixed(1)}%`);
    updateElement('memoryUsage', `${(metrics?.memory_usage || 0).toFixed(1)}%`);

    // Update performance metrics section (if these elements exist)
    updateElement('metricTotalRequests', formatNumber(overview?.total_requests || 0));
    updateElement('metricRequestsToday', formatNumber(overview?.requests_today || 0));
    updateElement('metricErrorRate', `${(overview?.error_rate || 0).toFixed(2)}%`);
    updateElement('metricActiveUsers', formatNumber(overview?.active_users || 0));
    updateElement('metricResponseTime', `${(overview?.avg_response_time || 0).toFixed(1)}s`);
    updateElement('metricSuccessRate', `${(overview?.success_rate || 0).toFixed(1)}%`);
    updateElement('metricPeakHour', overview?.peak_hour || '--');

    // Update live metrics (if these elements exist)
    if (metrics) {
        updateElement('liveActiveRequests', metrics.active_requests || 0);
        updateElement('liveRequestsPerMin', metrics.requests_per_minute || 0);
        updateElement('liveMemoryUsage', `${(metrics.memory_usage || 0).toFixed(1)}%`);
        updateElement('liveCpuUsage', `${(metrics.cpu_usage || 0).toFixed(1)}%`);
    }

    // Update system health indicators
    updateSystemHealth();
    
    // Update message classifications
    updateMessageClassifications();
    
    // Update user engagement
    updateUserEngagement();
    
    // Update traffic sources
    updateTrafficSources();
    
    // Update other services (performance alerts)
    updateOtherServices();
    
    // Update alerts
    updateAlerts();

    // Update timestamp
    updateElement('updateTime', new Date().toLocaleTimeString());
}

/**
 * Update system health indicators
 */
function updateSystemHealth() {
    const { health } = dashboardData;
    if (!health) return;

    const overallStatus = health.status || 'unknown';
    
    // Update overall health status
    updateElement('overallHealthStatus', capitalizeFirst(overallStatus));
    updateElement('lastHealthCheck', formatTime(new Date()));

    // Update health indicator color
    const indicatorElement = document.getElementById('overallHealthIndicator') || 
                            document.getElementById('overallHealth');
    if (indicatorElement) {
        indicatorElement.className = 'health-indicator';
        if (overallStatus === 'healthy') {
            indicatorElement.style.background = '#4caf50';
        } else if (overallStatus === 'degraded') {
            indicatorElement.style.background = '#ff9800';
        } else {
            indicatorElement.style.background = '#f44336';
        }
    }

    // Update service list if available
    if (health.services) {
        updateServiceList(health.services);
    }
}

/**
 * Update service list
 */
function updateServiceList(services) {
    const serviceList = document.getElementById('serviceList');
    if (!serviceList) return;

    const serviceNames = {
        'openai': 'OpenAI GPT-4',
        'twilio': 'Twilio WhatsApp',
        'database': 'Database',
        'webhook': 'Webhook Endpoint'
    };

    let html = '';
    for (const [key, name] of Object.entries(serviceNames)) {
        const service = services[key] || {};
        const status = service.status || 'unknown';
        const responseTime = service.response_time_ms || 0;

        let statusColor = '#4caf50';
        if (status === 'degraded' || status === 'warning') statusColor = '#ff9800';
        if (status === 'unhealthy' || status === 'error') statusColor = '#f44336';

        html += `
            <div class="service-item">
                <div class="service-name">${name}</div>
                <div class="service-status">
                    <div class="health-indicator" style="background: ${statusColor};"></div>
                    <span>${capitalizeFirst(status)}</span>
                    <span style="margin-left: 8px; font-size: 0.75rem; color: rgba(255,255,255,0.5);">${responseTime}ms</span>
                </div>
            </div>
        `;
    }
    serviceList.innerHTML = html;
}

/**
 * Update message classifications section
 */
function updateMessageClassifications() {
    const { trends, sourceData } = dashboardData;
    if (!trends || !trends.classifications) return;

    const classifications = trends.classifications;
    
    // Update total counts
    updateElement('legitCount', classifications.Legitimate || 0);
    updateElement('suspiciousCount', classifications.Suspicious || 0);
    updateElement('scamCount', classifications['Likely Scam'] || 0);

    // For now, we'll estimate breakdown by source ratio
    // In a full implementation, you'd get this data from a dedicated API
    if (sourceData && sourceData.source_percentages) {
        const whatsappRatio = sourceData.source_percentages.whatsapp / 100;
        const webRatio = sourceData.source_percentages.web / 100;
        
        updateElement('legitWhatsApp', Math.round((classifications.Legitimate || 0) * whatsappRatio));
        updateElement('legitWeb', Math.round((classifications.Legitimate || 0) * webRatio));
        updateElement('suspiciousWhatsApp', Math.round((classifications.Suspicious || 0) * whatsappRatio));
        updateElement('suspiciousWeb', Math.round((classifications.Suspicious || 0) * webRatio));
        updateElement('scamWhatsApp', Math.round((classifications['Likely Scam'] || 0) * whatsappRatio));
        updateElement('scamWeb', Math.round((classifications['Likely Scam'] || 0) * webRatio));
    }
}

/**
 * Update user engagement section
 */
function updateUserEngagement() {
    const { trends } = dashboardData;
    if (!trends || !trends.user_engagement) return;

    const engagement = trends.user_engagement;
    updateElement('dailyActiveUsers', engagement.daily_active_users || 0);
    updateElement('avgSessionTime', `${(engagement.avg_session_time || 0).toFixed(1)}m`);
    updateElement('returnRate', `${(engagement.return_rate || 0).toFixed(1)}%`);
    updateElement('newUsers', engagement.new_users || 0);
}

/**
 * Update traffic sources section
 */
function updateTrafficSources() {
    const { sourceData } = dashboardData;
    if (!sourceData) return;

    // WhatsApp data
    updateElement('whatsappPercentage', `${(sourceData.source_percentages?.whatsapp || 0).toFixed(1)}%`);
    updateElement('whatsappCount', sourceData.source_counts?.whatsapp || 0);
    updateElement('whatsappResponseTime', `${(sourceData.response_times?.whatsapp || 0).toFixed(1)}s`);
    updateElement('whatsappSuccessRate', `${(sourceData.success_rates?.whatsapp || 0).toFixed(1)}%`);

    // Web data
    updateElement('webPercentage', `${(sourceData.source_percentages?.web || 0).toFixed(1)}%`);
    updateElement('webCount', sourceData.source_counts?.web || 0);
    updateElement('webResponseTime', `${(sourceData.response_times?.web || 0).toFixed(1)}s`);
    updateElement('webSuccessRate', `${(sourceData.success_rates?.web || 0).toFixed(1)}%`);
}

/**
 * Update other services (performance monitoring) section
 */
function updateOtherServices() {
    // Simulate performance monitoring data based on metrics
    const { metrics, health } = dashboardData;
    
    // Update alert counters (simulated based on current system status)
    let criticalCount = 0, warningCount = 0, infoCount = 0;
    
    if (health) {
        const services = health.services || {};
        Object.values(services).forEach(service => {
            if (service.status === 'unhealthy' || service.status === 'error') criticalCount++;
            else if (service.status === 'degraded' || service.status === 'warning') warningCount++;
            else infoCount++;
        });
    }
    
    // Add performance-based alerts
    if (metrics) {
        if (metrics.cpu_usage > 80) criticalCount++;
        else if (metrics.cpu_usage > 60) warningCount++;
        
        if (metrics.memory_usage > 80) criticalCount++;
        else if (metrics.memory_usage > 60) warningCount++;
    }
    
    updateElement('criticalAlerts', criticalCount);
    updateElement('warningAlerts', warningCount);
    updateElement('infoAlerts', infoCount);

    // Update service monitoring status
    updateServiceMonitoringStatus('redisStatus', 'Normal');
    updateServiceMonitoringStatus('databaseStatus', health?.services?.database?.status === 'healthy' ? 'Normal' : 'Warning');
    updateServiceMonitoringStatus('taskStatus', 'Normal');
    updateServiceMonitoringStatus('circuitStatus', 'Closed');

    // Add recent performance alerts
    updateRecentPerformanceAlerts();
}

/**
 * Update service monitoring status with proper styling
 */
function updateServiceMonitoringStatus(elementId, status) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    element.textContent = status;
    element.className = 'monitor-status';
    
    if (status === 'Warning' || status === 'Degraded') {
        element.classList.add('warning');
    } else if (status === 'Error' || status === 'Critical') {
        element.classList.add('error');
    }
}

/**
 * Update recent performance alerts
 */
function updateRecentPerformanceAlerts() {
    const alertsList = document.getElementById('recentPerformanceAlerts');
    if (!alertsList) return;

    // Simulate recent alerts based on current system state
    const { metrics, health } = dashboardData;
    let alerts = [];

    if (metrics) {
        if (metrics.cpu_usage > 80) {
            alerts.push({
                type: 'critical',
                title: 'High CPU Usage',
                message: `CPU usage at ${metrics.cpu_usage.toFixed(1)}%`,
                time: '2 min ago'
            });
        }
        
        if (metrics.memory_usage > 80) {
            alerts.push({
                type: 'critical',
                title: 'High Memory Usage',
                message: `Memory usage at ${metrics.memory_usage.toFixed(1)}%`,
                time: '3 min ago'
            });
        }
        
        if (metrics.error_rate > 10) {
            alerts.push({
                type: 'warning',
                title: 'Elevated Error Rate',
                message: `Error rate at ${metrics.error_rate.toFixed(1)}%`,
                time: '5 min ago'
            });
        }
    }

    // Add a few sample alerts if no real alerts
    if (alerts.length === 0) {
        alerts.push({
            type: 'info',
            title: 'System Status',
            message: 'All systems operating normally',
            time: '1 min ago'
        });
    }

    const alertsHtml = alerts.map(alert => `
        <div class="performance-alert-item">
            <span class="material-icons performance-alert-icon ${alert.type}">
                ${getAlertIcon(alert.type)}
            </span>
            <div class="performance-alert-content">
                <div class="performance-alert-title">${escapeHtml(alert.title)}</div>
                <div class="performance-alert-message">${escapeHtml(alert.message)}</div>
            </div>
            <div class="performance-alert-time">${alert.time}</div>
        </div>
    `).join('');
    
    alertsList.innerHTML = alertsHtml;
}

/**
 * Update alerts section
 */
function updateAlerts() {
    // For now, keep existing static alerts since we need to fetch from health API alerts endpoint
    // TODO: Integrate with /health/alerts endpoint
    console.log('📢 Alerts update (using static data for now)');
}

/**
 * Utility functions
 */
function updateElement(id, value) {
    const element = document.getElementById(id);
    if (element) {
        element.textContent = value;
    }
}

function formatNumber(num) {
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
}

function formatTime(timestamp) {
    if (!timestamp) return '--';
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now - date;
    
    if (diff < 60000) return 'Just now';
    if (diff < 3600000) return `${Math.floor(diff / 60000)} minutes ago`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)} hours ago`;
    return date.toLocaleDateString();
}

function capitalizeFirst(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
}

function getAlertIcon(type) {
    switch (type) {
        case 'error': return 'error';
        case 'warning': return 'warning';
        case 'success': return 'check_circle';
        default: return 'info';
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * UI State Management
 */
function showLoading(show) {
    const loadingIndicator = document.getElementById('loadingIndicator');
    const liveIndicator = document.getElementById('liveIndicator');
    
    if (show) {
        loadingIndicator.style.display = 'flex';
        liveIndicator.style.display = 'none';
    } else {
        loadingIndicator.style.display = 'none';
    }
}

function showLiveIndicator() {
    const liveIndicator = document.getElementById('liveIndicator');
    liveIndicator.style.display = 'flex';
}

function showError() {
    const errorMessage = document.getElementById('errorMessage');
    errorMessage.style.display = 'flex';
}

function hideError() {
    const errorMessage = document.getElementById('errorMessage');
    errorMessage.style.display = 'none';
}

/**
 * Auto-refresh functionality
 */
function startAutoRefresh() {
    updateInterval = setInterval(loadDashboardData, 30000); // Refresh every 30 seconds
}

function stopAutoRefresh() {
    if (updateInterval) {
        clearInterval(updateInterval);
    }
}

/**
 * Keyboard shortcuts
 */
function initializeKeyboardShortcuts() {
    document.addEventListener('keydown', function(event) {
        if (event.ctrlKey || event.metaKey) {
            switch(event.key) {
                case 'r':
                    event.preventDefault();
                    loadDashboardData();
                    break;
                case 'p':
                    event.preventDefault();
                    if (updateInterval) {
                        stopAutoRefresh();
                        console.log('Auto-refresh paused');
                    } else {
                        startAutoRefresh();
                        console.log('Auto-refresh resumed');
                    }
                    break;
            }
        }
        
        // Escape key to dismiss errors
        if (event.key === 'Escape') {
            hideError();
        }
    });
}

/**
 * Cleanup on page unload
 */
window.addEventListener('beforeunload', function() {
    stopAutoRefresh();
});

/**
 * Accessibility enhancements
 */
function announceUpdate(message) {
    const announcement = document.createElement('div');
    announcement.setAttribute('aria-live', 'polite');
    announcement.setAttribute('aria-atomic', 'true');
    announcement.className = 'sr-only';
    announcement.textContent = message;
    document.body.appendChild(announcement);
    
    setTimeout(() => {
        document.body.removeChild(announcement);
    }, 1000);
}

/**
 * Error handling for fetch requests
 */
function handleFetchError(error) {
    console.error('Dashboard fetch error:', error);
    
    // Provide user-friendly error messages
    let userMessage = 'Unable to load dashboard data. ';
    
    if (!navigator.onLine) {
        userMessage += 'Please check your internet connection.';
    } else if (error.name === 'TypeError') {
        userMessage += 'Server is not responding.';
    } else {
        userMessage += 'Please try again later.';
    }
    
    announceUpdate(userMessage);
    showError();
}

// Export functions for testing (if in Node.js environment)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        formatNumber,
        formatTime,
        escapeHtml,
        getAlertIcon
    };
}