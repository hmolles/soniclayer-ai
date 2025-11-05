import redis
from rq import Queue

# Connect to Redis server
redis_conn = redis.Redis(host='localhost', port=6379, db=0)

# Create a task queue named 'transcript_tasks'
task_queue = Queue('transcript_tasks', connection=redis_conn)