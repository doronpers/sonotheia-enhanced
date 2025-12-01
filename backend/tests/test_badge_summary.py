"""
Tests for Badge Endpoints and Module Summary

Tests badge color selection logic and summary endpoint.
"""

import pytest
import os
import tempfile
from pathlib import Path
import sys

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.module_registry import ModuleRegistry, get_registry  # noqa: E402
from api.routes.badge import _get_badge_color, ShieldsBadgeResponse  # noqa: E402


class TestShieldsBadgeResponse:
    """Test ShieldsBadgeResponse Pydantic model schema validation."""

    def test_schema_version_is_one(self):
        """Test that schemaVersion defaults to and equals 1."""
        response = ShieldsBadgeResponse(
            label="modules", message="10/12", color="brightgreen"
        )
        assert response.schemaVersion == 1

    def test_schema_version_explicit_one(self):
        """Test that schemaVersion can be explicitly set to 1."""
        response = ShieldsBadgeResponse(
            schemaVersion=1, label="modules", message="5/10", color="yellow"
        )
        assert response.schemaVersion == 1

    def test_message_enabled_total_format(self):
        """Test that message follows E/N (enabled/total) format."""
        response = ShieldsBadgeResponse(
            label="modules", message="10/12", color="brightgreen"
        )
        # Message should contain "/" separator
        assert "/" in response.message
        # Message should be in format "N/M" where N and M are numbers
        parts = response.message.split("/")
        assert len(parts) == 2
        assert parts[0].isdigit()
        assert parts[1].isdigit()

    def test_message_zero_enabled(self):
        """Test E/N format with zero enabled modules."""
        response = ShieldsBadgeResponse(label="modules", message="0/10", color="red")
        parts = response.message.split("/")
        assert len(parts) == 2
        assert parts[0] == "0"
        assert parts[1] == "10"

    def test_message_all_enabled(self):
        """Test E/N format with all modules enabled."""
        response = ShieldsBadgeResponse(
            label="modules", message="10/10", color="brightgreen"
        )
        parts = response.message.split("/")
        assert parts[0] == parts[1]  # enabled equals total

    def test_message_large_numbers(self):
        """Test E/N format with large module counts."""
        response = ShieldsBadgeResponse(
            label="modules", message="100/125", color="brightgreen"
        )
        parts = response.message.split("/")
        assert len(parts) == 2
        assert int(parts[0]) == 100
        assert int(parts[1]) == 125

    def test_label_is_modules(self):
        """Test that label is 'modules' for module badge."""
        response = ShieldsBadgeResponse(label="modules", message="5/10", color="yellow")
        assert response.label == "modules"

    def test_valid_colors(self):
        """Test that color values match expected Shields.io colors."""
        valid_colors = ["brightgreen", "yellow", "red", "lightgrey"]

        for color in valid_colors:
            response = ShieldsBadgeResponse(
                label="modules", message="5/10", color=color
            )
            assert response.color == color

    def test_response_json_serialization(self):
        """Test that response can be serialized to JSON for Shields.io."""
        response = ShieldsBadgeResponse(
            schemaVersion=1, label="modules", message="8/10", color="brightgreen"
        )
        json_dict = response.model_dump()

        assert json_dict["schemaVersion"] == 1
        assert json_dict["label"] == "modules"
        assert json_dict["message"] == "8/10"
        assert json_dict["color"] == "brightgreen"

    def test_init_message_format(self):
        """Test 'init' message for uninitialized registry."""
        response = ShieldsBadgeResponse(
            label="modules", message="init", color="lightgrey"
        )
        assert response.message == "init"
        assert response.color == "lightgrey"


class TestBadgeColorSelection:
    """Test badge color selection logic for different ratios."""

    def test_zero_total_returns_lightgrey(self):
        """Test that 0/0 returns lightgrey."""
        assert _get_badge_color(0, 0) == "lightgrey"

    def test_zero_percent_returns_red(self):
        """Test that 0% enabled returns red."""
        assert _get_badge_color(0, 10) == "red"

    def test_45_percent_returns_red(self):
        """Test that 45% enabled returns red (< 50%)."""
        # 45/100 = 45%
        assert _get_badge_color(45, 100) == "red"

    def test_49_percent_returns_red(self):
        """Test that 49% enabled returns red (< 50%)."""
        assert _get_badge_color(49, 100) == "red"

    def test_50_percent_returns_yellow(self):
        """Test that exactly 50% enabled returns yellow."""
        assert _get_badge_color(50, 100) == "yellow"

    def test_70_percent_returns_yellow(self):
        """Test that 70% enabled returns yellow (50% <= x < 80%)."""
        assert _get_badge_color(70, 100) == "yellow"

    def test_79_percent_returns_yellow(self):
        """Test that 79% enabled returns yellow (< 80%)."""
        assert _get_badge_color(79, 100) == "yellow"

    def test_80_percent_returns_brightgreen(self):
        """Test that exactly 80% enabled returns brightgreen."""
        assert _get_badge_color(80, 100) == "brightgreen"

    def test_95_percent_returns_brightgreen(self):
        """Test that 95% enabled returns brightgreen (>= 80%)."""
        assert _get_badge_color(95, 100) == "brightgreen"

    def test_100_percent_returns_brightgreen(self):
        """Test that 100% enabled returns brightgreen."""
        assert _get_badge_color(100, 100) == "brightgreen"
        assert _get_badge_color(10, 10) == "brightgreen"

    def test_small_numbers(self):
        """Test color selection with small module counts."""
        # 8/10 = 80%
        assert _get_badge_color(8, 10) == "brightgreen"
        # 5/10 = 50%
        assert _get_badge_color(5, 10) == "yellow"
        # 4/10 = 40%
        assert _get_badge_color(4, 10) == "red"


class TestBadgeEndpointIntegration:
    """Integration tests for badge endpoint."""

    def setup_method(self):
        """Reset singleton before each test."""
        ModuleRegistry.reset()
        for key in list(os.environ.keys()):
            if key.startswith("MODULE_"):
                del os.environ[key]

    def teardown_method(self):
        """Clean up after each test."""
        ModuleRegistry.reset()
        for key in list(os.environ.keys()):
            if key.startswith("MODULE_"):
                del os.environ[key]

    def test_badge_endpoint_returns_valid_schema(self):
        """Test that badge endpoint returns valid Shields.io schema."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from api.routes.badge import router
        from api.middleware import limiter

        # Create test app with limiter
        app = FastAPI()
        app.state.limiter = limiter
        app.include_router(router)

        yaml_content = """
modules:
  test_enabled:
    enabled: true
  test_disabled:
    enabled: false
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            os.environ["MODULE_PROFILE"] = "full"
            get_registry(config_path=temp_path)

            client = TestClient(app)
            response = client.get("/api/badge/modules_enabled")

            assert response.status_code == 200
            data = response.json()

            # Validate Shields.io schema
            assert "schemaVersion" in data
            assert data["schemaVersion"] == 1
            assert "label" in data
            assert data["label"] == "modules"
            assert "message" in data
            assert "/" in data["message"]  # Format: "N/M"
            assert "color" in data
            assert data["color"] in ["brightgreen", "yellow", "red", "lightgrey"]

        finally:
            os.unlink(temp_path)

    def test_badge_endpoint_no_auth_required(self):
        """Test that badge endpoint does not require authentication."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from api.routes.badge import router
        from api.middleware import limiter

        app = FastAPI()
        app.state.limiter = limiter
        app.include_router(router)

        yaml_content = """
modules:
  test_module:
    enabled: true
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            os.environ["MODULE_PROFILE"] = "full"
            get_registry(config_path=temp_path)

            client = TestClient(app)
            # No X-API-Key header
            response = client.get("/api/badge/modules_enabled")

            # Should succeed without auth
            assert response.status_code == 200

        finally:
            os.unlink(temp_path)


class TestModuleSummaryEndpoint:
    """Tests for module summary endpoint."""

    def setup_method(self):
        """Reset singleton before each test."""
        ModuleRegistry.reset()
        for key in list(os.environ.keys()):
            if key.startswith("MODULE_"):
                del os.environ[key]

    def teardown_method(self):
        """Clean up after each test."""
        ModuleRegistry.reset()
        for key in list(os.environ.keys()):
            if key.startswith("MODULE_"):
                del os.environ[key]

    def test_summary_returns_counts(self):
        """Test that summary endpoint returns correct counts."""
        from fastapi import FastAPI, Request
        from fastapi.testclient import TestClient
        from api.routes.admin_modules import router, require_admin
        from api.middleware import limiter

        # Create test app with limiter
        app = FastAPI()
        app.state.limiter = limiter

        # Mock admin auth - need to properly handle dependency signature
        async def mock_admin(request: Request):
            return {"client": "test", "tier": "admin"}

        app.dependency_overrides[require_admin] = mock_admin
        app.include_router(router)

        yaml_content = """
modules:
  enabled_1:
    enabled: true
  enabled_2:
    enabled: true
  disabled_1:
    enabled: false
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            os.environ["MODULE_PROFILE"] = "full"
            get_registry(config_path=temp_path)

            client = TestClient(app)
            response = client.get("/api/admin/modules/summary")

            assert response.status_code == 200
            data = response.json()

            assert "total" in data
            assert "enabled" in data
            assert "disabled" in data
            assert "last_recheck" in data

            # Should have some modules
            assert data["total"] > 0
            assert data["enabled"] + data["disabled"] == data["total"]

        finally:
            os.unlink(temp_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
