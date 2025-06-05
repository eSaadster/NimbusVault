import os
import sys
import time
from pathlib import Path
from datetime import datetime
from typing import Dict

from fastapi import FastAPI, Depends, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import httpx
import uvicorn
import logging

# Add shared to sys.path
BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR / 'shared'))

# Import shared modules with fallbacks
try:
    from auth_middleware import AuthMiddleware, get_current_user
    from logger import configure_logger, request_id_middleware
    from storage_utils import save_file
except ImportError as e:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("upload-service")

    class AuthMiddleware:
        def __init__(self, app, public_key=None): pass

    async def get_current_user():
        return {"user": "anonymous"}

    async def request_id_middleware(request: Request, call_next):
        request.state.request_id = "fallback-id"
        return await call_next(request)

    def save_file(file_path: str, data: bytes):
        with open(file_path, 'wb') as f:
            f.write(data)
else:
    logger = configure_logger("upload-service")

# Load public key for auth middleware
try:
    PUBLIC_KEY_PATH = BASE_DIR / 'auth-service' / 'keys' / 'public.pem'
    PUBLIC_KEY = PUBLIC_KEY_PATH.read_text() if PUBLIC_KEY_PATH.exists() else None
    if not PUBLIC_KEY:
        print("Warning: Public key not found, authentication will be disabled")
except Exception as e:
    print(f"Warning loading public key: {e}")
    PUBLIC_KEY = None

SERVICE_NAME = "upload-service"
METADATA_SERVICE_URL = os.getenv("METADATA_SERVICE_URL", "http://metadata-service:8003/metadata")
VAULT_ROOT = Path("/vault-storage")
UPLOAD_DIR = VAULT_ROOT / "uploads"

app = FastAPI()

# Ensure upload directory exists
@app.on_event("startup")
async def startup_event():
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Using persistent storage: {UPLOAD_DIR}")
    logger.info(f"{SERVICE_NAME} starting up")

# Apply middleware
if PUBLIC_KEY:
    app.add_middleware(AuthMiddleware, public_key=PUBLIC_KEY)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    return await request_id_middleware(request, call_next)

# Prometheus metrics
REQUEST_COUNT = Counter("upload_requests_total", "Total HTTP requests", ["method", "endpoint", "http_status"])
REQUEST_LATENCY = Histogram("upload_request_latency_seconds", "Latency of HTTP requests", ["endpoint"])

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

@app.exception_handler(Exception)
async def exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})

# Health & system routes
@app.get("/")
async def root(request: Request):
    logger.info("Health check", extra={"requestId": getattr(request.state, 'request_id', 'unknown')})
    return {"message": f"Hello from {SERVICE_NAME}"}

@app.get("/health")
async def health() -> dict:
    return {"service": SERVICE_NAME, "status": "OK"}

@app.get("/health/live")
async def health_live():
    return {"status": "ok"}

@app.get("/health/ready")
async def health_ready():
    return {"status": "ok"}

@app.get("/health/detailed")
async def health_detailed() -> dict:
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

@app.get("/public")
async def public_route():
    return {"message": "public endpoint - no authentication required"}

@app.get("/protected")
async def protected_route(user=Depends(get_current_user)):
    return {"message": "protected endpoint", "user": user}

@app.get("/log")
async def log_route(request: Request):
    logger.info(
        f"Received request from {request.client.host} to {request.url.path}",
        extra={"requestId": getattr(request.state, 'request_id', 'unknown')}
    )
    return {"message": "Request logged"}

@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    request: Request = None,
    user=Depends(get_current_user)
):
    try:
        contents = await file.read()
        request_id = getattr(request.state, 'request_id', 'unknown') if request else 'unknown'
        logger.info(f"Received file {file.filename} from {user}", extra={"requestId": request_id})

        safe_filename = "".join(c for c in file.filename if c.isalnum() or c in "._- ")
        file_path = UPLOAD_DIR / safe_filename
        save_file(str(file_path), contents)

        metadata = {
            "filename": safe_filename,
            "uploaded_by": user.get("user", "unknown") if isinstance(user, dict) else str(user),
            "timestamp": datetime.utcnow().isoformat(),
            "file_size": len(contents),
            "content_type": file.content_type,
            "original_filename": file.filename
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(METADATA_SERVICE_URL, json=metadata)
                response.raise_for_status()
                metadata_response = response.json()
            return {
                "status": "success",
                "filename": safe_filename,
                "original_filename": file.filename,
                "size": len(contents),
                "uploaded_by": metadata["uploaded_by"],
                "metadata_response": metadata_response,
            }

        except Exception as exc:
            logger.exception("Failed to submit metadata", extra={"requestId": request_id})
            return {
                "status": "partial_success",
                "filename": safe_filename,
                "size": len(contents),
                "uploaded_by": metadata["uploaded_by"],
                "warning": "File uploaded but metadata submission failed",
                "error": str(exc),
            }

    except Exception as exc:
        logger.exception(f"Failed to upload file {file.filename}", extra={"requestId": getattr(request.state, 'request_id', 'unknown') if request else 'unknown'})
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": "File upload failed", "error": str(exc)}
        )

@app.get("/uploads")
async def list_uploads(user=Depends(get_current_user)):
    try:
        files = [
            {
                "filename": f.name,
                "size": f.stat().st_size,
                "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat()
            }
            for f in UPLOAD_DIR.iterdir() if f.is_file()
        ]
        logger.info(f"Listed {len(files)} uploads for user {user}")
        return {"uploads": files, "count": len(files)}

    except Exception as exc:
        logger.error(f"Failed to list uploads: {exc}")
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to list uploads", "details": str(exc)}
        )

@app.delete("/uploads/{filename}")
async def delete_upload(filename: str, user=Depends(get_current_user)):
    try:
        file_path = UPLOAD_DIR / filename
        if file_path.exists() and file_path.is_file():
            file_path.unlink()
            logger.info(f"File deleted: {filename} by user {user}")
            return {"message": f"File {filename} deleted successfully"}
        else:
            return JSONResponse(status_code=404, content={"error": "File not found"})
    except Exception as exc:
        logger.error(f"Failed to delete file {filename}: {exc}")
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to delete file", "details": str(exc)}
        )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8002))
    uvicorn.run(app, host="0.0.0.0", port=port)
