#!/usr/bin/env python3
"""
Check for outdated dates and version numbers in documentation.
"""

import re
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Tuple

def find_markdown_files(root_dir: str) -> List[Path]:
    """Find all markdown files."""
    md_files = []
    for path in Path(root_dir).rglob('*.md'):
        if 'node_modules' not in str(path) and '.venv' not in str(path):
            md_files.append(path)
    return md_files

def check_dates(file_path: Path) -> List[Tuple[int, str, str]]:
    """Check for potentially outdated dates."""
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    issues = []
    current_year = datetime.now().year
    
    for i, line in enumerate(lines, 1):
        # Look for date patterns
        date_patterns = [
            (r'Last Updated:\s*(\d{4}-\d{2}-\d{2})', 'Last Updated'),
            (r'Date:\s*(\d{4}-\d{2}-\d{2})', 'Date'),
            (r'Created:\s*(\d{4}-\d{2}-\d{2})', 'Created'),
            (r'Version.*?(\d{4}-\d{2}-\d{2})', 'Version date'),
            (r'\*\*(\d{4}-\d{2}-\d{2})\*\*', 'Bold date'),
            (r'Q[1-4]\s+(\d{4})', 'Quarter year'),
        ]
        
        for pattern, desc in date_patterns:
            matches = re.finditer(pattern, line, re.IGNORECASE)
            for match in matches:
                date_str = match.group(1)
                
                # Try to parse the date
                try:
                    if re.match(r'\d{4}$', date_str):  # Just year
                        year = int(date_str)
                        if year < current_year - 1:
                            issues.append((i, desc, f"Year {year} is more than 1 year old"))
                    else:  # Full date
                        date = datetime.strptime(date_str, '%Y-%m-%d')
                        age_days = (datetime.now() - date).days
                        
                        if age_days > 90:  # More than 3 months old
                            issues.append((i, desc, f"Date {date_str} is {age_days} days old"))
                except ValueError:
                    # Ignore lines that do not match the expected date format
                    pass
    
    return issues

def main():
    """Main date checking function."""
    import os
    root_dir = os.getcwd()
    
    print("📅 Checking for outdated dates in documentation...\n")
    
    md_files = find_markdown_files(root_dir)
    all_issues = {}
    
    for file_path in md_files:
        rel_path = file_path.relative_to(root_dir)
        issues = check_dates(file_path)
        
        if issues:
            all_issues[rel_path] = issues
    
    # Print results
    print("="*60)
    print("DATE CHECK RESULTS")
    print("="*60)
    
    if all_issues:
        print(f"\n⚠️  Found potentially outdated dates:\n")
        for file_path, issues in all_issues.items():
            print(f"  {file_path}:")
            for line_num, desc, message in issues:
                print(f"    Line {line_num}: {desc} - {message}")
        print(f"\n📊 Total: {sum(len(issues) for issues in all_issues.values())} outdated dates found")
        return 1
    else:
        print("\n✅ All dates appear current!")
        return 0

if __name__ == '__main__':
    sys.exit(main())
