import React, { useEffect, useState } from 'react'
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Chip,
  Box,
  CircularProgress,
} from '@mui/material'
import { systemApi, providersApi } from '../api/client'

export default function Dashboard() {
  const [status, setStatus] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadStatus()
  }, [])

  const loadStatus = async () => {
    try {
      const response = await systemApi.status()
      setStatus(response.data)
    } catch (error) {
      console.error('Failed to load status:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
      <CircularProgress />
    </Box>
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>

      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Active LLM Provider
              </Typography>
              <Typography variant="h5">
                {status?.active_provider || 'None'}
              </Typography>
              <Chip
                label={status?.active_provider ? 'Active' : 'Inactive'}
                color={status?.active_provider ? 'success' : 'default'}
                size="small"
                sx={{ mt: 1 }}
              />
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Database
              </Typography>
              <Typography variant="h5">
                {status?.database || 'Unknown'}
              </Typography>
              <Chip
                label={status?.database === 'connected' ? 'Connected' : 'Disconnected'}
                color={status?.database === 'connected' ? 'success' : 'error'}
                size="small"
                sx={{ mt: 1 }}
              />
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Telegram Bot
              </Typography>
              <Typography variant="h5">
                {status?.telegram_bot || 'Not configured'}
              </Typography>
              <Chip
                label={status?.telegram_bot === 'running' ? 'Running' : 'Stopped'}
                color={status?.telegram_bot === 'running' ? 'success' : 'default'}
                size="small"
                sx={{ mt: 1 }}
              />
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  )
}
