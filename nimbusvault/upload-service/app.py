import sys
from pathlib import Path
from fastapi import FastAPI, Depends, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
import httpx
import os
import uvicorn

# Add shared directory to path for imports
BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR / 'shared'))

# Import shared modules with fallbacks
try:
    from auth_middleware import AuthMiddleware, get_current_user
    from logger import configure_logger, request_id_middleware
    from storage_utils import save_file
except ImportError as e:
    print(f"Warning: Could not import shared modules: {e}")
    # Fallback implementations
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("upload-service")
    
    class AuthMiddleware:
        def __init__(self, app, public_key=None):
            pass
    
    async def get_current_user():
        return {"user": "anonymous"}
    
    async def request_id_middleware(request: Request, call_next):
        request.state.request_id = "fallback-id"
        return await call_next(request)
    
    def save_file(file_path: str, data: bytes):
        with open(file_path, 'wb') as f:
            f.write(data)
        print(f"Saving {file_path}")
else:
    logger = configure_logger("upload-service")

# Load public key for JWT authentication
try:
    PUBLIC_KEY_PATH = BASE_DIR / 'auth-service' / 'keys' / 'public.pem'
    if PUBLIC_KEY_PATH.exists():
        with open(PUBLIC_KEY_PATH) as f:
            PUBLIC_KEY = f.read()
    else:
        PUBLIC_KEY = None
        print("Warning: Public key not found, authentication will be disabled")
except Exception as e:
    print(f"Warning: Could not load public key: {e}")
    PUBLIC_KEY = None

# Service configuration
SERVICE_NAME = "upload-service"
METADATA_SERVICE_URL = os.getenv("METADATA_SERVICE_URL", "http://metadata-service:8003/metadata")
UPLOAD_DIR = Path("/tmp/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI()

# Add authentication middleware if public key is available
if PUBLIC_KEY:
    app.add_middleware(AuthMiddleware, public_key=PUBLIC_KEY)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    return await request_id_middleware(request, call_next)

@app.exception_handler(Exception)
async def exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})

@app.on_event("startup")
async def startup_event():
    logger.info(f"{SERVICE_NAME} starting up")

# Routes
@app.get("/")
async def root(request: Request):
    logger.info("Health check", extra={"requestId": getattr(request.state, 'request_id', 'unknown')})
    return {"message": f"Hello from {SERVICE_NAME}"}

@app.get("/health")
async def health() -> dict:
    return {"service": SERVICE_NAME, "status": "OK"}

@app.get("/public")
async def public_route():
    return {"message": "public endpoint - no authentication required"}

@app.get("/protected")
async def protected_route(user=Depends(get_current_user)):
    return {"message": "protected endpoint", "user": user}

@app.get("/log")
async def log_route(request: Request):
    logger.info(
        f"Received request from {request.client.host} to {request.url.path}", 
        extra={"requestId": getattr(request.state, 'request_id', 'unknown')}
    )
    return {"message": "Request logged"}

@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...), 
    request: Request = None, 
    user=Depends(get_current_user)
):
    """Upload a file with authentication and metadata tracking"""
    try:
        # Read file contents
        contents = await file.read()
        request_id = getattr(request.state, 'request_id', 'unknown') if request else 'unknown'
        
        logger.info(
            f"Received file {file.filename} of size {len(contents)} bytes from user {user}", 
            extra={"requestId": request_id}
        )
        
        # Create safe filename
        safe_filename = "".join(c for c in file.filename if c.isalnum() or c in "._- ")
        file_path = UPLOAD_DIR / safe_filename
        
        # Save file using shared utility
        save_file(str(file_path), contents)
        
        # Prepare metadata with user information
        metadata = {
            "filename": safe_filename,
            "uploaded_by": user.get("user", "unknown") if isinstance(user, dict) else str(user),
            "timestamp": datetime.utcnow().isoformat(),
            "file_size": len(contents),
            "content_type": file.content_type,
            "original_filename": file.filename
        }
        
        # Submit metadata to metadata service
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(METADATA_SERVICE_URL, json=metadata)
                response.raise_for_status()
                metadata_response = response.json()
            
            logger.info(
                f"File uploaded successfully: {safe_filename}", 
                extra={"requestId": request_id}
            )
            
            return {
                "status": "success",
                "filename": safe_filename,
                "original_filename": file.filename,
                "size": len(contents),
                "uploaded_by": metadata["uploaded_by"],
                "metadata_response": metadata_response,
            }
            
        except Exception as exc:
            logger.exception(
                "Failed to submit metadata", 
                extra={"requestId": request_id}
            )
            
            # File was saved but metadata submission failed
            return {
                "status": "partial_success",
                "filename": safe_filename,
                "size": len(contents),
                "uploaded_by": metadata["uploaded_by"],
                "warning": "File uploaded but metadata submission failed",
                "error": str(exc),
            }
            
    except Exception as exc:
        logger.exception(
            f"Failed to upload file {file.filename}", 
            extra={"requestId": getattr(request.state, 'request_id', 'unknown') if request else 'unknown'}
        )
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "File upload failed",
                "error": str(exc)
            }
        )

@app.get("/uploads")
async def list_uploads(user=Depends(get_current_user)):
    """List all uploaded files"""
    try:
        files = [
            {
                "filename": f.name,
                "size": f.stat().st_size,
                "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat()
            }
            for f in UPLOAD_DIR.iterdir() 
            if f.is_file()
        ]
        
        logger.info(f"Listed {len(files)} uploads for user {user}")
        return {"uploads": files, "count": len(files)}
        
    except Exception as exc:
        logger.error(f"Failed to list uploads: {exc}")
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to list uploads", "details": str(exc)}
        )

@app.delete("/uploads/{filename}")
async def delete_upload(filename: str, user=Depends(get_current_user)):
    """Delete a specific uploaded file"""
    try:
        file_path = UPLOAD_DIR / filename
        
        if file_path.exists() and file_path.is_file():
            file_path.unlink()
            logger.info(f"File deleted: {filename} by user {user}")
            return {"message": f"File {filename} deleted successfully"}
        else:
            return JSONResponse(
                status_code=404,
                content={"error": "File not found"}
            )
            
    except Exception as exc:
        logger.error(f"Failed to delete file {filename}: {exc}")
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to delete file", "details": str(exc)}
        )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)