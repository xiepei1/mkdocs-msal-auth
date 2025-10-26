// Google OAuth Integration for MkDocs

document.addEventListener('DOMContentLoaded', function () {
  // Check if user is authenticated
  checkAuth();
});

function checkAuth() {
  // Check if there's a token in localStorage
  const token = localStorage.getItem('mkdocs_google_auth_token');

  if (!token) {
    // If no token is found, redirect to login page if not already there
    if (!window.location.pathname.endsWith('/login/')) {
      redirectToLogin();
    }
  } else {
    // Verify token with the backend
    fetch('/auth/verify', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      }
    })
      .then(response => {
        if (!response.ok) {
          // Token is invalid or expired
          localStorage.removeItem('mkdocs_google_auth_token');
          redirectToLogin();
        }
      })
      .catch(error => {
        console.error('Authentication verification failed:', error);
        redirectToLogin();
      });
  }
}

function redirectToLogin() {
  // Save current URL to redirect back after login
  localStorage.setItem('mkdocs_auth_redirect', window.location.pathname);

  // Redirect to login page
  window.location.href = '/login/';
}

function loginWithGoogle() {
  // Redirect to Google OAuth endpoint
  window.location.href = '/auth/google';
}

function logout() {
  // Remove auth token and redirect to login
  localStorage.removeItem('mkdocs_google_auth_token');
  redirectToLogin();
}

// Expose functions for use in HTML
window.loginWithGoogle = loginWithGoogle;
window.logout = logout;