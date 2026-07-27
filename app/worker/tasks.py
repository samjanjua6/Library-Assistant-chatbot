"""
generate_and_email_report — ARQ async task

Fetches yesterday's library statistics from SQLite/Postgres, builds a
PDF report in memory with ReportLab, and emails it as an attachment.
No file is written to disk at any point.
"""
from __future__ import annotations

import io
import os
import smtplib
import logging
from datetime import datetime, timedelta, timezone
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# pyrefly: ignore [missing-import]
from arq import Retry

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)

from ..core.config import settings
from ..core.database import SessionLocal
from ..library.model import Loan

logger = logging.getLogger(__name__)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _yesterday_range() -> tuple[datetime, datetime]:
    """Return (start, end) in UTC for yesterday (midnight to midnight)."""
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday = today - timedelta(days=1)
    return yesterday, today


def _fetch_stats() -> dict:
    """
    Query the database for yesterday's loan activity.
    Returns a dict with new_borrows, returns, and overdue counts.
    """
    start, end = _yesterday_range()
    db = SessionLocal()
    try:
        new_borrows = db.query(Loan).filter(
            Loan.borrowed_at >= start,
            Loan.borrowed_at < end,
        ).all()

        returns = db.query(Loan).filter(
            Loan.returned_at >= start,
            Loan.returned_at < end,
        ).all()

        overdue = db.query(Loan).filter(
            Loan.status == "borrowed",
            Loan.due_date < end,
        ).all()

        return {
            "date": start.strftime("%B %d, %Y"),
            "new_borrows": new_borrows,
            "returns": returns,
            "overdue": overdue,
        }
    finally:
        db.close()


def _build_pdf(stats: dict) -> bytes:
    """
    Build the daily report PDF entirely in memory using ReportLab.
    Returns the raw PDF bytes — nothing is written to disk.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        leftMargin=2.5 * cm,
        rightMargin=2.5 * cm,
    )

    styles = getSampleStyleSheet()
    story = []

    # ── Title ─────────────────────────────────────────────────────────────────
    title_style = styles["Title"]
    story.append(Paragraph("📚 Zylo Library — Daily Report", title_style))
    story.append(Paragraph(f"Date: {stats['date']}", styles["Normal"]))
    story.append(Spacer(1, 0.5 * cm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#334155")))
    story.append(Spacer(1, 0.5 * cm))

    # ── Summary Table ─────────────────────────────────────────────────────────
    summary_data = [
        ["Metric", "Count"],
        ["Books Borrowed Yesterday", str(len(stats["new_borrows"]))],
        ["Books Returned Yesterday", str(len(stats["returns"]))],
        ["Total Overdue (all time)", str(len(stats["overdue"]))],
    ]
    summary_table = Table(summary_data, colWidths=[11 * cm, 4 * cm])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a5f")),
        ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
        ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",   (0, 0), (-1, 0), 11),
        ("ALIGN",      (1, 0), (1, -1), "CENTER"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f8fafc"), colors.HexColor("#e2e8f0")]),
        ("GRID",       (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("FONTNAME",   (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",   (0, 1), (-1, -1), 10),
        ("TOPPADDING",  (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 1 * cm))

    # ── Borrowed Yesterday Detail ─────────────────────────────────────────────
    story.append(Paragraph("New Borrows Yesterday", styles["Heading2"]))
    story.append(Spacer(1, 0.25 * cm))
    if stats["new_borrows"]:
        borrow_data = [["#", "Book Title", "User ID", "Due Date"]]
        for i, loan in enumerate(stats["new_borrows"], 1):
            borrow_data.append([
                str(i),
                loan.book.title if loan.book else f"Book #{loan.book_id}",
                str(loan.user_id),
                loan.due_date.strftime("%Y-%m-%d"),
            ])
        t = Table(borrow_data, colWidths=[1 * cm, 9 * cm, 2.5 * cm, 3.5 * cm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f766e")),
            ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
            ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0fdf4")]),
            ("GRID",       (0, 0), (-1, -1), 0.5, colors.HexColor("#d1fae5")),
            ("FONTNAME",   (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE",   (0, 0), (-1, -1), 9),
            ("TOPPADDING",  (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(t)
    else:
        story.append(Paragraph("No books were borrowed yesterday.", styles["Normal"]))

    story.append(Spacer(1, 1 * cm))

    # ── Overdue Detail ────────────────────────────────────────────────────────
    story.append(Paragraph("Currently Overdue Loans", styles["Heading2"]))
    story.append(Spacer(1, 0.25 * cm))
    if stats["overdue"]:
        overdue_data = [["#", "Book Title", "User ID", "Due Date", "Days Overdue"]]
        now = datetime.now(timezone.utc)
        for i, loan in enumerate(stats["overdue"], 1):
            due = loan.due_date
            # Make both timezone-aware for comparison
            if due.tzinfo is None:
                due = due.replace(tzinfo=timezone.utc)
            days_over = (now - due).days
            overdue_data.append([
                str(i),
                loan.book.title if loan.book else f"Book #{loan.book_id}",
                str(loan.user_id),
                loan.due_date.strftime("%Y-%m-%d"),
                str(days_over),
            ])
        t = Table(overdue_data, colWidths=[1 * cm, 8 * cm, 2 * cm, 2.5 * cm, 2.5 * cm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#991b1b")),
            ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
            ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fff1f2")]),
            ("GRID",       (0, 0), (-1, -1), 0.5, colors.HexColor("#fecaca")),
            ("FONTNAME",   (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE",   (0, 0), (-1, -1), 9),
            ("TOPPADDING",  (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(t)
    else:
        story.append(Paragraph("No overdue loans. 🎉", styles["Normal"]))

    # ── Footer ────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 1 * cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#94a3b8")))
    story.append(Spacer(1, 0.25 * cm))
    story.append(Paragraph(
        f"Generated automatically by Zylo Library Assistant · {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        styles["Normal"]
    ))

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes


def _send_email(pdf_bytes: bytes, report_date: str) -> None:
    """Send the PDF as an email attachment via SMTP.

    Set env var BREAK_EMAIL_FOR_TESTING=true to deliberately raise an error
    so you can confirm the retry logic works without touching real SMTP.
    """
    if os.environ.get("BREAK_EMAIL_FOR_TESTING", "").lower() == "true":
        raise RuntimeError("BREAK_EMAIL_FOR_TESTING is enabled — simulated email failure.")

    if not settings.SMTP_USER or not settings.REPORT_EMAIL_TO:
        logger.warning("[Report] SMTP_USER or REPORT_EMAIL_TO not set — skipping email.")
        return

    msg = MIMEMultipart()
    msg["From"] = settings.SMTP_FROM
    msg["To"] = settings.REPORT_EMAIL_TO
    msg["Subject"] = f"📚 Zylo Library Daily Report — {report_date}"

    body = (
        f"Hello,\n\n"
        f"Please find attached the daily library activity report for {report_date}.\n\n"
        f"This email was generated automatically by the Zylo Library Assistant.\n"
    )
    msg.attach(MIMEText(body, "plain"))

    filename = f"library_report_{report_date.replace(' ', '_')}.pdf"
    attachment = MIMEApplication(pdf_bytes, _subtype="pdf")
    attachment.add_header("Content-Disposition", "attachment", filename=filename)
    msg.attach(attachment)

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        server.starttls()
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.sendmail(settings.SMTP_USER, settings.REPORT_EMAIL_TO, msg.as_string())

    logger.info(f"[Report] Email sent to {settings.REPORT_EMAIL_TO}")


# ── ARQ Task ─────────────────────────────────────────────────────────────────

MAX_RETRIES = 3
RETRY_DEFER_SECONDS = 30   # wait 30 s between retries


async def generate_and_email_report(ctx: dict) -> str:
    """
    ARQ task: fetch stats, build PDF in memory, email it.

    Retry logic:
      ctx['job_try'] == 1  on the first attempt
      ctx['job_try'] == 2  on the first retry  (after Retry() was raised)
      ctx['job_try'] == 3  on the second retry
      After MAX_RETRIES attempts the job is marked failed.
    """
    job_try: int = ctx.get("job_try", 1)
    logger.info(f"[Report] Attempt {job_try}/{MAX_RETRIES} — fetching stats...")

    stats = _fetch_stats()
    logger.info(
        f"[Report] Stats — borrows: {len(stats['new_borrows'])}, "
        f"returns: {len(stats['returns'])}, overdue: {len(stats['overdue'])}"
    )

    logger.info("[Report] Building PDF in memory...")
    pdf_bytes = _build_pdf(stats)
    logger.info(f"[Report] PDF built — {len(pdf_bytes):,} bytes")

    logger.info(f"[Report] Sending email (attempt {job_try})...")
    try:
        _send_email(pdf_bytes, stats["date"])
    except Exception as exc:
        if job_try < MAX_RETRIES:
            logger.warning(
                f"[Report] Email failed on attempt {job_try} — {exc}. "
                f"Retrying in {RETRY_DEFER_SECONDS}s "
                f"({MAX_RETRIES - job_try} attempt(s) left)."
            )
            raise Retry(defer=RETRY_DEFER_SECONDS)
        # All retries exhausted — log and re-raise so ARQ marks job as failed
        logger.error(
            f"[Report] Email FAILED after {MAX_RETRIES} attempts — {exc}. Giving up."
        )
        raise

    result = (
        f"Report for {stats['date']}: "
        f"{len(stats['new_borrows'])} borrows, "
        f"{len(stats['returns'])} returns, "
        f"{len(stats['overdue'])} overdue. "
        f"PDF size: {len(pdf_bytes):,} bytes."
    )
    logger.info(f"[Report] Done — {result}")
    return result


# ── Session Document Ingestion Job ────────────────────────────────────────────

async def process_session_document(
    ctx,
    document_id: int,
    file_path: str,
    session_id: int,
    user_id: int,
    filename: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> str:
    """
    ARQ background job: extract → chunk → embed → index a user-uploaded file.

    Steps
    -----
    1. Mark SessionDocument.status = 'processing'
    2. Call ingest_session_document() — extract text, chunk, upsert to ChromaDB
    3. On success: set status='ready' and record chunk_count
    4. On failure: set status='failed' and record error_message
    5. Delete the on-disk temp file in all cases

    The ARQ ctx dict is injected by the worker and contains Redis settings.
    """
    from pathlib import Path as _Path
    from datetime import datetime, timezone as _tz
    from ..core.database import SessionLocal
    from ..chat.model import SessionDocument
    from ..library.rag import ingest_session_document

    db = SessionLocal()
    file_path_obj = _Path(file_path)

    try:
        # ── 1. Mark as processing ────────────────────────────────────────────
        doc = db.query(SessionDocument).filter(SessionDocument.id == document_id).first()
        if not doc:
            logger.error(f"[DocJob] SessionDocument {document_id} not found.")
            return f"not_found:{document_id}"

        doc.status = "processing"
        doc.updated_at = datetime.now(_tz.utc)
        db.commit()

        # ── 2. Ingest ────────────────────────────────────────────────────────
        chunk_count = ingest_session_document(
            document_id=document_id,
            session_id=session_id,
            user_id=user_id,
            filename=filename,
            file_path=file_path_obj,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

        # ── 3. Mark ready ────────────────────────────────────────────────────
        doc.status = "ready"
        doc.chunk_count = chunk_count
        doc.updated_at = datetime.now(_tz.utc)
        db.commit()
        logger.info(f"[DocJob] document_id={document_id} ready — {chunk_count} chunks.")
        return f"ready:{document_id}:{chunk_count}"

    except Exception as exc:
        # ── 4. Mark failed ───────────────────────────────────────────────────
        logger.exception(f"[DocJob] document_id={document_id} failed: {exc}")
        try:
            db.rollback()
            doc = db.query(SessionDocument).filter(SessionDocument.id == document_id).first()
            if doc:
                doc.status = "failed"
                doc.error_message = str(exc)[:2000]
                doc.updated_at = datetime.now(_tz.utc)
                db.commit()
        except Exception as inner:
            logger.exception(f"[DocJob] Failed to write error status: {inner}")
        return f"failed:{document_id}:{exc}"

    finally:
        db.close()
        # ── 5. Delete temp file ───────────────────────────────────────────────
        try:
            if file_path_obj.exists():
                file_path_obj.unlink()
                logger.info(f"[DocJob] Deleted temp file: {file_path_obj}")
        except Exception as e:
            logger.warning(f"[DocJob] Could not delete temp file {file_path_obj}: {e}")
