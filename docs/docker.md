# Docker

## Стек

Docker Compose поднимает два сервиса:

- **app** — FastAPI-приложение (Python 3.12)
- **searxng** — метапоисковик для веб-поиска

## Запуск

```bash
docker compose up -d
```

## Остановка

```bash
docker compose down
```

## Логи

```bash
docker compose logs -f          # все сервисы
docker compose logs -f app      # только приложение
docker compose logs -f searxng  # только SearXNG
```

## Конфигурация

Файл `config.json` монтируется в контейнер как read-only volume:

```yaml
volumes:
  - ./config.json:/app/config.json:ro
```

Перед запуском убедитесь, что `config.json` существует и содержит правильные настройки (см. [Конфигурация](configuration.md)).

## Сборка образа

Образ собирается из `Dockerfile` на базе `python:3.12-slim`:

```bash
docker compose build
```

## Проверка

```bash
# Проверка health-check
curl http://localhost:8000/api/health

# Проверка SearXNG
curl 'http://localhost:8080/search?q=test&format=json'
```
