import React, { useState } from 'react'
import {
  Box,
  Typography,
  TextField,
  Button,
  Paper,
  List,
  ListItem,
  ListItemText,
} from '@mui/material'
import { Send as SendIcon } from '@mui/icons-material'

interface Message {
  role: 'user' | 'bot'
  text: string
}

export default function TestChat() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')

  const handleSend = () => {
    if (!input.trim()) return

    // Add user message
    const userMsg: Message = { role: 'user', text: input }
    setMessages([...messages, userMsg])

    // Simulate bot response
    setTimeout(() => {
      const botMsg: Message = {
        role: 'bot',
        text: '🤖 Bot yanıtı (Backend integration pending)',
      }
      setMessages((prev) => [...prev, botMsg])
    }, 500)

    setInput('')
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Test Chat Interface
      </Typography>

      <Paper sx={{ height: '500px', p: 2, display: 'flex', flexDirection: 'column' }}>
        <List sx={{ flexGrow: 1, overflow: 'auto', mb: 2 }}>
          {messages.map((msg, idx) => (
            <ListItem
              key={idx}
              sx={{
                justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
              }}
            >
              <Paper
                sx={{
                  p: 1.5,
                  maxWidth: '70%',
                  bgcolor: msg.role === 'user' ? 'primary.main' : 'grey.800',
                }}
              >
                <ListItemText primary={msg.text} />
              </Paper>
            </ListItem>
          ))}
        </List>

        <Box sx={{ display: 'flex', gap: 1 }}>
          <TextField
            fullWidth
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Type a message..."
          />
          <Button variant="contained" onClick={handleSend} endIcon={<SendIcon />}>
            Send
          </Button>
        </Box>
      </Paper>
    </Box>
  )
}
