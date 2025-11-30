"""
Tests for CI Verify Operability Script

These tests validate the CI readiness checks without requiring a running server.
Uses mock HTTP responses to test the verification logic.
"""

import json
import pytest
import sys
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError, URLError

# Add scripts to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from ci_verify_operability import (  # noqa: E402
    check_admin_modules,
    check_metrics_endpoint,
    check_health_endpoint,
)


class MockResponse:
    """Mock HTTP response for urlopen."""

    def __init__(self, data: bytes, status: int = 200):
        self.data = data
        self.status = status

    def read(self):
        return self.data

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


class TestCheckAdminModules:
    """Tests for check_admin_modules function."""

    def test_valid_response(self):
        """Test with valid admin modules response."""
        mock_data = {
            "modules": [
                {"name": "audio", "enabled": True, "description": "Audio module"},
                {"name": "detection", "enabled": True, "description": "Detection"},
            ],
            "total": 2,
            "enabled_count": 2,
            "disabled_count": 0,
            "profile": "full",
            "available_profiles": {},
        }
        response = MockResponse(json.dumps(mock_data).encode("utf-8"))

        with patch("ci_verify_operability.urlopen", return_value=response):
            passed, details = check_admin_modules("http://localhost:8000")

        assert passed is True
        assert "Profile: full" in details
        assert "Total: 2 modules" in details

    def test_missing_modules_key(self):
        """Test response missing 'modules' key."""
        mock_data = {"total": 0, "profile": "minimal"}
        response = MockResponse(json.dumps(mock_data).encode("utf-8"))

        with patch("ci_verify_operability.urlopen", return_value=response):
            passed, details = check_admin_modules("http://localhost:8000")

        assert passed is False
        assert "Missing 'modules' key" in details

    def test_empty_modules_list(self):
        """Test response with empty modules list."""
        mock_data = {
            "modules": [],
            "total": 0,
            "enabled_count": 0,
            "disabled_count": 0,
            "profile": "minimal",
        }
        response = MockResponse(json.dumps(mock_data).encode("utf-8"))

        with patch("ci_verify_operability.urlopen", return_value=response):
            passed, details = check_admin_modules("http://localhost:8000")

        assert passed is False
        assert "empty" in details.lower()

    def test_module_missing_fields(self):
        """Test module missing required fields."""
        mock_data = {
            "modules": [{"description": "Missing name and enabled"}],
            "total": 1,
            "enabled_count": 0,
            "disabled_count": 0,
            "profile": "minimal",
        }
        response = MockResponse(json.dumps(mock_data).encode("utf-8"))

        with patch("ci_verify_operability.urlopen", return_value=response):
            passed, details = check_admin_modules("http://localhost:8000")

        assert passed is False
        assert "name" in details.lower() or "enabled" in details.lower()

    def test_http_403_forbidden(self):
        """Test HTTP 403 response (admin key required)."""
        error = HTTPError(
            "http://localhost:8000/api/admin/modules",
            403,
            "Forbidden",
            {},
            None,
        )

        with patch("ci_verify_operability.urlopen", side_effect=error):
            passed, details = check_admin_modules("http://localhost:8000")

        assert passed is False
        assert "403" in details
        assert "Admin API key" in details

    def test_connection_error(self):
        """Test connection error handling."""
        error = URLError("Connection refused")

        with patch("ci_verify_operability.urlopen", side_effect=error):
            passed, details = check_admin_modules("http://localhost:8000")

        assert passed is False
        assert "Connection error" in details

    def test_api_key_header(self):
        """Test that API key is passed in header."""
        mock_data = {
            "modules": [{"name": "test", "enabled": True}],
            "total": 1,
            "enabled_count": 1,
            "disabled_count": 0,
            "profile": "full",
        }
        response = MockResponse(json.dumps(mock_data).encode("utf-8"))

        captured_request = None

        def capture_request(req, **kwargs):
            nonlocal captured_request
            captured_request = req
            return response

        with patch("ci_verify_operability.urlopen", side_effect=capture_request):
            check_admin_modules("http://localhost:8000", api_key="test-key")

        assert captured_request is not None
        # Note: Python's urllib normalizes header names, so X-API-Key becomes X-api-key
        assert captured_request.get_header("X-api-key") == "test-key"


class TestCheckMetricsEndpoint:
    """Tests for check_metrics_endpoint function."""

    def test_valid_metrics(self):
        """Test with valid Prometheus metrics."""
        metrics_text = """
# HELP sonotheia_module_enabled Whether a module is enabled
# TYPE sonotheia_module_enabled gauge
sonotheia_module_enabled{name="audio"} 1
sonotheia_module_enabled{name="detection"} 1
sonotheia_module_enabled{name="calibration"} 0
"""
        response = MockResponse(metrics_text.encode("utf-8"))

        with patch("ci_verify_operability.urlopen", return_value=response):
            passed, details = check_metrics_endpoint("http://localhost:8000")

        assert passed is True
        assert "Found 3 module metrics" in details
        assert "audio" in details
        assert "detection" in details
        assert "calibration" in details

    def test_no_module_metrics(self):
        """Test when module metrics are missing."""
        metrics_text = """
# HELP other_metric Some other metric
# TYPE other_metric gauge
other_metric{label="value"} 42
"""
        response = MockResponse(metrics_text.encode("utf-8"))

        with patch("ci_verify_operability.urlopen", return_value=response):
            passed, details = check_metrics_endpoint("http://localhost:8000")

        assert passed is False
        assert "not found" in details.lower()

    def test_metric_defined_but_empty(self):
        """Test when metric type exists but no values."""
        metrics_text = """
# HELP sonotheia_module_enabled Whether a module is enabled
# TYPE sonotheia_module_enabled gauge
"""
        response = MockResponse(metrics_text.encode("utf-8"))

        with patch("ci_verify_operability.urlopen", return_value=response):
            passed, details = check_metrics_endpoint("http://localhost:8000")

        assert passed is False
        assert "no module values found" in details.lower()

    def test_connection_error(self):
        """Test connection error handling."""
        error = URLError("Connection refused")

        with patch("ci_verify_operability.urlopen", side_effect=error):
            passed, details = check_metrics_endpoint("http://localhost:8000")

        assert passed is False
        assert "Connection error" in details


class TestCheckHealthEndpoint:
    """Tests for check_health_endpoint function."""

    def test_healthy_response(self):
        """Test with healthy status response."""
        mock_data = {
            "status": "healthy",
            "service": "sonotheia-enhanced",
            "components": {"orchestrator": "operational"},
        }
        response = MockResponse(json.dumps(mock_data).encode("utf-8"))

        with patch("ci_verify_operability.urlopen", return_value=response):
            passed, details = check_health_endpoint("http://localhost:8000")

        assert passed is True
        assert "healthy" in details.lower()

    def test_unhealthy_response(self):
        """Test with unhealthy status response."""
        mock_data = {"status": "degraded"}
        response = MockResponse(json.dumps(mock_data).encode("utf-8"))

        with patch("ci_verify_operability.urlopen", return_value=response):
            passed, details = check_health_endpoint("http://localhost:8000")

        assert passed is False
        assert "degraded" in details.lower()

    def test_connection_refused(self):
        """Test when server is not running."""
        error = URLError("Connection refused")

        with patch("ci_verify_operability.urlopen", side_effect=error):
            passed, details = check_health_endpoint("http://localhost:8000")

        assert passed is False
        assert "Connection error" in details


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
