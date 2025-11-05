#!/bin/bash
# Start RQ worker with macOS fork fix
#
# This script sets the OBJC_DISABLE_INITIALIZE_FORK_SAFETY environment variable
# to prevent crashes on macOS when RQ forks worker processes.
#
# Usage: ./scripts/start_worker.sh

cd "$(dirname "$0")/.."

# Activate virtual environment
source venv/bin/activate

# Set environment variable to fix macOS fork issue
export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES

# Start RQ worker
echo "Starting RQ worker with macOS fork safety disabled..."
echo "Worker will process jobs from queue: transcript_tasks"
echo "Press Ctrl+C to stop"
echo ""

rq worker transcript_tasks
