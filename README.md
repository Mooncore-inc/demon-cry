# Demon Cry 🔍

Demon Cry — это автономный OSINT-агент, который использует LLM для проведения расследований в открытых источниках. Агент сам строит гипотезы, выбирает инструменты и анализирует данные.

[![License: MPL2](https://img.shields.io/badge/License-MPL2-red.svg)](https://www.mozilla.org/en-US/MPL/2.0/)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-red.svg)](https://www.python.org/downloads/)

## Быстрый старт

```bash
git clone https://github.com/Mooncore-inc/demon-cry.git && cd demon-cry
pip install poetry
poetry install
cp example_config.json config.json   # отредактировать: base_url, api_key, model
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
