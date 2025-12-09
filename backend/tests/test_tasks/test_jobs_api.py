"""
Tests for Jobs API Endpoints
Tests async job submission, status, results, and cancellation.
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path
import base64

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from api.main import app

# Create test client
client = TestClient(app)


class TestJobsAPIModels:
    """Test jobs API request/response models."""
    
    def test_async_analysis_request_validation(self):
        """Test request validation for async analysis."""
        # Missing required fields should fail
        response = client.post("/api/analyze/async", json={})
        assert response.status_code == 422
        
    def test_async_analysis_requires_audio_data(self):
        """Test that audio_data_base64 is required."""
        request_data = {
            "call_id": "CALL-001",
            "customer_id": "CUST-001"
        }
        response = client.post("/api/analyze/async", json=request_data)
        assert response.status_code == 422
        
    def test_async_analysis_requires_call_id(self):
        """Test that call_id is required."""
        request_data = {
            "audio_data_base64": base64.b64encode(b"test").decode(),
            "customer_id": "CUST-001"
        }
        response = client.post("/api/analyze/async", json=request_data)
        assert response.status_code == 422


class TestJobsEndpointAvailability:
    """Test that jobs endpoints are available."""
    
    def test_jobs_list_endpoint_exists(self):
        """Test jobs list endpoint returns response."""
        response = client.get("/api/jobs")
        # Should return 200 with info about endpoints
        assert response.status_code == 200
        data = response.json()
        assert "endpoints" in data
        
    def test_job_status_endpoint_exists(self):
        """Test job status endpoint accepts job_id."""
        # Should handle non-existent job gracefully
        response = client.get("/api/jobs/nonexistent-job-id")
        # Will return 200 with PENDING status (Celery behavior for unknown tasks)
        # or 503 if Celery is not available
        assert response.status_code in [200, 503]
        
    def test_job_result_endpoint_exists(self):
        """Test job result endpoint accepts job_id."""
        response = client.get("/api/jobs/nonexistent-job-id/result")
        assert response.status_code in [200, 503]
        
    def test_job_cancel_endpoint_exists(self):
        """Test job cancel endpoint accepts DELETE."""
        response = client.delete("/api/jobs/nonexistent-job-id")
        assert response.status_code in [200, 503]


class TestJobSubmissionValidation:
    """Test job submission input validation."""
    
    def test_rejects_invalid_base64(self):
        """Test that invalid base64 is rejected."""
        request_data = {
            "audio_data_base64": "not-valid-base64!!!",
            "call_id": "CALL-001",
            "customer_id": "CUST-001"
        }
        response = client.post("/api/analyze/async", json=request_data)
        # Should fail with validation error or service unavailable
        assert response.status_code in [422, 503]
    
    def test_rejects_oversized_audio(self):
        """Test that oversized audio is rejected."""
        # Create base64 data larger than 15MB limit
        large_data = base64.b64encode(b'\x00' * (16 * 1024 * 1024)).decode()
        request_data = {
            "audio_data_base64": large_data,
            "call_id": "CALL-001",
            "customer_id": "CUST-001"
        }
        response = client.post("/api/analyze/async", json=request_data)
        # Should fail with payload too large or service unavailable
        assert response.status_code in [413, 503]


class TestRequestHeaders:
    """Test that jobs endpoints follow API conventions."""
    
    def test_jobs_list_has_request_id(self):
        """Test jobs list includes request ID header."""
        response = client.get("/api/jobs")
        assert "x-request-id" in response.headers
        
    def test_jobs_list_has_response_time(self):
        """Test jobs list includes response time header."""
        response = client.get("/api/jobs")
        assert "x-response-time" in response.headers


class TestJobStatusResponse:
    """Test job status response format."""
    
    def test_status_response_has_job_id(self):
        """Test status response includes job_id."""
        response = client.get("/api/jobs/test-job-123")
        if response.status_code == 200:
            data = response.json()
            assert "job_id" in data
            assert data["job_id"] == "test-job-123"
    
    def test_status_response_has_status_field(self):
        """Test status response includes status field."""
        response = client.get("/api/jobs/test-job-456")
        if response.status_code == 200:
            data = response.json()
            assert "status" in data


class TestJobResultResponse:
    """Test job result response format."""
    
    def test_result_response_has_job_id(self):
        """Test result response includes job_id."""
        response = client.get("/api/jobs/test-job-789/result")
        if response.status_code == 200:
            data = response.json()
            assert "job_id" in data
    
    def test_pending_job_returns_appropriate_message(self):
        """Test pending job returns informative message."""
        response = client.get("/api/jobs/new-job-id/result")
        if response.status_code == 200:
            data = response.json()
            # Should indicate job not complete
            assert data.get("status") in ["PENDING", "STARTED", "PROCESSING"] or "error" in data


class TestJobCancellationResponse:
    """Test job cancellation response format."""
    
    def test_cancel_response_has_job_id(self):
        """Test cancel response includes job_id."""
        response = client.delete("/api/jobs/cancel-test-job")
        if response.status_code == 200:
            data = response.json()
            assert "job_id" in data
    
    def test_cancel_response_has_cancelled_field(self):
        """Test cancel response includes cancelled field."""
        response = client.delete("/api/jobs/cancel-test-job")
        if response.status_code == 200:
            data = response.json()
            assert "cancelled" in data


class TestJobsListResponse:
    """Test jobs list response format."""
    
    def test_list_response_provides_endpoints(self):
        """Test list response provides useful endpoint info."""
        response = client.get("/api/jobs")
        assert response.status_code == 200
        data = response.json()
        
        # Should provide endpoint documentation
        assert "endpoints" in data
        endpoints = data["endpoints"]
        assert "submit" in endpoints
        assert "status" in endpoints
        assert "result" in endpoints
        assert "cancel" in endpoints


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
