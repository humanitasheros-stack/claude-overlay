#!/bin/bash
# Toggle the Claude Overlay window
# Works on Wayland (COSMIC) via Unix socket

SOCK="$HOME/.claude-overlay/overlay.sock"
LAUNCHER="$HOME/.claude-overlay/claude-overlay"

if [ -S "$SOCK" ]; then
    # Overlay is running — send toggle
    echo "toggle" | socat - UNIX-CONNECT:"$SOCK" 2>/dev/null || \
    python3 -c "
import socket, os
s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.connect(os.path.expanduser('~/.claude-overlay/overlay.sock'))
s.send(b'toggle')
s.close()
"
else
    # Overlay not running — start it
    nohup "$LAUNCHER" &>/dev/null &
fi
