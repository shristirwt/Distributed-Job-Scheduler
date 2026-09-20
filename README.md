# Distributed Job Scheduler

A backend job scheduling system built with **FastAPI** and **PostgreSQL** that allows users to create, schedule, monitor, pause, resume, update, and delete jobs.

The system runs scheduled and recurring jobs in the background and maintains execution history for monitoring job status and failures.

## Features

* Create one-time and recurring jobs
* Schedule jobs for a specific date and time
* Automatically execute scheduled jobs in the background
* Support recurring jobs using configurable intervals
* Track job status such as `SCHEDULED`, `RUNNING`, `COMPLETED`, and `FAILED`
* Maintain execution history for every job
* Pause and resume scheduled jobs
* Update existing jobs
* Delete jobs
* Monitor scheduler status
* Health-check endpoint
* RESTful API with automatically generated Swagger documentation
* PostgreSQL database for persistent job storage
* Background scheduler for automatic job execution
* Error handling for failed or unknown jobs

## Tech Stack

| Technology   | Purpose             |
| ------------ | ------------------- |
| Python       | Backend programming |
| FastAPI      | REST API framework  |
| PostgreSQL   | Database            |
| SQLAlchemy   | Database ORM        |
| Pydantic     | Data validation     |
| Uvicorn      | ASGI server         |
| Git & GitHub | Version control     |

## Project Architecture

```text
                 Client
                   |
                   v
             FastAPI REST API
                   |
          +--------+--------+
          |                 |
          v                 v
    PostgreSQL         Scheduler
          |                 |
          |                 v
          |          Job Execution
          |                 |
          +--------+--------+
                   |
                   v
            Execution History
```

### Main Components

**FastAPI API**

Provides endpoints for creating and managing jobs.

**PostgreSQL**

Stores job information and execution history.

**SQLAlchemy**

Handles communication between the Python application and PostgreSQL database.

**Scheduler**

Runs in the background and continuously checks for jobs that are ready to execute.

**Job Functions**

Contains the actual operations performed by scheduled jobs, such as generating reports or sending emails.

**Execution Tracking**

Each execution is recorded so that previous attempts and their statuses can be viewed.

## Database Design

### `jobs`

Stores the configuration and current state of scheduled jobs.

Typical information includes:

* Job ID
* Job name
* Scheduled execution time
* Recurring/non-recurring status
* Job status
* Recurring interval

### `job_execution`

Stores information about individual job executions.

Typical information includes:

* Execution ID
* Job ID
* Start time
* Finish time
* Execution status

Relationship:

```text
jobs
  |
  | 1
  |
  | N
  v
job_execution
```

One job can have multiple execution records, especially for recurring jobs.

## API Endpoints

### Scheduler

| Method | Endpoint            | Description              |
| ------ | ------------------- | ------------------------ |
| GET    | `/scheduler/status` | Check scheduler status   |
| GET    | `/health`           | Check application health |

### Jobs

| Method | Endpoint                    | Description            |
| ------ | --------------------------- | ---------------------- |
| POST   | `/jobs`                     | Create a new job       |
| GET    | `/jobs`                     | Get all jobs           |
| GET    | `/jobs/{job_id}`            | Get a specific job     |
| PUT    | `/jobs/{job_id}`            | Update a job           |
| DELETE | `/jobs/{job_id}`            | Delete a job           |
| PUT    | `/jobs/{job_id}/pause`      | Pause a job            |
| PUT    | `/jobs/{job_id}/resume`     | Resume a job           |
| GET    | `/jobs/{job_id}/executions` | View execution history |

### Other

| Method | Endpoint | Description             |
| ------ | -------- | ----------------------- |
| GET    | `/`      | Application information |
| GET    | `/tasks` | View available tasks    |

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/shristirwt/Distributed-Job-Scheduler.git
cd Distributed-Job-Scheduler
```

### 2. Create a virtual environment

Windows:

```powershell
python -m venv venv
```

Activate it:

```powershell
.\venv\Scripts\activate
```

### 3. Install dependencies

```powershell
pip install -r requirements.txt
```

### 4. Configure PostgreSQL

Create a PostgreSQL database:

```text
job_scheduler
```

Configure the database connection in the application's configuration/environment variables.

> Do not commit database passwords, API keys, or other secrets to GitHub.

### 5. Start the application

```powershell
uvicorn main:app --reload
```

The application will be available at:

```text
http://127.0.0.1:8000
```

## API Documentation

Once the application is running, FastAPI automatically provides interactive API documentation.

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

ReDoc:

```text
http://127.0.0.1:8000/redoc
```

## Example Workflow

A typical job lifecycle looks like:

```text
Create Job
    |
    v
SCHEDULED
    |
    v
Scheduler detects due job
    |
    v
RUNNING
    |
    +-------> COMPLETED
    |
    +-------> FAILED
```

For recurring jobs:

```text
Create Recurring Job
        |
        v
    SCHEDULED
        |
        v
      RUN
        |
        v
   Next Run Time
        |
        v
      RUN
        |
        v
      ...
```

## Example Job

A job can be configured to execute a predefined task at a specified time.

Example:

```json
{
    "name": "generate_report",
    "run_at": "2026-09-20T23:30:00",
    "recurring": false
}
```

The scheduler detects the job when its execution time arrives and runs the corresponding task.

## Current Status

The current version supports:

* Job creation and management
* Scheduled execution
* Recurring jobs
* Background scheduler
* Job status tracking
* Execution history
* Pause/resume functionality
* PostgreSQL persistence
* REST API
* Swagger API documentation

### Planned Improvements

Future versions can include:

* Automatic retry mechanism
* Configurable retry limits
* Multiple worker nodes
* Distributed job execution
* Job priorities
* Task queues
* Concurrency control
* Authentication and authorization
* Web-based monitoring dashboard
* Structured logging
* Metrics and monitoring
* Docker/containerized deployment

## Why This Project?

The project demonstrates how a backend scheduling system can coordinate **job creation, persistence, scheduling, execution, and monitoring**.

It also provides a foundation for understanding concepts used in larger workflow and task-processing systems such as background workers, schedulers, task queues, and distributed execution.

## Author

**Shristi Rawat**

B.Tech CSE (AI & Data Science)

---

⭐ If you find this project useful, consider giving the repository a star.
