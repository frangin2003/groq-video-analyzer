import os
import base64
import cv2
import aiohttp
from fastapi import WebSocket
from typing import Dict, List
import pinecone

# Background task to process video
async def process_video(task_id: str, video_path: str, index: pinecone.Index):
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

async def send_progress(task_id: str, progress: int, error: str = "", connections: Dict[str, WebSocket] = None):
    if task_id in connections:
        websocket = connections[task_id]
        await websocket.send_json({"progress": progress, "error": error})

