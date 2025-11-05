#!/usr/bin/env python3
"""
Main entry point for SonicLayer AI backend with Azure OpenAI integration.
Runs the FastAPI backend on port 5000 for Replit webview.
"""
import uvicorn

if __name__ == "__main__":
    # Start FastAPI on port 5000 (Replit webview requirement)
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=5000,
        log_level="info",
        reload=False  # Disable reload in production
    )
