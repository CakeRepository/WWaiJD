from pathlib import Path
from bible_utils import get_available_versions, build_bible_index

BIBLE_DATA_DIR = Path("bible-data").resolve()

print(f"Checking bible data in: {BIBLE_DATA_DIR}")
versions = get_available_versions(BIBLE_DATA_DIR)
print(f"Available versions: {versions}")

for version in versions:
    print(f"\n--- Indexing {version} ---")
    index = build_bible_index(BIBLE_DATA_DIR, version=version)
    print(f"Testaments found: {len(index)}")
    if index:
        print(f"First testament: {index[0]['name']}")
        print(f"Books in first testament: {len(index[0]['books'])}")
        if index[0]['books']:
            first_book = index[0]['books'][0]
            print(f"First book: {first_book['name']}")
            print(f"Chapters in first book: {len(first_book['chapters'])}")
            if first_book['chapters']:
                print(f"First chapter path: {first_book['chapters'][0]['path']}")
