from sqlalchemy import DateTime, Boolean, Integer, Column, String
from database import base

class Job(base):
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    run_at = Column(DateTime, nullable=False)
    recurring = Column(Boolean, default=False)
    interval_seconds = Column(Integer, nullable=True)
    status = Column(String(20), default="SCHEDULED")
    max_retries = Column(Integer, default=0)
    retry_count = Column(Integer, default=0)
    
class JobExecution(base):
    __tablename__ = "job_execution"
    
    id = Column(Integer, primary_key=True, index = True)
    job_id = Column(Integer, nullable=False)
    started_at = Column(DateTime, nullable=False)
    finished_at = Column(DateTime)
    status = Column(String(20), default="RUNNING")