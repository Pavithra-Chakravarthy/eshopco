
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

ALIASES = {
    "app_port": "port",
    "app_workers": "workers",
    "num_workers": "workers",
    "app_debug": "debug",
    "app_log_level": "log_level",
    "app_api_key": "api_key",
}


def normalize_key(key):
    key = key.strip().lower()
    return ALIASES.get(key, key)


def to_bool(value):
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {
        "true", "1", "yes", "on"
    }


def coerce(key, value):
    if key in {"port", "workers"}:
        return int(value)
    if key == "debug":
        return to_bool(value)
    return str(value)


def load_yaml_config():
    config_file = BASE_DIR / "config.development.yaml"
    if not config_file.exists():
        return {}

    with config_file.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file) or {}

    return {
        normalize_key(key): value
        for key, value in data.items()
        if normalize_key(key) in DEFAULTS
    }


def load_dotenv_config():
    data = dotenv_values(BASE_DIR / ".env")
    return {
        normalize_key(key): value
        for key, value in data.items()
        if value is not None and normalize_key(key) in DEFAULTS
    }


def load_os_config():
    result = {}

    for key, value in os.environ.items():
        normalized = normalize_key(key)

        if normalized not in DEFAULTS:
            continue

        # Only use the specified application environment variables.
        if key.startswith("APP_") or key == "NUM_WORKERS":
            result[normalized] = value

    return result


@app.get("/")
def get_config(set: list[str] | None = Query(default=None)):
    # Precedence: defaults < YAML < .env < OS environment < CLI overrides.
    config = DEFAULTS.copy()
    config.update(load_yaml_config())
    config.update(load_dotenv_config())
    config.update(load_os_config())

    # Apply each query override to its own key only.
    for item in set or []:
        if "=" not in item:
            continue

        key, value = item.split("=", 1)
        key = normalize_key(key)

        if key in config:
            config[key] = value

    # Convert values to the expected types.
    result = {
        key: coerce(key, value)
        for key, value in config.items()
    }

    # Never expose the real API key.
    result["api_key"] = "****"

    return result
