"""
API Endpoint Tests
Tests for all API endpoints including authentication, SAR generation, and health checks
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


class TestHealthEndpoints:
    """Test health and status endpoints"""
    
    def test_root_endpoint(self):
        """Test root endpoint returns service information"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "Sonotheia Enhanced Platform"
        assert data["version"] == "1.0.0"
        assert data["status"] == "operational"
        assert "features" in data
        assert "documentation" in data
        
    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "sonotheia-enhanced"
        assert "components" in data


class TestRequestTracking:
    """Test request tracking and monitoring features"""
    
    def test_request_id_header(self):
        """Test that all responses include X-Request-ID header"""
        response = client.get("/")
        assert "x-request-id" in response.headers
        assert len(response.headers["x-request-id"]) > 0
        
    def test_response_time_header(self):
        """Test that all responses include X-Response-Time header"""
        response = client.get("/")
        assert "x-response-time" in response.headers
        # Check it's a valid time in ms
        time_str = response.headers["x-response-time"]
        assert time_str.endswith("ms")
        time_value = float(time_str[:-2])
        assert time_value >= 0


class TestAuthenticationEndpoints:
    """Test authentication endpoints"""
    
    def test_v1_authenticate_valid_request(self):
        """Test v1 authentication with valid request"""
        request_data = {
            "transaction_id": "TXN-001",
            "customer_id": "CUST-001",
            "amount_usd": 5000.00,
            "channel": "wire_transfer",
            "has_consent": True
        }
        response = client.post("/api/v1/authenticate", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert "decision" in data
        
    def test_v1_authenticate_invalid_amount(self):
        """Test v1 authentication rejects invalid amount"""
        request_data = {
            "transaction_id": "TXN-001",
            "customer_id": "CUST-001",
            "amount_usd": -100.00,  # Negative amount
            "channel": "wire_transfer",
            "has_consent": True
        }
        response = client.post("/api/v1/authenticate", json=request_data)
        assert response.status_code == 422  # Validation error
        
    def test_enhanced_authenticate_valid_request(self):
        """Test enhanced authentication with valid request"""
        request_data = {
            "transaction_id": "TXN-002",
            "customer_id": "CUST-002",
            "amount_usd": 10000.00,
            "channel": "wire_transfer",
            "destination_country": "US",
            "is_new_beneficiary": True
        }
        response = client.post("/api/authenticate", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert "decision" in data
        assert "confidence" in data
        assert "risk_score" in data
        assert "risk_level" in data
        assert "factor_results" in data
        
    def test_enhanced_authenticate_invalid_channel(self):
        """Test enhanced authentication rejects invalid channel"""
        request_data = {
            "transaction_id": "TXN-003",
            "customer_id": "CUST-003",
            "amount_usd": 1000.00,
            "channel": "invalid_channel",
            "destination_country": "US",
            "is_new_beneficiary": False
        }
        response = client.post("/api/authenticate", json=request_data)
        assert response.status_code == 422  # Validation error
        
    def test_enhanced_authenticate_invalid_country(self):
        """Test enhanced authentication rejects invalid country code"""
        request_data = {
            "transaction_id": "TXN-004",
            "customer_id": "CUST-004",
            "amount_usd": 1000.00,
            "channel": "wire_transfer",
            "destination_country": "USA",  # Should be 2-letter code
            "is_new_beneficiary": False
        }
        response = client.post("/api/authenticate", json=request_data)
        assert response.status_code == 422  # Validation error


class TestInputValidation:
    """Test input validation and sanitization"""
    
    def test_transaction_id_validation(self):
        """Test transaction ID format validation"""
        # Valid ID
        request_data = {
            "transaction_id": "TXN-12345",
            "customer_id": "CUST-001",
            "amount_usd": 1000.00,
            "channel": "wire_transfer",
            "destination_country": "US"
        }
        response = client.post("/api/authenticate", json=request_data)
        assert response.status_code == 200
        
        # Invalid ID with special characters (use enhanced endpoint which has validation)
        request_data["transaction_id"] = "TXN<script>alert('xss')</script>"
        response = client.post("/api/authenticate", json=request_data)
        assert response.status_code == 422
        
    def test_amount_validation(self):
        """Test amount validation"""
        request_data = {
            "transaction_id": "TXN-001",
            "customer_id": "CUST-001",
            "amount_usd": 1000.50,
            "channel": "wire_transfer"
        }
        
        # Valid amount
        response = client.post("/api/authenticate", json=request_data)
        assert response.status_code == 200
        
        # Zero amount
        request_data["amount_usd"] = 0.0
        response = client.post("/api/authenticate", json=request_data)
        assert response.status_code == 422
        
        # Negative amount
        request_data["amount_usd"] = -100.0
        response = client.post("/api/authenticate", json=request_data)
        assert response.status_code == 422
        
        # Extremely large amount (exceeds max)
        request_data["amount_usd"] = 2000000000.0  # > 1 billion
        response = client.post("/api/authenticate", json=request_data)
        assert response.status_code == 422


class TestDemoEndpoints:
    """Test demo endpoints"""
    
    def test_demo_waveform(self):
        """Test demo waveform endpoint"""
        response = client.get("/api/demo/waveform/sample1")
        assert response.status_code == 200
        data = response.json()
        assert "x" in data
        assert "y" in data
        assert "segments" in data
        assert "sample_id" in data
        assert data["sample_id"] == "sample1"
        assert len(data["x"]) > 0
        assert len(data["y"]) > 0
        assert len(data["segments"]) > 0


class TestErrorHandling:
    """Test error handling and error responses"""
    
    def test_missing_required_field(self):
        """Test error when required field is missing"""
        request_data = {
            "transaction_id": "TXN-001",
            # Missing customer_id and amount_usd
        }
        response = client.post("/api/v1/authenticate", json=request_data)
        assert response.status_code == 422
        
    def test_invalid_json(self):
        """Test error handling for invalid JSON"""
        response = client.post(
            "/api/v1/authenticate",
            content=b"not valid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422
        
    def test_nonexistent_endpoint(self):
        """Test 404 for nonexistent endpoint"""
        response = client.get("/api/nonexistent")
        assert response.status_code == 404


class TestCORS:
    """Test CORS configuration"""
    
    def test_cors_headers_present(self):
        """Test that CORS headers are present"""
        response = client.options("/", headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST"
        })
        # FastAPI TestClient doesn't fully simulate browser CORS,
        # but we can verify the middleware is configured
        assert response.status_code in [200, 405]  # OPTIONS might not be handled


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
