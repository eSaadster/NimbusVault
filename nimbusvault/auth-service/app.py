from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello from auth-service"}


@app.get("/health")
async def health():
    return {"service": "auth-service", "status": "OK"}
