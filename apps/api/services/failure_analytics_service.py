"""
Failure Analytics Service

Provides advanced failure pattern detection, correlation analysis, and root cause analysis
for the fishing agent monitoring system.
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc, text
import numpy as np
from collections import defaultdict, Counter

from packages.agent_fishing.tools.lure.models.system import (
    APILog, AgentExecutionLog, ToolCallLog, LLMLog,
    ErrorCategory, ErrorSeverity
)


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
        time_delta = self._parse_time_range(time_range)
        start_time = datetime.utcnow() - time_delta

        patterns = []

        # Pattern 1: Error Burst Detection
        burst_patterns = await self._detect_error_bursts(start_time)
        patterns.extend(burst_patterns)

        # Pattern 2: Cascading Failures
        cascade_patterns = await self._detect_cascading_failures(start_time)
        patterns.extend(cascade_patterns)

        # Pattern 3: Recurring Error Types
        recurring_patterns = await self._detect_recurring_errors(start_time)
        patterns.extend(recurring_patterns)

        # Pattern 4: Service Dependency Failures
        dependency_patterns = await self._detect_dependency_failures(start_time)
        patterns.extend(dependency_patterns)

        return patterns

    async def get_error_correlation(self, correlation_id: str) -> Optional[ErrorChain]:
        """
        Get error correlation chain for a specific correlation ID

        Args:
            correlation_id: Correlation ID to analyze

        Returns:
            ErrorChain object with related errors
        """
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

    async def get_root_cause_analysis(self, time_range: str = "24h") -> List[RootCause]:
        """
        Perform root cause analysis on recent failures

        Args:
            time_range: Time range for analysis

        Returns:
            List of potential root causes with confidence scores
        """
        time_delta = self._parse_time_range(time_range)
        start_time = datetime.utcnow() - time_delta

        root_causes = []

        # Analyze LLM API failures
        llm_root_causes = await self._analyze_llm_failures(start_time)
        root_causes.extend(llm_root_causes)

        # Analyze external service failures
        external_root_causes = await self._analyze_external_service_failures(start_time)
        root_causes.extend(external_root_causes)

        # Analyze tool execution failures
        tool_root_causes = await self._analyze_tool_failures(start_time)
        root_causes.extend(tool_root_causes)

        # Analyze database issues
        db_root_causes = await self._analyze_database_failures(start_time)
        root_causes.extend(db_root_causes)

        return root_causes

    async def get_failure_metrics(self) -> Dict[str, Any]:
        """
        Get comprehensive failure metrics

        Returns:
            Dictionary with failure statistics and metrics
        """
        now = datetime.utcnow()
        last_24h = now - timedelta(hours=24)
        last_7d = now - timedelta(days=7)

        metrics = {}

        # API Error Rates
        api_total_24h = self.db.query(APILog).filter(APILog.timestamp >= last_24h).count()
        api_errors_24h = self.db.query(APILog).filter(
            and_(APILog.timestamp >= last_24h, APILog.status_code >= 400)
        ).count()

        metrics['api_error_rate_24h'] = (api_errors_24h / api_total_24h * 100) if api_total_24h > 0 else 0

        # Agent Success Rates
        agent_total_24h = self.db.query(AgentExecutionLog).filter(
            AgentExecutionLog.timestamp >= last_24h
        ).count()
        agent_success_24h = self.db.query(AgentExecutionLog).filter(
            and_(AgentExecutionLog.timestamp >= last_24h, AgentExecutionLog.success == True)
        ).count()

        metrics['agent_success_rate_24h'] = (agent_success_24h / agent_total_24h * 100) if agent_total_24h > 0 else 0

        # Error Categories Distribution (24h)
        error_categories = self.db.query(
            APILog.error_category, func.count(APILog.id)
        ).filter(
            and_(
                APILog.timestamp >= last_24h,
                APILog.error_category.isnot(None)
            )
        ).group_by(APILog.error_category).all()

        metrics['error_categories_24h'] = [
            {'category': cat.value if isinstance(cat, ErrorCategory) else cat, 'count': count}
            for cat, count in error_categories
        ]

        # Top Error Messages (7d)
        top_errors = self.db.query(
            APILog.error_message, func.count(APILog.id)
        ).filter(
            and_(
                APILog.timestamp >= last_7d,
                APILog.error_message.isnot(None),
                APILog.status_code >= 400
            )
        ).group_by(APILog.error_message).order_by(desc(func.count(APILog.id))).limit(10).all()

        metrics['top_error_messages_7d'] = [
            {'message': msg, 'count': count} for msg, count in top_errors
        ]

        # MTTR (Mean Time To Recovery) estimation
        recovery_patterns = self.db.query(AgentExecutionLog).filter(
            and_(
                AgentExecutionLog.timestamp >= last_7d,
                AgentExecutionLog.recovery_attempted == True,
                AgentExecutionLog.recovery_successful == True,
                AgentExecutionLog.failure_stage.isnot(None)
            )
        ).all()

        if recovery_patterns:
            # Simple MTTR calculation based on failure stages
            metrics['mttr_minutes'] = len(recovery_patterns) * 5  # Placeholder
        else:
            metrics['mttr_minutes'] = None

        return metrics

    async def _detect_error_bursts(self, start_time: datetime) -> List[FailurePattern]:
        """Detect sudden error rate increases"""
        patterns = []

        # Analyze API errors per minute
        api_errors = self.db.query(
            func.date_trunc('minute', APILog.timestamp).label('minute'),
            func.count(APILog.id).label('error_count')
        ).filter(
            and_(
                APILog.timestamp >= start_time,
                APILog.status_code >= 400
            )
        ).group_by('minute').all()

        if len(api_errors) < 5:  # Need sufficient data
            return patterns

        error_counts = [count for _, count in api_errors]
        mean_errors = np.mean(error_counts)
        std_errors = np.std(error_counts)

        # Detect bursts (3-sigma threshold)
        threshold = mean_errors + self.burst_threshold * std_errors

        burst_periods = [
            (minute, count) for minute, count in api_errors
            if count > threshold
        ]

        for burst_time, burst_count in burst_periods:
            pattern = FailurePattern(
                pattern_id=str(uuid.uuid4()),
                pattern_type="error_burst",
                description=f"API error burst detected: {burst_count} errors at {burst_time}",
                severity="high" if burst_count > threshold * 2 else "medium",
                frequency=int(burst_count),
                affected_services=["api"],
                confidence=0.85,
                metadata={
                    'burst_time': burst_time.isoformat(),
                    'threshold': threshold,
                    'deviation': (burst_count - mean_errors) / std_errors
                }
            )
            patterns.append(pattern)

        return patterns

    async def _detect_cascading_failures(self, start_time: datetime) -> List[FailurePattern]:
        """Detect cascading failures across services"""
        patterns = []

        # Find correlation IDs with multiple failures
        cascade_errors = self.db.query(
            APILog.correlation_id,
            func.count(APILog.id).label('failure_count'),
            func.count(func.distinct(APILog.endpoint)).label('endpoint_count')
        ).filter(
            and_(
                APILog.timestamp >= start_time,
                APILog.correlation_id.isnot(None),
                APILog.status_code >= 400
            )
        ).group_by(APILog.correlation_id).having(
            func.count(APILog.id) >= 3
        ).all()

        for correlation_id, failure_count, endpoint_count in cascade_errors:
            pattern = FailurePattern(
                pattern_id=str(uuid.uuid4()),
                pattern_type="cascading_failure",
                description=f"Cascading failure: {failure_count} failures across {endpoint_count} endpoints",
                severity="critical" if failure_count > 5 else "high",
                frequency=failure_count,
                affected_services=["api"],
                confidence=0.90,
                metadata={
                    'correlation_id': correlation_id,
                    'endpoint_count': endpoint_count
                }
            )
            patterns.append(pattern)

        return patterns

    async def _detect_recurring_errors(self, start_time: datetime) -> List[FailurePattern]:
        """Detect recurring error patterns"""
        patterns = []

        # Group by error message patterns
        recurring_errors = self.db.query(
            APILog.error_message,
            func.count(APILog.id).label('count'),
            func.count(func.distinct(func.date(APILog.timestamp))).label('days_affected')
        ).filter(
            and_(
                APILog.timestamp >= start_time,
                APILog.error_message.isnot(None),
                APILog.status_code >= 400
            )
        ).group_by(APILog.error_message).having(
            and_(func.count(APILog.id) >= 5, func.count(func.distinct(func.date(APILog.timestamp))) >= 2)
        ).all()

        for error_msg, count, days in recurring_errors:
            pattern = FailurePattern(
                pattern_id=str(uuid.uuid4()),
                pattern_type="recurring_error",
                description=f"Recurring error: '{error_msg[:100]}...' occurred {count} times over {days} days",
                severity="medium",
                frequency=count,
                affected_services=["api"],
                confidence=0.75,
                metadata={
                    'error_message': error_msg,
                    'days_affected': days
                }
            )
            patterns.append(pattern)

        return patterns

    async def _detect_dependency_failures(self, start_time: datetime) -> List[FailurePattern]:
        """Detect service dependency failures"""
        patterns = []

        # Analyze LLM provider failures
        llm_failures = self.db.query(
            LLMLog.model_provider,
            func.count(LLMLog.id).label('failure_count')
        ).filter(
            and_(
                LLMLog.timestamp >= start_time,
                LLMLog.success == False
            )
        ).group_by(LLMLog.model_provider).having(
            func.count(LLMLog.id) >= 3
        ).all()

        for provider, failure_count in llm_failures:
            pattern = FailurePattern(
                pattern_id=str(uuid.uuid4()),
                pattern_type="dependency_failure",
                description=f"LLM provider '{provider}' failures: {failure_count} failed calls",
                severity="high" if failure_count > 10 else "medium",
                frequency=failure_count,
                affected_services=[f"llm_{provider}"],
                confidence=0.80,
                metadata={
                    'provider': provider,
                    'service_type': 'llm'
                }
            )
            patterns.append(pattern)

        return patterns

    async def _analyze_llm_failures(self, start_time: datetime) -> List[RootCause]:
        """Analyze LLM API failures for root causes"""
        root_causes = []

        llm_errors = self.db.query(LLMLog).filter(
            and_(
                LLMLog.timestamp >= start_time,
                LLMLog.success == False,
                LLMLog.error_message.isnot(None)
            )
        ).all()

        if not llm_errors:
            return root_causes

        # Group errors by provider
        provider_errors = defaultdict(list)
        for error in llm_errors:
            provider_errors[error.model_provider].append(error)

        for provider, errors in provider_errors.items():
            error_messages = [e.error_message for e in errors]

            # Common LLM error patterns
            if any("rate limit" in msg.lower() for msg in error_messages):
                root_cause.append(RootCause(
                    cause_id=str(uuid.uuid4()),
                    cause_type="rate_limiting",
                    description=f"Rate limiting detected for {provider} API",
                    confidence=0.85,
                    evidence=[msg for msg in error_messages if "rate limit" in msg.lower()][:3],
                    suggested_action="Implement request throttling and retry with exponential backoff"
                ))

            if any("timeout" in msg.lower() for msg in error_messages):
                root_causes.append(RootCause(
                    cause_id=str(uuid.uuid4()),
                    cause_type="timeout",
                    description=f"Timeout issues detected for {provider} API",
                    confidence=0.80,
                    evidence=[msg for msg in error_messages if "timeout" in msg.lower()][:3],
                    suggested_action="Increase timeout settings and implement request optimization"
                ))

        return root_causes

    async def _analyze_external_service_failures(self, start_time: datetime) -> List[RootCause]:
        """Analyze external service failures"""
        root_causes = []

        external_errors = self.db.query(APILog).filter(
            and_(
                APILog.timestamp >= start_time,
                APILog.error_category == ErrorCategory.EXTERNAL_SERVICE,
                APILog.error_message.isnot(None)
            )
        ).all()

        if not external_errors:
            return root_causes

        # Group by endpoint
        endpoint_errors = defaultdict(list)
        for error in external_errors:
            endpoint_errors[error.endpoint].append(error)

        for endpoint, errors in endpoint_errors.items():
            if len(errors) >= 3:  # Multiple failures suggest service issue
                root_causes.append(RootCause(
                    cause_id=str(uuid.uuid4()),
                    cause_type="external_service",
                    description=f"External service issues detected at {endpoint}",
                    confidence=0.75,
                    evidence=[e.error_message for e in errors][:3],
                    suggested_action="Check external service status and implement circuit breaker pattern"
                ))

        return root_causes

    async def _analyze_tool_failures(self, start_time: datetime) -> List[RootCause]:
        """Analyze tool execution failures"""
        root_causes = []

        tool_errors = self.db.query(ToolCallLog).filter(
            and_(
                ToolCallLog.timestamp >= start_time,
                ToolCallLog.success == False,
                ToolCallLog.error_message.isnot(None)
            )
        ).all()

        if not tool_errors:
            return root_causes

        # Group by tool name
        tool_failures = defaultdict(list)
        for error in tool_errors:
            tool_failures[error.tool_name].append(error)

        for tool_name, errors in tool_failures.items():
            if len(errors) >= 5:  # High failure rate
                root_causes.append(RootCause(
                    cause_id=str(uuid.uuid4()),
                    cause_type="tool_failure",
                    description=f"High failure rate detected for tool '{tool_name}'",
                    confidence=0.80,
                    evidence=[e.error_message for e in errors][:3],
                    suggested_action=f"Review {tool_name} tool implementation and add better error handling"
                ))

        return root_causes

    async def _analyze_database_failures(self, start_time: datetime) -> List[RootCause]:
        """Analyze database-related failures"""
        root_causes = []

        db_errors = self.db.query(APILog).filter(
            and_(
                APILog.timestamp >= start_time,
                APILog.error_category == ErrorCategory.DATABASE,
                APILog.error_message.isnot(None)
            )
        ).all()

        if not db_errors:
            return root_causes

        error_messages = [e.error_message for e in db_errors]

        if any("connection" in msg.lower() for msg in error_messages):
            root_causes.append(RootCause(
                cause_id=str(uuid.uuid4()),
                cause_type="database_connection",
                description="Database connection issues detected",
                confidence=0.85,
                evidence=[msg for msg in error_messages if "connection" in msg.lower()][:3],
                suggested_action="Check database connectivity and implement connection pooling"
            ))

        if any("timeout" in msg.lower() for msg in error_messages):
            root_causes.append(RootCause(
                cause_id=str(uuid.uuid4()),
                cause_type="database_timeout",
                description="Database timeout issues detected",
                confidence=0.75,
                evidence=[msg for msg in error_messages if "timeout" in msg.lower()][:3],
                suggested_action="Optimize database queries and check database performance"
            ))

        return root_causes

    def _parse_time_range(self, time_range: str) -> timedelta:
        """Parse time range string to timedelta"""
        if time_range.endswith('h'):
            return timedelta(hours=int(time_range[:-1]))
        elif time_range.endswith('d'):
            return timedelta(days=int(time_range[:-1]))
        elif time_range.endswith('m'):
            return timedelta(minutes=int(time_range[:-1]))
        else:
            return timedelta(hours=1)  # Default to 1 hour


# Helper methods for ErrorChain class
def _determine_root_cause(self) -> str:
    """Determine root cause from error chain"""
    critical_errors = [e for e in self.errors if e.get('severity') == 'critical']
    if critical_errors:
        return f"Critical error in {critical_errors[0]['service']}"

    # Find earliest error
    if self.errors:
        earliest = min(self.errors, key=lambda x: x['timestamp'])
        return f"Initial failure in {earliest['service']}: {earliest.get('error_message', 'Unknown')[:50]}"

    return "Unknown root cause"


def _calculate_impact_score(self) -> int:
    """Calculate impact score based on error count and severity"""
    severity_weights = {'critical': 10, 'high': 5, 'medium': 2, 'low': 1}
    score = 0

    for error in self.errors:
        severity = error.get('severity', 'low')
        score += severity_weights.get(severity, 1)

    return score


# Bind helper methods to ErrorChain class
ErrorChain._determine_root_cause = _determine_root_cause
ErrorChain._calculate_impact_score = _calculate_impact_score