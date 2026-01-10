#!/bin/bash

# Remote deployment script
# Connects to Proxmox server and runs deployment

SERVER="192.168.7.222"
USER="root"
PROJECT_DIR="/root/telegram-llm-bot"

echo "🚀 Starting remote deployment..."
echo "Server: $SERVER"
echo "Project: $PROJECT_DIR"
echo ""

# Check if SSH key is available
if [ ! -f ~/.ssh/id_rsa ] && [ ! -f ~/.ssh/id_ed25519 ]; then
    echo "⚠️  No SSH key found. You may need to enter password."
fi

# Connect and run deployment
ssh $USER@$SERVER << 'ENDSSH'
    echo "📦 Connected to server"
    echo "📂 Changing to project directory..."
    cd /root/telegram-llm-bot
    
    echo "🔄 Running deployment script..."
    ./deploy.sh
    
    echo ""
    echo "✅ Deployment completed!"
    echo ""
    echo "📊 Checking container status..."
    docker ps | grep telegram-llm-bot
    
    echo ""
    echo "🔍 Health check..."
    curl -s http://localhost:8000/api/health | head -20
ENDSSH

echo ""
echo "🎉 Remote deployment finished!"
echo "🌐 Application URL: http://192.168.7.62:8000"
