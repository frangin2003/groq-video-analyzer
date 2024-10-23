import os
import base64
import cv2
import aiohttp
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

        current_frame = 0
        frame_number = 0

        client = Groq()

        async with aiohttp.ClientSession() as session:
            while True:
                ret, frame = cap.read()
                # Calculate timestamp based on frame number and frame interval
                timestamp = frame_number * frame_interval / fps
                print(f"Timestamp for frame {frame_number}: {timestamp:.2f} seconds")
                if not ret:
                    break

                if current_frame % frame_interval == 0:
                    # Check if the frame is mainly full same color (like full black or full white)
                    frame_number += 1
                    if not (cv2.countNonZero(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)) == 0 or cv2.countNonZero(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)) == frame.size // 3):
                        # Resize frame proportionally to 1120 width before saving
                        target_width = 1120
                        height, width, _ = frame.shape
                        aspect_ratio = height / width
                        target_height = int(target_width * aspect_ratio)
                        resized_frame = cv2.resize(frame, (target_width, target_height))

                        # Save resized frame to disk
                        frame_filename = f"frames/{task_id}_frame_{frame_number}.jpg"
                        os.makedirs(os.path.dirname(frame_filename), exist_ok=True)
                        cv2.imwrite(frame_filename, resized_frame)
                    else:
                        print(f"Skipped frame {frame_number} as it is mainly full same color.")
                        continue

                    # Read image and encode to base64
                    with open(frame_filename, "rb") as image_file:
                        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')

                    # Print encoded string
                    print(f"Encoded string for frame {frame_number}:")
                    print(encoded_string[:100] + "..." if len(encoded_string) > 100 else encoded_string)
                    print()

                    # Call GROQ API to describe image
                    completion = client.chat.completions.create(
                        model="llama-3.2-11b-vision-preview",
                        messages=[
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "text",
                                        "text": "Describe this image in detail in 3-4 sentences. Provide the following details:\n\nA short summary of the scene.\nAssumed location (urban, rural, indoor, outdoor, etc.).\nAssumed time of day.\nAssumed weather conditions.\nNumber of people or animals and their description (clothing, posture, expression).\nDescription of actions being performed.\nVisible objects or buildings.\nType of ground and sky conditions.\nOverall composition of the image."
                                    },
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": f"data:image/jpeg;base64,{encoded_string}"
                                        }
                                    }
                                ]
                            }
                        ],
                        temperature=1,
                        max_tokens=1024,
                        top_p=1,
                        stream=False,
                        stop=None,
                    )
                    frame_description = completion.choices[0].message.content
                    print(frame_description)

                    # generate embedding
                    embedding_model = AutoModel.from_pretrained('jinaai/jina-embeddings-v2-base-en', trust_remote_code=True)
                    frame_description_embedding = embedding_model.encode(frame_description).tolist()

                    # insert into pinecone
                    metadata = {
                        "task_id": task_id,
                        "timecode": current_frame / fps,
                        "timestamp": timestamp,
                        "frame_number": frame_number,
                        "frame_path": f'frames/{task_id}_frame_{frame_number}.jpg',
                        "video_path": '../videos/paris_short.mp4',
                        "description": frame_description
                    }
                    upsert_response = pinecone_index.upsert(
                        vectors=[
                            {
                                "id": f"{task_id}_frame_{frame_number}",
                                "values": frame_description_embedding,
                                "metadata": metadata
                            }
                        ]
                    )
                    print(upsert_response)

                    # Update progress
                    progress = int((frame_number / total_frames) * 100)
                    await send_progress(task_id, progress, connections=connections)

                current_frame += 1

        cap.release()
        await send_progress(task_id, 100)
    except Exception as e:
        await send_progress(task_id, -1, str(e), connections=connections)

async def send_progress(task_id: str, progress: int, error: str = "", connections: Dict[str, WebSocket] = None):
    if task_id in connections:
        websocket = connections[task_id]
        await websocket.send_json({"progress": progress, "error": error})

