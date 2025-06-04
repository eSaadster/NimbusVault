import sys
from pathlib import Path
from fastapi import FastAPI, Depends, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List
import os
import uvicorn

# Add shared directory to path for imports
BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR / 'shared'))

# Import shared modules with fallbacks
try:
    from auth_middleware import AuthMiddleware, get_current_user
    from logger import configure_logger
    from storage_utils import save_file
except ImportError as e:
    print(f"Warning: Could not import shared modules: {e}")
    # Fallback implementations
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("storage-service")
    
    class AuthMiddleware:
        def __init__(self, app, public_key=None):
            pass
    
    async def get_current_user():
        return {"user": "anonymous"}
    
    def save_file(file_path: str, data: bytes):
        with open(file_path, 'wb') as f:
            f.write(data)
        print(f"Saving {file_path}")
else:
    logger = configure_logger("storage-service")

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
SERVICE_NAME = "storage-service"
STORAGE_DIR = Path("/tmp/storage")
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI()

# Add authentication middleware if public key is available
if PUBLIC_KEY:
    app.add_middleware(AuthMiddleware, public_key=PUBLIC_KEY)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for metadata (consider using persistent storage in production)
stored_metadata: List[Dict] = []

# Routes
@app.get("/")
async def root():
    logger.info("Health check hit")
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

@app.post("/store")
async def store_metadata(metadata: Dict, user=Depends(get_current_user)) -> Dict[str, str]:
    """Store metadata with user authentication"""
    # Add user info to metadata
    metadata_with_user = {
        **metadata,
        "stored_by": user.get("user", "unknown"),
        "timestamp": str(Path().stat().st_mtime) if Path().exists() else "unknown"
    }
    
    stored_metadata.append(metadata_with_user)
    logger.info(f"Metadata stored: {metadata_with_user}")
    return {"result": "saved", "metadata_id": len(stored_metadata) - 1}

@app.get("/store")
async def get_stored_metadata(user=Depends(get_current_user)) -> Dict[str, List[Dict]]:
    """Retrieve all stored metadata"""
    logger.info(f"Metadata retrieved by user: {user}")
    return {"metadata": stored_metadata}

@app.post("/files")
async def store_file(file: UploadFile = File(...), user=Depends(get_current_user)):
    """Store uploaded file with user authentication"""
    try:
        # Read file data
        data = await file.read()
        
        # Create safe filename
        safe_filename = "".join(c for c in file.filename if c.isalnum() or c in "._- ")
        file_path = STORAGE_DIR / safe_filename
        
        # Save file using shared utility
        save_file(str(file_path), data)
        
        # Store file metadata
        file_metadata = {
            "filename": safe_filename,
            "original_filename": file.filename,
            "size": len(data),
            "content_type": file.content_type,
            "uploaded_by": user.get("user", "unknown"),
            "file_path": str(file_path)
        }
        stored_metadata.append(file_metadata)
        
        logger.info(f"File saved: {safe_filename} by user: {user}")
        return {
            "filename": safe_filename,
            "size": len(data),
            "message": "File uploaded successfully"
        }
        
    except Exception as e:
        logger.error(f"Error storing file: {e}")
        return {"error": "Failed to store file", "details": str(e)}

@app.get("/files")
async def list_files(user=Depends(get_current_user)) -> Dict[str, List[str]]:
    """List all stored files"""
    try:
        files = [f.name for f in STORAGE_DIR.iterdir() if f.is_file()]
        logger.info(f"Files listed by user: {user}")
        return {"files": files}
    except Exception as e:
        logger.error(f"Error listing files: {e}")
        return {"error": "Failed to list files", "files": []}

@app.delete("/files/{filename}")
async def delete_file(filename: str, user=Depends(get_current_user)):
    """Delete a specific file"""
    try:
        file_path = STORAGE_DIR / filename
        if file_path.exists() and file_path.is_file():
            file_path.unlink()
            logger.info(f"File deleted: {filename} by user: {user}")
            return {"message": f"File {filename} deleted successfully"}
        else:
            return {"error": "File not found"}
    except Exception as e:
        logger.error(f"Error deleting file: {e}")
        return {"error": "Failed to delete file", "details": str(e)}

if __name__ == "__main__":
    logger.info("Storage service started")
    port = int(os.environ.get("PORT", 8004))
    uvicorn.run(app, host="0.0.0.0", port=port)