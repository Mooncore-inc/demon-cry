# Demon Cry 🔍

Demon Cry — это автономный OSINT-агент, который использует LLM для проведения расследований в открытых источниках. Агент сам строит гипотезы, выбирает инструменты и анализирует данные.

### Установка

Клонируем репозиторий
```bash
git clone https://github.com/Mooncore-inc/demon-cry.git && cd demon-cry
```
Создаём виртуальное окружение
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate  # Windows
```
Устанавливаем зависимости
```bash
pip install -r requirements.txt
```
### Конфигурация

Копируем шаблон конфига:
```bash
cp example_config.json config.json
```

Файл `config.json` содержит три поля:

| Поле | Описание |
|------|----------|
| `base_url` | URL API-провайдера (совместимого с OpenAI API) |
| `api_key` | Ключ доступа к API |
| `model` | Идентификатор модели |

#### Примеры для разных провайдеров

**OpenAI:**
```json
{
    "base_url": "https://api.openai.com/v1",
    "api_key": "sk-...",
    "model": "gpt-4o"
}
```

**Ollama (локально):**
```json
{
    "base_url": "http://localhost:11434/v1",
    "api_key": "ollama",
    "model": "qwen3:32b"
}
```

**OpenRouter:**
```json
{
    "base_url": "https://openrouter.ai/api/v1",
    "api_key": "sk-or-...",
    "model": "qwen/qwen3-32b"
}
```

> **Важно:** провайдер должен поддерживать OpenAI-compatible API (функции `chat.completions.create` с tool calling).

Запуск
```bash
uvicorn core.__main__:app --host 0.0.0.0 --port 8000
```

### API
Swagger-документация доступна по адресу `http://localhost:8000/docs`.

### Пример использования

Агент способен самостоятельно строить цепочку рассуждений и уточнять запросы. 

**Запрос:**
```bash
curl -X 'POST' 'http://localhost:8000/investigate' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
    "target": "кто такой fazzyt",
    "max_tokens": 10000
  }'
```

**Ответ:**
```json
{
  "status": "success",
  "result": "\n\nСудя по открытым источникам, **fazzyt** — это псевдоним (никнейм) разработчика.\n\nВот основные факты, которые о нем известны:\n\n*   **GitHub:** Пользователь с ником **Michael [fazzyt]** (ссылка: `github.com/Fazzyt`). У него есть около 5 публичных репозиториев.\n*   **Telegram-бот:** Он известен созданием бота для Telegram, который рисует анимированное сердечко в чате при использовании команды `+heart`.\n*   **Другие проекты:** В его портфолио также упоминается проект `Fanbase` (сайт для сбора цитат) и некий проект `mooncore-inc`",
  "tools_used": [
    {
      "name": "web_search",
      "arguments": { "query": "fazzyt", "max_results": 10 }
    },
    {
      "name": "parse_website",
      "arguments": { "url": "https://github.com/Fazzyt/" }
    },
    {
      "name": "web_search",
      "arguments": { "query": "fazzyt github michael", "max_results": 10 }
    }
  ],
  "total_tokens": 7931
}
```

### Docker

Сборка образа и запуск:
```bash
docker compose up -d
```

Остановка:
```bash
docker compose down
```

Логи:
```bash
docker compose logs -f
```

Конфигурация передаётся через volume-монтирование `config.json` (read-only).
