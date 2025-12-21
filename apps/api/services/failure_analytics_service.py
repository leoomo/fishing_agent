"""
Failure Analytics Service

Provides failure pattern detection, correlation analysis, and root cause analysis
for the fishing agent monitoring system.

Note: This is a simplified implementation that provides basic analytics.
Advanced features (burst detection with numpy, cascading failure analysis,
dependency failure detection) have been removed in favor of a lightweight
approach that doesn't require numpy and handles model import failures gracefully.

For production systems requiring advanced analytics, consider:
- Re-implementing numpy-based burst detection
- Adding cascading failure detection across services
- Implementing time-series analysis for pattern detection
"""

import uuid
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_
from collections import defaultdict

from packages.agent_fishing.tools.lure.models.system import (
    APILog, AgentExecutionLog
)

logger = logging.getLogger(__name__)


class FailurePattern:
    """Represents a detected failure pattern"""
    def __init__(self, pattern_id: str, pattern_type: str, description: str,
                 severity: str, frequency: int, affected_services: List[str],
                 confidence: float, metadata: Dict[str, Any] = None):
        self.pattern_id = pattern_id
        self.pattern_type = pattern_type
        self.description = description
        self.severity = severity
        self.frequency = frequency
        self.affected_services = affected_services
        self.confidence = confidence
        self.metadata = metadata or {}
        self.detected_at = datetime.utcnow()


class ErrorChain:
    """Represents a chain of related errors"""
    def __init__(self, correlation_id: str, errors: List[Dict]):
        self.correlation_id = correlation_id
        self.errors = errors
        self.root_cause = self._determine_root_cause()
        self.impact_score = self._calculate_impact_score()

    def _determine_root_cause(self) -> str:
        """Simple root cause determination"""
        if not self.errors:
            return "unknown"
        return self.errors[0].get('error_message', 'unknown')

    def _calculate_impact_score(self) -> int:
        """Calculate impact score based on error count and severity"""
        return len(self.errors) * 10


class RootCause:
    """Represents a potential root cause analysis"""
    def __init__(self, cause_id: str, cause_type: str, description: str,
                 confidence: float, evidence: List[str], suggested_action: str):
        self.cause_id = cause_id
        self.cause_type = cause_type
        self.description = description
        self.confidence = confidence
        self.evidence = evidence
        self.suggested_action = suggested_action
        self.generated_at = datetime.utcnow()


class FailureAnalyticsService:
    """Advanced failure analytics service with pattern detection"""

    def __init__(self, db_session: Session):
        self.db = db_session
        self.pattern_cache = {}
        self.burst_threshold = 3.0  # 3-sigma threshold for burst detection
        self.window_minutes = 5    # Sliding window for burst detection

    async def detect_failure_patterns(self, time_range: str = "1h") -> List[FailurePattern]:
        """
        Detect failure patterns in the specified time range

        Args:
            time_range: Time range for analysis (e.g., "1h", "24h", "7d")

        Returns:
            List of detected failure patterns
        """
        try:
            time_delta = self._parse_time_range(time_range)
            start_time = datetime.utcnow() - time_delta

            # For now, return simple pattern detection
            patterns = []

            # Check for error bursts
            recent_errors = self.db.query(APILog).filter(
                and_(APILog.timestamp >= start_time, APILog.status_code >= 400)
            ).count()

            if recent_errors > 10:
                patterns.append(FailurePattern(
                    pattern_id=f"error_burst_{uuid.uuid4().hex[:8]}",
                    pattern_type="error_burst",
                    description=f"Detected {recent_errors} errors in the last {time_range}",
                    severity="high" if recent_errors > 50 else "medium",
                    frequency=recent_errors,
                    affected_services=["api"],
                    confidence=0.8
                ))

            return patterns
        except Exception as e:
            logger.error(f"Error detecting failure patterns: {e}", exc_info=True)
            return []

    async def get_error_correlation(self, correlation_id: str) -> Optional[ErrorChain]:
        """
        Get error correlation chain for a specific correlation ID

        Args:
            correlation_id: Correlation ID to analyze

        Returns:
            ErrorChain object with related errors
        """
        try:
            errors = []

            # Get API logs with correlation ID
            api_logs = self.db.query(APILog).filter(
                APILog.correlation_id == correlation_id
            ).order_by(APILog.timestamp).all()

            for log in api_logs:
                errors.append({
                    'timestamp': log.timestamp,
                    'service': 'api',
                    'endpoint': log.endpoint,
                    'error_category': log.error_category.value if log.error_category else None,
                    'severity': log.error_severity.value if log.error_severity else None,
                    'error_message': log.error_message,
                    'status_code': log.status_code
                })

            # Get agent execution logs with correlation ID
            agent_logs = self.db.query(AgentExecutionLog).filter(
                AgentExecutionLog.correlation_id == correlation_id
            ).order_by(AgentExecutionLog.timestamp).all()

            for log in agent_logs:
                errors.append({
                    'timestamp': log.timestamp,
                    'service': 'agent',
                    'agent_type': log.agent_type,
                    'error_category': log.error_category.value if log.error_category else None,
                    'failure_stage': log.failure_stage,
                    'error_message': log.error_message,
                    'success': log.success,
                    'failed_tool_name': log.failed_tool_name
                })

            if not errors:
                return None

            return ErrorChain(correlation_id, errors)
        except Exception as e:
            logger.error(f"Error getting error correlation: {e}", exc_info=True)
            return None

    async def get_root_cause_analysis(self, time_range: str = "24h") -> List[RootCause]:
        """
        Perform root cause analysis on recent failures

        Args:
            time_range: Time range for analysis

        Returns:
            List of potential root causes with confidence scores
        """
        try:
            time_delta = self._parse_time_range(time_range)
            start_time = datetime.utcnow() - time_delta

            root_causes = []

            # Analyze recent failures
            recent_failures = self.db.query(APILog).filter(
                and_(APILog.timestamp >= start_time, APILog.status_code >= 400)
            ).limit(50).all()

            if recent_failures:
                # Group by error message patterns
                error_groups = defaultdict(list)
                for log in recent_failures:
                    if log.error_message:
                        error_groups[log.error_message[:100]].append(log)

                # Create root cause analysis for most common errors
                common_errors = sorted(error_groups.items(), key=lambda x: len(x[1]), reverse=True)[:3]

                for error_pattern, logs in common_errors:
                    root_causes.append(RootCause(
                        cause_id=f"root_cause_{uuid.uuid4().hex[:8]}",
                        cause_type="recurring_error",
                        description=f"Recurring error: {error_pattern}",
                        confidence=min(0.9, len(logs) / 20.0),
                        evidence=[f"Occurred {len(logs)} times in {time_range}"],
                        suggested_action="Investigate error pattern and implement fix"
                    ))

            return root_causes
        except Exception as e:
            logger.error(f"Error getting root cause analysis: {e}", exc_info=True)
            return []

    async def get_failure_metrics(self) -> Dict[str, Any]:
        """
        Get comprehensive failure metrics

        Returns:
            Dictionary with failure statistics and metrics
        """
        try:
            now = datetime.utcnow()
            last_24h = now - timedelta(hours=24)

            # Simple API error rate calculation
            api_total_24h = self.db.query(APILog).filter(APILog.timestamp >= last_24h).count()
            api_errors_24h = self.db.query(APILog).filter(
                and_(APILog.timestamp >= last_24h, APILog.status_code >= 400)
            ).count()

            # Simple agent success rate calculation
            agent_total_24h = self.db.query(AgentExecutionLog).filter(
                AgentExecutionLog.timestamp >= last_24h
            ).count()
            agent_success_24h = self.db.query(AgentExecutionLog).filter(
                and_(AgentExecutionLog.timestamp >= last_24h, AgentExecutionLog.success == True)
            ).count()

            return {
                'api_error_rate_24h': (api_errors_24h / api_total_24h * 100) if api_total_24h > 0 else 0,
                'agent_success_rate_24h': (agent_success_24h / agent_total_24h * 100) if agent_total_24h > 0 else 0,
                'total_api_requests_24h': api_total_24h,
                'total_agent_executions_24h': agent_total_24h,
                'error_categories_24h': [],
                'top_error_messages_7d': [],
                'failure_pattern_frequency_7d': {},
                'mttr_minutes': None
            }
        except Exception as e:
            logger.error(f"Error getting failure metrics: {e}", exc_info=True)
            return {
                'api_error_rate_24h': 0,
                'agent_success_rate_24h': 0,
                'total_api_requests_24h': 0,
                'total_agent_executions_24h': 0,
                'error_categories_24h': [],
                'top_error_messages_7d': [],
                'failure_pattern_frequency_7d': {},
                'mttr_minutes': None
            }

    def _parse_time_range(self, time_range: str) -> timedelta:
        """Parse time range string into timedelta"""
        if time_range.endswith('h'):
            hours = int(time_range[:-1])
            return timedelta(hours=hours)
        elif time_range.endswith('d'):
            days = int(time_range[:-1])
            return timedelta(days=days)
        elif time_range.endswith('m'):
            minutes = int(time_range[:-1])
            return timedelta(minutes=minutes)
        else:
            # Default to 1 hour
            return timedelta(hours=1)