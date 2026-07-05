from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import os
import yaml

app = FastAPI()

# -----------------------------
# CORS
# -----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# Defaults
# -----------------------------
config = {
    "port": 8000,
    "workers": 1,
    "debug": False,
    "log_level": "info",
    "api_key": "default-secret-000",
}

# -----------------------------
# YAML (config.development.yaml)
# -----------------------------
try:
    with open("config.development.yaml", "r") as f:
        data = yaml.safe_load(f)
        if data:
            config.update(data)
except FileNotFoundError:
    pass

# -----------------------------
# .env
# -----------------------------
try:
    with open(".env", "r") as f:
        for line in f:
            line = line.strip()

            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)

            key = key.strip()
            value = value.strip()

            if key == "NUM_WORKERS":
                config["workers"] = value
            else:
                config[key.lower()] = value

except FileNotFoundError:
    pass

# -----------------------------
# OS Environment (APP_*)
# -----------------------------
mapping = {
    "APP_PORT": "port",
    "APP_WORKERS": "workers",
    "APP_DEBUG": "debug",
    "APP_LOG_LEVEL": "log_level",
    "APP_API_KEY": "api_key",
}

for env_key, cfg_key in mapping.items():
    if env_key in os.environ:
        config[cfg_key] = os.environ[env_key]


# -----------------------------
# Helpers
# -----------------------------
def to_bool(v):
    if isinstance(v, bool):
        return v

    return str(v).strip().lower() in (
        "true",
        "1",
        "yes",
        "on",
    )


# -----------------------------
# Root
# -----------------------------
@app.get("/")
def root():
    return {"message": "Config Service Running"}


# -----------------------------
# Effective Config
# -----------------------------
@app.get("/effective-config")
def effective_config(
    set: list[str] = Query(default=[]),
):
    cfg = dict(config)

    # CLI overrides
    for item in set:
        if "=" not in item:
            continue

        key, value = item.split("=", 1)

        if key == "port":
            cfg["port"] = int(value)

        elif key == "workers":
            cfg["workers"] = int(value)

        elif key == "debug":
            cfg["debug"] = to_bool(value)

        else:
            cfg[key] = value

    # Final type coercion
    cfg["port"] = int(cfg["port"])
    cfg["workers"] = int(cfg["workers"])
    cfg["debug"] = to_bool(cfg["debug"])
    cfg["log_level"] = str(cfg["log_level"])

    # Always mask secret
    cfg["api_key"] = "****"

    return cfg