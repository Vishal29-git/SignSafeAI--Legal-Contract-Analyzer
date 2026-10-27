import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from root project directory
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=BASE_DIR / '.env')

class Settings:
    OLLAMA_BASE_URL: str = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
    LLM_MODEL: str = os.getenv('LLM_MODEL', 'qwen2.5:3b')
    EMBED_MODEL: str = os.getenv('EMBED_MODEL', 'nomic-embed-text')
    TEMPERATURE: float = float(os.getenv('TEMPERATURE', '0.2'))
    
    DATA_DIR: Path = BASE_DIR / 'data'
    UPLOADS_DIR: Path = DATA_DIR / 'uploads'
    CHROMA_DIR: Path = DATA_DIR / 'chroma'
    DB_PATH: Path = DATA_DIR / 'contracts.db'

settings = Settings()

# Ensure directories exist
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
settings.UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
settings.CHROMA_DIR.mkdir(parents=True, exist_ok=True)
