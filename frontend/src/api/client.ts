import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Providers
export const providersApi = {
  list: () => api.get('/api/providers/'),
  activate: (id: number) => api.post(`/api/providers/${id}/activate`),

  // Ollama
  getOllamaConfig: () => api.get('/api/providers/ollama/config'),
  updateOllamaConfig: (config: any) => api.put('/api/providers/ollama/config', config),
  testOllama: () => api.post('/api/providers/ollama/test'),

  // OpenAI
  getOpenAIConfig: () => api.get('/api/providers/openai/config'),
  updateOpenAIConfig: (config: any) => api.put('/api/providers/openai/config', config),

  // Gemini
  getGeminiConfig: () => api.get('/api/providers/gemini/config'),
  updateGeminiConfig: (config: any) => api.put('/api/providers/gemini/config', config),
}

// System
export const systemApi = {
  health: () => api.get('/api/health'),
  status: () => api.get('/api/status'),
}
