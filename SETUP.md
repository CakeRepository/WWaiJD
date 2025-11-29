# Quick Setup Guide

## Prerequisites Installation

### 1. Install Ollama
Visit [https://ollama.com/](https://ollama.com/) and download Ollama for your system.

### 2. Pull Required Models
After installing Ollama, run these commands in your terminal:

```bash
# Pull the Gemma embedding model (for creating vector embeddings)
ollama pull embeddinggemma

# Pull the Qwen3-VL:4b model (for generating responses)
ollama pull qwen3-vl:4b
```

**Note:** These models are large and may take some time to download.

## Application Setup

### 1. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 2. Download Bible Versions
Download Bible JSON files from the arron-taylor/bible-versions repository:

```bash
# Download popular versions (KJV, ESV, NIV, NLT, NASB, NKJV, CSB, ASV, WEB)
python download_bibles.py

# Or download ALL available versions (35+ files)
python download_bibles.py --all

# Or download a specific version
python download_bibles.py --version "KING JAMES BIBLE.json"

# List available versions
python download_bibles.py --list

# List locally downloaded versions
python download_bibles.py --local
```

Bible files are stored in `bible-data/json/` as JSON files.

### 3. Check Prerequisites
Run the startup check to verify everything is ready:
```bash
python startup_check.py
```

### 4. Build the Vector Database
This step processes the Bible versions and creates embeddings. **This will take 10-30 minutes** depending on your system and how many versions you downloaded:

```bash
python build_embeddings.py
```

You should see progress as it:
- Reads all Bible versions (JSON files)
- Chunks text into passages
- Generates embeddings for each chunk
- Stores them in ChromaDB

### 5. Test the RAG Pipeline (Optional)
You can test the RAG pipeline directly:
```bash
python rag_pipeline.py
```

### 6. Run the Web Application
```bash
python app.py
```

Open your browser to: **http://localhost:5000**

## Usage

Simply type your question in the search bar, such as:
- "What should I do when someone wrongs me?"
- "How should I treat my enemies?"
- "What does it mean to love my neighbor?"
- "How can I find peace in difficult times?"

You can also select different Bible versions (KJV, ESV, NIV, etc.) to see passages from your preferred translation.

## Troubleshooting

### "No Bible versions found"
- Run `python download_bibles.py` to download Bible versions
- Check if `bible-data/json/` directory contains JSON files

### "Ollama is not running"
- Make sure Ollama is installed and running
- On Windows, check if the Ollama service is started
- Try restarting Ollama

### "Model not found"
- Run `ollama list` to see installed models
- Pull missing models with `ollama pull <model-name>`

### "Vector database not found"
- Make sure you've run `python build_embeddings.py`
- Check if the `chroma_db/` directory exists

### Slow responses
- The first request may be slower as models load into memory
- Subsequent requests should be faster
- Larger models (like qwen3-vl:4b) require more RAM

## Bible Data Source

Bible data is sourced from [arron-taylor/bible-versions](https://github.com/arron-taylor/bible-versions), 
a comprehensive JSON dataset with 35+ English Bible translations.

Available versions include: KJV, ESV, NIV, NLT, NASB, NKJV, CSB, ASV, WEB, and many more!

## Architecture

```
┌─────────────┐
│   Browser   │
│   (UI)      │
└─────┬───────┘
      │ HTTP
      ▼
┌─────────────┐
│   Flask     │
│   Server    │
└─────┬───────┘
      │
      ▼
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│  RAG        │─────▶│   ChromaDB   │      │   Ollama    │
│  Pipeline   │      │  (Vectors)   │      │   Gemma     │
│             │◀─────┤              │◀─────┤   Qwen3-VL  │
└─────────────┘      └──────────────┘      └─────────────┘
```

1. User asks a question via the web UI
2. Flask server receives the question
3. RAG pipeline generates query embedding using Gemma
4. ChromaDB retrieves relevant Bible passages
5. Qwen3-VL generates a response based on the passages
6. Response is displayed to the user with source references

## Files Overview

- `app.py` - Flask web server
- `rag_pipeline.py` - RAG logic (retrieval + generation)
- `build_embeddings.py` - Creates vector database from Bible
- `startup_check.py` - Checks prerequisites
- `static/index.html` - Web UI
- `static/style.css` - Styles
- `static/script.js` - Frontend logic
- `bible-data/` - King James Bible markdown files
- `chroma_db/` - Vector database (created after setup)
