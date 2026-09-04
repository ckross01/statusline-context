# statusline-context

A Claude Code status line that shows how full your context window is.

```
🧠 Opus 5 (1M context)  📁 projects  🧘 ██░░░░░░░░░░░░ 14% (140k/1.0M)
```

The bar fills up as the chat gets longer. The emoji and the color change too, so
one glance tells you how much room is left.

## Install

1. Save `statusline-context.py` anywhere. Make it runnable:

   ```
   chmod +x ~/.claude/statusline-context.py
   ```

2. Add this to `~/.claude/settings.json`:

   ```json
   {
     "statusLine": {
       "type": "command",
       "command": "/Users/YOU/.claude/statusline-context.py",
       "padding": 0
     }
   }
   ```

3. Start Claude Code. The bar shows up at the bottom.

Needs `python3`. Nothing else. No installs.

## The five levels

| Full | Color | faces | growth | fire | weather | moon |
|---|---|---|---|---|---|---|
| 0–24% | green | 🧘 | 🌱 | 🧊 | ☀️ | 🌑 |
| 25–49% | green | 🙂 | 🌿 | 🌡️ | 🌤️ | 🌒 |
| 50–74% | yellow | 😅 | 🌳 | 🔥 | ⛅ | 🌓 |
| 75–89% | orange | 😰 | 🍂 | 🔥 | 🌧️ | 🌔 |
| 90%+ | red | 🚨 | 🥀 | 🚨 | ⛈️ | 🌕 |

At 90% it also adds `⚠ compact soon` on the end.

## Pick a theme

Default is `faces`. To change it, set one env var:

```
export CLAUDE_STATUSLINE_THEME=growth
```

Choices: `faces` `growth` `fire` `weather` `moon`

## Set the window size by hand

The script guesses your window: 1M for a 1M model, else 200k. To force a number:

```
export CLAUDE_CONTEXT_WINDOW=200000
```

## How it works

Claude Code pipes a small JSON blob to the script on every redraw. The script
opens your session transcript, finds the last main-chain assistant turn, and adds
up its `input_tokens` + both cache token counts. That sum is your real context
use. Sidechains (subagents) are skipped.
