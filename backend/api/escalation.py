"""
Human-in-the-Loop Escalation API
Provides endpoints for manual review and escalation workflow management
"""

from fastapi import APIRouter, HTTPException, Request, Depends, status, Query
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import logging

from api.middleware import limiter, verify_api_key, get_error_response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/escalation", tags=["escalation"])


class EscalationPriority(str, Enum):
    """Escalation priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EscalationStatus(str, Enum):
    """Escalation status enumeration"""
    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    DECLINED = "declined"
    NEEDS_INFO = "needs_info"


class ReviewDecision(str, Enum):
    """Reviewer decision options"""
    APPROVE = "approve"
    DECLINE = "decline"
    REQUEST_INFO = "request_info"
    ESCALATE_FURTHER = "escalate_further"


class EscalationRequest(BaseModel):
    """Request to escalate a session for manual review"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "session_id": "SESSION-ABC123",
                "reason": "High deepfake score detected",
                "priority": "high",
                "risk_score": 0.75,
                "details": {
                    "deepfake_score": 0.72,
                    "face_match_score": 0.88
                }
            }
        }
    )
    
    session_id: str = Field(..., description="Session identifier to escalate")
    reason: str = Field(..., description="Reason for escalation")
    priority: EscalationPriority = Field(default=EscalationPriority.MEDIUM)
    risk_score: float = Field(..., ge=0, le=1, description="Computed risk score")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional details")


class EscalationResponse(BaseModel):
    """Escalation record response"""
    escalation_id: str = Field(..., description="Unique escalation identifier")
    session_id: str
    reason: str
    priority: EscalationPriority
    status: EscalationStatus
    risk_score: float
    details: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    assigned_to: Optional[str] = Field(None, description="Reviewer assigned to this case")
    reviewed_at: Optional[datetime] = None
    reviewer_notes: Optional[str] = None
    decision: Optional[ReviewDecision] = None


class ReviewSubmission(BaseModel):
    """Reviewer's decision submission"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "decision": "approve",
                "notes": "After manual review, all documents appear legitimate",
                "reviewer_id": "REVIEWER-001"
            }
        }
    )
    
    decision: ReviewDecision = Field(..., description="Reviewer's decision")
    notes: str = Field(..., description="Reviewer's notes and reasoning")
    reviewer_id: str = Field(..., description="Identifier of the reviewer")
    additional_data: Optional[Dict[str, Any]] = Field(default_factory=dict)


class EscalationListFilter(BaseModel):
    """Filters for listing escalations"""
    status: Optional[EscalationStatus] = None
    priority: Optional[EscalationPriority] = None
    assigned_to: Optional[str] = None


# In-memory escalation storage (replace with database in production)
escalations_db: Dict[str, Dict[str, Any]] = {}
escalation_counter = 0


@router.post(
    "/create",
    response_model=EscalationResponse,
    summary="Create Escalation",
    description="Escalate a session for human review"
)
@limiter.limit("50/minute")
async def create_escalation(
    request: Request,
    escalation_request: EscalationRequest,
    api_key: Optional[str] = Depends(verify_api_key)
):
    """
    Create a new escalation for manual review.
    
    Flagged sessions are surfaced to human reviewers for manual assessment.
    
    **Rate Limit**: 50 requests per minute
    
    **Returns**: Escalation record with unique ID
    """
    global escalation_counter
    
    try:
        escalation_counter += 1
        escalation_id = f"ESC-{escalation_counter:06d}"
        
        now = datetime.now()
        escalation_data = {
            "escalation_id": escalation_id,
            "session_id": escalation_request.session_id,
            "reason": escalation_request.reason,
            "priority": escalation_request.priority,
            "status": EscalationStatus.PENDING,
            "risk_score": escalation_request.risk_score,
            "details": escalation_request.details,
            "created_at": now,
            "updated_at": now,
            "assigned_to": None,
            "reviewed_at": None,
            "reviewer_notes": None,
            "decision": None
        }
        
        escalations_db[escalation_id] = escalation_data
        
        logger.info(
            f"Escalation created: {escalation_id} for session {escalation_request.session_id} "
            f"with priority {escalation_request.priority}"
        )
        
        return EscalationResponse(**escalation_data)
        
    except Exception as e:
        logger.error(f"Error creating escalation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=get_error_response("PROCESSING_ERROR", "Failed to create escalation")
        )


@router.get(
    "/{escalation_id}",
    response_model=EscalationResponse,
    summary="Get Escalation Details",
    description="Retrieve details of a specific escalation"
)
@limiter.limit("100/minute")
async def get_escalation(
    request: Request,
    escalation_id: str,
    api_key: Optional[str] = Depends(verify_api_key)
):
    """
    Get details of a specific escalation.
    
    **Rate Limit**: 100 requests per minute
    
    **Returns**: Complete escalation information
    """
    if escalation_id not in escalations_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=get_error_response("NOT_FOUND", f"Escalation {escalation_id} not found")
        )
    
    escalation_data = escalations_db[escalation_id]
    return EscalationResponse(**escalation_data)


@router.get(
    "/",
    response_model=List[EscalationResponse],
    summary="List Escalations",
    description="List all escalations with optional filtering"
)
@limiter.limit("100/minute")
async def list_escalations(
    request: Request,
    status_filter: Optional[EscalationStatus] = Query(None, alias="status"),
    priority: Optional[EscalationPriority] = None,
    assigned_to: Optional[str] = None,
    api_key: Optional[str] = Depends(verify_api_key)
):
    """
    List all escalations with optional filtering.
    
    Use this endpoint to retrieve escalations that need manual review.
    
    **Rate Limit**: 100 requests per minute
    
    **Parameters**:
    - `status`: Filter by escalation status
    - `priority`: Filter by priority level
    - `assigned_to`: Filter by assigned reviewer
    
    **Returns**: List of escalations
    """
    escalations = list(escalations_db.values())
    
    if status_filter:
        escalations = [e for e in escalations if e["status"] == status_filter]
    
    if priority:
        escalations = [e for e in escalations if e["priority"] == priority]
    
    if assigned_to:
        escalations = [e for e in escalations if e["assigned_to"] == assigned_to]
    
    # Sort by priority and creation date
    priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    escalations.sort(
        key=lambda e: (priority_order.get(e["priority"], 4), e["created_at"]),
        reverse=True
    )
    
    return [EscalationResponse(**e) for e in escalations]


@router.post(
    "/{escalation_id}/assign",
    response_model=EscalationResponse,
    summary="Assign Escalation",
    description="Assign an escalation to a reviewer"
)
@limiter.limit("100/minute")
async def assign_escalation(
    request: Request,
    escalation_id: str,
    reviewer_id: str = Query(..., description="Reviewer identifier"),
    api_key: Optional[str] = Depends(verify_api_key)
):
    """
    Assign an escalation to a specific reviewer.
    
    **Rate Limit**: 100 requests per minute
    
    **Returns**: Updated escalation information
    """
    if escalation_id not in escalations_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=get_error_response("NOT_FOUND", f"Escalation {escalation_id} not found")
        )
    
    escalation = escalations_db[escalation_id]
    escalation["assigned_to"] = reviewer_id
    escalation["status"] = EscalationStatus.IN_REVIEW
    escalation["updated_at"] = datetime.now()
    
    logger.info(f"Escalation {escalation_id} assigned to {reviewer_id}")
    
    return EscalationResponse(**escalation)


@router.post(
    "/{escalation_id}/review",
    response_model=EscalationResponse,
    summary="Submit Review Decision",
    description="Submit a reviewer's decision for an escalation"
)
@limiter.limit("50/minute")
async def submit_review(
    request: Request,
    escalation_id: str,
    review: ReviewSubmission,
    api_key: Optional[str] = Depends(verify_api_key)
):
    """
    Submit a manual review decision for an escalation.
    
    This endpoint allows reviewers to make final decisions on escalated cases.
    
    **Rate Limit**: 50 requests per minute
    
    **Returns**: Updated escalation with review decision
    """
    if escalation_id not in escalations_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=get_error_response("NOT_FOUND", f"Escalation {escalation_id} not found")
        )
    
    escalation = escalations_db[escalation_id]
    
    # Update escalation with review decision
    escalation["decision"] = review.decision
    escalation["reviewer_notes"] = review.notes
    escalation["assigned_to"] = review.reviewer_id
    escalation["reviewed_at"] = datetime.now()
    escalation["updated_at"] = datetime.now()
    
    # Update status based on decision
    if review.decision == ReviewDecision.APPROVE:
        escalation["status"] = EscalationStatus.APPROVED
    elif review.decision == ReviewDecision.DECLINE:
        escalation["status"] = EscalationStatus.DECLINED
    elif review.decision == ReviewDecision.REQUEST_INFO:
        escalation["status"] = EscalationStatus.NEEDS_INFO
    elif review.decision == ReviewDecision.ESCALATE_FURTHER:
        # Keep in review but increase priority
        escalation["status"] = EscalationStatus.IN_REVIEW
        if escalation["priority"] == EscalationPriority.MEDIUM:
            escalation["priority"] = EscalationPriority.HIGH
        elif escalation["priority"] == EscalationPriority.HIGH:
            escalation["priority"] = EscalationPriority.CRITICAL
    
    logger.info(
        f"Review submitted for escalation {escalation_id}: "
        f"{review.decision} by {review.reviewer_id}"
    )
    
    return EscalationResponse(**escalation)


@router.get(
    "/pending/count",
    summary="Get Pending Count",
    description="Get count of pending escalations by priority"
)
@limiter.limit("100/minute")
async def get_pending_count(
    request: Request,
    api_key: Optional[str] = Depends(verify_api_key)
):
    """
    Get count of pending escalations grouped by priority.
    
    Useful for dashboard displays and alerts.
    
    **Rate Limit**: 100 requests per minute
    
    **Returns**: Count of pending escalations by priority
    """
    pending_escalations = [
        e for e in escalations_db.values()
        if e["status"] in [EscalationStatus.PENDING, EscalationStatus.IN_REVIEW]
    ]
    
    counts = {
        "total": len(pending_escalations),
        "by_priority": {
            "critical": len([e for e in pending_escalations if e["priority"] == EscalationPriority.CRITICAL]),
            "high": len([e for e in pending_escalations if e["priority"] == EscalationPriority.HIGH]),
            "medium": len([e for e in pending_escalations if e["priority"] == EscalationPriority.MEDIUM]),
            "low": len([e for e in pending_escalations if e["priority"] == EscalationPriority.LOW])
        },
        "by_status": {
            "pending": len([e for e in pending_escalations if e["status"] == EscalationStatus.PENDING]),
            "in_review": len([e for e in pending_escalations if e["status"] == EscalationStatus.IN_REVIEW])
        }
    }
    
    return counts


@router.delete(
    "/{escalation_id}",
    summary="Delete Escalation",
    description="Delete an escalation record (admin only)"
)
@limiter.limit("20/minute")
async def delete_escalation(
    request: Request,
    escalation_id: str,
    api_key: Optional[str] = Depends(verify_api_key)
):
    """
    Delete an escalation record.
    
    This should only be used in exceptional circumstances.
    
    **Rate Limit**: 20 requests per minute
    
    **Returns**: Confirmation message
    """
    if escalation_id not in escalations_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=get_error_response("NOT_FOUND", f"Escalation {escalation_id} not found")
        )
    
    del escalations_db[escalation_id]
    
    logger.warning(f"Escalation {escalation_id} deleted")
    
    return {
        "status": "success",
        "message": f"Escalation {escalation_id} deleted",
        "deleted_at": datetime.now().isoformat()
    }
