from fastapi import FastAPI
from pathlib import Path
import logging
import os

SERVICE_NAME = "storage-service"

# Persistent storage paths
VAULT_ROOT = Path("/vault-storage")
STORAGE_DIR = VAULT_ROOT / "files"

app = FastAPI()

logger = logging.getLogger(__name__)


def ensure_directories() -> None:
    """Ensure all persistent directories exist."""
    directories = [
        VAULT_ROOT / "files",
        VAULT_ROOT / "users",
        VAULT_ROOT / "shared",
        VAULT_ROOT / "trash",
    ]
    for dir in directories:
        dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Using persistent storage: {STORAGE_DIR}")


@app.on_event("startup")
async def startup_event() -> None:
    ensure_directories()


@app.get("/")
async def root():
    return {"message": "Hello from storage-service"}


@app.get("/health")
async def health():
    return {"status": "ok", "service": SERVICE_NAME}


@app.get("/health/detailed")
async def health_detailed():
    """Detailed health check including storage info."""
    storage_ok = Path("/vault-storage").exists()
    writable = os.access("/vault-storage", os.W_OK)
    return {
        "status": "ok" if storage_ok and writable else "error",
        "storage": {
            "mounted": storage_ok,
            "writable": writable,
            "path": "/vault-storage",
        },
    }
