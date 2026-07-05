from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import os
import yaml

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def to_bool(v):
    if isinstance(v, bool):
        return v
    return str(v).strip().lower() in ("true", "1", "yes", "on")


@app.get("/")
def root():
    return {"message": "Config Service Running"}


@app.get("/effective-config")
def effective_config(set: list[str] = Query(default=[])):
    # -----------------------------
    # 1. Defaults
    # -----------------------------
    cfg = {
        "port": 8000,
        "workers": 1,
        "debug": False,
        "log_level": "info",
        "api_key": "default-secret-000",
    }

    # -----------------------------
    # 2. YAML
    # -----------------------------
    try:
        with open("config.development.yaml") as f:
            data = yaml.safe_load(f) or {}
            cfg.update(data)
    except FileNotFoundError:
        pass

    # -----------------------------
    # 3. .env
    # -----------------------------
    try:
        with open(".env") as f:
            for line in f:
                line = line.strip()

                if not line or line.startswith("#") or "=" not in line:
                    continue

                key, value = line.split("=", 1)

                if key == "NUM_WORKERS":
                    cfg["workers"] = value
                else:
                    cfg[key.lower()] = value
    except FileNotFoundError:
        pass

    # -----------------------------
    # 4. OS ENV
    # -----------------------------
    cfg["port"] = os.getenv("APP_PORT", "8166")
    cfg["debug"] = os.getenv("APP_DEBUG", "false")
    cfg["log_level"] = os.getenv("APP_LOG_LEVEL", "error")

    if "APP_WORKERS" in os.environ:
        cfg["workers"] = os.environ["APP_WORKERS"]

    if "APP_API_KEY" in os.environ:
        cfg["api_key"] = os.environ["APP_API_KEY"]

    # -----------------------------
    # 5. CLI overrides
    # -----------------------------
    for item in set:
        if "=" not in item:
            continue

        key, value = item.split("=", 1)

        if key == "port":
            cfg["port"] = value

        elif key == "workers":
            cfg["workers"] = value

        elif key == "debug":
            cfg["debug"] = value

        else:
            cfg[key] = value

    # -----------------------------
    # Final type coercion
    # -----------------------------
    cfg["port"] = int(cfg["port"])
    cfg["workers"] = int(cfg["workers"])
    cfg["debug"] = to_bool(cfg["debug"])
    cfg["log_level"] = str(cfg["log_level"])

    # Mask secret
    cfg["api_key"] = "****"

    return cfg