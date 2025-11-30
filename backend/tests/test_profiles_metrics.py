"""
Tests for Module Profiles and Prometheus Metrics

Tests profile expansion, loading order, and metrics export.
"""

import pytest
import os
import tempfile
from pathlib import Path
import sys

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.module_registry import ModuleRegistry, get_registry  # noqa: E402
from core.profiles import (  # noqa: E402
    get_current_profile,
    get_profile_modules,
    get_profile_defaults,
    list_profiles,
    DEFAULT_PROFILE,
)
from observability.metrics import (  # noqa: E402
    update_module_metrics,
    get_module_metrics_values,
    refresh_metrics,
)


class TestProfiles:
    """Test module profile presets."""

    def setup_method(self):
        """Reset singleton and env vars before each test."""
        ModuleRegistry.reset()
        # Clear any MODULE_ environment variables from previous tests
        for key in list(os.environ.keys()):
            if key.startswith("MODULE_"):
                del os.environ[key]

    def teardown_method(self):
        """Clean up after each test."""
        ModuleRegistry.reset()
        for key in list(os.environ.keys()):
            if key.startswith("MODULE_"):
                del os.environ[key]

    def test_default_profile_is_full(self):
        """Test that default profile is 'full' when MODULE_PROFILE is not set."""
        assert get_current_profile() == "full"

    def test_profile_from_env(self):
        """Test getting profile from environment variable."""
        os.environ["MODULE_PROFILE"] = "minimal"
        assert get_current_profile() == "minimal"

        os.environ["MODULE_PROFILE"] = "standard"
        assert get_current_profile() == "standard"

        os.environ["MODULE_PROFILE"] = "full"
        assert get_current_profile() == "full"

    def test_invalid_profile_falls_back_to_default(self):
        """Test that invalid profile falls back to default."""
        os.environ["MODULE_PROFILE"] = "invalid_profile"
        assert get_current_profile() == DEFAULT_PROFILE

    def test_minimal_profile_modules(self):
        """Test minimal profile contains expected modules."""
        minimal_modules = get_profile_modules("minimal")
        expected = {"audio", "detection", "sar", "rate_limiting", "observability"}
        assert minimal_modules == expected

    def test_standard_profile_modules(self):
        """Test standard profile contains minimal + additional modules."""
        standard_modules = get_profile_modules("standard")
        minimal_modules = get_profile_modules("minimal")

        # Standard should contain all minimal modules
        assert minimal_modules.issubset(standard_modules)

        # Plus additional modules
        assert "calibration" in standard_modules
        assert "analysis" in standard_modules
        assert "celery" in standard_modules

    def test_full_profile_modules(self):
        """Test full profile contains all modules."""
        full_modules = get_profile_modules("full")
        standard_modules = get_profile_modules("standard")

        # Full should contain all standard modules
        assert standard_modules.issubset(full_modules)

        # Plus advanced modules
        assert "transcription" in full_modules
        assert "tenants" in full_modules
        assert "mlflow" in full_modules
        assert "risk_engine" in full_modules

    def test_profile_defaults_enables_profile_modules(self):
        """Test get_profile_defaults enables modules in the profile."""
        minimal_defaults = get_profile_defaults("minimal")
        minimal_modules = get_profile_modules("minimal")

        for module_name in minimal_modules:
            assert minimal_defaults[module_name]["enabled"] is True

    def test_profile_defaults_disables_non_profile_modules(self):
        """Test get_profile_defaults disables modules not in the profile."""
        minimal_defaults = get_profile_defaults("minimal")
        full_modules = get_profile_modules("full")
        minimal_modules = get_profile_modules("minimal")

        non_minimal = full_modules - minimal_modules
        for module_name in non_minimal:
            assert minimal_defaults[module_name]["enabled"] is False

    def test_list_profiles_returns_all_profiles(self):
        """Test list_profiles returns info for all profiles."""
        profiles = list_profiles()

        assert "minimal" in profiles
        assert "standard" in profiles
        assert "full" in profiles

        # Each profile should have modules and module_count
        for name, info in profiles.items():
            assert "modules" in info
            assert "module_count" in info
            assert info["module_count"] == len(info["modules"])


class TestProfileIntegration:
    """Test profile integration with ModuleRegistry."""

    def setup_method(self):
        """Reset singleton and env vars before each test."""
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

    def test_registry_uses_profile_defaults(self):
        """Test that registry initializes with profile defaults."""
        os.environ["MODULE_PROFILE"] = "minimal"

        yaml_content = """
modules:
  # Empty - rely on profile defaults
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            registry = ModuleRegistry(config_path=temp_path)

            # Modules in minimal profile should be enabled
            assert registry.is_enabled("audio") is True
            assert registry.is_enabled("detection") is True
            assert registry.is_enabled("sar") is True

            # Modules not in minimal profile should be disabled
            assert registry.is_enabled("transcription") is False
            assert registry.is_enabled("mlflow") is False
        finally:
            os.unlink(temp_path)

    def test_yaml_overrides_profile(self):
        """Test that YAML config overrides profile defaults."""
        os.environ["MODULE_PROFILE"] = "minimal"

        yaml_content = """
modules:
  audio:
    enabled: false
    description: "Disabled by YAML"
  transcription:
    enabled: true
    description: "Enabled by YAML"
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            registry = ModuleRegistry(config_path=temp_path)

            # YAML override should disable audio (despite being in minimal profile)
            assert registry.is_enabled("audio") is False

            # YAML override should enable transcription (despite not in minimal profile)
            assert registry.is_enabled("transcription") is True
        finally:
            os.unlink(temp_path)

    def test_env_overrides_yaml(self):
        """Test that env vars override YAML config."""
        os.environ["MODULE_PROFILE"] = "minimal"

        yaml_content = """
modules:
  audio:
    enabled: false
    description: "Disabled by YAML"
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            # Env var should override YAML
            os.environ["MODULE_AUDIO"] = "1"

            registry = ModuleRegistry(config_path=temp_path)

            # Env var should re-enable audio
            assert registry.is_enabled("audio") is True
        finally:
            os.unlink(temp_path)

    def test_full_loading_order(self):
        """Test complete loading order: profile -> YAML -> env."""
        # Start with minimal profile
        os.environ["MODULE_PROFILE"] = "minimal"

        yaml_content = """
modules:
  detection:
    enabled: false
    description: "Detection disabled by YAML"
  calibration:
    enabled: true
    description: "Calibration enabled by YAML"
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            # Override detection via env (should re-enable it)
            os.environ["MODULE_DETECTION"] = "1"
            # Override calibration via env (should disable it)
            os.environ["MODULE_CALIBRATION"] = "0"

            registry = ModuleRegistry(config_path=temp_path)

            # Profile default for audio (minimal has it enabled)
            assert registry.is_enabled("audio") is True

            # YAML disabled detection, but env re-enabled it
            assert registry.is_enabled("detection") is True

            # YAML enabled calibration, but env disabled it
            assert registry.is_enabled("calibration") is False

            # Profile should be stored
            assert registry.get_profile() == "minimal"
        finally:
            os.unlink(temp_path)


class TestPrometheusMetrics:
    """Test Prometheus metrics functionality."""

    def setup_method(self):
        """Reset singleton and env vars before each test."""
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

    def test_update_module_metrics(self):
        """Test that update_module_metrics sets gauge values."""
        yaml_content = """
modules:
  test_enabled:
    enabled: true
    description: "Test enabled module"
  test_disabled:
    enabled: false
    description: "Test disabled module"
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            os.environ["MODULE_PROFILE"] = "full"
            get_registry(config_path=temp_path)

            # Update metrics
            update_module_metrics()

            # Get metrics values
            values = get_module_metrics_values()

            assert "test_enabled" in values
            assert "test_disabled" in values
            assert values["test_enabled"] == 1
            assert values["test_disabled"] == 0
        finally:
            os.unlink(temp_path)

    def test_refresh_metrics_returns_values(self):
        """Test that refresh_metrics updates and returns values."""
        yaml_content = """
modules:
  module_a:
    enabled: true
  module_b:
    enabled: false
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            os.environ["MODULE_PROFILE"] = "full"
            get_registry(config_path=temp_path)

            values = refresh_metrics()

            assert isinstance(values, dict)
            assert "module_a" in values
            assert "module_b" in values
        finally:
            os.unlink(temp_path)

    def test_metrics_reflect_runtime_changes(self):
        """Test that metrics update when module states change."""
        yaml_content = """
modules:
  dynamic_module:
    enabled: true
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            os.environ["MODULE_PROFILE"] = "full"
            registry = get_registry(config_path=temp_path)

            # Initial update
            update_module_metrics()
            values = get_module_metrics_values()
            assert values.get("dynamic_module") == 1

            # Toggle module state
            registry.set_enabled("dynamic_module", False)

            # Refresh metrics
            values = refresh_metrics()
            assert values.get("dynamic_module") == 0

            # Toggle back
            registry.set_enabled("dynamic_module", True)
            values = refresh_metrics()
            assert values.get("dynamic_module") == 1
        finally:
            os.unlink(temp_path)


class TestMetricsEndpoint:
    """Test the /metrics endpoint integration."""

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

    @pytest.mark.asyncio
    async def test_metrics_endpoint_returns_prometheus_format(self):
        """Test that metrics endpoint returns Prometheus format."""
        from observability.metrics import metrics_endpoint
        from starlette.testclient import TestClient
        from starlette.applications import Starlette
        from starlette.routing import Route

        yaml_content = """
modules:
  test_module:
    enabled: true
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            os.environ["MODULE_PROFILE"] = "full"
            get_registry(config_path=temp_path)
            update_module_metrics()

            app = Starlette(routes=[Route("/metrics", metrics_endpoint)])
            client = TestClient(app)

            response = client.get("/metrics")

            assert response.status_code == 200
            assert "text/plain" in response.headers["content-type"]

            # Check for Prometheus metric format
            content = response.text
            assert "sonotheia_module_enabled" in content
        finally:
            os.unlink(temp_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
