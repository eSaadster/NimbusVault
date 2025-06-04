from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
import psycopg2
import uvicorn

from shared.logger import configure_logger, request_id_middleware
from config import SERVICE_NAME, DATABASE_URL, DB_CONNECT_TIMEOUT

logger = configure_logger(SERVICE_NAME)
app = FastAPI()

# Middleware
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

# Pydantic model
class Metadata(BaseModel):
    filename: str
    uploaded_by: str
    timestamp: datetime

# Routes
@app.get("/")
async def root(request: Request):
    logger.info("Health check", extra={"requestId": request.state.request_id})
    return {"message": f"Hello from {SERVICE_NAME}"}

@app.get("/health")
async def health() -> dict:
    return {"service": SERVICE_NAME, "status": "OK"}

@app.post("/metadata")
async def create_metadata(metadata: Metadata):
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

        logger.info(f"Metadata inserted: {metadata.filename}")
        return JSONResponse(status_code=200, content={
            "id": new_id,
            "filename": metadata.filename,
            "uploaded_by": metadata.uploaded_by,
            "timestamp": metadata.timestamp.isoformat(),
        })

    except Exception as e:
        logger.error(f"Database error: {e}", exc_info=True)
        return JSONResponse(status_code=500, content={"detail": "Database error"})

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003)
