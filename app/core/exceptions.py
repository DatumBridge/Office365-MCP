"""Error handling for Office 365 MCP Server (Microsoft Graph)."""

from typing import Any, Optional


class GraphError(Exception):
    """Base error for Microsoft Graph operations."""

    def __init__(
        self,
        message: str,
        error_code: str = "GRAPH_ERROR",
        retryable: bool = False,
        original_error: Optional[Any] = None,
    ):
        self.message = message
        self.error_code = error_code
        self.retryable = retryable
        self.original_error = original_error
        super().__init__(message)

    def to_dict(self) -> dict:
        return {
            "error_code": self.error_code,
            "error_message": self.message,
            "retryable": self.retryable,
            "original_provider_error": str(self.original_error)
            if self.original_error
            else None,
        }


class GraphAuthError(GraphError):
    def __init__(
        self,
        message: str = "Token expired or invalid",
        original_error: Optional[Any] = None,
    ):
        super().__init__(
            message=message,
            error_code="AUTH_ERROR",
            retryable=True,
            original_error=original_error,
        )


class GraphNotFoundError(GraphError):
    def __init__(
        self,
        message: str = "Resource not found",
        original_error: Optional[Any] = None,
    ):
        super().__init__(
            message=message,
            error_code="NOT_FOUND",
            retryable=False,
            original_error=original_error,
        )


class GraphPermissionError(GraphError):
    def __init__(
        self,
        message: str = "Permission denied",
        original_error: Optional[Any] = None,
    ):
        super().__init__(
            message=message,
            error_code="PERMISSION_DENIED",
            retryable=False,
            original_error=original_error,
        )


class GraphRateLimitError(GraphError):
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        original_error: Optional[Any] = None,
    ):
        super().__init__(
            message=message,
            error_code="RATE_LIMIT",
            retryable=True,
            original_error=original_error,
        )


class GraphValidationError(GraphError):
    def __init__(
        self,
        message: str,
        original_error: Optional[Any] = None,
    ):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            retryable=False,
            original_error=original_error,
        )


def normalize_graph_error(
    exc: Exception, status_code: Optional[int] = None
) -> GraphError:
    """Map Microsoft Graph HTTP / transport errors to GraphError subclasses."""
    error_str = str(exc).lower()
    code = status_code
    if code is None:
        for candidate in (401, 403, 404, 429, 500, 502, 503):
            if str(candidate) in error_str:
                code = candidate
                break

    if code == 401 or ("invalid" in error_str and "token" in error_str):
        return GraphAuthError(message="Token expired or invalid", original_error=exc)
    if code == 403 or "permission" in error_str or "forbidden" in error_str:
        return GraphPermissionError(message="Permission denied", original_error=exc)
    if code == 404 or "not found" in error_str or "itemnotfound" in error_str:
        return GraphNotFoundError(message="Resource not found", original_error=exc)
    if code == 429 or "rate" in error_str or "throttle" in error_str:
        return GraphRateLimitError(message="Rate limit exceeded", original_error=exc)
    if code in (500, 502, 503):
        return GraphError(
            message="Microsoft Graph server error",
            error_code="PROVIDER_ERROR",
            retryable=True,
            original_error=exc,
        )
    return GraphError(
        message=str(exc),
        error_code="UNKNOWN_ERROR",
        retryable=False,
        original_error=exc,
    )
