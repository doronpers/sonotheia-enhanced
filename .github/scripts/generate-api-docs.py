#!/usr/bin/env python3
"""
Auto-generate API documentation from FastAPI routes and docstrings.
"""

import os
import sys
import ast
import re
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

def extract_route_info(file_path: Path) -> List[Dict[str, Any]]:
    """Extract route information from FastAPI file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    routes = []
    
    # Parse the file
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return routes
    
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            # Check for FastAPI decorators
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Call):
                    if hasattr(decorator.func, 'attr'):
                        method = decorator.func.attr
                        if method in ['get', 'post', 'put', 'delete', 'patch']:
                            # Get the route path
                            if decorator.args:
                                if isinstance(decorator.args[0], ast.Constant):
                                    path = decorator.args[0].value
                                    
                                    # Get docstring
                                    docstring = ast.get_docstring(node) or "No description"
                                    
                                    # Get parameters
                                    params = []
                                    for arg in node.args.args:
                                        if arg.arg not in ['self', 'request', 'background_tasks']:
                                            params.append(arg.arg)
                                    
                                    routes.append({
                                        'method': method.upper(),
                                        'path': path,
                                        'function': node.name,
                                        'docstring': docstring,
                                        'params': params
                                    })
    
    return routes

def find_api_files(root_dir: str) -> List[Path]:
    """Find all API files."""
    api_files = []
    backend_api = Path(root_dir) / 'backend' / 'api'
    
    if backend_api.exists():
        for py_file in backend_api.rglob('*.py'):
            if py_file.name != '__init__.py':
                api_files.append(py_file)
    
    return api_files

def generate_api_markdown(routes: List[Dict[str, Any]]) -> str:
    """Generate markdown for API routes."""
    if not routes:
        return ""
    
    md = "\n## Endpoints\n\n"
    
    # Group by path prefix
    grouped = {}
    for route in routes:
        prefix = route['path'].split('/')[1] if route['path'].startswith('/') else 'root'
        if prefix not in grouped:
            grouped[prefix] = []
        grouped[prefix].append(route)
    
    for prefix, routes_list in sorted(grouped.items()):
        md += f"### /{prefix}\n\n"
        
        for route in routes_list:
            md += f"#### `{route['method']} {route['path']}`\n\n"
            md += f"{route['docstring']}\n\n"
            
            if route['params']:
                md += "**Parameters:**\n"
                for param in route['params']:
                    md += f"- `{param}`\n"
                md += "\n"
    
    return md

def main():
    """Main documentation generation function."""
    root_dir = os.getcwd()
    
    print("🔧 Generating API documentation...\n")
    
    # Create docs directory
    docs_dir = Path(root_dir) / 'docs'
    docs_dir.mkdir(exist_ok=True)
    
    # Find and process API files
    api_files = find_api_files(root_dir)
    all_routes = []
    
    for api_file in api_files:
        print(f"  Processing {api_file.name}...")
        routes = extract_route_info(api_file)
        all_routes.extend(routes)
    
    # Generate markdown
    if all_routes:
        md_content = f"""# API Reference (Auto-Generated)

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

**Note:** This documentation is automatically generated from code. For the main API documentation, see [API.md](../API.md).

{generate_api_markdown(all_routes)}

---

*This file is auto-generated. Manual edits may be overwritten.*
"""
        
        output_file = docs_dir / 'api-reference.md'
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        print(f"\n✓ Generated documentation: {output_file}")
        print(f"  Found {len(all_routes)} endpoints")
    else:
        print("\n⚠️  No API routes found")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
