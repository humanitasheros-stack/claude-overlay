"""Entry point for running the overlay."""
import sys
import os

# Ensure the venv's packages are available
venv_site = os.path.expanduser("~/.claude-overlay/venv/lib/python3.12/site-packages")
if venv_site not in sys.path:
    sys.path.insert(0, venv_site)

from claude_overlay.overlay import run_overlay

if __name__ == "__main__":
    run_overlay()
