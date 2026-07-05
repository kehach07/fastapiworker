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


def to_bool(v):
    if isinstance(v, bool):
        return v
    return str(v).strip().lower() in ("true", "1", "yes", "on")


# -----------------------------
# YAML Layer
# -----------------------------
try:
    with open("config.development.yaml", "r") as f:
        data = yaml.safe_load(f)
        if data:
            config.update(data)
except FileNotFoundError:
    pass


# -----------------------------
# .env Layer
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

            # Alias
            if key == "NUM_WORKERS":
                config["workers"] = value
            else:
                config[key.lower()] = value

except FileNotFoundError:
    pass


# -----------------------------
# Assigned OS ENV Layer
# -----------------------------
config["port"] = 8166
config["debug"] = False
config["log_level"] = "error"

# Override with real environment variables if present
if "APP_PORT" in os.environ:
    config["port"] = os.environ["APP_PORT"]

if "APP_WORKERS" in os.environ:
    config["workers"] = os.environ["APP_WORKERS"]

if "APP_DEBUG" in os.environ:
    config["debug"] = os.environ["APP_DEBUG"]

if "APP_LOG_LEVEL" in os.environ:
    config["log_level"] = os.environ["APP_LOG_LEVEL"]

if "APP_API_KEY" in os.environ:
    config["api_key"] = os.environ["APP_API_KEY"]


@app.get("/")
def root():
    return {"message": "Config Service Running"}


@app.get("/effective-config")
def effective_config(set: list[str] = Query(default=[])):

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

    # Secret masking
    cfg["api_key"] = "****"

    return cfg