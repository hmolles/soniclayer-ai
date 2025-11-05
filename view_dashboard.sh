#!/bin/bash

# Simple script to view dashboard for a specific audio ID
# Usage: ./view_dashboard.sh <audio_id>

if [ -z "$1" ]; then
    echo "❌ Error: Please provide an audio ID"
    echo ""
    echo "Usage: ./view_dashboard.sh <audio_id>"
    echo ""
    echo "To get an audio ID, upload a file to the API:"
    echo "  curl -X POST -F \"file=@your_audio.wav\" http://localhost:8000/evaluate/"
    echo ""
    exit 1
fi

AUDIO_ID="$1"

# Check if audio file exists
if [ ! -f "uploads/${AUDIO_ID}.wav" ]; then
    echo "❌ Error: Audio file not found: uploads/${AUDIO_ID}.wav"
    echo ""
    echo "Make sure you've uploaded the audio file first."
    exit 1
fi

echo "🎵 Starting dashboard for audio: ${AUDIO_ID}"
echo ""
echo "The dashboard will open in the Replit webview."
echo "Press Ctrl+C to stop."
echo ""

PORT=5000 python dashboard/app.py "$AUDIO_ID"
