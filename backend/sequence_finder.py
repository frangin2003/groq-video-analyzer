import os
os.environ['KMP_DUPLICATE_LIB_OK']='True'

from typing import Dict, List, Any
import pinecone
from groq import Groq
from transformers import AutoModel
import aiohttp
from collections import defaultdict
from .vector_db import LocalVectorDB
import tempfile
from moviepy.editor import VideoFileClip
from fastapi.responses import StreamingResponse

async def get_remote_embedding(query: str, embedding_model) -> List[float]:
    """Get embedding using Hugging Face model."""
    return embedding_model.encode(query).tolist()

async def get_local_embedding(query: str) -> List[float]:
    """Get embedding using Ollama."""
    async with aiohttp.ClientSession() as session:
        async with session.post('http://localhost:11434/api/embeddings', json={
            "model": "mxbai-embed-large",
            "prompt": query
        }) as response:
            result = await response.json()
            return result['embedding']

async def search_remote_database(query_embedding: List[float], pinecone_index: pinecone.Index, k: int = 5) -> List[Dict]:
    """Search Pinecone database."""
    result = pinecone_index.query(
        vector=query_embedding,
        top_k=k,
        include_values=False,
        include_metadata=True
    )
    return result.matches

async def search_local_database(query_embedding: List[float], k: int = 5) -> List[Dict]:
    """Search local FAISS database."""
    vector_db = LocalVectorDB()
    return vector_db.search(query_embedding, k)

def format_timestamp(seconds: float) -> str:
    """Format seconds into HH:MM:SS string."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

def group_frames_into_sequences(matches: List[Dict]) -> List[Dict]:
    """Group consecutive frames into sequences."""
    # Group frames by video path
    video_groups = defaultdict(list)
    
    for match in matches:
        # Handle both Pinecone and FAISS result formats
        if hasattr(match, 'metadata'):  # Pinecone format
            metadata = match.metadata
            score = float(match.score)
            id = match.id
        else:  # FAISS format
            metadata = match
            score = 1.0 - float(match.get('distance', 0))  # Convert distance to similarity score
            id = str(metadata.get('frame_number', ''))  # Use frame number as ID
            
        video_groups[metadata['video_path']].append({
            'frame': metadata['frame_number'],
            'frame_path': metadata['frame_path'],
            'timestamp': metadata['timestamp'],
            'metadata': metadata,
            'score': score,
            'id': id
        })
    
    sequences = []
    for video_path, frames in video_groups.items():
        # Sort frames by frame number
        frames.sort(key=lambda x: x['frame'])
        current_sequence = [frames[0]]
        
        for i in range(1, len(frames)):
            # Allow for one frame gap (frame difference of 2 or less)
            if frames[i]['frame'] <= current_sequence[-1]['frame'] + 2:
                current_sequence.append(frames[i])
            else:
                sequences.extend(create_sequence(current_sequence, video_path))
                current_sequence = [frames[i]]
        
        # Add the last sequence
        if len(current_sequence) > 1:
            sequences.extend(create_sequence(current_sequence, video_path))
    
    # Sort sequences by score
    sequences.sort(key=lambda x: x['score'], reverse=True)
    return sequences

def create_sequence(frames: List[Dict], video_path: str) -> List[Dict]:
    """Create a sequence from a list of consecutive frames."""
    if len(frames) <= 1:
        return []
        
    start_time = frames[0]['timestamp']
    end_time = frames[-1]['timestamp']
    
    return [{
        'video_path': video_path,
        'frame_start': frames[0]['frame'],
        'frame_end': frames[-1]['frame'],
        'time_start': start_time,
        'time_end': end_time,
        'time_start_formatted': format_timestamp(start_time),
        'time_end_formatted': format_timestamp(end_time),
        'duration': end_time - start_time,
        'frames': frames,
        'frame_paths': [f['frame_path'] for f in frames],
        'score': sum(f['score'] for f in frames) / len(frames),
        'description': frames[0]['metadata']['description']
    }]

def format_sequences_for_response(sequences: List[Dict]) -> List[Dict]:
    """Format sequences for API response."""
    return [{
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

async def search_video_sequences(
    user_query: str,
    pinecone_index: pinecone.Index = None,
    is_local: bool = False,
    k: int = 5
) -> Dict:
    """Search for video sequences and return formatted results."""
    print(f"🟢 Starting search for query: {user_query}")
    try:
        # Get query embedding
        print("🟢 Generating query embedding")
        if is_local:
            query_embedding = await get_local_embedding(user_query)
        else:
            if not pinecone_index:
                raise ValueError("Pinecone index required for remote search")
            embedding_model = AutoModel.from_pretrained('jinaai/jina-embeddings-v2-base-en', trust_remote_code=True)
            query_embedding = await get_remote_embedding(user_query, embedding_model)

        # Search database
        print("🟢 Searching database")
        if is_local:
            results = await search_local_database(query_embedding, k)
        else:
            results = await search_remote_database(query_embedding, pinecone_index, k)
        print(f"🟢 Search completed. Found {len(results)} matches")

        # Process results
        if len(results) > 0:
            sequences = group_frames_into_sequences(results)
            formatted_sequences = format_sequences_for_response(sequences)
            return {
                "status": "success",
                "results": formatted_sequences,
                "count": len(formatted_sequences)
            }
        else:
            return {
                "status": "success",
                "results": [],
                "count": 0
            }

    except Exception as e:
        error_message = f"Error in search: {str(e)}"
        print(f"🔴 {error_message}")
        return {
            "status": "error",
            "error": error_message,
            "results": [],
            "count": 0
        }

async def extract_video_sequence(
    video_path: str,
    time_start: float,
    time_end: float
) -> StreamingResponse:
    """Extract a video sequence between two timestamps."""
    print("🟢 Extracting video sequence")
    try:
        # Load video with moviepy
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
        raise e
