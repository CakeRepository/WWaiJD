# What Would AI Jesus Do (WWAIJD) - Project Complete! 🎉

Your application has been successfully created! Here's everything you need to know:

## 📁 Project Structure

```
wwaijd/
├── app.py                  # Main Flask web server
├── rag_pipeline.py         # RAG logic (retrieval + AI response generation)
├── build_embeddings.py     # Script to create vector database from Bible
├── startup_check.py        # Checks if everything is ready to run
├── requirements.txt        # Python dependencies
├── README.md              # Project overview
├── SETUP.md               # Detailed setup instructions
├── .gitignore             # Git ignore file
├── static/                # Frontend files
│   ├── index.html         # Web interface
│   ├── style.css          # Styling
│   └── script.js          # Frontend logic
├── bible-data/            # King James Bible (markdown)
│   ├── Old Testament/     # All Old Testament books
│   └── New Testament/     # All New Testament books
└── chroma_db/             # Vector database (created after setup)
```

## 🚀 Quick Start

### Step 1: Install Ollama & Models
1. Install Ollama from https://ollama.com/
2. Pull required models:
   ```powershell
   ollama pull embeddinggemma
   ollama pull qwen3-vl:4b
   ```

### Step 2: Install Python Dependencies
```powershell
pip install -r requirements.txt
```

### Step 3: Check Your Setup
```powershell
python startup_check.py
```

### Step 4: Build the Vector Database (Takes 10-30 minutes)
```powershell
python build_embeddings.py
```

This will:
- Read all 66 books of the King James Bible
- Split them into meaningful passages
- Generate embeddings using Ollama's Gemma model
- Store everything in ChromaDB

### Step 5: Run the Application
```powershell
python app.py
```

Then open your browser to: **http://localhost:5000**

## 💡 How It Works

### The RAG Pipeline:

1. **User Question** → "What should I do when someone wrongs me?"

2. **Embedding Generation** → Gemma converts the question to a vector

3. **Semantic Search** → ChromaDB finds relevant Bible passages

4. **Context Building** → Top 5 most relevant passages are selected

5. **AI Response** → Qwen3-VL generates answer as "AI Jesus" based on passages

6. **Display** → Answer shown with source references

### Technology Stack:

- **Frontend**: Vanilla HTML/CSS/JavaScript (clean, responsive UI)
- **Backend**: Flask (Python web framework)
- **Vector DB**: ChromaDB (stores Bible embeddings)
- **Embeddings**: Ollama Gemma (converts text to vectors)
- **LLM**: Ollama Qwen3-VL:4b (generates responses)
- **Data Source**: King James Bible (markdown format)

## 🎨 Features

✅ Beautiful gradient UI with smooth animations
✅ Real-time Bible passage retrieval
✅ Contextually grounded AI responses
✅ Shows source references for transparency
✅ Responsive design (works on mobile)
✅ Fast semantic search across entire Bible
✅ Compassionate "AI Jesus" persona

## 🔧 Configuration

### Adjust Number of Retrieved Passages
In `rag_pipeline.py`, change the `top_k` parameter:
```python
rag = BibleRAG(top_k=5)  # Change 5 to desired number
```

### Adjust Chunk Size
In `build_embeddings.py`, modify:
```python
chunks = chunk_bible_text(texts, chunk_size=500)  # Adjust size
```

### Change AI Temperature
In `rag_pipeline.py`, modify the `generate_response` method:
```python
options={
    'temperature': 0.7,  # Lower = more focused, Higher = more creative
    'top_p': 0.9,
}
```

## 📝 Example Questions

Try asking:
- "What should I do when someone wrongs me?"
- "How should I treat my enemies?"
- "What does it mean to love my neighbor?"
- "How can I find peace in difficult times?"
- "What should I do when I am afraid?"
- "How should I handle my wealth?"
- "What is the meaning of faith?"

## 🐛 Troubleshooting

### Ollama Not Running
```powershell
# Check if Ollama is running
ollama list
```

### Models Not Found
```powershell
# List installed models
ollama list

# Install missing models
ollama pull embeddinggemma
ollama pull qwen3-vl:4b
```

### Vector Database Issues
```powershell
# Rebuild from scratch
Remove-Item -Recurse -Force chroma_db
python build_embeddings.py
```

### Slow Responses
- First query loads models into memory (slower)
- Subsequent queries are much faster
- Consider using smaller models if RAM limited

## 📊 Performance

- **Database Size**: ~31,000 verses across 66 books
- **Embedding Generation**: 10-30 minutes (one-time)
- **Query Time**: 1-3 seconds per question
- **Storage**: ~100-500MB for vector database

## 🎯 Next Steps / Enhancements

Consider adding:
1. **User History**: Save past questions and answers
2. **Verse Lookup**: Direct Bible verse search
3. **Multiple Translations**: Add NIV, ESV, etc.
4. **Export Answers**: Save as PDF or text
5. **API Mode**: REST API for other apps
6. **Docker**: Containerize the application
7. **Authentication**: User accounts
8. **Themes**: Light/dark mode toggle

## 📚 Resources

- [Ollama Documentation](https://ollama.com/docs)
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [King James Bible Source](https://github.com/awerkamp/markdown-king-james-version-holy-bible)

## 📄 License

This project uses:
- King James Bible (Public Domain)
- Open source software (see individual licenses)

## 🤝 Contributing

To improve this project:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

---

**Enjoy seeking wisdom with AI Jesus! 🙏**
