// Jobexa Dashboard API Client
const API_BASE_URL = window.location.origin.includes('localhost') 
  ? 'http://localhost:8000/api/v1' 
  : 'https://jobexa-backend.onrender.com/api/v1';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Request Interceptor to attach JWT token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response Interceptor to handle unauthorized errors
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('token');
      // Redirect to login if not already there
      if (!window.location.pathname.endsWith('login.html') && !window.location.pathname.endsWith('index.html')) {
        window.location.href = 'index.html'; // Assume landing/login shell
      }
    }
    return Promise.reject(error);
  }
);
