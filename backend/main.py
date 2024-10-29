import os
os.environ['KMP_DUPLICATE_LIB_OK']='True'

from dotenv import load_dotenv
load_dotenv()

import uuid
from fastapi import FastAPI, File, UploadFile, BackgroundTasks, WebSocket, WebSocketDisconnect, HTTPException, Request, Body, Form, Depends, status, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Body
from pinecone import Pinecone
import pinecone
from typing import Dict
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
import urllib.parse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .video_processing import process_video
from .sequence_finder import extract_video_sequence

# Get LOCAL from environment variables
IS_LOCAL = os.getenv("LOCAL", "false").lower() == "true"

# Initialize FastAPI app
app = FastAPI()

# Set up CORS (adjust origins as needed)
origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:8000",
    "http://localhost:11434",
    "http://localhost:8080",
    "https://*.repl.co",  # Allow Replit domains
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Pinecone only if not local
if not IS_LOCAL:
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
    pc = Pinecone(api_key=PINECONE_API_KEY)
    INDEX_NAME = "groq-video-analyzer"

    if INDEX_NAME not in pc.list_indexes().names():
        pc.create_index(
            name=INDEX_NAME,
            spec=pinecone.IndexSpec(
                dimension=768,
                metric='cosine'
            )
        )
    pinecone_index = pc.Index(INDEX_NAME)
else:
    pinecone_index = None

# Dictionary to hold WebSocket connections
connections: Dict[str, WebSocket] = {}

# WebSocket endpoint for progress updates
@app.websocket("/api/ws/{task_id}")
async def websocket_endpoint(
    websocket: WebSocket, 
    task_id: str,
    token: str = Query(...)  # Get token from query params
):
    print(f"Received token: {token}")  # Debug line

    if token != "authenticated":
        print("Invalid token")  # Debug line
        await websocket.close(code=4001)
        return

    await websocket.accept()
    connections[task_id] = websocket
    try:
        while True:
            await websocket.receive_text()
            # Can handle incoming messages if needed
            pass
    except WebSocketDisconnect:
        del connections[task_id]

security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify the Bearer token."""
    print(f"🔑 Auth check - IS_LOCAL: {IS_LOCAL}")  # Debug log
    
    if IS_LOCAL:
        print("🟢 Skipping auth check in local mode")  # Debug log
        return True
        
    if not credentials or credentials.credentials != os.getenv("AUTH_TOKEN"):
        print("🔴 Auth failed - invalid or missing token")  # Debug log
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )
    return True

@app.get("/api/auth")
async def authenticate(password: str):
    if password == "groq is beautiful":
        return {"authenticated": True}
    raise HTTPException(status_code=401, detail="Invalid password")

# Upload endpoint
@app.post("/api/upload")
async def upload_video(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    _: bool = Depends(verify_token)
):
    task_id = str(uuid.uuid4())
    video_dir = "videos"
    os.makedirs(video_dir, exist_ok=True)
    video_path = os.path.join(video_dir, f"{task_id}_{file.filename}")
    with open(video_path, "wb") as f:
        f.write(await file.read())

    # Start background task with local flag
    background_tasks.add_task(
        process_video, 
        task_id, 
        video_path, 
        pinecone_index, 
        connections,
        is_local=IS_LOCAL
    )

    return {"task_id": task_id}

# Upload endpoint
@app.get("/api/search_video_sequences/{user_query}")
async def search_video_sequences_endpoint(
    user_query: str,
    _: bool = Depends(verify_token)
):
    """REST endpoint for searching video sequences"""
    try:
        print("🔵 Starting search for query:", user_query)
        
        # Use the sequence_finder's search function
        from .sequence_finder import search_video_sequences
        result = await search_video_sequences(
            user_query=user_query,
            pinecone_index=pinecone_index,
            is_local=IS_LOCAL,
            k=5
        )
        
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["error"])
            
        return result

    except Exception as e:
        print(f"🔴 Error in search_video_sequences_endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/extract_sequence")
async def extract_sequence(
    video_path: str,
    time_start: float,
    time_end: float,
    _: bool = Depends(verify_token)
):
    print("🟢 Extract sequence endpoint called")
    try:
        video_path = urllib.parse.unquote(video_path)
        video_path = os.path.normpath(video_path).replace('\\', '/')
        return await extract_video_sequence(video_path, time_start, time_end)
    except Exception as e:
        print(f"🔴 Error in extract_sequence: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

# Create both frames and videos directories
os.makedirs("frames", exist_ok=True)
os.makedirs("videos", exist_ok=True)

# Mount both directories as static file directories
app.mount("/frames", StaticFiles(directory="frames"), name="frames")
app.mount("/videos", StaticFiles(directory="videos"), name="videos")
app.mount("/video_sample_to_test", StaticFiles(directory="video_sample_to_test"), name="video_sample_to_test")
app.mount("/", StaticFiles(directory="./frontend/build", html=True), name="frontend")

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    print(f"🔴 Validation error details: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()}
    )

# Add this right after your app definition to see all registered routes
@app.on_event("startup")
async def startup_event():
    print("\n🟢 Registered routes:")
    for route in app.routes:
        if hasattr(route, 'methods'):
            print(f"🟢 {route.methods} {route.path}")
        else:
            print(f"🟢 WebSocket {route.path}")
