import React, { useState } from 'react'
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
} from '@mui/material'

export default function HomeAssistant() {
  const [config, setConfig] = useState({
    base_url: 'http://192.168.7.200:8123',
    api_token: '',
    dry_run_mode: true,
  })
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  const handleSave = () => {
    setMessage({ type: 'success', text: 'HA config saved! (Backend integration pending)' })
  }

  const handleTest = () => {
    setMessage({ type: 'info', text: 'Testing connection... (Backend integration pending)' })
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Home Assistant Integration
      </Typography>

      <Card sx={{ maxWidth: 600 }}>
        <CardContent>
          <Box component="form" sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            {message && <Alert severity={message.type}>{message.text}</Alert>}

            <TextField
              label="Home Assistant URL"
              value={config.base_url}
              onChange={(e) => setConfig({ ...config, base_url: e.target.value })}
              fullWidth
              helperText="e.g., http://192.168.1.100:8123"
            />

            <TextField
              label="API Token (Optional)"
              type="password"
              value={config.api_token}
              onChange={(e) => setConfig({ ...config, api_token: e.target.value })}
              fullWidth
              helperText="Long-lived access token from HA"
            />

            <FormControlLabel
              control={
                <Switch
                  checked={config.dry_run_mode}
                  onChange={(e) => setConfig({ ...config, dry_run_mode: e.target.checked })}
                />
              }
              label="Dry Run Mode (log only, don't execute)"
            />

            <Box sx={{ display: 'flex', gap: 2 }}>
              <Button variant="contained" onClick={handleSave}>
                Save Configuration
              </Button>
              <Button variant="outlined" onClick={handleTest}>
                Test Connection
              </Button>
            </Box>
          </Box>
        </CardContent>
      </Card>
    </Box>
  )
}
