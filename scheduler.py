import threading
import logging
from datetime import datetime, timedelta
from database import SessionLocal
from models import Job, JobExecution
from tasks import JOB_FUNCTIONS
from config import SCHEDULER_INTERVAL, RETRY_BASE_DELAY


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)

logger = logging.getLogger("scheduler")


scheduler_stop_event = threading.Event()


def execute_job(job):
    logger.info(f"Executing job: {job.name}")
    logger.info(f"Job id: {job.id}")
    
    task_info = JOB_FUNCTIONS.get(job.name)

    if task_info is None:
        raise Exception(f"Unknown job: {job.name}")

    task = task_info["function"]

    task()
    
    logger.info(f"Job {job.id} executed successfully!")
    
    
def claim_job(db):
    job = db.query(Job).filter(
        Job.status == "SCHEDULED",
        Job.run_at <= datetime.now()
    ).with_for_update(skip_locked=True).first()

    if job is None:
        return None

    job.status = "RUNNING"
    db.commit()
    db.refresh(job)

    return job


def create_execution(db, job):
    execution = JobExecution(
        job_id=job.id,
        started_at=datetime.now(),
        status="RUNNING"
    )

    db.add(execution)
    db.commit()
    db.refresh(execution)

    return execution


def handle_success(db, job, execution):
    execution.finished_at = datetime.now()
    execution.status = "SUCCESS"

    if job.recurring:
        job.run_at = datetime.now() + timedelta(
            seconds=job.interval_seconds
        )
        job.status = "SCHEDULED"
    else:
        job.status = "COMPLETED"

    job.retry_count = 0
    db.commit()


def handle_failure(db, job, execution, error):
    logger.error(f"Job {job.id} failed: {error}")

    execution.finished_at = datetime.now()
    execution.status = "FAILED"

    if job.retry_count < job.max_retries:
        job.retry_count += 1

        delay = RETRY_BASE_DELAY * (2 ** (job.retry_count - 1))

        job.run_at = datetime.now() + timedelta(seconds=delay)
        job.status = "SCHEDULED"

        logger.warning(
            f"Retrying job {job.id} "
            f"({job.retry_count}/{job.max_retries}) "
            f"after {delay} seconds"
        )

    else:
        job.status = "FAILED"
        logger.error(f"Job {job.id} permanently failed")

    db.commit()
    
    
def check_jobs():
    db = SessionLocal()
    
    try:
        while True:
            
            job = claim_job(db)
            
            if job is None:
                break
            
            execution = create_execution(db, job)
            
            try:
                execute_job(job)   
                handle_success(db, job, execution)
                
            except Exception as e:
                handle_failure(db, job, execution, e)
            
            
    finally:
        db.close()
        
        
def start_scheduler():
    logger.info("Scheduler started...")
    
    while not scheduler_stop_event.is_set():
        check_jobs()
        scheduler_stop_event.wait(SCHEDULER_INTERVAL)
        
    logger.info("Scheduler stopped.")
        
        
if __name__ == "__main__":
    start_scheduler()