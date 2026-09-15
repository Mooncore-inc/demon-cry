# Разработка

## Установка зависимостей

```bash
git clone https://github.com/Mooncore-inc/demon-cry.git && cd demon-cry
uv sync --locked --group dev
```

## Pre-commit

Проект использует [pre-commit](https://pre-commit.com/) для автоматической проверки кода перед коммитом.

Активация хуков (один раз после clone):

```bash
uv run pre-commit install
```

`pre-commit` уже в `[dependency-groups] dev`, отдельная установка не нужна.

При каждом `git commit` автоматически запускаются проверки:

- trailing whitespace, end-of-file, смешанные окончания строк
- отсутствие debug-остатков (`breakpoint`, `print` в production-коде)
- проверка yaml/toml/json на валидность
- поиск приватных ключей и секретов

Запуск вручную:

```bash
uv run pre-commit run --all-files
```

## Линтер и форматтер

Проект использует [ruff](https://docs.astral.sh/ruff/) для линтинга и форматирования.

Запуск:

```bash
uv run ruff check        # линтинг
uv run ruff check --fix  # автоисправление
uv run ruff format       # форматирование
```

Конфигурация в `pyproject.toml`:
- `E` — pycodestyle ошибки
- `F` — pyflakes (неиспользуемые переменные и импорты)
- `I` — isort (сортировка импортов)
- `UP` — pyupgrade (современный синтаксис)
- `B` — flake8-bugbear (антипаттерны)
- `SIM` — flake8-simplify (упрощение синтаксиса)
- `RET` — flake8-return (оптимизация return)

## Запуск локально

```bash
# Инициализация БД
demon-cry migrate upgrade

# Создание пользователя
demon-cry user create admin --admin

# Запуск сервера
demon-cry
```

Swagger доступен по `http://localhost:8000/docs`.

## Архитектура

```
demon_cry/
  __main__.py          — FastAPI app, lifespan, router mounting
  cli.py               — CLI entry point (argparse)
  core/
    config.py          — App config (pydantic-settings, DC_* env vars)
    plugin_registry.py — OSINT plugin discovery via entry points
  api/
    investigate.py     — Main investigation endpoint
    health.py          — Health check
    tools.py           — Tool listing
    admin/             — Admin CRUD (users, settings, plugins, llm_models)
    dependencies/      — FastAPI DI (auth, database)
    schemas/           — Pydantic request/response schemas
  database/
    engine.py          — SQLAlchemy async engine/session
    models/            — ORM models (users, settings, plugins, llm_models)
    repositories/      — Repository pattern (data access)
  services/
    llm.py             — LLM interaction (chain loop, tool calling)
  utils/
    version.py         — Version retrieval
```

### Слой за слоем

1. **core** — конфигурация и реестр плагинов (ничего не знает об HTTP)
2. **database** — ORM модели и репозитории (ничего не знает о API)
3. **services** — бизнес-логика (LLM взаимодействие)
4. **api** — HTTP маршруты, schemas, DI (зависит от всех предыдущих)
5. **cli** — точка входа, парсинг аргументов

## Добавление плагина

Плагины — это отдельные pip-пакеты с entry points. Контракт описан в [demon-cry-base](https://github.com/Mooncore-inc/demon-cry-base).

Кратко:

1. Установить `demon-cry-base`
2. Создать класс, наследующий `BasePlugin`
3. Определить `config_model`, `parameters_model`, `execute()`
4. Зарегистрировать entry point в `pyproject.toml`:

```toml
[project.entry-points."demon_cry.plugins"]
my_plugin = "my_package.my_plugin:MyPlugin"
```

5. Установить пакет: `uv sync --locked --group dev` (editable-установка проекта происходит автоматически)

Плагин автоматически обнаруживается при старте demon-cry и появляется в Admin API.

## Тесты

```bash
uv run pytest
```

Тесты используют моки вместо реальных вызовов API. Подробнее: [docs/tests.md](tests.md).
