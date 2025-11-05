#!/usr/bin/env python3
"""
Start RQ worker to process persona evaluation jobs.
"""
from redis import Redis
from rq import Worker

if __name__ == "__main__":
    redis_conn = Redis(host='localhost', port=6000)
    worker = Worker(['transcript_tasks'], connection=redis_conn)
    print("🔧 Starting RQ worker to process persona evaluation jobs...")
    print("📋 Queue: transcript_tasks")
    print("Press Ctrl+C to stop\n")
    worker.work()
