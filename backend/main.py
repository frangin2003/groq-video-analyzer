import os
from dotenv import load_dotenv
load_dotenv()

import uuid
from fastapi import FastAPI, File, UploadFile, BackgroundTasks, WebSocket, WebSocketDisconnect, HTTPException, Request, Body, Form, Depends, status, Query
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Body
from pinecone import Pinecone
import pinecone
from typing import Dict, List
from transformers import AutoModel
from collections import defaultdict
from fastapi.staticfiles import StaticFiles
import cv2
import tempfile
from typing import Dict
from pydub import AudioSegment
import subprocess
from pydantic import BaseModel
from fastapi.exceptions import RequestValidationError
import urllib.parse
import numpy as np
from scipy.io import wavfile
from scipy.signal import resample
import soundfile as sf
from moviepy.editor import VideoFileClip
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .video_processing import process_video



# Initialize FastAPI app
app = FastAPI()

# Set up CORS (adjust origins as needed)
origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:8000",
    "https://*.repl.co",  # Allow Replit domains
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

pinecone_index = pc.Index(INDEX_NAME)

# Dictionary to hold WebSocket connections
connections: Dict[str, WebSocket] = {}

# WebSocket endpoint for progress updates
@app.websocket("/api/ws/{task_id}")
async def websocket_endpoint(
    websocket: WebSocket, 
    task_id: str,
    token: str = Query(...)  # Get token from query params
):
    # Verify token
    if not token.startswith('Bearer '):
        await websocket.close(code=4001)
        return

    clean_token = token.replace('Bearer ', '')
    if clean_token != "authenticated":
        await websocket.close(code=4001)
        return

    await websocket.accept()
    connections[task_id] = websocket
    try:
        while True:
            data = await websocket.receive_text()
            # Can handle incoming messages if needed
            pass
    except WebSocketDisconnect:
        del connections[task_id]

security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != "authenticated":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials

@app.get("/debug/routes")
async def debug_routes():
    routes = []
    for route in app.routes:
        route_info = {
            "path": route.path,
            "name": route.name,
            "methods": getattr(route, "methods", ["WebSocket"]) if not hasattr(route, "methods") else route.methods
        }
        routes.append(route_info)
    return {"routes": routes}

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
    token: str = Depends(verify_token)
):
    task_id = str(uuid.uuid4())
    video_dir = "videos"
    os.makedirs(video_dir, exist_ok=True)
    video_path = os.path.join(video_dir, f"{task_id}_{file.filename}")
    with open(video_path, "wb") as f:
        f.write(await file.read())

    # Start background task
    background_tasks.add_task(process_video, task_id, video_path, pinecone_index, connections)

    return {"task_id": task_id}

# Upload endpoint
@app.get("/api/search_video_sequences/{user_query}")
async def search_video_sequences(user_query: str):
    try:
        print("🔵 Starting search for query:", user_query)
        
        # Load embedding model
        print("🔵 Loading embedding model")
        embedding_model = AutoModel.from_pretrained('jinaai/jina-embeddings-v2-base-en', trust_remote_code=True)
        
        # Generate embeddings
        print("🔵 Generating embeddings")
        user_query_embedding = embedding_model.encode(user_query).tolist()
        
        # Query Pinecone
        print("🔵 Querying Pinecone")
        result = pinecone_index.query(
            vector=user_query_embedding,
            top_k=5,
            include_values=False,
            include_metadata=True
        )
        
        # Group frames into sequences
        sequences = group_frames_into_sequences(result.matches)
        
        # Format the sequences for JSON response
        formatted_sequences = [{
            'id': idx,
            'video_path': seq['video_path'],
            'frame_start': seq['frame_start'],
            'frame_end': seq['frame_end'],
            'time_start': seq['time_start'],
            'time_end': seq['time_end'],
            'duration': seq['duration'],
            'score': seq['score'],
            'description': seq['description'],
            'frame_paths': seq['frame_paths'],
            'metadata': {
                'frames': [f['frame'] for f in seq['frames']],
                'video_path': seq['video_path']
            }
        } for idx, seq in enumerate(sequences)]

        return {"results": formatted_sequences}
        
    except Exception as e:
        print(f"🔴 Error in search_video_sequences: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def group_frames_into_sequences(matches):
    # Group frames by video path
    video_groups = defaultdict(list)
    for match in matches:
        video_groups[match.metadata['video_path']].append({
            'frame': match.metadata['frame_number'],
            'frame_path': match.metadata['frame_path'],
            'timestamp': match.metadata['timestamp'],
            'metadata': match.metadata,
            'score': float(match.score),
            'id': match.id
        })
    
    # Find sequences in each video
    sequences = []
    for video_path, frames in video_groups.items():
        # Sort frames by frame number
        frames.sort(key=lambda x: x['frame'])
        
        current_sequence = [frames[0]]
        
        for i in range(1, len(frames)):
            # Allow for one frame gap (frame difference of 2 or less)
            if frames[i]['frame'] <= current_sequence[-1]['frame'] + 2:
                # Frame is consecutive or has one frame gap, add to current sequence
                current_sequence.append(frames[i])
            else:
                # Frame gap is too large, save current sequence and start new one
                if len(current_sequence) > 1:  # Only add sequences with more than one frame
                    start_time = current_sequence[0]['timestamp']
                    end_time = current_sequence[-1]['timestamp']
                    sequences.append({
                        'video_path': video_path,
                        'frame_start': current_sequence[0]['frame'],
                        'frame_end': current_sequence[-1]['frame'],
                        'time_start': start_time,
                        'time_end': end_time,
                        'time_start_formatted': format_timestamp(start_time),
                        'time_end_formatted': format_timestamp(end_time),
                        'duration': end_time - start_time,
                        'frames': current_sequence,
                        'frame_paths': [f['frame_path'] for f in current_sequence],
                        'score': sum(f['score'] for f in current_sequence) / len(current_sequence),
                        'description': current_sequence[0]['metadata']['description']
                    })
                current_sequence = [frames[i]]

        # Add the last sequence only if it has more than one frame
        if len(current_sequence) > 1:
            start_time = current_sequence[0]['timestamp']
            end_time = current_sequence[-1]['timestamp']
            sequences.append({
                'video_path': video_path,
                'frame_start': current_sequence[0]['frame'],
                'frame_end': current_sequence[-1]['frame'],
                'time_start': start_time,
                'time_end': end_time,
                'time_start_formatted': format_timestamp(start_time),
                'time_end_formatted': format_timestamp(end_time),
                'duration': end_time - start_time,
                'frames': current_sequence,
                'frame_paths': [f['frame_path'] for f in current_sequence],
                'score': sum(f['score'] for f in current_sequence) / len(current_sequence),
                'description': current_sequence[0]['metadata']['description']
            })
    
    # Sort sequences by score
    sequences.sort(key=lambda x: x['score'], reverse=True)
    return sequences

def format_timestamp(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

@app.get("/api/extract_sequence")
async def extract_sequence(
    video_path: str,
    time_start: float,
    time_end: float
):
    print("🟢 Extract sequence endpoint called")
    try:
        video_path = urllib.parse.unquote(video_path)
        video_path = os.path.normpath(video_path).replace('\\', '/')
        
        # Use a single VideoFileClip for both video and audio
        try:
            print("🟢 Loading video with moviepy")
            video = VideoFileClip(video_path)
            
            # Extract the subclip with both video and audio
            print(f"🟢 Extracting subclip from {time_start} to {time_end}")
            clip = video.subclip(time_start, time_end)
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
                output_path = temp_file.name
                
                # Write video with audio
                print("🟢 Writing video with audio")
                clip.write_videofile(
                    output_path,
                    codec='libx264',
                    audio_codec='aac',
                    temp_audiofile=None,
                    remove_temp=True,
                    logger=None
                )
                
                # Clean up moviepy clips
                clip.close()
                video.close()
                
                def iterfile():
                    try:
                        with open(output_path, 'rb') as f:
                            yield from f
                    finally:
                        try:
                            os.unlink(output_path)
                        except Exception as cleanup_error:
                            print(f"🔴 Error during cleanup: {str(cleanup_error)}")

                return StreamingResponse(
                    iterfile(),
                    media_type='video/mp4',
                    headers={
                        'Content-Disposition': f'attachment; filename="sequence_{time_start:.2f}-{time_end:.2f}.mp4"'
                    }
                )
                
        except Exception as e:
            print(f"🔴 Error processing video: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

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
