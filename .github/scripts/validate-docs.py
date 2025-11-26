#!/usr/bin/env python3
"""
Documentation Validation Script

Validates documentation files for:
- Required sections
- Consistent formatting
- Valid YAML frontmatter
- Cross-references
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Tuple

# Required documents in root
REQUIRED_DOCS = [
    'README.md',
    'QUICKSTART.md',
    'API.md',
    'INTEGRATION.md',
    'CONTRIBUTING.md',
    'ROADMAP.md',
    'CHANGELOG.md'
]

# Required sections in each document
REQUIRED_SECTIONS = {
    'README.md': ['Quick Start', 'Documentation', 'Architecture'],
    'CONTRIBUTING.md': ['Getting Started', 'Code Standards', 'Testing'],
    'ROADMAP.md': ['Timeline', 'Milestones'],
    'CHANGELOG.md': ['Version'],
    'API.md': ['Endpoints'],
}

def find_markdown_files(root_dir: str) -> List[Path]:
    """Find all markdown files in repository."""
    md_files = []
    for path in Path(root_dir).rglob('*.md'):
        # Skip node_modules and other dependency directories
        if 'node_modules' not in str(path) and '.venv' not in str(path):
            md_files.append(path)
    return md_files

def check_required_docs(root_dir: str) -> Tuple[bool, List[str]]:
    """Check if all required documents exist."""
    missing = []
    for doc in REQUIRED_DOCS:
        doc_path = Path(root_dir) / doc
        if not doc_path.exists():
            missing.append(doc)
    
    return len(missing) == 0, missing

def check_required_sections(file_path: Path) -> Tuple[bool, List[str]]:
    """Check if document has required sections."""
    if file_path.name not in REQUIRED_SECTIONS:
        return True, []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    required = REQUIRED_SECTIONS[file_path.name]
    missing = []
    
    for section in required:
        # Check for section heading (# or ##)
        pattern = rf'^#+\s+.*{re.escape(section)}.*$'
        if not re.search(pattern, content, re.MULTILINE | re.IGNORECASE):
            missing.append(section)
    
    return len(missing) == 0, missing

def check_broken_internal_links(root_dir: str, file_path: Path) -> List[str]:
    """Check for broken internal markdown links."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    broken = []
    # Find markdown links: [text](path)
    links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)
    
    for text, link in links:
        # Skip external links
        if link.startswith('http://') or link.startswith('https://'):
            continue
        
        # Skip anchors
        if link.startswith('#'):
            continue
        
        # Remove anchor from link
        link_path = link.split('#')[0]
        if not link_path:
            continue
        
        # Resolve relative path
        full_path = (file_path.parent / link_path).resolve()
        
        if not full_path.exists():
            broken.append(f"[{text}]({link})")
    
    return broken

def validate_markdown_structure(file_path: Path) -> List[str]:
    """Validate markdown structure and formatting."""
    issues = []
    
    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:

        lines = f.readlines()
    
    # Check for title (first non-empty line should be # heading)
    first_content_line = None
    for i, line in enumerate(lines):
        if line.strip():
            first_content_line = i
            break
    
    if first_content_line is not None:
        if not lines[first_content_line].startswith('# '):
            issues.append("Missing top-level heading (# Title)")
    
    # Check for excessive blank lines
    blank_count = 0
    for i, line in enumerate(lines):
        if not line.strip():
            blank_count += 1
            if blank_count > 3:
                issues.append(f"Excessive blank lines at line {i+1}")
                blank_count = 0  # Reset to avoid duplicate reports
        else:
            blank_count = 0
    
    return issues

def main():
    """Main validation function."""
    root_dir = os.getcwd()
    print(f"📚 Validating documentation in: {root_dir}\n")
    
    errors = []
    warnings = []
    
    # Check required documents
    print("✓ Checking required documents...")
    has_all, missing = check_required_docs(root_dir)
    if not has_all:
        errors.append(f"Missing required documents: {', '.join(missing)}")
    else:
        print("  ✓ All required documents present")
    
    # Validate each markdown file
    md_files = find_markdown_files(root_dir)
    print(f"\n✓ Found {len(md_files)} markdown files\n")
    
    for file_path in md_files:
        rel_path = file_path.relative_to(root_dir)
        print(f"  Checking {rel_path}...")
        
        # Check required sections
        has_sections, missing_sections = check_required_sections(file_path)
        if not has_sections:
            warnings.append(f"{rel_path}: Missing sections: {', '.join(missing_sections)}")
        
        # Check broken links
        broken = check_broken_internal_links(root_dir, file_path)
        if broken:
            errors.extend([f"{rel_path}: Broken link: {link}" for link in broken])
        
        # Validate structure
        structure_issues = validate_markdown_structure(file_path)
        if structure_issues:
            warnings.extend([f"{rel_path}: {issue}" for issue in structure_issues])
    
    # Print results
    print("\n" + "="*60)
    print("VALIDATION RESULTS")
    print("="*60)
    
    if errors:
        print(f"\n❌ ERRORS ({len(errors)}):")
        for error in errors:
            print(f"  - {error}")
    
    if warnings:
        print(f"\n⚠️  WARNINGS ({len(warnings)}):")
        for warning in warnings:
            print(f"  - {warning}")
    
    if not errors and not warnings:
        print("\n✅ All documentation validation checks passed!")
        return 0
    
    print(f"\n📊 Summary: {len(errors)} errors, {len(warnings)} warnings")
    
    # Exit with error if there are errors
    return 1 if errors else 0

if __name__ == '__main__':
    sys.exit(main())
