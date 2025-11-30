#!/usr/bin/env python3
"""
CI Readiness Verification Script

This script performs operability checks to verify that the Sonotheia Enhanced
backend is properly configured before merging PRs.

Checks performed:
1. GET /api/admin/modules → Verify endpoint returns configured vs effective states
2. GET /metrics → Verify sonotheia_module_enabled{name="..."} metrics exist

Usage:
    # Run against local dev server (default http://localhost:8000)
    python scripts/ci_verify_operability.py

    # Run against specific URL
    python scripts/ci_verify_operability.py --base-url http://localhost:8080

    # Run with admin API key
    python scripts/ci_verify_operability.py --api-key your-admin-key

    # Run in CI mode (non-zero exit on failure)
    python scripts/ci_verify_operability.py --ci

Exit codes:
    0 - All checks passed
    1 - One or more checks failed
    2 - Connection error (server not reachable)
"""

import argparse
import json
import re
import sys
from typing import Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def print_header(title: str) -> None:
    """Print a formatted header."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


def print_check(name: str, passed: bool, details: str = "") -> None:
    """Print check result with formatting."""
    status = "✓ PASS" if passed else "✗ FAIL"
    print(f"  [{status}] {name}")
    if details:
        for line in details.split("\n"):
            print(f"           {line}")


def check_admin_modules(
    base_url: str, api_key: Optional[str] = None
) -> tuple[bool, str]:
    """
    Check /api/admin/modules endpoint.

    Verifies:
    - Endpoint returns 200 status
    - Response contains 'modules' list
    - Each module has 'name', 'enabled' fields
    - Response includes 'profile' info
    - Total module count is reasonable (> 0)

    Returns:
        (passed, details) tuple
    """
    url = f"{base_url}/api/admin/modules"
    headers = {"Accept": "application/json"}
    if api_key:
        headers["X-API-Key"] = api_key

    try:
        req = Request(url, headers=headers)
        with urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))

        # Validate response structure
        errors = []

        if "modules" not in data:
            errors.append("Missing 'modules' key in response")
        else:
            modules = data["modules"]
            if not isinstance(modules, list):
                errors.append("'modules' is not a list")
            elif len(modules) == 0:
                errors.append("'modules' list is empty")
            else:
                # Check first module structure
                sample_module = modules[0]
                if "name" not in sample_module:
                    errors.append("Module missing 'name' field")
                if "enabled" not in sample_module:
                    errors.append("Module missing 'enabled' field")

        if "profile" not in data:
            errors.append("Missing 'profile' key in response")

        if "total" not in data:
            errors.append("Missing 'total' key in response")
        elif data["total"] <= 0:
            errors.append(f"Invalid total count: {data['total']}")

        if "enabled_count" not in data:
            errors.append("Missing 'enabled_count' key")

        if "disabled_count" not in data:
            errors.append("Missing 'disabled_count' key")

        if errors:
            return False, "\n".join(errors)

        # Build success details
        details = f"Profile: {data['profile']}\n"
        details += f"Total: {data['total']} modules "
        details += f"({data['enabled_count']} enabled, {data['disabled_count']} disabled)"
        return True, details

    except HTTPError as e:
        if e.code == 403:
            return False, "HTTP 403 Forbidden - Admin API key may be required"
        return False, f"HTTP {e.code}: {e.reason}"
    except URLError as e:
        return False, f"Connection error: {e.reason}"
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON response: {e}"
    except Exception as e:
        return False, f"Unexpected error: {e}"


def check_metrics_endpoint(base_url: str) -> tuple[bool, str]:
    """
    Check /metrics endpoint for Prometheus metrics.

    Verifies:
    - Endpoint returns 200 status
    - Response contains sonotheia_module_enabled gauge
    - Metric has at least one module label

    Returns:
        (passed, details) tuple
    """
    url = f"{base_url}/metrics"
    headers = {"Accept": "text/plain"}

    try:
        req = Request(url, headers=headers)
        with urlopen(req, timeout=10) as response:
            metrics_text = response.read().decode("utf-8")

        # Look for module_enabled metrics
        # Pattern: sonotheia_module_enabled{name="modulename"} 0|1
        pattern = r'sonotheia_module_enabled\{name="([^"]+)"\}\s+(\d+(?:\.\d+)?)'
        matches = re.findall(pattern, metrics_text)

        if not matches:
            # Check if HELP/TYPE lines exist but no values
            if "sonotheia_module_enabled" in metrics_text:
                return False, "Metric defined but no module values found"
            return False, "sonotheia_module_enabled metric not found"

        # Categorize modules
        enabled_modules = [name for name, val in matches if float(val) >= 1]
        disabled_modules = [name for name, val in matches if float(val) < 1]

        details = f"Found {len(matches)} module metrics\n"
        if enabled_modules:
            details += f"Enabled: {', '.join(sorted(enabled_modules))}\n"
        if disabled_modules:
            details += f"Disabled: {', '.join(sorted(disabled_modules))}"

        return True, details.strip()

    except HTTPError as e:
        return False, f"HTTP {e.code}: {e.reason}"
    except URLError as e:
        return False, f"Connection error: {e.reason}"
    except Exception as e:
        return False, f"Unexpected error: {e}"


def check_health_endpoint(base_url: str) -> tuple[bool, str]:
    """
    Check /api/v1/health endpoint for basic connectivity.

    This is a prerequisite check to ensure the server is running.

    Returns:
        (passed, details) tuple
    """
    url = f"{base_url}/api/v1/health"
    headers = {"Accept": "application/json"}

    try:
        req = Request(url, headers=headers)
        with urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))

        status = data.get("status", "unknown")
        if status == "healthy":
            return True, f"Status: {status}"
        return False, f"Unexpected status: {status}"

    except HTTPError as e:
        return False, f"HTTP {e.code}: {e.reason}"
    except URLError as e:
        return False, f"Connection error: {e.reason}"
    except Exception as e:
        return False, f"Unexpected error: {e}"


def main() -> int:
    """Run CI verification checks."""
    parser = argparse.ArgumentParser(
        description="CI Readiness Verification for Sonotheia Enhanced",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="Base URL of the API server (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--api-key",
        help="Admin API key for protected endpoints",
    )
    parser.add_argument(
        "--ci",
        action="store_true",
        help="CI mode: exit with non-zero status on failure",
    )
    parser.add_argument(
        "--skip-health",
        action="store_true",
        help="Skip health check (useful if health endpoint differs)",
    )

    args = parser.parse_args()

    print_header("Sonotheia CI Operability Verification")
    print(f"  Target: {args.base_url}")

    all_passed = True
    checks_run = 0
    checks_passed = 0

    # 1. Health check (prerequisite)
    if not args.skip_health:
        print("\n[1/3] Health Check")
        passed, details = check_health_endpoint(args.base_url)
        print_check("Server health", passed, details)
        checks_run += 1
        if passed:
            checks_passed += 1
        else:
            all_passed = False
            if "Connection error" in details:
                print("\n  ! Server not reachable. Ensure the API is running.")
                print("    Try: uvicorn api.main:app --host 0.0.0.0 --port 8000")
                return 2  # Connection error exit code

    # 2. Admin modules endpoint
    print("\n[2/3] Module Registry Check")
    passed, details = check_admin_modules(args.base_url, args.api_key)
    print_check("GET /api/admin/modules", passed, details)
    checks_run += 1
    if passed:
        checks_passed += 1
    else:
        all_passed = False

    # 3. Prometheus metrics
    print("\n[3/3] Prometheus Metrics Check")
    passed, details = check_metrics_endpoint(args.base_url)
    print_check("GET /metrics (module gauges)", passed, details)
    checks_run += 1
    if passed:
        checks_passed += 1
    else:
        all_passed = False

    # Summary
    print_header("Summary")
    print(f"  Checks run: {checks_run}")
    print(f"  Checks passed: {checks_passed}")
    print(f"  Checks failed: {checks_run - checks_passed}")

    if all_passed:
        print("\n  ✓ All CI readiness checks PASSED")
        return 0
    else:
        print("\n  ✗ Some CI readiness checks FAILED")
        if args.ci:
            return 1
        print("  (Run with --ci flag to fail the build)")
        return 0


if __name__ == "__main__":
    sys.exit(main())
