#!/usr/bin/env python3
"""
Startup script for Dash dashboard
Usage: python run_dashboard.py [audio_id]
"""
import sys
import os

# Get audio_id from command line or environment or use default
audio_id = (
    sys.argv[1] if len(sys.argv) > 1 
    else os.getenv('AUDIO_ID', '50f5315356317fa1a803bc5a754e4899d3275b711590f5baa7db35947f04bf70')
)

# Set environment variable for dashboard
os.environ['AUDIO_ID'] = audio_id
os.environ['PORT'] = '5000'  # Replit webview port
os.environ['BACKEND_PORT'] = '8000'  # Backend API port

print(f"Starting Dash dashboard for audio: {audio_id}")
print(f"Dashboard will be available at http://localhost:5000")
print(f"Backend API at http://localhost:8000")

# Import and run the dashboard
sys.path.insert(0, '/home/runner/workspace')
sys.argv = ['dashboard/app.py', audio_id]

import dashboard.app as dash_app
