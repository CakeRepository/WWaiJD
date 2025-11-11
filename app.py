"""
What Would AI Jesus Do - Flask Application
Main web server that connects the frontend to the RAG pipeline
"""

from flask import Flask, request, jsonify, send_from_directory, Response, stream_with_context
from waitress import serve
from pathlib import Path
import json
from bible_utils import (
    build_bible_index,
    extract_book_name,
    extract_chapter_number,
    parse_verses,
    resolve_bible_path,
)
from rag_pipeline import BibleRAG

app = Flask(__name__, static_folder='static')

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
    print("✅ RAG pipeline initialized successfully")
except Exception as e:
    print(f"⚠️  Warning: Could not initialize RAG pipeline: {e}")
    print("Make sure you've run 'python build_embeddings.py' first!")
    rag = None


@app.route('/')
def index():
    """Serve the main page."""
    return send_from_directory('static', 'index.html')


@app.route('/static/<path:path>')
def serve_static(path):
    """Serve static files."""
    return send_from_directory('static', path)


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
    if not relative_path:
        return jsonify({'error': 'path parameter is required'}), 400

    start = _safe_int(request.args.get('start'))
    end = _safe_int(request.args.get('end'))

    try:
        chapter_path = resolve_bible_path(relative_path)
    except FileNotFoundError:
        return jsonify({'error': 'Bible passage not found'}), 404
    except ValueError:
        return jsonify({'error': 'Invalid bible path provided'}), 400

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
    chapter = request.args.get('chapter', '').strip()
    verse_start = _safe_int(request.args.get('verse_start'))
    verse_end = _safe_int(request.args.get('verse_end'))
    
    if not book or not chapter or verse_start is None:
        return jsonify({'error': 'book, chapter, and verse_start are required'}), 400
    
    # If verse_end not provided, use verse_start
    if verse_end is None:
        verse_end = verse_start
    
    try:
        # Normalize book name to handle variations (Psalm -> Psalms)
        normalized_book = normalize_book_name(book)
        
        # Find the chapter file for this book and chapter
        bible_data_dir = Path(__file__).parent / 'bible-data'
        
        # Search in both Old and New Testament
        chapter_path = None
        for testament in ['Old Testament', 'New Testament']:
            testament_dir = bible_data_dir / testament
            if testament_dir.exists():
                for book_dir in testament_dir.iterdir():
                    if book_dir.is_dir():
                        # Extract book name from directory (remove number prefix)
                        dir_book_name = extract_book_name(book_dir.name)
                        dir_book_normalized = normalize_book_name(dir_book_name)
                        
                        # Match using both original and normalized names
                        if (dir_book_name.lower() == book.lower() or 
                            dir_book_name.lower() == normalized_book or
                            dir_book_normalized == normalized_book):
                            
                            # Try multiple filename patterns
                            # For Psalms, files are named "psalm" (singular)
                            # Use the incoming book name for the file pattern
                            possible_base_names = [
                                book.lower().replace(' ', ''),           # Use what user requested
                                dir_book_name.lower().replace(' ', ''),  # Use directory name
                                normalized_book.replace(' ', ''),        # Use normalized name
                            ]
                            
                            # Remove duplicates while preserving order
                            seen = set()
                            unique_base_names = []
                            for name in possible_base_names:
                                if name not in seen:
                                    seen.add(name)
                                    unique_base_names.append(name)
                            
                            # Try all combinations
                            for book_name_lower in unique_base_names:
                                # Try both with and without zero-padding
                                possible_names = [
                                    f"{book_name_lower}{str(chapter).zfill(2)}.md",  # psalm35.md
                                    f"{book_name_lower}{str(chapter)}.md",           # psalm35.md (same for Psalms)
                                ]
                                
                                for filename in possible_names:
                                    chapter_file = book_dir / filename
                                    if chapter_file.exists():
                                        chapter_path = chapter_file
                                        break
                                
                                if chapter_path:
                                    break
                            
                            if chapter_path:
                                break
            if chapter_path:
                break
        
        if not chapter_path:
            return jsonify({'error': f'Chapter not found: {book} {chapter}'}), 404
        
        # Read and parse the chapter
        with open(chapter_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        verses = parse_verses(content)
        
        # Extract the requested verses (convert verse_num to int for comparison)
        selected_verses = []
        for verse_num, verse_text in verses:
            # Ensure verse_num is int for comparison
            if isinstance(verse_num, str):
                verse_num = int(verse_num)
            if verse_start <= verse_num <= verse_end:
                selected_verses.append(f"{verse_num}. {verse_text}")
        
        if not selected_verses:
            return jsonify({'error': f'Verses not found: {book} {chapter}:{verse_start}-{verse_end}'}), 404
        
        return jsonify({
            'book': book,
            'chapter': chapter,
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


def main():
    """Run the Flask application."""
    print("=" * 60)
    print("What Would AI Jesus Do - Web Application")
    print("=" * 60)
    
    if not rag:
        print("\n⚠️  WARNING: RAG pipeline not initialized!")
        print("Please run 'python build_embeddings.py' first to create the vector database.")
        print("=" * 60)
    
    print("\n🚀 Starting production server with Waitress...")
    print("📍 Open your browser to: http://localhost:5000")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 60 + "\n")
    
    # Run with Waitress production server
    serve(app, host='0.0.0.0', port=5000, threads=4)


if __name__ == '__main__':
    main()
