"""
Audit Logging with Compliance Tagging
Logs all events with time, user, session, score, and audit information
"""

from fastapi import APIRouter, HTTPException, Request, Depends, Query, status
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import logging
import threading

from api.middleware import limiter, verify_api_key, get_error_response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/audit", tags=["audit"])


class EventType(str, Enum):
    """Audit event types"""

    SESSION_STARTED = "session_started"
    SESSION_COMPLETED = "session_completed"
    BIOMETRIC_CAPTURED = "biometric_captured"
    VOICE_CAPTURED = "voice_captured"
    RISK_EVALUATED = "risk_evaluated"
    AUTHENTICATION_ATTEMPT = "authentication_attempt"
    ESCALATION_CREATED = "escalation_created"
    ESCALATION_REVIEWED = "escalation_reviewed"
    SAR_GENERATED = "sar_generated"
    COMPLIANCE_CHECK = "compliance_check"
    SYSTEM_ERROR = "system_error"


class ComplianceTag(str, Enum):
    """Compliance framework tags"""

    GDPR = "gdpr"
    PCI_DSS = "pci_dss"
    SOC2 = "soc2"
    FINCEN = "fincen"
    KYC = "kyc"
    AML = "aml"
    BIOMETRIC_CONSENT = "biometric_consent"
    DATA_RETENTION = "data_retention"


class AuditEvent(BaseModel):
    """Audit log event"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "event_type": "risk_evaluated",
                "user_id": "USER-MASKED-123",
                "session_id": "SESSION-ABC123",
                "score": 0.25,
                "metadata": {"decision": "approve", "risk_level": "low"},
                "compliance_tags": ["kyc", "aml"],
                "ip_address": "masked_ip_xxx",
                "user_agent": "MobileApp/1.0",
            }
        }
    )

    event_type: EventType = Field(..., description="Type of event")
    user_id: str = Field(..., description="User identifier (privacy-masked)")
    session_id: Optional[str] = Field(None, description="Session identifier if applicable")
    score: Optional[float] = Field(
        None, ge=0, le=1, description="Associated score (risk, confidence, etc.)"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional event data")
    compliance_tags: List[ComplianceTag] = Field(
        default_factory=list, description="Compliance framework tags"
    )
    ip_address: Optional[str] = Field(None, description="Client IP (privacy-masked)")
    user_agent: Optional[str] = Field(None, description="Client user agent")


class AuditLogResponse(BaseModel):
    """Audit log entry response"""

    log_id: str = Field(..., description="Unique log entry identifier")
    timestamp: datetime = Field(..., description="Event timestamp")
    event_type: EventType
    user_id: str
    session_id: Optional[str]
    score: Optional[float]
    metadata: Dict[str, Any]
    compliance_tags: List[ComplianceTag]
    ip_address: Optional[str]
    user_agent: Optional[str]


class AuditQueryFilter(BaseModel):
    """Filter parameters for audit log queries"""

    event_type: Optional[EventType] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    compliance_tag: Optional[ComplianceTag] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


# In-memory audit log storage (replace with database in production)
# Thread-safe implementation with lock
audit_logs_db: List[Dict[str, Any]] = []
_audit_logs_lock = threading.Lock()
_log_counter = 0
_log_counter_lock = threading.Lock()


def _get_next_log_id() -> str:
    """Thread-safe log ID generation."""
    global _log_counter
    with _log_counter_lock:
        _log_counter += 1
        return f"LOG-{_log_counter:08d}"


def mask_sensitive_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Privacy-mask sensitive data in audit logs.

    Args:
        data: Dictionary potentially containing sensitive data

    Returns:
        Dictionary with sensitive fields masked
    """
    masked = data.copy()

    # Mask common sensitive fields
    sensitive_fields = [
        "password",
        "pin",
        "ssn",
        "tax_id",
        "credit_card",
        "account_number",
        "routing_number",
        "full_address",
        "phone_number",
        "email",
        "voice_sample",
        "biometric_data",
    ]

    for field in sensitive_fields:
        if field in masked:
            masked[field] = "***MASKED***"

    # Recursively mask nested dictionaries
    for key, value in masked.items():
        if isinstance(value, dict):
            masked[key] = mask_sensitive_data(value)

    return masked


@router.post(
    "/log",
    response_model=AuditLogResponse,
    summary="Create Audit Log Entry",
    description="Log an event with compliance tagging",
)
@limiter.limit("200/minute")
async def create_audit_log(
    request: Request, audit_event: AuditEvent, api_key: Optional[str] = Depends(verify_api_key)
):
    """
    Create a new audit log entry.

    All events are logged with time, user, session, score, and compliance tags
    for regulatory reporting and forensic analysis.

    **Rate Limit**: 200 requests per minute

    **Returns**: Audit log entry with unique identifier
    """
    try:
        # Thread-safe log ID generation
        log_id = _get_next_log_id()

        # Mask sensitive data in metadata
        masked_metadata = mask_sensitive_data(audit_event.metadata)

        log_entry = {
            "log_id": log_id,
            "timestamp": datetime.now(),
            "event_type": audit_event.event_type,
            "user_id": audit_event.user_id,
            "session_id": audit_event.session_id,
            "score": audit_event.score,
            "metadata": masked_metadata,
            "compliance_tags": audit_event.compliance_tags,
            "ip_address": audit_event.ip_address,
            "user_agent": audit_event.user_agent,
        }

        # Thread-safe append to audit logs
        with _audit_logs_lock:
            audit_logs_db.append(log_entry)

        # Log to system logger for external aggregation
        logger.info(
            f"AUDIT: {audit_event.event_type} | User: {audit_event.user_id} | "
            f"Session: {audit_event.session_id} | Score: {audit_event.score} | "
            f"Tags: {','.join(audit_event.compliance_tags or [])}"
        )

        return AuditLogResponse(**log_entry)

    except Exception as e:
        logger.error(f"Error creating audit log: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=get_error_response("PROCESSING_ERROR", "Failed to create audit log"),
        )


@router.get(
    "/logs",
    response_model=List[AuditLogResponse],
    summary="Query Audit Logs",
    description="Query audit logs with filtering",
)
@limiter.limit("100/minute")
async def query_audit_logs(
    request: Request,
    event_type: Optional[EventType] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    compliance_tag: Optional[ComplianceTag] = None,
    start_date: Optional[str] = Query(None, description="ISO format datetime"),
    end_date: Optional[str] = Query(None, description="ISO format datetime"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum results to return"),
    api_key: Optional[str] = Depends(verify_api_key),
):
    """
    Query audit logs with filtering.

    Supports filtering by event type, user, session, compliance tag, and date range.

    **Rate Limit**: 100 requests per minute

    **Parameters**:
    - `event_type`: Filter by event type
    - `user_id`: Filter by user ID
    - `session_id`: Filter by session ID
    - `compliance_tag`: Filter by compliance tag
    - `start_date`: Start of date range (ISO format)
    - `end_date`: End of date range (ISO format)
    - `limit`: Maximum results to return (1-1000)

    **Returns**: List of audit log entries
    """
    # Thread-safe copy
    with _audit_logs_lock:
        logs = audit_logs_db.copy()

    # Apply filters
    if event_type:
        logs = [log for log in logs if log["event_type"] == event_type]

    if user_id:
        logs = [log for log in logs if log["user_id"] == user_id]

    if session_id:
        logs = [log for log in logs if log["session_id"] == session_id]

    if compliance_tag:
        logs = [log for log in logs if compliance_tag in log.get("compliance_tags", [])]

    # Date range filtering
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            logs = [log for log in logs if log["timestamp"] >= start_dt]
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=get_error_response("VALIDATION_ERROR", "Invalid start_date format"),
            )

    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            logs = [log for log in logs if log["timestamp"] <= end_dt]
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=get_error_response("VALIDATION_ERROR", "Invalid end_date format"),
            )

    # Sort by timestamp (most recent first) and apply limit
    logs.sort(key=lambda x: x["timestamp"], reverse=True)
    logs = logs[:limit]

    return [AuditLogResponse(**log) for log in logs]


@router.get(
    "/session/{session_id}/timeline",
    summary="Get Session Timeline",
    description="Get chronological timeline of all events for a session",
)
@limiter.limit("100/minute")
async def get_session_timeline(
    request: Request, session_id: str, api_key: Optional[str] = Depends(verify_api_key)
):
    """
    Get chronological timeline of all audit events for a specific session.

    **Rate Limit**: 100 requests per minute

    **Returns**: Timeline of events with full details
    """
    # Thread-safe access
    with _audit_logs_lock:
        session_logs = [log for log in audit_logs_db if log.get("session_id") == session_id]

    if not session_logs:
        return {
            "session_id": session_id,
            "events": [],
            "message": "No audit logs found for this session",
        }

    # Sort chronologically
    session_logs.sort(key=lambda x: x["timestamp"])

    return {
        "session_id": session_id,
        "events": [AuditLogResponse(**log) for log in session_logs],
        "total_events": len(session_logs),
        "first_event": session_logs[0]["timestamp"].isoformat(),
        "last_event": session_logs[-1]["timestamp"].isoformat(),
    }


@router.get(
    "/compliance/report",
    summary="Generate Compliance Report",
    description="Generate compliance report for specific framework",
)
@limiter.limit("20/minute")
async def generate_compliance_report(
    request: Request,
    compliance_tag: ComplianceTag,
    start_date: Optional[str] = Query(None, description="ISO format datetime"),
    end_date: Optional[str] = Query(None, description="ISO format datetime"),
    api_key: Optional[str] = Depends(verify_api_key),
):
    """
    Generate compliance report for a specific framework.

    Aggregates all events tagged with the specified compliance framework.

    **Rate Limit**: 20 requests per minute

    **Returns**: Compliance report with aggregated statistics
    """
    # Thread-safe access and filter logs by compliance tag
    with _audit_logs_lock:
        compliance_logs = [
            log for log in audit_logs_db if compliance_tag in log.get("compliance_tags", [])
        ]

    # Apply date filtering if provided
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            compliance_logs = [log for log in compliance_logs if log["timestamp"] >= start_dt]
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=get_error_response("VALIDATION_ERROR", "Invalid start_date format"),
            )

    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            compliance_logs = [log for log in compliance_logs if log["timestamp"] <= end_dt]
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=get_error_response("VALIDATION_ERROR", "Invalid end_date format"),
            )

    # Aggregate statistics
    event_counts = {}
    for log in compliance_logs:
        event_type = log["event_type"]
        event_counts[event_type] = event_counts.get(event_type, 0) + 1

    unique_users = len(set(log["user_id"] for log in compliance_logs if log.get("user_id")))
    unique_sessions = len(
        set(log["session_id"] for log in compliance_logs if log.get("session_id"))
    )

    return {
        "compliance_framework": compliance_tag,
        "period": {"start": start_date or "all_time", "end": end_date or "now"},
        "statistics": {
            "total_events": len(compliance_logs),
            "unique_users": unique_users,
            "unique_sessions": unique_sessions,
            "events_by_type": event_counts,
        },
        "generated_at": datetime.now().isoformat(),
    }


@router.get(
    "/stats", summary="Get Audit Statistics", description="Get overall audit log statistics"
)
@limiter.limit("100/minute")
async def get_audit_stats(request: Request, api_key: Optional[str] = Depends(verify_api_key)):
    """
    Get overall audit log statistics.

    Provides high-level metrics about logged events.

    **Rate Limit**: 100 requests per minute

    **Returns**: Aggregate statistics
    """
    # Thread-safe access
    with _audit_logs_lock:
        logs_snapshot = audit_logs_db.copy()

    total_logs = len(logs_snapshot)

    if total_logs == 0:
        return {"total_logs": 0, "message": "No audit logs available"}

    # Count by event type
    event_type_counts = {}
    for log in logs_snapshot:
        event_type = log["event_type"]
        event_type_counts[event_type] = event_type_counts.get(event_type, 0) + 1

    # Count by compliance tag
    compliance_tag_counts = {}
    for log in logs_snapshot:
        for tag in log.get("compliance_tags", []):
            compliance_tag_counts[tag] = compliance_tag_counts.get(tag, 0) + 1

    # Get date range
    timestamps = [log["timestamp"] for log in logs_snapshot]
    oldest = min(timestamps)
    newest = max(timestamps)

    return {
        "total_logs": total_logs,
        "date_range": {"oldest": oldest.isoformat(), "newest": newest.isoformat()},
        "events_by_type": event_type_counts,
        "events_by_compliance_tag": compliance_tag_counts,
        "unique_users": len(set(log["user_id"] for log in logs_snapshot if log.get("user_id"))),
        "unique_sessions": len(
            set(log["session_id"] for log in logs_snapshot if log.get("session_id"))
        ),
    }


@router.delete(
    "/logs/purge",
    summary="Purge Old Logs",
    description="Purge audit logs older than specified date (admin only)",
)
@limiter.limit("5/minute")
async def purge_old_logs(
    request: Request,
    before_date: str = Query(..., description="ISO format datetime"),
    api_key: Optional[str] = Depends(verify_api_key),
):
    """
    Purge audit logs older than specified date.

    Use with caution - this is irreversible. Should only be used per data retention policies.

    **Rate Limit**: 5 requests per minute

    **Returns**: Number of logs purged
    """
    try:
        purge_dt = datetime.fromisoformat(before_date.replace("Z", "+00:00"))
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=get_error_response("VALIDATION_ERROR", "Invalid date format"),
        )

    global audit_logs_db

    # Thread-safe purge
    with _audit_logs_lock:
        original_count = len(audit_logs_db)
        # Keep only logs after purge date
        audit_logs_db = [log for log in audit_logs_db if log["timestamp"] >= purge_dt]
        purged_count = original_count - len(audit_logs_db)
        remaining_count = len(audit_logs_db)

    logger.warning(f"Audit log purge: {purged_count} logs deleted (before {before_date})")

    return {
        "status": "success",
        "purged_count": purged_count,
        "remaining_count": remaining_count,
        "purge_date": before_date,
        "executed_at": datetime.now().isoformat(),
    }
