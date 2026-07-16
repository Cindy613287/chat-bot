from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
KNOWLEDGE_DIR = ROOT_DIR / "knowledge"
MEMORY_FILE = ROOT_DIR / "memory.json"

APP_NAME = "知行 AI 学习助手"
DEFAULT_BASE_URL = "https://api.deepseek.com"
DEFAULT_MODEL = "deepseek-chat"

MAX_KNOWLEDGE_CHARS = 80_000
MAX_UPLOAD_BYTES = 2 * 1024 * 1024
MAX_HISTORY_MESSAGES = 14
