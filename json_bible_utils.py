"""
Utility module for working with JSON-formatted Bible data.
Handles the structure from arron-taylor/bible-versions repository.

JSON Structure:
{
    "Genesis": {
        "1": {
            "1": "In the beginning God created...",
            "2": "And the earth was without form..."
        },
        "2": { ... }
    },
    "Exodus": { ... }
}
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Default root directory for JSON Bible files
BIBLE_JSON_ROOT = Path(__file__).parent / "bible-data" / "json"

# Canonical book order (66 books)
BOOK_ORDER = [
    # Old Testament (39 books)
    "Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy",
    "Joshua", "Judges", "Ruth", "1 Samuel", "2 Samuel",
    "1 Kings", "2 Kings", "1 Chronicles", "2 Chronicles",
    "Ezra", "Nehemiah", "Esther", "Job", "Psalms",
    "Proverbs", "Ecclesiastes", "Song of Solomon", "Isaiah", "Jeremiah",
    "Lamentations", "Ezekiel", "Daniel", "Hosea", "Joel",
    "Amos", "Obadiah", "Jonah", "Micah", "Nahum",
    "Habakkuk", "Zephaniah", "Haggai", "Zechariah", "Malachi",
    # New Testament (27 books)
    "Matthew", "Mark", "Luke", "John", "Acts",
    "Romans", "1 Corinthians", "2 Corinthians", "Galatians", "Ephesians",
    "Philippians", "Colossians", "1 Thessalonians", "2 Thessalonians",
    "1 Timothy", "2 Timothy", "Titus", "Philemon", "Hebrews",
    "James", "1 Peter", "2 Peter", "1 John", "2 John",
    "3 John", "Jude", "Revelation"
]

OLD_TESTAMENT_BOOKS = set(BOOK_ORDER[:39])
NEW_TESTAMENT_BOOKS = set(BOOK_ORDER[39:])

# Book name normalization mapping
BOOK_ALIASES = {
    # Variations of book names
    "psalm": "Psalms",
    "psalms": "Psalms",
    "song of songs": "Song of Solomon",
    "songs of solomon": "Song of Solomon",
    "song of solomon": "Song of Solomon",
    "canticles": "Song of Solomon",
    "1samuel": "1 Samuel",
    "2samuel": "2 Samuel",
    "1 sam": "1 Samuel",
    "2 sam": "2 Samuel",
    "1kings": "1 Kings",
    "2kings": "2 Kings",
    "1chronicles": "1 Chronicles",
    "2chronicles": "2 Chronicles",
    "1 chron": "1 Chronicles",
    "2 chron": "2 Chronicles",
    "1corinthians": "1 Corinthians",
    "2corinthians": "2 Corinthians",
    "1 cor": "1 Corinthians",
    "2 cor": "2 Corinthians",
    "1thessalonians": "1 Thessalonians",
    "2thessalonians": "2 Thessalonians",
    "1 thess": "1 Thessalonians",
    "2 thess": "2 Thessalonians",
    "1timothy": "1 Timothy",
    "2timothy": "2 Timothy",
    "1 tim": "1 Timothy",
    "2 tim": "2 Timothy",
    "1peter": "1 Peter",
    "2peter": "2 Peter",
    "1 pet": "1 Peter",
    "2 pet": "2 Peter",
    "1john": "1 John",
    "2john": "2 John",
    "3john": "3 John",
    "1 jn": "1 John",
    "2 jn": "2 John",
    "3 jn": "3 John",
    "gen": "Genesis",
    "ex": "Exodus",
    "exod": "Exodus",
    "lev": "Leviticus",
    "num": "Numbers",
    "deut": "Deuteronomy",
    "josh": "Joshua",
    "judg": "Judges",
    "neh": "Nehemiah",
    "esth": "Esther",
    "prov": "Proverbs",
    "eccl": "Ecclesiastes",
    "eccles": "Ecclesiastes",
    "isa": "Isaiah",
    "jer": "Jeremiah",
    "lam": "Lamentations",
    "ezek": "Ezekiel",
    "dan": "Daniel",
    "hos": "Hosea",
    "ob": "Obadiah",
    "obad": "Obadiah",
    "mic": "Micah",
    "nah": "Nahum",
    "hab": "Habakkuk",
    "zeph": "Zephaniah",
    "hag": "Haggai",
    "zech": "Zechariah",
    "mal": "Malachi",
    "matt": "Matthew",
    "mt": "Matthew",
    "mk": "Mark",
    "lk": "Luke",
    "jn": "John",
    "rom": "Romans",
    "gal": "Galatians",
    "eph": "Ephesians",
    "phil": "Philippians",
    "col": "Colossians",
    "phm": "Philemon",
    "philem": "Philemon",
    "heb": "Hebrews",
    "jas": "James",
    "rev": "Revelation",
    "revelations": "Revelation",
}


def normalize_book_name(book: str) -> str:
    """
    Normalize a book name to its canonical form.
    
    Args:
        book: Book name in any common format
        
    Returns:
        Canonical book name (e.g., "Genesis", "1 John")
    """
    if not book:
        return book
    
    # Clean and lowercase for lookup
    cleaned = book.strip().lower()
    
    # Check aliases first
    if cleaned in BOOK_ALIASES:
        return BOOK_ALIASES[cleaned]
    
    # Try to match with canonical names (case-insensitive)
    for canonical in BOOK_ORDER:
        if canonical.lower() == cleaned:
            return canonical
    
    # If no match, return title-cased version
    return book.strip().title()


def get_testament(book: str) -> str:
    """Get the testament for a book name."""
    canonical = normalize_book_name(book)
    if canonical in OLD_TESTAMENT_BOOKS:
        return "Old Testament"
    elif canonical in NEW_TESTAMENT_BOOKS:
        return "New Testament"
    return "Unknown"


@lru_cache(maxsize=50)
def load_bible_json(version: str, bible_root: Path | str = BIBLE_JSON_ROOT) -> Dict:
    """
    Load a Bible version from JSON file.
    
    Args:
        version: Version code (e.g., "kjv", "esv", "niv")
        bible_root: Root directory containing JSON files
        
    Returns:
        Dictionary with book -> chapter -> verse -> text structure
    """
    root = Path(bible_root)
    json_path = root / f"{version.lower()}.json"
    
    if not json_path.exists():
        raise FileNotFoundError(f"Bible version not found: {version} (looking for {json_path})")
    
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_available_versions(bible_root: Path | str = BIBLE_JSON_ROOT) -> List[str]:
    """Return a list of available Bible version codes."""
    root = Path(bible_root)
    if not root.exists():
        return []
    return sorted([f.stem for f in root.glob("*.json")])


def get_books(version: str, bible_root: Path | str = BIBLE_JSON_ROOT) -> List[str]:
    """
    Get list of books in a Bible version, ordered canonically.
    
    Args:
        version: Version code
        bible_root: Root directory
        
    Returns:
        List of book names in canonical order
    """
    data = load_bible_json(version, bible_root)
    
    # Get books that exist in this version
    available_books = set(data.keys())
    
    # Return in canonical order, filtering to only those available
    return [book for book in BOOK_ORDER if book in available_books]


def get_chapters(version: str, book: str, bible_root: Path | str = BIBLE_JSON_ROOT) -> List[int]:
    """
    Get list of chapter numbers for a book.
    
    Args:
        version: Version code
        book: Book name
        bible_root: Root directory
        
    Returns:
        List of chapter numbers (sorted)
    """
    data = load_bible_json(version, bible_root)
    canonical_book = normalize_book_name(book)
    
    if canonical_book not in data:
        raise KeyError(f"Book not found: {book} in version {version}")
    
    chapters = data[canonical_book]
    return sorted([int(ch) for ch in chapters.keys()])


def get_verses(
    version: str, 
    book: str, 
    chapter: int, 
    bible_root: Path | str = BIBLE_JSON_ROOT
) -> List[Tuple[int, str]]:
    """
    Get all verses for a chapter.
    
    Args:
        version: Version code
        book: Book name
        chapter: Chapter number
        bible_root: Root directory
        
    Returns:
        List of (verse_number, verse_text) tuples, sorted by verse number
    """
    data = load_bible_json(version, bible_root)
    canonical_book = normalize_book_name(book)
    
    if canonical_book not in data:
        raise KeyError(f"Book not found: {book} in version {version}")
    
    chapters = data[canonical_book]
    chapter_str = str(chapter)
    
    if chapter_str not in chapters:
        raise KeyError(f"Chapter not found: {book} {chapter} in version {version}")
    
    verses = chapters[chapter_str]
    return sorted([(int(v), text) for v, text in verses.items()], key=lambda x: x[0])


def get_verse(
    version: str,
    book: str,
    chapter: int,
    verse: int,
    bible_root: Path | str = BIBLE_JSON_ROOT
) -> str:
    """
    Get a single verse.
    
    Args:
        version: Version code
        book: Book name
        chapter: Chapter number
        verse: Verse number
        bible_root: Root directory
        
    Returns:
        Verse text
    """
    data = load_bible_json(version, bible_root)
    canonical_book = normalize_book_name(book)
    
    if canonical_book not in data:
        raise KeyError(f"Book not found: {book}")
    
    chapters = data[canonical_book]
    chapter_str = str(chapter)
    
    if chapter_str not in chapters:
        raise KeyError(f"Chapter not found: {book} {chapter}")
    
    verses = chapters[chapter_str]
    verse_str = str(verse)
    
    if verse_str not in verses:
        raise KeyError(f"Verse not found: {book} {chapter}:{verse}")
    
    return verses[verse_str]


def get_verse_range(
    version: str,
    book: str,
    chapter: int,
    start_verse: int,
    end_verse: int,
    bible_root: Path | str = BIBLE_JSON_ROOT
) -> List[Tuple[int, str]]:
    """
    Get a range of verses.
    
    Args:
        version: Version code
        book: Book name
        chapter: Chapter number
        start_verse: Starting verse number
        end_verse: Ending verse number (inclusive)
        bible_root: Root directory
        
    Returns:
        List of (verse_number, verse_text) tuples
    """
    all_verses = get_verses(version, book, chapter, bible_root)
    return [(v, text) for v, text in all_verses if start_verse <= v <= end_verse]


def format_reference(book: str, chapter: int, verse_start: int = None, verse_end: int = None) -> str:
    """
    Format a Bible reference string.
    
    Examples:
        format_reference("John", 3, 16) -> "John 3:16"
        format_reference("John", 3, 16, 17) -> "John 3:16-17"
        format_reference("John", 3) -> "John 3"
    """
    canonical = normalize_book_name(book)
    
    if verse_start is None:
        return f"{canonical} {chapter}"
    
    if verse_end is None or verse_start == verse_end:
        return f"{canonical} {chapter}:{verse_start}"
    
    return f"{canonical} {chapter}:{verse_start}-{verse_end}"


def build_bible_index(version: str, bible_root: Path | str = BIBLE_JSON_ROOT) -> List[Dict]:
    """
    Build a structured index for a Bible version.
    Compatible with the old markdown-based index structure.
    
    Args:
        version: Version code
        bible_root: Root directory
        
    Returns:
        List of testament dictionaries with books and chapters
    """
    try:
        data = load_bible_json(version, bible_root)
    except FileNotFoundError:
        return []
    
    testaments = []
    
    for testament_name, book_set in [
        ("Old Testament", OLD_TESTAMENT_BOOKS),
        ("New Testament", NEW_TESTAMENT_BOOKS)
    ]:
        books = []
        
        for book_name in BOOK_ORDER:
            if book_name not in book_set:
                continue
            if book_name not in data:
                continue
            
            chapters = []
            chapter_data = data[book_name]
            
            for chapter_str in sorted(chapter_data.keys(), key=int):
                chapters.append({
                    "number": chapter_str,
                    # Create a virtual path for compatibility
                    "path": f"{version}/{book_name}/{chapter_str}",
                })
            
            if chapters:
                books.append({
                    "name": book_name,
                    "folder": book_name,  # For compatibility
                    "chapters": chapters,
                })
        
        if books:
            testaments.append({
                "name": testament_name,
                "books": books,
            })
    
    return testaments


def iter_all_verses(
    version: str,
    bible_root: Path | str = BIBLE_JSON_ROOT
):
    """
    Iterator that yields all verses in a Bible version.
    
    Yields:
        (book, testament, chapter, verse, text) tuples
    """
    data = load_bible_json(version, bible_root)
    
    for book_name in BOOK_ORDER:
        if book_name not in data:
            continue
        
        testament = get_testament(book_name)
        book_data = data[book_name]
        
        for chapter_str in sorted(book_data.keys(), key=int):
            chapter_num = int(chapter_str)
            verses = book_data[chapter_str]
            
            for verse_str in sorted(verses.keys(), key=int):
                verse_num = int(verse_str)
                text = verses[verse_str]
                yield book_name, testament, chapter_num, verse_num, text


def iter_chapters(
    version: str,
    bible_root: Path | str = BIBLE_JSON_ROOT
):
    """
    Iterator that yields chapter data for processing.
    
    Yields:
        Dictionary with book, testament, chapter, verses list, and version
    """
    data = load_bible_json(version, bible_root)
    
    for book_name in BOOK_ORDER:
        if book_name not in data:
            continue
        
        testament = get_testament(book_name)
        book_data = data[book_name]
        
        for chapter_str in sorted(book_data.keys(), key=int):
            chapter_num = int(chapter_str)
            verse_data = book_data[chapter_str]
            
            # Convert to list of (verse_num, text) tuples
            verses = sorted(
                [(int(v), text) for v, text in verse_data.items()],
                key=lambda x: x[0]
            )
            
            yield {
                "book": book_name,
                "testament": testament,
                "chapter": chapter_num,
                "verses": verses,
                "version": version,
            }


def clear_cache():
    """Clear the LRU cache for loaded Bible data."""
    load_bible_json.cache_clear()
