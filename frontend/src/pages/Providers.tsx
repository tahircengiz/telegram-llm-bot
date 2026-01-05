import React, { useEffect, useState } from 'react'
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  Alert,
  Snackbar,
  Switch,
  FormControlLabel,
  CircularProgress,
  Grid,
  Tabs,
  Tab,
  Chip,
  Slider,
} from '@mui/material'
import { Save, Check, Settings, Cloud } from '@mui/icons-material'
import axios from 'axios'

interface TabPanelProps {
  children?: React.ReactNode
  index: number
  value: number
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props
  return (
    <div role="tabpanel" hidden={value !== index} {...other}>
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  )
}

export default function Providers() {
  const [tabValue, setTabValue] = useState(0)
  const [providers, setProviders] = useState<any[]>([])
  const [ollamaConfig, setOllamaConfig] = useState({
    base_url: '',
    model: 'qwen:1.8b',
    temperature: 0.7,
    max_tokens: 1000,
    system_prompt: 'Sen Türkçe konuşan bir akıllı ev asistanısın.',
  })
  const [loading, setLoading] = useState(true)
  const [testing, setTesting] = useState(false)
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' as 'success' | 'error' })

  useEffect(() => {
    loadProviders()
    loadOllamaConfig()
  }, [])

  const loadProviders = async () => {
    try {
      const response = await axios.get('/api/providers/')
      setProviders(response.data)
    } catch (error) {
      showSnackbar('Failed to load providers', 'error')
    } finally {
      setLoading(false)
    }
  }

  const loadOllamaConfig = async () => {
    try {
      const response = await axios.get('/api/providers/ollama/config')
      setOllamaConfig(response.data)
    } catch (error) {
      console.error('Failed to load Ollama config')
    }
  }

  const saveOllamaConfig = async () => {
    try {
      await axios.put('/api/providers/ollama/config', ollamaConfig)
      showSnackbar('Ollama configuration saved!', 'success')
      loadProviders()
    } catch (error: any) {
      showSnackbar(error.response?.data?.detail || 'Failed to save config', 'error')
    }
  }

  const testOllama = async () => {
    setTesting(true)
    try {
      const response = await axios.post('/api/providers/ollama/test')
      if (response.data.success) {
        showSnackbar(`Ollama connected! ${response.data.details?.version || ''}`, 'success')
      } else {
        showSnackbar(response.data.message, 'error')
      }
    } catch (error) {
      showSnackbar('Failed to test connection', 'error')
    } finally {
      setTesting(false)
    }
  }

  const activateProvider = async (providerId: number) => {
    try {
      await axios.post(`/api/providers/${providerId}/activate`)
      showSnackbar('Provider activated!', 'success')
      loadProviders()
    } catch (error) {
      showSnackbar('Failed to activate provider', 'error')
    }
  }

  const showSnackbar = (message: string, severity: 'success' | 'error') => {
    setSnackbar({ open: true, message, severity })
  }

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
        <CircularProgress />
      </Box>
    )
  }

  const activeProvider = providers.find((p) => p.active)

  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
        <Cloud sx={{ fontSize: 40, color: '#2196f3' }} />
        <Typography variant="h4">LLM Providers</Typography>
      </Box>

      {/* Active Provider Status */}
      <Alert severity={activeProvider ? 'success' : 'warning'} sx={{ mb: 3 }}>
        <Typography variant="body1">
          <strong>Active Provider:</strong> {activeProvider ? activeProvider.name.toUpperCase() : 'None'}
        </Typography>
      </Alert>

      {/* Provider Tabs */}
      <Card>
        <Tabs value={tabValue} onChange={(e, v) => setTabValue(v)} sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tab label="Ollama" />
          <Tab label="OpenAI" disabled />
          <Tab label="Gemini" disabled />
        </Tabs>

        {/* Ollama Tab */}
        <TabPanel value={tabValue} index={0}>
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>
                Ollama Configuration
              </Typography>
            </Grid>

            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Base URL"
                value={ollamaConfig.base_url}
                onChange={(e) => setOllamaConfig({ ...ollamaConfig, base_url: e.target.value })}
                placeholder="http://ollama:11434"
                helperText="Ollama server URL"
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Model"
                value={ollamaConfig.model}
                onChange={(e) => setOllamaConfig({ ...ollamaConfig, model: e.target.value })}
                placeholder="qwen:1.8b"
                helperText="Model name (e.g., llama2, mistral, qwen)"
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                type="number"
                label="Max Tokens"
                value={ollamaConfig.max_tokens}
                onChange={(e) => setOllamaConfig({ ...ollamaConfig, max_tokens: Number(e.target.value) })}
                inputProps={{ min: 100, max: 4000 }}
              />
            </Grid>

            <Grid item xs={12}>
              <Typography gutterBottom>Temperature: {ollamaConfig.temperature}</Typography>
              <Slider
                value={ollamaConfig.temperature}
                onChange={(e, v) => setOllamaConfig({ ...ollamaConfig, temperature: v as number })}
                min={0}
                max={2}
                step={0.1}
                marks={[
                  { value: 0, label: '0 (Focused)' },
                  { value: 1, label: '1 (Balanced)' },
                  { value: 2, label: '2 (Creative)' },
                ]}
                valueLabelDisplay="auto"
              />
            </Grid>

            <Grid item xs={12}>
              <TextField
                fullWidth
                multiline
                rows={3}
                label="System Prompt"
                value={ollamaConfig.system_prompt}
                onChange={(e) => setOllamaConfig({ ...ollamaConfig, system_prompt: e.target.value })}
                placeholder="System prompt for the AI"
              />
            </Grid>

            <Grid item xs={12}>
              <Box sx={{ display: 'flex', gap: 2 }}>
                <Button variant="contained" startIcon={<Save />} onClick={saveOllamaConfig}>
                  Save Configuration
                </Button>
                <Button
                  variant="outlined"
                  startIcon={testing ? <CircularProgress size={20} /> : <Check />}
                  onClick={testOllama}
                  disabled={testing}
                >
                  Test Connection
                </Button>
                {providers.find((p) => p.name === 'ollama') && (
                  <Button
                    variant="contained"
                    color="success"
                    onClick={() => activateProvider(providers.find((p) => p.name === 'ollama')!.id)}
                    disabled={activeProvider?.name === 'ollama'}
                  >
                    {activeProvider?.name === 'ollama' ? 'Active' : 'Activate'}
                  </Button>
                )}
              </Box>
            </Grid>
          </Grid>
        </TabPanel>

        {/* OpenAI Tab */}
        <TabPanel value={tabValue} index={1}>
          <Alert severity="info">OpenAI configuration coming soon...</Alert>
        </TabPanel>

        {/* Gemini Tab */}
        <TabPanel value={tabValue} index={2}>
          <Alert severity="info">Gemini configuration coming soon...</Alert>
        </TabPanel>
      </Card>

      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
      >
        <Alert severity={snackbar.severity} onClose={() => setSnackbar({ ...snackbar, open: false })}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  )
}
