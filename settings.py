import os
from typing import Any

import yaml
from dotenv import load_dotenv

ENV_OVERRIDE_KEYS = (
    "POSTGRES_DB_USER",
    "POSTGRES_DB_PASSWORD",
    "POSTGRES_DB_HOST",
    "POSTGRES_DB_PORT",
    "POSTGRES_DB_NAME",
    "POSTGRES_TEST_DB_NAME",
    "POSTGRES_POOL_SIZE",
    "POSTGRES_MAX_OVERFLOW",
    "POSTGRES_POOL_RECYCLE_SEC",
    "FASTAPI_PORT",
    "FASTAPI_HOST",
    "FASTAPI_RELOAD",
    "LOG_FILE",
)


def load_config() -> dict[str, Any]:
    """
    Загружает конфигурацию:
        1. config.default.yaml — базовые настройки
        2. config.yaml — локальные переопределения (не секреты)
        3. .env / переменные окружения — наивысший приоритет (секреты и prod)
    """
    load_dotenv()

    base_dir = os.path.dirname(os.path.abspath(__file__))
    default_config_path = os.path.join(base_dir, "config", "config.default.yaml")
    custom_config_path = os.path.join(base_dir, "config", "config.yaml")

    def _load_yaml(path: str) -> dict[str, Any]:
        if not os.path.exists(path):
            return {}
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    config = _load_yaml(default_config_path)
    config.update(_load_yaml(custom_config_path))

    for key in ENV_OVERRIDE_KEYS:
        value = os.getenv(key)
        if value is not None and value != "":
            config[key] = value

    return config


CONFIG = load_config()


def config_loader(key: str, default: Any = None) -> Any:
    """
    Возвращает значение по ключу из конфигурации.
    Поддерживает вложенные ключи через точку, например:
        config_loader('database.host')

    :param key: ключ или путь через точку
    :param default: значение по умолчанию, если ключ не найден
    """
    value = CONFIG
    for part in key.split("."):
        if not isinstance(value, dict) or part not in value:
            return default
        value = value[part]

    return value
