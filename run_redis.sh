#!/bin/bash
# Start Redis server in foreground for Replit
echo "Starting Redis on port 6000..."
redis-server --port 6000 --dir /tmp --save "" --appendonly no
