# Demon Cry

Demon Cry — автономный OSINT-агент, использующий LLM для расследований в открытых источниках. Агент строит гипотезы, выбирает инструменты и анализирует данные.

[![License: MPL2](https://img.shields.io/badge/License-MPL2-red.svg)](https://www.mozilla.org/en-US/MPL/2.0/)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-red.svg)](https://www.python.org/downloads/)

## Быстрый старт

```bash
pip install demon-cry
demon-cry migrate upgrade
demon-cry user create admin --admin
demon-cry
```

Swagger: http://localhost:8000/docs

## CLI

| Команда | Описание |
|---------|----------|
| `demon-cry` | Запустить API-сервер |
| `demon-cry migrate upgrade [ревизия]` | Применить миграции БД (по умолчанию: head) |
| `demon-cry migrate downgrade [ревизия]` | Откатить миграции (по умолчанию: -1) |
| `demon-cry migrate current` | Текущая ревизия |
| `demon-cry migrate history` | История миграций |
| `demon-cry user create <имя> [--admin]` | Создать пользователя |
| `--no-banner` | Убрать ASCII-баннер при старте |

## Использование

```bash
curl -X POST http://localhost:8000/api/investigate \
  -H "Authorization: Bearer <api_key>" \
  -H "Content-Type: application/json" \
  -d '{"target": "example.com"}'
```

## Документация

- [Установка](docs/installation.md) — pip, исходники, NixOS
- [Конфигурация](docs/configuration.md) — env vars, LLM-модели, настройки
- [Управление пользователями](docs/user-management.md) — API keys, admin endpoints
- [Разработка](docs/development.md) — архитектура, добавление модулей, тесты
- [Nix / NixOS](docs/nix.md) — flake, NixOS-модуль, секреты

## Контрибьюторы

Спасибо нашим контрибьюторам!

<a href="https://github.com/Mooncore-inc/demon-cry/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=Mooncore-inc/demon-cry&columns=25&max=500" />
</a>

## Лицензия

Mozilla Public License 2.0
