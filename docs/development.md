# Разработка

## Установка зависимостей

```bash
git clone https://github.com/Mooncore-inc/demon-cry.git && cd demon-cry
pip install poetry
poetry install
```

## Pre-commit

Проект использует [pre-commit](https://pre-commit.com/) для автоматической проверки кода перед коммитом.

Активация хуков (один раз после clone):

```bash
poetry run pre-commit install
```

После этого при каждом `git commit` будут автоматически запускаться проверки:

- trailing whitespace, end-of-file, смешанные окончания строк
- отсутствие debug-остатков (`breakpoint`, `print` в production-коде)
- проверка yaml/toml/json на валидность
- поиск приватных ключей и секретов

Запуск вручную по всем файлам:

```bash
poetry run pre-commit run --all-files
```

## Запуск локально

```bash
cp example_config.json config.json  # настроить base_url, api_key, model

# Запускает только зависимости (SearXNG)
docker compose -f docker-compose-dev.yml up -d

# Запуск веб-сервера
poetry run uvicorn core.__main__:app --host 0.0.0.0 --port 8000 --reload
```

Swagger доступен по `http://localhost:8000/docs`.

## SearXNG для локальной разработки

Модуль `web_search` работает через SearXNG — метапоисковик, агрегирующий результаты Google, DuckDuckGo, Bing и других. Без него поиск в интернете не будет работать.

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

Все **OSINT-инструменты наследуются** от `OSINTModule` из `modules/base_modules.py`. Для создания нового модуля:

1. Создайте файл в `modules/`, например `modules/my_tool.py`
2. Наследуйтесь от `OSINTModule` и реализуйте интерфейс:

```python
from modules.base_modules import OSINTModule


class MyTool(OSINTModule):
    name = "my_tool"
    description = "Описание инструмента для LLM"
    category = "search"  # network / content / search
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
