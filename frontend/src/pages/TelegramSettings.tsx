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
  Chip,
  CircularProgress,
  Divider,
  Grid,
} from '@mui/material'
import { Send, Info, Save, Telegram } from '@mui/icons-material'
import axios from 'axios'

interface TelegramConfig {
  id: number
  bot_token: string
  allowed_chat_ids: string
  rate_limit: number
  enabled: boolean
}

export default function TelegramSettings() {
  const [config, setConfig] = useState<TelegramConfig | null>(null)
  const [botToken, setBotToken] = useState('')
  const [chatIds, setChatIds] = useState('')
  const [rateLimit, setRateLimit] = useState(10)
  const [enabled, setEnabled] = useState(false)
  const [testChatId, setTestChatId] = useState('')
  const [testMessage, setTestMessage] = useState('🤖 Test message from Admin Panel!')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [botInfo, setBotInfo] = useState<any>(null)
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' as 'success' | 'error' | 'info' })

  useEffect(() => {
    loadConfig()
  }, [])

  const loadConfig = async () => {
    try {
      const response = await axios.get('/api/telegram/config')
      const data = response.data
      setConfig(data)
      setBotToken(data.bot_token === '***' ? '' : data.bot_token)
      setChatIds(data.allowed_chat_ids || '[]')
      setRateLimit(data.rate_limit)
      setEnabled(data.enabled)
    } catch (error) {
      showSnackbar('Failed to load config', 'error')
    } finally {
      setLoading(false)
    }
  }

  const saveConfig = async () => {
    setSaving(true)
    try {
      await axios.put('/api/telegram/config', {
        bot_token: botToken,
        allowed_chat_ids: chatIds,
        rate_limit: rateLimit,
        enabled: enabled,
      })
      showSnackbar('Configuration saved successfully!', 'success')
      loadConfig()
    } catch (error: any) {
      showSnackbar(error.response?.data?.detail || 'Failed to save config', 'error')
    } finally {
      setSaving(false)
    }
  }

  const getBotInfo = async () => {
    try {
      const response = await axios.get('/api/telegram/me')
      if (response.data.success) {
        setBotInfo(response.data.details)
        showSnackbar('Bot info retrieved!', 'success')
      } else {
        showSnackbar(response.data.message, 'error')
      }
    } catch (error) {
      showSnackbar('Failed to get bot info', 'error')
    }
  }

  const sendTestMessage = async () => {
    try {
      const response = await axios.post('/api/telegram/test', {
        chat_id: testChatId,
        message: testMessage,
      })
      if (response.data.success) {
        showSnackbar('Test message sent successfully!', 'success')
      } else {
        showSnackbar(response.data.message, 'error')
      }
    } catch (error: any) {
      showSnackbar(error.response?.data?.detail || 'Failed to send test message', 'error')
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
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
        <Telegram sx={{ fontSize: 40, color: '#0088cc' }} />
        <Typography variant="h4">Telegram Bot Settings</Typography>
      </Box>

      {/* Bot Configuration Card */}
      <Card sx={{ mb: 3, background: 'linear-gradient(135deg, rgba(0,136,204,0.1) 0%, rgba(0,0,0,0.3) 100%)' }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Bot Configuration
          </Typography>

          <Alert severity="info" sx={{ mb: 3 }}>
            <Typography variant="body2">
              <strong>How to get Bot Token:</strong> Open Telegram → Search @BotFather → /newbot → Follow instructions
              <br />
              <strong>How to get Chat ID:</strong> Send /start to your bot → Visit https://api.telegram.org/bot&lt;TOKEN&gt;/getUpdates
            </Typography>
          </Alert>

          <Grid container spacing={2}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Bot Token"
                value={botToken}
                onChange={(e) => setBotToken(e.target.value)}
                placeholder="123456:ABC-DEF1234ghIkl-zyx"
                type="password"
                helperText="Your bot token from @BotFather"
              />
            </Grid>

            <Grid item xs={12} md={8}>
              <TextField
                fullWidth
                label="Allowed Chat IDs (JSON Array)"
                value={chatIds}
                onChange={(e) => setChatIds(e.target.value)}
                placeholder='["123456789", "987654321"]'
                helperText="JSON array of allowed Telegram chat IDs"
              />
            </Grid>

            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                type="number"
                label="Rate Limit"
                value={rateLimit}
                onChange={(e) => setRateLimit(Number(e.target.value))}
                inputProps={{ min: 1, max: 100 }}
                helperText="Messages per minute"
              />
            </Grid>

            <Grid item xs={12}>
              <FormControlLabel
                control={<Switch checked={enabled} onChange={(e) => setEnabled(e.target.checked)} />}
                label="Enable Bot"
              />
            </Grid>

            <Grid item xs={12}>
              <Box sx={{ display: 'flex', gap: 2 }}>
                <Button
                  variant="contained"
                  startIcon={saving ? <CircularProgress size={20} /> : <Save />}
                  onClick={saveConfig}
                  disabled={saving}
                >
                  Save Configuration
                </Button>
                <Button variant="outlined" startIcon={<Info />} onClick={getBotInfo}>
                  Get Bot Info
                </Button>
              </Box>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Bot Info Card */}
      {botInfo && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Bot Information
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <Typography variant="body2" color="textSecondary">
                  Username
                </Typography>
                <Typography variant="body1">@{botInfo.username}</Typography>
              </Grid>
              <Grid item xs={12} sm={6}>
                <Typography variant="body2" color="textSecondary">
                  Name
                </Typography>
                <Typography variant="body1">{botInfo.first_name}</Typography>
              </Grid>
              <Grid item xs={12} sm={6}>
                <Typography variant="body2" color="textSecondary">
                  Bot ID
                </Typography>
                <Typography variant="body1">{botInfo.id}</Typography>
              </Grid>
              <Grid item xs={12} sm={6}>
                <Typography variant="body2" color="textSecondary">
                  Status
                </Typography>
                <Chip label={botInfo.is_bot ? 'Active Bot' : 'Not a Bot'} color="success" size="small" />
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      )}

      {/* Test Message Card */}
      <Card sx={{ background: 'linear-gradient(135deg, rgba(33,150,243,0.1) 0%, rgba(0,0,0,0.3) 100%)' }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Send Test Message
          </Typography>

          <Grid container spacing={2}>
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                label="Chat ID"
                value={testChatId}
                onChange={(e) => setTestChatId(e.target.value)}
                placeholder="123456789"
                helperText="Telegram chat ID to send test message"
              />
            </Grid>

            <Grid item xs={12} md={8}>
              <TextField
                fullWidth
                label="Test Message"
                value={testMessage}
                onChange={(e) => setTestMessage(e.target.value)}
                placeholder="Enter your test message"
              />
            </Grid>

            <Grid item xs={12}>
              <Button
                variant="contained"
                color="primary"
                startIcon={<Send />}
                onClick={sendTestMessage}
                disabled={!testChatId || !testMessage}
              >
                Send Test Message
              </Button>
            </Grid>
          </Grid>
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
