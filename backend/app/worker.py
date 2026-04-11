"""Celery application and beat schedule (T4.2).

Start the worker:
    celery -A app.worker worker --loglevel=info

Start the beat scheduler (separate process):
    celery -A app.worker beat --loglevel=info

Or combined (development only):
    celery -A app.worker worker --beat --loglevel=info
"""

from __future__ import annotations

from celery import Celery
from celery.schedules import crontab

from app.config import settings

celery_app = Celery(
    "compliai",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.compliance",
        "app.tasks.email_nurturing",
        "app.tasks.wizard_reminders",
        "app.tasks.upsell_sequence",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    beat_schedule={
        "periodic-compliance-checks": {
            "task": "app.tasks.compliance.run_periodic_compliance_checks",
            "schedule": settings.COMPLIANCE_CHECK_INTERVAL_SECONDS,
        },
        "daily-pmm-reminder": {
            "task": "app.tasks.compliance.send_pmm_reminders",
            "schedule": crontab(hour=8, minute=0),  # Daily at 08:00 UTC
        },
        "daily-wizard-reminders": {
            "task": "app.tasks.wizard_reminders.send_wizard_reminders_daily",
            "schedule": crontab(hour=9, minute=0),  # Daily at 09:00 UTC
        },
        "daily-upsell-sequence": {
            "task": "app.tasks.upsell_sequence.send_upsell_emails_daily",
            "schedule": crontab(hour=10, minute=0),  # Daily at 10:00 UTC
        },
    },
)
