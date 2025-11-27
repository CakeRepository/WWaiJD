"""
Utility helpers for working with the King James Bible markdown files.
Shared between the embedding builder and the Flask application.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple, Dict, Any, Union

BIBLE_ROOT = Path("bible-data")

_VERSE_HEADER_RE = re.compile(r"^\s*##\s*(\d+)\.\s*$")
_CHAPTER_NUMBER_RE = re.compile(r"(\d+)")


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
    return absolute.relative_to(base).as_posix()


def parse_verses(markdown_text: str) -> List[Tuple[str, str]]:
    """
    Parse a markdown chapter into a list of verse tuples.

    Identifies verses based on markdown headers like '## 12.'.

    Args:
        markdown_text: The content of the markdown file.

    Returns:
        List[Tuple[str, str]]: A list of tuples, where each tuple contains
            (verse_number, verse_text).
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


def _compact_lines(lines: Sequence[str]) -> str:
    """
    Join lines of text, removing empty lines and extra whitespace.

    Args:
        lines: A sequence of strings.

    Returns:
        str: A single string with lines joined by spaces.
    """
    filtered = [line for line in lines if line]
    return " ".join(filtered).strip()


def build_bible_index(bible_dir: Path | str = BIBLE_ROOT) -> List[Dict[str, Any]]:
    """
    Build a structured index of the Bible from the file system.

    Scans the directory structure to organize testaments, books, and chapters.

    Args:
        bible_dir: The root directory of the Bible data. Defaults to BIBLE_ROOT.

    Returns:
        List[Dict[str, Any]]: A list of dictionaries representing testaments.
            Each testament contains a list of books, and each book contains
            a list of chapters with metadata.

            Example structure:
            [
                {
                    "name": "Old Testament",
                    "books": [
                        {
                            "name": "Genesis",
                            "folder": "01 Genesis",
                            "chapters": [
                                {
                                    "number": "1",
                                    "path": "Old Testament/01 Genesis/gen1.md",
                                    "filename": "gen1.md"
                                },
                                ...
                            ]
                        },
                        ...
                    ]
                },
                ...
            ]
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
