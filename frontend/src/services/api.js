import axios from 'axios'
import i18n from '../i18n'

const API_URL = import.meta.env.VITE_API_URL || '/api/v1'

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add token and language to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }

  // Add Accept-Language header for backend i18n
  const language = i18n.language || 'en'
  config.headers['Accept-Language'] = language

  return config
})

// Handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// Auth API
export const authAPI = {
  login: (username, password) =>
    api.post('/auth/login', { username, password }),

  register: (username, password) =>
    api.post('/auth/register', { username, password }),

  getCurrentUser: () =>
    api.get('/auth/me'),

  initAdmin: () =>
    api.post('/auth/init'),
}

// Backup API
export const backupAPI = {
  start: (data) =>
    api.post('/backup/start', data),

  getStatus: (backupId) =>
    api.get(`/backup/${backupId}`),

  getHistory: (limit = 20, offset = 0) =>
    api.get(`/backup/history?limit=${limit}&offset=${offset}`),

  stop: (backupId) =>
    api.post(`/backup/${backupId}/stop`),

  getStats: () =>
    api.get('/backup/stats'),
}

// Sources API
export const sourcesAPI = {
  getAll: () =>
    api.get('/sources'),

  getOne: (sourceId) =>
    api.get(`/sources/${sourceId}`),

  create: (data) =>
    api.post('/sources', data),

  update: (sourceId, data) =>
    api.put(`/sources/${sourceId}`, data),

  delete: (sourceId) =>
    api.delete(`/sources/${sourceId}`),

  test: (sourceId) =>
    api.post(`/sources/${sourceId}/test`),
}

export default api
