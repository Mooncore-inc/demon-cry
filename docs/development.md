# Разработка

## Установка зависимостей

```bash
git clone https://github.com/Mooncore-inc/demon-cry.git && cd demon-cry
make setup
```

## Pre-commit

Проект использует [pre-commit](https://pre-commit.com/) для автоматической проверки кода перед коммитом.
Хуки: ruff (линтинг и форматирование), ty (проверка типов), typos (орфография) и базовые проверки файлов.

Активация хуков (один раз после clone):

`pre-commit` уже в `[dependency-groups] dev`, отдельная установка не нужна.

Запуск вручную:

```bash
uv run pre-commit run --all-files
```

## Линтер и форматтер

Проект использует [ruff](https://docs.astral.sh/ruff/) для линтинга и форматирования.

Запуск:

```bash
make lint        # все линтеры: ruff + ty + typos
make lint-ruff   # только ruff
make lint-fix    # автоисправление ruff
make format      # форматирование
```

Конфигурация в `pyproject.toml`:
- `E` — pycodestyle ошибки
- `F` — pyflakes (неиспользуемые переменные и импорты)
- `I` — isort (сортировка импортов)
- `UP` — pyupgrade (современный синтаксис)
- `B` — flake8-bugbear (антипаттерны)
- `SIM` — flake8-simplify (упрощение синтаксиса)
- `RET` — flake8-return (оптимизация return)

## Проверка типов

Проект использует [ty](https://github.com/astral-sh/ty) для проверки типов.

Запуск:

```bash
make lint-ty  # эквивалент: uv run ty check
```

`make lint` запускает все линтеры сразу (ruff + ty + typos).

Конфигурация в `pyproject.toml` (`[tool.ty.src]`, исключены `tests/`, `alembic/`).

## Проверка орфографии

Проект использует [typos](https://github.com/crate-ci/typos) для поиска опечаток в коде и документации.

Запуск:

```bash
make lint-typos  # эквивалент: uv run typos
```

Конфигурация в `pyproject.toml` (`[tool.typos.files]`, исключён `alembic/`).

## Запуск локально

```bash
# Инициализация БД
demon-cry migrate upgrade

# Создание пользователя
demon-cry user create admin --admin
```

Дефолтных CORS-origins (`localhost:3000/5173`, `127.0.0.1:3000/5173`) хватает для локального фронта. Если фронт на другом порту/домене:

```bash
DC_CORS_ORIGINS='["*"]' demon-cry
```

Подробности: [Конфигурация](configuration.md#cors).

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
    __init__.py          — корневой роутер с префиксом `/api/v1`
    investigate.py     — investigation endpoints (`POST /investigate`, `GET /investigate/tools`, `POST /investigate/{tool_name}/execute`)
    admin/             — Admin CRUD (users, settings, plugins, llm_models), монтируется под `/api/v1/admin`
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

5. Установить пакет: `uv pip install -e /путь/к/плагину` (editable-установка проекта происходит автоматически)

Плагин автоматически обнаруживается при старте demon-cry и появляется в Admin API.

## Тесты

```bash
make test
```

Тесты используют моки вместо реальных вызовов API. Подробнее: [docs/tests.md](tests.md).
