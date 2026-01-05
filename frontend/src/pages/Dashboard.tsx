import React, { useEffect, useState } from 'react'
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Chip,
  Box,
  CircularProgress,
  LinearProgress,
} from '@mui/material'
import { CheckCircle, Error, Settings } from '@mui/icons-material'
import axios from 'axios'

export default function Dashboard() {
  const [status, setStatus] = useState<any>(null)
  const [providers, setProviders] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadData()
    const interval = setInterval(loadData, 10000) // Refresh every 10s
    return () => clearInterval(interval)
  }, [])

  const loadData = async () => {
    try {
      const [statusRes, providersRes] = await Promise.all([
        axios.get('/api/status'),
        axios.get('/api/providers/'),
      ])
      setStatus(statusRes.data)
      setProviders(providersRes.data)
    } catch (error) {
      console.error('Failed to load dashboard data:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '60vh' }}>
        <CircularProgress size={60} />
      </Box>
    )
  }

  const activeProvider = providers.find((p) => p.active)

  return (
    <Box>
      <Typography variant="h4" gutterBottom sx={{ mb: 4, fontWeight: 'bold' }}>
        📊 Dashboard
      </Typography>

      <Grid container spacing={3}>
        {/* System Status Cards */}
        <Grid item xs={12} md={4}>
          <Card
            sx={{
              background: 'linear-gradient(135deg, rgba(33,150,243,0.1) 0%, rgba(0,0,0,0.3) 100%)',
              border: '1px solid rgba(33,150,243,0.3)',
            }}
          >
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                <Settings sx={{ fontSize: 40, color: '#2196f3' }} />
                <Typography variant="h6">LLM Provider</Typography>
              </Box>
              <Typography variant="h4" sx={{ mb: 1 }}>
                {activeProvider ? activeProvider.name.toUpperCase() : 'None'}
              </Typography>
              <Chip
                icon={activeProvider ? <CheckCircle /> : <Error />}
                label={activeProvider ? 'Active' : 'Inactive'}
                color={activeProvider ? 'success' : 'default'}
                size="small"
              />
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card
            sx={{
              background: 'linear-gradient(135deg, rgba(76,175,80,0.1) 0%, rgba(0,0,0,0.3) 100%)',
              border: '1px solid rgba(76,175,80,0.3)',
            }}
          >
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                <CheckCircle sx={{ fontSize: 40, color: '#4caf50' }} />
                <Typography variant="h6">Database</Typography>
              </Box>
              <Typography variant="h4" sx={{ mb: 1 }}>
                {status?.database || 'Unknown'}
              </Typography>
              <Chip
                icon={status?.database === 'connected' ? <CheckCircle /> : <Error />}
                label={status?.database === 'connected' ? 'Connected' : 'Disconnected'}
                color={status?.database === 'connected' ? 'success' : 'error'}
                size="small"
              />
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card
            sx={{
              background: 'linear-gradient(135deg, rgba(0,136,204,0.1) 0%, rgba(0,0,0,0.3) 100%)',
              border: '1px solid rgba(0,136,204,0.3)',
            }}
          >
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                <img
                  src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%230088cc'%3E%3Cpath d='M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm5.562 8.161c-.18.717-.962 4.815-1.359 6.389-.168.666-.5.888-.817.91-.693.064-1.22-.458-1.891-.897-1.051-.687-1.642-1.114-2.664-1.785-1.183-.776-.416-1.202.258-1.898.177-.182 3.247-2.977 3.307-3.23.007-.032.015-.15-.056-.212s-.174-.041-.248-.024c-.106.024-1.793 1.139-5.062 3.345-.479.329-.913.489-1.302.481-.428-.009-1.252-.242-1.865-.441-.752-.244-1.349-.374-1.297-.788.027-.216.324-.437.892-.663 3.498-1.524 5.831-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635.099-.001.321.023.465.14.122.099.155.232.171.326.016.094.037.308.02.475z'/%3E%3C/svg%3E"
                  alt="Telegram"
                  style={{ width: 40, height: 40 }}
                />
                <Typography variant="h6">Telegram Bot</Typography>
              </Box>
              <Typography variant="h4" sx={{ mb: 1, textTransform: 'capitalize' }}>
                {status?.telegram_bot || 'Not configured'}
              </Typography>
              <Chip
                icon={status?.telegram_bot === 'running' ? <CheckCircle /> : <Error />}
                label={status?.telegram_bot === 'running' ? 'Running' : 'Stopped'}
                color={status?.telegram_bot === 'running' ? 'success' : 'default'}
                size="small"
              />
            </CardContent>
          </Card>
        </Grid>

        {/* Available Providers */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Available LLM Providers
              </Typography>
              <Grid container spacing={2} sx={{ mt: 1 }}>
                {providers.map((provider) => (
                  <Grid item xs={12} sm={6} md={4} key={provider.id}>
                    <Card
                      variant="outlined"
                      sx={{
                        borderColor: provider.active ? 'success.main' : 'divider',
                        backgroundColor: provider.active ? 'rgba(76,175,80,0.1)' : 'transparent',
                      }}
                    >
                      <CardContent>
                        <Typography variant="h6" sx={{ textTransform: 'uppercase' }}>
                          {provider.name}
                        </Typography>
                        <Box sx={{ display: 'flex', gap: 1, mt: 1 }}>
                          <Chip
                            label={provider.enabled ? 'Enabled' : 'Disabled'}
                            color={provider.enabled ? 'primary' : 'default'}
                            size="small"
                          />
                          {provider.active && <Chip label="Active" color="success" size="small" />}
                        </Box>
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Quick Stats */}
        <Grid item xs={12}>
          <Card sx={{ background: 'linear-gradient(135deg, rgba(156,39,176,0.1) 0%, rgba(0,0,0,0.3) 100%)' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                System Health
              </Typography>
              <Box sx={{ mt: 2 }}>
                <Typography variant="body2" color="textSecondary" gutterBottom>
                  API Status
                </Typography>
                <LinearProgress variant="determinate" value={100} color="success" sx={{ height: 8, borderRadius: 4 }} />
                <Typography variant="caption" sx={{ mt: 0.5, display: 'block' }}>
                  All systems operational
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  )
}
