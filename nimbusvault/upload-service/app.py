from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello from upload-service"}


@app.get("/health")
async def health():
    return {"service": "upload-service", "status": "OK"}
