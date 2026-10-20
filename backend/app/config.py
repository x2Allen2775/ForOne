import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = BASE_DIR.parent
STORAGE_DIR = PROJECT_DIR / "storage"
LECTURES_DIR = STORAGE_DIR / "lectures"
MASTER_DIR = LECTURES_DIR / "master"
PERSONALIZED_DIR = LECTURES_DIR / "personalized"
DATABASE_DIR = STORAGE_DIR / "database"
DB_PATH = DATABASE_DIR / "forone.db"

# Ensure all directories exist
for p in [MASTER_DIR, PERSONALIZED_DIR, DATABASE_DIR]:
    p.mkdir(parents=True, exist_ok=True)

from dotenv import load_dotenv

# Load .env file
load_dotenv(BASE_DIR / ".env")
load_dotenv(PROJECT_DIR / ".env")

# Free Service Configurations
DATABASE_URL = f"sqlite:///{DB_PATH}"

# API keys for cloud services specified in the ForOne technical documentation
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
SYNCLABS_API_KEY = os.getenv("SYNCLABS_API_KEY", "")
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN", "")

# Whisper config
WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "base")  # 'tiny', 'base', 'small'
WHISPER_DEVICE = os.getenv("WHISPER_DEVICE", "cpu")  # CPU or Apple Silicon
