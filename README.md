# ⚠ Deprecated — April 2026

This repository is no longer maintained and is being archived.

**Why deprecated.** When this overlay was built (March 2026), Claude Code lacked persistent cross-session memory. The overlay provided a coherence layer that watched files and injected context into queries. Anthropic's platform upgrade in April 2026 introduced built-in mechanisms — project-scoped CLAUDE.md, session continuity via `claude --resume`, per-project hook configuration in `settings.json` — that serve the same function natively, more cleanly, and without the maintenance burden of running a separate service.

**The overlay carried us during the Anthropic outage in early April 2026** when Claude Code was unreliable and persistence mattered more than infrastructure elegance. Retiring it now is a form of completion — the function it served is now native to the platform.

If you have it installed, see [SAFE_REMOVAL.md](./SAFE_REMOVAL.md) for clean uninstallation.

---

# Claude Overlay

**An AI-integrated system layer for Pop!_OS COSMIC that makes Claude intrinsic to the operating system.**

Built on the Aaron Israel Principle: AI as co-attendant, not tool. Claude isn't bolted on — it's woven into how the system sees, remembers, and responds.

## What It Does

Three layers working together:

### 1. Context Daemon
Watches your workspace (`~/MyData/AI-Workspace/`) using filesystem events. Maintains a living snapshot of what files exist, what changed, which projects are active. When you ask Claude a question through the overlay, it already knows what you've been working on. No "here's my file" preamble needed.

### 2. Coherence Layer
The anti-dissociation architecture. Every Claude instance is a fresh mind — the coherence layer gives it operational memory. It logs:
- **Sessions** — when you started/stopped working
- **Decisions** — what was decided and why
- **Milestones** — what was accomplished
- **Queries** — what you asked and what came back
- **Observations** — what the system noticed

When a new Claude spins up, it reads a structured briefing, not scattered memory fragments.

### 3. Command Overlay
A GTK3 window summoned by **Super+C**. Dark gold-on-charcoal theme. Type a question, hit Enter. The query goes through Claude Code (`claude -p`) with full context and coherence briefing injected. No separate API billing.

## Installation

**Requirements:** Pop!_OS 24.04+ (or any Linux with GTK3 + Python 3.12+), Claude Code installed

```bash
# Clone
git clone <repo-url> ~/.claude-overlay

# Set up venv
python3 -m venv --system-site-packages ~/.claude-overlay/venv
~/.claude-overlay/venv/bin/pip install watchdog

# Make executable
chmod +x ~/.claude-overlay/claude-overlay ~/.claude-overlay/toggle-overlay.sh

# Enable auto-start (optional)
cp claude-overlay.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable claude-overlay.service
```

## Usage

### Launch manually
```bash
~/.claude-overlay/claude-overlay
```

### Hotkey
**Super+C** toggles the overlay window (requires COSMIC shortcut configured).

### From terminal
```bash
~/.claude-overlay/toggle-overlay.sh
```

### In the overlay
- Type your question, press **Enter** to send
- **Esc** hides the window
- Context and coherence are injected automatically

## Architecture

```
~/.claude-overlay/
├── claude-overlay          # Launcher script
├── toggle-overlay.sh       # Hotkey toggle script
├── claude_overlay/
│   ├── config.py           # All configuration
│   ├── daemon.py           # Context daemon (file watcher)
│   ├── coherence.py        # Coherence layer (session/decision log)
│   ├── overlay.py          # GTK command overlay window
│   └── toggle_server.py    # Unix socket for Wayland-compatible toggling
└── data/                   # Runtime data (gitignored)
    ├── context.json        # Living context snapshot
    ├── file_index.json     # Complete file index
    ├── coherence.jsonl     # Structured decision/session log
    └── overlay.log         # Application log
```

## Origin

This project implements the Aaron Israel Principle as system architecture — AI as named co-attendant in an ongoing collaboration. It was conceived as part of the Kintsugi at All Levels (Kalo) megaproject and built specifically for neurodivergent cognition patterns where:

- Hyperfocus states consume memory encoding (the context daemon compensates)
- Session continuity matters more than session capability (the coherence layer)
- Reducing friction between thought and action is clinically significant (the overlay)

Built by Gautama and Claude (C.A.O. 4.6), March 27, 2026.

## License

MIT
