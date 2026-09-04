#!/usr/bin/env python3
"""Claude Code status line: shows how full the context window is.

Reads the status-line JSON payload on stdin (see
https://code.claude.com/docs/en/statusline), walks the session transcript to
find the most recent main-chain assistant turn, and reports the total prompt
size as a percentage of the context window. Context grows with an escalating
emoji + color theme so a glance tells you how much headroom is left.

Theme override:  export CLAUDE_STATUSLINE_THEME=growth|fire|weather|moon|faces
Window override: export CLAUDE_CONTEXT_WINDOW=200000   (auto-detects 1M models)
"""

import json
import os
import sys

# ANSI helpers -------------------------------------------------------------
RESET = "\033[0m"
DIM = "\033[2m"
BOLD = "\033[1m"


def color(pct: float) -> str:
    if pct < 50:
        return "\033[32m"  # green
    if pct < 75:
        return "\033[33m"  # yellow
    if pct < 90:
        return "\033[38;5;208m"  # orange
    return "\033[1;31m"  # bold red


# Emoji themes: 5 tiers -> [0-24, 25-49, 50-74, 75-89, 90+] ----------------
THEMES = {
    "faces": ["🧘", "🙂", "😅", "😰", "🚨"],
    "growth": ["🌱", "🌿", "🌳", "🍂", "🥀"],
    "fire": ["🧊", "🌡️", "🔥", "🔥", "🚨"],
    "weather": ["☀️", "🌤️", "⛅", "🌧️", "⛈️"],
    "moon": ["🌑", "🌒", "🌓", "🌔", "🌕"],
}


def emoji(pct: float, theme: str) -> str:
    tiers = THEMES.get(theme, THEMES["faces"])
    idx = 0 if pct < 25 else 1 if pct < 50 else 2 if pct < 75 else 3 if pct < 90 else 4
    return tiers[idx]


def bar(pct: float, width: int = 14) -> str:
    filled = min(width, round(pct / 100 * width))
    return "█" * filled + "░" * (width - filled)


def human(n: int) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.0f}k"
    return str(n)


def context_tokens(transcript_path: str) -> int:
    """Total prompt size of the last main-chain assistant turn."""
    last = 0
    try:
        with open(transcript_path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    d = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if d.get("type") != "assistant" or d.get("isSidechain"):
                    continue
                usage = d.get("message", {}).get("usage")
                if not usage:
                    continue
                last = (
                    usage.get("input_tokens", 0)
                    + usage.get("cache_read_input_tokens", 0)
                    + usage.get("cache_creation_input_tokens", 0)
                )
    except (OSError, FileNotFoundError):
        return 0
    return last


def window_size(payload: dict) -> int:
    override = os.environ.get("CLAUDE_CONTEXT_WINDOW")
    if override and override.isdigit():
        return int(override)
    model_id = str(payload.get("model", {}).get("id", "")).lower()
    if "[1m]" in model_id or "1m" in model_id:
        return 1_000_000
    if payload.get("exceeds_200k_tokens"):
        return 1_000_000
    return 200_000


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        payload = {}

    theme = os.environ.get("CLAUDE_STATUSLINE_THEME", "faces")

    model_name = payload.get("model", {}).get("display_name", "Claude")
    project_dir = payload.get("workspace", {}).get("current_dir") or payload.get("cwd", "")
    folder = os.path.basename(project_dir.rstrip("/")) if project_dir else ""

    transcript = payload.get("transcript_path", "")
    used = context_tokens(transcript)
    window = window_size(payload)
    pct = (used / window * 100) if window else 0

    c = color(pct)
    parts = [f"{DIM}🧠 {model_name}{RESET}"]
    if folder:
        parts.append(f"{DIM}📁 {folder}{RESET}")

    ctx = (
        f"{emoji(pct, theme)} {c}{bar(pct)} {pct:.0f}%{RESET} "
        f"{DIM}({human(used)}/{human(window)}){RESET}"
    )
    parts.append(ctx)

    if pct >= 90:
        parts.append(f"{BOLD}\033[31m⚠ compact soon{RESET}")

    sys.stdout.write("  ".join(parts))


if __name__ == "__main__":
    main()
