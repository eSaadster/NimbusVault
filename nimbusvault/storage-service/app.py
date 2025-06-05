import os
import sys
import time
import logging
from pathlib import Path
from typing import Dict, List
from fastapi import FastAPI, Request, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import uvicorn

# Constants
SERVICE_NAME = "storage-service"
VAULT_ROOT = Path("/vault-storage")
STORAGE_DIR = VAULT_ROOT / "files"

# Add shared to path
BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR / "shared"))

# Attempt shared imports
try:
    from auth_middleware import AuthMiddleware, get_current_user
    from logger import configure_logger
    from storage_utils import save_file
except ImportError as e:
    print(f"Warning: Could not import shared modules: {e}")
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(SERVICE_NAME)

    class AuthMiddleware:
        def __init__(self, app, public_key=None): pass

    async def get_current_user():
        return {"user": "anonymous"}

    def save_file(file_path: str, data: bytes):
        with open(file_path, 'wb') as f:
            f.write(data)
        print(f"Saved {file_path}")
else:
    logger = configure_logger(SERVICE_NAME)

# Load public key
try:
    PUBLIC_KEY_PATH = BASE_DIR / 'auth-service' / 'keys' / 'public.pem'
    PUBLIC_KEY = PUBLIC_KEY_PATH.read_text() if PUBLIC_KEY_PATH.exists() else None
    if not PUBLIC_KEY:
        print("Warning: Public key not found, authentication will be disabled")
except Exception as e:
    print(f"Warning loading public key: {e}")
    PUBLIC_KEY = None

# Init FastAPI app
app = FastAPI()

# Middleware setup
if PUBLIC_KEY:
    app.add_middleware(AuthMiddleware, public_key=PUBLIC_KEY)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure directories
def ensure_directories():
    for dir in [VAULT_ROOT / "files", VAULT_ROOT / "users", VAULT_ROOT / "shared", VAULT_ROOT / "trash"]:
        dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Using persistent storage: {STORAGE_DIR}")

@app.on_event("startup")
async def startup_event():
    ensure_directories()

# Prometheus metrics
REQUEST_COUNT = Counter("storage_requests_total", "Total HTTP requests", ["method", "endpoint", "http_status"])
REQUEST_LATENCY = Histogram("storage_request_latency_seconds", "Latency of HTTP requests", ["endpoint"])

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    REQUEST_COUNT.labels(request.method, request.url.path, response.status_code).inc()
    REQUEST_LATENCY.labels(request.url.path).observe(duration)
    return response

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

# Health routes
@app.get("/")
async def root():
    logger.info("Health check hit")
    return {"message": f"Hello from {SERVICE_NAME}"}

@app.get("/health")
async def health():
    return {"status": "ok", "service": SERVICE_NAME}

@app.get("/health/live")
async def health_live():
    return {"status": "ok"}

@app.get("/health/ready")
async def health_ready():
    return {"status": "ok"}

@app.get("/health/detailed")
async def health_detailed():
    """Detailed health check including storage info."""
    storage_ok = VAULT_ROOT.exists()
    writable = os.access(VAULT_ROOT, os.W_OK)
    return {
        "status": "ok" if storage_ok and writable else "error",
        "storage": {
            "mounted": storage_ok,
            "writable": writable,
            "path": str(VAULT_ROOT),
        },
    }

# In-memory metadata store
stored_metadata: List[Dict] = []

# Public/protected endpoints
@app.get("/public")
async def public_route():
    return {"message": "public endpoint - no authentication required"}

@app.get("/protected")
async def protected_route(user=Depends(get_current_user)):
    return {"message": "protected endpoint", "user": user}

# Metadata routes
@app.post("/store")
async def store_metadata(metadata: Dict, user=Depends(get_current_user)):
    metadata_with_user = {
        **metadata,
        "stored_by": user.get("user", "unknown"),
        "timestamp": str(time.time())
    }
    stored_metadata.append(metadata_with_user)
    logger.info(f"Metadata stored: {metadata_with_user}")
    return {"result": "saved", "metadata_id": len(stored_metadata) - 1}

@app.get("/store")
async def get_stored_metadata(user=Depends(get_current_user)):
    logger.info(f"Metadata retrieved by user: {user}")
    return {"metadata": stored_metadata}

# File routes
@app.post("/files")
async def store_file(file: UploadFile = File(...), user=Depends(get_current_user)):
    try:
        data = await file.read()
        safe_filename = "".join(c for c in file.filename if c.isalnum() or c in "._- ")
        file_path = STORAGE_DIR / safe_filename
        save_file(str(file_path), data)
        file_metadata = {
            "filename": safe_filename,
            "original_filename": file.filename,
            "size": len(data),
            "content_type": file.content_type,
            "uploaded_by": user.get("user", "unknown"),
            "file_path": str(file_path)
        }
        stored_metadata.append(file_metadata)
        logger.info(f"File saved: {safe_filename} by user: {user}")
        return {"filename": safe_filename, "size": len(data), "message": "File uploaded successfully"}
    except Exception as e:
        logger.error(f"Error storing file: {e}")
        return {"error": "Failed to store file", "details": str(e)}

@app.get("/files")
async def list_files(user=Depends(get_current_user)):
    try:
        files = [f.name for f in STORAGE_DIR.iterdir() if f.is_file()]
        logger.info(f"Files listed by user: {user}")
        return {"files": files}
    except Exception as e:
        logger.error(f"Error listing files: {e}")
        return {"error": "Failed to list files", "files": []}

@app.delete("/files/{filename}")
async def delete_file(filename: str, user=Depends(get_current_user)):
    try:
        file_path = STORAGE_DIR / filename
        if file_path.exists() and file_path.is_file():
            file_path.unlink()
            logger.info(f"File deleted: {filename} by user: {user}")
            return {"message": f"File {filename} deleted successfully"}
        else:
            return {"error": "File not found"}
    except Exception as e:
        logger.error(f"Error deleting file: {e}")
        return {"error": "Failed to delete file", "details": str(e)}

# Startup runner
if __name__ == "__main__":
    logger.info("Storage service started")
    port = int(os.environ.get("PORT", 8004))
    uvicorn.run(app, host="0.0.0.0", port=port)
