import os
from dotenv import load_dotenv
load_dotenv()

import uuid
from fastapi import FastAPI, File, UploadFile, BackgroundTasks, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pinecone import Pinecone
import pinecone
from typing import Dict, List
from transformers import AutoModel
from collections import defaultdict
from fastapi.staticfiles import StaticFiles
import cv2
import tempfile
from typing import Dict

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

# Create both frames and videos directories
os.makedirs("frames", exist_ok=True)
os.makedirs("videos", exist_ok=True)

# Mount both directories as static file directories
app.mount("/frames", StaticFiles(directory="frames"), name="frames")
app.mount("/videos", StaticFiles(directory="videos"), name="videos")

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

@app.post("/extract_sequence")
async def extract_sequence(request: Dict):
    try:
        video_path = request["video_path"]
        time_start = float(request["time_start"])
        time_end = float(request["time_end"])
        
        # Open the video file
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise HTTPException(status_code=500, detail="Could not open video file")
            
        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Calculate start and end frames
        start_frame = int(time_start * fps)
        end_frame = int(time_end * fps)
        
        # Create temporary output file
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
            output_path = temp_file.name
            
            # Create VideoWriter object
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, fps, (frame_width, frame_height))
            
            # Set frame position to start_frame
            cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
            
            # Read and write frames
            current_frame = start_frame
            while current_frame <= end_frame:
                ret, frame = cap.read()
                if not ret:
                    break
                    
                out.write(frame)
                current_frame += 1
            
            # Release everything
            cap.release()
            out.release()
            
            # Return the video file as a streaming response
            def iterfile():
                with open(output_path, 'rb') as f:
                    yield from f
                
                # Cleanup temp file
                os.unlink(output_path)
            
            return StreamingResponse(
                iterfile(),
                media_type='video/mp4',
                headers={
                    'Content-Disposition': f'attachment; filename="sequence_{time_start:.2f}-{time_end:.2f}.mp4"'
                }
            )
            
    except Exception as e:
        print(f"Error extracting sequence: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
