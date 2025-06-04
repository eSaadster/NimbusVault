from fastapi import FastAPI

app = FastAPI()


@app.get("/health")
async def health():
    return {"service": "metadata-service", "status": "OK"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=8003)
