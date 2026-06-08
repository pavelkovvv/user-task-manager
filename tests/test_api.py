import pytest
from httpx import AsyncClient
from tests.conftest import API_PREFIX, create_task, create_user


@pytest.mark.asyncio
async def test_create_user(client: AsyncClient, test_email: str) -> None:
    """Проверяет, что POST /users создаёт пользователя и возвращает ожидаемые поля"""
    response = await client.post(
        f"{API_PREFIX}/users",
        json={"email": test_email, "name": "Ivan"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == test_email
    assert data["name"] == "Ivan"
    assert isinstance(data["id"], int)
    assert data["created_at"]


@pytest.mark.asyncio
async def test_create_user_duplicate_email_returns_conflict(client: AsyncClient, test_email: str) -> None:
    """Проверяет, что повторная регистрация с тем же email возвращает 409 Conflict"""
    payload = {"email": test_email, "name": "Ivan"}

    first = await client.post(f"{API_PREFIX}/users", json=payload)
    second = await client.post(f"{API_PREFIX}/users", json=payload)

    assert first.status_code == 201
    assert second.status_code == 409


@pytest.mark.asyncio
async def test_create_task(client: AsyncClient, test_email: str) -> None:
    """Проверяет, что POST /users/{id}/tasks создаёт задачу со статусом new"""
    user = await create_user(client, test_email)

    response = await client.post(
        f"{API_PREFIX}/users/{user['id']}/tasks",
        json={
            "title": "Подготовить отчет",
            "description": "Собрать данные за неделю",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["user_id"] == user["id"]
    assert data["title"] == "Подготовить отчет"
    assert data["description"] == "Собрать данные за неделю"
    assert data["status"] == "new"


@pytest.mark.asyncio
async def test_list_user_tasks(client: AsyncClient, test_email: str) -> None:
    """Проверяет, что GET /users/{id}/tasks возвращает список задач и общее количество"""
    user = await create_user(client, test_email)
    for index in range(3):
        await create_task(client, user["id"], title=f"Задача {index}")

    response = await client.get(f"{API_PREFIX}/users/{user['id']}/tasks")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["items"]) == 3
    assert {task["title"] for task in data["items"]} == {"Задача 0", "Задача 1", "Задача 2"}


@pytest.mark.asyncio
async def test_filter_tasks_by_status(client: AsyncClient, test_email: str) -> None:
    """Проверяет фильтрацию списка задач по query-параметру status"""
    user = await create_user(client, test_email)
    done_task = await create_task(client, user["id"], title="Готово")
    await create_task(client, user["id"], title="Новая")

    patch_response = await client.patch(
        f"{API_PREFIX}/tasks/{done_task['id']}/status",
        json={"status": "done"},
    )
    assert patch_response.status_code == 200

    response = await client.get(
        f"{API_PREFIX}/users/{user['id']}/tasks",
        params={"status": "done"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["status"] == "done"
    assert data["items"][0]["title"] == "Готово"


@pytest.mark.asyncio
async def test_update_task_status(client: AsyncClient, test_email: str) -> None:
    """Проверяет, что PATCH /tasks/{id}/status обновляет статус задачи"""
    user = await create_user(client, test_email)
    task = await create_task(client, user["id"], title="В работе")

    response = await client.patch(
        f"{API_PREFIX}/tasks/{task['id']}/status",
        json={"status": "in_progress"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == task["id"]
    assert data["status"] == "in_progress"


@pytest.mark.asyncio
async def test_delete_task(client: AsyncClient, test_email: str) -> None:
    """Проверяет, что DELETE /tasks/{id} удаляет задачу и возвращает ответ с ok: true"""
    user = await create_user(client, test_email)
    task = await create_task(client, user["id"], title="Удалить")

    response = await client.delete(f"{API_PREFIX}/tasks/{task['id']}")

    assert response.status_code == 200
    assert response.json() == {"ok": True}

    list_response = await client.get(f"{API_PREFIX}/users/{user['id']}/tasks")
    assert list_response.json()["total"] == 0


@pytest.mark.asyncio
async def test_get_task_stats(client: AsyncClient, test_email: str) -> None:
    """Проверяет, что GET /users/{id}/tasks/stats возвращает счётчики по статусам"""
    user = await create_user(client, test_email)

    await create_task(client, user["id"], title="Новая")
    in_progress_task = await create_task(client, user["id"], title="В работе")
    done_task = await create_task(client, user["id"], title="Готово")
    cancelled_task = await create_task(client, user["id"], title="Отменена")

    await client.patch(f"{API_PREFIX}/tasks/{in_progress_task['id']}/status", json={"status": "in_progress"})
    await client.patch(f"{API_PREFIX}/tasks/{done_task['id']}/status", json={"status": "done"})
    await client.patch(f"{API_PREFIX}/tasks/{cancelled_task['id']}/status", json={"status": "cancelled"})

    response = await client.get(f"{API_PREFIX}/users/{user['id']}/tasks/stats")

    assert response.status_code == 200
    stats = response.json()
    assert stats == {
        "total": 4,
        "new": 1,
        "in_progress": 1,
        "done": 1,
        "cancelled": 1,
    }
