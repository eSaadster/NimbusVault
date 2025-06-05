from fastapi import FastAPI
import uvicorn
from pathlib import Path
import logging

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


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
