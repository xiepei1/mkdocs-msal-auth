# Login

<div class="login-container">
  <h2>Login Required</h2>
  <p>This documentation requires authentication. Please log in with your Google account.</p>

  <button class="md-button md-button--primary" onclick="loginWithGoogle()">
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" style="vertical-align: middle; margin-right: 8px;">
      <path fill="#EA4335" d="M12 5.04c2.17 0 4.1.89 5.51 2.31l4.15-4.09C19.26 1.03 15.89-.01 12 0 7.28.01 3.19 2.7.96 6.6l4.81 3.74C7.07 7.04 9.39 5.04 12 5.04z"></path>
      <path fill="#4285F4" d="M23.78 12.27c0-.79-.07-1.54-.19-2.27H12v4.51h6.67c-.29 1.48-1.14 2.73-2.43 3.58l4.77 3.71c2.78-2.55 4.37-6.32 4.37-10.73z"></path>
      <path fill="#FBBC05" d="M5.77 14.33c-.25-.76-.4-1.56-.4-2.39 0-.83.15-1.63.4-2.39L.96 5.81C.35 7.69 0 9.75 0 11.94s.35 4.25.96 6.13l4.81-3.74z"></path>
      <path fill="#34A853" d="M12 24c3.24 0 5.95-1.08 7.93-2.91l-4.77-3.71c-1.31.88-2.99 1.41-4.76 1.41-2.61 0-4.93-1.99-5.73-4.7l-4.81 3.74C1.19 21.3 5.28 24 12 24z"></path>
    </svg>
    Sign in with Google
  </button>
</div>

<style>
  .login-container {
    text-align: center;
    margin: 100px auto;
    padding: 20px;
    max-width: 400px;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  }

  .md-button--primary {
    display: inline-flex;
    align-items: center;
    padding: 10px 16px;
    border-radius: 4px;
    background-color: #fff;
    color: #757575;
    font-weight: 500;
    border: 1px solid #ddd;
    cursor: pointer;
    transition: background-color 0.3s, box-shadow 0.3s;
  }

  .md-button--primary:hover {
    box-shadow: 0 1px 3px rgba(0,0,0,0.2);
  }
</style>