"""
Session Management API
Handles onboarding sessions, linking biometric and audio samples with unique session IDs
"""

from fastapi import APIRouter, HTTPException, Request, Depends, status
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import uuid
import logging

from api.middleware import limiter, verify_api_key, get_error_response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/session", tags=["session"])


class SessionStatus(str, Enum):
    """Session status enumeration"""
    INITIATED = "initiated"
    IN_PROGRESS = "in_progress"
    BIOMETRIC_COMPLETE = "biometric_complete"
    VOICE_COMPLETE = "voice_complete"
    COMPLETE = "complete"
    ESCALATED = "escalated"
    APPROVED = "approved"
    DECLINED = "declined"


class SessionType(str, Enum):
    """Session type enumeration"""
    ONBOARDING = "onboarding"
    AUTHENTICATION = "authentication"
    TRANSACTION = "transaction"


class SessionRequest(BaseModel):
    """Request to start a new session"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": "USER-12345",
                "session_type": "onboarding",
                "metadata": {
                    "channel": "mobile_app",
                    "ip_address": "masked_ip_xxx"
                }
            }
        }
    )
    
    user_id: str = Field(..., description="User identifier (privacy-masked)")
    session_type: SessionType = Field(default=SessionType.ONBOARDING, description="Type of session")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional session metadata")


class SessionResponse(BaseModel):
    """Session response with details"""
    session_id: str = Field(..., description="Unique session identifier")
    user_id: str = Field(..., description="User identifier (privacy-masked)")
    session_type: SessionType
    status: SessionStatus
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BiometricDataUpdate(BaseModel):
    """Update session with biometric data from Incode"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "document_verified": True,
                "face_match_score": 0.95,
                "liveness_passed": True,
                "incode_session_id": "incode-xxx-yyy"
            }
        }
    )
    
    document_verified: bool = Field(..., description="Document verification result")
    face_match_score: float = Field(..., ge=0, le=1, description="Face match confidence score")
    liveness_passed: bool = Field(..., description="Liveness check result")
    incode_session_id: str = Field(..., description="Incode's session identifier")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class VoiceDataUpdate(BaseModel):
    """Update session with voice/audio data from Sonotheia"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "deepfake_score": 0.15,
                "speaker_verified": True,
                "speaker_score": 0.96,
                "audio_quality": 0.85,
                "audio_duration_seconds": 4.5
            }
        }
    )
    
    deepfake_score: float = Field(..., ge=0, le=1, description="Deepfake detection score")
    speaker_verified: bool = Field(..., description="Speaker verification result")
    speaker_score: float = Field(..., ge=0, le=1, description="Speaker match confidence")
    audio_quality: float = Field(..., ge=0, le=1, description="Audio quality score")
    audio_duration_seconds: float = Field(..., gt=0, description="Audio sample duration")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class RiskEvaluationRequest(BaseModel):
    """Request to evaluate composite risk for a session"""
    session_id: str = Field(..., description="Session identifier")
    include_factors: bool = Field(default=True, description="Include detailed factor breakdown")


class RiskEvaluationResponse(BaseModel):
    """Response with composite risk evaluation"""
    session_id: str
    composite_risk_score: float = Field(..., ge=0, le=1, description="Overall risk score")
    risk_level: str = Field(..., description="LOW, MEDIUM, HIGH, or CRITICAL")
    biometric_risk: float = Field(..., ge=0, le=1)
    voice_risk: float = Field(..., ge=0, le=1)
    factors: List[Dict[str, Any]] = Field(default_factory=list)
    decision: str = Field(..., description="APPROVE, DECLINE, or ESCALATE")
    reason: str = Field(..., description="Explanation for decision")
    updated_at: datetime


# In-memory session storage (replace with database in production)
sessions_db: Dict[str, Dict[str, Any]] = {}


@router.post(
    "/start",
    response_model=SessionResponse,
    summary="Start New Session",
    description="Initialize a new onboarding or authentication session"
)
@limiter.limit("100/minute")
async def start_session(
    request: Request,
    session_request: SessionRequest,
    api_key: Optional[str] = Depends(verify_api_key)
):
    """
    Start a new session for onboarding or authentication.
    
    Creates a unique session ID that will be used to link biometric data
    from Incode and audio data from Sonotheia.
    
    **Rate Limit**: 100 requests per minute
    
    **Returns**: Session details with unique session_id
    """
    try:
        # Generate unique session ID
        session_id = f"SESSION-{uuid.uuid4().hex[:16].upper()}"
        
        now = datetime.now()
        session_data = {
            "session_id": session_id,
            "user_id": session_request.user_id,
            "session_type": session_request.session_type,
            "status": SessionStatus.INITIATED,
            "created_at": now,
            "updated_at": now,
            "metadata": session_request.metadata or {},
            "biometric_data": None,
            "voice_data": None,
            "risk_evaluation": None
        }
        
        # Store session
        sessions_db[session_id] = session_data
        
        logger.info(f"Session started: {session_id} for user {session_request.user_id}")
        
        return SessionResponse(**session_data)
        
    except Exception as e:
        logger.error(f"Error starting session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=get_error_response("PROCESSING_ERROR", "Failed to start session")
        )


@router.get(
    "/{session_id}",
    response_model=SessionResponse,
    summary="Get Session Details",
    description="Retrieve details of a specific session"
)
@limiter.limit("100/minute")
async def get_session(
    request: Request,
    session_id: str,
    api_key: Optional[str] = Depends(verify_api_key)
):
    """
    Get details of a specific session.
    
    **Rate Limit**: 100 requests per minute
    
    **Returns**: Complete session information
    """
    if session_id not in sessions_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=get_error_response("NOT_FOUND", f"Session {session_id} not found")
        )
    
    session_data = sessions_db[session_id]
    return SessionResponse(**session_data)


@router.post(
    "/{session_id}/biometric",
    response_model=SessionResponse,
    summary="Update Biometric Data",
    description="Update session with biometric data from Incode"
)
@limiter.limit("100/minute")
async def update_biometric_data(
    request: Request,
    session_id: str,
    biometric_data: BiometricDataUpdate,
    api_key: Optional[str] = Depends(verify_api_key)
):
    """
    Update session with biometric data from Incode SDK.
    
    Stores document verification, face matching, and liveness results.
    
    **Rate Limit**: 100 requests per minute
    
    **Returns**: Updated session information
    """
    if session_id not in sessions_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=get_error_response("NOT_FOUND", f"Session {session_id} not found")
        )
    
    session = sessions_db[session_id]
    session["biometric_data"] = biometric_data.model_dump()
    session["updated_at"] = datetime.now()
    
    # Update status
    if session["voice_data"] is not None:
        session["status"] = SessionStatus.COMPLETE
    else:
        session["status"] = SessionStatus.BIOMETRIC_COMPLETE
    
    logger.info(f"Biometric data updated for session {session_id}")
    
    return SessionResponse(**session)


@router.post(
    "/{session_id}/voice",
    response_model=SessionResponse,
    summary="Update Voice Data",
    description="Update session with voice/audio data from Sonotheia"
)
@limiter.limit("100/minute")
async def update_voice_data(
    request: Request,
    session_id: str,
    voice_data: VoiceDataUpdate,
    api_key: Optional[str] = Depends(verify_api_key)
):
    """
    Update session with voice data from Sonotheia SDK.
    
    Stores deepfake detection, speaker verification, and audio quality results.
    
    **Rate Limit**: 100 requests per minute
    
    **Returns**: Updated session information
    """
    if session_id not in sessions_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=get_error_response("NOT_FOUND", f"Session {session_id} not found")
        )
    
    session = sessions_db[session_id]
    session["voice_data"] = voice_data.model_dump()
    session["updated_at"] = datetime.now()
    
    # Update status
    if session["biometric_data"] is not None:
        session["status"] = SessionStatus.COMPLETE
    else:
        session["status"] = SessionStatus.VOICE_COMPLETE
    
    logger.info(f"Voice data updated for session {session_id}")
    
    return SessionResponse(**session)


@router.post(
    "/{session_id}/evaluate",
    response_model=RiskEvaluationResponse,
    summary="Evaluate Composite Risk",
    description="Calculate composite risk score from biometric and voice data"
)
@limiter.limit("50/minute")
async def evaluate_session_risk(
    request: Request,
    session_id: str,
    evaluation_request: RiskEvaluationRequest,
    api_key: Optional[str] = Depends(verify_api_key)
):
    """
    Evaluate composite risk for a session.
    
    Combines biometric risk (from Incode) and voice risk (from Sonotheia)
    to produce an overall risk assessment.
    
    **Rate Limit**: 50 requests per minute
    
    **Returns**: Risk evaluation with decision recommendation
    """
    if session_id not in sessions_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=get_error_response("NOT_FOUND", f"Session {session_id} not found")
        )
    
    session = sessions_db[session_id]
    
    # Check if both biometric and voice data are available
    if not session.get("biometric_data") or not session.get("voice_data"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=get_error_response(
                "INCOMPLETE_DATA",
                "Both biometric and voice data are required for risk evaluation"
            )
        )
    
    biometric = session["biometric_data"]
    voice = session["voice_data"]
    
    # Calculate risk scores
    # Biometric risk: higher if face match is low, liveness failed, or doc not verified
    biometric_risk = 0.0
    if not biometric["document_verified"]:
        biometric_risk += 0.4
    if not biometric["liveness_passed"]:
        biometric_risk += 0.3
    if biometric["face_match_score"] < 0.8:
        biometric_risk += (1.0 - biometric["face_match_score"]) * 0.3
    
    # Voice risk: based on deepfake score and speaker verification
    voice_risk = voice["deepfake_score"]
    if not voice["speaker_verified"]:
        voice_risk += 0.2
    if voice["speaker_score"] < 0.8:
        voice_risk += (1.0 - voice["speaker_score"]) * 0.2
    
    # Normalize risks
    biometric_risk = min(biometric_risk, 1.0)
    voice_risk = min(voice_risk, 1.0)
    
    # Composite risk (weighted average)
    composite_risk = (biometric_risk * 0.5) + (voice_risk * 0.5)
    
    # Determine risk level
    if composite_risk < 0.3:
        risk_level = "LOW"
        decision = "APPROVE"
    elif composite_risk < 0.5:
        risk_level = "MEDIUM"
        decision = "APPROVE"
    elif composite_risk < 0.7:
        risk_level = "HIGH"
        decision = "ESCALATE"
    else:
        risk_level = "CRITICAL"
        decision = "ESCALATE"
    
    # Build factors list
    factors = []
    if evaluation_request.include_factors:
        factors.extend([
            {
                "name": "Document Verification",
                "passed": biometric["document_verified"],
                "weight": 0.4
            },
            {
                "name": "Face Match",
                "score": biometric["face_match_score"],
                "weight": 0.3
            },
            {
                "name": "Liveness Check",
                "passed": biometric["liveness_passed"],
                "weight": 0.3
            },
            {
                "name": "Deepfake Detection",
                "score": voice["deepfake_score"],
                "weight": 0.4
            },
            {
                "name": "Speaker Verification",
                "passed": voice["speaker_verified"],
                "score": voice["speaker_score"],
                "weight": 0.3
            },
            {
                "name": "Audio Quality",
                "score": voice["audio_quality"],
                "weight": 0.1
            }
        ])
    
    # Determine reason
    if decision == "APPROVE":
        reason = "All biometric and voice factors passed with acceptable scores"
    else:
        issues = []
        if not biometric["document_verified"]:
            issues.append("document verification failed")
        if not biometric["liveness_passed"]:
            issues.append("liveness check failed")
        if biometric["face_match_score"] < 0.8:
            issues.append("low face match score")
        if voice["deepfake_score"] > 0.3:
            issues.append("high deepfake score")
        if not voice["speaker_verified"]:
            issues.append("speaker verification failed")
        reason = f"Escalation required due to: {', '.join(issues)}"
    
    # Store risk evaluation
    risk_evaluation = {
        "composite_risk_score": composite_risk,
        "risk_level": risk_level,
        "biometric_risk": biometric_risk,
        "voice_risk": voice_risk,
        "factors": factors,
        "decision": decision,
        "reason": reason,
        "updated_at": datetime.now()
    }
    
    session["risk_evaluation"] = risk_evaluation
    
    # Update session status based on decision
    if decision == "APPROVE":
        session["status"] = SessionStatus.APPROVED
    elif decision == "ESCALATE":
        session["status"] = SessionStatus.ESCALATED
    else:
        session["status"] = SessionStatus.DECLINED
    
    logger.info(f"Risk evaluation completed for session {session_id}: {decision} ({risk_level})")
    
    return RiskEvaluationResponse(
        session_id=session_id,
        **risk_evaluation
    )


@router.get(
    "/",
    response_model=List[SessionResponse],
    summary="List Sessions",
    description="List all sessions with optional filtering"
)
@limiter.limit("100/minute")
async def list_sessions(
    request: Request,
    status: Optional[SessionStatus] = None,
    session_type: Optional[SessionType] = None,
    api_key: Optional[str] = Depends(verify_api_key)
):
    """
    List all sessions with optional filtering.
    
    **Rate Limit**: 100 requests per minute
    
    **Parameters**:
    - `status`: Filter by session status
    - `session_type`: Filter by session type
    
    **Returns**: List of sessions
    """
    sessions = list(sessions_db.values())
    
    if status:
        sessions = [s for s in sessions if s["status"] == status]
    
    if session_type:
        sessions = [s for s in sessions if s["session_type"] == session_type]
    
    return [SessionResponse(**s) for s in sessions]
