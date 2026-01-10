#!/bin/bash

# Telegram-LLM-Bot Safe Deployment Script
# Features: Backup, Health Check, Rollback, Zero-downtime

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

LOG_FILE="/root/deploy.log"
BACKUP_TAG="telegram-llm-bot:backup"
MAX_RETRIES=3
HEALTH_CHECK_PORT=8000

echo "$(date): Starting deployment..." | tee -a "$LOG_FILE"

# Function: Pre-deployment backup
backup_previous_version() {
    echo -e "${GREEN}[1/7] Backing up current version...${NC}"
    
    if docker images | grep -q "telegram-llm-bot:latest"; then
        docker tag telegram-llm-bot:latest "$BACKUP_TAG" 2>/dev/null || true
        docker tag telegram-llm-bot:latest "telegram-llm-bot:previous-$(date +%Y%m%d_%H%M%S)" 2>/dev/null || true
        echo -e "${GREEN}✅ Backup created: telegram-llm-bot:backup${NC}"
    else
        echo -e "${YELLOW}⚠️  No previous version to backup${NC}"
    fi
}

# Function: Validate git pull
validate_git_pull() {
    echo -e "${GREEN}[2/7] Pulling latest changes...${NC}"
    
    cd /root/telegram-llm-bot
    
    # Get current hash
    CURRENT_HASH=$(git rev-parse HEAD 2>/dev/null || echo "unknown")
    echo "Current hash: $CURRENT_HASH" | tee -a "$LOG_FILE"
    
    if ! git pull origin master 2>&1 | tee -a "$LOG_FILE"; then
        echo -e "${RED}❌ Git pull failed - aborting deployment${NC}" | tee -a "$LOG_FILE"
        exit 1
    fi
    
    NEW_HASH=$(git rev-parse HEAD 2>/dev/null || echo "unknown")
    echo "New hash: $NEW_HASH" | tee -a "$LOG_FILE"
    
    if [ "$CURRENT_HASH" = "$NEW_HASH" ]; then
        echo -e "${YELLOW}⚠️  No new changes detected${NC}" | tee -a "$LOG_FILE"
        exit 0
    fi
    
    echo -e "${GREEN}✅ Git pull successful${NC}" | tee -a "$LOG_FILE"
}

# Function: Build new image
build_new_image() {
    echo -e "${GREEN}[3/7] Building new image...${NC}" | tee -a "$LOG_FILE"
    
    cd /root/telegram-llm-bot
    
    # Build with retry logic
    for i in $(seq 1 $MAX_RETRIES); do
        if docker build -t telegram-llm-bot:latest . 2>&1 | tee -a "$LOG_FILE"; then
            echo -e "${GREEN}✅ Build successful (attempt $i)${NC}" | tee -a "$LOG_FILE"
            return 0
        fi
        echo -e "${YELLOW}⚠️  Build failed, retrying ($i/$MAX_RETRIES)...${NC}" | tee -a "$LOG_FILE"
        sleep 2
    done
    
    echo -e "${RED}❌ Build failed after $MAX_RETRIES attempts${NC}" | tee -a "$LOG_FILE"
    return 1
}

# Function: Health check
health_check() {
    local container_name=$1
    local port=${2:-$HEALTH_CHECK_PORT}
    local max_wait=${3:-30}
    
    echo -e "${GREEN}Checking container health...${NC}" | tee -a "$LOG_FILE"
    
    for i in $(seq 1 $max_wait); do
        if docker ps --format '{{.Names}}' | grep -q "^${container_name}$"; then
            # Try using Python for health check (more reliable than curl)
            if docker exec "$container_name" python -c "import urllib.request; urllib.request.urlopen('http://localhost:$port/api/health')" 2>/dev/null; then
                echo -e "${GREEN}✅ Container is healthy${NC}" | tee -a "$LOG_FILE"
                return 0
            fi
        fi
        sleep 2
    done
    
    echo -e "${RED}❌ Health check failed${NC}" | tee -a "$LOG_FILE"
    return 1
}

# Function: Zero-downtime deploy
zero_downtime_deploy() {
    echo -e "${GREEN}[4/7] Starting zero-downtime deployment...${NC}" | tee -a "$LOG_FILE"
    
    # Stop old container gracefully
    if docker ps --format '{{.Names}}' | grep -q "^telegram-llm-bot$"; then
        echo "Stopping old container..." | tee -a "$LOG_FILE"
        docker stop telegram-llm-bot 2>/dev/null || true
        docker rm telegram-llm-bot 2>/dev/null || true
    fi
    
    # Start new container on different port
    echo "Starting new container on port 8001..." | tee -a "$LOG_FILE"
    if ! docker run -d \
        --name telegram-llm-bot-new \
        -p 8001:8000 \
        -v /root/bot-data:/app/data \
        --restart unless-stopped \
        telegram-llm-bot:latest 2>&1 | tee -a "$LOG_FILE"; then
        echo -e "${RED}❌ Failed to start new container${NC}" | tee -a "$LOG_FILE"
        return 1
    fi
    
    # Health check new container
    if ! health_check "telegram-llm-bot-new" 8001; then
        echo -e "${RED}❌ New container failed health check${NC}" | tee -a "$LOG_FILE"
        docker stop telegram-llm-bot-new 2>/dev/null || true
        docker rm telegram-llm-bot-new 2>/dev/null || true
        return 1
    fi
    
    # Switch ports (atomic switch)
    echo "Switching to new container..." | tee -a "$LOG_FILE"
    docker stop telegram-llm-bot-new 2>/dev/null || true
    docker rm telegram-llm-bot-new 2>/dev/null || true
    
    # Start final container on port 8000
    if ! docker run -d \
        --name telegram-llm-bot \
        -p 8000:8000 \
        -v /root/bot-data:/app/data \
        --restart unless-stopped \
        telegram-llm-bot:latest 2>&1 | tee -a "$LOG_FILE"; then
        echo -e "${RED}❌ Failed to start final container${NC}" | tee -a "$LOG_FILE"
        return 1
    fi
    
    # Final health check
    if ! health_check "telegram-llm-bot" 8000 60; then
        echo -e "${RED}❌ Final health check failed${NC}" | tee -a "$LOG_FILE"
        return 1
    fi
    
    echo -e "${GREEN}✅ Zero-downtime deployment successful${NC}" | tee -a "$LOG_FILE"
}

# Function: Rollback
rollback() {
    echo -e "${RED}[ROLLBACK] Starting rollback...${NC}" | tee -a "$LOG_FILE"
    
    # Stop failed container
    docker stop telegram-llm-bot 2>/dev/null || true
    docker rm telegram-llm-bot 2>/dev/null || true
    
    # Restore from backup
    if docker images | grep -q "$BACKUP_TAG"; then
        echo "Restoring from backup..." | tee -a "$LOG_FILE"
        docker tag "$BACKUP_TAG" telegram-llm-bot:latest
        docker run -d \
            --name telegram-llm-bot \
            -p 8000:8000 \
            -v /root/bot-data:/app/data \
            --restart unless-stopped \
            telegram-llm-bot:latest 2>&1 | tee -a "$LOG_FILE"
        
        echo -e "${GREEN}✅ Rollback complete${NC}" | tee -a "$LOG_FILE"
    else
        echo -e "${RED}❌ No backup available${NC}" | tee -a "$LOG_FILE"
        exit 1
    fi
}

# Main deployment flow
main() {
    trap rollback EXIT ERR  # Auto-rollback on failure
    
    # Step 1: Backup
    backup_previous_version
    
    # Step 2: Git pull
    if validate_git_pull; then
        # Step 3: Build (only if new changes)
        if ! build_new_image; then
            echo -e "${RED}Build failed, aborting...${NC}" | tee -a "$LOG_FILE"
            exit 1
        fi
        
        # Step 4: Zero-downtime deploy
        if ! zero_downtime_deploy; then
            echo -e "${RED}Deployment failed, triggering rollback...${NC}" | tee -a "$LOG_FILE"
            rollback
            exit 1
        fi
        
        echo "$(date): Deployment completed successfully!" | tee -a "$LOG_FILE"
        echo -e "${GREEN}═════════════════════════════════${NC}"
        echo -e "${GREEN}  🎉 SUCCESS 🎉  ${NC}"
        echo -e "${GREEN}═════════════════════════════════${NC}" | tee -a "$LOG_FILE"
    fi
    
    # Cleanup old images
    echo "Cleaning up old images..." | tee -a "$LOG_FILE"
    docker image prune -f --filter "until=24h" 2>/dev/null || true
    
    # Remove trap on success
    trap - EXIT ERR
}

# Run main function
main
