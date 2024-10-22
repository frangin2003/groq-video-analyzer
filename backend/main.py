# backend/main.py
import os
import uuid
from fastapi import FastAPI, File, UploadFile, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pinecone import Pinecone
import pinecone
from typing import Dict, List
from dotenv import load_dotenv
from video_processing import process_video

load_dotenv()

# Initialize FastAPI app
app = FastAPI()

# Set up CORS (adjust origins as needed)
origins = [
    "http://localhost",
    "http://localhost:3000",
    # Add your frontend URL if different
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Pinecone
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")  # Replace with your Pinecone API key

pc = Pinecone(api_key=PINECONE_API_KEY)

INDEX_NAME = "groq-video-analyzer"

if INDEX_NAME not in pc.list_indexes().names():
    pc.create_index(
        name=INDEX_NAME,
        spec=pinecone.IndexSpec(
            dimension=768,  # Adjust dimension as per embedding
            metric='cosine'  # or 'euclidean' or 'dotproduct' as per your requirement
        )
    )

index = pc.Index(INDEX_NAME)

# Dictionary to hold WebSocket connections
connections: Dict[str, WebSocket] = {}

# WebSocket endpoint for progress updates
@app.websocket("/ws/{task_id}")
async def websocket_endpoint(websocket: WebSocket, task_id: str):
    await websocket.accept()
    connections[task_id] = websocket
    try:
        while True:
            data = await websocket.receive_text()
            # Can handle incoming messages if needed
            pass
    except WebSocketDisconnect:
        del connections[task_id]

# Upload endpoint
@app.post("/upload")
async def upload_video(file: UploadFile = File(...), background_tasks: BackgroundTasks = None):
    task_id = str(uuid.uuid4())
    video_dir = "videos"
    os.makedirs(video_dir, exist_ok=True)
    video_path = os.path.join(video_dir, f"{task_id}_{file.filename}")
    with open(video_path, "wb") as f:
        f.write(await file.read())

    # Start background task
    background_tasks.add_task(process_video, task_id, video_path, index)

    return {"task_id": task_id}

# Endpoint to download video sequence
@app.get("/download_sequence/{task_id}/{sequence_id}")
async def download_sequence(task_id: str, sequence_id: str):
    # Logic to extract the video sequence based on sequence_id
    # For simplicity, assume sequence_id corresponds to start and end frames
    # This requires storing the sequences during processing

    # Placeholder implementation
    sequence_path = f"sequences/{task_id}_sequence_{sequence_id}.mp4"
    if os.path.exists(sequence_path):
        return FileResponse(sequence_path, media_type='video/mp4', filename=os.path.basename(sequence_path))
    else:
        return JSONResponse(status_code=404, content={"message": "Sequence not found"})

# Serve frontend (assuming build is in 'frontend/build')
from fastapi.staticfiles import StaticFiles
app.mount("/", StaticFiles(directory="../frontend/build", html=True), name="frontend")
