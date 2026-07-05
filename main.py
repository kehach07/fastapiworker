from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import os
import yaml

app = FastAPI()

# ---------------- CORS ----------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- Defaults ----------------
config = {
    "port": 8000,
    "workers": 1,
    "debug": False,
    "log_level": "info",
    "api_key": "default-secret-000",
}

# ---------------- YAML ----------------
try:
    with open("config.development.yaml") as f:
        config.update(yaml.safe_load(f) or {})
except FileNotFoundError:
    pass

# ---------------- .env ----------------
try:
    with open(".env") as f:
        for line in f:
            line = line.strip()
            if not line or "=" not in line:
                continue

            k, v = line.split("=", 1)

            if k == "NUM_WORKERS":
                config["workers"] = int(v)
            else:
                config[k.lower()] = v
except FileNotFoundError:
    pass

# ---------------- OS ENV ----------------
mapping = {
    "APP_PORT": "port",
    "APP_DEBUG": "debug",
    "APP_LOG_LEVEL": "log_level",
    "APP_API_KEY": "api_key",
    "APP_WORKERS": "workers",
}

for env_key, cfg_key in mapping.items():
    if env_key in os.environ:
        config[cfg_key] = os.environ[env_key]


def to_bool(v):
    return str(v).lower() in ["true", "1", "yes", "on"]


@app.get("/")
def root():
    return {"message": "Config Service Running"}

@app.get("/effective-config")
def effective_config(set: list[str] = Query(default=[])):
    cfg = dict(config)

    for item in set:
        if "=" not in item:
            continue

        key, value = item.split("=", 1)

        if key in ("port", "workers"):
            cfg[key] = int(value)
        elif key == "debug":
            cfg[key] = value.lower() in ("true", "1", "yes", "on")
        else:
            cfg[key] = value

    cfg["port"] = int(cfg["port"])
    cfg["workers"] = int(cfg["workers"])
    cfg["debug"] = bool(cfg["debug"])
    cfg["api_key"] = "****"

    return cfg