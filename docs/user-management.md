# Управление пользователями

## Создание пользователей

### Через CLI

```bash
# Создать обычного пользователя
demon-cry user create alice

# Создать администратора
demon-cry user create bob --admin
```

CLI выведет API key — **сохраните его, повторный показ невозможен**.

### Через Admin API

```bash
curl -X POST http://localhost:8000/api/v1/admin/users \
  -H "Authorization: Bearer <admin_key>" \
  -H "Content-Type: application/json" \
  -d '{"username": "charlie"}'
```

> Через API создаются только обычные пользователи. Для создания администратора используйте CLI.

## Аутентификация

Все запросы к API требуют Bearer-токен (API key пользователя):

```bash
curl -X POST http://localhost:8000/api/v1/investigates/ \
  -H "Authorization: Bearer <api_key>" \
  -H "Content-Type: application/json" \
  -d '{"name": "case-1"}'
```

### Investigation endpoints

| Endpoint | Метод | Описание |
|----------|-------|----------|
| `/api/v1/investigates/` | POST | Создать расследование |
| `/api/v1/investigates/` | GET | Список своих расследований |
| `/api/v1/investigates/{id}` | GET | Получить расследование |
| `/api/v1/investigates/{id}` | PATCH | Переименовать расследование |
| `/api/v1/investigates/{id}` | DELETE | Удалить расследование и его данные |
| `/api/v1/investigates/{id}/data` | GET | Список run'ов расследования |
| `/api/v1/investigates/{id}/{tool_name}/execute` | POST | Выполнить инструмент в контексте расследования |
| `/api/v1/investigate/tools` | GET | Список доступных инструментов (OpenAI-compatible schema) |
| `/api/v1/investigate` | POST | Disabled (410), LLM investigation удалён |

## Роли

| Роль | Доступ |
|------|--------|
| Admin | Полный доступ: user CRUD, настройки, плагины, LLM-модели |
| User | Только investigation endpoints (`/api/v1/investigates/*`, `GET /api/v1/investigate/tools`) |

## Admin API

Все admin-endpoint'ы доступны только пользователям с `is_admin: true`.

### Пользователи

| Endpoint | Метод | Описание |
|----------|-------|----------|
| `/api/v1/admin/users/` | POST | Создать пользователя |
| `/api/v1/admin/users/{id}` | GET | Получить пользователя |
| `/api/v1/admin/users/{id}` | PATCH | Обновить пользователя |
| `/api/v1/admin/users/{id}` | DELETE | Удалить пользователя |

### Настройки

| Endpoint | Метод | Описание |
|----------|-------|----------|
| `/api/v1/admin/settings/` | GET | Все настройки |
| `/api/v1/admin/settings/{key}` | GET | Получить настройку |
| `/api/v1/admin/settings/{key}` | PATCH | Обновить настройку |

### LLM-модели

| Endpoint | Метод | Описание |
|----------|-------|----------|
| `/api/v1/admin/llm-models/` | GET | Список моделей |
| `/api/v1/admin/llm-models/` | POST | Добавить модель |
| `/api/v1/admin/llm-models/{id}` | GET | Получить модель |
| `/api/v1/admin/llm-models/{id}` | PATCH | Обновить модель |
| `/api/v1/admin/llm-models/{id}` | DELETE | Удалить модель |

### Плагины

| Endpoint | Метод | Описание |
|----------|-------|----------|
| `/api/v1/admin/plugins/` | GET | Список плагинов |
| `/api/v1/admin/plugins/{plugin_name}` | GET | Получить плагин |
| `/api/v1/admin/plugins/{plugin_name}` | PATCH | Настроить плагин |
