"""
Script to download Bible versions from the arron-taylor/bible-versions repository.
Downloads JSON files for English Bible translations.
"""

import os
import json
import urllib.request
import urllib.error
from pathlib import Path
from typing import List, Optional

# GitHub API base URL for the repo
REPO_API_BASE = "https://api.github.com/repos/arron-taylor/bible-versions/contents/versions/en"
RAW_BASE = "https://raw.githubusercontent.com/arron-taylor/bible-versions/main/versions/en"

# Default directory to store Bible JSON files
BIBLE_JSON_DIR = Path(__file__).parent / "bible-data" / "json"

# Popular versions to download by default (these are commonly used)
DEFAULT_VERSIONS = [
    "KING JAMES BIBLE.json",
    "ENGLISH STANDARD VERSION.json",
    "NEW INTERNATIONAL VERSION.json",
    "NEW LIVING TRANSLATION.json",
    "NEW AMERICAN STANDARD BIBLE.json",
    "NEW KING JAMES VERSION.json",
    "CHRISTIAN STANDARD BIBLE.json",
    "AMERICAN STANDARD VERSION.json",
    "WORLD ENGLISH BIBLE.json",
]

# Short name mapping for convenience
VERSION_SHORT_NAMES = {
    "KING JAMES BIBLE.json": "kjv",
    "ENGLISH STANDARD VERSION.json": "esv",
    "NEW INTERNATIONAL VERSION.json": "niv",
    "NEW LIVING TRANSLATION.json": "nlt",
    "NEW AMERICAN STANDARD BIBLE.json": "nasb",
    "NEW KING JAMES VERSION.json": "nkjv",
    "CHRISTIAN STANDARD BIBLE.json": "csb",
    "AMERICAN STANDARD VERSION.json": "asv",
    "WORLD ENGLISH BIBLE.json": "web",
    "BEREAN STANDARD BIBLE.json": "bsb",
    "BEREAN LITERAL BIBLE.json": "blb",
    "NET BIBLE.json": "net",
    "GOOD NEWS TRANSLATION.json": "gnt",
    "CONTEMPORARY ENGLISH VERSION.json": "cev",
    "NEW REVISED STANDARD VERSION.json": "nrsv",
    "HOLMAN CHRISTIAN STANDARD BIBLE.json": "hcsb",
    "AMPLIFIED BIBLE.json": "amp",
    "NASB 1995.json": "nasb95",
    "NASB 1977.json": "nasb77",
    "YOUNG'S LITERAL TRANSLATION.json": "ylt",
    "DOUAY-RHEIMS BIBLE.json": "drb",
    "LITERAL STANDARD VERSION.json": "lsv",
    "LEGACY STANDARD BIBLE.json": "lsb",
    "MAJORITY STANDARD BIBLE.json": "msb",
}


def get_available_versions() -> List[str]:
    """Fetch list of available Bible versions from GitHub."""
    try:
        req = urllib.request.Request(
            REPO_API_BASE,
            headers={"User-Agent": "WWAIJD-Bible-Downloader"}
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode())
            return [item["name"] for item in data if item["name"].endswith(".json")]
    except Exception as e:
        print(f"Error fetching version list: {e}")
        return []


def download_version(filename: str, output_dir: Path = BIBLE_JSON_DIR) -> bool:
    """
    Download a specific Bible version.
    
    Args:
        filename: The JSON filename (e.g., "KING JAMES BIBLE.json")
        output_dir: Directory to save the file
        
    Returns:
        True if successful, False otherwise
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Use short name if available, otherwise sanitize the full name
    short_name = VERSION_SHORT_NAMES.get(filename)
    if short_name:
        output_filename = f"{short_name}.json"
    else:
        # Sanitize filename: lowercase, replace spaces with underscores
        output_filename = filename.lower().replace(" ", "_").replace("'", "").replace("®", "")
    
    output_path = output_dir / output_filename
    
    # URL encode the filename for the request
    encoded_filename = urllib.parse.quote(filename)
    url = f"{RAW_BASE}/{encoded_filename}"
    
    try:
        print(f"  Downloading {filename}...")
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "WWAIJD-Bible-Downloader"}
        )
        with urllib.request.urlopen(req, timeout=120) as response:
            data = response.read()
            
            # Validate JSON
            json.loads(data.decode('utf-8'))
            
            # Save to file
            with open(output_path, 'wb') as f:
                f.write(data)
                
        print(f"  ✅ Saved as {output_filename}")
        return True
        
    except urllib.error.HTTPError as e:
        print(f"  ❌ HTTP Error {e.code}: {filename}")
        return False
    except json.JSONDecodeError:
        print(f"  ❌ Invalid JSON: {filename}")
        return False
    except Exception as e:
        print(f"  ❌ Error downloading {filename}: {e}")
        return False


def download_all_versions(output_dir: Path = BIBLE_JSON_DIR) -> int:
    """Download all available Bible versions."""
    versions = get_available_versions()
    if not versions:
        print("Could not fetch version list from GitHub.")
        return 0
    
    print(f"Found {len(versions)} versions available")
    success_count = 0
    
    for filename in versions:
        if download_version(filename, output_dir):
            success_count += 1
            
    return success_count


def download_default_versions(output_dir: Path = BIBLE_JSON_DIR) -> int:
    """Download only the popular/default Bible versions."""
    print(f"Downloading {len(DEFAULT_VERSIONS)} popular Bible versions...")
    success_count = 0
    
    for filename in DEFAULT_VERSIONS:
        if download_version(filename, output_dir):
            success_count += 1
            
    return success_count


def list_local_versions(bible_dir: Path = BIBLE_JSON_DIR) -> List[str]:
    """List locally available Bible versions."""
    if not bible_dir.exists():
        return []
    return sorted([f.stem for f in bible_dir.glob("*.json")])


def main():
    """Main function to download Bible versions."""
    import argparse
    
    # Need to import urllib.parse for URL encoding
    import urllib.parse
    
    parser = argparse.ArgumentParser(description="Download Bible versions from GitHub")
    parser.add_argument(
        "--all", 
        action="store_true", 
        help="Download all available versions (35+ files, may take a while)"
    )
    parser.add_argument(
        "--list", 
        action="store_true", 
        help="List available versions from GitHub"
    )
    parser.add_argument(
        "--local", 
        action="store_true", 
        help="List locally downloaded versions"
    )
    parser.add_argument(
        "--version", 
        type=str, 
        help="Download a specific version by filename"
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default=str(BIBLE_JSON_DIR),
        help="Output directory for downloaded files"
    )
    
    args = parser.parse_args()
    output_dir = Path(args.output)
    
    print("=" * 60)
    print("Bible Version Downloader")
    print("Source: github.com/arron-taylor/bible-versions")
    print("=" * 60)
    
    if args.list:
        print("\nFetching available versions from GitHub...")
        versions = get_available_versions()
        if versions:
            print(f"\nAvailable versions ({len(versions)}):")
            for v in sorted(versions):
                short = VERSION_SHORT_NAMES.get(v, "")
                if short:
                    print(f"  - {v} ({short})")
                else:
                    print(f"  - {v}")
        return
    
    if args.local:
        versions = list_local_versions(output_dir)
        if versions:
            print(f"\nLocally available versions ({len(versions)}):")
            for v in versions:
                print(f"  - {v}")
        else:
            print("\nNo Bible versions downloaded yet.")
            print(f"Run 'python download_bibles.py' to download default versions.")
        return
    
    if args.version:
        # Download specific version
        # Need to import at top level for URL encoding
        download_version(args.version, output_dir)
        return
    
    if args.all:
        print("\nDownloading ALL available Bible versions...")
        print("This may take several minutes...\n")
        count = download_all_versions(output_dir)
        print(f"\n✅ Downloaded {count} Bible versions to {output_dir}")
    else:
        print("\nDownloading popular Bible versions...")
        count = download_default_versions(output_dir)
        print(f"\n✅ Downloaded {count} Bible versions to {output_dir}")
        print("\nRun with --all to download all 35+ versions")
    
    print(f"\nFiles saved to: {output_dir}")
    print("\nNext step: Run 'python build_embeddings.py' to create the vector database")


if __name__ == "__main__":
    # Import urllib.parse here since it's used in download_version
    import urllib.parse
    main()
