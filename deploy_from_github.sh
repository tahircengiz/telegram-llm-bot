#!/bin/bash

# GitHub'dan Manuel Deployment Script
# Bu script sunucuya bağlanıp GitHub'dan güncel kodu çekip deployment yapar

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SERVER="192.168.7.62"
USER="root"
SSH_KEY="$HOME/.ssh/id_ed25519"
PROJECT_DIR="/root/telegram-llm-bot"
GITHUB_REPO="https://github.com/tahircengiz/telegram-llm-bot.git"
BRANCH="master"

echo -e "${BLUE}════════════════════════════════════════${NC}"
echo -e "${BLUE}  Telegram LLM Bot - GitHub Deployment${NC}"
echo -e "${BLUE}════════════════════════════════════════${NC}"
echo ""
echo -e "${GREEN}Server:${NC} $SERVER"
echo -e "${GREEN}User:${NC} $USER"
echo -e "${GREEN}Project:${NC} $PROJECT_DIR"
echo -e "${GREEN}Repository:${NC} $GITHUB_REPO"
echo -e "${GREEN}Branch:${NC} $BRANCH"
echo ""

# Check SSH key
if [ ! -f "$SSH_KEY" ]; then
    echo -e "${YELLOW}⚠️  SSH key not found at $SSH_KEY${NC}"
    echo -e "${YELLOW}   Will try password authentication${NC}"
    SSH_OPTIONS=""
else
    echo -e "${GREEN}✅ SSH key found${NC}"
    SSH_OPTIONS="-i $SSH_KEY"
fi

# Test SSH connection
echo -e "${BLUE}[1/5] Testing SSH connection...${NC}"
if ! ssh $SSH_OPTIONS -o ConnectTimeout=5 -o StrictHostKeyChecking=no $USER@$SERVER "echo 'Connection successful'" 2>/dev/null; then
    echo -e "${RED}❌ Cannot connect to server $SERVER${NC}"
    echo -e "${RED}   Please check:${NC}"
    echo -e "${RED}   - Server is reachable${NC}"
    echo -e "${RED}   - SSH key is correct${NC}"
    echo -e "${RED}   - User has access${NC}"
    exit 1
fi
echo -e "${GREEN}✅ SSH connection successful${NC}"
echo ""

# Deploy on remote server
echo -e "${BLUE}[2/5] Connecting to server and starting deployment...${NC}"
echo ""

ssh $SSH_OPTIONS -o StrictHostKeyChecking=no $USER@$SERVER << ENDSSH
    set -e
    
    echo "📦 Connected to server: \$(hostname)"
    echo ""
    
    # Check if project directory exists
    if [ ! -d "$PROJECT_DIR" ]; then
        echo "📂 Project directory not found. Cloning repository..."
        mkdir -p $(dirname $PROJECT_DIR)
        git clone $GITHUB_REPO $PROJECT_DIR
        cd $PROJECT_DIR
        git checkout $BRANCH
    else
        echo "📂 Project directory exists. Updating from GitHub..."
        cd $PROJECT_DIR
        
        # Check if it's a git repository
        if [ ! -d .git ]; then
            echo "⚠️  Not a git repository. Re-initializing..."
            rm -rf $PROJECT_DIR
            mkdir -p $(dirname $PROJECT_DIR)
            git clone $GITHUB_REPO $PROJECT_DIR
            cd $PROJECT_DIR
            git checkout $BRANCH
        else
            # Fetch and pull latest changes
            echo "🔄 Fetching latest changes from GitHub..."
            git fetch origin $BRANCH
            
            # Get current and new commit hashes
            CURRENT_HASH=\$(git rev-parse HEAD 2>/dev/null || echo "unknown")
            NEW_HASH=\$(git rev-parse origin/$BRANCH 2>/dev/null || echo "unknown")
            
            echo "   Current: \${CURRENT_HASH:0:8}"
            echo "   Latest:  \${NEW_HASH:0:8}"
            
            if [ "\$CURRENT_HASH" = "\$NEW_HASH" ]; then
                echo "ℹ️  Already on latest version"
            else
                echo "📥 Pulling latest changes..."
                git reset --hard origin/$BRANCH
                git clean -fd
            fi
        fi
    fi
    
    echo ""
    echo "📋 Current commit:"
    git log -1 --oneline
    
    echo ""
    echo "🔧 Making deploy.sh executable..."
    chmod +x deploy.sh
    
    echo ""
    echo -e "${BLUE}[3/5] Running deployment script...${NC}"
    echo ""
    
    # Run deployment script
    cd $PROJECT_DIR
    ./deploy.sh
    
    echo ""
    echo -e "${BLUE}[4/5] Checking deployment status...${NC}"
    echo ""
    
    # Check container status
    if docker ps | grep -q telegram-llm-bot; then
        echo "✅ Container is running"
        docker ps | grep telegram-llm-bot
    else
        echo "⚠️  Container is not running"
    fi
    
    echo ""
    echo -e "${BLUE}[5/5] Health check...${NC}"
    echo ""
    
    # Health check
    sleep 2
    if curl -s -f http://localhost:8000/api/health > /dev/null 2>&1; then
        echo "✅ Health check passed"
        curl -s http://localhost:8000/api/health | head -5
    else
        echo "⚠️  Health check failed (container might still be starting)"
    fi
    
    echo ""
    echo "📊 Deployment Summary:"
    echo "   Application URL: http://192.168.7.62:8000"
    echo "   Admin Panel: http://192.168.7.62:8000"
    echo "   API Docs: http://192.168.7.62:8000/api/docs"
    echo "   Health: http://192.168.7.62:8000/api/health"
    
ENDSSH

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}════════════════════════════════════════${NC}"
    echo -e "${GREEN}  ✅ Deployment Completed Successfully!${NC}"
    echo -e "${GREEN}════════════════════════════════════════${NC}"
    echo ""
    echo -e "${GREEN}🌐 Application URL:${NC} http://192.168.7.62:8000"
    echo -e "${GREEN}📚 API Docs:${NC} http://192.168.7.62:8000/api/docs"
    echo ""
else
    echo ""
    echo -e "${RED}════════════════════════════════════════${NC}"
    echo -e "${RED}  ❌ Deployment Failed${NC}"
    echo -e "${RED}════════════════════════════════════════${NC}"
    echo ""
    echo "Check the output above for error details."
    exit 1
fi
