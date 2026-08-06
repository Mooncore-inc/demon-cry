# Docker

## Стек

Docker Compose поднимает два сервиса:

- **app** — FastAPI-приложение (Python 3.12)
- **searxng** — метапоисковик для веб-поиска

## Команды

| Действие | Команда |
|----------|---------|
| Запуск | `docker compose up -d` |
| Остановка | `docker compose down` |
| Логи (все) | `docker compose logs -f` |
| Логи (приложение) | `docker compose logs -f app` |
| Логи (SearXNG) | `docker compose logs -f searxng` |

## Конфигурация

Файл `config.json` монтируется в контейнер как read-only volume:

```yaml
volumes:
  - ./config.json:/app/config.json:ro
```

Перед запуском убедитесь, что `config.json` существует и содержит правильные настройки (см. [Конфигурация](configuration.md)).
