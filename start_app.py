#!/usr/bin/env python3
"""
Simplified startup script for SonicLayer AI on Replit
This starts a simple demo dashboard on port 5000
"""
import os
import sys

# Set environment variables
os.environ["PORT"] = "5000"
os.environ["REDIS_HOST"] = "localhost"
os.environ["REDIS_PORT"] = "6379"

# For now, we'll create a simple welcome page since the full app requires ML dependencies
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(title="SonicLayer AI - Replit Setup")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", response_class=HTMLResponse)
def read_root():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>SonicLayer AI</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                max-width: 800px;
                margin: 50px auto;
                padding: 20px;
                background: #f3f4f6;
            }
            .container {
                background: white;
                padding: 30px;
                border-radius: 8px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }
            h1 { color: #111827; margin-top: 0; }
            h2 { color: #374151; border-bottom: 2px solid #e5e7eb; padding-bottom: 10px; }
            .status { 
                padding: 10px;
                margin: 10px 0;
                border-radius: 4px;
                background: #fef3c7;
                border-left: 4px solid #f59e0b;
            }
            .feature { margin: 10px 0; padding-left: 20px; }
            code {
                background: #f3f4f6;
                padding: 2px 6px;
                border-radius: 3px;
                font-family: monospace;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎵 SonicLayer AI</h1>
            <p>An intelligent audio insight system for producers and content teams.</p>
            
            <div class="status">
                <strong>⚠️ Setup Required</strong><br>
                This application requires additional ML dependencies (PyTorch, Whisper, Transformers) 
                that are too large for the current Replit environment.
            </div>
            
            <h2>Features</h2>
            <div class="feature">✓ WAV audio upload and transcription via Whisper</div>
            <div class="feature">✓ Segment classification (topic, tone)</div>
            <div class="feature">✓ Langflow-powered persona evaluation</div>
            <div class="feature">✓ Interactive dashboard with waveform overlays</div>
            <div class="feature">✓ Redis-based caching and RQ background jobs</div>
            
            <h2>Tech Stack</h2>
            <p>Python 3.11, FastAPI, Redis, Whisper, HuggingFace, Langflow, Dash + Plotly</p>
            
            <h2>To Run Locally</h2>
            <ol>
                <li>Clone this repository to your local machine</li>
                <li>Install ML dependencies: <code>pip install torch transformers openai-whisper librosa scipy</code></li>
                <li>Start Redis: <code>redis-server</code></li>
                <li>Start backend: <code>uvicorn app.main:app --reload</code></li>
                <li>Start worker: <code>rq worker transcript_tasks</code></li>
                <li>Upload audio via API and launch dashboard</li>
            </ol>
            
            <h2>Documentation</h2>
            <ul>
                <li><a href="https://github.com/yourusername/soniclayer-ai">View README.md</a></li>
                <li><a href="/docs">API Documentation</a> (when backend is running)</li>
            </ul>
            
            <p><em>See <code>README.md</code> and <code>QUICK_START.md</code> for complete setup instructions.</em></p>
        </div>
    </body>
    </html>
    """

@app.get("/health")
def health():
    return {"status": "ok", "message": "SonicLayer AI - Setup required for full functionality"}

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🎵 SonicLayer AI - Replit Environment")
    print("="*60)
    print("\n⚠️  Note: This is a simplified version.")
    print("   Full ML features require PyTorch, Whisper, and Transformers")
    print("   which are too large for Replit's current environment.")
    print("\n🌐 Starting web server on http://0.0.0.0:5000")
    print("="*60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=5000, log_level="info")
