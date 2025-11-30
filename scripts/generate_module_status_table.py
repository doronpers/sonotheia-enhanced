#!/usr/bin/env python3
"""
Generate Module Status Table

Fetches module status from the API and generates a markdown table fragment.
This script can be run locally or in CI to update MODULE_STATUS_FRAGMENT.md.

Usage:
    python scripts/generate_module_status_table.py [--api-url URL] [--output FILE]

Environment variables:
    API_BASE_URL: Base URL for the API (default: http://localhost:8000)
    API_KEY: API key for admin endpoints (optional in demo mode)
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from typing import Optional
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError


# Table format markers
TABLE_START_MARKER = "<!-- MODULE_STATUS_TABLE_START -->"
TABLE_END_MARKER = "<!-- MODULE_STATUS_TABLE_END -->"


def fetch_modules(api_url: str, api_key: Optional[str] = None) -> dict:
    """
    Fetch module status from the API.

    Args:
        api_url: Base URL for the API
        api_key: Optional API key for admin endpoints

    Returns:
        JSON response from /api/admin/modules endpoint

    Raises:
        Exception: If API request fails
    """
    url = f"{api_url}/api/admin/modules"
    headers = {"Accept": "application/json"}

    if api_key:
        headers["X-API-Key"] = api_key

    try:
        req = Request(url, headers=headers)
        with urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode())
    except HTTPError as e:
        raise Exception(f"HTTP Error {e.code}: {e.reason}") from e
    except URLError as e:
        raise Exception(f"URL Error: {e.reason}") from e


def generate_table(modules_data: dict) -> str:
    """
    Generate markdown table from module data.

    Args:
        modules_data: Response from /api/admin/modules endpoint

    Returns:
        Markdown table string

    Required columns:
    - Module
    - Configured
    - Effective
    - Last Change (UTC)
    - Last Recheck (UTC)
    - Reason
    """
    lines = []

    # Table header
    lines.append(
        "| Module | Configured | Effective | Last Change (UTC) | Last Recheck (UTC) | Reason |"
    )
    lines.append(
        "|--------|-----------|-----------|-------------------|--------------------|--------|"
    )

    # Get last health recheck timestamp
    last_recheck = modules_data.get("last_health_recheck", "N/A")

    # Table rows
    for module in modules_data.get("modules", []):
        name = module.get("name", "unknown")
        configured = "✅" if module.get("configured_enabled", True) else "❌"
        effective = "✅" if module.get("effective_enabled", True) else "❌"
        last_change = module.get("last_effective_change") or "N/A"
        reason = module.get("reason", "unknown")

        lines.append(
            f"| {name} | {configured} | {effective} | {last_change} | {last_recheck} | {reason} |"
        )

    return "\n".join(lines)


def generate_fragment(modules_data: dict) -> str:
    """
    Generate the complete markdown fragment with markers.

    Args:
        modules_data: Response from /api/admin/modules endpoint

    Returns:
        Complete markdown fragment with table and metadata
    """
    table = generate_table(modules_data)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    profile = modules_data.get("profile", "unknown")
    total = modules_data.get("total", 0)
    enabled = modules_data.get("enabled_count", 0)
    disabled = modules_data.get("disabled_count", 0)

    lines = [
        TABLE_START_MARKER,
        "",
        "## Module Status",
        "",
        f"**Profile:** {profile} | **Total:** {total} | **Enabled:** {enabled} | **Disabled:** {disabled}",
        "",
        f"*Last generated: {timestamp}*",
        "",
        table,
        "",
        TABLE_END_MARKER,
    ]

    return "\n".join(lines)


def validate_table(fragment: str) -> list:
    """
    Validate that the generated table has all required columns.

    Args:
        fragment: Generated markdown fragment

    Returns:
        List of missing columns (empty if valid)
    """
    required_columns = [
        "Module",
        "Configured",
        "Effective",
        "Last Change (UTC)",
        "Last Recheck (UTC)",
        "Reason",
    ]

    # Find the header line
    for line in fragment.split("\n"):
        if line.startswith("|") and "Module" in line:
            missing = [col for col in required_columns if col not in line]
            return missing

    return required_columns  # All missing if no header found


def main():
    parser = argparse.ArgumentParser(
        description="Generate module status markdown table"
    )
    parser.add_argument(
        "--api-url",
        default=os.environ.get("API_BASE_URL", "http://localhost:8000"),
        help="Base URL for the API",
    )
    parser.add_argument(
        "--api-key",
        default=os.environ.get("API_KEY"),
        help="API key for admin endpoints",
    )
    parser.add_argument(
        "--output",
        default="MODULE_STATUS_FRAGMENT.md",
        help="Output file path",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate existing file, don't regenerate",
    )
    parser.add_argument(
        "--mock-data",
        action="store_true",
        help="Use mock data instead of fetching from API",
    )

    args = parser.parse_args()

    # Mock data for testing without running API
    mock_modules_data = {
        "modules": [
            {
                "name": "audio",
                "configured_enabled": True,
                "effective_enabled": True,
                "description": "Core audio processing",
                "last_effective_change": None,
                "reason": "configured",
            },
            {
                "name": "detection",
                "configured_enabled": True,
                "effective_enabled": True,
                "description": "Deepfake detection",
                "last_effective_change": None,
                "reason": "configured",
            },
            {
                "name": "calibration",
                "configured_enabled": False,
                "effective_enabled": False,
                "description": "Audio calibration",
                "last_effective_change": "2025-01-15T10:30:00Z",
                "reason": "configured",
            },
        ],
        "total": 3,
        "enabled_count": 2,
        "disabled_count": 1,
        "profile": "standard",
        "last_health_recheck": "2025-01-15T12:00:00Z",
    }

    try:
        if args.validate_only:
            # Read existing file and validate
            try:
                with open(args.output, "r") as f:
                    content = f.read()
                missing = validate_table(content)
                if missing:
                    print(f"ERROR: Missing required columns: {missing}", file=sys.stderr)
                    sys.exit(1)
                print(f"Validation passed: {args.output}")
                sys.exit(0)
            except FileNotFoundError:
                print(f"ERROR: File not found: {args.output}", file=sys.stderr)
                sys.exit(1)

        # Fetch or use mock data
        if args.mock_data:
            print("Using mock data")
            modules_data = mock_modules_data
        else:
            print(f"Fetching modules from {args.api_url}")
            modules_data = fetch_modules(args.api_url, args.api_key)

        # Generate fragment
        fragment = generate_fragment(modules_data)

        # Validate
        missing = validate_table(fragment)
        if missing:
            print(f"ERROR: Generated table missing columns: {missing}", file=sys.stderr)
            sys.exit(1)

        # Write output
        with open(args.output, "w") as f:
            f.write(fragment)

        print(f"Generated {args.output}")
        print(f"  Total modules: {modules_data.get('total', 0)}")
        print(f"  Enabled: {modules_data.get('enabled_count', 0)}")
        print(f"  Disabled: {modules_data.get('disabled_count', 0)}")

    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
