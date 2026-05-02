"""Custom exceptions for Solar Core."""
from typing import Any


class SolarCoreError(Exception):
    """Base exception for Solar Core."""

    status_code: int = 500
    error_code: str = "internal_error"

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class AuthenticationError(SolarCoreError):
    status_code = 401
    error_code = "authentication_error"


class NotFoundError(SolarCoreError):
    status_code = 404
    error_code = "not_found"


class ValidationError(SolarCoreError):
    status_code = 422
    error_code = "validation_error"


class AIProviderError(SolarCoreError):
    status_code = 502
    error_code = "ai_provider_error"


class ActionError(SolarCoreError):
    status_code = 500
    error_code = "action_error"


class ConnectorError(SolarCoreError):
    status_code = 502
    error_code = "connector_error"
