import redis
import os
from rq import Queue

# Use port 6000 for Replit (6379 not available for workflows)
REDIS_PORT = int(os.getenv("REDIS_PORT", 6000))

# Connect to Redis server
redis_conn = redis.Redis(host='localhost', port=REDIS_PORT, db=0)

# Create a task queue named 'transcript_tasks'
task_queue = Queue('transcript_tasks', connection=redis_conn)
