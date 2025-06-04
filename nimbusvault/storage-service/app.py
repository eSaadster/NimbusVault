from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello from storage-service"}

@app.get("/health")
async def health():
    return {"status": "ok"}
