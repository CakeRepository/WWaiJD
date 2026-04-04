"""Shared Ollama model defaults for WWAIJD."""

import os

DEFAULT_EMBED_MODEL = os.getenv('WWAIJD_EMBED_MODEL', 'embeddinggemma')
DEFAULT_LLM_MODEL = os.getenv('WWAIJD_LLM_MODEL', 'gemma4:e2b')