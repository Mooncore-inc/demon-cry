# Demon Cry 🔍

Demon Cry — это автономный OSINT-агент, который использует LLM для проведения расследований в открытых источниках. Агент сам строит гипотезы, выбирает инструменты и анализирует данные.

[![License: MPL2](https://img.shields.io/badge/License-MPL2-red.svg)](https://www.mozilla.org/en-US/MPL/2.0/)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-red.svg)](https://www.python.org/downloads/)

## Быстрый старт

Создайте `docker-compose.yml`:

```yaml
services:
  app:
    image: fazzyt/demon-cry
    ports:
      - "8000:8000"
    volumes:
      - ./config.json:/app/config.json:ro,z
    restart: unless-stopped

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
  demon-cry-net:
    name: demon-cry-net
```

Создайте `config.json`:

```json
{
    "base_url": "https://api.openai.com/v1",
    "api_key": "sk-...",
    "model": "gpt-4o",
    "searxng_url": "http://searxng:8080"
}
```

Создайте папку `searxng` с файлом `settings.yml`:

```yml
use_default_settings: true

server:
  secret_key: "сюда ключ придумай"
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
```

Запуск:

```bash
docker compose up -d
```

Swagger: http://localhost:8000/docs

**Пример:**

```bash
curl -X 'POST' 'http://localhost:8000/api/investigate' \
  -H 'Content-Type: application/json' \
  -d '{"target": "кто такой fazzyt", "max_tokens": 10000}'
```

## Документация

- [Конфигурация](docs/configuration.md) — настройка `config.json`, провайдеры
- [API](docs/api.md) — REST API, эндпоинты, формат запросов/ответов
- [Docker](docs/docker.md) — Docker Compose, сборка, запуск
- [SearXNG](docs/searxng.md) — метапоисковик, настройка
- [Разработка](docs/development.md) — локальный запуск, добавление модулей

## Лицензия

Mozilla Public License 2.0
