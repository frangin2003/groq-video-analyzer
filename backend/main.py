import os
from dotenv import load_dotenv
load_dotenv()

import uuid
from fastapi import FastAPI, File, UploadFile, BackgroundTasks, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pinecone import Pinecone
import pinecone
from typing import Dict, List
from transformers import AutoModel
from collections import defaultdict
from fastapi.staticfiles import StaticFiles

from .video_processing import process_video



# Initialize FastAPI app
app = FastAPI()

# Set up CORS (adjust origins as needed)
origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:8000",
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

pinecone_index = pc.Index(INDEX_NAME)

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
    background_tasks.add_task(process_video, task_id, video_path, pinecone_index, connections)

    return {"task_id": task_id}

# Upload endpoint
@app.post("/search_video_sequences/{user_query}")
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
            'frame_paths': seq['frame_paths'],  # Include ordered frame paths array
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
            if frames[i]['frame'] == current_sequence[-1]['frame'] + 1:
                # Frame is consecutive, add to current sequence
                current_sequence.append(frames[i])
            else:
                # Frame is not consecutive, save current sequence and start new one
                if len(current_sequence) > 1:  # Only add sequences with more than one frame
                    sequences.append({
                        'video_path': video_path,
                        'frame_start': current_sequence[0]['frame'],
                        'frame_end': current_sequence[-1]['frame'],
                        'time_start': current_sequence[0]['timestamp'],
                        'time_end': current_sequence[-1]['timestamp'],
                        'duration': current_sequence[-1]['timestamp'] - current_sequence[0]['timestamp'],
                        'frames': current_sequence,
                        'frame_paths': [f['frame_path'] for f in current_sequence],  # Add ordered frame paths
                        'score': sum(f['score'] for f in current_sequence) / len(current_sequence),
                        'description': current_sequence[0]['metadata']['description']
                    })
                current_sequence = [frames[i]]
        
        # Add the last sequence only if it has more than one frame
        if len(current_sequence) > 1:
            sequences.append({
                'video_path': video_path,
                'frame_start': current_sequence[0]['frame'],
                'frame_end': current_sequence[-1]['frame'],
                'time_start': current_sequence[0]['timestamp'],
                'time_end': current_sequence[-1]['timestamp'],
                'duration': current_sequence[-1]['timestamp'] - current_sequence[0]['timestamp'],
                'frames': current_sequence,
                'frame_paths': [f['frame_path'] for f in current_sequence],  # Add ordered frame paths
                'score': sum(f['score'] for f in current_sequence) / len(current_sequence),
                'description': current_sequence[0]['metadata']['description']
            })
    
    # Sort sequences by score
    sequences.sort(key=lambda x: x['score'], reverse=True)
    return sequences

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

# Create frames directory if it doesn't exist
os.makedirs("frames", exist_ok=True)

# Mount the frames directory as a static file directory
app.mount("/frames", StaticFiles(directory="frames"), name="frames")

# Serve frontend (assuming build is in 'frontend/build')
app.mount("/", StaticFiles(directory="./frontend/build", html=True), name="frontend")

# Remove the POST endpoint and modify the WebSocket endpoint
@app.websocket("/ws/search")
async def websocket_search_endpoint(websocket: WebSocket):
    print("🔵 WebSocket connection initiated")
    try:
        await websocket.accept()
        print("🔵 WebSocket connection accepted")
        
        while True:
            try:
                print("🔵 Waiting for message...")
                data = await websocket.receive_json()
                print(f"🔵 Received data: {data}")
                
                query = data.get('query')
                print(f"🔵 Extracted query: {query}")
                
                if query:
                    try:
                        task_id = str(uuid.uuid4())
                        print(f"🔵 Generated task_id: {task_id}")
                        connections[task_id] = websocket
                        print(f"🔵 Stored WebSocket connection for task_id: {task_id}")
                        
                        print("🔵 Creating background task")
                        background_tasks = BackgroundTasks()
                        background_tasks.add_task(
                            search_video_sequences, 
                            task_id,
                            query, 
                            pinecone_index, 
                            connections
                        )
                        print("🔵 Added search task to background tasks")
                        
                        print("🔵 Executing background tasks")
                        await background_tasks()
                        print("🔵 Background tasks execution completed")
                    except Exception as e:
                        print(f"🔴 Error processing query: {str(e)}")
                        print(f"🔴 Error type: {type(e)}")
                        import traceback
                        print(f"🔴 Traceback: {traceback.format_exc()}")
                        await websocket.send_json({
                            "error": str(e)
                        })
                else:
                    print("🔴 No query in received data")
                    await websocket.send_json({
                        "error": "No query provided"
                    })
                    
            except Exception as e:
                print(f"🔴 Error receiving message: {str(e)}")
                print(f"🔴 Error type: {type(e)}")
                import traceback
                print(f"🔴 Traceback: {traceback.format_exc()}")
                break
                
    except WebSocketDisconnect:
        print("🔵 WebSocket disconnected")
    except Exception as e:
        print(f"🔴 Unexpected error: {str(e)}")
        print(f"🔴 Error type: {type(e)}")
        import traceback
        print(f"🔴 Traceback: {traceback.format_exc()}")
    finally:
        print("🔵 WebSocket connection handling complete")
