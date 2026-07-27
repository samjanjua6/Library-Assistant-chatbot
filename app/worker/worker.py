"""
ARQ WorkerSettings — defines which tasks run and when.

To TEST: the cron job is currently set to fire every minute (minute=None).
For PRODUCTION: change to cron(generate_and_email_report, hour=7, minute=0)
"""
from __future__ import annotations

# pyrefly: ignore [missing-import]
from arq import cron
# pyrefly: ignore [missing-import]
from arq.connections import RedisSettings

from .tasks import generate_and_email_report
from ..core.config import settings


def _redis_settings_from_url() -> RedisSettings:
    """Parse REDIS_URL (e.g. redis://redis:6379/0) into an ARQ RedisSettings object."""
    url = settings.REDIS_URL  # e.g. "redis://redis:6379/0"
    # Strip the scheme
    url = url.replace("redis://", "").replace("rediss://", "")
    host_port, *db_parts = url.split("/")
    db = int(db_parts[0]) if db_parts else 0
    if ":" in host_port:
        host, port_str = host_port.split(":", 1)
        port = int(port_str)
    else:
        host = host_port
        port = 6379
    return RedisSettings(host=host, port=port, database=db)


class WorkerSettings:
    """
    ARQ worker configuration.

    TESTING MODE  : fires every minute (minute=None means "every minute")
    PRODUCTION    : change the cron line below to hour=7, minute=0
    """
    functions = [generate_and_email_report]

    # ── TESTING: fires every minute ──────────────────────────────────────────
    # cron_jobs = [
    #     cron(generate_and_email_report, minute={0, 1, 2, 3, 4, 5, 6, 7, 8, 9,
    #                                             10, 11, 12, 13, 14, 15, 16, 17, 18, 19,
    #                                             20, 21, 22, 23, 24, 25, 26, 27, 28, 29,
    #                                             30, 31, 32, 33, 34, 35, 36, 37, 38, 39,
    #                                             40, 41, 42, 43, 44, 45, 46, 47, 48, 49,
    #                                             50, 51, 52, 53, 54, 55, 56, 57, 58, 59}),
    # ]

    # ── PRODUCTION (uncomment after testing): fires at 07:00 daily ───────────
    cron_jobs = [
        cron(generate_and_email_report, hour=7, minute=0),
    ]

    redis_settings = _redis_settings_from_url()

    # Worker keeps running even if a job raises an exception
    keep_result = 3600  # store job results in Redis for 1 hour
    max_jobs = 4
    job_timeout = 300   # 5 minutes max per job
