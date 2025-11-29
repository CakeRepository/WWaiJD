"""
Utility helpers for working with Bible data.
Supports both JSON format (from arron-taylor/bible-versions) and legacy markdown files.
Shared between the embedding builder and the Flask application.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple, Optional, Dict, Any, Union

BIBLE_ROOT = Path("bible-data")
BIBLE_JSON_ROOT = BIBLE_ROOT / "json"

# Import JSON utilities for the new format
try:
    from json_bible_utils import (
        load_bible_json,
        get_available_versions as get_json_versions,
        get_books as get_json_books,
        get_chapters as get_json_chapters,
        get_verses as get_json_verses,
        get_verse as get_json_verse,
        get_verse_range as get_json_verse_range,
        get_testament as get_json_testament,
        normalize_book_name as normalize_json_book,
        build_bible_index as build_json_index,
        iter_chapters as iter_json_chapters,
        format_reference,
        BIBLE_JSON_ROOT as JSON_ROOT,
    )
    JSON_AVAILABLE = True
except ImportError:
    JSON_AVAILABLE = False

_VERSE_HEADER_RE = re.compile(r"^\s*##\s*(\d+)\.\s*$")
_ESV_VERSE_RE = re.compile(r"^(\d+)\.\s+(.*)$")
_CHAPTER_NUMBER_RE = re.compile(r"(\d+)")


def get_available_versions(bible_root: Path | str = BIBLE_ROOT) -> List[str]:
    """
    Return a list of available bible versions.
    Checks JSON directory first, then falls back to markdown directories.
    """
    versions = []
    
    # Check for JSON versions first (preferred)
    json_root = Path(bible_root) / "json"
    if json_root.exists():
        versions.extend([f.stem for f in json_root.glob("*.json")])
    
    # Also check for legacy markdown versions
    root = Path(bible_root)
    if root.exists():
        for d in root.iterdir():
            if d.is_dir() and d.name != "json" and (d / "Old Testament").exists():
                if d.name not in versions:
                    versions.append(d.name)
    
    return sorted(set(versions))


def is_json_version(version: str, bible_root: Path | str = BIBLE_ROOT) -> bool:
    """Check if a version exists as JSON."""
    json_path = Path(bible_root) / "json" / f"{version}.json"
    return json_path.exists()


def is_markdown_version(version: str, bible_root: Path | str = BIBLE_ROOT) -> bool:
    """Check if a version exists as markdown folders."""
    md_path = Path(bible_root) / version / "Old Testament"
    return md_path.exists()


def extract_book_name(folder_name: str) -> str:
    """
    Extract the book name from a folder name, stripping any numeric prefix.

    Args:
        folder_name: The name of the folder (e.g., "18 Job").

    Returns:
        str: The book name without the numeric prefix (e.g., "Job").
             If no prefix is found, returns the original name.
    """
    if not folder_name:
        return folder_name
    return folder_name.split(" ", 1)[1] if " " in folder_name else folder_name


def extract_chapter_number(file_path: Path | str) -> str:
    """
    Extract the chapter number from a file path or filename.

    Attempts to find the numeric suffix in the file stem (e.g., "job12.md" -> "12").
    Uses the last number found in the filename to handle books with numbers
    in their name (e.g., "1 Corinthians").

    Args:
        file_path: The file path or filename to parse.

    Returns:
        str: The extracted chapter number as a string.
             Returns "1" if no number is found.
    """
    stem = Path(file_path).stem
    # Find all numbers in the stem and take the last one (the chapter number)
    matches = _CHAPTER_NUMBER_RE.findall(stem)
    return matches[-1] if matches else "1"


def to_relative_source_path(file_path: Path, bible_dir: Path | str = BIBLE_ROOT) -> str:
    """
    Convert an absolute file path to a path relative to the Bible root directory.

    Args:
        file_path: The absolute path to the file.
        bible_dir: The root directory of the Bible data. Defaults to BIBLE_ROOT.

    Returns:
        str: The relative path as a POSIX string.
    """
    base = Path(bible_dir).resolve()
    absolute = Path(file_path).resolve()
    try:
        return absolute.relative_to(base).as_posix()
    except ValueError:
        # Fallback if not relative to base (e.g. different version)
        # Try to find relative path from the version root
        for parent in absolute.parents:
            if parent.parent == base:
                return absolute.relative_to(base).as_posix()
        raise


def _compact_lines(lines: Sequence[str]) -> str:
    """Join verse lines with spaces while removing empty fragments."""
    filtered = [line for line in lines if line]
    return " ".join(filtered).strip()

def parse_verses(markdown_text: str) -> List[Tuple[str, str]]:
    """
    Parse a markdown chapter into (verse_number, verse_text) tuples.
    Verses are identified by lines that look like '## 12.' (KJV)
    OR lines that start with '12. ' (ESV).
    """
    verses: List[Tuple[str, str]] = []
    verse_num: str | None = None
    current_lines: List[str] = []

    for raw_line in markdown_text.splitlines():
        clean_line = raw_line.strip("\ufeff\b")
        
        # Check for KJV style header: ## 1.
        header_match = _VERSE_HEADER_RE.match(clean_line.strip())
        
        # Check for ESV style verse: 1. In the beginning...
        esv_match = _ESV_VERSE_RE.match(clean_line.strip())
        
        if header_match:
            if verse_num is not None:
                verses.append((verse_num, _compact_lines(current_lines)))
            verse_num = header_match.group(1)
            current_lines = []
        elif esv_match:
            if verse_num is not None:
                verses.append((verse_num, _compact_lines(current_lines)))
            verse_num = esv_match.group(1)
            current_lines = [esv_match.group(2)]
        else:
            # Preserve meaningful whitespace but collapse excess gaps later.
            current_lines.append(clean_line.strip())

    if verse_num is not None:
        verses.append((verse_num, _compact_lines(current_lines)))

    return verses


def get_verses_for_chapter(
    version: str,
    book: str,
    chapter: int,
    bible_root: Path | str = BIBLE_ROOT
) -> List[Tuple[str, str]]:
    """
    Get verses for a chapter from either JSON or markdown source.
    Returns list of (verse_number, verse_text) tuples.
    """
    # Try JSON first
    json_root = Path(bible_root) / "json"
    if is_json_version(version, bible_root) and JSON_AVAILABLE:
        try:
            verses = get_json_verses(version, book, chapter, json_root)
            return [(str(v), text) for v, text in verses]
        except Exception as e:
            print(f"Warning: Could not load JSON verses: {e}")
    
    # Fall back to markdown
    if is_markdown_version(version, bible_root):
        # Need to find and parse markdown file
        md_path = Path(bible_root) / version
        normalized_book = normalize_book_name(book)
        
        for testament in ("Old Testament", "New Testament"):
            testament_dir = md_path / testament
            if not testament_dir.exists():
                continue
            
            for book_dir in testament_dir.iterdir():
                if not book_dir.is_dir():
                    continue
                folder_book = extract_book_name(book_dir.name)
                if normalize_book_name(folder_book) == normalized_book:
                    for chapter_file in book_dir.glob("*.md"):
                        file_chapter = extract_chapter_number(chapter_file)
                        if int(file_chapter) == chapter:
                            with open(chapter_file, 'r', encoding='utf-8') as f:
                                content = f.read()
                            return parse_verses(content)
    
    return []


def normalize_book_name(book: str) -> str:
    """
    Normalize a book name for comparison.
    Uses JSON normalizer if available, otherwise basic normalization.
    """
    if JSON_AVAILABLE:
        return normalize_json_book(book)
    
    # Basic normalization for legacy support
    if not book:
        return book
    return book.strip().lower()


def resolve_bible_path(relative_path: str, bible_dir: Path | str = BIBLE_ROOT) -> Path:
    """
    Resolve a relative Bible path to an absolute path, ensuring security.

    Prevents directory traversal attacks by checking if the resolved path
    is within the Bible directory.

    Args:
        relative_path: The relative path to resolve (e.g., 'Old Testament/18 Job/job1.md').
        bible_dir: The root directory of the Bible data. Defaults to BIBLE_ROOT.

    Returns:
        Path: The resolved absolute path.

    Raises:
        ValueError: If the path resolves to a location outside the Bible directory.
        FileNotFoundError: If the file does not exist.
    """
    base = Path(bible_dir).resolve()
    candidate = (base / Path(relative_path)).resolve()
    if not str(candidate).startswith(str(base)):
        raise ValueError("Invalid bible path provided.")
    if not candidate.exists():
        raise FileNotFoundError(f"Bible markdown not found: {relative_path}")
    return candidate


def build_bible_index(bible_dir: Path | str = BIBLE_ROOT, version: str = None):
    """
    Return a structured index of available testaments, books, and chapters.
    Uses JSON format if available, falls back to markdown.
    """
    if not version:
        return []
    
    bible_path = Path(bible_dir)
    json_root = bible_path / "json"
    
    # Try JSON first
    if is_json_version(version, bible_dir) and JSON_AVAILABLE:
        try:
            return build_json_index(version, json_root)
        except Exception as e:
            print(f"Warning: Could not build JSON index for {version}: {e}")
    
    # Fall back to markdown
    if is_markdown_version(version, bible_dir):
        return _build_markdown_index(bible_path / version)
    
    return []


def _build_markdown_index(bible_path: Path):
    """Build index from markdown files (legacy support)."""
    testaments = []

    for testament_name in ("Old Testament", "New Testament"):
        testament_path = bible_path / testament_name
        if not testament_path.exists():
            continue

        books = []
        for book_folder in sorted(t for t in testament_path.iterdir() if t.is_dir()):
            book_name = extract_book_name(book_folder.name)
            chapters = []

            for file in sorted(book_folder.glob("*.md")):
                chapter_num = extract_chapter_number(file)
                # Calculate relative path
                rel_path = to_relative_source_path(file, bible_path.parent)
                
                chapters.append({
                    "number": chapter_num,
                    "path": rel_path,
                    "filename": file.name,
                })

            # Sort chapters numerically by chapter number
            if chapters:
                chapters.sort(key=lambda c: int(c["number"]))
                books.append({
                    "name": book_name,
                    "folder": book_folder.name,
                    "chapters": chapters,
                })

        if books:
            testaments.append({
                "name": testament_name,
                "books": books,
            })

    return testaments
