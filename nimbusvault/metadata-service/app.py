import os
import time
import psycopg2
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    generate_latest,
    CONTENT_TYPE_LATEST,
)

app = FastAPI()

DATABASE_URL = os.getenv("DATABASE_URL", "")

REQUEST_COUNT = Counter(
    "metadata_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "http_status"],
)
REQUEST_LATENCY = Histogram(
    "metadata_request_latency_seconds",
    "Latency of HTTP requests",
    ["endpoint"],
)
DB_CONNECTIONS = Gauge(
    "metadata_db_connections",
    "Number of active database connections",
)


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

@app.get("/")
async def root():
    return {"message": "Hello from metadata-service"}


@app.get("/health/live")
async def health_live():
    return {"status": "ok"}


@app.get("/health/ready")
async def health_ready():
    if check_db():
        return {"status": "ok"}
    return JSONResponse(status_code=503, content={"status": "error", "database": "unreachable"})


@app.get("/health/detailed")
async def health_detailed():
    db_ok = check_db()
    status = "ok" if db_ok else "error"
    return JSONResponse(status_code=200 if db_ok else 503, content={"status": status, "dependencies": {"database": db_ok}})
