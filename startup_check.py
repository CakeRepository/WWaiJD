"""
Quick start script for What Would AI Jesus Do
Checks prerequisites and guides through setup
"""

import sys
import subprocess
import os
from pathlib import Path
from model_config import DEFAULT_EMBED_MODEL, DEFAULT_LLM_MODEL


def check_python_version() -> bool:
    """
    Check if the current Python version is 3.8 or higher.

    Args:
        None

    Returns:
        bool: True if Python version is >= 3.8, False otherwise.
    """
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8 or higher is required")
        print(f"   Current version: {version.major}.{version.minor}.{version.micro}")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    return True


def check_ollama() -> bool:
    """
    Check if the Ollama Python package is installed and the Ollama service is running.

    Args:
        None

    Returns:
        bool: True if Ollama is accessible, False otherwise.
    """
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


def check_ollama_models() -> bool:
    """
    Check if the required Ollama models are available.

    Verifies the presence of the configured embedding and generation models.

    Args:
        None

    Returns:
        bool: True if all required models are found, False otherwise.
    """
    try:
        import ollama
        models_list = ollama.list()
        model_names = []
        # Support both legacy dictionary response and new ListResponse object response
        if hasattr(models_list, 'models'):
            model_names = [m.model for m in models_list.models]
        elif isinstance(models_list, dict):
            model_names = [m.get('name', m.get('model', '')) for m in models_list.get('models', [])]
        else:
            model_names = [getattr(m, 'model', getattr(m, 'name', '')) for m in models_list]
        
        embed_model = DEFAULT_EMBED_MODEL.lower()
        llm_model = DEFAULT_LLM_MODEL.lower()
        has_gemma_embed = any(embed_model in name.lower() for name in model_names)
        has_llm_model = any(llm_model in name.lower() for name in model_names)
        
        if not has_gemma_embed:
            print(f"⚠️  {DEFAULT_EMBED_MODEL} model not found")
            print(f"   Run: ollama pull {DEFAULT_EMBED_MODEL}")
        else:
            print(f"✅ {DEFAULT_EMBED_MODEL} model found")
        
        if not has_llm_model:
            print(f"⚠️  {DEFAULT_LLM_MODEL} model not found")
            print(f"   Run: ollama pull {DEFAULT_LLM_MODEL}")
        else:
            print(f"✅ {DEFAULT_LLM_MODEL} model found")
        
        return has_gemma_embed and has_llm_model
    except Exception as e:
        print(f"⚠️  Could not check Ollama models: {e}")
        return False


def check_dependencies() -> bool:
    """
    Check if required Python packages are installed.

    Verifies installation of 'flask', 'chromadb', and 'ollama'.

    Args:
        None

    Returns:
        bool: True if all dependencies are installed, False otherwise.
    """
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


def check_vector_database() -> bool:
    """
    Check if the vector database directory exists and is not empty.

    Args:
        None

    Returns:
        bool: True if the database exists, False otherwise.
    """
    db_path = Path("chroma_db")
    if db_path.exists() and any(db_path.iterdir()):
        print("✅ Vector database found")
        return True
    else:
        print("⚠️  Vector database not found")
        print("   Run: python build_embeddings.py")
        return False


def main():
    """
    Run startup checks and guide the user through the setup process.

    Performs the following checks:
    1. Python version
    2. Python dependencies
    3. Ollama availability
    4. Ollama models
    5. Vector database existence

    Args:
        None

    Returns:
        None
    """
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
