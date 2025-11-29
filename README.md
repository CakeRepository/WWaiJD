# What Would AI Jesus Do (WWAIJD) ✝️

An AI-powered application that provides moral and spiritual guidance based on the Bible using advanced RAG (Retrieval Augmented Generation) technology. Ask any question and receive compassionate, biblically-grounded wisdom with relevant scripture references.

## ✨ Features

- 📖 **Grounded in Scripture** - All answers based on the Bible (35+ translations available!)
- 🤖 **Advanced AI** - Uses Ollama with Gemma embeddings and Gemma3:4b model
- 🔍 **Smart Retrieval** - RAG pipeline finds the most relevant passages
- 💬 **Beautiful Interface** - Clean, responsive web UI with gradient design
- 📚 **Bible Reader** - Built-in Bible browser to read any book, chapter, or verse
- 📜 **Multiple Versions** - KJV, ESV, NIV, NLT, NASB, NKJV, and 30+ more translations
- ⚡ **Real-time Streaming** - Watch responses generate in real-time
- 🎯 **Context-Aware** - Retrieves top 5 most relevant passages for each question
- 🌐 **REST API** - Easy integration with other applications

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+**
- **[Ollama](https://ollama.com/)** installed locally
- Required Ollama models:
  ```bash
  ollama pull embeddinggemma
  ollama pull gemma3:4b
  ```

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/CakeRepository/WWaiJD.git
   cd WWaiJD
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Download Bible versions**
   ```bash
   # Download popular versions (KJV, ESV, NIV, NLT, NASB, NKJV, etc.)
   python download_bibles.py
   
   # Or download ALL 35+ available versions
   python download_bibles.py --all
   ```

4. **Run setup check** (optional but recommended)
   ```bash
   python startup_check.py
   ```

5. **Build the vector database** (first time only - takes 10-30 minutes)
   ```bash
   python build_embeddings.py
   ```
   This processes all Bible versions and creates searchable embeddings.

6. **Run the application**
   ```bash
   python app.py
   ```

7. **Open your browser** to `http://localhost:5000`

### Windows PowerShell Quick Setup
```powershell
.\setup.ps1
```

## 💡 Usage

### Web Interface
1. Visit `http://localhost:5000`
2. Type your question in the search bar
3. Select your preferred Bible version
4. Examples:
   - "What should I do when someone wrongs me?"
   - "How can I find peace in difficult times?"
   - "What does it mean to love my neighbor?"
   - "How should I treat my enemies?"

### Bible Reader
- Click "Read the Bible" button
- Browse by Testament → Book → Chapter
- Search for specific passages
- View verses with verse numbers
- Switch between translations

### API Usage
```bash
# POST to /api/ask
curl -X POST http://localhost:5000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What should I do when someone wrongs me?", "version": "kjv"}'

# Streaming endpoint
curl -X POST http://localhost:5000/api/ask-stream \
  -H "Content-Type: application/json" \
  -d '{"question": "How can I find strength?", "version": "esv"}'
```

## 📁 Project Structure

```
wwaijd/
├── app.py                    # Main Flask web server with API endpoints
├── rag_pipeline.py           # RAG implementation (retrieval + generation)
├── build_embeddings.py       # Processes Bible and creates vector database
├── download_bibles.py        # Script to download Bible versions from GitHub
├── json_bible_utils.py       # JSON Bible file utilities
├── bible_utils.py            # Bible data handling (JSON + legacy MD support)
├── startup_check.py          # Validates prerequisites and setup
├── generate_favicons.py      # Generates favicon images
├── requirements.txt          # Python dependencies
├── setup.ps1                 # Windows PowerShell setup script
├── README.md                 # This file
├── SETUP.md                  # Detailed setup instructions
├── QUICKREF.md               # Quick reference commands
├── PROJECT_COMPLETE.md       # Project documentation
├── static/                   # Frontend files
│   ├── index.html            # Main web interface
│   ├── style.css             # Main page styling
│   ├── script.js             # Main page logic
│   ├── bible.html            # Bible reader interface
│   ├── bible.css             # Bible reader styling
│   ├── bible.js              # Bible reader logic
│   ├── passage.html          # Individual passage viewer
│   ├── passage.css           # Passage styling
│   ├── passage.js            # Passage logic
│   └── [favicons]            # Favicon files
├── bible-data/               # Bible data directory
│   └── json/                 # JSON Bible versions
│       ├── kjv.json          # King James Version
│       ├── esv.json          # English Standard Version
│       ├── niv.json          # New International Version
│       └── [35+ more...]     # Other translations
└── chroma_db/                # Vector database (generated after setup)
```

## 🔧 Technology Stack

- **Backend**: Flask (Python web framework)
- **Vector Database**: ChromaDB (stores Bible embeddings)
- **Embeddings**: Ollama Gemma (converts text to vectors)
- **LLM**: Ollama Gemma3:4b (generates compassionate responses)
- **Data Source**: [arron-taylor/bible-versions](https://github.com/arron-taylor/bible-versions) (35+ English translations)
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Server**: Waitress (production-ready WSGI server)

## 🎯 How It Works

1. **User asks a question** → "What should I do when someone wrongs me?"
2. **Embedding generation** → Question converted to vector using Gemma
3. **Semantic search** → ChromaDB finds 5 most relevant Bible passages
4. **Context building** → Passages formatted with references
5. **AI response** → Gemma3:4b generates compassionate answer as "AI Jesus"
6. **Display** → Answer shown with scripture references for transparency

## 📚 Additional Documentation

- **[SETUP.md](SETUP.md)** - Detailed installation and setup guide
- **[QUICKREF.md](QUICKREF.md)** - Quick reference commands and troubleshooting
- **[PROJECT_COMPLETE.md](PROJECT_COMPLETE.md)** - Comprehensive project documentation

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| "Ollama not running" | Start Ollama application |
| "Model not found" | Run `ollama pull embeddinggemma` and `ollama pull gemma3:4b` |
| "Vector DB not found" | Run `python build_embeddings.py` |
| Port 5000 in use | Change port in `app.py` (line 455) |
| Slow first response | Models loading into memory (normal) |

Run `python startup_check.py` to diagnose setup issues.

## 🙏 About

This project demonstrates how AI can be used to make ancient wisdom more accessible and provide spiritual guidance grounded in scripture. All responses are based on actual Bible passages, ensuring theological accuracy and transparency.

## 👨‍💻 Author

**Justin Trantham**  
🌐 [FlowDevs.io](https://www.flowdevs.io/team/justin-trantham)

## ☕ Support

If you find this project helpful, consider supporting its development:

[![Buy Me A Coffee](https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png)](https://buymeacoffee.com/wwaijd)

## 📄 License

This project is open source. The King James Bible text is in the public domain.
