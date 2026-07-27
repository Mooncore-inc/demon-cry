#!/bin/bash
set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Welcome to Demon Cry Installer${NC}"
echo "This script will set up the agent for you."

# Проверка Docker
if ! command -v docker &> /dev/null || ! command -v docker compose &> /dev/null; then
    echo "❌ Error: Docker and Docker Compose are required."
    echo "Please install them first: https://docs.docker.com/get-docker/"
    exit 1
fi

# Сбор данных у пользователя
echo ""
echo -e "${GREEN}Step 1: LLM Configuration${NC}"
read -p "Enter your LLM Provider Base URL (e.g., https://api.deepseek.com/v1): " BASE_URL
read -p "Enter your API Key: (e.g., sk-...)" API_KEY
read -p "Enter Model Name (e.g., deepseek-v4-flash): " MODEL

# Мастер ключ
echo ""
echo -e "${GREEN}Step 2: Security${NC}"
read -p "Set a Master API Key for Demon Cry (leave empty for random): " MASTER_KEY
if [ -z "$MASTER_KEY" ]; then
    MASTER_KEY=$(openssl rand -hex 16)
    echo "Generated random Master Key: $MASTER_KEY"
fi

echo ""
echo "📂 Creating project structure..."

mkdir -p searxng

# Создаём config.json
cat > config.json <<EOF
{
    "base_url": "$BASE_URL",
    "master_key": "$MASTER_KEY",
    "api_key": "$API_KEY",
    "model": "$MODEL",
    "searxng_url": "http://searxng:8080"
}
EOF

# Создаём docker-compose.yml
cat > docker-compose.yml <<EOF
services:
  app:
    image: fazzyt/demon-cry:latest
    ports:
      - "8000:8000"
    volumes:
      - ./config.json:/app/config.json:ro,z
    restart: unless-stopped
    depends_on:
      - searxng
    networks:
      - demon-cry-net

  searxng:
    image: searxng/searxng:latest
    ports:
      - "8080:8080"
    volumes:
      - ./searxng:/etc/searxng:z
    environment:
      - SEARXNG_BASE_URL=http://localhost:8080/
    restart: unless-stopped
    networks:
      - demon-cry-net

networks:
  demon-cry-net:
    name: demon-cry-net
EOF

# Создаем настройки для SearXNG
cat > searxng/settings.yml <<EOF
use_default_settings: true

server:
  secret_key: "$(openssl rand -hex 32)"
  limiter: false
  bind_address: "0.0.0.0"
  port: 8080

search:
  formats:
    - html
    - json
  cache:
    enable: true
    expiration_time: 3600

engines:
  - name: startpage
    disabled: true
  - name: duckduckgo
    disabled: false
    weight: 1.5
  - name: google
    disabled: false
    weight: 1.5
  - name: bing
    disabled: false
    weight: 1.5
  - name: qwant
    disabled: false
    weight: 1.2
  - name: yandex
    disabled: false
    weight: 1.0
  - name: wikipedia
    disabled: false
    weight: 0.8
EOF

# Запуск DC
echo ""
echo -e "${GREEN}🚀 Starting Demon Cry...${NC}"
docker compose up -d

# Футер
echo ""
echo -e "${GREEN}✅ Installation Complete!${NC}"
echo "-----------------------------------"
echo "API Docs: http://localhost:8000/docs"
echo "Master Key: $MASTER_KEY (Save it! You'll need it for the SDK/Bot)"
echo ""
echo "To stop: docker compose down"