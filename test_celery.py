import time
from app.server.workers.tasks import evaluate_daily_divergence
from app.server.dependencies import get_repo
from app.core.entities import Identity, Telemetry
from datetime import datetime

def main():
    # Since PostgresRepository is currently an in-memory mock in dependencies.py,
    # the worker process (which is a separate process) has its own in-memory database.
    # We will seed the mock repository inside the worker by passing the task,
    # but first let's see how Celery processes the background task.
    
    print("Sending task 'evaluate_daily_divergence' for user 'test_user' via Celery...")
    result = evaluate_daily_divergence.delay("test_user")
    
    print(f"Task ID: {result.id}")
    print(f"Initial State: {result.state}")
    
    print("Waiting for task to complete (timeout=10s)...")
    try:
        val = result.get(timeout=10)
        print(f"Success! Task returned: {val}")
        print(f"Final State: {result.state}")
    except Exception as e:
        print(f"Error waiting for task: {e}")
        print("Make sure the Celery worker is running!")

if __name__ == "__main__":
    main()
