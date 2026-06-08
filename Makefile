.PHONY: up down test lint format migrate

up:
	docker compose up --build

down:
	docker compose down

test:
	pytest tests/ -v

lint:
	ruff check src tests main.py settings.py logs.py alembic
	ruff format --check src tests main.py settings.py logs.py alembic
	mypy src main.py settings.py logs.py tests

format:
	ruff format src tests main.py settings.py logs.py alembic
	ruff check --fix src tests main.py settings.py logs.py alembic

migrate:
	alembic upgrade head
