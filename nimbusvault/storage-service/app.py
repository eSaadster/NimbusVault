from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os

SERVICE_NAME = "storage-service"

app = FastAPI()

# Enable CORS for all origins, methods, and headers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": f"Hello from {SERVICE_NAME}"}

@app.get("/health")
async def health() -> dict:
    """Health check endpoint."""
    return {"service": SERVICE_NAME, "status": "OK"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8004))
    uvicorn.run(app, host="0.0.0.0", port=port)
