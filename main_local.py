import os
import argparse
from pathlib import Path
from dotenv import load_dotenv
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

def load_env():
    parser = argparse.ArgumentParser(description='Run the local server with environment configuration')
    parser.add_argument('--env', default='.env.local', help='Path to env file (default: .env.local)')
    args = parser.parse_args()

    # Load environment variables from file
    env_path = Path(args.env)
    if not env_path.exists():
        print(f"Warning: {args.env} not found. Creating default .env.local file...")
        with open(env_path, 'w') as f:
            f.write("LOCAL=true\nPORT=8000\n")
    
    # Load the env file
    load_dotenv(env_path)
    
    # Explicitly set the environment variables
    os.environ["LOCAL"] = "true"
    
    print(f"Loaded environment from: {env_path}")
    print(f"LOCAL env var: {os.environ.get('LOCAL')}")

# Load environment before any other imports
load_env()

# Create a new FastAPI app
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import routes from backend
from backend.main import app as backend_app
for route in backend_app.routes:
    app.routes.append(route)

# Explicit root handler
@app.get("/")
async def read_root():
    return FileResponse("frontend/build/index.html")

# Add debug endpoint
@app.get("/debug")
async def debug_info():
    build_path = Path("frontend/build")
    return {
        "build_exists": build_path.exists(),
        "files": [str(f) for f in build_path.rglob("*") if f.is_file()],
        "static_exists": (build_path / "static").exists(),
        "index_exists": (build_path / "index.html").exists()
    }

# Mount static files in correct order
app.mount("/static", StaticFiles(directory="frontend/build/static"), name="static")
app.mount("/frames", StaticFiles(directory="frames"), name="frames")
app.mount("/videos", StaticFiles(directory="videos"), name="videos")
app.mount("/video_sample_to_test", StaticFiles(directory="video_sample_to_test"), name="video_sample_to_test")
# Mount the rest of the build directory for other assets
app.mount("/", StaticFiles(directory="frontend/build"), name="frontend")

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    
    print(f"Starting local server on port {port}")
    print(f"Local mode: {os.environ.get('LOCAL', 'false')}")
    
    # Start the server with debug mode enabled
    uvicorn.run(
        "main_local:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        env_file=".env.local",
        log_level="debug"
    )
