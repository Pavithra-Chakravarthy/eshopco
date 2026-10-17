
import os
from pathlib import Path

import yaml
from dotenv import dotenv_values
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

DEFAULTS = {
    "port": 8000,
    "workers": 1,
    "debug": False,
    "log_level": "info",
    "api_key": "default-secret",
}

BASE_DIR = Path(__file__).resolve().parent


def to_bool(value):
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "on"}


def coerce(key, value):
    if key in {"port", "workers"}:
        return int(value)
    if key == "debug":
        return to_bool(value)
    return str(value)


def normalize_key(key):
    key = key.strip().lower()

    aliases = {
        "app_port": "port",
        "app_workers": "workers",
        "num_workers": "workers",
        "app_debug": "debug",
        "app_log_level": "log_level",
        "app_api_key": "api_key",
    }
    return aliases.get(key, key)


@app.get("/")
def get_config(set: list[str] | None = Query(default=None)):
    config = DEFAULTS.copy()

    # YAML configuration
    config_path = BASE_DIR / "config.development.yaml"
    if config_path.exists():
        with config_path.open(encoding="utf-8") as file:
            yaml_config = yaml.safe_load(file) or {}

        for key, value in yaml_config.items():
            normalized = normalize_key(key)
            if normalized in config:
                config[normalized] = value

    # .env configuration
    env_file = dotenv_values(BASE_DIR / ".env")
    for key, value in env_file.items():
        if value is None:
            continue
        normalized = normalize_key(key)
        if normalized in config:
            config[normalized] = value

    # OS environment variables take precedence
    for key, value in os.environ.items():
        normalized = normalize_key(key)
        if normalized in config and (
            key.startswith("APP_") or key == "NUM_WORKERS"
        ):
            config[normalized] = value

    # Query overrides have the highest precedence
    for item in set or []:
        if "=" not in item:
            continue
        key, value = item.split("=", 1)
        normalized = normalize_key(key)
        if normalized in config:
            config[normalized] = value

    # Coerce types and mask secrets
    result = {
        key: coerce(key, value)
        for key, value in config.items()
    }
    result["api_key"] = "****"

    return result
