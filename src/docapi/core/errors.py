"""Structured errors. Every failure is JSON with a stable `type`, a human `message`, context."""
from __future__ import annotations

from typing import Any


class DocApiError(Exception):
    type: str = "processing_error"
    http_status: int = 500

    def __init__(self, message: str, **context: Any) -> None:
        super().__init__(message)
        self.message = message
        self.context = context

    def to_dict(self) -> dict[str, Any]:
        return {"error": {"type": self.type, "message": self.message, **self.context}}


class UnsupportedFileType(DocApiError):
    type = "unsupported_file_type"
    http_status = 415


class FileTooLarge(DocApiError):
    type = "file_too_large"
    http_status = 413


class TooManyPages(DocApiError):
    type = "too_many_pages"
    http_status = 422


class ValidationFailed(DocApiError):
    type = "validation_failed"
    http_status = 422


class ProcessingError(DocApiError):
    type = "processing_error"
    http_status = 500


class UpstreamModelError(DocApiError):
    type = "upstream_model_error"
    http_status = 502
