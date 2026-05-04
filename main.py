# Entry point for Render deployment
# This file re-exports the FastAPI app from backend/main.py
# so that the default uvicorn command works correctly

from backend.main import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
