import axios from 'axios'

// Default to the Vercel backend service prefix when no absolute API URL is set.
const API_BASE_URL = import.meta.env.VITE_API_URL || '/_/backend'

const api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('sentinelai_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Auth API
export const authAPI = {
  login: (credentials) => api.post('/auth/login', credentials),
  register: (userData) => api.post('/auth/register', userData),
  logout: () => api.post('/auth/logout'),
  getCurrentUser: () => api.get('/auth/me'),
}

// Dashboard API
export const dashboardAPI = {
  getStats: () => api.get('/dashboard/stats'),
  getRecentThreats: () => api.get('/dashboard/recent-threats'),
  getThreatTimeline: () => api.get('/dashboard/threat-timeline'),
  getThreatDistribution: () => api.get('/dashboard/threat-distribution'),
  getGeographicThreats: () => api.get('/dashboard/geographic-threats'),
  getSystemHealth: () => api.get('/dashboard/system-health'),
  getActivity: () => api.get('/dashboard/activity'),
}

// Reports API
export const reportsAPI = {
  exportBundle: (scope = 'all') => api.get('/reports/export', {
    params: { scope },
    responseType: 'blob',
  }),
}

// Malware API
export const malwareAPI = {
  analyzeFile: (formData) => api.post('/malware/analyze', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  getScanHistory: () => api.get('/malware/scan-history'),
  getThreatIntelligence: (fileHash) => api.get(`/malware/threat-intelligence/${fileHash}`),
  bulkScan: (fileHashes) => api.post('/malware/bulk-scan', { file_hashes: fileHashes }),
}

// Phishing API
export const phishingAPI = {
  checkEmail: (data) => api.post('/phishing/check-email', data),
  checkUrl: (url) => api.post('/phishing/check-url', null, { params: { url } }),
  getRecentPhishing: () => api.get('/phishing/recent-phishing'),
  getPhishingStats: () => api.get('/phishing/phishing-stats'),
}

// Vulnerabilities API
export const vulnerabilitiesAPI = {
  fetchFromNvd: (limit = 50) => api.post('/vulnerabilities/fetch', null, { params: { limit } }),
  getList: (params) => api.get('/vulnerabilities/list', { params }),
  getCVEDetails: (cveId) => api.get(`/vulnerabilities/cve/${cveId}`),
  getPrioritized: () => api.get('/vulnerabilities/prioritize'),
  getStats: () => api.get('/vulnerabilities/stats'),
  getTrending: () => api.get('/vulnerabilities/trending'),
  startScan: () => api.post('/vulnerabilities/scan'),
  getScanStatus: (scanId) => api.get(`/vulnerabilities/scan/${scanId}`),
}

// Security Assistant API
export const assistantAPI = {
  chat: (message, conversationId) => api.post('/assistant/chat', {
    message,
    conversation_id: conversationId,
  }),
  getSuggestions: () => api.get('/assistant/suggestions'),
  getConversation: (conversationId) => api.get(`/assistant/conversation/${conversationId}`),
  clearConversation: (conversationId) => api.delete(`/assistant/conversation/${conversationId}`),
  submitFeedback: (conversationId, rating, feedback) => 
    api.post('/assistant/feedback', null, {
      params: { conversation_id: conversationId, rating, feedback },
    }),
}

export default api
