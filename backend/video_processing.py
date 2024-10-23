import os
import base64
import cv2
import aiohttp
import asyncio
from fastapi import WebSocket
from typing import Dict, List
import pinecone
from groq import Groq
from transformers import AutoModel


# Background task to process video
async def process_video(task_id: str, video_path: str, pinecone_index: pinecone.Index, connections: Dict[str, WebSocket]):
    try:
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_interval = int(fps * 2)  # every 2 seconds

        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        total_frames = frame_count // frame_interval

        frame_number = 0
        processed_frames = 0

        client = Groq()

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

                # Call GROQ API to describe image
                try:
                    completion = client.chat.completions.create(
                        model="llama-3.2-11b-vision-preview",
                        messages=[
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": "Describe this image in detail."},
                                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded_string}"}}
                                ]
                            }
                        ],
                        max_tokens=1024,
                    )
                    frame_description = completion.choices[0].message.content
                    print(f"Frame {frame_number} description: {frame_description[:100]}...")

                    # Generate embedding and insert into Pinecone
                    embedding_model = AutoModel.from_pretrained('jinaai/jina-embeddings-v2-base-en', trust_remote_code=True)
                    frame_description_embedding = embedding_model.encode(frame_description).tolist()

                    metadata = {
                        "task_id": task_id,
                        "timestamp": timestamp,
                        "frame_number": frame_number,
                        "frame_path": frame_filename,
                        "video_path": video_path,
                        "description": frame_description
                    }
                    upsert_response = pinecone_index.upsert(
                        vectors=[{
                            "id": f"{task_id}_frame_{frame_number}",
                            "values": frame_description_embedding,
                            "metadata": metadata
                        }]
                    )
                    print(f"Pinecone upsert response: {upsert_response}")

                    processed_frames += 1
                    progress = int((processed_frames / total_frames) * 100)
                    await send_progress(task_id, progress, connections=connections)

                except Exception as e:
                    print(f"Error processing frame {frame_number}: {str(e)}")

                frame_number += 1
                await asyncio.sleep(0.1)  # Add a small delay to prevent overwhelming the system

        cap.release()
        await send_progress(task_id, 100, connections=connections)
        print("Video processing completed successfully")

    except Exception as e:
        error_message = f"Error in video processing: {str(e)}"
        print(error_message)
        await send_progress(task_id, -1, error=error_message, connections=connections)

async def send_progress(task_id: str, progress: int, error: str = "", connections: Dict[str, WebSocket] = None):
    if connections and task_id in connections:
        websocket = connections[task_id]
        try:
            await websocket.send_json({"progress": progress, "error": error})
        except Exception as e:
            print(f"Error sending progress update: {str(e)}")
