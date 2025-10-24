"""
Celery configuration for HyperKit AI Agent production system.

This module configures Celery for async job processing including
compilation, deployment, and auditing jobs.
"""

import os
from celery import Celery
from celery.schedules import crontab
import logging

logger = logging.getLogger(__name__)

# Celery configuration
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

# Create Celery app
celery_app = Celery(
    "hyperkit_agent",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=[
        "backend.jobs.compile",
        "backend.jobs.deploy", 
        "backend.jobs.audit"
    ]
)

# Celery configuration
celery_app.conf.update(
    # Task routing
    task_routes={
        "backend.jobs.compile.*": {"queue": "compile"},
        "backend.jobs.deploy.*": {"queue": "deploy"},
        "backend.jobs.audit.*": {"queue": "audit"},
    },
    
    # Task execution
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Task retry configuration
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_reject_on_worker_lost=True,
    
    # Task time limits
    task_soft_time_limit=300,  # 5 minutes
    task_time_limit=600,       # 10 minutes
    
    # Retry configuration
    task_default_retry_delay=60,  # 1 minute
    task_max_retries=3,
    
    # Result backend configuration
    result_expires=3600,  # 1 hour
    
    # Beat schedule for periodic tasks
    beat_schedule={
        "cleanup-old-jobs": {
            "task": "backend.jobs.cleanup.cleanup_old_jobs",
            "schedule": crontab(hour=2, minute=0),  # Daily at 2 AM
        },
        "health-check": {
            "task": "backend.jobs.health.health_check",
            "schedule": 60.0,  # Every minute
        },
    },
    
    # Worker configuration
    worker_hijack_root_logger=False,
    worker_log_color=False,
    worker_log_format="[%(asctime)s: %(levelname)s/%(processName)s] %(message)s",
    worker_task_log_format="[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s",
)


@celery_app.task(bind=True)
def debug_task(self):
    """Debug task to test Celery setup."""
    logger.info(f"Request: {self.request!r}")
    return "Celery is working!"


def get_celery_app() -> Celery:
    """Get Celery app instance."""
    return celery_app


# Health check task
@celery_app.task
def health_check():
    """Health check task for monitoring."""
    return {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z"
    }


# Cleanup task
@celery_app.task
def cleanup_old_jobs():
    """Cleanup old completed jobs."""
    from ..db.connection import get_database_session
    from ..db.models import Job
    from datetime import datetime, timedelta
    
    try:
        with get_database_session() as db:
            # Delete jobs older than 7 days
            cutoff_date = datetime.utcnow() - timedelta(days=7)
            old_jobs = db.query(Job).filter(
                Job.status.in_(["completed", "failed"]),
                Job.created_at < cutoff_date
            ).all()
            
            for job in old_jobs:
                db.delete(job)
            
            db.commit()
            logger.info(f"Cleaned up {len(old_jobs)} old jobs")
            
    except Exception as e:
        logger.error(f"Cleanup task failed: {e}")
        raise


if __name__ == "__main__":
    celery_app.start()
