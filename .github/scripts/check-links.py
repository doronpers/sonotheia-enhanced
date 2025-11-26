#!/usr/bin/env python3
"""
Check for broken external links in documentation.
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed

def find_markdown_files(root_dir: str) -> List[Path]:
    """Find all markdown files."""
    md_files = []
    for path in Path(root_dir).rglob('*.md'):
        if 'node_modules' not in str(path) and '.venv' not in str(path):
            md_files.append(path)
    return md_files

def extract_links(file_path: Path) -> List[Tuple[str, str]]:
    """Extract all links from markdown file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    links = []
    # Markdown links: [text](url)
    md_links = re.findall(r'\[([^\]]+)\]\((https?://[^\s)]+)(?:\s+[^)]*)?\)', content)
    for text, url in md_links:
        if url.startswith('http://') or url.startswith('https://'):
            links.append((text, url))
    
    # Bare URLs
    bare_urls = re.findall(r'https?://[^\s<>"{}|\\^`\[\]]+', content)
    for url in bare_urls:
        links.append(('', url))
    
    return links

def check_link(url: str, timeout: int = 10) -> Tuple[str, bool, str]:
    """Check if a URL is accessible."""
    try:
        # Skip localhost URLs
        if 'localhost' in url or '127.0.0.1' in url:
            return url, True, "Skipped (localhost)"
        
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=timeout) as response:
            status = response.getcode()
            return url, status == 200, f"Status {status}"
    except urllib.error.HTTPError as e:
        return url, False, f"HTTP {e.code}"
    except urllib.error.URLError as e:
        return url, False, f"URL Error: {e.reason}"
    except Exception as e:
        return url, False, f"Error: {str(e)}"

def main():
    """Main link checking function."""
    import os
    root_dir = os.getcwd()
    
    print("🔗 Checking links in documentation...\n")
    
    md_files = find_markdown_files(root_dir)
    
    # Collect all unique links
    all_links = {}
    for file_path in md_files:
        rel_path = file_path.relative_to(root_dir)
        links = extract_links(file_path)
        for text, url in links:
            if url not in all_links:
                all_links[url] = []
            all_links[url].append((rel_path, text))
    
    print(f"Found {len(all_links)} unique external links\n")
    
    if not all_links:
        print("✅ No external links to check")
        return 0
    
    # Check links concurrently
    broken_links = []
    checked = 0
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(check_link, url): url for url in all_links.keys()}
        
        for future in as_completed(futures):
            url = futures[future]
            checked += 1
            try:
                url, is_ok, message = future.result()
                
                if not is_ok:
                    broken_links.append((url, message, all_links[url]))
                    print(f"  ❌ [{checked}/{len(all_links)}] {url} - {message}")
                else:
                    print(f"  ✓ [{checked}/{len(all_links)}] {url}")
            except Exception as e:
                broken_links.append((url, str(e), all_links[url]))
                print(f"  ❌ [{checked}/{len(all_links)}] {url} - {e}")
    
    # Print results
    print("\n" + "="*60)
    print("LINK CHECK RESULTS")
    print("="*60)
    
    if broken_links:
        print(f"\n❌ Found {len(broken_links)} broken links:\n")
        for url, message, locations in broken_links:
            print(f"  {url}")
            print(f"    Error: {message}")
            print(f"    Found in:")
            for file_path, text in locations:
                if text:
                    print(f"      - {file_path}: [{text}]")
                else:
                    print(f"      - {file_path}")
            print()
        return 1
    else:
        print(f"\n✅ All {len(all_links)} links are working!")
        return 0

if __name__ == '__main__':
    sys.exit(main())
