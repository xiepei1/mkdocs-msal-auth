// Show the reason the auth callback recorded in ?error=<reason>.
// The login page is static, so the reason is rendered here in the browser.
(function () {
  var messages = {
    no_code: 'Sign-in did not return an authorization code. Try again.',
    unauthorized: 'Your account is not on the allow-list for this site.',
    no_email: 'Sign-in returned no email address for your account.',
  }
  var reason = new URLSearchParams(window.location.search).get('error')
  if (!reason) {
    return
  }
  var target = document.getElementById('login-error')
  if (!target) {
    return
  }
  target.textContent = messages[reason] || 'Sign-in failed: ' + reason
  target.hidden = false
})()
