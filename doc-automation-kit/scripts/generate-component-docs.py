#!/usr/bin/env python3
"""
Auto-generate component documentation from source code.
"""

import os
import sys
import re
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

def extract_react_component_info(file_path: Path) -> Dict[str, Any]:
    """Extract React component information."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    info = {
        'name': file_path.stem,
        'description': '',
        'props': [],
        'path': str(file_path)
    }
    
    # Look for component description in comments
    desc_match = re.search(r'/\*\*\s*\n\s*\*\s*(.*?)\s*\n\s*\*/', content, re.DOTALL)
    if desc_match:
        info['description'] = desc_match.group(1).replace('\n * ', ' ').strip()
    
    # Look for function component with props
    func_match = re.search(r'function\s+(\w+)\s*\(\s*\{([^}]+)\}\s*\)', content)
    if func_match:
        info['name'] = func_match.group(1)
        props_str = func_match.group(2)
        props = [p.strip() for p in props_str.split(',')]
        info['props'] = props
    else:
        # Look for arrow function component
        arrow_match = re.search(r'const\s+(\w+)\s*=\s*\(\s*\{([^}]+)\}\s*\)', content)
        if arrow_match:
            info['name'] = arrow_match.group(1)
            props_str = arrow_match.group(2)
            props = [p.strip() for p in props_str.split(',')]
            info['props'] = props
    
    return info

def extract_python_class_info(file_path: Path) -> List[Dict[str, Any]]:
    """Extract Python class information."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    classes = []
    
    # Find class definitions
    class_pattern = r'class\s+(\w+).*?:\s*\n\s*"""(.*?)"""'
    matches = re.finditer(class_pattern, content, re.DOTALL)
    
    for match in matches:
        class_name = match.group(1)
        docstring = match.group(2).strip()
        
        classes.append({
            'name': class_name,
            'description': docstring,
            'path': str(file_path)
        })
    
    return classes

def find_components(root_dir: str) -> Dict[str, List[Any]]:
    """Find all components in the project."""
    components = {
        'react': [],
        'python': []
    }
    
    # Find React components
    frontend_components = Path(root_dir) / 'frontend' / 'src' / 'components'
    if frontend_components.exists():
        for jsx_file in frontend_components.glob('*.jsx'):
            info = extract_react_component_info(jsx_file)
            components['react'].append(info)
    
    # Find Python classes in backend
    backend_path = Path(root_dir) / 'backend'
    if backend_path.exists():
        for py_file in backend_path.rglob('*.py'):
            if '__pycache__' not in str(py_file):
                classes = extract_python_class_info(py_file)
                components['python'].extend(classes)
    
    return components

def generate_component_markdown(components: Dict[str, List[Any]]) -> str:
    """Generate markdown for components."""
    md = ""
    
    # React components
    if components['react']:
        md += "## React Components\n\n"
        for comp in components['react']:
            md += f"### {comp['name']}\n\n"
            if comp['description']:
                md += f"{comp['description']}\n\n"
            
            if comp['props']:
                md += "**Props:**\n"
                for prop in comp['props']:
                    md += f"- `{prop}`\n"
                md += "\n"
            
            md += f"**File:** `{comp['path']}`\n\n"
    
    # Python classes
    if components['python']:
        md += "## Python Classes\n\n"
        for cls in components['python']:
            md += f"### {cls['name']}\n\n"
            md += f"{cls['description']}\n\n"
            md += f"**File:** `{cls['path']}`\n\n"
    
    return md

def main():
    """Main component documentation generation."""
    root_dir = os.getcwd()
    
    print("🧩 Generating component documentation...\n")
    
    # Create docs directory
    docs_dir = Path(root_dir) / 'docs'
    docs_dir.mkdir(exist_ok=True)
    
    # Find components
    components = find_components(root_dir)
    
    total = len(components['react']) + len(components['python'])
    
    if total > 0:
        md_content = f"""# Component Reference (Auto-Generated)

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

**Note:** This documentation is automatically generated from code docstrings and comments.

{generate_component_markdown(components)}

---

*This file is auto-generated. Manual edits may be overwritten.*
"""
        
        output_file = docs_dir / 'components.md'
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        print(f"\n✓ Generated documentation: {output_file}")
        print(f"  Found {len(components['react'])} React components")
        print(f"  Found {len(components['python'])} Python classes")
    else:
        print("\n⚠️  No components found")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
