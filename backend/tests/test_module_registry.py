"""
Tests for Module Registry

Tests module loading, environment variable overrides, and API route blocking.
"""

import pytest
import os
import tempfile
from pathlib import Path
import sys

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.module_registry import (  # noqa: E402
    ModuleRegistry,
    get_registry,
    is_module_enabled,
)


class TestModuleRegistry:
    """Test ModuleRegistry class functionality"""

    def setup_method(self):
        """Reset singleton before each test"""
        ModuleRegistry.reset()
        # Clear any MODULE_ environment variables from previous tests
        for key in list(os.environ.keys()):
            if key.startswith("MODULE_"):
                del os.environ[key]

    def teardown_method(self):
        """Clean up after each test"""
        ModuleRegistry.reset()
        # Clear any MODULE_ environment variables
        for key in list(os.environ.keys()):
            if key.startswith("MODULE_"):
                del os.environ[key]

    def test_load_yaml_config(self):
        """Test loading module configuration from YAML file"""
        # Create a temporary YAML file
        yaml_content = """
modules:
  test_module:
    enabled: true
    description: "Test module"
  disabled_module:
    enabled: false
    description: "Disabled test module"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            registry = ModuleRegistry(config_path=temp_path)

            assert registry.is_enabled("test_module") is True
            assert registry.is_enabled("disabled_module") is False
        finally:
            os.unlink(temp_path)

    def test_env_override_yaml_true_to_false(self):
        """Test that environment variable can disable a YAML-enabled module"""
        yaml_content = """
modules:
  audio:
    enabled: true
    description: "Audio module"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            # Set env var to disable
            os.environ["MODULE_AUDIO"] = "0"

            registry = ModuleRegistry(config_path=temp_path)

            # Env var should override YAML
            assert registry.is_enabled("audio") is False
        finally:
            os.unlink(temp_path)

    def test_env_override_yaml_false_to_true(self):
        """Test that environment variable can enable a YAML-disabled module"""
        yaml_content = """
modules:
  calibration:
    enabled: false
    description: "Calibration module"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            # Set env var to enable
            os.environ["MODULE_CALIBRATION"] = "1"

            registry = ModuleRegistry(config_path=temp_path)

            # Env var should override YAML
            assert registry.is_enabled("calibration") is True
        finally:
            os.unlink(temp_path)

    def test_env_var_boolean_values(self):
        """Test various boolean value formats for environment variables"""
        yaml_content = """
modules:
  mod_a:
    enabled: true
  mod_b:
    enabled: true
  mod_c:
    enabled: true
  mod_d:
    enabled: false
  mod_e:
    enabled: false
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            # Test various false values
            os.environ["MODULE_MOD_A"] = "false"
            os.environ["MODULE_MOD_B"] = "False"
            os.environ["MODULE_MOD_C"] = "no"
            # Test various true values
            os.environ["MODULE_MOD_D"] = "true"
            os.environ["MODULE_MOD_E"] = "yes"

            registry = ModuleRegistry(config_path=temp_path)

            assert registry.is_enabled("mod_a") is False
            assert registry.is_enabled("mod_b") is False
            assert registry.is_enabled("mod_c") is False
            assert registry.is_enabled("mod_d") is True
            assert registry.is_enabled("mod_e") is True
        finally:
            os.unlink(temp_path)

    def test_unknown_module_defaults_enabled(self):
        """Test that unknown modules default to enabled"""
        yaml_content = """
modules:
  known_module:
    enabled: true
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            registry = ModuleRegistry(config_path=temp_path)

            # Unknown module should default to enabled
            assert registry.is_enabled("unknown_module") is True
        finally:
            os.unlink(temp_path)

    def test_env_creates_new_module(self):
        """Test that env var can create a module not in YAML"""
        yaml_content = """
modules:
  existing_module:
    enabled: true
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            # Create new module via env var
            os.environ["MODULE_NEW_MODULE"] = "0"

            registry = ModuleRegistry(config_path=temp_path)

            # New module should exist and be disabled
            assert registry.is_enabled("new_module") is False
            info = registry.get_module_info("new_module")
            assert info is not None
            assert info["enabled"] is False
        finally:
            os.unlink(temp_path)

    def test_list_modules(self):
        """Test listing all modules"""
        yaml_content = """
modules:
  module_a:
    enabled: true
    description: "Module A"
  module_b:
    enabled: false
    description: "Module B"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            registry = ModuleRegistry(config_path=temp_path)
            modules = registry.list_modules()

            assert "module_a" in modules
            assert "module_b" in modules
            assert modules["module_a"]["enabled"] is True
            assert modules["module_b"]["enabled"] is False
        finally:
            os.unlink(temp_path)

    def test_list_enabled_disabled(self):
        """Test listing enabled and disabled modules separately"""
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
            registry = ModuleRegistry(config_path=temp_path)

            enabled = registry.list_enabled()
            disabled = registry.list_disabled()

            assert "enabled_1" in enabled
            assert "enabled_2" in enabled
            assert "disabled_1" not in enabled

            assert "disabled_1" in disabled
            assert "enabled_1" not in disabled
        finally:
            os.unlink(temp_path)

    def test_runtime_set_enabled(self):
        """Test runtime toggling of module state"""
        yaml_content = """
modules:
  test_module:
    enabled: true
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            registry = ModuleRegistry(config_path=temp_path)

            assert registry.is_enabled("test_module") is True

            # Toggle to disabled
            registry.set_enabled("test_module", False)
            assert registry.is_enabled("test_module") is False

            # Toggle back to enabled
            registry.set_enabled("test_module", True)
            assert registry.is_enabled("test_module") is True
        finally:
            os.unlink(temp_path)

    def test_singleton_pattern(self):
        """Test that ModuleRegistry is a singleton"""
        yaml_content = """
modules:
  test_module:
    enabled: true
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            registry1 = ModuleRegistry(config_path=temp_path)
            registry2 = ModuleRegistry()  # Should return same instance

            assert registry1 is registry2

            # Modify through one, check through other
            registry1.set_enabled("test_module", False)
            assert registry2.is_enabled("test_module") is False
        finally:
            os.unlink(temp_path)

    def test_case_insensitive_module_names(self):
        """Test that module names are case-insensitive"""
        yaml_content = """
modules:
  TestModule:
    enabled: true
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            registry = ModuleRegistry(config_path=temp_path)

            # Should work with different cases
            assert registry.is_enabled("testmodule") is True
            assert registry.is_enabled("TESTMODULE") is True
            assert registry.is_enabled("TestModule") is True
        finally:
            os.unlink(temp_path)

    def test_missing_yaml_file(self):
        """Test behavior when YAML file doesn't exist"""
        registry = ModuleRegistry(config_path="/nonexistent/path/modules.yaml")

        # Should not raise, and modules should default to enabled
        assert registry.is_enabled("any_module") is True

    def test_convenience_functions(self):
        """Test module-level convenience functions"""
        yaml_content = """
modules:
  test_mod:
    enabled: false
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            # Initialize registry with path
            get_registry(config_path=temp_path)

            # Test convenience function
            assert is_module_enabled("test_mod") is False
        finally:
            os.unlink(temp_path)


class TestModuleRegistryIntegration:
    """Integration tests for module registry with FastAPI"""

    def setup_method(self):
        """Reset singleton before each test"""
        ModuleRegistry.reset()
        for key in list(os.environ.keys()):
            if key.startswith("MODULE_"):
                del os.environ[key]

    def teardown_method(self):
        """Clean up after each test"""
        ModuleRegistry.reset()
        for key in list(os.environ.keys()):
            if key.startswith("MODULE_"):
                del os.environ[key]

    def test_disabled_module_returns_503(self):
        """Test that disabled module returns 503 via dependency"""
        from fastapi import FastAPI, Depends
        from fastapi.testclient import TestClient
        from api.dependencies import require_module

        # Create test app
        app = FastAPI()

        @app.get("/test-endpoint")
        async def test_endpoint(_: None = Depends(require_module("test_module"))):
            return {"status": "ok"}

        client = TestClient(app)

        # Create config with module disabled
        yaml_content = """
modules:
  test_module:
    enabled: false
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            # Initialize registry
            get_registry(config_path=temp_path)

            # Request should return 503
            response = client.get("/test-endpoint")
            assert response.status_code == 503

            data = response.json()
            # The detail field contains our error info
            detail = data.get("detail", data)
            assert detail["error_code"] == "MODULE_DISABLED"
            assert "test_module" in detail["message"]
        finally:
            os.unlink(temp_path)

    def test_enabled_module_returns_200(self):
        """Test that enabled module allows request through"""
        from fastapi import FastAPI, Depends
        from fastapi.testclient import TestClient
        from api.dependencies import require_module

        app = FastAPI()

        @app.get("/test-endpoint")
        async def test_endpoint(_: None = Depends(require_module("test_module"))):
            return {"status": "ok"}

        client = TestClient(app)

        yaml_content = """
modules:
  test_module:
    enabled: true
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            get_registry(config_path=temp_path)

            response = client.get("/test-endpoint")
            assert response.status_code == 200
            assert response.json() == {"status": "ok"}
        finally:
            os.unlink(temp_path)

    def test_env_override_blocks_route(self):
        """Test that env var override can block a route"""
        from fastapi import FastAPI, Depends
        from fastapi.testclient import TestClient
        from api.dependencies import require_module

        app = FastAPI()

        @app.get("/test-endpoint")
        async def test_endpoint(_: None = Depends(require_module("test_module"))):
            return {"status": "ok"}

        client = TestClient(app)

        # Module enabled in YAML
        yaml_content = """
modules:
  test_module:
    enabled: true
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            # But disabled via env var
            os.environ["MODULE_TEST_MODULE"] = "0"

            get_registry(config_path=temp_path)

            # Should be blocked due to env override
            response = client.get("/test-endpoint")
            assert response.status_code == 503
        finally:
            os.unlink(temp_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
