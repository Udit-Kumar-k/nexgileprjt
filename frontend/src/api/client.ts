import axios from 'axios';

const api = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('decarbx_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // If unauthorized and not on login page, redirect or clear token
      if (window.location.pathname !== '/login') {
        // localStorage.removeItem('decarbx_token');
        // window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export default api;
