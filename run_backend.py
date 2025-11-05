#!/usr/bin/env python3
"""
Main entry point for SonicLayer AI backend with Azure OpenAI integration.
Runs the FastAPI backend on port 5000 for Replit webview.
"""
import uvicorn

if __name__ == "__main__":
    import os
    # Start FastAPI on port 8000 (Dash frontend uses port 5000)
    port = int(os.getenv("BACKEND_PORT", 8000))
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        log_level="info",
        reload=False  # Disable reload in production
    )
