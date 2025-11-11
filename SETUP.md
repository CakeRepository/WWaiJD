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

### 2. Check Prerequisites
Run the startup check to verify everything is ready:
```bash
python startup_check.py
```

### 3. Build the Vector Database
This step processes the King James Bible and creates embeddings. **This will take 10-30 minutes** depending on your system:

```bash
python build_embeddings.py
```

You should see progress as it:
- Reads all Bible books
- Chunks text into passages
- Generates embeddings for each chunk
- Stores them in ChromaDB

### 4. Test the RAG Pipeline (Optional)
You can test the RAG pipeline directly:
```bash
python rag_pipeline.py
```

### 5. Run the Web Application
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

The AI will retrieve relevant Bible passages and provide guidance based on Biblical teachings.

## Troubleshooting

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
