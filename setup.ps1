# What Would AI Jesus Do - Setup Script
# This script helps you get started quickly on Windows

Write-Host ""
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "  What Would AI Jesus Do - Quick Setup" -ForegroundColor Yellow
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host ""

# Function to check if command exists
function Test-Command {
    param($Command)
    try {
        if (Get-Command $Command -ErrorAction Stop) {
            return $true
        }
    } catch {
        return $false
    }
}

# Check Python
Write-Host "Checking Python..." -ForegroundColor Yellow
if (Test-Command python) {
    $pythonVersion = python --version
    Write-Host "✓ $pythonVersion found" -ForegroundColor Green
} else {
    Write-Host "✗ Python not found. Please install Python 3.8+" -ForegroundColor Red
    Write-Host "  Download from: https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# Check Ollama
Write-Host "Checking Ollama..." -ForegroundColor Yellow
if (Test-Command ollama) {
    Write-Host "✓ Ollama found" -ForegroundColor Green
    
    # Check models
    Write-Host "Checking Ollama models..." -ForegroundColor Yellow
    $models = ollama list | Out-String
    
    if ($models -match "gemma") {
        Write-Host "✓ Gemma model found" -ForegroundColor Green
    } else {
        Write-Host "⚠ Gemma model not found" -ForegroundColor Yellow
        $response = Read-Host "Would you like to pull Gemma model now? (y/n)"
        if ($response -eq 'y') {
            Write-Host "Pulling Gemma model (this may take a while)..." -ForegroundColor Yellow
            ollama pull gemma
            Write-Host "✓ Gemma model installed" -ForegroundColor Green
        }
    }
    
    if ($models -match "qwen3-vl") {
        Write-Host "✓ Qwen3-VL:4b model found" -ForegroundColor Green
    } else {
        Write-Host "⚠ Qwen3-VL:4b model not found" -ForegroundColor Yellow
        $response = Read-Host "Would you like to pull Qwen3-VL:4b model now? (y/n)"
        if ($response -eq 'y') {
            Write-Host "Pulling Qwen3-VL:4b model (this may take a while)..." -ForegroundColor Yellow
            ollama pull qwen3-vl:4b
            Write-Host "✓ Qwen3-VL:4b model installed" -ForegroundColor Green
        }
    }
} else {
    Write-Host "✗ Ollama not found" -ForegroundColor Red
    Write-Host "  Download from: https://ollama.com/" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# Install Python packages
Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
if (Test-Path "requirements.txt") {
    pip install -r requirements.txt
    Write-Host "✓ Dependencies installed" -ForegroundColor Green
} else {
    Write-Host "✗ requirements.txt not found" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Check vector database
Write-Host "Checking vector database..." -ForegroundColor Yellow
if (Test-Path "chroma_db") {
    Write-Host "✓ Vector database found" -ForegroundColor Green
    Write-Host ""
    Write-Host "===============================================" -ForegroundColor Cyan
    Write-Host "  Setup Complete! Ready to run." -ForegroundColor Green
    Write-Host "===============================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Start the application with:" -ForegroundColor Yellow
    Write-Host "  python app.py" -ForegroundColor White
    Write-Host ""
    Write-Host "Then open: http://localhost:5000" -ForegroundColor Cyan
} else {
    Write-Host "⚠ Vector database not found" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "===============================================" -ForegroundColor Cyan
    Write-Host "  Setup Almost Complete!" -ForegroundColor Yellow
    Write-Host "===============================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Next step: Build the vector database" -ForegroundColor Yellow
    Write-Host "  python build_embeddings.py" -ForegroundColor White
    Write-Host ""
    Write-Host "⚠ Note: This will take 10-30 minutes" -ForegroundColor Yellow
    Write-Host ""
    $response = Read-Host "Would you like to start building the database now? (y/n)"
    if ($response -eq 'y') {
        Write-Host ""
        Write-Host "Building vector database..." -ForegroundColor Yellow
        python build_embeddings.py
    } else {
        Write-Host ""
        Write-Host "Run 'python build_embeddings.py' when ready" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host ""
