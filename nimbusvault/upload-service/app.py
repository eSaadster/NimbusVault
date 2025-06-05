from fastapi import FastAPI
import uvicorn
from pathlib import Path
import logging
import os

SERVICE_NAME = "upload-service"

app = FastAPI()

logger = logging.getLogger(__name__)

# Root persistent storage directory
VAULT_ROOT = Path("/vault-storage")
UPLOAD_DIR = VAULT_ROOT / "uploads"


@app.on_event("startup")
async def startup_event():
    """Ensure persistent directories exist."""
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Using persistent storage: {UPLOAD_DIR}")


@app.get("/health")
async def health() -> dict:
    """Health check endpoint."""
    return {"service": SERVICE_NAME, "status": "OK"}


@app.get("/health/detailed")
async def health_detailed() -> dict:
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


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
