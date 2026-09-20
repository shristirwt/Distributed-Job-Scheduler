import os
from dotenv import load_dotenv

load_dotenv()


SCHEDULER_INTERVAL = int(
    os.getenv("SCHEDULER_INTERVAL", 5)
)

RETRY_BASE_DELAY = int(
    os.getenv("RETRY_BASE_DELAY", 5)
)

TASK_TIMEOUT = int(
    os.getenv("TASK_TIMEOUT", 30)
)