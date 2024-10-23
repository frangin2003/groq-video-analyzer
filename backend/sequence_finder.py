from fastapi import WebSocket
from typing import Dict, List
import pinecone
from groq import Groq
from transformers import AutoModel

# Background task to search for sequences
async def search_video_sequences(task_id: str, user_query: str, pinecone_index: pinecone.Index, connections: Dict[str, WebSocket]):
    print(f"🟢 Starting search_video_sequences for task_id: {task_id}")
    try:
        # Send initial status
        if task_id in connections:
            print(f"🟢 Sending initial status for task_id: {task_id}")
            await connections[task_id].send_json({
                "status": "Starting search process..."
            })

        print("🟢 Loading embedding model")
        embedding_model = AutoModel.from_pretrained('jinaai/jina-embeddings-v2-base-en', trust_remote_code=True)
        print("🟢 Embedding model loaded successfully")
        
        # Update status
        if task_id in connections:
            print(f"🟢 Sending embedding status for task_id: {task_id}")
            await connections[task_id].send_json({
                "status": "Generating embeddings..."
            })

        print(f"🟢 Generating embeddings for query: {user_query}")
        user_query_embedding = embedding_model.encode(user_query).tolist()
        print("🟢 Embeddings generated successfully")

        # Update status
        if task_id in connections:
            print(f"🟢 Sending search status for task_id: {task_id}")
            await connections[task_id].send_json({
                "status": "Searching vector database..."
            })

        print("🟢 Querying Pinecone")
        result = pinecone_index.query(
            vector=user_query_embedding,
            top_k=5,
            include_values=False,
            include_metadata=True
        )
        print(f"🟢 Pinecone query completed. Found {len(result.matches)} matches")

        # Send results back to frontend
        if task_id in connections:
            print(f"🟢 Sending results for task_id: {task_id}")
            await connections[task_id].send_json({
                "status": "Complete",
                "results": result.matches
            })
            print("🟢 Results sent successfully")

    except Exception as e:
        print(f"🔴 Error in search_video_sequences: {str(e)}")
        if task_id in connections:
            await connections[task_id].send_json({
                "error": str(e)
            })
    finally:
        # Clean up connection if needed
        if task_id in connections:
            print(f"🟢 Cleaning up connection for task_id: {task_id}")
            del connections[task_id]
            print(f"🟢 Connection cleaned up for task_id: {task_id}")

async def search_video_sequences(user_query: str, pinecone_index: pinecone.Index):
    """
    Search for video sequences using the query and return matches from Pinecone.
    """
    print(f"🟢 Starting search for query: {user_query}")
    try:
        # Load embedding model
        print("🟢 Loading embedding model")
        embedding_model = AutoModel.from_pretrained('jinaai/jina-embeddings-v2-base-en', trust_remote_code=True)
        print("🟢 Embedding model loaded successfully")

        # Generate embeddings
        print(f"🟢 Generating embeddings for query: {user_query}")
        user_query_embedding = embedding_model.encode(user_query).tolist()
        print("🟢 Embeddings generated successfully")

        # Query Pinecone
        print("🟢 Querying Pinecone")
        result = pinecone_index.query(
            vector=user_query_embedding,
            top_k=5,
            include_values=False,
            include_metadata=True
        )
        print(f"🟢 Pinecone query completed. Found {len(result.matches)} matches")

        return result.matches

    except Exception as e:
        print(f"🔴 Error in search_video_sequences: {str(e)}")
        raise e
