import os
import time
from pathlib import Path
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, Request, Depends, Response
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from jose import jwt, JWTError
from passlib.context import CryptContext
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import uvicorn

# Import custom utilities
try:
    from jwt_utils import create_token as jwt_utils_create_token
except ImportError:
    jwt_utils_create_token = None

try:
    from shared.logger import configure_logger, request_id_middleware
except ImportError:
    # Fallback logger if shared logger is not available
    import logging
    def configure_logger(name):
        logger = logging.getLogger(name)
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger
    
    async def request_id_middleware(request, call_next):
        response = await call_next(request)
        return response

SERVICE_NAME = "auth-service"
BASE_DIR = Path(__file__).resolve().parent

# RSA Key loading with fallback
try:
    with open(BASE_DIR / 'keys/private.pem') as f:
        PRIVATE_KEY = f.read()
    with open(BASE_DIR / 'keys/public.pem') as f:
        PUBLIC_KEY = f.read()
    ALGORITHM = "RS256"
except FileNotFoundError:
    # Fallback to symmetric key for development
    PRIVATE_KEY = PUBLIC_KEY = os.getenv("JWT_SECRET", "fallback-secret-key")
    ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_SECONDS = 3600

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# In-memory storage (replace with database in production)
users = {"admin": "password"}  # Legacy simple storage
user_store = {}  # Enhanced user storage
next_id = 1

# Rate limiting
RATE_LIMIT = {}
RATE_LIMIT_WINDOW = 60
RATE_LIMIT_COUNT = 5

# Initialize logger
logger = configure_logger(SERVICE_NAME)

# FastAPI app
app = FastAPI(title="Authentication Service", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics
REQUEST_COUNT = Counter(
    "auth_requests_total", "Total HTTP requests", ["method", "endpoint", "http_status"]
)
REQUEST_LATENCY = Histogram(
    "auth_request_latency_seconds", "Latency of HTTP requests", ["endpoint"]
)

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    REQUEST_COUNT.labels(request.method, request.url.path, response.status_code).inc()
    REQUEST_LATENCY.labels(request.url.path).observe(duration)
    return response

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    return await request_id_middleware(request, call_next)

@app.exception_handler(Exception)
async def exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})

# Pydantic Models
class User(BaseModel):
    id: int
    username: str
    email: str
    password_hash: str

class Credentials(BaseModel):
    username: str
    password: str

class RegisterModel(BaseModel):
    username: str
    email: str
    password: str

class LoginModel(BaseModel):
    username: str
    password: str

# Authentication utilities
def check_rate_limit(ip: str):
    """Check if IP has exceeded rate limit"""
    now = datetime.utcnow()
    timestamps = RATE_LIMIT.get(ip, [])
    timestamps = [t for t in timestamps if (now - t).total_seconds() < RATE_LIMIT_WINDOW]
    if len(timestamps) >= RATE_LIMIT_COUNT:
        logger.warning(f"Rate limit exceeded for IP: {ip}")
        raise HTTPException(status_code=429, detail="Too many requests")
    timestamps.append(now)
    RATE_LIMIT[ip] = timestamps

def create_token(data: dict, expires: timedelta = None, refresh: bool = False):
    """Create JWT token with optional expiration"""
    if expires is None:
        expires = timedelta(seconds=ACCESS_TOKEN_EXPIRE_SECONDS)
    
    payload = data.copy()
    payload['exp'] = datetime.utcnow() + expires
    payload['iat'] = datetime.utcnow()
    
    if refresh:
        payload['type'] = 'refresh'
    
    try:
        if ALGORITHM == "RS256":
            return jwt.encode(payload, PRIVATE_KEY, algorithm=ALGORITHM)
        else:
            return jwt.encode(payload, PRIVATE_KEY, algorithm=ALGORITHM)
    except Exception as e:
        logger.error(f"Token creation failed: {e}")
        raise HTTPException(status_code=500, detail="Token creation failed")

def verify_token(token: str, refresh: bool = False):
    """Verify JWT token"""
    try:
        payload = jwt.decode(token, PUBLIC_KEY, algorithms=[ALGORITHM])
        if refresh and payload.get('type') != 'refresh':
            raise JWTError("Invalid token type")
        return payload
    except JWTError as e:
        logger.warning(f"Token verification failed: {e}")
        raise HTTPException(status_code=401, detail='Invalid token')

def get_token_from_request(request: Request):
    """Extract token from request headers or cookies"""
    auth = request.headers.get('Authorization')
    if auth and auth.lower().startswith('bearer '):
        return auth.split(' ', 1)[1]
    return request.cookies.get('access_token')

def get_current_user(request: Request):
    """Get current user from token"""
    token = get_token_from_request(request)
    if not token:
        raise HTTPException(status_code=401, detail='Not authenticated')
    payload = verify_token(token)
    return payload

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)

# Authentication Routes
@app.post('/register', tags=["Authentication"])
async def register(data: RegisterModel, request: Request):
    """Register a new user with enhanced security"""
    check_rate_limit(request.client.host)
    global next_id
    
    # Check if user already exists
    if data.username in user_store or data.username in users:
        logger.warning(f"Registration attempt for existing user: {data.username}")
        raise HTTPException(status_code=400, detail='User already exists')
    
    # Create new user
    user = User(
        id=next_id,
        username=data.username,
        email=data.email,
        password_hash=hash_password(data.password),
    )
    
    user_store[data.username] = user
    next_id += 1
    
    logger.info(f"User registered successfully: {data.username}")
    return {'message': 'User registered successfully'}

@app.post('/login', tags=["Authentication"])
async def login(data: LoginModel, request: Request):
    """Enhanced login with cookie and token support"""
    check_rate_limit(request.client.host)
    
    # Check enhanced user store first
    user = user_store.get(data.username)
    if user and verify_password(data.password, user.password_hash):
        # Enhanced user authentication
        token_data = {'sub': user.username, 'uid': user.id}
        access = create_token(token_data, timedelta(minutes=30))
        refresh = create_token(token_data, timedelta(days=7), refresh=True)
        
        response = JSONResponse({
            'access_token': access, 
            'refresh_token': refresh,
            'token_type': 'bearer'
        })
        response.set_cookie('access_token', access, httponly=True, secure=True, samesite='strict')
        response.set_cookie('refresh_token', refresh, httponly=True, secure=True, samesite='strict')
        
        logger.info(f"User logged in successfully: {data.username}")
        return response
    
    # Fallback to simple user store for backward compatibility
    elif users.get(data.username) == data.password:
        # Simple authentication for legacy users
        token_data = {'sub': data.username}
        
        # Use jwt_utils if available, otherwise use internal function
        if jwt_utils_create_token:
            token = jwt_utils_create_token(token_data)
        else:
            token = create_token(token_data)
        
        logger.info(f"Legacy user logged in: {data.username}")
        return {"token": token, "token_type": "bearer"}
    
    logger.warning(f"Invalid login attempt for user: {data.username}")
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.post('/refresh', tags=["Authentication"])
async def refresh(request: Request):
    """Refresh access token using refresh token"""
    token = request.cookies.get('refresh_token') or get_token_from_request(request)
    if not token:
        raise HTTPException(status_code=401, detail='No refresh token provided')
    
    payload = verify_token(token, refresh=True)
    user = user_store.get(payload['sub'])
    if not user:
        raise HTTPException(status_code=401, detail='User not found')
    
    access = create_token({'sub': user.username, 'uid': user.id}, timedelta(minutes=30))
    response = JSONResponse({'access_token': access})
    response.set_cookie('access_token', access, httponly=True, secure=True, samesite='strict')
    
    logger.info(f"Token refreshed for user: {user.username}")
    return response

@app.get('/me', tags=["Authentication"])
async def me(user=Depends(get_current_user)):
    """Get current user information"""
    return {'user': user}

@app.post('/logout', tags=["Authentication"])
async def logout(response: Response):
    """Logout user by clearing cookies"""
    response.delete_cookie('access_token')
    response.delete_cookie('refresh_token')
    return {'message': 'Logged out successfully'}

# Legacy endpoints for backward compatibility
@app.post("/auth/login", tags=["Legacy"])
async def legacy_login(creds: Credentials):
    """Legacy login endpoint for backward compatibility"""
    if users.get(creds.username) != creds.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token_data = {"sub": creds.username}
    
    # Use jwt_utils if available, otherwise use internal function
    if jwt_utils_create_token:
        token = jwt_utils_create_token(token_data)
    else:
        token = create_token(token_data)
    
    return {"token": token}

@app.post("/auth/register", tags=["Legacy"])
async def legacy_register(creds: Credentials):
    """Legacy register endpoint for backward compatibility"""
    if creds.username in users:
        raise HTTPException(status_code=400, detail="User already exists")
    
    users[creds.username] = creds.password
    token_data = {"sub": creds.username}
    
    # Use jwt_utils if available, otherwise use internal function
    if jwt_utils_create_token:
        token = jwt_utils_create_token(token_data)
    else:
        token = create_token(token_data)
    
    return {"token": token}

# Health and utility endpoints
@app.get("/", tags=["Health"])
async def root():
    """Root endpoint"""
    return {'message': f'Hello from {SERVICE_NAME}', 'version': '1.0.0'}

@app.get("/metrics", tags=["Monitoring"])
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/health", tags=["Health"])
async def health():
    """Basic health check"""
    return {"service": SERVICE_NAME, "status": "OK", "timestamp": datetime.utcnow().isoformat()}

@app.get("/health/live", tags=["Health"])
async def health_live():
    """Kubernetes liveness probe"""
    return {"status": "ok"}

@app.get("/health/ready", tags=["Health"])
async def health_ready():
    """Kubernetes readiness probe"""
    return {"status": "ok", "users_count": len(user_store)}

@app.get("/health/detailed", tags=["Health"])
async def health_detailed():
    """Detailed health information"""
    return {
        "status": "ok", 
        "dependencies": {},
        "users_count": len(user_store),
        "algorithm": ALGORITHM,
        "service": SERVICE_NAME
    }

if __name__ == "__main__":
    logger.info(f"Starting {SERVICE_NAME} on port 8001")
    uvicorn.run(app, host="0.0.0.0", port=8001)