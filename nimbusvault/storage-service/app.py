from fastapi import FastAPI
import uvicorn
import os

SERVICE_NAME = "storage-service"

app = FastAPI()

@app.get("/")
async def root():
    return {"message": f"Hello from {SERVICE_NAME}"}

@app.get("/health")
async def health() -> dict:
    """Health check endpoint."""
    return {"service": SERVICE_NAME, "status": "OK"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

