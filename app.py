"""
What Would AI Jesus Do - Flask Application
Main web server that connects the frontend to the RAG pipeline
"""

import os
import sys

# Force unbuffered output to prevent "hit enter" issue on some servers
os.environ['PYTHONUNBUFFERED'] = '1'
sys.stdout.reconfigure(line_buffering=True) if hasattr(sys.stdout, 'reconfigure') else None

from flask import Flask, request, jsonify, send_from_directory, Response, stream_with_context
from waitress import serve
from pathlib import Path
import json
from datetime import datetime
from bible_utils import (
    build_bible_index,
    extract_book_name,
    extract_chapter_number,
    parse_verses,
    resolve_bible_path,
)
from rag_pipeline import BibleRAG

app = Flask(__name__, static_folder='static')
BIBLE_DATA_DIR = (Path(__file__).parent / 'bible-data').resolve()

# Book name variations mapping
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

def normalize_book_name(book_name):
    """Normalize book names to handle common variations."""
    normalized = book_name.lower().strip()
    return BOOK_NAME_VARIATIONS.get(normalized, normalized)

# Initialize RAG pipeline
try:
    rag = BibleRAG()
    print("✅ RAG pipeline initialized successfully", flush=True)
except Exception as e:
    print(f"⚠️  Warning: Could not initialize RAG pipeline: {e}", flush=True)
    print("Make sure you've run 'python build_embeddings.py' first!", flush=True)
    rag = None


@app.route('/')
def index():
    """Serve the main page."""
    return send_from_directory('static', 'index.html')


@app.route('/static/<path:path>')
def serve_static(path):
    """Serve static files."""
    return send_from_directory('static', path)


@app.route('/robots.txt')
def robots():
    """Serve robots.txt for search engine crawlers."""
    return send_from_directory('static', 'robots.txt')


@app.route('/img/<path:path>')
def serve_image(path):
    """Serve image files for social media."""
    return send_from_directory('img', path)


@app.route('/api/ask', methods=['POST'])
def ask_question():
    """
    API endpoint to handle questions.
    
    Request body:
        {
            "question": "User's question"
        }
    
    Response:
        {
            "answer": "AI Jesus response",
            "passages": [
                {
                    "text": "Bible verse text",
                    "reference": "Book Chapter:Verses",
                    "book": "Book name",
                    "testament": "Old/New Testament"
                }
            ]
        }
    """
    if not rag:
        return jsonify({
            'error': 'RAG pipeline not initialized. Please run build_embeddings.py first.'
        }), 500
    
    try:
        # Get question from request
        data = request.get_json()
        question = data.get('question', '').strip()
        
        if not question:
            return jsonify({
                'error': 'Question is required'
            }), 400
        
        # Get response from RAG pipeline
        result = rag.ask(question)
        
        if result.get('error'):
            return jsonify({
                'error': result['answer']
            }), 500
        
        return jsonify({
            'answer': result['answer'],
            'passages': result['passages']
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
    Uses Server-Sent Events (SSE) to stream the AI response in real-time.
    
    Request body:
        {
            "question": "User's question"
        }
    
    Response: Server-Sent Events stream
        - event: chunk - Response text chunks
        - event: passages - Bible passages used
        - event: done - Stream complete
        - event: error - Error occurred
    """
    if not rag:
        return jsonify({
            'error': 'RAG pipeline not initialized. Please run build_embeddings.py first.'
        }), 500
    
    try:
        # Get question from request
        data = request.get_json()
        question = data.get('question', '').strip()
        
        if not question:
            return jsonify({
                'error': 'Question is required'
            }), 400
        
        def generate():
            """Generator function for SSE streaming."""
            try:
                # Retrieve relevant passages first
                print(f"\n🙏 Question: {question}")
                print("📖 Retrieving relevant Bible passages...")
                passages = rag.retrieve_passages(question)
                print(f"✅ Found {len(passages)} relevant passages")
                
                # Send passages first so UI can display them
                yield f"event: passages\ndata: {json.dumps({'passages': passages})}\n\n"
                
                # Stream the response
                print("🤖 Generating AI Jesus response (streaming)...")
                for chunk_data in rag.generate_response_stream(question, passages):
                    if chunk_data.get('error'):
                        yield f"event: error\ndata: {json.dumps({'error': chunk_data.get('chunk', 'Error occurred')})}\n\n"
                        break
                    elif chunk_data.get('chunk'):
                        # Send text chunk
                        yield f"event: chunk\ndata: {json.dumps({'text': chunk_data['chunk']})}\n\n"
                    
                    if chunk_data.get('done'):
                        yield f"event: done\ndata: {json.dumps({'done': True})}\n\n"
                        print("✅ Response generated")
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


@app.route('/api/bible-index', methods=['GET'])
def get_bible_index():
    """Return the structure of the Bible library."""
    index = build_bible_index()
    return jsonify({'testaments': index})


@app.route('/api/bible-passage', methods=['GET'])
def get_bible_passage():
    """
    Returns the verses for a specific Bible markdown chapter so the UI can render it.
    Query parameters:
        path  - relative markdown path inside bible-data (required)
        start - optional starting verse number
        end   - optional ending verse number
    """
    relative_path = request.args.get('path', '').strip()
    book_param = request.args.get('book', '').strip()
    chapter_param = _safe_int(request.args.get('chapter'))
    
    start = _safe_int(request.args.get('start'))
    end = _safe_int(request.args.get('end'))
    
    chapter_path = None
    
    if relative_path:
        try:
            chapter_path = resolve_bible_path(relative_path)
        except FileNotFoundError:
            return jsonify({'error': 'Bible passage not found'}), 404
        except ValueError:
            return jsonify({'error': 'Invalid bible path provided'}), 400
    else:
        if not book_param or chapter_param is None:
            return jsonify({
                'error': 'Provide either a bible path or both book and chapter parameters.'
            }), 400
        try:
            chapter_path, relative_path, _, _ = _find_chapter_markdown(book_param, chapter_param)
        except FileNotFoundError:
            return jsonify({
                'error': f'Bible passage not found for {book_param} {chapter_param}'
            }), 404
        except ValueError as exc:
            return jsonify({'error': str(exc)}), 400

    with open(chapter_path, 'r', encoding='utf-8') as f:
        content = f.read()

    verses = parse_verses(content)
    book, testament, chapter = _derive_metadata_from_path(relative_path)

    return jsonify({
        'book': book,
        'testament': testament,
        'chapter': chapter,
        'path': relative_path,
        'verses': [{'number': v_num, 'text': v_text} for v_num, v_text in verses],
        'highlight': {
            'start': start,
            'end': end
        }
    })


@app.route('/api/verse-preview', methods=['GET'])
def get_verse_preview():
    """
    Returns the text of specific verses for tooltip preview.
    Query parameters:
        book        - Book name (e.g., "Proverbs")
        chapter     - Chapter number
        verse_start - Starting verse number
        verse_end   - Ending verse number (optional, defaults to verse_start)
    """
    book = request.args.get('book', '').strip()
    chapter_raw = request.args.get('chapter', '').strip()
    chapter_num = _safe_int(chapter_raw)
    verse_start = _safe_int(request.args.get('verse_start'))
    verse_end = _safe_int(request.args.get('verse_end'))
    
    if not book or chapter_num is None or verse_start is None:
        return jsonify({'error': 'book, chapter, and verse_start are required'}), 400
    
    if verse_end is None:
        verse_end = verse_start
    
    try:
        chapter_path, _, canonical_book_name, _ = _find_chapter_markdown(book, chapter_num)
    except FileNotFoundError:
        return jsonify({'error': f'Chapter not found: {book} {chapter_raw or chapter_num}'}), 404
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400
    
    try:
        with open(chapter_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        verses = parse_verses(content)
        
        selected_verses = []
        for verse_num, verse_text in verses:
            verse_number = _safe_int(verse_num)
            if verse_number is None:
                continue
            if verse_start <= verse_number <= verse_end:
                selected_verses.append(f"{verse_number}. {verse_text}")
        
        if not selected_verses:
            return jsonify({
                'error': f'Verses not found: {book} {chapter_num}:{verse_start}-{verse_end}'
            }), 404
        
        return jsonify({
            'book': canonical_book_name or book,
            'chapter': chapter_num,
            'verse_start': verse_start,
            'verse_end': verse_end,
            'text': ' '.join(selected_verses)
        })
        
    except Exception as e:
        print(f"Error fetching verse preview: {e}")
        return jsonify({'error': 'Failed to fetch verse'}), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
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
    """Handle 404 errors."""
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors."""
    return jsonify({'error': 'Internal server error'}), 500


def _safe_int(value):
    """Convert a value to int when possible."""
    try:
        if value is None or value == '':
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def _derive_metadata_from_path(relative_path: str):
    """Derive (book, testament, chapter) from a bible-data relative path."""
    path = Path(relative_path)
    parts = path.parts
    testament = parts[0] if parts else ""
    book_folder = parts[1] if len(parts) > 1 else ""
    book = extract_book_name(book_folder)
    chapter = extract_chapter_number(path.name)
    return book, testament, chapter


def _find_chapter_markdown(book: str, chapter: int):
    """Locate a chapter markdown file using a book/chapter reference."""
    normalized_book = normalize_book_name(book)
    if not normalized_book:
        raise ValueError('A valid book name is required to locate a passage.')
    
    chapter_num = _safe_int(chapter)
    if chapter_num is None:
        raise ValueError('A valid chapter number is required to locate a passage.')
    
    for testament in ('Old Testament', 'New Testament'):
        testament_dir = BIBLE_DATA_DIR / testament
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
                    relative_path = absolute_path.relative_to(BIBLE_DATA_DIR).as_posix()
                    return absolute_path, relative_path, book_name, testament
    
    raise FileNotFoundError(f'Chapter not found: {book} {chapter}')


@app.route('/sitemap.xml')
def sitemap():
    """
    Generate dynamic XML sitemap for SEO.
    Includes main pages and all Bible books/chapters.
    """
    base_url = 'https://wwaijd.com'
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
        bible_index = build_bible_index(BIBLE_DATA_DIR)
        # bible_index is a list of testament dicts
        for testament_data in bible_index:
            for book_data in testament_data['books']:
                book_name = book_data['name']
                # Use the actual chapters list from the index
                for chapter_data in book_data['chapters']:
                    chapter_num = chapter_data['number']
                    # URL encode book name
                    safe_book = book_name.replace(' ', '%20')
                    xml.append('  <url>')
                    xml.append(f'    <loc>{base_url}/static/passage.html?book={safe_book}&amp;chapter={chapter_num}</loc>')
                    xml.append(f'    <lastmod>{today}</lastmod>')
                    xml.append('    <changefreq>yearly</changefreq>')
                    xml.append('    <priority>0.6</priority>')
                    xml.append('  </url>')
    except Exception as e:
        print(f"Warning: Could not generate Bible URLs for sitemap: {e}", flush=True)
    
    xml.append('</urlset>')
    
    return Response('\n'.join(xml), mimetype='application/xml')


def main():
    """Run the Flask application."""
    print("=" * 60, flush=True)
    print("What Would AI Jesus Do - Web Application", flush=True)
    print("=" * 60, flush=True)
    
    if not rag:
        print("\n⚠️  WARNING: RAG pipeline not initialized!", flush=True)
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
