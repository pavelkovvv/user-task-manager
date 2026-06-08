# user-task-manager

Backend-сервис для учёта задач пользователей: REST API на FastAPI, PostgreSQL, async SQLAlchemy, Alembic, Pytest.

## Возможности

- создание и получение пользователя;
- CRUD-операции с задачами пользователя;
- фильтрация задач по статусу и пагинация;
- обновление статуса задачи;
- статистика по задачам пользователя.

## Быстрый старт (Docker)

```bash
docker compose up --build
```

После запуска:

| Ресурс | URL |
|--------|-----|
| API | http://localhost:8000 |
| Swagger | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |

Миграции Alembic применяются автоматически при старте контейнера `api`. Ручная настройка БД не требуется.

Остановка:

```bash
docker compose down
```

## Локальный запуск без Docker

**Требования:** Python 3.11+, PostgreSQL 16+.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# заполните POSTGRES_DB_PASSWORD и при необходимости другие переменные

createdb user-task-manager
alembic upgrade head
python main.py
```

## Тесты

Тесты используют **отдельную** БД `user-task-manager-test` (не dev-базу).

```bash
createdb user-task-manager-test
POSTGRES_DB_NAME=user-task-manager-test alembic upgrade head
pytest tests/ -v
```

Или через Makefile:

```bash
make test
```

Покрытие сценариев:

1. создание пользователя;
2. конфликт при дублирующемся email (409);
3. создание задачи;
4. получение списка задач;
5. фильтрация по статусу;
6. обновление статуса;
7. удаление задачи;
8. статистика по задачам.

## Переменные окружения

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `POSTGRES_DB_HOST` | хост PostgreSQL | `localhost` |
| `POSTGRES_DB_PORT` | порт PostgreSQL | `5432` |
| `POSTGRES_DB_USER` | пользователь БД | — |
| `POSTGRES_DB_PASSWORD` | пароль БД | — |
| `POSTGRES_DB_NAME` | имя БД приложения | `user-task-manager` |
| `POSTGRES_TEST_DB_NAME` | имя БД для pytest | `user-task-manager-test` |
| `POSTGRES_POOL_SIZE` | размер пула соединений | `10` |
| `POSTGRES_MAX_OVERFLOW` | доп. соединения при пиках | `20` |
| `POSTGRES_POOL_RECYCLE_SEC` | пересоздание соединений, сек | `1800` |
| `FASTAPI_HOST` | хост uvicorn | `0.0.0.0` |
| `FASTAPI_PORT` | порт uvicorn | `8000` |
| `FASTAPI_RELOAD` | hot-reload (`true`/`false`) | `false` |
| `LOG_FILE` | путь к файлу логов | `/var/log/user-task-manager/app.log` |

Приоритет конфигурации: `config/config.default.yaml` → `config/config.yaml` → переменные окружения / `.env`.

В Docker Compose значения для PostgreSQL заданы в `docker-compose.yml`.

## Архитектура

```
main.py                 # точка входа, FastAPI-приложение
settings.py             # загрузка конфигурации (YAML + .env)
src/
  routers/              # HTTP-слой (эндпоинты)
  schemas/              # Pydantic-схемы запросов и ответов
  services/             # бизнес-логика, HTTP-ошибки
  crud/                 # работа с БД (repository)
  models/               # SQLAlchemy-модели
  database.py           # engine, session, dependency get_obj_db
alembic/                # миграции схемы БД
tests/                  # интеграционные API-тесты (httpx + pytest-asyncio)
```

Слои: **router → service → crud → model**. Валидация входных данных — Pydantic; уникальность email и ограничения полей — на уровне моделей и БД.

Стек: Python 3.13, FastAPI, async SQLAlchemy 2.0, asyncpg, Alembic, Pydantic v2, Pytest, Ruff.

## API

Базовый URL: `http://localhost:8000`

### Создать пользователя

```http
POST /users
Content-Type: application/json

{
  "email": "user@example.com",
  "name": "Ivan"
}
```

Ответ `201`:

```json
{
  "id": 1,
  "email": "user@example.com",
  "name": "Ivan",
  "created_at": "2026-06-05T12:00:00"
}
```

При дублирующемся email — `409 Conflict`.

### Получить пользователя

```http
GET /users/1
```

`404` — пользователь не найден.

### Создать задачу

```http
POST /users/1/tasks
Content-Type: application/json

{
  "title": "Подготовить отчет",
  "description": "Собрать данные за неделю"
}
```

Ответ `201`. `404` — пользователь не найден.

### Список задач пользователя

```http
GET /users/1/tasks
GET /users/1/tasks?status=done
GET /users/1/tasks?limit=10&offset=0
```

Ответ `200`:

```json
{
  "items": [
    {
      "id": 1,
      "user_id": 1,
      "title": "Подготовить отчет",
      "description": "Собрать данные за неделю",
      "status": "new",
      "created_at": "2026-06-05T12:00:00",
      "updated_at": null
    }
  ],
  "total": 1
}
```

`total` — общее число задач с учётом фильтра (без учёта пагинации). По умолчанию `limit=20`, максимум `100`.

### Обновить статус задачи

```http
PATCH /tasks/1/status
Content-Type: application/json

{
  "status": "in_progress"
}
```

Допустимые статусы: `new`, `in_progress`, `done`, `cancelled`.  
`404` — задача не найдена. `422` — некорректный статус.

### Удалить задачу

```http
DELETE /tasks/1
```

Ответ `200`:

```json
{
  "ok": true
}
```

### Статистика по задачам

```http
GET /users/1/tasks/stats
```

Ответ `200`:

```json
{
  "total": 10,
  "new": 3,
  "in_progress": 2,
  "done": 4,
  "cancelled": 1
}
```

## Примеры curl

```bash
# создать пользователя
curl -s -X POST http://localhost:8000/users \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","name":"Ivan"}'

# создать задачу
curl -s -X POST http://localhost:8000/users/1/tasks \
  -H "Content-Type: application/json" \
  -d '{"title":"Подготовить отчет","description":"Собрать данные за неделю"}'

# список задач
curl -s "http://localhost:8000/users/1/tasks?status=new&limit=10&offset=0"

# обновить статус
curl -s -X PATCH http://localhost:8000/tasks/1/status \
  -H "Content-Type: application/json" \
  -d '{"status":"in_progress"}'

# статистика
curl -s http://localhost:8000/users/1/tasks/stats

# удалить задачу
curl -s -X DELETE http://localhost:8000/tasks/1
```

## Makefile

```bash
make up       # docker compose up --build
make down     # docker compose down
make test     # pytest
make lint     # ruff check + format check
make format   # автоформатирование
make migrate  # alembic upgrade head
```

## Линтер

```bash
make lint
```

Или по отдельности:

```bash
ruff check src tests main.py settings.py logs.py alembic
ruff format --check src tests main.py settings.py logs.py alembic
mypy src main.py settings.py logs.py tests
```
