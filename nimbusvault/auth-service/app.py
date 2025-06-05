@app.get("/", tags=["Health"])
async def root() -> dict:
    """Root endpoint returning a greeting."""
    return {'message': f'Hello from {SERVICE_NAME}', 'version': '1.0.0'}

@app.get("/health", tags=["Health"])
async def health() -> dict:
    """Basic health check endpoint."""
    return {"service": SERVICE_NAME, "status": "OK", "timestamp": datetime.utcnow().isoformat()}

@app.get("/health/live", tags=["Health"])
async def health_live() -> dict:
    """Kubernetes liveness probe."""
    return {"status": "ok"}

@app.get("/health/ready", tags=["Health"])
async def health_ready() -> dict:
    """Kubernetes readiness probe."""
    return {"status": "ok", "users_count": len(user_store)}

@app.get("/health/detailed", tags=["Health"])
async def health_detailed() -> dict:
    """Detailed health check including storage and algorithm info."""
    storage_path = Path("/vault-storage")
    storage_ok = storage_path.exists()
    writable = os.access(storage_path, os.W_OK)
    
    return {
        "status": "ok" if storage_ok and writable else "error",
        "storage": {
            "mounted": storage_ok,
            "writable": writable,
            "path": str(storage_path),
        },
        "users_count": len(user_store),
        "algorithm": ALGORITHM,
        "service": SERVICE_NAME
    }
