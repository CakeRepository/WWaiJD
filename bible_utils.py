"""
Utility helpers for working with the King James Bible markdown files.
Shared between the embedding builder and the Flask application.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple

BIBLE_ROOT = Path("bible-data")

_VERSE_HEADER_RE = re.compile(r"^\s*##\s*(\d+)\.\s*$")
_CHAPTER_NUMBER_RE = re.compile(r"(\d+)")


def extract_book_name(folder_name: str) -> str:
    """Strip the numeric prefix from a folder name like '18 Job'."""
    if not folder_name:
        return folder_name
    return folder_name.split(" ", 1)[1] if " " in folder_name else folder_name


def extract_chapter_number(file_path: Path | str) -> str:
    """
    Attempt to read the chapter number from a file stem (e.g., job12 -> 12).
    Returns "1" when no numeric suffix can be found.
    Looks for the LAST number in the filename to handle books like "1 Corinthians".
    """
    stem = Path(file_path).stem
    # Find all numbers in the stem and take the last one (the chapter number)
    matches = _CHAPTER_NUMBER_RE.findall(stem)
    return matches[-1] if matches else "1"


def to_relative_source_path(file_path: Path, bible_dir: Path | str = BIBLE_ROOT) -> str:
    """Return the path to a markdown file relative to the bible root directory."""
    base = Path(bible_dir).resolve()
    absolute = Path(file_path).resolve()
    return absolute.relative_to(base).as_posix()


def parse_verses(markdown_text: str) -> List[Tuple[str, str]]:
    """
    Parse a markdown chapter into (verse_number, verse_text) tuples.
    Verses are identified by lines that look like '## 12.'.
    """
    verses: List[Tuple[str, str]] = []
    verse_num: str | None = None
    current_lines: List[str] = []

    for raw_line in markdown_text.splitlines():
        clean_line = raw_line.strip("\ufeff\b")
        header_match = _VERSE_HEADER_RE.match(clean_line.strip())
        if header_match:
            if verse_num is not None:
                verses.append((verse_num, _compact_lines(current_lines)))
            verse_num = header_match.group(1)
            current_lines = []
        else:
            # Preserve meaningful whitespace but collapse excess gaps later.
            current_lines.append(clean_line.strip())

    if verse_num is not None:
        verses.append((verse_num, _compact_lines(current_lines)))

    return verses


def resolve_bible_path(relative_path: str, bible_dir: Path | str = BIBLE_ROOT) -> Path:
    """
    Resolve a relative bible path such as 'Old Testament/18 Job/job1.md'
    and ensure it stays within the bible directory tree.
    """
    base = Path(bible_dir).resolve()
    candidate = (base / Path(relative_path)).resolve()
    if not str(candidate).startswith(str(base)):
        raise ValueError("Invalid bible path provided.")
    if not candidate.exists():
        raise FileNotFoundError(f"Bible markdown not found: {relative_path}")
    return candidate


def _compact_lines(lines: Sequence[str]) -> str:
    """Join verse lines with spaces while removing empty fragments."""
    filtered = [line for line in lines if line]
    return " ".join(filtered).strip()


def build_bible_index(bible_dir: Path | str = BIBLE_ROOT):
    """
    Return a structured index of available testaments, books, and chapters.
    """
    bible_path = Path(bible_dir)
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
                chapters.append({
                    "number": chapter_num,
                    "path": to_relative_source_path(file, bible_path),
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
