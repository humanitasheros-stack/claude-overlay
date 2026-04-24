# Safe Removal Guide

If you have the Claude Overlay installed, follow these steps in order to fully remove it.

## Critical first

The overlay's systemd service is configured with `Restart=always`. **If you `pkill` the process without first stopping the service via systemctl, systemd will respawn it every 3 seconds.** Always stop via systemctl first.

## Step-by-step

1. **Stop the service:**
   ```
   systemctl --user stop claude-overlay.service
   ```

2. **Disable autostart:**
   ```
   systemctl --user disable claude-overlay.service
   ```

3. **Remove the service file** (so it can't be re-enabled):
   ```
   rm ~/.config/systemd/user/claude-overlay.service
   systemctl --user daemon-reload
   ```

4. **Kill any remaining processes:**
   ```
   pkill -9 -f claude-overlay
   ```

5. **Remove Claude Code hooks** that referenced the overlay. Edit `~/.claude/settings.json` and remove any hook entries pointing to `claude-code-shunt` or similar overlay binaries. Look in the `hooks.Stop` section. If you skip this, Claude Code will hang on every response trying to sync to a destination that no longer exists.

6. **Remove the socket file:**
   ```
   rm -f ~/.claude-overlay/overlay.sock
   ```

7. **Remove the overlay directory and any installed binaries:**
   ```
   rm -rf ~/.claude-overlay
   rm -f ~/.local/bin/claude-code-shunt
   ```

8. **Verify clean:**
   ```
   ls ~/.config/autostart/ 2>/dev/null | grep -i claude
   ps aux | grep -i claude-overlay | grep -v grep
   ```
   Both should return empty.

## What happens to the data

Your `~/.claude-overlay/data/coherence.jsonl` is removed by step 7. If you want to preserve historical data, copy it elsewhere before that step.
