/**
 * Agent Platform Admin Panel JavaScript
 * Common functionality for the admin interface
 */

// Global utilities
window.AdminUtils = {
    // Show toast notifications
    showToast: function(message, type = 'success', duration = 5000) {
        const toastContainer = document.getElementById('toast-container') || this.createToastContainer();
        const toast = this.createToast(message, type);
        toastContainer.appendChild(toast);
        
        // Trigger animation
        setTimeout(() => toast.classList.add('show'), 100);
        
        // Auto remove
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toastContainer.removeChild(toast), 300);
        }, duration);
    },
    
    createToastContainer: function() {
        const container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'position-fixed top-0 end-0 p-3';
        container.style.zIndex = '9999';
        document.body.appendChild(container);
        return container;
    },
    
    createToast: function(message, type) {
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-bg-${type} border-0`;
        toast.setAttribute('role', 'alert');
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" onclick="this.parentElement.parentElement.remove()"></button>
            </div>
        `;
        return toast;
    },
    
    // Loading states
    showLoading: function(element, text = 'Loading...') {
        const originalContent = element.innerHTML;
        element.setAttribute('data-original-content', originalContent);
        element.innerHTML = `<i class="fas fa-spinner fa-spin me-2"></i>${text}`;
        element.disabled = true;
    },
    
    hideLoading: function(element) {
        const originalContent = element.getAttribute('data-original-content');
        if (originalContent) {
            element.innerHTML = originalContent;
            element.removeAttribute('data-original-content');
        }
        element.disabled = false;
    },
    
    // API helpers
    apiRequest: async function(url, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
            },
        };
        
        const config = { ...defaultOptions, ...options };
        
        try {
            const response = await fetch(url, config);
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.message || 'Request failed');
            }
            
            return data;
        } catch (error) {
            console.error('API Request failed:', error);
            throw error;
        }
    },
    
    // Form helpers
    serializeForm: function(form) {
        const formData = new FormData(form);
        const data = {};
        for (let [key, value] of formData.entries()) {
            data[key] = value;
        }
        return data;
    },
    
    // Confirmation dialog
    confirm: function(message, title = 'Confirm Action') {
        return new Promise((resolve) => {
            const modal = this.createConfirmModal(title, message, resolve);
            document.body.appendChild(modal);
            const bsModal = new bootstrap.Modal(modal);
            bsModal.show();
        });
    },
    
    createConfirmModal: function(title, message, callback) {
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.innerHTML = `
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">${title}</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <p>${message}</p>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal" onclick="this.confirmCallback(false)">Cancel</button>
                        <button type="button" class="btn btn-primary" data-bs-dismiss="modal" onclick="this.confirmCallback(true)">Confirm</button>
                    </div>
                </div>
            </div>
        `;
        
        modal.confirmCallback = callback;
        
        modal.addEventListener('hidden.bs.modal', function() {
            document.body.removeChild(this);
        });
        
        return modal;
    },
    
    // Format utilities
    formatBytes: function(bytes, decimals = 2) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const dm = decimals < 0 ? 0 : decimals;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
        
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
    },
    
    formatDate: function(timestamp) {
        const date = new Date(timestamp * 1000);
        return date.toLocaleString();
    },
    
    // Copy to clipboard
    copyToClipboard: async function(text, successMessage = 'Copied to clipboard!') {
        try {
            await navigator.clipboard.writeText(text);
            this.showToast(successMessage, 'success');
        } catch (err) {
            console.error('Failed to copy text: ', err);
            this.showToast('Failed to copy text', 'danger');
        }
    },
    
    // Search and filter utilities
    filterTable: function(tableId, searchValue) {
        const table = document.getElementById(tableId);
        const rows = table.getElementsByTagName('tbody')[0].getElementsByTagName('tr');
        
        for (let i = 0; i < rows.length; i++) {
            const row = rows[i];
            const text = row.textContent || row.innerText;
            
            if (text.toLowerCase().indexOf(searchValue.toLowerCase()) > -1) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        }
    },
    
    // Auto-refresh functionality
    autoRefresh: function(callback, interval = 30000) {
        let refreshInterval;
        
        const start = () => {
            refreshInterval = setInterval(callback, interval);
        };
        
        const stop = () => {
            if (refreshInterval) {
                clearInterval(refreshInterval);
                refreshInterval = null;
            }
        };
        
        const toggle = () => {
            if (refreshInterval) {
                stop();
                return false;
            } else {
                start();
                return true;
            }
        };
        
        // Stop refresh when user becomes inactive
        let inactiveTimer;
        const resetInactiveTimer = () => {
            clearTimeout(inactiveTimer);
            inactiveTimer = setTimeout(stop, 300000); // 5 minutes
        };
        
        document.addEventListener('mousemove', resetInactiveTimer);
        document.addEventListener('keypress', resetInactiveTimer);
        
        return { start, stop, toggle };
    }
};

// Initialize common functionality
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Add copy functionality to code blocks
    document.querySelectorAll('code').forEach(function(codeBlock) {
        if (codeBlock.textContent.length > 10) {
            codeBlock.style.cursor = 'pointer';
            codeBlock.title = 'Click to copy';
            codeBlock.addEventListener('click', function() {
                AdminUtils.copyToClipboard(this.textContent);
            });
        }
    });
    
    // Add search functionality to tables
    const searchInputs = document.querySelectorAll('[data-table-search]');
    searchInputs.forEach(function(input) {
        const tableId = input.getAttribute('data-table-search');
        input.addEventListener('input', function() {
            AdminUtils.filterTable(tableId, this.value);
        });
    });
    
    // Auto-hide alerts after 5 seconds
    document.querySelectorAll('.alert:not(.alert-permanent)').forEach(function(alert) {
        setTimeout(function() {
            if (alert.parentNode) {
                alert.classList.remove('show');
                setTimeout(() => alert.remove(), 150);
            }
        }, 5000);
    });
    
    // Add loading states to forms
    document.querySelectorAll('form').forEach(function(form) {
        form.addEventListener('submit', function(e) {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn && !form.hasAttribute('data-no-loading')) {
                AdminUtils.showLoading(submitBtn, 'Processing...');
                
                // Re-enable button after 10 seconds as fallback
                setTimeout(() => {
                    AdminUtils.hideLoading(submitBtn);
                }, 10000);
            }
        });
    });
    
    // Add confirmation to dangerous actions
    document.querySelectorAll('[data-confirm]').forEach(function(element) {
        element.addEventListener('click', async function(e) {
            e.preventDefault();
            
            const message = this.getAttribute('data-confirm');
            const confirmed = await AdminUtils.confirm(message, 'Confirm Action');
            
            if (confirmed) {
                // If it's a form submission
                if (this.type === 'submit') {
                    this.form.submit();
                }
                // If it's a link
                else if (this.href) {
                    window.location.href = this.href;
                }
                // If it has a data-action
                else if (this.hasAttribute('data-action')) {
                    const action = this.getAttribute('data-action');
                    if (typeof window[action] === 'function') {
                        window[action](this);
                    }
                }
            }
        });
    });
});

// System health monitoring
window.HealthMonitor = {
    status: 'unknown',
    lastCheck: null,
    
    async check() {
        try {
            const response = await AdminUtils.apiRequest('/api/health');
            this.status = response.status;
            this.lastCheck = new Date();
            this.updateUI();
            return response;
        } catch (error) {
            this.status = 'unhealthy';
            this.lastCheck = new Date();
            this.updateUI();
            throw error;
        }
    },
    
    updateUI() {
        const indicators = document.querySelectorAll('[data-health-status]');
        indicators.forEach(indicator => {
            indicator.className = `badge ${this.status === 'healthy' ? 'bg-success' : 'bg-danger'}`;
            indicator.textContent = this.status === 'healthy' ? 'Healthy' : 'Unhealthy';
        });
        
        const timestamps = document.querySelectorAll('[data-health-timestamp]');
        timestamps.forEach(timestamp => {
            timestamp.textContent = this.lastCheck ? this.lastCheck.toLocaleTimeString() : 'Never';
        });
    },
    
    startMonitoring(interval = 60000) {
        // Initial check
        this.check();
        
        // Set up periodic checks
        return setInterval(() => {
            this.check().catch(error => {
                console.warn('Health check failed:', error);
            });
        }, interval);
    }
};

// Export for use in other scripts
window.Admin = {
    Utils: AdminUtils,
    HealthMonitor: HealthMonitor
};