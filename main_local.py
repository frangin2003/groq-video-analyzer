import os
import argparse
from pathlib import Path
from dotenv import load_dotenv
import uvicorn
from fastapi.staticfiles import StaticFiles

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

# Now import the app after environment is set
from backend.main import app

# Mount the frontend build directory
app.mount("/", StaticFiles(directory="frontend/build", html=True), name="frontend")

if __name__ == "__main__":
    # Use the PORT environment variable or fallback to 8000
    port = int(os.getenv("PORT", "8000"))
    
    print(f"Starting local server on port {port}")
    print(f"Local mode: {os.environ.get('LOCAL', 'false')}")
    
    # Start the server
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        env_file=".env.local"
    )
