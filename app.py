"""
What Would AI Jesus Do - Flask Application
Main web server that connects the frontend to the RAG pipeline
"""

import os
import sys

# Force unbuffered output to prevent "hit enter" issue on some servers
os.environ['PYTHONUNBUFFERED'] = '1'
sys.stdout.reconfigure(line_buffering=True) if hasattr(sys.stdout, 'reconfigure') else None

from flask import Flask, request, jsonify, send_from_directory, Response, stream_with_context, render_template, abort, url_for
from waitress import serve
from pathlib import Path
import json
import ollama
from datetime import datetime
from typing import Optional, Tuple, Dict, Any, Union
from bible_utils import (
    build_bible_index,
    extract_book_name,
    extract_chapter_number,
    parse_verses,
    resolve_bible_path,
    get_available_versions,
    is_json_version,
    normalize_book_name,
    get_verses_for_chapter,
)
from json_bible_utils import (
    get_verses as get_json_verses,
    get_books as get_json_books,
    get_chapters as get_json_chapters,
    get_testament,
    BIBLE_JSON_ROOT,
)
from rag_pipeline import BibleRAG, MODE_INSTRUCTIONS, DEFAULT_MODE
import database
import markdown

app = Flask(__name__, static_folder='static')
BIBLE_DATA_DIR = (Path(__file__).parent / 'bible-data').resolve()
BIBLE_JSON_DIR = BIBLE_DATA_DIR / 'json'

# Initialize Bible Index
BIBLE_INDICES = {}
DEFAULT_VERSION = 'kjv'

try:
    versions = get_available_versions(BIBLE_DATA_DIR)
    if not versions:
        print("[!] Warning: No bible versions found in bible-data", flush=True)
        print("   Run 'python download_bibles.py' to download Bible versions", flush=True)
    
    for version in versions:
        print(f"Building index for {version}...", flush=True)
        BIBLE_INDICES[version] = build_bible_index(BIBLE_DATA_DIR, version=version)
        
    # Set default index for backward compatibility
    if DEFAULT_VERSION in BIBLE_INDICES:
        BIBLE_INDEX = BIBLE_INDICES[DEFAULT_VERSION]
    elif BIBLE_INDICES:
        DEFAULT_VERSION = next(iter(BIBLE_INDICES.keys()))
        BIBLE_INDEX = BIBLE_INDICES[DEFAULT_VERSION]
    else:
        BIBLE_INDEX = []

    print(f"[OK] Bible index built successfully for {len(BIBLE_INDICES)} version(s)", flush=True)
except Exception as e:
    print(f"[!] Warning: Could not build Bible index: {e}", flush=True)
    BIBLE_INDEX = []

OLLAMA_LLM_KEEP_ALIVE = os.getenv('WWAIJD_LLM_KEEP_ALIVE', '120s')
OLLAMA_EMBED_KEEP_ALIVE = os.getenv('WWAIJD_EMBED_KEEP_ALIVE', '0s')

# Book name variations mapping (for URL normalization)
BOOK_NAME_VARIATIONS = {
    'psalm': 'psalms',
    'song of songs': 'song of solomon',
    '1 john': '1john',
    '2 john': '2john',
    '3 john': '3john',
    '1 peter': '1peter',
    '2 peter': '2peter',
    '1 timothy': '1timothy',
    '2 timothy': '2timothy',
    '1 thessalonians': '1thessalonians',
    '2 thessalonians': '2thessalonians',
    '1 corinthians': '1corinthians',
    '2 corinthians': '2corinthians',
    '1 samuel': '1samuel',
    '2 samuel': '2samuel',
    '1 kings': '1kings',
    '2 kings': '2kings',
    '1 chronicles': '1chronicles',
    '2 chronicles': '2chronicles',
}

def normalize_url_book_name(book_name):
    """Normalize book names from URLs to handle common variations."""
    normalized = book_name.lower().strip()
    return BOOK_NAME_VARIATIONS.get(normalized, normalized)

def find_chapter_path(book_name, chapter_num, version=DEFAULT_VERSION):
    """
    Find the chapter info for a specific book and chapter.
    Works with both JSON and markdown formats.
    Returns (path, proper_book_name) tuple.
    """
    target_book = normalize_book_name(book_name)
    target_chapter = str(chapter_num)
    
    index = BIBLE_INDICES.get(version, BIBLE_INDEX)
    
    for testament in index:
        for book in testament['books']:
            if normalize_book_name(book['name']).lower() == target_book.lower():
                for chapter in book['chapters']:
                    if chapter['number'] == target_chapter:
                        return chapter['path'], book['name']
    return None, None

def get_next_prev_chapters(book_name, chapter_num, version=DEFAULT_VERSION):
    """Get the next and previous chapter references."""
    target_book = normalize_book_name(book_name).lower()
    target_chapter = int(chapter_num)
    
    index = BIBLE_INDICES.get(version, BIBLE_INDEX)
    
    flat_chapters = []
    for testament in index:
        for book in testament['books']:
            b_name = book['name']
            for chapter in book['chapters']:
                flat_chapters.append({
                    'book': b_name,
                    'chapter': int(chapter['number'])
                })
    
    prev_chap = None
    next_chap = None
    
    for i, chap in enumerate(flat_chapters):
        if normalize_book_name(chap['book']).lower() == target_book and chap['chapter'] == target_chapter:
            if i > 0:
                prev_chap = flat_chapters[i-1]
            if i < len(flat_chapters) - 1:
                next_chap = flat_chapters[i+1]
            break
            
    return prev_chap, next_chap

def normalize_mode(mode_raw: Optional[str]) -> str:
    """
    Ensure mode matches a supported focus option.

    Args:
        mode_raw: The input mode string (e.g., "Comfort").

    Returns:
        str: The normalized mode key (e.g., "comfort") or DEFAULT_MODE.
    """
    if not mode_raw:
        return DEFAULT_MODE
    mode_key = str(mode_raw).strip().lower()
    return mode_key if mode_key in MODE_INSTRUCTIONS else DEFAULT_MODE

# Initialize RAG pipeline
try:
    rag = BibleRAG(
        embed_keep_alive=OLLAMA_EMBED_KEEP_ALIVE,
        llm_keep_alive=OLLAMA_LLM_KEEP_ALIVE
    )
    print("[OK] RAG pipeline initialized successfully", flush=True)
except Exception as e:
    print(f"[!] Warning: Could not initialize RAG pipeline: {e}", flush=True)
    print("Make sure you've run 'python build_embeddings.py' first!", flush=True)
    rag = None


@app.route('/')
def index():
    """
    Serve the main page (index.html).

    Returns:
        Response: The index.html file content.
    """
    try:
        database.increment_visit_count()
    except Exception as e:
        print(f"Error incrementing visit count: {e}")
    return send_from_directory('static', 'index.html')


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """
    Get site statistics.

    Returns:
        JSON response with visit count.
    """
    count = database.get_visit_count()
    return jsonify({'visits': count})


@app.route('/static/<path:path>')
def serve_static(path):
    """
    Serve static files from the static directory.

    Args:
        path: The relative path to the static file.

    Returns:
        Response: The static file content.
    """
    return send_from_directory('static', path)


@app.route('/robots.txt')
def robots():
    """
    Serve robots.txt for search engine crawlers.

    Returns:
        Response: The robots.txt file content.
    """
    return send_from_directory('static', 'robots.txt')


@app.route('/img/<path:path>')
def serve_image(path):
    """
    Serve image files from the img directory.

    Args:
        path: The relative path to the image file.

    Returns:
        Response: The image file content.
    """
    return send_from_directory('img', path)


@app.route('/api/ask', methods=['POST'])
def ask_question():
    """
    API endpoint to handle questions.
    
    Expects a JSON payload with a "question" key.
    Returns the AI-generated answer and relevant Bible passages.
    
    Request Body:
        {
            "question": "User's question",
            "mode": "Optional tone mode"
        }

    Returns:
        JSON response with "answer", "passages", and "mode".
    """
    if not rag:
        return jsonify({
            'error': 'RAG pipeline not initialized. Please run build_embeddings.py first.'
        }), 500
    
    try:
        # Get question from request
        data = request.get_json(silent=True) or {}
        question = data.get('question', '').strip()
        mode = normalize_mode(data.get('mode'))
        version = data.get('version', DEFAULT_VERSION).strip()
        
        if not question:
            return jsonify({
                'error': 'Question is required'
            }), 400
        
        # Get response from RAG pipeline
        result = rag.ask(question, mode=mode, version=version)
        
        if result.get('error'):
            return jsonify({
                'error': result['answer']
            }), 500
        
        return jsonify({
            'answer': result['answer'],
            'passages': result['passages'],
            'mode': mode,
            'version': version
        })
        
    except Exception as e:
        print(f"Error processing question: {e}")
        return jsonify({
            'error': f'An error occurred: {str(e)}'
        }), 500


@app.route('/api/ask-stream', methods=['POST'])
def ask_question_stream():
    """
    API endpoint to handle questions with streaming response.
    
    Uses Server-Sent Events (SSE) to stream the AI response token by token.

    Request Body:
        {
            "question": "User's question",
            "mode": "Optional tone mode"
        }
    
    Returns:
        Response: Event stream with types 'passages', 'chunk', 'done', or 'error'.
    """
    if not rag:
        return jsonify({
            'error': 'RAG pipeline not initialized. Please run build_embeddings.py first.'
        }), 500
    
    try:
        # Get question from request
        data = request.get_json(silent=True) or {}
        question = data.get('question', '').strip()
        mode = normalize_mode(data.get('mode'))
        version = data.get('version', DEFAULT_VERSION).strip()
        
        if not question:
            return jsonify({
                'error': 'Question is required'
            }), 400
        
        def generate():
            """Generator function for SSE streaming."""
            try:
                # Retrieve relevant passages first
                print(f"\n[QUESTION] (hidden) ({version})")
                print("[INFO] Retrieving relevant Bible passages...")
                passages = rag.retrieve_passages(question, version=version)
                print(f"[OK] Found {len(passages)} relevant passages")
                
                # Send passages first so UI can display them
                yield f"event: passages\ndata: {json.dumps({'passages': passages, 'mode': mode, 'version': version})}\n\n"
                
                # Stream the response
                print("[AI] Generating AI Jesus response (streaming)...")
                for chunk_data in rag.generate_response_stream(question, passages, mode=mode, version=version):
                    if chunk_data.get('error'):
                        yield f"event: error\ndata: {json.dumps({'error': chunk_data.get('chunk', 'Error occurred')})}\n\n"
                        break
                    elif chunk_data.get('chunk'):
                        # Send text chunk
                        yield f"event: chunk\ndata: {json.dumps({'text': chunk_data['chunk']})}\n\n"
                    
                    if chunk_data.get('done'):
                        yield f"event: done\ndata: {json.dumps({'done': True, 'mode': mode})}\n\n"
                        print("[OK] Response generated")
                        break
                        
            except Exception as e:
                print(f"Error in streaming: {e}")
                yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
        
        return Response(
            stream_with_context(generate()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no'
            }
        )
        
    except Exception as e:
        print(f"Error processing streaming question: {e}")
        return jsonify({
            'error': f'An error occurred: {str(e)}'
        }), 500


@app.route('/api/study', methods=['POST'])
def generate_study():
    """
    API endpoint to generate a thematic Bible study.
    
    Request Body:
        {
            "topic": "Topic string"
        }

    Returns:
        JSON response containing the study text and source passages.
    """
    if not rag:
        return jsonify({
            'error': 'RAG pipeline not initialized.'
        }), 500
    
    try:
        data = request.get_json(silent=True) or {}
        topic = data.get('topic', '').strip()
        
        if not topic:
            return jsonify({
                'error': 'Topic is required'
            }), 400
        
        result = rag.generate_study(topic)
        
        if result.get('error'):
            return jsonify({
                'error': result['study']
            }), 500
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Error generating study: {e}")
        return jsonify({
            'error': f'An error occurred: {str(e)}'
        }), 500


@app.route('/api/prayer', methods=['POST'])
def generate_prayer():
    """
    API endpoint to generate a personalized prayer.
    
    Request Body:
        {
            "request": "Prayer request text"
        }

    Returns:
        JSON response containing the prayer text and source passages.
    """
    if not rag:
        return jsonify({
            'error': 'RAG pipeline not initialized.'
        }), 500
    
    try:
        data = request.get_json(silent=True) or {}
        req_text = data.get('request', '').strip()
        
        if not req_text:
            return jsonify({
                'error': 'Prayer request is required'
            }), 400
        
        result = rag.generate_prayer(req_text)
        
        if result.get('error'):
            return jsonify({
                'error': result['prayer']
            }), 500
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Error generating prayer: {e}")
        return jsonify({
            'error': f'An error occurred: {str(e)}'
        }), 500


@app.route('/api/study-stream', methods=['POST'])
def generate_study_stream():
    """
    API endpoint to generate a thematic Bible study with streaming.

    Uses Server-Sent Events (SSE) to stream the response.

    Request Body:
        {
            "topic": "Topic string"
        }

    Returns:
        Response: Event stream.
    """
    if not rag:
        return jsonify({
            'error': 'RAG pipeline not initialized.'
        }), 500
    
    try:
        data = request.get_json(silent=True) or {}
        topic = data.get('topic', '').strip()
        
        if not topic:
            return jsonify({
                'error': 'Topic is required'
            }), 400
        
        def generate():
            """Generator function for SSE streaming."""
            try:
                # Retrieve relevant passages first
                print(f"\n[STUDY] Topic: (hidden)")
                print("[INFO] Retrieving relevant passages...")
                passages = rag.retrieve_passages(topic)
                print(f"[OK] Found {len(passages)} relevant passages")
                
                if not passages:
                    yield f"event: error\ndata: {json.dumps({'error': 'Could not find relevant passages'})}\n\n"
                    return
                
                # Send passages first
                yield f"event: passages\ndata: {json.dumps({'passages': passages})}\n\n"
                
                # Build the study prompt
                context = "Here are relevant passages:\n\n"
                for i, passage in enumerate(passages, 1):
                    context += f"{i}. {passage['reference']}:\n\"{passage['text']}\"\n\n"
                    
                prompt = f"""You are AI Jesus, a wise teacher. Create a short Bible study on the topic: "{topic}".
        
{context}

Structure the study as follows:
1. **Introduction**: Briefly introduce the topic.
2. **Key Verses**: Discuss 2-3 of the provided verses and their meaning.
3. **Reflection**: Ask 2-3 questions to help the reader apply this to their life.
4. **Prayer**: A short closing prayer.

Keep the tone encouraging and insightful.
"""
                
                # Stream the response
                print("[AI] Generating Bible study (streaming)...")
                stream = ollama.generate(
                    model=rag.llm_model if rag else 'gemma3:4b',
                    prompt=prompt,
                    stream=True,
                    options={'temperature': 0.7},
                    keep_alive=OLLAMA_LLM_KEEP_ALIVE
                )
                
                for chunk in stream:
                    if chunk.get('response'):
                        yield f"event: chunk\ndata: {json.dumps({'text': chunk['response']})}\n\n"
                    if chunk.get('done'):
                        yield f"event: done\ndata: {json.dumps({'done': True})}\n\n"
                        print("[OK] Bible study generated")
                        break
                        
            except Exception as e:
                print(f"Error in streaming study: {e}")
                yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
        
        return Response(
            stream_with_context(generate()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no'
            }
        )
        
    except Exception as e:
        print(f"Error processing streaming study: {e}")
        return jsonify({
            'error': f'An error occurred: {str(e)}'
        }), 500


@app.route('/api/prayer-stream', methods=['POST'])
def generate_prayer_stream():
    """
    API endpoint to generate a personalized prayer with streaming.

    Uses Server-Sent Events (SSE) to stream the response.

    Request Body:
        {
            "request": "Prayer request text"
        }

    Returns:
        Response: Event stream.
    """
    if not rag:
        return jsonify({
            'error': 'RAG pipeline not initialized.'
        }), 500
    
    try:
        data = request.get_json(silent=True) or {}
        req_text = data.get('request', '').strip()
        
        if not req_text:
            return jsonify({
                'error': 'Prayer request is required'
            }), 400
        
        def generate():
            """Generator function for SSE streaming."""
            try:
                # Retrieve relevant passages first
                print(f"\n[PRAYER] Request: (hidden)")
                print("[INFO] Retrieving relevant passages...")
                passages = rag.retrieve_passages(req_text)
                print(f"[OK] Found {len(passages)} relevant passages")
                
                # Send passages (even if empty)
                yield f"event: passages\ndata: {json.dumps({'passages': passages[:3]})}\n\n"
                
                # Build the prayer prompt
                context = ""
                if passages:
                    context = "Here are some relevant verses to inspire the prayer:\n\n"
                    for i, passage in enumerate(passages[:3], 1):
                        context += f"{i}. {passage['reference']}:\n\"{passage['text']}\"\n\n"
                
                prompt = f"""You are AI Jesus. A user has asked for prayer: "{req_text}".
        
{context}

Write a heartfelt, comforting prayer for them. 
- Address their specific situation.
- Weave in the themes from the verses if applicable.
- Keep it under 150 words.
- End with "Amen."
"""
                
                # Stream the response
                print("[AI] Generating prayer (streaming)...")
                stream = ollama.generate(
                    model=rag.llm_model if rag else 'gemma3:4b',
                    prompt=prompt,
                    stream=True,
                    options={'temperature': 0.8},
                    keep_alive=OLLAMA_LLM_KEEP_ALIVE
                )
                
                for chunk in stream:
                    if chunk.get('response'):
                        yield f"event: chunk\ndata: {json.dumps({'text': chunk['response']})}\n\n"
                    if chunk.get('done'):
                        yield f"event: done\ndata: {json.dumps({'done': True})}\n\n"
                        print("[OK] Prayer generated")
                        break
                        
            except Exception as e:
                print(f"Error in streaming prayer: {e}")
                yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
        
        return Response(
            stream_with_context(generate()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no'
            }
        )
        
    except Exception as e:
        print(f"Error processing streaming prayer: {e}")
        return jsonify({
            'error': f'An error occurred: {str(e)}'
        }), 500


# Version display names mapping (KISS - single source of truth)
VERSION_NAMES = {
    'kjv': 'King James Version',
    'esv': 'English Standard Version',
    'niv': 'New International Version',
    'nasb': 'New American Standard Bible',
    'nkjv': 'New King James Version',
    'nlt': 'New Living Translation',
    'csb': 'Christian Standard Bible',
    'asv': 'American Standard Version',
    'web': 'World English Bible',
    'bsb': 'Berean Standard Bible',
    'blb': 'Berean Literal Bible',
    'net': 'NET Bible',
    'gnt': 'Good News Translation',
    'cev': 'Contemporary English Version',
    'nrsv': 'New Revised Standard Version',
    'hcsb': 'Holman Christian Standard Bible',
    'amp': 'Amplified Bible',
    'nasb95': 'NASB 1995',
    'nasb77': 'NASB 1977',
    'ylt': "Young's Literal Translation",
    'drb': 'Douay-Rheims Bible',
    'lsv': 'Literal Standard Version',
    'lsb': 'Legacy Standard Bible',
    'msb': 'Majority Standard Bible',
}

# Curated list of inspiring verses for "Verse of the Day"
INSPIRING_VERSES = [
    ("John", 3, 16),
    ("Jeremiah", 29, 11),
    ("Philippians", 4, 13),
    ("Romans", 8, 28),
    ("Proverbs", 3, 5),
    ("Isaiah", 41, 10),
    ("Psalm", 23, 1),
    ("Matthew", 11, 28),
    ("Joshua", 1, 9),
    ("Romans", 12, 2),
    ("Psalm", 46, 1),
    ("Proverbs", 18, 10),
    ("Isaiah", 40, 31),
    ("Philippians", 4, 6),
    ("Psalm", 91, 1),
    ("Matthew", 6, 33),
    ("2 Timothy", 1, 7),
    ("Hebrews", 11, 1),
    ("1 Corinthians", 13, 4),
    ("Galatians", 5, 22),
    ("Ephesians", 2, 8),
    ("James", 1, 5),
    ("1 Peter", 5, 7),
    ("Psalm", 119, 105),
    ("John", 14, 6),
    ("Romans", 5, 8),
    ("Psalm", 37, 4),
    ("Matthew", 5, 14),
    ("John", 8, 32),
    ("Lamentations", 3, 22),
]


@app.route('/api/verse-of-the-day', methods=['GET'])
def get_verse_of_the_day():
    """Return a random inspiring verse - changes daily based on date seed."""
    import random
    from datetime import date
    
    # Use today's date as seed for consistent daily verse
    today = date.today()
    seed = today.year * 10000 + today.month * 100 + today.day
    random.seed(seed)
    
    book, chapter, verse_num = random.choice(INSPIRING_VERSES)
    version = request.args.get('version', DEFAULT_VERSION)
    
    try:
        # Get the verse text
        verses = get_verses_for_chapter(book, chapter, version, BIBLE_DATA_DIR)
        verse_text = None
        for v_num, text in verses:
            if int(v_num) == verse_num:
                verse_text = text
                break
        
        if not verse_text:
            verse_text = "The Lord is my shepherd; I shall not want."
            book, chapter, verse_num = "Psalm", 23, 1
        
        return jsonify({
            'reference': f"{book} {chapter}:{verse_num}",
            'text': verse_text,
            'book': book,
            'chapter': chapter,
            'verse': verse_num,
            'version': version.upper()
        })
    except Exception as e:
        # Fallback verse
        return jsonify({
            'reference': "Psalm 23:1",
            'text': "The Lord is my shepherd; I shall not want.",
            'book': "Psalm",
            'chapter': 23,
            'verse': 1,
            'version': version.upper()
        })


@app.route('/api/compare-verse', methods=['GET'])
def compare_verse():
    """Compare the same verse across multiple Bible versions."""
    book = request.args.get('book')
    chapter = request.args.get('chapter', type=int)
    verse = request.args.get('verse', type=int)
    versions_param = request.args.get('versions', '')  # comma-separated
    
    if not all([book, chapter, verse]):
        return jsonify({'error': 'Missing book, chapter, or verse parameter'}), 400
    
    # Parse versions or use all available
    if versions_param:
        requested_versions = [v.strip().lower() for v in versions_param.split(',')]
    else:
        requested_versions = list(BIBLE_INDICES.keys())
    
    comparisons = []
    for version in requested_versions:
        if version not in BIBLE_INDICES:
            continue
        try:
            verses = get_verses_for_chapter(book, chapter, version, BIBLE_DATA_DIR)
            for v_num, text in verses:
                if int(v_num) == verse:
                    comparisons.append({
                        'version': version.upper(),
                        'version_name': VERSION_NAMES.get(version, version.upper()),
                        'text': text
                    })
                    break
        except Exception as e:
            continue
    
    return jsonify({
        'reference': f"{book} {chapter}:{verse}",
        'book': book,
        'chapter': chapter,
        'verse': verse,
        'comparisons': comparisons
    })


@app.route('/api/versions', methods=['GET'])
def get_versions():
    """Return list of available Bible versions with display names."""
    available = list(BIBLE_INDICES.keys())
    versions = []
    for code in available:
        versions.append({
            'code': code,
            'name': VERSION_NAMES.get(code, code.upper()),
            'short': code.upper()
        })
    # Sort by name, but keep KJV first
    versions.sort(key=lambda v: (v['code'] != 'kjv', v['name']))
    return jsonify({'versions': versions})


@app.route('/api/bible-index', methods=['GET'])
def get_bible_index():
    """Return the structure of the Bible library."""
    version = request.args.get('version', DEFAULT_VERSION)
    index = BIBLE_INDICES.get(version, [])
    return jsonify({
        'testaments': index,
        'version': version,
        'versions': list(BIBLE_INDICES.keys())
    })


@app.route('/api/bible-passage', methods=['GET'])
def get_bible_passage():
    """
    Returns the verses for a specific Bible chapter.
    Works with both JSON and markdown formats.
    Query parameters:
        path    - virtual path (version/book/chapter) - optional
        book    - Book name (e.g., "Job")
        chapter - Chapter number
        version - Bible version (default: kjv)
        start   - optional starting verse number
        end     - optional ending verse number
    """
    relative_path = request.args.get('path', '').strip()
    book_param = request.args.get('book', '').strip()
    chapter_param = _safe_int(request.args.get('chapter'))
    version_param = request.args.get('version', DEFAULT_VERSION).strip()
    
    start = _safe_int(request.args.get('start'))
    end = _safe_int(request.args.get('end'))
    
    # Parse path if provided (format: version/book/chapter)
    if relative_path:
        parts = relative_path.split('/')
        if len(parts) >= 3:
            version_param = parts[0]
            book_param = parts[1]
            chapter_param = _safe_int(parts[2])
    
    if not book_param or chapter_param is None:
        return jsonify({
            'error': 'Provide either a path or both book and chapter parameters.'
        }), 400
    
    # Get verses from the appropriate source
    try:
        verses = get_verses_for_chapter(version_param, book_param, chapter_param, BIBLE_DATA_DIR)
        if not verses:
            return jsonify({'error': f'Bible passage not found for {book_param} {chapter_param}'}), 404
        
        # Normalize the book name
        canonical_book = normalize_book_name(book_param)
        testament = get_testament(canonical_book)
        
        return jsonify({
            'book': canonical_book,
            'testament': testament,
            'chapter': str(chapter_param),
            'path': f"{version_param}/{canonical_book}/{chapter_param}",
            'version': version_param,
            'verses': [{'number': v_num, 'text': v_text} for v_num, v_text in verses],
            'highlight': {
                'start': start,
                'end': end
            }
        })
    except FileNotFoundError:
        return jsonify({'error': 'Bible passage not found'}), 404
    except Exception as e:
        print(f"Error getting bible passage: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/verse-preview', methods=['GET'])
def get_verse_preview():
    """
    Returns the text of specific verses for tooltip preview.

    Query parameters:
        book        - Book name (e.g., "Proverbs")
        chapter     - Chapter number
        verse_start - Starting verse number
        verse_end   - Ending verse number (optional, defaults to verse_start)
        version     - Bible version (default: kjv)
    """
    book = request.args.get('book', '').strip()
    chapter_raw = request.args.get('chapter', '').strip()
    chapter_num = _safe_int(chapter_raw)
    verse_start = _safe_int(request.args.get('verse_start'))
    verse_end = _safe_int(request.args.get('verse_end'))
    version = request.args.get('version', DEFAULT_VERSION).strip()
    
    if not book or chapter_num is None or verse_start is None:
        return jsonify({'error': 'book, chapter, and verse_start are required'}), 400
    
    if verse_end is None:
        verse_end = verse_start
    
    try:
        verses = get_verses_for_chapter(version, book, chapter_num, BIBLE_DATA_DIR)
        if not verses:
            return jsonify({'error': f'Chapter not found: {book} {chapter_num}'}), 404
        
        canonical_book = normalize_book_name(book)
        
        # Filter to requested verse range
        selected_verses = []
        for verse_num_str, verse_text in verses:
            verse_number = _safe_int(verse_num_str)
            if verse_number is None:
                continue
            if verse_start <= verse_number <= verse_end:
                selected_verses.append(f"{verse_number}. {verse_text}")
        
        if not selected_verses:
            return jsonify({
                'error': f'Verses not found: {book} {chapter_num}:{verse_start}-{verse_end}'
            }), 404
        
        return jsonify({
            'book': canonical_book,
            'chapter': chapter_num,
            'verse_start': verse_start,
            'verse_end': verse_end,
            'text': ' '.join(selected_verses),
            'version': version
        })
        
    except Exception as e:
        print(f"Error fetching verse preview: {e}")
        return jsonify({'error': 'Failed to fetch verse'}), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """
    Health check endpoint.

    Returns:
        JSON status indicating if the service is healthy and RAG is initialized.
    """
    status = {
        'status': 'healthy',
        'rag_initialized': rag is not None
    }
    
    if rag:
        try:
            # Check if database has passages
            count = rag.collection.count()
            status['passages_count'] = count
        except:
            status['passages_count'] = 0
    
    return jsonify(status)


@app.errorhandler(404)
def not_found(e):
    """
    Handle 404 errors.

    Returns:
        JSON error message with 404 status.
    """
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def server_error(e):
    """
    Handle 500 errors.

    Returns:
        JSON error message with 500 status.
    """
    return jsonify({'error': 'Internal server error'}), 500


def _safe_int(value: Any) -> Optional[int]:
    """
    Convert a value to int when possible.

    Args:
        value: The input value.

    Returns:
        Optional[int]: The integer value, or None if conversion fails.
    """
    try:
        if value is None or value == '':
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def _derive_metadata_from_path(relative_path: str) -> Tuple[str, str, str]:
    """
    Derive (book, testament, chapter) from a bible-data relative path.

    Args:
        relative_path: The relative path to the markdown file.

    Returns:
        Tuple[str, str, str]: (book, testament, chapter) strings.
    """
    path = Path(relative_path)
    parts = path.parts
    
    # Check if first part is a known version
    if parts and parts[0] in BIBLE_INDICES:
        # Structure: version/Testament/Book/Chapter
        testament = parts[1] if len(parts) > 1 else ""
        book_folder = parts[2] if len(parts) > 2 else ""
    else:
        # Structure: Testament/Book/Chapter
        testament = parts[0] if parts else ""
        book_folder = parts[1] if len(parts) > 1 else ""
        
    book = extract_book_name(book_folder)
    chapter = extract_chapter_number(path.name)
    return book, testament, chapter


def _find_chapter_markdown(book: str, chapter: int, version: str = DEFAULT_VERSION):
    """Locate a chapter markdown file using a book/chapter reference."""
    normalized_book = normalize_book_name(book)
    if not normalized_book:
        raise ValueError('A valid book name is required to locate a passage.')
    
    chapter_num = _safe_int(chapter)
    if chapter_num is None:
        raise ValueError('A valid chapter number is required to locate a passage.')
    
    version_dir = BIBLE_DATA_DIR / version
    if not version_dir.exists():
         raise FileNotFoundError(f'Bible version not found: {version}')

    for testament in ('Old Testament', 'New Testament'):
        testament_dir = version_dir / testament
        if not testament_dir.exists():
            continue
        
        for book_dir in testament_dir.iterdir():
            if not book_dir.is_dir():
                continue
            
            book_name = extract_book_name(book_dir.name)
            if normalize_book_name(book_name) != normalized_book:
                continue
            
            for chapter_file in sorted(book_dir.glob('*.md')):
                file_chapter = _safe_int(extract_chapter_number(chapter_file))
                if file_chapter == chapter_num:
                    absolute_path = chapter_file.resolve()
                    # Return path relative to BIBLE_DATA_DIR (which includes version folder)
                    # Wait, resolve_bible_path expects path relative to BIBLE_ROOT (bible-data)
                    # So we should return path relative to BIBLE_DATA_DIR
                    relative_path = absolute_path.relative_to(BIBLE_DATA_DIR).as_posix()
                    return absolute_path, relative_path, book_name, testament
    
    raise FileNotFoundError(f'Chapter not found: {book} {chapter} in {version}')


@app.route('/bible/<book>/<chapter>')
def bible_chapter_legacy(book, chapter):
    """Serve a specific Bible chapter with SSR (default version)."""
    return bible_chapter(DEFAULT_VERSION, book, chapter)


@app.route('/bible/<version>/<book>/<chapter>')
def bible_chapter(version, book, chapter):
    """Serve a specific Bible chapter with SSR."""
    try:
        # Normalize inputs
        book_name = normalize_book_name(book)
        chapter_num = int(chapter)
        
        # Get verses from JSON or markdown
        verses = get_verses_for_chapter(version, book_name, chapter_num, BIBLE_DATA_DIR)
        
        if not verses:
            abort(404)
        
        # Get proper book name
        proper_book_name = book_name
        
        # Format content as HTML
        passage_html = []
        for v_num, v_text in verses:
            passage_html.append(
                f'<div class="verse-row" id="{v_num}">'
                f'<span class="verse-number">{v_num}</span> '
                f'<span class="verse-text">{v_text}</span>'
                f'</div>'
            )
        passage_content = "\n".join(passage_html)
        
        # Get navigation
        prev_chap, next_chap = get_next_prev_chapters(book_name, chapter_num, version=version)
        
        prev_url = None
        if prev_chap:
            if version == DEFAULT_VERSION:
                prev_url = url_for('bible_chapter_legacy', book=prev_chap['book'], chapter=prev_chap['chapter'])
            else:
                prev_url = url_for('bible_chapter', version=version, book=prev_chap['book'], chapter=prev_chap['chapter'])

        next_url = None
        if next_chap:
            if version == DEFAULT_VERSION:
                next_url = url_for('bible_chapter_legacy', book=next_chap['book'], chapter=next_chap['chapter'])
            else:
                next_url = url_for('bible_chapter', version=version, book=next_chap['book'], chapter=next_chap['chapter'])
        
        # Metadata
        version_upper = version.upper()
        title = f"{proper_book_name} {chapter_num} - {version_upper} Bible | WWAIJD"
        description = f"Read {proper_book_name} Chapter {chapter_num} of the {version_upper} Bible. {verses[0][1][:100]}..."
        
        if version == DEFAULT_VERSION:
            canonical_url = url_for('bible_chapter_legacy', book=proper_book_name, chapter=chapter_num, _external=True)
        else:
            canonical_url = url_for('bible_chapter', version=version, book=proper_book_name, chapter=chapter_num, _external=True)
        
        # Schema.org
        schema = {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": f"{proper_book_name} Chapter {chapter_num}",
            "description": description,
            "inLanguage": "en",
            "isPartOf": {
                "@type": "Book",
                "name": "The Holy Bible",
                "bookEdition": f"{version_upper} Version"
            }
        }
        
        # Build version list for template
        available_versions = []
        for code in BIBLE_INDICES.keys():
            available_versions.append({
                'code': code,
                'name': VERSION_NAMES.get(code, code.upper()),
                'short': code.upper()
            })
        available_versions.sort(key=lambda v: (v['code'] != 'kjv', v['name']))
        
        return render_template(
            'passage.html',
            title=title,
            description=description,
            canonical_url=canonical_url,
            og_url=canonical_url,
            og_title=title,
            og_description=description,
            twitter_url=canonical_url,
            twitter_title=title,
            twitter_description=description,
            schema_json=json.dumps(schema),
            passage_title=f"{proper_book_name} {chapter_num}",
            passage_subtitle=f"{version_upper} Version",
            passage_content=passage_content,
            prev_chapter_url=prev_url,
            next_chapter_url=next_url,
            book=proper_book_name,
            chapter=chapter_num,
            version=version,
            available_versions=available_versions
        )
        
    except Exception as e:
        print(f"Error serving chapter: {e}")
        abort(404)


@app.route('/sitemap.xml')
def sitemap():
    """
    Generate dynamic XML sitemap for SEO.

    Includes main pages and all Bible books/chapters to help search engines
    index the content.

    Returns:
        Response: XML sitemap content.
    """
    base_url = 'https://wwaijd.org'
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Start XML
    xml = ['<?xml version="1.0" encoding="UTF-8"?>']
    xml.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    
    # Main pages
    main_pages = [
        {'loc': '/', 'priority': '1.0', 'changefreq': 'daily'},
        {'loc': '/static/bible.html', 'priority': '0.9', 'changefreq': 'weekly'},
        {'loc': '/static/passage.html', 'priority': '0.7', 'changefreq': 'monthly'},
    ]
    
    for page in main_pages:
        xml.append('  <url>')
        xml.append(f'    <loc>{base_url}{page["loc"]}</loc>')
        xml.append(f'    <lastmod>{today}</lastmod>')
        xml.append(f'    <changefreq>{page["changefreq"]}</changefreq>')
        xml.append(f'    <priority>{page["priority"]}</priority>')
        xml.append('  </url>')
    
    # Bible books and chapters
    try:
        # Iterate through all available versions
        # If BIBLE_INDICES is empty, try to build at least the default one
        indices_to_process = BIBLE_INDICES if BIBLE_INDICES else {DEFAULT_VERSION: build_bible_index(BIBLE_DATA_DIR)}
        
        for version_code, bible_index in indices_to_process.items():
            is_default = (version_code == DEFAULT_VERSION)
            
            for testament_data in bible_index:
                for book_data in testament_data['books']:
                    book_name = book_data['name']
                    # Use the actual chapters list from the index
                    for chapter_data in book_data['chapters']:
                        chapter_num = chapter_data['number']
                        # URL encode book name
                        safe_book = book_name.replace(' ', '%20')
                        
                        # Generate URL for this version
                        xml.append('  <url>')
                        if is_default:
                            # Default version gets the clean short URL
                            xml.append(f'    <loc>{base_url}/bible/{safe_book}/{chapter_num}</loc>')
                        else:
                            # Other versions get the version-prefixed URL
                            xml.append(f'    <loc>{base_url}/bible/{version_code}/{safe_book}/{chapter_num}</loc>')
                            
                        xml.append(f'    <lastmod>{today}</lastmod>')
                        xml.append('    <changefreq>yearly</changefreq>')
                        xml.append('    <priority>0.6</priority>')
                        xml.append('  </url>')
                        
    except Exception as e:
        print(f"Warning: Could not generate Bible URLs for sitemap: {e}", flush=True)
    
    xml.append('</urlset>')
    
    return Response('\n'.join(xml), mimetype='application/xml')


@app.route('/api/share', methods=['POST'])
def share_conversation():
    """
    Save a conversation and return a shareable link.

    Request Body:
        {
            "question": "Question text",
            "answer": "Answer text",
            "passages": [Passage objects],
            "mode": "Tone mode"
        }

    Returns:
        JSON response with share_id and share_url.
    """
    try:
        data = request.get_json(silent=True) or {}
        question = data.get('question')
        answer = data.get('answer')
        passages = data.get('passages')
        mode = data.get('mode', 'balanced')
        
        if not question or not answer:
            return jsonify({'error': 'Missing question or answer'}), 400
            
        share_id = database.save_conversation(question, answer, passages, mode)
        share_url = url_for('shared_page', share_id=share_id, _external=True)
        
        return jsonify({
            'share_id': share_id,
            'share_url': share_url
        })
        
    except Exception as e:
        print(f"Error sharing conversation: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/q/<share_id>')
def shared_page(share_id):
    """
    Render a shared conversation page.

    Args:
        share_id: The unique conversation ID.

    Returns:
        Response: Rendered HTML template or 404 abort.
    """
    try:
        data = database.get_conversation(share_id)
        if not data:
            abort(404)
            
        # Parse passages if stored as JSON string
        passages = data['passages']
        if isinstance(passages, str):
            try:
                passages = json.loads(passages)
            except:
                passages = []
                
        # Render markdown answer to HTML
        answer_html = markdown.markdown(data['answer'])
        
        # Metadata
        title = f"{data['question']} - AI Jesus Answer | WWAIJD"
        description = f"AI Jesus answers: {data['question']}. Read the biblical perspective and scripture references."
        canonical_url = url_for('shared_page', share_id=share_id, _external=True)
        
        # Schema.org
        schema = {
            "@context": "https://schema.org",
            "@type": "QAPage",
            "mainEntity": {
                "@type": "Question",
                "name": data['question'],
                "text": data['question'],
                "answerCount": 1,
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": data['answer'],
                    "dateCreated": data['created_at'],
                    "author": {
                        "@type": "Organization",
                        "name": "What Would AI Jesus Do"
                    }
                }
            }
        }
        
        return render_template(
            'share.html',
            title=title,
            description=description,
            canonical_url=canonical_url,
            og_url=canonical_url,
            og_title=title,
            og_description=description,
            twitter_url=canonical_url,
            twitter_title=title,
            twitter_description=description,
            schema_json=json.dumps(schema),
            question=data['question'],
            answer_html=answer_html,
            passages=passages,
            mode=data['mode'],
            date=data['created_at'][:10]
        )
        
    except Exception as e:
        print(f"Error rendering shared page: {e}")
        abort(404)

@app.route('/api/search', methods=['POST'])
def search_bible():
    """
    API endpoint to search for Bible passages without generating an LLM response.
    
    Request Body:
        {
            "query": "Search query"
        }
    
    Returns:
        JSON response with found passages and count.
    """
    if not rag:
        return jsonify({
            'error': 'RAG pipeline not initialized.'
        }), 500
    
    try:
        data = request.get_json(silent=True) or {}
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({
                'error': 'Search query is required'
            }), 400
            
        print(f"\n[SEARCH] Searching Bible...")
        passages = rag.retrieve_passages(query)
        print(f"[OK] Found {len(passages)} relevant passages")
        
        return jsonify({
            'passages': passages,
            'count': len(passages)
        })
        
    except Exception as e:
        print(f"Error searching Bible: {e}")
        return jsonify({
            'error': f'An error occurred: {str(e)}'
        }), 500


def main():
    """
    Run the Flask application using Waitress.

    This is the entry point for the production server.
    """
    print("=" * 60, flush=True)
    print("What Would AI Jesus Do - Web Application", flush=True)
    print("=" * 60, flush=True)
    
    if not rag:
        print("\n[!] WARNING: RAG pipeline not initialized!", flush=True)
        print("Please run 'python build_embeddings.py' first to create the vector database.", flush=True)
        print("=" * 60, flush=True)
    
    print("\n🚀 Starting production server with Waitress...", flush=True)
    print("📍 Open your browser to: http://localhost:5000", flush=True)
    print("\nPress Ctrl+C to stop the server", flush=True)
    print("=" * 60 + "\n", flush=True)
    
    # Run with Waitress production server
    serve(app, host='0.0.0.0', port=5000, threads=4)


if __name__ == '__main__':
    main()
