from fastapi import FastAPI, Body
import os
import psycopg2

DATABASE_URL = os.environ.get("DATABASE_URL")

def get_conn():
    return psycopg2.connect(DATABASE_URL)

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello from metadata-service"}


@app.post("/metadata")
async def create_metadata(info: str = Body(..., embed=True)):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO metadata (info) VALUES (%s)", (info,))
    conn.commit()
    cur.close()
    conn.close()
    return {"status": "stored"}
