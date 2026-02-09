"""Utility helpers."""

import hashlib


def hash_text(text: str) -> str:
    """Return a SHA-256 hex digest of *text*."""
    return hashlib.sha256(text.encode()).hexdigest()
