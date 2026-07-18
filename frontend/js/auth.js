// Auth Controller
let supabaseClient = null;

document.addEventListener('DOMContentLoaded', async () => {
  // Try initializing Supabase Auth client first
  await initSupabase();

  const token = localStorage.getItem('token');
  if (token) {
    showDashboard();
  } else {
    showAuth();
  }

  // Tab Toggle Logic
  const tabLogin = document.getElementById('tab-login');
  const tabRegister = document.getElementById('tab-register');
  const submitBtn = document.getElementById('auth-submit-btn');
  let authMode = 'login'; // 'login' or 'register'

  tabLogin.addEventListener('click', () => {
    authMode = 'login';
    tabLogin.className = 'flex-1 pb-3 font-medium border-b-2 border-stripi-primary text-stripi-primary transition';
    tabRegister.className = 'flex-1 pb-3 font-light border-b-2 border-transparent text-stripi-ink-mute hover:text-stripi-ink transition';
    submitBtn.innerText = 'Log In';
  });

  tabRegister.addEventListener('click', () => {
    authMode = 'register';
    tabRegister.className = 'flex-1 pb-3 font-medium border-b-2 border-stripi-primary text-stripi-primary transition';
    tabLogin.className = 'flex-1 pb-3 font-light border-b-2 border-transparent text-stripi-ink-mute hover:text-stripi-ink transition';
    submitBtn.innerText = 'Register Account';
  });

  // Auth Form Submission
  const authForm = document.getElementById('auth-form');
  const emailInput = document.getElementById('auth-email');
  const passwordInput = document.getElementById('auth-password');
  const authAlert = document.getElementById('auth-alert');

  authForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    authAlert.className = 'hidden';

    try {
      if (authMode === 'login') {
        const formData = new FormData();
        formData.append('username', emailInput.value);
        formData.append('password', passwordInput.value);

        const response = await apiClient.post('/auth/token', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        });
        
        localStorage.setItem('token', response.data.access_token);
        showDashboard();
      } else {
        await apiClient.post('/auth/register', {
          email: emailInput.value,
          password: passwordInput.value
        });
        
        // Auto login on register
        const formData = new FormData();
        formData.append('username', emailInput.value);
        formData.append('password', passwordInput.value);

        const response = await apiClient.post('/auth/token', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        });
        
        localStorage.setItem('token', response.data.access_token);
        showDashboard();
      }
    } catch (err) {
      console.error(err);
      let errMsg = err.response?.data?.detail || err.message || 'Authentication failed. Please check credentials.';
      if (Array.isArray(errMsg)) {
        errMsg = errMsg.map(e => e.msg || e).join(', ');
      }
      authAlert.innerText = errMsg;
      authAlert.className = 'block mb-4 p-3 rounded bg-stripi-ruby/10 border border-stripi-ruby/20 text-stripi-ruby text-xs font-medium';
    }
  });

  // Logout Button
  document.getElementById('logout-btn').addEventListener('click', async () => {
    if (supabaseClient) {
      await supabaseClient.auth.signOut();
    }
    localStorage.removeItem('token');
    showAuth();
  });
});

async function initSupabase() {
  try {
    const configResp = await apiClient.get('/auth/supabase-config');
    const { supabase_url, supabase_key } = configResp.data;
    if (supabase_url && supabase_key && window.supabase) {
      supabaseClient = window.supabase.createClient(supabase_url, supabase_key);
      console.log('Supabase Auth Client initialized successfully.');

      // Make the Google login button visible
      const googleContainer = document.getElementById('google-auth-container');
      if (googleContainer) {
        googleContainer.classList.remove('hidden');
      }

      // Bind click handler for Google OAuth login
      const googleBtn = document.getElementById('google-signin-btn');
      if (googleBtn) {
        googleBtn.addEventListener('click', async () => {
          try {
            const { error } = await supabaseClient.auth.signInWithOAuth({
              provider: 'google',
              options: {
                redirectTo: window.location.origin
              }
            });
            if (error) throw error;
          } catch (err) {
            console.error(err);
            const authAlert = document.getElementById('auth-alert');
            authAlert.innerText = err.message || 'Google Auth failed.';
            authAlert.className = 'block mb-4 p-3 rounded bg-stripi-ruby/10 border border-stripi-ruby/20 text-stripi-ruby text-xs font-medium';
          }
        });
      }

      // Listen for auth state changes (e.g. redirect back from Google OAuth)
      supabaseClient.auth.onAuthStateChange((event, session) => {
        if (session) {
          localStorage.setItem('token', session.access_token);
          showDashboard();
        }
      });
    }
  } catch (err) {
    console.warn('Unable to load Supabase public config. Defaulting to local login database.', err);
  }
}

function showDashboard() {
  document.getElementById('auth-section').className = 'hidden';
  document.getElementById('dashboard-section').className = 'relative z-10 min-h-screen flex flex-col md:flex-row';
  // Shrink the gradient mesh to act as a header banner when logged in
  document.getElementById('mesh-bg').className = 'absolute top-0 left-0 right-0 h-[60px] gradient-mesh z-0 transition-all duration-700';
  
  if (window.loadDashboardData) {
    window.loadDashboardData();
  }
}

function showAuth() {
  document.getElementById('dashboard-section').className = 'hidden';
  document.getElementById('auth-section').className = 'relative z-10 flex items-center justify-center min-h-screen px-4';
  // Expand the gradient mesh back to the top third
  document.getElementById('mesh-bg').className = 'absolute top-0 left-0 right-0 h-[38vh] gradient-mesh z-0 transition-all duration-700';
}
