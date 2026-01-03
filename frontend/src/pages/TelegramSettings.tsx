import React, { useState } from 'react'
import {
  Box,
  Typography,
  TextField,
  Button,
  Card,
  CardContent,
  Alert,
} from '@mui/material'

export default function TelegramSettings() {
  const [config, setConfig] = useState({
    bot_token: '',
    allowed_chat_ids: '',
    rate_limit: 10,
  })
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  const handleSave = () => {
    setMessage({ type: 'success', text: 'Telegram config saved! (Backend integration pending)' })
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Telegram Bot Settings
      </Typography>

      <Card sx={{ maxWidth: 600 }}>
        <CardContent>
          <Box component="form" sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            {message && <Alert severity={message.type}>{message.text}</Alert>}

            <TextField
              label="Bot Token"
              type="password"
              value={config.bot_token}
              onChange={(e) => setConfig({ ...config, bot_token: e.target.value })}
              fullWidth
              helperText="Get from @BotFather on Telegram"
            />

            <TextField
              label="Allowed Chat IDs"
              value={config.allowed_chat_ids}
              onChange={(e) => setConfig({ ...config, allowed_chat_ids: e.target.value })}
              fullWidth
              helperText="Comma-separated list, e.g., 123456789,987654321"
            />

            <TextField
              label="Rate Limit (messages/minute)"
              type="number"
              value={config.rate_limit}
              onChange={(e) => setConfig({ ...config, rate_limit: parseInt(e.target.value) })}
              fullWidth
            />

            <Button variant="contained" onClick={handleSave}>
              Save Configuration
            </Button>
          </Box>
        </CardContent>
      </Card>
    </Box>
  )
}
