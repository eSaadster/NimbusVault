from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from passlib.context import CryptContext
from jose import jwt
import time
import uvicorn

from shared.logger import configure_logger, request_id_middleware

SERVICE_NAME = "auth-service"
SECRET_KEY = "secret"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_SECONDS = 3600

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
users = {}

logger = configure_logger(SERVICE_NAME)
app = FastAPI()

# Middleware for request ID tracking
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    return await request_id_middleware(request, call_next)

# Global error handler
@app.exception_handler(Exception)
async def exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("Auth service starting up")

# Models
class UserCredentials(BaseModel):
    username: str
    password: str

# Routes
@app.get("/")
async def root(request: Request):
    logger.info("Health check", extra={"requestId": request.state.request_id})
    return {"message": f"Hello from {SERVICE_NAME}"}

@app.get("/health")
async def health() -> dict:
    return {"service": SERVICE_NAME, "status": "OK"}

@app.post("/signup")
async def signup(creds: UserCredentials):
    if creds.username in users:
        raise HTTPException(status_code=400, detail="User already exists")
    users[creds.username] = pwd_context.hash(creds.password)
    logger.info(f"User {creds.username} signed up")
    return {"message": "User created"}

@app.post("/login")
async def login(creds: UserCredentials):
    hashed = users.get(creds.username)
    if not hashed or not pwd_context.verify(creds.password, hashed):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(creds.username)
    logger.info(f"User {creds.username} logged in")
    return {"access_token": token, "token_type": "bearer"}

# Token creation
def create_access_token(username: str):
    payload = {
        "sub": username,
        "exp": int(time.time()) + ACCESS_TOKEN_EXPIRE_SECONDS,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
