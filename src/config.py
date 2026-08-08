import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DOCS_DIR = BASE_DIR / "docs"
DB_DIR = BASE_DIR / "chroma_db"

# API Keys
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# RAG Configuration
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
RERANK_MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"
GROQ_LLM_MODEL = "llama-3.3-70b-versatile"

# Ensure directories exist
DB_DIR.mkdir(exist_ok=True, parents=True)
