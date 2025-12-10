"""
API logging middleware

Logs all API requests and responses to the database for monitoring and analytics.
"""

import time
import logging
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from packages.agent_fishing.tools.lure.orm.session import get_db_session
from packages.agent_fishing.tools.lure.models.system import APILog

logger = logging.getLogger(__name__)


class APILoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all API requests to database

    Captures:
    - Request method and endpoint
    - Response status code
    - Response time
    - User ID (if authenticated)
    - Client IP and user agent
    - Error messages (if any)
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

    async def dispatch(self, request: Request, call_next):
        """Process request and log to database"""

        # Skip logging for excluded paths
        if request.url.path in self.log_excluded_paths:
            return await call_next(request)

        # Record start time
        start_time = time.time()

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

        try:
            # Call next middleware/endpoint
            response = await call_next(request)
            status_code = response.status_code

        except Exception as e:
            # Capture exception
            error_message = str(e)
            logger.error(f"API error: {request.method} {request.url.path} - {error_message}")
            raise

        finally:
            # Calculate response time
            response_time = (time.time() - start_time) * 1000  # Convert to milliseconds

            # Log to database (non-blocking)
            try:
                self._log_to_database(
                    endpoint=request.url.path,
                    method=request.method,
                    status_code=status_code,
                    response_time=response_time,
                    user_id=user_id,
                    ip_address=client_host,
                    user_agent=user_agent,
                    error_message=error_message
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
        error_message: str | None = None
    ):
        """
        Save API log to database

        Args:
            endpoint: API endpoint path
            method: HTTP method
            status_code: HTTP status code
            response_time: Response time in milliseconds
            user_id: User ID if authenticated
            ip_address: Client IP address
            user_agent: User agent string
            error_message: Error message if any
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
                    user_agent=user_agent[:500] if user_agent else None,  # Truncate to 500 chars
                    error_message=error_message
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
