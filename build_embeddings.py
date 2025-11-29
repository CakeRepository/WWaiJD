"""
Script to process Bible JSON files and create a vector database
using Ollama's Gemma embeddings via ChromaDB.

Supports both JSON format (from arron-taylor/bible-versions) and legacy markdown files.
Supports resuming interrupted builds and checking progress.
"""

import argparse
from pathlib import Path
import chromadb
import ollama
from typing import List, Dict, Any, Optional
from bible_utils import (
    get_available_versions,
    is_json_version,
    is_markdown_version,
)

# Import JSON Bible utilities
from json_bible_utils import (
    iter_chapters as iter_json_chapters,
    BIBLE_JSON_ROOT,
)

BIBLE_DATA_DIR = Path("bible-data")


def read_bible_files(bible_dir="bible-data"):
    """
    Read every Bible chapter from JSON files and capture its metadata.
    Falls back to legacy markdown if JSON not available.
    """
    texts = []
    bible_path = Path(bible_dir)
    json_root = bible_path / "json"
    
    versions = get_available_versions(bible_path)
    if not versions:
        print("[!] No Bible versions found. Run 'python download_bibles.py' first.")
        return []

    for version in versions:
        print(f"Processing version: {version}")
        
        # Check if this is a JSON version
        if is_json_version(version, bible_path):
            # Use JSON iterator
            try:
                for chapter_data in iter_json_chapters(version, json_root):
                    # Convert verses list to content string for compatibility
                    verses_text = "\n".join([
                        f"{v}. {text}" 
                        for v, text in chapter_data["verses"]
                    ])
                    
                    texts.append({
                        "book": chapter_data["book"],
                        "testament": chapter_data["testament"],
                        "chapter": str(chapter_data["chapter"]),
                        "verses": chapter_data["verses"],  # Keep as list for direct use
                        "source_path": f"{version}/{chapter_data['book']}/{chapter_data['chapter']}",
                        "version": version
                    })
            except Exception as e:
                print(f"  [!] Error processing {version}: {e}")
                continue
        
        elif is_markdown_version(version, bible_path):
            # Fall back to legacy markdown processing
            texts.extend(_read_markdown_version(bible_path, version))

    return texts


def _read_markdown_version(bible_path: Path, version: str):
    """Read Bible chapters from legacy markdown files."""
    from bible_utils import extract_book_name, extract_chapter_number, parse_verses, to_relative_source_path
    
    texts = []
    version_path = bible_path / version

    def process_testament(testament_name: str):
        testament_path = version_path / testament_name
        if not testament_path.exists():
            return

        for book_folder in sorted(testament_path.iterdir()):
            if not book_folder.is_dir():
                continue

            book_name = extract_book_name(book_folder.name)
            for file in sorted(book_folder.glob("*.md")):
                chapter_num = extract_chapter_number(file)
                with open(file, "r", encoding="utf-8") as f:
                    content = f.read()

                verses = parse_verses(content)
                texts.append({
                    "book": book_name,
                    "testament": testament_name,
                    "chapter": chapter_num,
                    "verses": verses,  # Already in (num, text) format
                    "source_path": to_relative_source_path(file, bible_path),
                    "version": version
                })

    process_testament("Old Testament")
    process_testament("New Testament")
    
    return texts


def chunk_bible_text(texts: List[Dict[str, str]], chunk_size: int = 500) -> List[Dict[str, Any]]:
    """
    Chunk the Bible text into smaller passages for better retrieval.

    Tries to split on verse boundaries when possible to maintain context.
    Accumulates verses until the chunk size is reached.

    Args:
        texts: A list of chapter dictionaries (as returned by read_bible_files).
        chunk_size: Approximate maximum size of a text chunk in characters.
                    Defaults to 500.

    Returns:
        List[Dict[str, Any]]: A list of chunk dictionaries.
        Keys: "text", "book", "testament", "chapter", "verses", "reference", "source_path".
    """
    chunks = []

    for chapter_data in texts:
        book = chapter_data["book"]
        testament = chapter_data["testament"]
        chapter_num = chapter_data["chapter"]
        source_path = chapter_data["source_path"]
        version = chapter_data.get("version", "kjv")
        
        # Get verses - already in (verse_num, text) format
        verses = chapter_data.get("verses", [])

        if not verses:
            continue

        current_chunk = ""
        verse_start = None
        verse_end = None

        for verse_num, verse_text in verses:
            if not verse_text:
                continue
            
            # Ensure verse_num is a string for consistent formatting
            verse_num_str = str(verse_num)

            if verse_start is None:
                verse_start = verse_num_str

            verse_end = verse_num_str
            verse_content = f"{verse_num_str}. {verse_text} "

            if len(current_chunk) + len(verse_content) < chunk_size:
                current_chunk += verse_content
            else:
                if current_chunk and verse_start:
                    verse_range = _format_verse_range(verse_start, verse_end)
                    chunks.append({
                        "text": current_chunk.strip(),
                        "book": book,
                        "testament": testament,
                        "chapter": chapter_num,
                        "verses": verse_range,
                        "reference": f"{book} {chapter_num}:{verse_range}",
                        "source_path": source_path,
                        "version": version,
                    })

                current_chunk = verse_content
                verse_start = verse_num_str
                verse_end = verse_num_str

        if current_chunk and verse_start:
            verse_range = _format_verse_range(verse_start, verse_end)
            chunks.append({
                "text": current_chunk.strip(),
                "book": book,
                "testament": testament,
                "chapter": chapter_num,
                "verses": verse_range,
                "reference": f"{book} {chapter_num}:{verse_range}",
                "source_path": source_path,
                "version": version,
            })

    return chunks


def _format_verse_range(start: str, end: str | None) -> str:
    """
    Format a readable verse range string.

    Args:
        start: The starting verse number.
        end: The ending verse number.

    Returns:
        str: A string like "1" or "1-5".
    """
    if not end or start == end:
        return str(start)
    return f"{start}-{end}"


def create_embedding(text: str) -> Optional[List[float]]:
    """
    Generate embeddings using Ollama's Gemma model.

    Args:
        text: The text content to embed.

    Returns:
        Optional[List[float]]: The vector embedding as a list of floats,
        or None if generation fails.
    """
    try:
        response = ollama.embeddings(model='embeddinggemma', prompt=text)
        return response['embedding']
    except Exception as e:
        print(f"Error generating embedding: {e}")
        return None


def get_chunk_id(chunk, index):
    """Generate a unique ID for a chunk."""
    return f"{chunk.get('version', 'kjv')}_{chunk['book']}_{chunk['chapter']}_{chunk['verses']}_{index}"


def get_existing_ids(db_path="chroma_db"):
    """Get all existing chunk IDs from the database."""
    if not Path(db_path).exists():
        return set()
    
    try:
        client = chromadb.PersistentClient(path=db_path)
        collection = client.get_collection("bible_verses")
        # Get all IDs from the collection
        results = collection.get(include=[])
        return set(results['ids'])
    except Exception as e:
        print(f"[!] Could not read existing database: {e}")
        return set()


def check_status(db_path="chroma_db"):
    """Check the current status of the embeddings database."""
    print("=" * 60)
    print("Embeddings Database Status")
    print("=" * 60)
    
    if not Path(db_path).exists():
        print("[!] No database found at:", db_path)
        print("    Run 'python build_embeddings.py' to build the database.")
        return None
    
    try:
        client = chromadb.PersistentClient(path=db_path)
        collection = client.get_collection("bible_verses")
        count = collection.count()
        
        print(f"[OK] Database found at: {db_path}")
        print(f"     Total embedded chunks: {count:,}")
        
        # Get version breakdown
        results = collection.get(include=["metadatas"])
        versions = {}
        for meta in results['metadatas']:
            version = meta.get('version', 'unknown')
            versions[version] = versions.get(version, 0) + 1
        
        if versions:
            print("\n     Chunks by version:")
            for version, v_count in sorted(versions.items()):
                print(f"       - {version.upper()}: {v_count:,}")
        
        return count
    except Exception as e:
        error_str = str(e)
        if "PanicException" in error_str or "range" in error_str:
            print(f"[ERROR] Database appears to be corrupted!")
            print(f"        This can happen if a previous build was interrupted.")
            print(f"\n        Options:")
            print(f"          1. Delete the database and start fresh:")
            print(f"             python build_embeddings.py --fresh")
            print(f"          2. Or manually remove: {db_path}")
        else:
            print(f"[ERROR] Could not read database: {e}")
        return None


def safe_check_status(db_path="chroma_db"):
    """Wrapper that catches panics from corrupted databases."""
    import sys
    
    # Check if database directory exists first
    if not Path(db_path).exists():
        print("=" * 60)
        print("Embeddings Database Status")
        print("=" * 60)
        print("[!] No database found at:", db_path)
        print("    Run 'python build_embeddings.py' to build the database.")
        return None, False
    
    # Try to check status - this may panic if DB is corrupted
    try:
        result = check_status(db_path)
        return result, False
    except BaseException as e:
        # Catch any exception including Rust panics
        error_str = str(e)
        print("=" * 60)
        print("Embeddings Database Status") 
        print("=" * 60)
        print(f"[ERROR] Database appears to be corrupted!")
        print(f"        Error: {error_str[:100]}...")
        print(f"\n        Options:")
        print(f"          1. Delete the database and start fresh:")
        print(f"             python build_embeddings.py --fresh")
        print(f"          2. Or manually remove: {db_path}")
        return None, True  # Return corrupted=True
        return None


def build_vector_database(chunks, db_path="chroma_db", resume=False, fresh=False):
    """Build the ChromaDB vector database with Bible chunks.
    
    Args:
        chunks: List of chunk dictionaries to embed
        db_path: Path to ChromaDB database
        resume: If True, skip chunks that are already embedded
        fresh: If True, delete existing database and start fresh
    """
    import shutil
    
    total_chunks = len(chunks)
    print(f"\nBuilding vector database with {total_chunks:,} chunks...")
    
    existing_ids = set()
    
    if fresh and Path(db_path).exists():
        print(f"[!] Removing existing database at {db_path}...")
        shutil.rmtree(db_path)
        print("[OK] Old database removed")
    elif resume and Path(db_path).exists():
        print("[!] Resume mode: checking for existing embeddings...")
        existing_ids = get_existing_ids(db_path)
        if existing_ids:
            print(f"[OK] Found {len(existing_ids):,} existing embeddings")
    
    # Initialize ChromaDB client
    client = chromadb.PersistentClient(path=db_path)
    
    # Create or get collection
    try:
        collection = client.get_collection("bible_verses")
        print("[OK] Using existing collection")
    except Exception:
        collection = client.create_collection(
            name="bible_verses",
            metadata={"description": "Bible verses for RAG", "embedding_dimension": 3072}
        )
        print("[OK] Created new collection")
    
    # Filter out already-embedded chunks if resuming
    if resume and existing_ids:
        chunks_to_process = []
        for i, chunk in enumerate(chunks):
            chunk_id = get_chunk_id(chunk, i)
            if chunk_id not in existing_ids:
                # Store original index for ID generation
                chunk['_original_index'] = i
                chunks_to_process.append(chunk)
        
        skipped = total_chunks - len(chunks_to_process)
        print(f"[OK] Skipping {skipped:,} already-embedded chunks")
        print(f"     Remaining to process: {len(chunks_to_process):,}")
        chunks = chunks_to_process
        
        if not chunks:
            print("\n[OK] All chunks are already embedded! Nothing to do.")
            print(f"Database has {collection.count():,} passages.")
            return
    
    # Add documents in batches
    batch_size = 100
    total_batches = (len(chunks) + batch_size - 1) // batch_size
    processed = 0
    failed = 0
    
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        batch_num = i // batch_size + 1
        print(f"Processing batch {batch_num}/{total_batches}... ", end="", flush=True)
        
        documents = []
        metadatas = []
        ids = []
        embeddings = []
        
        for j, chunk in enumerate(batch):
            # Generate embedding
            embedding = create_embedding(chunk['text'])
            if embedding is None:
                failed += 1
                continue
            
            # Use original index if available (for resume mode)
            original_idx = chunk.get('_original_index', i + j)
            
            documents.append(chunk['text'])
            metadatas.append({
                'book': chunk['book'],
                'testament': chunk['testament'],
                'chapter': chunk['chapter'],
                'verses': chunk['verses'],
                'reference': chunk['reference'],
                'source_path': chunk['source_path'],
                'version': chunk.get('version', 'kjv')
            })
            ids.append(get_chunk_id(chunk, original_idx))
            embeddings.append(embedding)
        
        # Add to collection
        if documents:
            collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids,
                embeddings=embeddings
            )
            processed += len(documents)
        
        print(f"[OK] ({processed:,} total)")
    
    print(f"\n[OK] Vector database updated successfully!")
    print(f"     Total passages in database: {collection.count():,}")
    if failed > 0:
        print(f"     [!] Failed embeddings: {failed}")
    print(f"     Database saved to: {db_path}")


def main():
    """Main function to build the embeddings database."""
    parser = argparse.ArgumentParser(
        description="Build Bible embeddings for the RAG pipeline.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python build_embeddings.py              # Fresh build (asks for confirmation)
  python build_embeddings.py --status     # Check current progress
  python build_embeddings.py --resume     # Continue from where you left off
  python build_embeddings.py --fresh      # Force fresh build (no confirmation)
        """
    )
    parser.add_argument(
        '--status', '-s',
        action='store_true',
        help='Check the current status of the embeddings database'
    )
    parser.add_argument(
        '--resume', '-r',
        action='store_true',
        help='Resume building from where you left off (skip existing embeddings)'
    )
    parser.add_argument(
        '--fresh', '-f',
        action='store_true',
        help='Force a fresh build, deleting any existing database'
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("What Would AI Jesus Do - Embeddings Builder")
    print("=" * 60)
    
    # Status check only
    if args.status:
        try:
            check_status()
        except BaseException as e:
            print("=" * 60)
            print("Embeddings Database Status")
            print("=" * 60)
            print(f"[ERROR] Database appears to be corrupted!")
            print(f"        Error: {str(e)[:100]}...")
            print(f"\n        Options:")
            print(f"          1. Delete the database and start fresh:")
            print(f"             python build_embeddings.py --fresh")
            print(f"          2. Or manually remove: chroma_db")
        return
    
    # Check for Bible data
    json_dir = BIBLE_DATA_DIR / "json"
    versions = get_available_versions(BIBLE_DATA_DIR)
    
    if not versions:
        print("[ERROR] No Bible versions found!")
        print("   Run 'python download_bibles.py' first to download Bible versions.")
        return
    
    print(f"[OK] Found {len(versions)} Bible version(s): {', '.join(versions)}")
    
    # Check if Ollama is available
    try:
        ollama.list()
        print("[OK] Ollama is running")
    except Exception as e:
        print("[ERROR] Ollama is not running. Please start Ollama first.")
        print(f"   Details: {e}")
        return
    
    # Check if Gemma model is available
    try:
        models = ollama.list()
        model_names = [model['name'] for model in models.get('models', [])]
        if not any('gemma' in name.lower() for name in model_names):
            print("[!] Warning: Gemma model not found. Pulling it now...")
            print("   This may take a few minutes...")
            ollama.pull('embeddinggemma')
            print("[OK] Gemma model downloaded")
    except Exception as e:
        print(f"[!] Could not verify Gemma model: {e}")
    
    # Check existing database status
    if not args.resume and not args.fresh and Path("chroma_db").exists():
        try:
            existing_count = check_status()
            if existing_count is not None and existing_count > 0:
                print("\n[!] An existing database was found.")
                print("    Options:")
                print("      --resume  : Continue adding to existing database")
                print("      --fresh   : Delete and rebuild from scratch")
                response = input("\n    Proceed with FRESH build? This will DELETE the existing database. [y/N]: ")
                if response.lower() != 'y':
                    print("\n[!] Cancelled. Use --resume to continue from where you left off.")
                    return
                args.fresh = True
        except BaseException as e:
            print("\n[!] Existing database is corrupted and cannot be read.")
            print("    Will proceed with fresh build...")
            args.fresh = True
    
    # Read Bible files
    print("\nStep 1: Reading Bible files...")
    texts = read_bible_files()
    print(f"[OK] Processed {len(texts)} chapters")
    
    if not texts:
        print("[ERROR] No Bible chapters found to process.")
        return
    
    # Chunk the text
    print("\nStep 2: Chunking text into passages...")
    chunks = chunk_bible_text(texts)
    print(f"[OK] Created {len(chunks):,} chunks")
    
    # Build vector database
    print("\nStep 3: Building vector database...")
    if args.resume:
        print("[!] Resume mode: will skip already-embedded passages...")
    else:
        print("[!] This will take several minutes as we generate embeddings for each passage...")
    
    build_vector_database(chunks, resume=args.resume, fresh=args.fresh)
    
    print("\n" + "=" * 60)
    print("Setup complete! You can now run the application with:")
    print("   python app.py")
    print("=" * 60)


if __name__ == "__main__":
    main()
