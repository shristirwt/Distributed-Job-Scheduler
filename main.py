from fastapi import FastAPI, Depends, HTTPException, status
from contextlib import asynccontextmanager
from pydantic import BaseModel, model_validator
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import SessionLocal
from models import Job as JobModel, JobExecution
from scheduler import start_scheduler, scheduler_stop_event
from tasks import JOB_FUNCTIONS
import threading
import logging


logger = logging.getLogger("main")

scheduler_thread = None 

@asynccontextmanager
async def lifespan(app:FastAPI):
    
    global scheduler_thread
    
    scheduler_stop_event.clear()
    
    scheduler_thread = threading.Thread(
        target= start_scheduler,
        daemon=True
    )
    
    scheduler_thread.start()
    
    logger.info("Application started.")
    
    yield
    
    logger.info("Stopping scheduler")
    scheduler_stop_event.set()
    scheduler_thread.join()
    
    logger.info("Application stopped.")
    

app = FastAPI(lifespan=lifespan)

# Database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
    

@app.get("/scheduler/status")
async def scheduler_status():
    
    if scheduler_thread is not None and scheduler_thread.is_alive():
        return {
            "scheduler": "running"
        }
    
    return {
        "scheduler": "stopped"
    }
    

@app.get("/health")
async def health(db: Session = Depends(get_db)):
    
    try:
        db.execute(text("SELECT 1"))
        database_status = "running"
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable"
        )

    scheduler_running = (
        scheduler_thread is not None
        and scheduler_thread.is_alive()
    )

    return {
        "application": "running",
        "scheduler": "running" if scheduler_running else "stopped",
        "database": database_status
    }
    
    
@app.get("/tasks")
async def get_tasks():
    return {
        "tasks": [
            {
                "name": name,
                "description": task_info["description"]
            }
            for name, task_info in JOB_FUNCTIONS.items()
        ]
    }


class Job(BaseModel):
    name: str
    run_at: datetime
    recurring: bool = False
    interval_seconds: int | None = None
    max_retries: int = 0
    
    @model_validator(mode="after")
    def validate_interval(self):
        if self.recurring and self.interval_seconds is None:
            raise ValueError("interval_seconds is required for recurring jobs")
        
        if self.interval_seconds is not None and self.interval_seconds <= 0:
            raise ValueError("interval_seconds must be greater than 0")
        
        if self.max_retries < 0:
            raise ValueError("max_retries cannot be negative")
        
        return self
    
    
class JobUpdate(BaseModel):
    name: str
    run_at: datetime 
    recurring: bool = False
    interval_seconds: int | None = None 
    max_retries: int = 0
    
    
    @model_validator(mode="after")
    def validate_interval(self):
        if self.recurring and self.interval_seconds is None:
            raise ValueError("interval_seconds is required for recurring jobs")
        
        if self.interval_seconds is not None and self.interval_seconds <= 0:
            raise ValueError("interval_seconds must be greater than 0")
        
        if self.max_retries < 0:
            raise ValueError("max_retries cannot be negative")
                
        return self


@app.get("/")
async def root():
    return {"message" : "Hello world"}

@app.post("/jobs")
async def create_jobs(job: Job, db: Session = Depends(get_db)):
    
    if job.name not in JOB_FUNCTIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown job: {job.name}"
        )
        
    new_job = JobModel(
        name=job.name,
        run_at=job.run_at,
        recurring=job.recurring,
        interval_seconds = job.interval_seconds,
        max_retries= job.max_retries
    )
    
    db.add(new_job)
    db.commit()
    db.refresh(new_job)
    
    return {
        "message" : "Job Posted",
        "job": {
            "id": new_job.id,
            "name":new_job.name,
            "run_at":new_job.run_at,
            "recurring":new_job.recurring,
            "interval_seconds":new_job.interval_seconds,
            "status":new_job.status,
            "max_retries": new_job.max_retries,
            "retry_count": new_job.retry_count
        }
    }

@app.get("/jobs")
async def get_jobs(skip: int=0, limit: int=10, db: Session = Depends(get_db)):
    
    if skip < 0:
        raise HTTPException(
            status_code=400,
            detail="skip cannot be negative"
        )
    
    if limit <= 0:
        raise HTTPException(
            status_code=400,
            detail="limit must be greater than 0"
        )
    
    if limit > 100:
        raise HTTPException(
            status_code=400,
            detail="limit cannot be greater than 100"
        )
    
    jobs = db.query(JobModel).offset(skip).limit(limit).all()
    
    total_jobs = db.query(JobModel).count()
    
    return {
        "message": "Jobs Found",
        "skip": skip,
        "limit": limit,
        "total_jobs": total_jobs,
        "jobs": [
            {
                "id": job.id,
                "name": job.name,
                "run_at": job.run_at,
                "recurring": job.recurring,
                "interval_seconds": job.interval_seconds,
                "status": job.status,
                "max_retries": job.max_retries,
                "retry_count": job.retry_count
            }
            for job in jobs
        ]
    }

@app.get("/jobs/{job_id}")
async def get_job_by_id(job_id: int, db: Session = Depends(get_db)):
    
    job = db.query(JobModel).filter(JobModel.id == job_id).first()
    
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {
        "message" : "Job Found",
        "job": {
            "id": job.id,
            "name": job.name,
            "run_at": job.run_at,
            "recurring": job.recurring,
            "interval_seconds": job.interval_seconds,
            "status": job.status,
            "max_retries": job.max_retries,
            "retry_count": job.retry_count
        }
    }


@app.delete("/jobs/{job_id}")
async def delete_job_by_id(job_id: int, db: Session = Depends(get_db)):
    
    job = db.query(JobModel).filter(JobModel.id == job_id).first()
    
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    
    db.delete(job)
    db.commit()
    
    return {
        "message" : "Job deleted",
        "job": {
            "id": job.id,
            "name": job.name,
            "run_at": job.run_at,
            "recurring": job.recurring,
            "interval_seconds": job.interval_seconds,
            "status": job.status,
            "max_retries": job.max_retries,
            "retry_count": job.retry_count
        }
    }
    

@app.put("/jobs/{job_id}")
async def update_job(job_id: int, job_data: JobUpdate, db: Session = Depends(get_db)):
    
    if job_data.name not in JOB_FUNCTIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown job: {job_data.name}"
        )
    
    job = db.query(JobModel).filter(JobModel.id == job_id).first()
    
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job.name = job_data.name
    job.run_at = job_data.run_at
    job.recurring = job_data.recurring
    job.interval_seconds = job_data.interval_seconds
    job.status = "SCHEDULED"
    job.max_retries = job_data.max_retries 
    job.retry_count = 0
    
    db.commit()
    db.refresh(job)
    
    return {
        "message": "Job updated",
        "job": {
            "id": job.id,
            "name": job.name,
            "run_at": job.run_at,
            "recurring": job.recurring,
            "interval_seconds": job.interval_seconds,
            "status": job.status,
            "max_retries": job.max_retries,
            "retry_count": job.retry_count
        }
    }
    
    
@app.get("/jobs/{job_id}/executions")
async def get_job_executions(job_id: int, db: Session=Depends(get_db)):
    
    job = db.query(JobModel).filter(JobModel.id == job_id).first()
    
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    
    executions = db.query(JobExecution).filter(
        JobExecution.job_id == job_id
    ).order_by(
        JobExecution.started_at.asc()
    ).all()
    
    return {
        "job_id": job_id,
        "executions": [
            {
                "id": execution.id,
                "started_at": execution.started_at,
                "finished_at": execution.finished_at,
                "status": execution.status
            }
            for execution in executions
        ]
    }
    
    
@app.put("/jobs/{job_id}/pause")
async def pause_job(job_id: int, db:Session = Depends(get_db)):
    
    job = db.query(JobModel).filter(JobModel.id == job_id).first()
    
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status != "SCHEDULED":
        raise HTTPException(status_code=400, detail="Only scheduled jobs can be paused")
    
    job.status = "PAUSED"
    db.commit()
    db.refresh(job)
    
    return {
        "message": "Job paused",
        "job": {
            "id": job.id,
            "name": job.name,
            "run_at": job.run_at,
            "recurring": job.recurring,
            "interval_seconds": job.interval_seconds,
            "status": job.status,
            "max_retries": job.max_retries,
            "retry_count": job.retry_count
        }
    }
    
    
@app.put("/jobs/{job_id}/resume")
async def resume_job(job_id: int, db: Session=Depends(get_db)):
    
    job = db.query(JobModel).filter(JobModel.id == job_id).first()
    
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status != "PAUSED":
        raise HTTPException(status_code=400, detail="Only paused jobs can be resumed")
    
    job.status = "SCHEDULED"
    db.commit()
    db.refresh(job)
    
    return {
        "message": "Job resumed",
        "job": {
            "id": job.id,
            "name": job.name,
            "run_at": job.run_at,
            "recurring": job.recurring,
            "interval_seconds": job.interval_seconds,
            "status": job.status,
            "max_retries": job.max_retries,
            "retry_count": job.retry_count
        }
    }