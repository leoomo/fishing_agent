"""
API logging middleware

Logs all API requests and responses to the database for monitoring and analytics.
Enhanced with intelligent error categorization and correlation tracking.
"""

import time
import logging
import traceback
import uuid
import json
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from apps.api.orm.session import get_db_session
from apps.api.models.system import APILog, ErrorCategory, ErrorSeverity

logger = logging.getLogger(__name__)


class ErrorCategorizer:
    """Intelligent error categorization utility"""

    @staticmethod
    def categorize_error(error_message: str, status_code: int, endpoint: str) -> ErrorCategory:
        """Categorize error based on message, status code, and endpoint"""
        error_msg_lower = error_message.lower() if error_message else ""
        endpoint_lower = endpoint.lower()

        # Check for specific error patterns
        if any(keyword in error_msg_lower for keyword in ["timeout", "timed out", "deadline exceeded"]):
            return ErrorCategory.TIMEOUT

        if any(keyword in error_msg_lower for keyword in ["openai", "claude", "anthropic", "gpt", "llm"]):
            return ErrorCategory.LLM_API

        if any(keyword in error_msg_lower for keyword in ["validation", "invalid", "malformed", "bad request"]):
            return ErrorCategory.VALIDATION

        if any(keyword in error_msg_lower for keyword in ["auth", "unauthorized", "forbidden", "permission"]):
            return ErrorCategory.AUTHENTICATION

        if any(keyword in error_msg_lower for keyword in ["rate limit", "quota", "too many requests"]):
            return ErrorCategory.RATE_LIMIT

        if any(keyword in error_msg_lower for keyword in ["database", "connection", "sql", "db"]):
            return ErrorCategory.DATABASE

        if any(keyword in error_msg_lower for keyword in ["network", "connection refused", "dns"]):
            return ErrorCategory.NETWORK

        if any(keyword in endpoint_lower for keyword in ["weather", "amap", "caiyun", "external"]):
            return ErrorCategory.EXTERNAL_SERVICE

        if any(keyword in error_msg_lower for keyword in ["memory", "disk", "cpu", "resource"]):
            return ErrorCategory.SYSTEM_RESOURCE

        # Default categorization based on status code
        if 400 <= status_code < 500:
            return ErrorCategory.VALIDATION
        elif 500 <= status_code < 600:
            return ErrorCategory.DATABASE
        else:
            return ErrorCategory.UNKNOWN

    @staticmethod
    def determine_severity(error_category: ErrorCategory, status_code: int) -> ErrorSeverity:
        """Determine error severity based on category and status code"""
        # Critical errors
        if status_code >= 500 or error_category in [ErrorCategory.DATABASE, ErrorCategory.SYSTEM_RESOURCE]:
            return ErrorSeverity.CRITICAL

        # High severity
        if error_category in [ErrorCategory.LLM_API, ErrorCategory.EXTERNAL_SERVICE, ErrorCategory.TIMEOUT]:
            return ErrorSeverity.HIGH

        # Medium severity
        if error_category in [ErrorCategory.RATE_LIMIT, ErrorCategory.AUTHENTICATION]:
            return ErrorSeverity.MEDIUM

        # Low severity
        if error_category in [ErrorCategory.VALIDATION, ErrorCategory.NETWORK]:
            return ErrorSeverity.LOW

        return ErrorSeverity.MEDIUM


class APILoggingMiddleware(BaseHTTPMiddleware):
    """
    Enhanced middleware to log all API requests to database with intelligent error analysis

    Captures:
    - Request method and endpoint
    - Response status code
    - Response time
    - User ID (if authenticated)
    - Client IP and user agent
    - Error messages (if any)
    - Intelligent error categorization and severity
    - Correlation ID for cross-service tracing
    - Stack traces for debugging
    - Error context metadata
    """

    def __init__(self, app: ASGIApp, log_excluded_paths: list[str] | None = None):
        """
        Initialize API logging middleware

        Args:
            app: ASGI application
            log_excluded_paths: Paths to exclude from logging (e.g., /health, /docs)
        """
        super().__init__(app)
        self.log_excluded_paths = log_excluded_paths or ["/health", "/docs", "/redoc", "/openapi.json"]
        self.categorizer = ErrorCategorizer()

    async def dispatch(self, request: Request, call_next):
        """Process request and log to database with enhanced error tracking"""

        # Skip logging for excluded paths
        if request.url.path in self.log_excluded_paths:
            return await call_next(request)

        # Record start time
        start_time = time.time()

        # Generate or extract correlation ID
        correlation_id = request.headers.get("x-correlation-id") or str(uuid.uuid4())
        # Store correlation ID in request state for downstream use
        request.state.correlation_id = correlation_id

        # Extract user ID from request state (set by auth dependency)
        user_id = None
        if hasattr(request.state, "user"):
            user_id = request.state.user.user_id

        # Get client IP and user agent
        client_host = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent", "")

        # Initialize response variables
        status_code = 500
        error_message = None
        stack_trace = None
        error_category = None
        error_severity = None
        error_context = None

        try:
            # Call next middleware/endpoint
            response = await call_next(request)
            status_code = response.status_code

            # Add correlation ID to response headers for client tracing
            response.headers["x-correlation-id"] = correlation_id

        except Exception as e:
            # Capture exception with enhanced details
            error_message = str(e)
            stack_trace = traceback.format_exc()

            # Categorize the error
            error_category = self.categorizer.categorize_error(
                error_message, status_code, request.url.path
            )
            error_severity = self.categorizer.determine_severity(error_category, status_code)

            # Create error context
            error_context = json.dumps({
                "request_method": request.method,
                "endpoint": request.url.path,
                "query_params": str(request.query_params),
                "client_host": client_host,
                "user_agent": user_agent[:100] if user_agent else None,
                "user_id": user_id,
                "timestamp": time.time()
            }, default=str)

            logger.error(f"API error: {request.method} {request.url.path} - {error_message}")
            raise

        finally:
            # Calculate response time
            response_time = (time.time() - start_time) * 1000  # Convert to milliseconds

            # Categorize errors for non-exception cases (4xx, 5xx responses)
            if not error_category and status_code >= 400:
                # Use response status for categorization when no exception occurred
                error_category = self.categorizer.categorize_error(
                    f"HTTP {status_code}", status_code, request.url.path
                )
                error_severity = self.categorizer.determine_severity(error_category, status_code)

            # Log to database (non-blocking)
            try:
                self._log_to_database(
                    endpoint=request.url.path,
                    method=request.method,
                    status_code=status_code,
                    response_time=response_time,
                    user_id=user_id,
                    ip_address=client_host,
                    user_agent=user_agent[:500] if user_agent else None,  # Truncate to 500 chars
                    error_message=error_message,
                    correlation_id=correlation_id,
                    error_category=error_category,
                    error_severity=error_severity,
                    error_context=error_context,
                    stack_trace=stack_trace
                )
            except Exception as log_error:
                # Don't let logging errors affect the response
                logger.error(f"Failed to log API request: {log_error}")

        return response

    def _log_to_database(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        response_time: float,
        user_id: int | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        error_message: str | None = None,
        correlation_id: str | None = None,
        error_category: ErrorCategory | None = None,
        error_severity: ErrorSeverity | None = None,
        error_context: str | None = None,
        stack_trace: str | None = None
    ):
        """
        Save enhanced API log to database with categorization and correlation

        Args:
            endpoint: API endpoint path
            method: HTTP method
            status_code: HTTP status code
            response_time: Response time in milliseconds
            user_id: User ID if authenticated
            ip_address: Client IP address
            user_agent: User agent string
            error_message: Error message if any
            correlation_id: Correlation ID for cross-service tracing
            error_category: Intelligent error categorization
            error_severity: Error severity level
            error_context: Additional error context (JSON)
            stack_trace: Stack trace for debugging
        """
        try:
            with get_db_session() as session:
                api_log = APILog(
                    endpoint=endpoint,
                    method=method,
                    status_code=status_code,
                    response_time=response_time,
                    user_id=user_id,
                    ip_address=ip_address,
                    user_agent=user_agent,  # Already truncated in caller
                    error_message=error_message,
                    correlation_id=correlation_id,
                    error_category=error_category,
                    error_severity=error_severity,
                    error_context=error_context,
                    stack_trace=stack_trace
                )

                session.add(api_log)
                session.commit()

        except Exception as e:
            logger.error(f"Database logging error: {e}")
            # Don't raise - logging should never break the API


def install_api_logging_middleware(app, excluded_paths: list[str] | None = None):
    """
    Install API logging middleware to FastAPI app

    Args:
        app: FastAPI application instance
        excluded_paths: Paths to exclude from logging

    Example:
        from fastapi import FastAPI
        app = FastAPI()
        install_api_logging_middleware(app, excluded_paths=["/health", "/metrics"])
    """
    app.add_middleware(
        APILoggingMiddleware,
        log_excluded_paths=excluded_paths
    )
    logger.info("API logging middleware installed")
