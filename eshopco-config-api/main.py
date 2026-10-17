import os
from pathlib import Path
from typing import Optional

import yaml
from dotenv import dotenv_values
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

BASE_DIR = Path(__file__).resolve().parent

DEFAULTS = {
    "port": 8000,
    "workers": 1,
    "debug": False,
    "log_level": "info",
    "api_key": "default-secret-000",
}

INTEGER_KEYS = {"port", "workers"}
BOOLEAN_TRUE = {"true", "1", "yes", "on"}


def coerce(key: str, value):
    """Convert known settings to their required types."""
    if key in INTEGER_KEYS:
        return int(value)
    if key == "debug":
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in BOOLEAN_TRUE
    if isinstance(value, str):
        return value
    return str(value)


def normalize_key(key: str) -> str:
    key = key.strip()
    if key.upper() == "NUM_WORKERS":
        return "workers"
    return key.lower()


def read_yaml_config() -> dict:
    env_name = os.environ.get("APP_ENV", "development")
    path = BASE_DIR / f"config.{env_name}.yaml"
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return {normalize_key(k): v for k, v in data.items()}


def read_dotenv_config() -> dict:
    # dotenv_values reads .env without merging it into os.environ.
    values = dotenv_values(BASE_DIR / ".env")
    return {
        normalize_key(k): v
        for k, v in values.items()
        if v is not None
    }


def read_os_config() -> dict:
    result = {}
    mapping = {
        "APP_PORT": "port",
        "APP_WORKERS": "workers",
        "APP_DEBUG": "debug",
        "APP_LOG_LEVEL": "log_level",
        "APP_API_KEY": "api_key",
    }
    for env_key, config_key in mapping.items():
        if env_key in os.environ:
            result[config_key] = os.environ[env_key]
    return result


def effective_config(overrides: Optional[list[str]] = None) -> dict:
    config = dict(DEFAULTS)
    config.update(read_yaml_config())
    config.update(read_dotenv_config())
    config.update(read_os_config())

    for item in overrides or []:
        # Split only on the first "=" so values may contain "=".
        if "=" not in item:
            continue
        key, value = item.split("=", 1)
        key = normalize_key(key)
        if key:
            config[key] = value

    # Coerce every key, including keys introduced by query overrides.
    config = {key: coerce(key, value) for key, value in config.items()}

    # Never return the actual secret.
    if "api_key" in config:
        config["api_key"] = "****"

    return config


app = FastAPI(title="eShopCo Config Health Check")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"status": "ok", "endpoint": "/effective-config"}


@app.get("/effective-config")
def get_effective_config(set: Optional[list[str]] = Query(default=None)):
    return effective_config(set)
