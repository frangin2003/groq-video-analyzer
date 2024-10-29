import os
import base64
import cv2
import aiohttp
import asyncio
from fastapi import WebSocket
from typing import Dict, List, Any
import pinecone
from groq import Groq
from transformers import AutoModel
import faiss
import numpy as np
from pathlib import Path
import json
from .vector_db import LocalVectorDB


# Background task to process video
async def process_video(task_id: str, video_path: str, pinecone_index: pinecone.Index, connections: Dict[str, WebSocket], is_local: bool = False):
    try:
        print(f"🟢 Starting video processing. Local mode: {is_local}")
        
        # Check if Ollama is running when in local mode
        if is_local:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get('http://localhost:11434/api/version') as response:
                        if response.status != 200:
                            raise Exception("Ollama server not responding")
                        version = await response.json()
                        print(f"🟢 Connected to Ollama version: {version.get('version')}")
            except Exception as e:
                error_msg = f"Failed to connect to Ollama server: {str(e)}"
                print(f"🔴 {error_msg}")
                await send_progress(task_id, -1, error=error_msg, connections=connections)
                return

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise Exception(f"Failed to open video file: {video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_interval = int(fps * 2)  # every 2 seconds

        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        total_frames = frame_count // frame_interval

        frame_number = 0
        frames_metadata = []  # Store metadata for local processing

        # Load embedding model only if using remote processing
        embedding_model = None
        if not is_local:
            embedding_model = AutoModel.from_pretrained(
                'jinaai/jina-embeddings-v2-base-en',
                trust_remote_code=True
            )

        async with aiohttp.ClientSession() as session:
            while frame_number * frame_interval < frame_count:
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number * frame_interval)
                ret, frame = cap.read()
                if not ret:
                    print(f"Failed to read frame at position {frame_number * frame_interval}")
                    break

                timestamp = frame_number * frame_interval / fps
                print(f"Processing frame {frame_number}: {timestamp:.2f} seconds")

                # Process the frame
                frame_filename = f"frames/{task_id}_frame_{frame_number}.jpg"
                cv2.imwrite(frame_filename, frame)

                with open(frame_filename, "rb") as image_file:
                    encoded_string = base64.b64encode(image_file.read()).decode('utf-8')

                try:
                    # Get frame description
                    frame_description = await get_frame_description(encoded_string, is_local)
                    print(f"Frame {frame_number} description: {frame_description[:100]}...")

                    # Create metadata for this frame
                    metadata = {
                        "description": frame_description,
                        "frame_number": frame_number,
                        "frame_path": frame_filename,
                        "task_id": task_id,
                        "timestamp": timestamp,
                        "video_path": video_path
                    }

                    if is_local:
                        frames_metadata.append(metadata)
                    else:
                        await process_remote_frame(
                            frame_description,
                            metadata,
                            embedding_model,
                            pinecone_index,
                            task_id,
                            frame_number
                        )

                    # Update progress
                    progress = int((frame_number + 1) / total_frames * 100)
                    await send_progress(task_id, progress, connections=connections)

                except Exception as e:
                    print(f"Error processing frame {frame_number}: {str(e)}")
                    continue

                frame_number += 1
                await asyncio.sleep(0.1)

        cap.release()

        # If local processing, handle all frames at once after the loop
        if is_local and frames_metadata:
            await process_local_frames(frames_metadata)

        await send_progress(task_id, 100, connections=connections)
        print("Video processing completed successfully")

    except Exception as e:
        error_message = f"Error in video processing: {str(e)}"
        print(f"🔴 {error_message}")
        await send_progress(task_id, -1, error=error_message, connections=connections)
        raise

async def send_progress(task_id: str, progress: int, error: str = "", connections: Dict[str, WebSocket] = None):
    """Send progress update through WebSocket with better error handling"""
    try:
        if connections and task_id in connections:
            websocket = connections[task_id]
            try:
                await websocket.send_json({
                    "progress": progress,
                    "error": error
                })
                print(f"🟢 Progress update sent: {progress}%{' Error: ' + error if error else ''}")
            except Exception as e:
                print(f"🔴 Failed to send WebSocket message: {str(e)}")
    except Exception as e:
        print(f"🔴 Error in send_progress: {str(e)}")

async def get_frame_description(frame_base64: str, is_local: bool = False) -> str:
    """Get frame description using either local LLaVa or remote GROQ."""
    if is_local:
        try:
            print("🔵 Calling local Ollama LLaVa model...")
            async with aiohttp.ClientSession() as session:
                async with session.post('http://localhost:11434/api/generate', 
                    json={
                        "model": "llava",
                        "prompt": "Describe this image in detail.",
                        "images": [frame_base64],
                        "stream": False  # Add this to get a single response
                    },
                    headers={'Accept': 'application/json'}  # Explicitly request JSON
                ) as response:
                    print(f"🔵 Ollama response status: {response.status}")
                    
                    # Read the raw response text
                    response_text = await response.text()
                    print(f"🔵 Raw response: {response_text[:200]}...")  # Print first 200 chars
                    
                    try:
                        # Try to parse as single JSON
                        result = await response.json()
                        return result.get('response', 'No description available')
                    except json.JSONDecodeError as e:
                        print(f"🔴 JSON decode error: {str(e)}")
                        
                        # Handle streaming response format
                        try:
                            # Split by newlines and parse each line as JSON
                            lines = response_text.strip().split('\n')
                            full_response = ''
                            for line in lines:
                                if line.strip():
                                    try:
                                        json_response = json.loads(line)
                                        if 'response' in json_response:
                                            full_response += json_response['response']
                                    except json.JSONDecodeError:
                                        print(f"🔴 Couldn't parse line: {line}")
                                        continue
                            
                            if full_response:
                                return full_response
                            else:
                                raise ValueError("No valid response found in stream")
                        except Exception as stream_error:
                            print(f"🔴 Error parsing stream: {str(stream_error)}")
                            raise
                        
        except aiohttp.ClientError as e:
            print(f"🔴 Network error calling Ollama: {str(e)}")
            raise
        except Exception as e:
            print(f"🔴 Unexpected error in get_frame_description: {str(e)}")
            raise
    else:
        try:
            print("🔵 Calling remote GROQ API...")
            client = Groq()
            completion = client.chat.completions.create(
                model="llama-3.2-11b-vision-preview",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Describe this image in detail."},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{frame_base64}"}}
                        ]
                    }
                ],
                max_tokens=1024,
            )
            return completion.choices[0].message.content
        except Exception as e:
            print(f"🔴 Error calling GROQ API: {str(e)}")
            raise

async def process_remote_frame(
    frame_description: str,
    metadata: Dict[str, Any],
    embedding_model,
    pinecone_index: pinecone.Index,
    task_id: str,
    frame_number: int
) -> None:
    """Process a frame using remote services (GROQ + Pinecone)"""
    # Generate embedding using Jina
    frame_description_embedding = embedding_model.encode(frame_description).tolist()

    # Upsert single vector to Pinecone
    upsert_response = pinecone_index.upsert(
        vectors=[{
            "id": f"{task_id}_frame_{frame_number}",
            "values": frame_description_embedding,
            "metadata": metadata
        }]
    )
    print(f"Pinecone upsert response for frame {frame_number}: {upsert_response}")

async def process_local_frames(
    frames_metadata: List[Dict[str, Any]]
) -> None:
    """Process all frames using local services (Ollama + FAISS)"""
    embeddings = []
    metadata_list = []
    
    # Get the first embedding to determine dimension
    async with aiohttp.ClientSession() as session:
        async with session.post('http://localhost:11434/api/embeddings', json={
            "model": "mxbai-embed-large",
            "prompt": frames_metadata[0]["description"]
        }) as response:
            result = await response.json()
            first_embedding = result['embedding']
            embedding_dim = len(first_embedding)
            print(f"🟢 Detected embedding dimension: {embedding_dim}")
            
            # Initialize vector DB with correct dimension
            vector_db = LocalVectorDB(dimension=embedding_dim)
            
            # Add first embedding
            embeddings.append(first_embedding)
            metadata_list.append(frames_metadata[0])
            
            # Process remaining frames
            for metadata in frames_metadata[1:]:
                async with session.post('http://localhost:11434/api/embeddings', json={
                    "model": "mxbai-embed-large",
                    "prompt": metadata["description"]
                }) as response:
                    result = await response.json()
                    embedding = result['embedding']
                    embeddings.append(embedding)
                    metadata_list.append(metadata)
    
    try:
        # Insert embeddings into FAISS
        vector_db.add_vectors(embeddings, metadata_list)
        print(f"🟢 Successfully inserted {len(embeddings)} embeddings into FAISS vector database")
    except Exception as e:
        print(f"🔴 Error inserting vectors: {str(e)}")
        print(f"🔴 Embedding dimensions: {[len(emb) for emb in embeddings]}")
        raise

# Example search function (you can add this wherever needed)
async def search_similar_frames(query_description: str, k: int = 5) -> List[Dict]:
    """Search for similar frames using the local vector database"""
    # Get a sample embedding to determine dimension
    async with aiohttp.ClientSession() as session:
        async with session.post('http://localhost:11434/api/embeddings', json={
            "model": "mxbai-embed-large",
            "prompt": query_description
        }) as response:
            result = await response.json()
            query_embedding = result['embedding']
            embedding_dim = len(query_embedding)
            
    # Initialize vector DB with correct dimension
    vector_db = LocalVectorDB(dimension=embedding_dim)
    
    # Search in FAISS
    results = vector_db.search(query_embedding, k)
    return results
