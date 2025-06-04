from fastapi import FastAPI
import uvicorn

SERVICE_NAME = "upload-service"

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello from upload-service"}

@app.get("/health")
async def health() -> dict:
    """Health check endpoint."""
    return {"service": SERVICE_NAME, "status": "OK"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
