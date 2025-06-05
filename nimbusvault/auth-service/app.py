from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from jwt_utils import create_token

users = {"admin": "password"}

class Credentials(BaseModel):
    username: str
    password: str

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello from auth-service"}


@app.post("/login")
async def login(creds: Credentials):
    if users.get(creds.username) != creds.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_token({"sub": creds.username})
    return {"token": token}


@app.post("/register")
async def register(creds: Credentials):
    if creds.username in users:
        raise HTTPException(status_code=400, detail="User already exists")
    users[creds.username] = creds.password
    token = create_token({"sub": creds.username})
    return {"token": token}
