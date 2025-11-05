// src/api/http.js
import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_BASE_URL || 'http://127.0.0.1:8000';

const api = axios.create({ baseURL: API_BASE });

// —— Request: Authorization + prefijo /api si falta
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;

  const u = config.url || '';
  if (!u.startsWith('/api')) {
    config.url = `/api${u.startsWith('/') ? '' : '/'}${u}`;
  }
  return config;
});

// —— Response: refresh 401 una sola vez
let refreshingPromise = null;
api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config || {};
    const status = error.response?.status;
    const isRefresh = (original.url || '').includes('/auth/refresh/');

    if (status !== 401 || original._retry || isRefresh) throw error;

    const refresh = localStorage.getItem('refresh_token');
    if (!refresh) throw error;

    if (!refreshingPromise) {
      refreshingPromise = api.post('/auth/refresh/', { refresh })
        .then(({ data }) => {
          const access = data?.access;
          if (access) localStorage.setItem('access_token', access);
          return access;
        })
        .finally(() => { refreshingPromise = null; });
    }

    const newAccess = await refreshingPromise;
    original._retry = true;
    original.headers = original.headers || {};
    original.headers.Authorization = `Bearer ${newAccess}`;
    return api(original);
  }
);

export default api;
