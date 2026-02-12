"""
Task 2: FastAPI Application
reCAPTCHA solving API with task queue system.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uuid
from datetime import datetime
from typing import Optional

from .models import (
    RecaptchaRequest,
    RecaptchaResponse,
    TaskStatusResponse,
    TaskStatus
)
from .database import Database, get_db
from .solver import RecaptchaSolver
from loguru import logger


# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application lifecycle."""
    # Startup
    logger.info("Starting reCAPTCHA API server...")
    db = await get_db()
    await db.initialize()
    logger.info("Database initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down reCAPTCHA API server...")
    from .database import close_db
    await close_db()


# Create FastAPI app
app = FastAPI(
    title="reCAPTCHA Solving API",
    description="API for automated reCAPTCHA solving with task queue system",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize solver
solver = RecaptchaSolver()


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "reCAPTCHA Solving API",
        "version": "1.0.0",
        "endpoints": {
            "submit_task": "POST /recaptcha/in",
            "get_result": "GET /recaptcha/res",
            "health": "GET /health"
        },
        "documentation": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/recaptcha/in", response_model=RecaptchaResponse)
async def submit_recaptcha_task(
    request: RecaptchaRequest,
    background_tasks: BackgroundTasks,
    db: Database = Depends(get_db)
):
    """
    Submit a new reCAPTCHA solving task.
    
    Args:
        request: RecaptchaRequest with sitekey, pageurl, and optional proxy
        background_tasks: FastAPI background tasks
        db: Database instance
    
    Returns:
        RecaptchaResponse with taskId and status
    """
    try:
        # Generate unique task ID
        task_id = str(uuid.uuid4())
        
        # Create task in database
        await db.create_task(
            task_id=task_id,
            sitekey=request.sitekey,
            pageurl=request.pageurl,
            proxy=request.proxy,
            status=TaskStatus.PROCESSING
        )
        
        # Start solving in background
        background_tasks.add_task(
            solve_recaptcha_task,
            task_id=task_id,
            request=request,
            db=db
        )
        
        logger.info(f"Created task {task_id} for {request.pageurl}")
        
        return RecaptchaResponse(
            taskId=task_id,
            status=TaskStatus.PROCESSING
        )
        
    except Exception as e:
        logger.error(f"Error creating task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/recaptcha/res", response_model=TaskStatusResponse)
async def get_recaptcha_result(
    taskId: str,
    db: Database = Depends(get_db)
):
    """
    Get the result of a reCAPTCHA solving task.
    
    Args:
        taskId: The task ID returned from /recaptcha/in
        db: Database instance
    
    Returns:
        TaskStatusResponse with status and token (if ready)
    """
    try:
        # Get task from database
        task = await db.get_task(taskId)
        
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        response = TaskStatusResponse(
            status=task["status"],
            taskId=taskId
        )
        
        if task["status"] == TaskStatus.READY:
            response.token = task["token"]
            response.solveTime = task["solve_time"]
        elif task["status"] == TaskStatus.ERROR:
            response.error = task["error"]
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting task result: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def solve_recaptcha_task(
    task_id: str,
    request: RecaptchaRequest,
    db: Database
):
    """
    Background task to solve reCAPTCHA.
    
    Args:
        task_id: Task ID
        request: RecaptchaRequest
        db: Database instance
    """
    try:
        logger.info(f"Starting to solve task {task_id}")
        
        # Solve reCAPTCHA
        result = await solver.solve(
            sitekey=request.sitekey,
            pageurl=request.pageurl,
            proxy=request.proxy
        )
        
        if result["success"]:
            # Update task as ready
            await db.update_task(
                task_id=task_id,
                status=TaskStatus.READY,
                token=result["token"],
                solve_time=result["solve_time"]
            )
            logger.success(f"Task {task_id} solved successfully in {result['solve_time']:.2f}s")
        else:
            # Update task as error
            await db.update_task(
                task_id=task_id,
                status=TaskStatus.ERROR,
                error=result.get("error", "Unknown error")
            )
            logger.error(f"Task {task_id} failed: {result.get('error')}")
            
    except Exception as e:
        logger.error(f"Error solving task {task_id}: {e}")
        await db.update_task(
            task_id=task_id,
            status=TaskStatus.ERROR,
            error=str(e)
        )


@app.get("/stats")
async def get_statistics(db: Database = Depends(get_db)):
    """Get API statistics."""
    try:
        stats = await db.get_statistics()
        return stats
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/tasks/{task_id}")
async def delete_task(
    task_id: str = Path(..., description="The UUID of the task to delete"),
    db: Database = Depends(get_db)
):
    """Delete a task by ID."""
    try:
        success = await db.delete_task(task_id)
        if not success:
            raise HTTPException(status_code=404, detail="Task not found")
        return {"message": "Task deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
