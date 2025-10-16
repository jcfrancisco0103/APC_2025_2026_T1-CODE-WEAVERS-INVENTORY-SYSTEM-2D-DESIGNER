/**
 * Admin Security Client-Side Validation
 * Provides additional security checks for admin dashboard access
 */

// Check if user is trying to access admin dashboard
function checkAdminAccess() {
    const currentPath = window.location.pathname;
    const adminPaths = ['/admin-dashboard', '/admin/', '/view-customer', '/add-product'];
    
    // Check if current path is an admin path
    const isAdminPath = adminPaths.some(path => currentPath.includes(path));
    
    if (isAdminPath) {
        // Make AJAX request to verify admin status
        fetch('/verify-admin-status/', {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCookie('csrftoken')
            },
            credentials: 'same-origin'
        })
        .then(response => response.json())
        .then(data => {
            if (!data.is_admin) {
                // User is not admin, show warning and redirect
                showAccessDeniedModal();
                setTimeout(() => {
                    window.location.href = '/adminlogin';
                }, 3000);
            }
        })
        .catch(error => {
            console.error('Admin verification failed:', error);
            // On error, redirect to login for safety
            window.location.href = '/adminlogin';
        });
    }
}

// Show access denied modal
function showAccessDeniedModal() {
    // Create modal HTML
    const modalHTML = `
        <div id="accessDeniedModal" style="
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0, 0, 0, 0.8);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 10000;
        ">
            <div style="
                background: white;
                padding: 30px;
                border-radius: 10px;
                text-align: center;
                max-width: 400px;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
            ">
                <div style="color: #dc3545; font-size: 48px; margin-bottom: 20px;">
                    ⚠️
                </div>
                <h2 style="color: #dc3545; margin-bottom: 15px;">Access Denied</h2>
                <p style="margin-bottom: 20px; color: #666;">
                    You do not have administrator privileges to access this page.
                    You will be redirected to the login page.
                </p>
                <div style="
                    background: #f8f9fa;
                    padding: 10px;
                    border-radius: 5px;
                    font-size: 14px;
                    color: #666;
                ">
                    Redirecting in <span id="countdown">3</span> seconds...
                </div>
            </div>
        </div>
    `;
    
    // Add modal to page
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    
    // Start countdown
    let countdown = 3;
    const countdownElement = document.getElementById('countdown');
    const countdownInterval = setInterval(() => {
        countdown--;
        if (countdownElement) {
            countdownElement.textContent = countdown;
        }
        if (countdown <= 0) {
            clearInterval(countdownInterval);
        }
    }, 1000);
}

// Get CSRF token from cookies
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Monitor for navigation to admin pages
function monitorAdminAccess() {
    // Check on page load
    checkAdminAccess();
    
    // Monitor for programmatic navigation
    const originalPushState = history.pushState;
    const originalReplaceState = history.replaceState;
    
    history.pushState = function() {
        originalPushState.apply(history, arguments);
        setTimeout(checkAdminAccess, 100);
    };
    
    history.replaceState = function() {
        originalReplaceState.apply(history, arguments);
        setTimeout(checkAdminAccess, 100);
    };
    
    // Monitor for back/forward navigation
    window.addEventListener('popstate', () => {
        setTimeout(checkAdminAccess, 100);
    });
}

// Initialize security monitoring when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    monitorAdminAccess();
});

// Also check immediately if DOM is already loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', monitorAdminAccess);
} else {
    monitorAdminAccess();
}