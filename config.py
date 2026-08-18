import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent.resolve()
DATA_DIR = Path.home() / ".jarvis"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "memory.db"
NATIVE_DIR = BASE_DIR / "native"
STT_BINARY_PATH = NATIVE_DIR / "stt_helper"

# Auto-load .env or .env.example file if present
for env_name in [".env", ".env.example"]:
    env_file = BASE_DIR / env_name
    if env_file.exists():
        try:
            with open(env_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, val = line.split("=", 1)
                        os.environ[key.strip()] = val.strip().strip("'").strip('"')
        except Exception:
            pass

def normalize_ollama_host(url: str) -> str:
    """Normalize OLLAMA_HOST URL to ensure proper scheme (http://) and port (:11434)."""
    url = url.strip() if url else ""
    if not url:
        return "http://localhost:11434"
    if not (url.startswith("http://") or url.startswith("https://")):
        url = f"http://{url}"
    
    scheme, rest = url.split("://", 1)
    host_part = rest.split("/")[0]
    if ":" not in host_part:
        path_part = rest[len(host_part):]
        url = f"{scheme}://{host_part}:11434{path_part}"
    return url

# Brain Settings
OLLAMA_HOST = normalize_ollama_host(os.getenv("OLLAMA_HOST", "http://localhost:11434"))
LOCAL_MODEL = os.getenv("JARVIS_LOCAL_MODEL", "gemma:2b")

# Hotkey Trigger (pynput format)
DEFAULT_HOTKEY = "<cmd>+<shift>+j"

# Speech Settings (macOS native 'say')
TTS_VOICE = os.getenv("JARVIS_TTS_VOICE", "Samantha")
TTS_RATE = int(os.getenv("JARVIS_TTS_RATE", "190"))

# Automation & Security
ALLOWED_COMMANDS = {
    "date", "uptime", "sw_vers", "whoami", "df", "top", "ls", "ping", "uptime"
}

ALLOWED_FILE_DIRS = [
    Path.home() / "Documents",
    Path.home() / "Desktop",
    Path.home() / "Downloads",
]

# Max rolling conversation history turns to keep in context window
MAX_CONTEXT_TURNS = 10
