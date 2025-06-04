import sys
from pathlib import Path
from fastapi import FastAPI, Depends, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
import os
import psycopg2
import uvicorn

# Add shared directory to path for imports
BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR / 'shared'))

# Import shared modules
try:
    from auth_middleware import AuthMiddleware, get_current_user
    from logger import configure_logger, request_id_middleware
    from config import SERVICE_NAME, DATABASE_URL, DB_CONNECT_TIMEOUT
except ImportError as e:
    # Fallback if shared modules don't exist
    print(f"Warning: Could not import shared modules: {e}")
    SERVICE_NAME = "metadata-service"
    DATABASE_URL = os.getenv("DATABASE_URL")
    DB_CONNECT_TIMEOUT = 30
    
    # Simple logger fallback
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(SERVICE_NAME)
    
    async def request_id_middleware(request: Request, call_next):
        request.state.request_id = "fallback-id"
        return await call_next(request)
    
    # Simple auth middleware fallback
    class AuthMiddleware:
        def __init__(self, app, public_key=None):
            pass
    
    async def get_current_user():
        return {"user": "anonymous"}
else:
    logger = configure_logger(SERVICE_NAME)

# Load public key for JWT authentication
try:
    PUBLIC_KEY_PATH = BASE_DIR / 'auth-service' / 'keys' / 'public.pem'
    if PUBLIC_KEY_PATH.exists():
        with open(PUBLIC_KEY_PATH) as f:
            PUBLIC_KEY = f.read()
    else:
        PUBLIC_KEY = None
        logger.warning("Public key not found, authentication will be disabled")
except Exception as e:
    logger.warning(f"Could not load public key: {e}")
    PUBLIC_KEY = None

app = FastAPI()

# Add authentication middleware if public key is available
if PUBLIC_KEY:
    app.add_middleware(AuthMiddleware, public_key=PUBLIC_KEY)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    return await request_id_middleware(request, call_next)

@app.exception_handler(Exception)
async def exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})

@app.on_event("startup")
async def startup_event():
    logger.info(f"{SERVICE_NAME} starting up")
    if not DATABASE_URL:
        logger.error("DATABASE_URL not set. Cannot connect to database.")
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

# Pydantic models
class Metadata(BaseModel):
    filename: str
    uploaded_by: str
    timestamp: datetime

# Routes
@app.get("/")
async def root(request: Request):
    logger.info("Health check", extra={"requestId": getattr(request.state, 'request_id', 'unknown')})
    return {"message": f"Hello from {SERVICE_NAME}"}

@app.get("/health")
async def health() -> dict:
    return {"service": SERVICE_NAME, "status": "OK"}

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
        return JSONResponse(status_code=200, content={
            "id": new_id,
            "filename": metadata.filename,
            "uploaded_by": metadata.uploaded_by,
            "timestamp": metadata.timestamp.isoformat(),
        })

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

        metadata_list = [
            {
                "id": row[0],
                "filename": row[1],
                "uploaded_by": row[2],
                "timestamp": row[3].isoformat() if row[3] else None,
            }
            for row in rows
        ]

        return JSONResponse(status_code=200, content={"metadata": metadata_list})

    except Exception as e:
        logger.error(f"Database error: {e}", exc_info=True)
        return JSONResponse(status_code=500, content={"detail": "Database error"})

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003)