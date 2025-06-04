from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from passlib.context import CryptContext
from jose import jwt
import time

SECRET_KEY = "secret"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_SECONDS = 3600

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
users = {}

class UserCredentials(BaseModel):
    username: str
    password: str

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello from auth-service"}


def create_access_token(username: str):
    payload = {
        "sub": username,
        "exp": int(time.time()) + ACCESS_TOKEN_EXPIRE_SECONDS,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


@app.post("/signup")
async def signup(creds: UserCredentials):
    if creds.username in users:
        raise HTTPException(status_code=400, detail="User already exists")
    users[creds.username] = pwd_context.hash(creds.password)
    return {"message": "User created"}


@app.post("/login")
async def login(creds: UserCredentials):
    hashed = users.get(creds.username)
    if not hashed or not pwd_context.verify(creds.password, hashed):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(creds.username)
    return {"access_token": token, "token_type": "bearer"}
