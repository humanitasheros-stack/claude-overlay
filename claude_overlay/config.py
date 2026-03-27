"""Configuration for Claude Overlay."""
import os
from pathlib import Path

# Paths
HOME = Path.home()
OVERLAY_DIR = HOME / ".claude-overlay"
DATA_DIR = OVERLAY_DIR / "data"
WORKSPACE = HOME / "MyData" / "AI-Workspace"
CLAUDE_MD = WORKSPACE / "CLAUDE.md"
OPS_DIR = WORKSPACE / "Ops"

# Context daemon
CONTEXT_FILE = DATA_DIR / "context.json"
FILE_INDEX = DATA_DIR / "file_index.json"
WATCH_DIRS = [
    WORKSPACE,
]
# Extensions the daemon tracks
TRACKED_EXTENSIONS = {
    ".md", ".txt", ".odt", ".docx", ".pdf", ".py", ".sh",
    ".csv", ".json", ".html", ".epub", ".lua", ".yaml",
}
# Directories to ignore
IGNORE_DIRS = {
    "node_modules", ".git", "__pycache__", "venv",
    "_Archive",  # Don't track archived files for active context
    "readwise_data",  # 7000+ export files, not active work
    "chatgpt_conversations",  # Export archive
}
# Max depth for watching
MAX_WATCH_DEPTH = 4

# Coherence layer
COHERENCE_LOG = DATA_DIR / "coherence.jsonl"
COHERENCE_SUMMARY = DATA_DIR / "coherence_summary.md"
MAX_COHERENCE_ENTRIES = 500

# Command overlay
CLAUDE_CODE_BIN = str(HOME / ".npm-global" / "bin" / "claude")  # Absolute path — systemd strips PATH
OVERLAY_HOTKEY = "Super+c"
MAX_CONTEXT_TOKENS = 1500  # Slimmed down — less context = faster responses
QUERY_TIMEOUT = 300  # 5 minutes — Claude Code needs breathing room

# Ensure dirs exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
