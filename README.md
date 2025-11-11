# What Would AI Jesus Do (WWAIJD)

An AI-powered application that answers moral and spiritual questions based on the King James Bible using RAG (Retrieval Augmented Generation).

## Features

- 📖 Grounded in the King James Bible
- 🤖 Uses Ollama with Gemma embeddings and Qwen3-VL:4b model
- 🔍 RAG pipeline for contextually accurate responses
- 💬 Simple web interface

## Prerequisites

- Python 3.8+
- [Ollama](https://ollama.com/) installed locally
- Required Ollama models:
  - `ollama pull embeddinggemma`
  - `ollama pull qwen3-vl:4b`

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Build the vector database (first time only):
```bash
python build_embeddings.py
```

3. Run the application:
```bash
python app.py
```

4. Open your browser to `http://localhost:5000`

## Usage

Simply type your question in the search bar (e.g., "What should I do when someone wrongs me?") and receive guidance based on Biblical teachings.

## Project Structure

- `app.py` - Main Flask application
- `build_embeddings.py` - Script to process Bible and create vector database
- `rag_pipeline.py` - RAG logic for retrieval and generation
- `static/` - Frontend files (HTML, CSS, JS)
- `bible-data/` - King James Bible markdown files
- `chroma_db/` - Vector database (generated)
