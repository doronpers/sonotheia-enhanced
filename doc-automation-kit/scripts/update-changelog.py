#!/usr/bin/env python3
"""
Auto-update CHANGELOG.md based on recent commits.
"""

import sys
import subprocess
from datetime import datetime
from pathlib import Path

def get_recent_commits(since_days: int = 7) -> list:
    """Get commits from the last N days."""
    try:
        result = subprocess.run(
            ['git', 'log', f'--since={since_days}.days.ago', '--pretty=format:%H|%s|%an|%ad', '--date=short'],
            capture_output=True,
            text=True,
            check=True
        )
        
        commits = []
        for line in result.stdout.strip().split('\n'):
            if line:
                hash_, subject, author, date = line.split('|')
                commits.append({
                    'hash': hash_[:7],
                    'subject': subject,
                    'author': author,
                    'date': date
                })
        
        return commits
    except subprocess.CalledProcessError:
    except (subprocess.CalledProcessError, FileNotFoundError):

def categorize_commit(subject: str) -> str:
    """Categorize commit by type."""
    subject_lower = subject.lower()
    
    if any(word in subject_lower for word in ['fix', 'bug', 'issue']):
        return 'Fixed'
    elif any(word in subject_lower for word in ['add', 'new', 'feature', 'implement']):
        return 'Added'
    elif any(word in subject_lower for word in ['update', 'improve', 'enhance', 'refactor']):
        return 'Changed'
    elif any(word in subject_lower for word in ['remove', 'delete']):
        return 'Removed'
    elif any(word in subject_lower for word in ['doc', 'readme']):
        return 'Documentation'
    elif any(word in subject_lower for word in ['test']):
        return 'Testing'
    else:
        return 'Other'

def update_changelog(commits: list) -> None:
    """Update CHANGELOG.md with new commits."""
    changelog_path = Path('CHANGELOG.md')
    
    if not changelog_path.exists():
        print("⚠️  CHANGELOG.md not found")
        return
    
    with open(changelog_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Group commits by category
    categorized = {}
    for commit in commits:
        category = categorize_commit(commit['subject'])
        if category not in categorized:
            categorized[category] = []
        categorized[category].append(commit)
    
    # Generate new section
    today = datetime.now().strftime('%Y-%m-%d')
    new_section = f"\n## [Unreleased] - {today}\n\n"
    
    for category in ['Added', 'Changed', 'Fixed', 'Removed', 'Documentation', 'Testing', 'Other']:
        if category in categorized:
            new_section += f"### {category}\n\n"
            for commit in categorized[category]:
                new_section += f"- {commit['subject']} ({commit['hash']})\n"
            new_section += "\n"
    
    # Insert after the first heading
    lines = content.split('\n')
    insert_pos = 0
    for i, line in enumerate(lines):
        if line.startswith('## '):
            insert_pos = i
            break
    
    # Check if there's already an Unreleased section
    if insert_pos > 0 and 'Unreleased' in lines[insert_pos]:
        print("⚠️  Unreleased section already exists. Skipping update.")
        return
    
    # Insert new section
    new_lines = lines[:insert_pos] + new_section.split('\n') + lines[insert_pos:]
    
    with open(changelog_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))
    
    print(f"✓ Updated CHANGELOG.md with {len(commits)} recent commits")

def main():
    """Main changelog update function."""
    print("📝 Updating CHANGELOG.md...\n")
    
    commits = get_recent_commits(since_days=7)
    
    if not commits:
        print("No recent commits found")
        return 0
    
    print(f"Found {len(commits)} commits from the last 7 days")
    update_changelog(commits)
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
