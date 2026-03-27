# Claude Overlay — Operations Manual

## Quick Reference

| Action | Command |
|---|---|
| Start overlay | `~/.claude-overlay/claude-overlay` |
| Toggle visibility | **Super+C** or `~/.claude-overlay/toggle-overlay.sh` |
| Hide overlay | **Esc** (from within overlay) |
| Send query | Type question, press **Enter** |
| Check if running | `ls ~/.claude-overlay/overlay.sock` (exists = running) |
| Stop overlay | Close window or `echo quit \| python3 -c "import socket,os; s=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM); s.connect(os.path.expanduser('~/.claude-overlay/overlay.sock')); s.send(b'quit'); s.close()"` |
| View log | `cat ~/.claude-overlay/data/overlay.log` |
| View coherence | `cat ~/.claude-overlay/data/coherence.jsonl` |
| View context | `cat ~/.claude-overlay/data/context.json` |

## How It Works (Plain Language)

**When you launch the overlay**, three things happen:

1. **The context daemon starts watching** your workspace. Every time you create, edit, move, or delete a file, it updates its picture of what's going on. Think of it as peripheral vision — it's not reading your files, it's noticing them.

2. **The coherence layer loads** everything it remembers from previous sessions — what was decided, what milestones were reached, what you asked about. This is the briefing packet for whatever Claude instance answers your question.

3. **The overlay window appears.** A dark window with a text box. That's your interface.

**When you type a question and press Enter:**

1. The overlay grabs the current context snapshot (what files exist, what changed recently, which projects are active)
2. It grabs the coherence briefing (what happened in previous sessions)
3. It bundles both with your question
4. It sends everything to `claude -p` (Claude Code in single-prompt mode)
5. The response appears in the overlay window

**You are not billed separately for this.** It runs through Claude Code, which uses your existing Anthropic plan.

## What the Context Daemon Tracks

- Files with these extensions: `.md`, `.txt`, `.odt`, `.docx`, `.pdf`, `.py`, `.sh`, `.csv`, `.json`, `.html`, `.epub`, `.lua`, `.yaml`
- Organized by project (maps to your `_Active_Projects/` structure)
- Last 100 file change events
- 20 most recently modified files

**It ignores:** `_Archive/`, `node_modules/`, `readwise_data/`, `.git/`, `venv/`, `__pycache__/`

## What the Coherence Layer Records

Every entry has a timestamp, type, content, source, and tags. Types:

- **session** — "Session started via overlay" / "Session ended"
- **decision** — "Chose X because Y" (with reasoning field)
- **milestone** — "Completed X"
- **query** — What you asked + summary of what came back
- **observation** — What the system noticed (file changes, patterns)

The coherence log is append-only. It holds up to 500 entries before trimming old ones.

## Troubleshooting

### Overlay doesn't appear
- Is GTK available? Run: `python3 -c "import gi; gi.require_version('Gtk', '3.0'); print('OK')"`
- Check the log: `cat ~/.claude-overlay/data/overlay.log`
- Try launching manually: `~/.claude-overlay/claude-overlay`

### Super+C doesn't work
- COSMIC may need a restart to pick up new shortcuts
- Try: Log out → Log back in
- Or manually run: `~/.claude-overlay/toggle-overlay.sh`

### "claude not found" error
- Is Claude Code installed? Run: `which claude`
- If not: `npm install -g @anthropic-ai/claude-code`

### Queries time out
- Default timeout is 120 seconds
- Complex queries through Claude Code can take time
- Check your internet connection

### Context shows too many/few files
- Edit `~/.claude-overlay/claude_overlay/config.py`
- Adjust `TRACKED_EXTENSIONS`, `IGNORE_DIRS`, or `MAX_WATCH_DEPTH`

## Files You Might Want to Edit

| File | What to change |
|---|---|
| `config.py` | Watch paths, extensions, ignore dirs, token budget |
| `overlay.py` | CSS theme, window size, prompt construction |
| `coherence.py` | Briefing format, max entries, entry types |

## Auto-Start

The overlay is configured to start automatically via systemd:
```
~/.config/systemd/user/claude-overlay.service
```

To disable auto-start:
```bash
systemctl --user disable claude-overlay.service
```

To start/stop manually via systemd:
```bash
systemctl --user start claude-overlay.service
systemctl --user stop claude-overlay.service
```
