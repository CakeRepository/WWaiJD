"""
Quick start script for What Would AI Jesus Do
Checks prerequisites and guides through setup
"""

import sys
import subprocess
import os
from pathlib import Path


def check_python_version():
    """Check if Python version is 3.8 or higher."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8 or higher is required")
        print(f"   Current version: {version.major}.{version.minor}.{version.micro}")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    return True


def check_ollama():
    """Check if Ollama is installed and running."""
    try:
        import ollama
        ollama.list()
        print("✅ Ollama is installed and running")
        return True
    except ImportError:
        print("❌ Ollama Python package not installed")
        return False
    except Exception as e:
        print("❌ Ollama is not running or not accessible")
        print(f"   Please start Ollama first: {e}")
        return False


def check_ollama_models():
    """Check if required Ollama models are available."""
    try:
        import ollama
        models_list = ollama.list()
        model_names = [model['name'] for model in models_list.get('models', [])]
        
        has_gemma_embed = any('embeddinggemma' in name.lower() for name in model_names)
        has_gemma3 = any('gemma3:4b' in name.lower() for name in model_names)
        
        if not has_gemma_embed:
            print("⚠️  Embedding Gemma model not found")
            print("   Run: ollama pull embeddinggemma")
        else:
            print("✅ Gemma embeddings model found")
        
        if not has_gemma3:
            print("⚠️  Gemma3:4b model not found")
            print("   Run: ollama pull gemma3:4b")
        else:
            print("✅ Gemma3:4b model found")
        
        return has_gemma_embed and has_gemma3
    except Exception as e:
        print(f"⚠️  Could not check Ollama models: {e}")
        return False


def check_dependencies():
    """Check if required Python packages are installed."""
    required = ['flask', 'chromadb', 'ollama']
    missing = []
    
    for package in required:
        try:
            __import__(package)
            print(f"✅ {package} installed")
        except ImportError:
            print(f"❌ {package} not installed")
            missing.append(package)
    
    return len(missing) == 0


def check_vector_database():
    """Check if vector database exists."""
    db_path = Path("chroma_db")
    if db_path.exists() and any(db_path.iterdir()):
        print("✅ Vector database found")
        return True
    else:
        print("⚠️  Vector database not found")
        print("   Run: python build_embeddings.py")
        return False


def main():
    """Run startup checks and guide user."""
    print("=" * 60)
    print("What Would AI Jesus Do - Startup Check")
    print("=" * 60)
    print()
    
    all_checks_passed = True
    
    print("📋 Checking prerequisites...\n")
    
    # Check Python version
    if not check_python_version():
        all_checks_passed = False
    
    print()
    
    # Check dependencies
    print("📦 Checking Python packages...\n")
    if not check_dependencies():
        print("\n💡 Install missing packages with:")
        print("   pip install -r requirements.txt")
        all_checks_passed = False
    
    print()
    
    # Check Ollama
    print("🤖 Checking Ollama...\n")
    if not check_ollama():
        print("\n💡 Install Ollama from: https://ollama.com/")
        all_checks_passed = False
    else:
        check_ollama_models()
    
    print()
    
    # Check vector database
    print("📊 Checking vector database...\n")
    has_db = check_vector_database()
    
    print()
    print("=" * 60)
    
    if all_checks_passed and has_db:
        print("🎉 All checks passed! Ready to run.")
        print()
        print("Start the application with:")
        print("   python app.py")
        print()
        print("Then open: http://localhost:5000")
    else:
        print("⚠️  Setup incomplete. Please follow the steps above.")
        print()
        if all_checks_passed and not has_db:
            print("Next step: Build the vector database")
            print("   python build_embeddings.py")
            print()
            print("⚠️  Note: This will take 10-30 minutes depending on your system.")
    
    print("=" * 60)


if __name__ == "__main__":
    main()
