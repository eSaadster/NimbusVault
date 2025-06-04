from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
async def health() -> dict:
    return {"service": "storage-service", "status": "OK"}
