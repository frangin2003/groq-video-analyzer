# backend/main.py

import os
import uuid
import base64
from fastapi import FastAPI, File, UploadFile, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import cv2
import asyncio
import aiohttp
from pinecone import Pinecone
from typing import Dict, List
from dotenv import load_dotenv

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

# Background task to process video
async def process_video(task_id: str, video_path: str):
    try:
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_interval = int(fps * 2)  # every 2 seconds

        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        total_frames = frame_count // frame_interval

        current_frame = 0
        frame_number = 0

        async with aiohttp.ClientSession() as session:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                if current_frame % frame_interval == 0:
                    frame_number += 1
                    # Save frame to disk
                    frame_filename = f"frames/{task_id}_frame_{frame_number}.jpg"
                    os.makedirs(os.path.dirname(frame_filename), exist_ok=True)
                    cv2.imwrite(frame_filename, frame)

                    # Read image and encode to base64
                    with open(frame_filename, "rb") as image_file:
                        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')

                    # Call GROQ API to describe image
                    description = await describe_image(session, encoded_string)

                    # Call GROQ API to generate embedding
                    embedding = await generate_embedding(session, description)

                    # Insert into Pinecone
                    metadata = {
                        "task_id": task_id,
                        "timecode": current_frame / fps,
                        "frame_path": frame_filename,
                        "video_path": video_path
                    }
                    upsert_response = index.upsert(
                        vectors=[
                            {
                                "id": f"{task_id}_frame_{frame_number}",
                                "values": embedding,
                                "metadata": metadata
                            }
                        ]
                    )

                    # Update progress
                    progress = int((frame_number / total_frames) * 100)
                    await send_progress(task_id, progress)

                current_frame += 1

        cap.release()
        await send_progress(task_id, 100)
    except Exception as e:
        await send_progress(task_id, -1, str(e))

async def describe_image(session: aiohttp.ClientSession, image_base64: str) -> str:
    # Replace with actual GROQ API endpoint and headers
    groq_description_url = "https://api.groq.com/describe"  # Placeholder URL
    headers = {
        "Authorization": f"Bearer your-groq-api-key",  # Replace with your GROQ API key
        "Content-Type": "application/json"
    }
    payload = {
        "image": image_base64
    }
    async with session.post(groq_description_url, json=payload, headers=headers) as resp:
        if resp.status == 200:
            data = await resp.json()
            return data["description"]
        else:
            raise Exception(f"GROQ describe API failed with status {resp.status}")

async def generate_embedding(session: aiohttp.ClientSession, description: str) -> List[float]:
    # Replace with actual GROQ API endpoint and headers
    groq_embedding_url = "https://api.groq.com/embedding"  # Placeholder URL
    headers = {
        "Authorization": f"Bearer your-groq-api-key",  # Replace with your GROQ API key
        "Content-Type": "application/json"
    }
    payload = {
        "text": description
    }
    async with session.post(groq_embedding_url, json=payload, headers=headers) as resp:
        if resp.status == 200:
            data = await resp.json()
            return data["embedding"]  # Assuming embedding is a list of floats
        else:
            raise Exception(f"GROQ embedding API failed with status {resp.status}")

async def send_progress(task_id: str, progress: int, error: str = ""):
    if task_id in connections:
        websocket = connections[task_id]
        await websocket.send_json({"progress": progress, "error": error})

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
    background_tasks.add_task(process_video, task_id, video_path)

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
