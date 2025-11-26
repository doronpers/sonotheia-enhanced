#!/usr/bin/env python3
"""
Check documentation completeness.
"""

import os
import sys
from pathlib import Path

def check_component_docs(root_dir: str) -> list:
    """Check that components have README files."""
    issues = []
    
    # Check backend components
    backend_dirs = [
        'backend/api',
        'backend/authentication',
        'backend/sar',
        'backend/config',
    ]
    
    for dir_path in backend_dirs:
        full_path = Path(root_dir) / dir_path
        if full_path.exists() and full_path.is_dir():
            readme = full_path / 'README.md'
            if not readme.exists():
                issues.append(f"Missing README.md in {dir_path}")
    
    # Check frontend components
    frontend_components = Path(root_dir) / 'frontend' / 'src' / 'components'
    if frontend_components.exists() and frontend_components.is_dir():
        readme = frontend_components / 'README.md'
        if not readme.is_file():
            issues.append(f"Missing README.md in frontend/src/components")
    
    return issues

def check_api_documentation(root_dir: str) -> list:
    """Check that API endpoints are documented."""
    issues = []
    api_md = Path(root_dir) / 'API.md'
    
    if not api_md.exists():
        issues.append("Missing API.md file")
        return issues

    if not api_md.is_file():
        issues.append("API.md is not a regular file")
        return issues

    try:
        with open(api_md, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
    except OSError as e:
        issues.append(f"Unable to read API.md: {e.__class__.__name__}")
        return issues
    
    # Check for common endpoints
    expected_endpoints = [
        '/api/authenticate',
        '/api/sar/generate',
        '/api/demo',
    ]
    
    for endpoint in expected_endpoints:
        if endpoint not in content:
            issues.append(f"API endpoint {endpoint} not documented in API.md")
    
    return issues

def main():
    """Main completeness check."""
    root_dir = os.getcwd()
    
    print("📋 Checking documentation completeness...\n")
    
    all_issues = []
    
    # Check component docs
    print("✓ Checking component documentation...")
    component_issues = check_component_docs(root_dir)
    all_issues.extend(component_issues)
    
    # Check API documentation
    print("✓ Checking API documentation...")
    api_issues = check_api_documentation(root_dir)
    all_issues.extend(api_issues)
    
    # Print results
    print("\n" + "="*60)
    print("COMPLETENESS CHECK RESULTS")
    print("="*60)
    
    if all_issues:
        print(f"\n⚠️  Found {len(all_issues)} completeness issues:\n")
        for issue in all_issues:
            print(f"  - {issue}")
        return 1
    else:
        print("\n✅ Documentation is complete!")
        return 0

if __name__ == '__main__':
    sys.exit(main())
