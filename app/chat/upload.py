"""
app/chat/upload.py
──────────────────
Helpers for validating and saving user-uploaded chat-session documents.

MIME sniffing strategy
──────────────────────
We use ``python-magic`` to read the first 2 KiB of the file and compare the
detected MIME type against an allow-list.  If ``libmagic`` is not installed
(common on Windows dev boxes), we fall back to extension-only sniffing with a
warning — this is acceptable in development but the Docker image always has
libmagic so production is fully protected.
"""
from __future__ import annotations

import re
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB

# Extension → canonical MIME type
ALLOWED_EXTENSIONS: dict[str, str] = {
    ".pdf":  "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".txt":  "text/plain",
    ".md":   "text/plain",
    ".csv":  "text/csv",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".json": "application/json",
}

# Allowed MIME type prefixes (magic may return slight variants)
ALLOWED_MIME_PREFIXES: set[str] = {
    "application/pdf",
    "application/vnd.openxmlformats",
    "application/zip",   # OOXML (docx/xlsx) is actually a zip
    "text/",
    "application/json",
    "application/octet-stream",  # generic fallback — extension check still applies
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _sanitise_filename(name: str) -> str:
    """Strip path separators and replace unsafe characters."""
    # Take only the basename
    name = Path(name).name
    # Replace anything that isn't alphanumeric, dash, underscore, dot
    name = re.sub(r"[^\w.\-]", "_", name)
    # Collapse consecutive underscores/dashes
    name = re.sub(r"[_\-]{2,}", "_", name)
    return name[:200]  # cap length


def _sniff_mime(data: bytes) -> str | None:
    """
    Return the MIME type detected by libmagic, or None if unavailable.
    Never raises — always returns a string or None.
    """
    try:
        import magic  # python-magic
        mime = magic.from_buffer(data, mime=True)
        return mime
    except ImportError:
        logger.warning(
            "[Upload] python-magic not installed — falling back to extension-only "
            "MIME validation. Install `python-magic` + `libmagic1` for full sniffing."
        )
        return None
    except Exception as exc:
        logger.warning(f"[Upload] MIME sniff failed: {exc}")
        return None


def validate_upload(
    filename: str,
    data: bytes,
) -> tuple[bool, str, str]:
    """
    Validate file size, extension, and MIME type.

    Returns (ok: bool, error_message: str, safe_filename: str).
    On success error_message is empty.
    """
    # 1. Size check
    if len(data) > MAX_FILE_SIZE:
        size_mb = len(data) / (1024 * 1024)
        return False, f"File too large ({size_mb:.1f} MB). Maximum is 20 MB.", ""

    # 2. Extension check
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_EXTENSIONS))
        return False, f"File type '{ext}' is not allowed. Allowed: {allowed}", ""

    # 3. MIME sniff (best-effort)
    detected_mime = _sniff_mime(data[:2048])
    if detected_mime is not None:
        mime_ok = any(detected_mime.startswith(prefix) for prefix in ALLOWED_MIME_PREFIXES)
        if not mime_ok:
            return (
                False,
                f"File content does not match an allowed type (detected: {detected_mime}).",
                "",
            )

    safe_name = _sanitise_filename(filename)
    return True, "", safe_name


def save_upload(
    data: bytes,
    safe_filename: str,
    user_id: int,
    session_id: int,
    base_dir: Path,
) -> Path:
    """
    Save *data* to ``base_dir / user_{user_id} / session_{session_id} / safe_filename``.
    Creates parent directories as needed.
    Returns the full path to the saved file.
    """
    dest_dir = base_dir / f"user_{user_id}" / f"session_{session_id}"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / safe_filename
    dest.write_bytes(data)
    return dest
