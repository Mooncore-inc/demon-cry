# Разработка

## Установка зависимостей

```bash
git clone https://github.com/Mooncore-inc/demon-cry.git && cd demon-cry
pip install poetry
poetry install
```

## Запуск локально

```bash
cp example_config.json config.json  # настроить base_url, api_key, model
poetry run uvicorn core.__main__:app --host 0.0.0.0 --port 8000
```

Swagger доступен по `http://localhost:8000/docs`.

## SearXNG для локальной разработки

Модуль `web_search` работает через SearXNG — метапоисковик, агрегирующий результаты Google, DuckDuckGo, Bing и других. Без него поиск в интернете не будет работать.

При запуске через Docker Compose SearXNG поднимается автоматически. Если же запускаете приложение через `uvicorn` напрямую, поднимите SearXNG отдельно:

```bash
docker run -d --name searxng -p 8080:8080 searxng/searxng:latest
```

Укажите URL в `config.json`:

```json
{
    "searxng_url": "http://localhost:8080"
}
```

Проверка:

```bash
curl 'http://localhost:8080/search?q=test&format=json'
```

Должен вернуться JSON с полем `results`.

## Добавление своего модуля

Все OSINT-инструменты наследуются от `OSINTModule` из `modules/base_modules.py`. Для создания нового модуля:

1. Создайте файл в `modules/`, например `modules/my_tool.py`
2. Наследуйтесь от `OSINTModule` и реализуйте интерфейс:

```python
from modules.base_modules import OSINTModule


class MyTool(OSINTModule):
    name = "my_tool"
    description = "Описание инструмента для LLM"
    parameters = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Входные данные"}
        },
        "required": ["query"]
    }

    async def execute(self, **kwargs) -> str:
        query = kwargs["query"]
        # Ваша логика
        return "результат"
```

Модуль автоматически зарегистрируется при старте приложения благодаря `ModuleRegistry.discover()`.
