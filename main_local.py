import os
from backend.main import app
import uvicorn
from fastapi.staticfiles import StaticFiles

# Check if we're running on Replit
# Mount the frontend build directory
app.mount("/", StaticFiles(directory="frontend/build", html=True), name="frontend")

if __name__ == "__main__":
    # Use the PORT environment variable or fallback to 8080
    port = int(os.getenv("PORT", "8080"))
    
    # Start the server
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=port,
        reload=True
    )
