# Конфигурация

Demon Cry настраивается через файл `config.json` в корне проекта.

## Создание конфига

```bash
cp example_config.json config.json
```

## Поля конфигурации

| Поле | Описание | Пример |
|------|----------|--------|
| `base_url` | URL API-провайдера (совместимого с OpenAI API) | `https://api.openai.com/v1` |
| `api_key` | Ключ доступа к API | `sk-...` |
| `model` | Идентификатор модели | `gpt-4o` |
| `searxng_url` | URL SearXNG | `http://localhost:8080` |

## Примеры для разных провайдеров

### OpenAI

```json
{
    "base_url": "https://api.openai.com/v1",
    "api_key": "sk-...",
    "model": "gpt-4o"
}
```

### DeepSeek

```json
{
    "base_url": "https://api.deepseek.com/v1",
    "api_key": "sk-...",
    "model": "deepseek-chat"
}
```

### Ollama (локально)

```json
{
    "base_url": "http://localhost:11434/v1",
    "api_key": "ollama",
    "model": "qwen3:32b"
}
```

### OpenRouter

```json
{
    "base_url": "https://openrouter.ai/api/v1",
    "api_key": "sk-or-...",
    "model": "qwen/qwen3-32b"
}
```

> **Важно:** провайдер должен поддерживать OpenAI-compatible API (функция `chat.completions.create` с tool calling).

## SearXNG URL

- **Docker Compose:** `http://searxng:8080` (имя контейнера в сети)
- **Локальная разработка:** `http://localhost:8080`

Поле `searxng_url` необязательно — по умолчанию используется `http://searxng:8080`.
