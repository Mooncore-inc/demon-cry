# SearXNG

Demon Cry использует [SearXNG](https://docs.searxng.org/) — метапоисковик, агрегирующий результаты из нескольких поисковых систем.

## Зачем нужен

Модуль `web_search` обращается к SearXNG для поиска в интернете. SearXNG объединяет результаты Google, DuckDuckGo, Bing, Qwant, Yandex и других — это повышает покрытие и снижает зависимость от одного поисковика.

## Запуск

### В Docker Compose (автоматически)

При запуске через `docker compose up -d` SearXNG поднимается автоматически в отдельном контейнере. URL: `http://searxng:8080`.

### Локально для разработки

Если запускаете приложение через `uvicorn` напрямую:

```bash
docker run -d --name searxng -p 8080:8080 searxng/searxng:latest
```

Укажите URL в `config.json`:

```json
{
    "searxng_url": "http://localhost:8080"
}
```

## Настройка поисковиков

Конфигурация SearXNG хранится в `searxng/settings.yml`. По умолчанию включены:

| Движок | Вес |
|--------|-----|
| DuckDuckGo | 1.5 |
| Google | 1.5 |
| Bing | 1.5 |
| Qwant | 1.2 |
| Yandex | 1.0 |
| Wikipedia | 0.8 |

Startpage отключён.

## Проверка работоспособности

```bash
curl 'http://localhost:8080/search?q=test&format=json'
```

Ответ должен содержать JSON с полем `results`.

## Категории поиска

Модуль `web_search` поддерживает категории: `general`, `images`, `files`, `it`, `social media`, `news`. Категория указывается в параметрах запроса.
