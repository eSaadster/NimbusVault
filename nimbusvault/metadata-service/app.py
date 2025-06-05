import os
import sys
import time
import psycopg2
from pathlib import Path
from datetime import datetime
from fastapi import FastAPI, Request, Depends
from fastapi.responses import JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
import uvicorn

# Add shared directory to path
BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR / 'shared'))

# Attempt to import shared modules
try:
    from auth_middleware import AuthMiddleware, get_current_user
    from logger import configure_logger, request_id_middleware
    from config import SERVICE_NAME, DATABASE_URL, DB_CONNECT_TIMEOUT
except ImportError as e:
    SERVICE_NAME = "metadata-service"
    DATABASE_URL = os.getenv("DATABASE_URL", "")
    DB_CONNECT_TIMEOUT = 30

    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(SERVICE_NAME)

    async def request_id_middleware(request: Request, call_next):
        request.state.request_id = "fallback-id"
        return await call_next(request)

    class AuthMiddleware:
        def __init__(self, app, public_key=None):
            pass

    async def get_current_user():
        return {"user": "anonymous"}
else:
    logger = configure_logger(SERVICE_NAME)

# Attempt to load public key
try:
    PUBLIC_KEY_PATH = BASE_DIR / 'auth-service' / 'keys' / 'public.pem'
    PUBLIC_KEY = PUBLIC_KEY_PATH.read_text() if PUBLIC_KEY_PATH.exists() else None
    if not PUBLIC_KEY:
        logger.warning("Public key not found, authentication will be disabled")
except Exception as e:
    logger.warning(f"Could not load public key: {e}")
    PUBLIC_KEY = None

app = FastAPI()

# Middleware
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
REQUEST_COUNT = Counter("metadata_requests_total", "Total HTTP requests", ["method", "endpoint", "http_status"])
REQUEST_LATENCY = Histogram("metadata_request_latency_seconds", "Latency of HTTP requests", ["endpoint"])
DB_CONNECTIONS = Gauge("metadata_db_connections", "Number of active database connections")

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

@app.on_event("startup")
async def startup_event():
    logger.info(f"{SERVICE_NAME} starting up")
    if not DATABASE_URL:
        logger.error("DATABASE_URL not set")
        return
    try:
        with psycopg2.connect(DATABASE_URL, connect_timeout=DB_CONNECT_TIMEOUT) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS metadata (
                        id SERIAL PRIMARY KEY,
                        filename TEXT NOT NULL,
                        uploaded_by TEXT NOT NULL,
                        timestamp TIMESTAMPTZ NOT NULL
                    );
                """)
                conn.commit()
                logger.info("Ensured metadata table exists.")
    except Exception as e:
        logger.error(f"Database init failed: {e}", exc_info=True)

# Database check for health
def check_db():
    try:
        conn = psycopg2.connect(DATABASE_URL, connect_timeout=1)
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.fetchone()
        cur.execute("SELECT count(*) FROM pg_stat_activity")
        DB_CONNECTIONS.set(cur.fetchone()[0])
        cur.close()
        conn.close()
        return True
    except Exception:
        return False

# Pydantic model
class Metadata(BaseModel):
    filename: str
    uploaded_by: str
    timestamp: datetime

# Routes
@app.get("/")
async def root(request: Request):
    logger.info("Root ping", extra={"requestId": getattr(request.state, 'request_id', 'unknown')})
    return {"message": f"Hello from {SERVICE_NAME}"}

@app.get("/health")
async def health():
    return {"service": SERVICE_NAME, "status": "OK"}

@app.get("/health/live")
async def health_live():
    return {"status": "ok"}

@app.get("/health/ready")
async def health_ready():
    if check_db():
        return {"status": "ok"}
    return JSONResponse(status_code=503, content={"status": "error", "database": "unreachable"})

@app.get("/health/detailed")
async def health_detailed() -> dict:
    """Detailed health check including storage and DB info."""
    storage_ok = Path("/vault-storage").exists()
    writable = os.access("/vault-storage", os.W_OK)
    db_ok = check_db()
    status = "ok" if storage_ok and writable and db_ok else "error"
    return {
        "status": status,
        "storage": {
            "mounted": storage_ok,
            "writable": writable,
            "path": "/vault-storage",
        },
        "dependencies": {
            "database": db_ok
        }
    }

@app.get("/public")
async def public_route():
    return {"message": "public endpoint - no authentication required"}

@app.get("/protected")
async def protected_route(user=Depends(get_current_user)):
    return {"message": "protected endpoint", "user": user}

@app.post("/metadata")
async def create_metadata(metadata: Metadata, user=Depends(get_current_user)):
    if not DATABASE_URL:
        logger.error("DATABASE_URL not set")
        return JSONResponse(status_code=500, content={"detail": "DATABASE_URL not set"})

    try:
        with psycopg2.connect(DATABASE_URL, connect_timeout=DB_CONNECT_TIMEOUT) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO metadata (filename, uploaded_by, timestamp) VALUES (%s, %s, %s) RETURNING id",
                    (metadata.filename, metadata.uploaded_by, metadata.timestamp),
                )
                new_id = cur.fetchone()[0]
                conn.commit()
        logger.info(f"Metadata inserted: {metadata.filename} by user: {user}")
        return {
            "id": new_id,
            "filename": metadata.filename,
            "uploaded_by": metadata.uploaded_by,
            "timestamp": metadata.timestamp.isoformat(),
        }
    except Exception as e:
        logger.error(f"Database error: {e}", exc_info=True)
        return JSONResponse(status_code=500, content={"detail": "Database error"})

@app.get("/metadata")
async def list_metadata(user=Depends(get_current_user)):
    if not DATABASE_URL:
        logger.error("DATABASE_URL not set")
        return JSONResponse(status_code=500, content={"detail": "DATABASE_URL not set"})

    try:
        with psycopg2.connect(DATABASE_URL, connect_timeout=DB_CONNECT_TIMEOUT) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, filename, uploaded_by, timestamp FROM metadata ORDER BY timestamp DESC")
                rows = cur.fetchall()
        return {
            "metadata": [
                {
                    "id": row[0],
                    "filename": row[1],
                    "uploaded_by": row[2],
                    "timestamp": row[3].isoformat() if row[3] else None,
                }
                for row in rows
            ]
        }
    except Exception as e:
        logger.error(f"Database error: {e}", exc_info=True)
        return JSONResponse(status_code=500, content={"detail": "Database error"})

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003)
