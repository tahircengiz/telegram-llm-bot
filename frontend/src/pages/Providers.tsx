import React, { useState, useEffect } from 'react'
import {
  Box,
  Typography,
  Tabs,
  Tab,
  TextField,
  Button,
  Card,
  CardContent,
  Alert,
  CircularProgress,
} from '@mui/material'
import { providersApi } from '../api/client'

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
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  // Ollama state
  const [ollamaConfig, setOllamaConfig] = useState({
    base_url: 'http://ollama.ollama.svc.cluster.local:11434',
    model: 'qwen:1.8b',
    temperature: 0.7,
    max_tokens: 1000,
    system_prompt: 'Sen Türkçe konuşan bir akıllı ev asistanısın.',
  })

  useEffect(() => {
    if (tabValue === 0) loadOllamaConfig()
  }, [tabValue])

  const loadOllamaConfig = async () => {
    try {
      const response = await providersApi.getOllamaConfig()
      setOllamaConfig(response.data)
    } catch (error: any) {
      console.error('Failed to load Ollama config:', error)
    }
  }

  const handleSaveOllama = async () => {
    setLoading(true)
    setMessage(null)
    try {
      await providersApi.updateOllamaConfig(ollamaConfig)
      setMessage({ type: 'success', text: 'Ollama config saved successfully!' })
    } catch (error: any) {
      setMessage({ type: 'error', text: error.response?.data?.detail || 'Failed to save config' })
    } finally {
      setLoading(false)
    }
  }

  const handleTestOllama = async () => {
    setLoading(true)
    setMessage(null)
    try {
      const response = await providersApi.testOllama()
      if (response.data.success) {
        setMessage({ type: 'success', text: response.data.message })
      } else {
        setMessage({ type: 'error', text: response.data.message })
      }
    } catch (error: any) {
      setMessage({ type: 'error', text: 'Test failed: ' + error.message })
    } finally {
      setLoading(false)
    }
  }

  const handleActivateOllama = async () => {
    setLoading(true)
    setMessage(null)
    try {
      await providersApi.activate(1) // Ollama provider ID = 1
      setMessage({ type: 'success', text: 'Ollama activated!' })
    } catch (error: any) {
      setMessage({ type: 'error', text: 'Failed to activate' })
    } finally {
      setLoading(false)
    }
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        LLM Providers
      </Typography>

      <Card>
        <Tabs value={tabValue} onChange={(e, v) => setTabValue(v)}>
          <Tab label="Ollama" />
          <Tab label="OpenAI" />
          <Tab label="Gemini" />
        </Tabs>

        <TabPanel value={tabValue} index={0}>
          <Box component="form" sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            {message && (
              <Alert severity={message.type}>{message.text}</Alert>
            )}

            <TextField
              label="Base URL"
              value={ollamaConfig.base_url}
              onChange={(e) => setOllamaConfig({ ...ollamaConfig, base_url: e.target.value })}
              fullWidth
            />

            <TextField
              label="Model"
              value={ollamaConfig.model}
              onChange={(e) => setOllamaConfig({ ...ollamaConfig, model: e.target.value })}
              fullWidth
              helperText="e.g., qwen:1.8b, llama2:7b"
            />

            <TextField
              label="Temperature"
              type="number"
              inputProps={{ min: 0, max: 2, step: 0.1 }}
              value={ollamaConfig.temperature}
              onChange={(e) => setOllamaConfig({ ...ollamaConfig, temperature: parseFloat(e.target.value) })}
              fullWidth
            />

            <TextField
              label="Max Tokens"
              type="number"
              value={ollamaConfig.max_tokens}
              onChange={(e) => setOllamaConfig({ ...ollamaConfig, max_tokens: parseInt(e.target.value) })}
              fullWidth
            />

            <TextField
              label="System Prompt"
              multiline
              rows={3}
              value={ollamaConfig.system_prompt}
              onChange={(e) => setOllamaConfig({ ...ollamaConfig, system_prompt: e.target.value })}
              fullWidth
            />

            <Box sx={{ display: 'flex', gap: 2 }}>
              <Button
                variant="contained"
                onClick={handleSaveOllama}
                disabled={loading}
              >
                {loading ? <CircularProgress size={24} /> : 'Save Config'}
              </Button>

              <Button
                variant="outlined"
                onClick={handleTestOllama}
                disabled={loading}
              >
                Test Connection
              </Button>

              <Button
                variant="contained"
                color="success"
                onClick={handleActivateOllama}
                disabled={loading}
              >
                Activate
              </Button>
            </Box>
          </Box>
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          <Typography>OpenAI configuration coming soon...</Typography>
        </TabPanel>

        <TabPanel value={tabValue} index={2}>
          <Typography>Gemini configuration coming soon...</Typography>
        </TabPanel>
      </Card>
    </Box>
  )
}
