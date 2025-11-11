# Quick Reference Card

## 🚀 Essential Commands

### First Time Setup
```powershell
# 1. Install Ollama models
ollama pull embeddinggemma
ollama pull qwen3-vl:4b

# 2. Install Python packages
pip install -r requirements.txt

# 3. Build vector database (10-30 minutes)
python build_embeddings.py

# 4. Run application
python app.py
```

### Quick Setup (Windows PowerShell)
```powershell
# Run automated setup
.\setup.ps1
```

### Daily Usage
```powershell
# Just run this after first setup
python app.py

# Then open: http://localhost:5000
```

## 📁 Key Files

| File | Purpose |
|------|---------|
| `app.py` | Main web server |
| `rag_pipeline.py` | RAG logic |
| `build_embeddings.py` | Creates vector DB |
| `startup_check.py` | Verify setup |
| `setup.ps1` | Automated Windows setup |
| `static/index.html` | Web interface |

## 🔧 Useful Commands

### Check Setup Status
```powershell
python startup_check.py
```

### Test RAG Pipeline
```powershell
python rag_pipeline.py
```

### Check Ollama Models
```powershell
ollama list
```

### Rebuild Vector Database
```powershell
Remove-Item -Recurse -Force chroma_db
python build_embeddings.py
```

## 🌐 API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | Web interface |
| `/api/ask` | POST | Submit question |
| `/api/health` | GET | Check status |

### Example API Usage
```powershell
# Using curl (PowerShell)
curl -X POST http://localhost:5000/api/ask `
  -H "Content-Type: application/json" `
  -d '{"question": "What should I do when someone wrongs me?"}'
```

## 🐛 Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| "Ollama not running" | Start Ollama application |
| "Model not found" | Run `ollama pull embeddinggemma` and `ollama pull qwen3-vl:4b` |
| "Vector DB not found" | Run `python build_embeddings.py` |
| Port 5000 in use | Change port in `app.py` |
| Slow responses | First query loads models; wait a moment |

## 📊 Performance Tips

- **First Query**: 3-5 seconds (loading models)
- **Subsequent Queries**: 1-2 seconds
- **RAM Usage**: ~4-6 GB (with models loaded)
- **Disk Space**: ~2-3 GB (models + database)

## 🎯 Example Questions

```
✅ Good Questions:
- "What should I do when someone wrongs me?"
- "How can I find peace in difficult times?"
- "What does the Bible say about loving enemies?"

❌ Avoid:
- Non-Biblical questions
- Modern events not in Bible
- Personal information requests
```

## 📝 Project Structure

```
wwaijd/
├── 📄 Python Scripts (app, rag, build, startup)
├── 📄 Documentation (README, SETUP, this file)
├── 📁 static/ (HTML, CSS, JS)
├── 📁 bible-data/ (KJV markdown)
└── 📁 chroma_db/ (Vector database - created)
```

## 🔗 Important URLs

- **Application**: http://localhost:5000
- **Health Check**: http://localhost:5000/api/health
- **Ollama**: https://ollama.com/
- **ChromaDB Docs**: https://docs.trychroma.com/

---

**Need help? Check PROJECT_COMPLETE.md for full documentation!**
