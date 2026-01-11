import React, { useState, useEffect } from 'react'
import {
  Box,
  Typography,
  TextField,
  Button,
  Card,
  CardContent,
  Alert,
  Switch,
  FormControlLabel,
  CircularProgress,
  Snackbar,
} from '@mui/material'
import axios from 'axios'

interface HAConfig {
  id: number
  base_url: string
  api_token: string
  dry_run: boolean
}

export default function HomeAssistant() {
  const [config, setConfig] = useState<HAConfig | null>(null)
  const [baseUrl, setBaseUrl] = useState('')
  const [apiToken, setApiToken] = useState('')
  const [dryRun, setDryRun] = useState(true)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [testing, setTesting] = useState(false)
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' as 'success' | 'error' | 'info' })

  useEffect(() => {
    loadConfig()
  }, [])

  const loadConfig = async () => {
    try {
      setLoading(true)
      const response = await axios.get('/api/homeassistant/config')
      const data = response.data
      setConfig(data)
      setBaseUrl(data.base_url || '')
      setApiToken(data.api_token === '***' ? '' : data.api_token)
      setDryRun(data.dry_run !== undefined ? data.dry_run : true)
    } catch (error: any) {
      showSnackbar('Failed to load config', 'error')
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async () => {
    setSaving(true)
    try {
      await axios.put('/api/homeassistant/config', {
        base_url: baseUrl,
        api_token: apiToken,
        dry_run: dryRun,
      })
      showSnackbar('Configuration saved successfully!', 'success')
      loadConfig()
    } catch (error: any) {
      showSnackbar(error.response?.data?.detail || 'Failed to save config', 'error')
    } finally {
      setSaving(false)
    }
  }

  const handleTest = async () => {
    setTesting(true)
    try {
      const response = await axios.get('/api/homeassistant/test')
      if (response.data.success) {
        showSnackbar('Connection test successful!', 'success')
      } else {
        showSnackbar(response.data.message || 'Connection test failed', 'error')
      }
    } catch (error: any) {
      showSnackbar(error.response?.data?.message || 'Connection test failed', 'error')
    } finally {
      setTesting(false)
    }
  }

  const showSnackbar = (message: string, severity: 'success' | 'error' | 'info') => {
    setSnackbar({ open: true, message, severity })
  }

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
        <CircularProgress />
      </Box>
    )
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Home Assistant Integration
      </Typography>

      <Alert severity="info" sx={{ mb: 3 }}>
        <Typography variant="body2">
          <strong>How to get API Token:</strong> Home Assistant → Profile → Long-lived access tokens → Create Token
          <br />
          <strong>Dry Run Mode:</strong> When enabled, commands are logged but not executed (for testing)
        </Typography>
      </Alert>

      <Card sx={{ maxWidth: 600 }}>
        <CardContent>
          <Box component="form" sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <TextField
              label="Home Assistant URL"
              value={baseUrl}
              onChange={(e) => setBaseUrl(e.target.value)}
              fullWidth
              placeholder="http://192.168.7.200:8123"
              helperText="Home Assistant base URL (e.g., http://192.168.1.100:8123)"
            />

            <TextField
              label="API Token"
              type="password"
              value={apiToken}
              onChange={(e) => setApiToken(e.target.value)}
              fullWidth
              placeholder="Enter long-lived access token"
              helperText="Long-lived access token from Home Assistant (required for commands)"
            />

            <FormControlLabel
              control={
                <Switch
                  checked={dryRun}
                  onChange={(e) => setDryRun(e.target.checked)}
                />
              }
              label="Dry Run Mode (log only, don't execute commands)"
            />

            <Box sx={{ display: 'flex', gap: 2 }}>
              <Button
                variant="contained"
                onClick={handleSave}
                disabled={saving}
                startIcon={saving ? <CircularProgress size={20} /> : null}
              >
                {saving ? 'Saving...' : 'Save Configuration'}
              </Button>
              <Button
                variant="outlined"
                onClick={handleTest}
                disabled={testing || !baseUrl}
                startIcon={testing ? <CircularProgress size={20} /> : null}
              >
                {testing ? 'Testing...' : 'Test Connection'}
              </Button>
            </Box>
          </Box>
        </CardContent>
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
