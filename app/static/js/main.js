// Green Production ERP - Main JavaScript

// Toggle Sidebar on Mobile
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    sidebar.classList.toggle('open');
}

// Theme Toggle
function toggleTheme() {
    const body = document.body;
    const currentTheme = body.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    body.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
}

// Initialize Theme
function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.body.setAttribute('data-theme', savedTheme);
}

// API Helper
const api = {
    baseUrl: '/api',

    async request(method, endpoint, data = null, showLoadingIndicator = true) {
        // Show loading for write operations
        if (showLoadingIndicator && ['POST', 'PUT', 'DELETE'].includes(method)) {
            showLoading();
        }

        const options = {
            method,
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'same-origin'
        };

        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
        if (csrfToken) {
            options.headers['X-CSRFToken'] = csrfToken;
        }

        if (data) {
            options.body = JSON.stringify(data);
        }

        try {
            const response = await fetch(this.baseUrl + endpoint, options);

            // Check if response is JSON
            const contentType = response.headers.get('content-type');
            if (!contentType || !contentType.includes('application/json')) {
                // Server returned non-JSON (probably HTML error page)
                const text = await response.text();
                console.error('Non-JSON response:', text);
                throw new Error(`Server returned ${response.status} error. Please check the console for details.`);
            }

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.message || 'Request failed');
            }

            return result;
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        } finally {
            // Hide loading after request completes
            if (showLoadingIndicator && ['POST', 'PUT', 'DELETE'].includes(method)) {
                hideLoading();
            }
        }
    },

    get(endpoint) {
        return this.request('GET', endpoint);
    },

    post(endpoint, data, showLoadingIndicator = true) {
        return this.request('POST', endpoint, data, showLoadingIndicator);
    },

    put(endpoint, data, showLoadingIndicator = true) {
        return this.request('PUT', endpoint, data, showLoadingIndicator);
    },

    delete(endpoint, showLoadingIndicator = true) {
        return this.request('DELETE', endpoint, null, showLoadingIndicator);
    }
};

// Loading Functions
function showLoading(message = 'Memproses...') {
    const overlay = document.getElementById('loadingOverlay');
    const textEl = overlay?.querySelector('.loading-text');
    if (textEl) textEl.textContent = message;
    if (overlay) overlay.classList.add('active');
}

function hideLoading() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) overlay.classList.remove('active');
}

// Toast Notifications
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
        <span>${message}</span>
    `;

    document.body.appendChild(toast);

    setTimeout(() => toast.classList.add('show'), 100);
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Modal Functions
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('active');
        document.body.style.overflow = '';
    }
}

// Close modal on backdrop click
document.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal-backdrop')) {
        e.target.classList.remove('active');
        document.body.style.overflow = '';
    }
});

// Form Helpers
function serializeForm(form) {
    const formData = new FormData(form);
    const data = {};
    formData.forEach((value, key) => {
        data[key] = value;
    });
    return data;
}

// Confirm Dialog
function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

// Format Date
function formatDate(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString('id-ID', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

// Format DateTime
function formatDateTime(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString('id-ID', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Debounce
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initTheme();

    // Close sidebar on mobile when clicking outside
    document.addEventListener('click', (e) => {
        const sidebar = document.getElementById('sidebar');
        const menuToggle = document.querySelector('.menu-toggle');

        if (sidebar && sidebar.classList.contains('open')) {
            if (!sidebar.contains(e.target) && !menuToggle.contains(e.target)) {
                sidebar.classList.remove('open');
            }
        }
    });

    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 300);
        }, 5000);
    });
});

// Barcode Scanner (using QuaggaJS)
const BarcodeScanner = {
    init(elementId, onDetected) {
        if (typeof Quagga === 'undefined') {
            console.error('QuaggaJS not loaded');
            return;
        }

        Quagga.init({
            inputStream: {
                name: "Live",
                type: "LiveStream",
                target: document.getElementById(elementId),
                constraints: {
                    facingMode: "environment"
                }
            },
            decoder: {
                readers: ["code_128_reader", "ean_reader", "ean_8_reader"]
            }
        }, (err) => {
            if (err) {
                console.error(err);
                return;
            }
            Quagga.start();
        });

        Quagga.onDetected((result) => {
            const code = result.codeResult.code;
            onDetected(code);
            Quagga.stop();
        });
    },

    stop() {
        if (typeof Quagga !== 'undefined') {
            Quagga.stop();
        }
    }
};
