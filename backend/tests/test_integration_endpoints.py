"""
Tests for new Session Management, Escalation, and Audit Logging APIs
Tests the integration endpoints added for Sonotheia x Incode
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add parent to path
sys.path.append(str(Path(__file__).parent.parent))

from api.main import app

# Create test client
client = TestClient(app)


class TestSessionManagement:
    """Test session management endpoints"""

    def _start_session(self):
        """Helper: start session and return session_id"""
        request_data = {
            "user_id": "USER-TEST-001",
            "session_type": "onboarding",
            "metadata": {
                "channel": "mobile_app",
                "ip_address": "masked_ip_xxx"
            }
        }
        response = client.post("/api/session/start", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert data["session_id"].startswith("SESSION-")
        assert data["user_id"] == "USER-TEST-001"
        assert data["session_type"] == "onboarding"
        assert data["status"] == "initiated"
        return data["session_id"]

    def test_start_session(self):
        """Test starting a new onboarding session"""
        session_id = self._start_session()
        assert session_id.startswith("SESSION-")
    
    def test_get_session(self):
        """Test retrieving session details"""
        # First create a session
        session_id = self._start_session()
        
        # Then retrieve it
        response = client.get(f"/api/session/{session_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == session_id
        assert data["status"] == "initiated"
    
    def test_update_biometric_data(self):
        """Test updating session with Incode biometric data"""
        # Create session first
        session_id = self._start_session()
        
        # Update with biometric data
        biometric_data = {
            "document_verified": True,
            "face_match_score": 0.95,
            "liveness_passed": True,
            "incode_session_id": "incode-test-123"
        }
        response = client.post(
            f"/api/session/{session_id}/biometric",
            json=biometric_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["biometric_complete", "complete"]
        
    def test_update_voice_data(self):
        """Test updating session with Sonotheia voice data"""
        # Create session first
        session_id = self._start_session()
        
        # Update with voice data
        voice_data = {
            "deepfake_score": 0.15,
            "speaker_verified": True,
            "speaker_score": 0.96,
            "audio_quality": 0.85,
            "audio_duration_seconds": 4.5
        }
        response = client.post(
            f"/api/session/{session_id}/voice",
            json=voice_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["voice_complete", "complete"]
    
    def test_evaluate_session_risk(self):
        """Test composite risk evaluation"""
        # Create session and add both biometric and voice data
        session_id = self._start_session()
        
        # Add biometric data
        biometric_data = {
            "document_verified": True,
            "face_match_score": 0.95,
            "liveness_passed": True,
            "incode_session_id": "incode-test-123"
        }
        client.post(f"/api/session/{session_id}/biometric", json=biometric_data)
        
        # Add voice data
        voice_data = {
            "deepfake_score": 0.15,
            "speaker_verified": True,
            "speaker_score": 0.96,
            "audio_quality": 0.85,
            "audio_duration_seconds": 4.5
        }
        client.post(f"/api/session/{session_id}/voice", json=voice_data)
        
        # Evaluate risk
        response = client.post(
            f"/api/session/{session_id}/evaluate",
            json={"session_id": session_id, "include_factors": True}
        )
        assert response.status_code == 200
        data = response.json()
        assert "composite_risk_score" in data
        assert "risk_level" in data
        assert "biometric_risk" in data
        assert "voice_risk" in data
        assert "decision" in data
        assert "factors" in data
        assert data["decision"] in ["APPROVE", "DECLINE", "ESCALATE"]
        assert 0 <= data["composite_risk_score"] <= 1
    
    def test_list_sessions(self):
        """Test listing sessions"""
        # Create a few sessions
        self._start_session()
        
        # List all sessions
        response = client.get("/api/session/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
    
    def test_session_not_found(self):
        """Test error when session doesn't exist"""
        response = client.get("/api/session/NONEXISTENT-SESSION")
        assert response.status_code == 404


class TestEscalationAPI:
    """Test escalation and human review endpoints"""

    def _create_escalation(self):
        """Helper: create escalation and return id"""
        escalation_data = {
            "session_id": "SESSION-TEST-001",
            "reason": "High deepfake score detected",
            "priority": "high",
            "risk_score": 0.75,
            "details": {
                "deepfake_score": 0.72,
                "face_match_score": 0.88
            }
        }
        response = client.post("/api/escalation/create", json=escalation_data)
        assert response.status_code == 200
        data = response.json()
        assert "escalation_id" in data
        assert data["escalation_id"].startswith("ESC-")
        assert data["session_id"] == "SESSION-TEST-001"
        assert data["status"] == "pending"
        assert data["priority"] == "high"
        return data["escalation_id"]

    def test_create_escalation(self):
        """Test creating an escalation for manual review"""
        escalation_id = self._create_escalation()
        assert escalation_id.startswith("ESC-")
    
    def test_get_escalation(self):
        """Test retrieving escalation details"""
        # Create escalation first
        escalation_id = self._create_escalation()
        
        # Retrieve it
        response = client.get(f"/api/escalation/{escalation_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["escalation_id"] == escalation_id
    
    def test_list_escalations(self):
        """Test listing escalations with filtering"""
        # Create an escalation
        self._create_escalation()
        
        # List all
        response = client.get("/api/escalation/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        
        # List with filter
        response = client.get("/api/escalation/?status=pending")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_assign_escalation(self):
        """Test assigning escalation to reviewer"""
        escalation_id = self._create_escalation()
        
        response = client.post(
            f"/api/escalation/{escalation_id}/assign",
            params={"reviewer_id": "REVIEWER-001"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["assigned_to"] == "REVIEWER-001"
        assert data["status"] == "in_review"
    
    def test_submit_review(self):
        """Test submitting a review decision"""
        escalation_id = self._create_escalation()
        
        review_data = {
            "decision": "approve",
            "notes": "After manual review, all documents appear legitimate",
            "reviewer_id": "REVIEWER-001"
        }
        response = client.post(
            f"/api/escalation/{escalation_id}/review",
            json=review_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["decision"] == "approve"
        assert data["status"] == "approved"
        assert data["reviewer_notes"] == review_data["notes"]
    
    def test_get_pending_count(self):
        """Test getting pending escalation counts"""
        response = client.get("/api/escalation/pending/count")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "by_priority" in data
        assert "by_status" in data


class TestAuditLogging:
    """Test audit logging and compliance endpoints"""

    def _create_audit_log(self):
        """Helper: create audit log and return id"""
        log_data = {
            "event_type": "session_started",
            "user_id": "USER-MASKED-123",
            "session_id": "SESSION-ABC123",
            "score": 0.25,
            "metadata": {
                "decision": "approve",
                "risk_level": "low"
            },
            "compliance_tags": ["kyc", "aml"],
            "ip_address": "masked_ip_xxx",
            "user_agent": "MobileApp/1.0"
        }
        response = client.post("/api/audit/log", json=log_data)
        assert response.status_code == 200
        data = response.json()
        assert "log_id" in data
        assert data["log_id"].startswith("LOG-")
        assert data["event_type"] == "session_started"
        return data["log_id"]

    def test_create_audit_log(self):
        """Test creating an audit log entry"""
        log_id = self._create_audit_log()
        assert log_id.startswith("LOG-")
    
    def test_query_audit_logs(self):
        """Test querying audit logs"""
        # Create a log first
        self._create_audit_log()
        
        # Query logs
        response = client.get("/api/audit/logs")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        
        # Query with filters
        response = client.get("/api/audit/logs?event_type=session_started")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_session_timeline(self):
        """Test getting session timeline"""
        session_id = "SESSION-TEST-TIMELINE"
        
        # Create some events for this session
        for event_type in ["session_started", "biometric_captured", "voice_captured"]:
            log_data = {
                "event_type": event_type,
                "user_id": "USER-001",
                "session_id": session_id,
                "compliance_tags": ["kyc"]
            }
            client.post("/api/audit/log", json=log_data)
        
        # Get timeline
        response = client.get(f"/api/audit/session/{session_id}/timeline")
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == session_id
        assert "events" in data
        assert len(data["events"]) >= 3
    
    def test_compliance_report(self):
        """Test generating compliance report"""
        # Create some logs with compliance tags
        log_data = {
            "event_type": "compliance_check",
            "user_id": "USER-001",
            "compliance_tags": ["kyc"],
            "metadata": {}
        }
        client.post("/api/audit/log", json=log_data)
        
        # Generate report
        response = client.get("/api/audit/compliance/report?compliance_tag=kyc")
        assert response.status_code == 200
        data = response.json()
        assert data["compliance_framework"] == "kyc"
        assert "statistics" in data
        assert "total_events" in data["statistics"]
    
    def test_audit_stats(self):
        """Test getting audit statistics"""
        response = client.get("/api/audit/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_logs" in data


class TestIntegrationFlow:
    """Test complete integration flow from start to finish"""
    
    def test_complete_onboarding_flow(self):
        """Test complete onboarding flow with all steps"""
        # Step 1: Start session
        session_response = client.post("/api/session/start", json={
            "user_id": "USER-INTEGRATION-001",
            "session_type": "onboarding",
            "metadata": {"channel": "mobile_app"}
        })
        assert session_response.status_code == 200
        session_id = session_response.json()["session_id"]
        
        # Step 2: Log session start
        audit_response = client.post("/api/audit/log", json={
            "event_type": "session_started",
            "user_id": "USER-INTEGRATION-001",
            "session_id": session_id,
            "compliance_tags": ["kyc", "aml"]
        })
        assert audit_response.status_code == 200
        
        # Step 3: Add biometric data (Incode)
        biometric_response = client.post(
            f"/api/session/{session_id}/biometric",
            json={
                "document_verified": True,
                "face_match_score": 0.92,
                "liveness_passed": True,
                "incode_session_id": "incode-integration-001"
            }
        )
        assert biometric_response.status_code == 200
        
        # Step 4: Log biometric capture
        client.post("/api/audit/log", json={
            "event_type": "biometric_captured",
            "user_id": "USER-INTEGRATION-001",
            "session_id": session_id,
            "compliance_tags": ["kyc"]
        })
        
        # Step 5: Add voice data (Sonotheia)
        voice_response = client.post(
            f"/api/session/{session_id}/voice",
            json={
                "deepfake_score": 0.18,
                "speaker_verified": True,
                "speaker_score": 0.94,
                "audio_quality": 0.87,
                "audio_duration_seconds": 5.2
            }
        )
        assert voice_response.status_code == 200
        
        # Step 6: Log voice capture
        client.post("/api/audit/log", json={
            "event_type": "voice_captured",
            "user_id": "USER-INTEGRATION-001",
            "session_id": session_id,
            "compliance_tags": ["aml"]
        })
        
        # Step 7: Evaluate risk
        risk_response = client.post(
            f"/api/session/{session_id}/evaluate",
            json={"session_id": session_id, "include_factors": True}
        )
        assert risk_response.status_code == 200
        risk_data = risk_response.json()
        
        # Step 8: Log risk evaluation
        client.post("/api/audit/log", json={
            "event_type": "risk_evaluated",
            "user_id": "USER-INTEGRATION-001",
            "session_id": session_id,
            "score": risk_data["composite_risk_score"],
            "metadata": {"decision": risk_data["decision"]},
            "compliance_tags": ["kyc", "aml"]
        })
        
        # Step 9: If high risk, create escalation
        if risk_data["decision"] == "ESCALATE":
            escalation_response = client.post("/api/escalation/create", json={
                "session_id": session_id,
                "reason": "Automated escalation due to risk threshold",
                "priority": "high",
                "risk_score": risk_data["composite_risk_score"],
                "details": risk_data
            })
            assert escalation_response.status_code == 200
        
        # Step 10: Verify session timeline
        timeline_response = client.get(f"/api/audit/session/{session_id}/timeline")
        assert timeline_response.status_code == 200
        timeline = timeline_response.json()
        assert len(timeline["events"]) >= 4  # Should have multiple events


class TestErrorHandlingNewEndpoints:
    """Test error handling for new endpoints"""
    
    def test_evaluate_risk_without_data(self):
        """Test evaluating risk without both biometric and voice data fails"""
        # Create session
        session_response = client.post("/api/session/start", json={
            "user_id": "USER-ERROR-001",
            "session_type": "onboarding"
        })
        session_id = session_response.json()["session_id"]
        
        # Try to evaluate without data
        response = client.post(
            f"/api/session/{session_id}/evaluate",
            json={"session_id": session_id}
        )
        assert response.status_code == 400
    
    def test_escalation_not_found(self):
        """Test error when escalation doesn't exist"""
        response = client.get("/api/escalation/NONEXISTENT-ESC")
        assert response.status_code == 404
    
    def test_invalid_compliance_tag(self):
        """Test handling of invalid compliance tag"""
        response = client.get("/api/audit/compliance/report?compliance_tag=invalid_tag")
        assert response.status_code == 422


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
