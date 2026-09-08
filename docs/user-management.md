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
curl -X POST http://localhost:8000/api/admin/users \
  -H "Authorization: Bearer <admin_key>" \
  -H "Content-Type: application/json" \
  -d '{"username": "charlie"}'
```

> Через API создаются только обычные пользователи. Для создания администратора используйте CLI.

## Аутентификация

Все запросы к API требуют Bearer-токен (API key пользователя):

```bash
curl http://localhost:8000/api/investigate \
  -H "Authorization: Bearer <api_key>" \
  -H "Content-Type: application/json" \
  -d '{"target": "example.com"}'
```

## Роли

| Роль | Доступ |
|------|--------|
| Admin | Полный доступ: user CRUD, настройки, модули, LLM-модели |
| User | Только investigation и health check |

## Admin API

Все admin-endpoint'ы доступны только пользователям с `is_admin: true`.

### Пользователи

| Endpoint | Метод | Описание |
|----------|-------|----------|
| `/api/admin/users/` | POST | Создать пользователя |
| `/api/admin/users/{id}` | GET | Получить пользователя |
| `/api/admin/users/{id}` | PATCH | Обновить пользователя |
| `/api/admin/users/{id}` | DELETE | Удалить пользователя |

### Настройки

| Endpoint | Метод | Описание |
|----------|-------|----------|
| `/api/admin/settings/` | GET | Все настройки |
| `/api/admin/settings/{key}` | GET | Получить настройку |
| `/api/admin/settings/{key}` | PATCH | Обновить настройку |

### LLM-модели

| Endpoint | Метод | Описание |
|----------|-------|----------|
| `/api/admin/llm-models/` | GET | Список моделей |
| `/api/admin/llm-models/` | POST | Добавить модель |
| `/api/admin/llm-models/{id}` | GET | Получить модель |
| `/api/admin/llm-models/{id}` | PATCH | Обновить модель |
| `/api/admin/llm-models/{id}` | DELETE | Удалить модель |

### Модули

| Endpoint | Метод | Описание |
|----------|-------|----------|
| `/api/admin/modules/` | GET | Список модулей |
| `/api/admin/modules/{id}` | GET | Получить модуль |
| `/api/admin/modules/{id}` | PATCH | Настроить модуль |
