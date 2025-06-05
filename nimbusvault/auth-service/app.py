from fastapi import FastAPI
import uvicorn
from pathlib import Path
import os

SERVICE_NAME = "auth-service"

app = FastAPI()


@app.get("/")
async def root() -> dict:
    """Root endpoint returning a greeting."""
    return {"message": f"Hello from {SERVICE_NAME}"}


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
    uvicorn.run(app, host="0.0.0.0", port=8001)
