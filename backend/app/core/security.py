"""Security utilities: file validation, filename sanitization, and SSRF protection."""

import uuid
import re
import ipaddress
from urllib.parse import urlparse
from fastapi import UploadFile
from typing import Tuple, Optional
from app.core.config import settings

MAX_FILENAME_LENGTH = 255

ALL_ALLOWED_MIME_TYPES = {
    # Images
    'image/jpeg', 'image/png', 'image/webp', 'image/gif', 'image/bmp',
    # Documents / PDF
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/msword',
    'text/plain', 'text/csv', 'text/html', 'text/markdown',
    # Video
    'video/mp4', 'video/quicktime', 'video/webm', 'video/x-msvideo', 'video/mpeg',
    # Audio
    'audio/mpeg', 'audio/wav', 'audio/x-m4a', 'audio/mp4', 'audio/ogg', 'audio/webm',
    # Generic octet stream fallback with extension checking
    'application/octet-stream',
}

ALL_ALLOWED_EXTENSIONS = {
    '.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif',
    '.pdf', '.docx', '.doc', '.txt', '.csv',
    '.mp4', '.mov', '.webm', '.avi',
    '.mp3', '.wav', '.m4a', '.ogg',
}


def validate_file(file: UploadFile, category: Optional[str] = None) -> Tuple[bool, str]:
    """Validates uploaded file against allowed MIME types and extensions."""
    content_type = (file.content_type or "").lower()
    filename = (file.filename or "").lower()
    ext = "." + filename.split(".")[-1] if "." in filename else ""

    # Check extension
    if ext and ext not in ALL_ALLOWED_EXTENSIONS:
        return False, f"Unsupported file extension: '{ext}'. Supported formats: PDF, Images, Videos, Audio, Documents."

    # Check MIME type
    if content_type and content_type not in ALL_ALLOWED_MIME_TYPES:
        # If octet-stream or unknown MIME, allow if extension is valid
        if ext in ALL_ALLOWED_EXTENSIONS:
            return True, ""
        return False, f"Unsupported file type: '{content_type}'."

    return True, ""


def sanitize_filename(filename: str) -> str:
    clean_name = re.sub(r'[^a-zA-Z0-9_.-]', '_', filename)
    if len(clean_name) > MAX_FILENAME_LENGTH - 37:
        clean_name = clean_name[:MAX_FILENAME_LENGTH - 37]
    return f"{uuid.uuid4()}_{clean_name}"


def is_safe_url(url: str) -> bool:
    """SSRF protection: prevents querying private, link-local, or loopback IPs."""
    try:
        parsed = urlparse(url)
        if not parsed.hostname:
            return False
        if parsed.hostname.lower() in ['localhost', '127.0.0.1', '::1', '0.0.0.0']:
            return False
        try:
            ip = ipaddress.ip_address(parsed.hostname)
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
                return False
        except ValueError:
            # Hostname is a domain name, not direct IP
            pass
    except Exception:
        return False
    return True
