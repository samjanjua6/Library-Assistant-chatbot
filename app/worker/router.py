"""
Admin endpoints for triggering and checking ARQ background jobs.

POST /api/admin/trigger-report   — enqueue generate_and_email_report immediately
GET  /api/admin/report-status/{job_id} — poll for completion / result
"""
from __future__ import annotations
import io
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

# pyrefly: ignore [missing-import]
from arq import create_pool
# pyrefly: ignore [missing-import]
from arq.jobs import Job, JobStatus

from ..core.deps import get_current_admin_user
from ..users.model import User
from .worker import _redis_settings_from_url
from .tasks import _fetch_stats, _build_pdf, _send_email

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/admin", tags=["Admin - Reports"])


# ── Shared pool helper ────────────────────────────────────────────────────────

async def _arq_pool():
    """Open a short-lived ARQ connection pool for a single request."""
    return await create_pool(_redis_settings_from_url())


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/trigger-report", summary="Queue the daily report immediately")
async def trigger_report(admin: User = Depends(get_current_admin_user)) -> dict[str, str]:
    """
    Enqueue generate_and_email_report as an on-demand ARQ job.
    Returns a job_id you can use to poll for status.
    """
    pool = await _arq_pool()
    try:
        job = await pool.enqueue_job("generate_and_email_report")
        if job is None:
            # ARQ returns None if an identical job is already queued
            raise HTTPException(
                status_code=409,
                detail="A report job is already queued. Poll /report-status to check progress."
            )
        logger.info(f"[Report] On-demand job enqueued: {job.job_id}")
        return {"job_id": job.job_id, "status": "queued"}
    finally:
        await pool.close()


@router.get("/report-status/{job_id}", summary="Check the status of a queued report job")
async def report_status(
    job_id: str,
    admin: User = Depends(get_current_admin_user),
) -> dict[str, Any]:
    """
    Poll the status of a report job by its job_id.

    Possible status values:
      - queued       : waiting for the worker to pick it up
      - in_progress  : worker is currently running it
      - deferred     : scheduled to run at a future time (e.g. after a retry delay)
      - complete     : finished successfully — result string is included
      - not_found    : job_id unknown or expired (results are kept 1 hour)
    """
    pool = await _arq_pool()
    try:
        job = Job(job_id, redis=pool)
        status: JobStatus = await job.status()

        response: dict[str, Any] = {
            "job_id": job_id,
            "status": status.value,
            "result": None,
            "error": None,
        }

        if status == JobStatus.complete:
            try:
                # result() with timeout=0 is non-blocking; raises if the job itself raised
                response["result"] = await job.result(timeout=0)
            except Exception as exc:
                # The job completed but raised — expose the error message
                response["status"] = "failed"
                response["error"] = str(exc)

        return response
    finally:
        await pool.close()


@router.get("/download-report", summary="Generate and download the daily PDF report instantly")
async def download_report(admin: User = Depends(get_current_admin_user)):
    """
    Builds the PDF report synchronously in memory, sends it via email,
    and streams it directly to the browser as a file download.
    """
    stats = _fetch_stats()
    pdf_bytes = _build_pdf(stats)
    filename = f"library_report_{stats['date'].replace(' ', '_').replace(',', '')}.pdf"

    # Send the email in the background of the same request
    try:
        _send_email(pdf_bytes, stats["date"])
    except Exception as exc:
        logger.error(f"[Report] Manual download email failed: {exc}")

    # Also update Notion
    try:
        from ..library.notion_mcp import write_daily_report_to_notion
        await write_daily_report_to_notion(
            date_str=stats["date"],
            new_borrows=len(stats["new_borrows"]),
            returns=len(stats["returns"]),
            overdue=len(stats["overdue"])
        )
    except Exception as exc:
        logger.error(f"[Report] Manual download Notion write failed: {exc}")

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
