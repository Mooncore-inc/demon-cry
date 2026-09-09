# Конфигурация

Demon Cry использует комбинацию переменных окружения и настроек в БД.

## Переменные окружения

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `DC_DB_URL` | URL базы данных (SQLAlchemy async) | `sqlite+aiosqlite:///database.db` |
| `DC_HOST` | Адрес API-сервера | `127.0.0.1` |
| `DC_PORT` | Порт API-сервера | `8000` |
| `DC_LOG_FILE` | Путь к файлу лога (stderr если не задано) | — |

Пример:

```bash
DC_HOST=0.0.0.0 DC_PORT=9000 demon-cry
```

## LLM-модели

LLM-провайдеры хранятся в БД и управляются через Admin API.

### Добавление модели

```bash
curl -X POST http://localhost:8000/api/admin/llm-models \
  -H "Authorization: Bearer <api_key>" \
  -H "Content-Type: application/json" \
  -d '{
    "base_url": "https://api.openai.com/v1",
    "api_key": "sk-...",
    "model_name": "gpt-4o",
    "is_default": true
  }'
```

### Просмотр моделей

```bash
curl http://localhost:8000/api/admin/llm-models \
  -H "Authorization: Bearer <api_key>"
```

### Провайдеры

| Провайдер | base_url | Пример модели |
|-----------|----------|---------------|
| OpenAI | `https://api.openai.com/v1` | `gpt-4o` |
| DeepSeek | `https://api.deepseek.com/v1` | `deepseek-chat` |
| Ollama | `http://localhost:11434/v1` | `qwen3:32b` |
| OpenRouter | `https://openrouter.ai/api/v1` | `qwen/qwen3-32b` |

> Провайдер должен поддерживать OpenAI-compatible API (`chat.completions.create` с tool calling).

## Настройки

Настройки хранятся в БД как ключ-значение и управляются через Admin API.

| Ключ | Описание | По умолчанию |
|------|----------|--------------|
| `system_prompt` | Системный промпт для LLM | Встроенный промпт Demon Cry |
| `iteration_limit` | Максимум циклов взаимодействия с LLM | `150` |

### Просмотр настройки

```bash
curl http://localhost:8000/api/admin/settings \
  -H "Authorization: Bearer <api_key>"
```

### Изменение настройки

```bash
curl -X PATCH http://localhost:8000/api/admin/settings/iteration_limit \
  -H "Authorization: Bearer <api_key>" \
  -H "Content-Type: application/json" \
  -d '{"value": "200"}'
```

## Лимит итераций

Рекомендуемый минимум: **25 итераций**. При меньших значениях модель может не успеть собрать данные для отчёта.

При достижении лимита модель автоматически формирует итоговый отчёт.
