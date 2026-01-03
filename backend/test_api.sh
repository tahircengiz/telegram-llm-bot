#!/bin/bash
# Test Backend API

echo "🧪 Testing Telegram LLM Bot Backend API"
echo "=========================================="

BASE_URL="http://localhost:8000"

# Health Check
echo -e "\n1️⃣ Health Check"
curl -s "$BASE_URL/api/health" | python3 -m json.tool

# System Status
echo -e "\n\n2️⃣ System Status"
curl -s "$BASE_URL/api/status" | python3 -m json.tool

# List Providers
echo -e "\n\n3️⃣ List LLM Providers"
curl -s "$BASE_URL/api/providers/" | python3 -m json.tool

# Get Ollama Config
echo -e "\n\n4️⃣ Get Ollama Config"
curl -s "$BASE_URL/api/providers/ollama/config" | python3 -m json.tool

# Update Ollama Config
echo -e "\n\n5️⃣ Update Ollama Config"
curl -s -X PUT "$BASE_URL/api/providers/ollama/config" \
  -H "Content-Type: application/json" \
  -d '{
    "base_url": "http://192.168.7.7:30114",
    "model": "qwen:1.8b",
    "temperature": 0.7,
    "max_tokens": 1000
  }' | python3 -m json.tool

# Test Ollama Connection
echo -e "\n\n6️⃣ Test Ollama Connection"
curl -s -X POST "$BASE_URL/api/providers/ollama/test" | python3 -m json.tool

# Activate Ollama
echo -e "\n\n7️⃣ Activate Ollama Provider"
curl -s -X POST "$BASE_URL/api/providers/1/activate" | python3 -m json.tool

echo -e "\n\n✅ Tests Complete!"
