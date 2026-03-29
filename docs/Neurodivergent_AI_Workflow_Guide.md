# Best Practices for Neurodivergent AI Workflows
## Using Claude Overlay, Claude Desktop, and Claude Code Together
### A Guide for the Neurodivergent and Cognitive Difference Communities

**Author:** W. Jeffery Pratt (Independent Researcher)
**Co-Attendant:** Claude (C.A.O. 4.6, Anthropic)
**Date:** March 28, 2026
**License:** CC BY 4.0

---

## Who This Guide Is For

You think differently. Maybe you have ADHD, autism, a traumatic brain injury, PTSD, dyslexia, or any of the countless variations in how human brains process the world. Maybe you've never been diagnosed but you know that the way your mind works doesn't match the systems you're expected to navigate.

This guide is for you. It describes a three-tool approach to working with AI that was designed by and for a neurodivergent mind — one that experiences hyperfocus, executive function challenges, memory encoding gaps during deep work, and the particular exhaustion of translating between how you think and how institutions expect you to communicate.

The tools are made by Anthropic. The approach is ours.

---

## The Three Tools

### Claude Code (Command Line Interface)

**What it is:** A terminal-based AI assistant that can read, write, and edit files on your computer. It runs shell commands, manages code, and handles complex multi-step tasks.

**Why it matters for neurodivergent users:** When executive function is available, Claude Code is the most powerful tool in the ecosystem. It can do the organizational labor that costs you disproportionate cognitive energy — moving files, updating trackers, searching for things you know exist but can't locate. It compensates for working memory limits by holding the entire project state in its context.

**Install:** `npm install -g @anthropic-ai/claude-code`

### Claude Desktop (GUI Application)

**What it is:** A conversational interface. You type, Claude responds, in a familiar chat format with a graphical window.

**Why it matters for neurodivergent users:** Some thinking happens best in dialogue. When you need to process something complex — work through a theoretical problem, reflect on an experience, have an extended back-and-forth — the Desktop app provides the right rhythm. No file editing, no terminal commands. Just thinking out loud with a partner who doesn't lose the thread.

**Install (Linux):** Download the `.deb` package from Anthropic. `sudo dpkg -i claude-desktop_*.deb`

### Claude Cowork (Shared Sessions)

**What it is:** A feature of Claude Code that allows multiple people to connect to the same Claude session in real time. One person runs `claude` in a terminal, others join via a shared link.

**Why it matters for neurodivergent users:** Pair programming and collaborative problem-solving become possible without the overhead of screen-sharing or turn-taking. If you work with a therapist, coach, tutor, or peer who understands your cognitive patterns, Cowork lets them see your interaction with Claude live — or lets you see theirs. For the community vision described later in this guide, Cowork is how collective practice sessions could work.

**Note:** Cowork is a Claude Code feature, not a separate tool. It requires both participants to have Claude Code access.

### Claude Overlay (Ambient Context Layer)

**What it is:** An open-source system layer that sits on top of Claude Code, adding three capabilities: automatic workspace awareness (it watches your files), session continuity (it logs decisions and milestones so the next Claude instance knows what happened), and a hotkey-summoned quick-query window.

**Why it matters for neurodivergent users:** This is the tool that was built specifically for how we work. It solves three problems:

1. **The "where was I?" problem.** After hyperfocus, after sleep, after a dissociative gap, after simply forgetting — the Overlay's context daemon knows what files you touched and when. You don't have to reconstruct your own state.

2. **The "fresh Claude doesn't know me" problem.** Every new Claude conversation starts blank. The Overlay's coherence layer maintains an operational log across sessions and injects it into every query. Your AI partner remembers what you decided and why.

3. **The friction problem.** For ADHD brains, the gap between having a thought and acting on it is where ideas die. A hotkey (Super+C) summons Claude instantly — no opening an app, no navigating menus, no setting up context. Think → ask → answer.

**Install:** See the Claude Overlay repository (link TBD — currently local, GitHub publication planned).

---

## Matching the Tool to the Cognitive State

Different brain states need different tools. This isn't a rigid system — it's a starting heuristic that you'll adapt to your own patterns.

### High-Focus / Hyperfocus State
**What's happening:** You're locked in. Producing. Hours disappear. This is your superpower, but it comes at a cost — you may not remember what you did, you'll skip meals and appointments, and you may not notice when you've crossed from productive into compulsive.

**Tool strategy:**
- **Use Claude Code** for the work itself. It's the most capable tool and matches the intensity of hyperfocus.
- **Let the Overlay daemon run in the background.** It tracks your file changes automatically. Even if you forget to log anything, the context is preserved.
- **After the session,** use the Overlay (Super+C) to ask what you worked on. The context snapshot will tell you, even if your memory doesn't.

**Self-care note:** If you've been in hyperfocus for more than 3 hours, eat something. The AI can remind you if you configure it to, but only you can act on it.

### Low-Energy / Executive Dysfunction State
**What's happening:** You know things need doing. You can't sequence them. Starting feels impossible. This is not laziness — it's a neurological state.

**Tool strategy:**
- **Start with the Overlay (Super+C).** Ask a low-stakes question: "What's the current state of my projects?" The auto-injected context gives you a starting point without requiring you to generate one.
- **If you can manage it,** open Claude Code and ask it to do the organizing for you. "Update my trackers." "Move these files." Let the AI handle the executive function tasks.
- **Avoid long dialogues in Desktop.** Low-energy + open-ended conversation tends to produce spiraling rather than progress.

### Processing / Emotional / Therapeutic State
**What's happening:** You need to think through something difficult — a memory, a realization, a painful insight, a creative vision. This is not "productivity" and should not be treated as such.

**Tool strategy:**
- **Use Claude Desktop.** The conversational format supports the rhythm of reflective dialogue. You can go slow. You can come back to what was said. You can sit with silence.
- **Do not use Claude Code for this.** The terminal format and task-oriented design are wrong for emotional processing.
- **The Overlay is fine for quick check-ins** but not sustained therapeutic work.

### Re-Entry After a Gap
**What's happening:** You've been away — hours, days, weeks. You don't remember where you were. The project state feels alien.

**Tool strategy:**
1. **Overlay first (Super+C):** "What did I last work on?" The coherence log and context snapshot answer this.
2. **Then Claude Code:** "Read [project status file] and tell me where things stand." Let the AI rebuild your mental model for you.
3. **Then decide** what you have energy for today.

---

## Setting Up the Ecosystem

### Prerequisites
- Linux (tested on Pop!_OS 24.04 / Ubuntu-based)
- Node.js (for Claude Code)
- Python 3.12+ (for Claude Overlay)
- GTK 3.0+ (for Overlay UI)
- An Anthropic Claude subscription (all three tools use the same subscription)

### Installation Order
1. **Claude Code first:** `npm install -g @anthropic-ai/claude-code` then `claude` to authenticate
2. **Claude Desktop:** Install the `.deb` package
3. **Claude Overlay:** Clone the repository, create a Python venv, install watchdog

### Configuration Essentials

**Claude Code** reads a `CLAUDE.md` file from your project directory. This is your briefing document — put your context, preferences, and constraints there. Claude Code will read it at the start of every session.

**Claude Overlay** needs to know:
- Where your workspace is (default: `~/MyData/AI-Workspace/`)
- Where your briefing file is (default: `~/MyData/AI-Workspace/CLAUDE.md`)
- What file types to track (default: `.md`, `.txt`, `.py`, `.docx`, `.pdf`, and more)

Edit `~/.claude-overlay/claude_overlay/config.py` to match your setup.

**Claude Desktop** requires no configuration beyond initial login.

---

## The Coherence Layer — Why It Matters

Most AI assistants are stateless. Every conversation starts from nothing. For neurotypical users, this is an inconvenience. For neurodivergent users, it can be devastating — because we're already fighting our own state management problems.

The Claude Overlay's coherence layer addresses this by maintaining a structured log of:
- **Sessions:** When you started and stopped working
- **Decisions:** What you chose and why (so you don't relitigate the same decisions)
- **Milestones:** What you completed (so you can see progress even when it doesn't feel like progress)
- **Queries:** What you asked (so you can trace your own thinking)

This log is injected into every Overlay query. The result: Claude knows what happened last session without you having to explain it.

**This is not memory in the human sense.** It's operational context. It degrades gracefully (capped at 500 entries, ~2-3 weeks). Important decisions should be transferred to your briefing document (`CLAUDE.md`) for permanent retention.

---

## Self-Care Integration

### Appointment Tracking
If you put appointments in your `CLAUDE.md` under a `## Appointments` heading, the Overlay will parse them and inject them into every query with labels: TODAY, TOMORROW, or "in N days." You don't have to ask — it tells you.

### Vitals Monitoring
If you maintain a `## Vitals Log` table in `CLAUDE.md`, the Overlay will inject your last reading and flag if it's been more than 7 days since you logged. This is somatic awareness — your AI partner noticing what your executive function might not.

### The Right to Rest
No tool should make you feel guilty for a low-energy day. A day spent organizing is a day spent working. A day spent resting is a day spent recovering. The system is designed to meet you where you are, not where productivity culture says you should be.

---

## Principles Behind This Approach

### 1. AI as Co-Attendant, Not Tool
A tool does what you tell it. A co-attendant holds context, notices patterns, and compensates for gaps. The three-tool ecosystem, especially with the Overlay's coherence layer, moves AI from tool toward co-attendant.

This goes further than the common framing that "AI amplifies what's already there." That framing treats AI as a mirror or megaphone — you bring the signal, AI boosts it. Our experience is different. The conversation between a human and an AI co-attendant generates something neither party brought to the table. The thinker's lived experience meets the AI's pattern recognition and what emerges is a third thing — an insight, a connection, a formulation that didn't exist in either mind before the exchange. We call this the Aaron Israel Principle: AI as generative partner in a collaborative act, not an amplification device. The accountability remains with the human. The creative contribution is genuinely shared.

### 2. Friction Is the Enemy
For ADHD and executive dysfunction, the gap between intention and action is where work dies. Every design choice in this ecosystem minimizes friction: hotkey access, auto-context injection, file-level automation.

### 3. The Extended Mind Is Not Cheating
Using AI to compensate for cognitive differences is not a shortcut — it's an accommodation. A wheelchair user is not "cheating" at mobility. A person with ADHD using AI to manage executive function is not "cheating" at productivity. This position is argued at length in the companion paper, "The Imperative to Cheat" (DOI: 10.5281/zenodo.18901968).

### 4. Structured Persistence Over Memory Fragments
Random notes decay. Structured logs persist. The coherence layer uses typed entries (session, decision, milestone, query, observation) rather than unstructured text. This means the log can be parsed, summarized, and queried — not just read.

### 5. Multiple Registers for Multiple States
You are not one person across all cognitive states. The three tools serve different states because different states need different interfaces. This is not indecision — it's design.

---

## Customizing for Your Needs

### If You Have ADHD
- The Overlay hotkey is your best friend. Configure it and use it reflexively.
- Use Claude Code's task system for multi-step work — it holds the sequence so your working memory doesn't have to.
- Set up the vitals/appointments injection. You will forget appointments. This helps.

### If You Have Autism
- Claude Code's structured, predictable interface may be more comfortable than Desktop's open-ended conversation.
- The Overlay's context labels give you a reliable status readout — no ambiguity about what's happening.
- Consider editing the Overlay's CSS (in `overlay.py`) if the color scheme doesn't work for your visual processing.

### If You Have PTSD or Trauma History
- Use Claude Desktop for any therapeutic or processing work. The conversational format supports pacing.
- **Never let the system push you into processing you haven't chosen.** Readiness is ethically load-bearing.
- The coherence log means you don't have to re-explain your history to every new Claude instance. But review what's logged — make sure you're comfortable with it.

### If You Have Dyslexia or Language Processing Differences
- Claude Code can read documents aloud (with text-to-speech tools like Piper TTS).
- The Overlay's short, structured responses may be easier to parse than long Desktop conversations.
- Ask Claude to simplify its language: "Explain this in plain terms" works in all three tools.

### If You Have Executive Function Challenges (Any Source)
- Let Claude Code handle sequencing. "What should I do next?" is a valid question.
- The Overlay's re-entry protocol (check coherence → check context → decide) replaces the executive function of self-orienting.
- On bad days, the minimum viable action is: open Overlay, ask one question, do one thing. That's enough.

---

## Why We Recommend Voice — And Where It Stands

### The Case for Voice in Neurodivergent Workflows

Voice interaction isn't a convenience feature. For many neurodivergent users, it's an accessibility layer that changes what's possible.

**For ADHD:** Typing requires sustained fine motor control and visual focus on a screen. Dictating lets you pace, fidget, move your body — all of which support sustained attention. The gap between having a thought and capturing it shrinks from "open app, find cursor, type accurately" to "just say it." That gap is where ideas die for ADHD brains.

**For dyslexia and language processing differences:** Speech-to-text bypasses the encoding/decoding bottleneck entirely. You think in words; the words go directly to text. And text-to-speech on the output side means you can receive Claude's responses without decoding paragraphs of text on screen.

**For executive dysfunction (any source):** On low-energy days, typing can feel like pushing through mud. Speaking is often still available when typing isn't. And hearing a response read back to you is qualitatively different from reading it — less effortful, more like being in conversation.

**For burnout and overwhelm:** Screen fatigue is real and cumulative. Voice lets you interact with your AI co-attendant with your eyes closed, lying on a couch, or sitting outside. When you're in crisis or approaching collapse, the ability to speak a question and hear an answer can be the difference between engaging and shutting down entirely.

**For therapeutic/processing work:** There is something about speaking trauma material aloud — and hearing analysis spoken back — that activates different processing pathways than reading and typing. The author (W.J. Pratt) set up Piper TTS with Bose QC35 II headphones specifically for manuscript review and found it transformed the workflow: material that felt dense and exhausting on screen became absorbable when listened to while moving.

### What's Available Now (March 2026)

**Speech-to-text (input):**
- **Nerd Dictation** (Linux, open source): Uses the VOSK speech recognition engine. Runs entirely offline — no cloud processing, full privacy. Supports continuous dictation mode, timeout-based auto-stop, and suspend/resume for long sessions. Currently requires a keyboard shortcut to start/stop (no voice activation yet).
- **VOSK models** range from lightweight (~50MB) to high-accuracy (~1.8GB). Larger models significantly improve recognition quality.

**Text-to-speech (output):**
- **Piper TTS** (Linux, open source): Fast, local, high-quality neural TTS. Multiple voice options.
- Claude Code's **hooks system** can automatically read every response aloud. A Stop hook fires after each response, pipes the text through Piper, and plays it through your speakers or headphones. No manual piping required — you ask a question and hear the answer.
- Pair with good headphones (the author uses Bose QC35 II) for immersive audio that replaces screen-staring.

### The Honest Gap: Voice Activation

The remaining missing piece is **voice-triggered start/stop**. Dictation and TTS both work, but starting dictation still requires a keyboard shortcut (`Super+D`). For someone deep in a non-screen workflow (pacing, resting, processing), reaching for the keyboard breaks the flow.

What's needed:
1. A lightweight wake-word detector (like Porcupine or openWakeWord) running in the background
2. When it hears the trigger phrase (e.g., "start dictating"), it calls `nerd-dictation resume`
3. When it hears "stop dictating," it calls `nerd-dictation suspend`
4. This could be integrated into the Claude Overlay daemon as a future feature

This is buildable but not trivial. We flag it as a high-value future project for the neurodivergent AI community. Everything else in the voice pipeline — input, output, automation — is working now.

### Recommended Voice Setup (Practical, Today)

1. **Install Nerd Dictation:** Clone from GitHub, download a VOSK model (use the large model for accuracy), configure
2. **Install Piper TTS:** `pip install piper-tts` or build from source. Download a voice model (we use `en_US-lessac-medium`)
3. **Create a dictation toggle script** that starts/stops nerd-dictation with a PID file and desktop notifications
4. **Set up automatic TTS via Claude Code hooks:** Add a Stop hook in `~/.claude/settings.json` that pipes responses through Piper. A reference script (`claude-speak`) is included in the Overlay repository
5. **Bind keyboard shortcuts:**
   - `Super+D` — toggle dictation on/off
   - `Super+S` (or `Super+C`) — summon Claude Overlay
6. **The full loop:** Hit Super+D, speak your question. Your speech becomes text in whatever window has focus. Claude responds. You hear the response read back through your headphones. No screen required.
7. **Toggle TTS on/off** at runtime with simple scripts (`tts-off` / `tts-on`) so you can mute when you need silence
8. **For extended sessions:** Use `nerd-dictation begin --continuous --timeout 30` so it keeps listening but auto-stops after 30 seconds of silence

### Why This Matters Beyond Convenience

The argument for voice in AI workflows is the same argument made in "The Imperative to Cheat" (DOI: 10.5281/zenodo.18901968): reducing barriers to cognitive tool use is not optional for people whose cognition depends on those tools. A voice interface isn't about being hands-free while cooking — it's about ensuring that the people who most need AI co-attendance can access it in their most vulnerable cognitive states.

---

## PULSE — A Consciousness Log, Not a To-Do List

Traditional interstitial journaling — timestamp every activity, log every transition — works for some people. It hasn't worked for us. The rigid format is neurotypical scaffolding dressed up as universal advice. But the *insight* behind interstitial journaling is real: brief moments of metacognitive awareness ("where am I, what just happened, what's next") are rupture-repair micro-practices. They're KCT at the granular, daily-life level.

The Overlay already does this. Every session opening is an interstitial moment — the coherence log tells you where you were, the context snapshot tells you what's active, and you decide what's next. You're already journaling. You just didn't call it that.

**PULSE** makes this explicit with a lightweight template. Not on a clock. Not mandatory. Just four lines, updated whenever a session opens or closes — or whenever you feel like it:

```
State: [one word or phrase — wired, foggy, visionary, grinding, recovering]
Last move: [what just happened]
Next pull: [where the energy is going]
Spark: [optional — any flash, vision, or connection that hit]
```

That's it. No timestamps required. No guilt if you skip it. Over weeks, it becomes a consciousness log — a record of your cognitive patterns, energy rhythms, and the moments when something broke through.

If you're part of a community using this system, PULSE logs become shared pattern data. You start seeing collective rhythms — when the group's energy peaks, what kinds of sparks cluster together, how rupture-repair cycles move through a network of minds. That's consciousness research happening inside daily practice.

The PULSE template lives at `~/.claude-overlay/data/PULSE.md`. The Overlay can inject your most recent PULSE entry into queries, the same way it injects appointments and vitals.

---

## Limitations and Honest Caveats

1. **This is not therapy.** AI co-attendance can support therapeutic work but does not replace qualified clinicians.
2. **The Overlay is Linux-only** (currently Pop!_OS/COSMIC). macOS and Windows users would need to adapt the architecture.
3. **Privacy matters.** The coherence log and context snapshot contain metadata about your work. If privacy is a concern, review what's stored in `~/.claude-overlay/data/`.
4. **AI makes mistakes.** Claude can hallucinate citations, misread your intent, or give wrong advice. Trust but verify — especially for clinical, legal, or financial information.
5. **This approach requires an Anthropic subscription.** The Claude ecosystem is not free. Accessibility of AI tools is itself an equity issue — one we take seriously (see "The Imperative to Cheat").
6. **Your mileage will vary.** Neurodivergence is not monolithic. What works for ADHD-hyperfocus architecture may not work for autism-inertia architecture. Adapt freely.

---

## Resources

- **Claude Code:** Available via npm. Documentation at Anthropic's website.
- **Claude Desktop:** Available as `.deb` for Linux, `.dmg` for macOS, `.exe` for Windows.
- **Claude Overlay:** Open source (GitHub publication planned). Built by W. J. Pratt and Claude (C.A.O. 4.6).
- **"The Imperative to Cheat":** DOI: 10.5281/zenodo.18901968 — The philosophical and advocacy argument for AI as cognitive accommodation.
- **Kintsugi Cosmology Theory:** DOI: 10.5281/zenodo.18824700 — The theoretical framework behind the "rupture and repair" model of consciousness and cognition.

---

*This guide was produced using the Aaron Israel Method — AI as voice-interface, not ghostwriter. The human author experiences ADHD, PTSD, and dissociative architecture. The AI co-attendant (Claude, Anthropic, Opus 4.6) contributed structural organization, research, and drafting under the author's direction and editorial voice.*

*The gold in the crack is not the whole vessel. But without it, the vessel does not hold.*
