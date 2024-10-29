import os
os.environ['KMP_DUPLICATE_LIB_OK']='True'

import faiss
import numpy as np
import json
from pathlib import Path
from typing import Dict, List, Any

class LocalVectorDB:
    def __init__(self, dimension: int = 768, index_path: str = "vector_db"):
        """Initialize FAISS index
        Args:
            dimension: Size of embedding vectors (768 for mxbai-embed-large)
            index_path: Directory to store the index and metadata
        """
        self.dimension = dimension
        self.index_path = Path(index_path)
        self.index_file = self.index_path / "faiss.index"
        self.metadata_file = self.index_path / "metadata.json"
        
        # Create directory if it doesn't exist
        self.index_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize or load the index
        if self.index_file.exists():
            print("🟢 Loading existing FAISS index...")
            self.index = faiss.read_index(str(self.index_file))
            with open(self.metadata_file, 'r') as f:
                self.metadata = json.load(f)
        else:
            print("🟡 Creating new FAISS index...")
            self.index = faiss.IndexFlatL2(dimension)
            self.metadata = []

    def add_vectors(self, vectors: List[List[float]], metadata_list: List[Dict[str, Any]]) -> None:
        """Add vectors and their metadata to the index
        Args:
            vectors: List of embedding vectors
            metadata_list: List of metadata dictionaries corresponding to the vectors
        """
        try:
            # Convert vectors to numpy array
            vectors_np = np.array(vectors).astype('float32')
            
            # Add vectors to FAISS index
            self.index.add(vectors_np)
            
            # Add metadata
            self.metadata.extend(metadata_list)
            
            # Save index and metadata
            self._save_index()
            
            print(f"🟢 Successfully added {len(vectors)} vectors to FAISS index")
        except Exception as e:
            print(f"🔴 Error adding vectors to FAISS index: {str(e)}")
            raise

    def search(self, query_vector: List[float], k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar vectors
        Args:
            query_vector: Query embedding vector
            k: Number of results to return
        Returns:
            List of metadata for the k most similar vectors
        """
        try:
            # Convert query vector to numpy array
            query_np = np.array([query_vector]).astype('float32')
            
            # Search the index
            distances, indices = self.index.search(query_np, k)
            
            # Get metadata for results
            results = []
            for idx, dist in zip(indices[0], distances[0]):
                if idx < len(self.metadata):  # Check if index is valid
                    result = self.metadata[idx].copy()
                    result['distance'] = float(dist)  # Add distance score
                    results.append(result)
            
            return results
        except Exception as e:
            print(f"🔴 Error searching FAISS index: {str(e)}")
            raise

    def _save_index(self) -> None:
        """Save the FAISS index and metadata to disk"""
        try:
            faiss.write_index(self.index, str(self.index_file))
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f)
            print("🟢 Saved FAISS index and metadata to disk")
        except Exception as e:
            print(f"🔴 Error saving FAISS index: {str(e)}")
            raise

    def __len__(self) -> int:
        """Return the number of vectors in the index"""
        return self.index.ntotal