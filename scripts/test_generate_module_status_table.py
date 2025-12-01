"""
Tests for Generate Module Status Table Script

These tests validate the module status table generation without requiring a running server.
Uses mock HTTP responses and data to test the generation logic.
"""

import json
import pytest
import sys
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError, URLError

# Add scripts to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from generate_module_status_table import (  # noqa: E402
    fetch_modules,
    generate_table,
    generate_fragment,
    validate_table,
    TABLE_START_MARKER,
    TABLE_END_MARKER,
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


class TestFetchModules:
    """Tests for fetch_modules function."""

    def test_valid_response(self):
        """Test with valid modules response."""
        mock_data = {
            "modules": [
                {
                    "name": "audio",
                    "configured_enabled": True,
                    "effective_enabled": True,
                },
            ],
            "total": 1,
            "enabled_count": 1,
            "disabled_count": 0,
            "profile": "full",
        }
        response = MockResponse(json.dumps(mock_data).encode("utf-8"))

        with patch("generate_module_status_table.urlopen", return_value=response):
            result = fetch_modules("http://localhost:8000")

        assert result["total"] == 1
        assert result["profile"] == "full"
        assert len(result["modules"]) == 1

    def test_http_error(self):
        """Test HTTP error handling."""
        error = HTTPError(
            "http://localhost:8000/api/admin/modules",
            500,
            "Internal Server Error",
            {},
            None,
        )

        with patch("generate_module_status_table.urlopen", side_effect=error):
            with pytest.raises(Exception) as exc_info:
                fetch_modules("http://localhost:8000")

        assert "HTTP Error 500" in str(exc_info.value)

    def test_connection_error(self):
        """Test connection error handling."""
        error = URLError("Connection refused")

        with patch("generate_module_status_table.urlopen", side_effect=error):
            with pytest.raises(Exception) as exc_info:
                fetch_modules("http://localhost:8000")

        assert "URL Error" in str(exc_info.value)

    def test_api_key_header(self):
        """Test that API key is passed in header."""
        mock_data = {"modules": [], "total": 0, "profile": "minimal"}
        response = MockResponse(json.dumps(mock_data).encode("utf-8"))

        captured_request = None

        def capture_request(req, **kwargs):
            nonlocal captured_request
            captured_request = req
            return response

        with patch("generate_module_status_table.urlopen", side_effect=capture_request):
            fetch_modules("http://localhost:8000", api_key="test-key")

        assert captured_request is not None
        # Note: Python's urllib normalizes header names
        assert captured_request.get_header("X-api-key") == "test-key"


class TestGenerateTable:
    """Tests for generate_table function."""

    def test_basic_table_generation(self):
        """Test basic table generation with modules."""
        modules_data = {
            "modules": [
                {
                    "name": "audio",
                    "configured_enabled": True,
                    "effective_enabled": True,
                    "last_effective_change": None,
                    "reason": "configured",
                },
                {
                    "name": "detection",
                    "configured_enabled": False,
                    "effective_enabled": False,
                    "last_effective_change": "2025-01-15T10:30:00Z",
                    "reason": "disabled_by_user",
                },
            ],
            "last_health_recheck": "2025-01-15T12:00:00Z",
        }

        table = generate_table(modules_data)

        # Check header row
        assert "| Module | Configured | Effective | Last Change (UTC) |" in table
        # Check data rows
        assert "| audio |" in table
        assert "| detection |" in table
        # Check status icons
        assert "✅" in table  # Enabled
        assert "❌" in table  # Disabled

    def test_empty_modules_list(self):
        """Test table generation with empty modules list."""
        modules_data = {"modules": [], "last_health_recheck": "2025-01-15T12:00:00Z"}

        table = generate_table(modules_data)

        # Should still have header
        assert "| Module | Configured | Effective |" in table
        # Should have separator line
        assert "|--------|" in table

    def test_all_required_columns(self):
        """Test that all required columns are present."""
        modules_data = {
            "modules": [
                {
                    "name": "test",
                    "configured_enabled": True,
                    "effective_enabled": True,
                    "last_effective_change": None,
                    "reason": "configured",
                }
            ],
            "last_health_recheck": "2025-01-15T12:00:00Z",
        }

        table = generate_table(modules_data)

        # All required columns
        assert "Module" in table
        assert "Configured" in table
        assert "Effective" in table
        assert "Last Change (UTC)" in table
        assert "Last Recheck (UTC)" in table
        assert "Reason" in table

    def test_null_last_change_displays_na(self):
        """Test that null last_effective_change displays as N/A."""
        modules_data = {
            "modules": [
                {
                    "name": "test",
                    "configured_enabled": True,
                    "effective_enabled": True,
                    "last_effective_change": None,
                    "reason": "configured",
                }
            ],
            "last_health_recheck": "2025-01-15T12:00:00Z",
        }

        table = generate_table(modules_data)

        assert "N/A" in table


class TestGenerateFragment:
    """Tests for generate_fragment function."""

    def test_fragment_includes_markers(self):
        """Test that fragment includes start and end markers."""
        modules_data = {
            "modules": [],
            "total": 0,
            "enabled_count": 0,
            "disabled_count": 0,
            "profile": "minimal",
            "last_health_recheck": "2025-01-15T12:00:00Z",
        }

        fragment = generate_fragment(modules_data)

        assert TABLE_START_MARKER in fragment
        assert TABLE_END_MARKER in fragment

    def test_fragment_includes_profile_info(self):
        """Test that fragment includes profile information."""
        modules_data = {
            "modules": [],
            "total": 5,
            "enabled_count": 3,
            "disabled_count": 2,
            "profile": "standard",
            "last_health_recheck": "2025-01-15T12:00:00Z",
        }

        fragment = generate_fragment(modules_data)

        assert "**Profile:** standard" in fragment
        assert "**Total:** 5" in fragment
        assert "**Enabled:** 3" in fragment
        assert "**Disabled:** 2" in fragment

    def test_fragment_includes_table(self):
        """Test that fragment includes the module table."""
        modules_data = {
            "modules": [
                {
                    "name": "audio",
                    "configured_enabled": True,
                    "effective_enabled": True,
                    "last_effective_change": None,
                    "reason": "configured",
                }
            ],
            "total": 1,
            "enabled_count": 1,
            "disabled_count": 0,
            "profile": "full",
            "last_health_recheck": "2025-01-15T12:00:00Z",
        }

        fragment = generate_fragment(modules_data)

        assert "| audio |" in fragment

    def test_fragment_includes_timestamp(self):
        """Test that fragment includes generation timestamp."""
        modules_data = {
            "modules": [],
            "total": 0,
            "enabled_count": 0,
            "disabled_count": 0,
            "profile": "minimal",
            "last_health_recheck": "2025-01-15T12:00:00Z",
        }

        fragment = generate_fragment(modules_data)

        assert "*Last generated:" in fragment


class TestValidateTable:
    """Tests for validate_table function."""

    def test_valid_table_returns_empty_list(self):
        """Test that a valid table returns empty list."""
        valid_fragment = """
<!-- MODULE_STATUS_TABLE_START -->
| Module | Configured | Effective | Last Change (UTC) | Last Recheck (UTC) | Reason |
|--------|-----------|-----------|-------------------|--------------------|--------|
| audio | ✅ | ✅ | N/A | 2025-01-15 | configured |
<!-- MODULE_STATUS_TABLE_END -->
"""
        missing = validate_table(valid_fragment)
        assert missing == []

    def test_missing_module_column(self):
        """Test detection of missing Module column."""
        invalid_fragment = """
| Configured | Effective | Last Change (UTC) | Last Recheck (UTC) | Reason |
|-----------|-----------|-------------------|--------------------|--------|
"""
        missing = validate_table(invalid_fragment)
        assert "Module" in missing

    def test_missing_configured_column(self):
        """Test detection of missing Configured column."""
        invalid_fragment = """
| Module | Effective | Last Change (UTC) | Last Recheck (UTC) | Reason |
|--------|-----------|-------------------|--------------------|--------|
"""
        missing = validate_table(invalid_fragment)
        assert "Configured" in missing

    def test_missing_effective_column(self):
        """Test detection of missing Effective column."""
        invalid_fragment = """
| Module | Configured | Last Change (UTC) | Last Recheck (UTC) | Reason |
|--------|-----------|-------------------|--------------------|--------|
"""
        missing = validate_table(invalid_fragment)
        assert "Effective" in missing

    def test_missing_last_change_column(self):
        """Test detection of missing Last Change column."""
        invalid_fragment = """
| Module | Configured | Effective | Last Recheck (UTC) | Reason |
|--------|-----------|-----------|-------------------|--------|
"""
        missing = validate_table(invalid_fragment)
        assert "Last Change (UTC)" in missing

    def test_missing_last_recheck_column(self):
        """Test detection of missing Last Recheck column."""
        invalid_fragment = """
| Module | Configured | Effective | Last Change (UTC) | Reason |
|--------|-----------|-----------|-------------------|--------|
"""
        missing = validate_table(invalid_fragment)
        assert "Last Recheck (UTC)" in missing

    def test_missing_reason_column(self):
        """Test detection of missing Reason column."""
        invalid_fragment = """
| Module | Configured | Effective | Last Change (UTC) | Last Recheck (UTC) |
|--------|-----------|-----------|-------------------|--------------------|
"""
        missing = validate_table(invalid_fragment)
        assert "Reason" in missing

    def test_no_header_returns_all_columns(self):
        """Test that no table header returns all columns as missing."""
        no_table_fragment = "Just some text without a table"
        missing = validate_table(no_table_fragment)
        assert len(missing) == 6  # All 6 required columns


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
