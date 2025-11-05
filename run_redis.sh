#!/bin/bash
# Start Redis server with persistence enabled for Replit
echo "Starting Redis on port 6000 with AOF persistence..."

# Create persistent data directory
mkdir -p redis_data

# Start Redis with AOF persistence enabled
redis-server --port 6000 \
  --dir ./redis_data \
  --appendonly yes \
  --appendfsync everysec \
  --save 900 1 \
  --save 300 10 \
  --save 60 10000
