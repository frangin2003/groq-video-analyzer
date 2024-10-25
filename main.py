import os
from backend.main import app
import uvicorn
from fastapi.staticfiles import StaticFiles

# Check if we're running on Replit
IS_REPLIT = os.getenv("REPL_ID") is not None

if IS_REPLIT:
    # Build the frontend
    os.system("cd frontend && npm install && npm run build")
    
    # Mount the frontend build directory
    app.mount("/", StaticFiles(directory="frontend/build", html=True), name="frontend")
    
    # Mount API routes under /api
    app.mount("/api", app)

if __name__ == "__main__":
    if IS_REPLIT:
        uvicorn.run(app, host="0.0.0.0", port=8080)
    else:
        uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
