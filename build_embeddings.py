"""
Script to process the King James Bible markdown files and create a vector database
using Ollama's Gemma embeddings via ChromaDB.
"""

from pathlib import Path
import chromadb
import ollama
from bible_utils import (
    extract_book_name,
    extract_chapter_number,
    parse_verses,
    to_relative_source_path,
)


def read_bible_files(bible_dir="bible-data"):
    """Read every Bible markdown chapter and capture its metadata."""
    texts = []
    bible_path = Path(bible_dir)

    def process_testament(testament_name: str):
        testament_path = bible_path / testament_name
        if not testament_path.exists():
            return

        for book_folder in sorted(testament_path.iterdir()):
            if not book_folder.is_dir():
                continue

            book_name = extract_book_name(book_folder.name)
            for file in sorted(book_folder.glob("*.md")):
                chapter_num = extract_chapter_number(file)
                print(f"Reading {book_name} {chapter_num} ({file.name})...")
                with open(file, "r", encoding="utf-8") as f:
                    content = f.read()

                texts.append({
                    "book": book_name,
                    "testament": testament_name,
                    "chapter": chapter_num,
                    "content": content,
                    "source_path": to_relative_source_path(file, bible_path),
                })

    process_testament("Old Testament")
    process_testament("New Testament")

    return texts


def chunk_bible_text(texts, chunk_size=500):
    """
    Chunk the Bible text into smaller passages for better retrieval.
    Tries to split on verse boundaries when possible.
    """
    chunks = []

    for chapter_data in texts:
        book = chapter_data["book"]
        testament = chapter_data["testament"]
        chapter_num = chapter_data["chapter"]
        source_path = chapter_data["source_path"]
        verses = parse_verses(chapter_data["content"])

        if not verses:
            continue

        current_chunk = ""
        verse_start = None
        verse_end = None

        for verse_num, verse_text in verses:
            if not verse_text:
                continue

            if verse_start is None:
                verse_start = verse_num

            verse_end = verse_num
            verse_content = f"{verse_num}. {verse_text} "

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
                    })

                current_chunk = verse_content
                verse_start = verse_num
                verse_end = verse_num

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
            })

    return chunks


def _format_verse_range(start: str, end: str | None) -> str:
    """Format a readable verse range string."""
    if not end or start == end:
        return str(start)
    return f"{start}-{end}"


def create_embedding(text):
    """Generate embeddings using Ollama's Gemma model."""
    try:
        response = ollama.embeddings(model='embeddinggemma', prompt=text)
        return response['embedding']
    except Exception as e:
        print(f"Error generating embedding: {e}")
        return None


def build_vector_database(chunks, db_path="chroma_db"):
    """Build the ChromaDB vector database with Bible chunks."""
    print(f"\nBuilding vector database with {len(chunks)} chunks...")
    
    # Remove old database if it exists to avoid dimension mismatch
    import shutil
    if Path(db_path).exists():
        print(f"⚠️  Removing existing database at {db_path}...")
        shutil.rmtree(db_path)
        print("✅ Old database removed")
    
    # Initialize ChromaDB client
    client = chromadb.PersistentClient(path=db_path)
    
    # Create collection with explicit embedding dimension
    collection = client.create_collection(
        name="bible_kjv",
        metadata={"description": "King James Bible verses for RAG", "embedding_dimension": 3072}
    )
    
    # Add documents in batches
    batch_size = 100
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        print(f"Processing batch {i//batch_size + 1}/{(len(chunks) + batch_size - 1)//batch_size}...")
        
        documents = []
        metadatas = []
        ids = []
        embeddings = []
        
        for j, chunk in enumerate(batch):
            # Generate embedding
            embedding = create_embedding(chunk['text'])
            if embedding is None:
                continue
            
            documents.append(chunk['text'])
            metadatas.append({
                'book': chunk['book'],
                'testament': chunk['testament'],
                'chapter': chunk['chapter'],
                'verses': chunk['verses'],
                'reference': chunk['reference'],
                'source_path': chunk['source_path']
            })
            ids.append(f"{chunk['book']}_{chunk['chapter']}_{chunk['verses']}_{i+j}")
            embeddings.append(embedding)
        
        # Add to collection
        if documents:
            collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids,
                embeddings=embeddings
            )
    
    print(f"\n✅ Vector database created successfully with {collection.count()} passages!")
    print(f"Database saved to: {db_path}")


def main():
    """Main function to build the embeddings database."""
    print("=" * 60)
    print("What Would AI Jesus Do - Embeddings Builder")
    print("=" * 60)
    
    # Check if Ollama is available
    try:
        ollama.list()
        print("✅ Ollama is running")
    except Exception as e:
        print("❌ Error: Ollama is not running. Please start Ollama first.")
        print(f"   Details: {e}")
        return
    
    # Check if Gemma model is available
    try:
        models = ollama.list()
        model_names = [model['name'] for model in models.get('models', [])]
        if not any('gemma' in name.lower() for name in model_names):
            print("⚠️  Warning: Gemma model not found. Pulling it now...")
            print("   This may take a few minutes...")
            ollama.pull('embeddinggemma')
            print("✅ Gemma model downloaded")
    except Exception as e:
        print(f"⚠️  Could not verify Gemma model: {e}")
    
    # Read Bible files
    print("\nStep 1: Reading Bible files...")
    texts = read_bible_files()
    print(f"✅ Processed {len(texts)} chapters")
    
    # Chunk the text
    print("\nStep 2: Chunking text into passages...")
    chunks = chunk_bible_text(texts)
    print(f"✅ Created {len(chunks)} chunks")
    
    # Build vector database
    print("\nStep 3: Building vector database...")
    print("⚠️  This will take several minutes as we generate embeddings for each passage...")
    build_vector_database(chunks)
    
    print("\n" + "=" * 60)
    print("🎉 Setup complete! You can now run the application with:")
    print("   python app.py")
    print("=" * 60)


if __name__ == "__main__":
    main()
