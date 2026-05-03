"""
ui.py — Terminal UI: header, styled boxes, feature list, streaming header.

All print/display logic lives here. Other modules import style_print
and streaming_header but never call print() for final output directly.
"""

from __future__ import annotations
from profile import FEATURES, t, is_id

# ── Box borders ───────────────────────────────────────────────────────────────
_BORDERS: dict[str, str] = {
    "JAMAL":  "╭── 🤖 JAMAL ASSISTANT ──────────────────────────",
    "SYSTEM": "╭── ⚙️  SYSTEM INFO ─────────────────────────────",
    "WEB":    "╭── 🌐 SUMBER REFERENSI ────────────────────────",
    "FILE":   "╭── 📂 FILE MANAGER ────────────────────────────",
    "CODE":   "╭── 💻 CODE EDITOR ─────────────────────────────",
    "ERROR":  "╭── ❌ ERROR ────────────────────────────────────",
}
_FOOTER = "╰" + "─" * 55
_LINE   = "━" * 60

# ── ASCII header ──────────────────────────────────────────────────────────────
HEADER = r"""
 ██████╗     █████╗      ███╗   ███╗      █████╗      ██╗     
  ╚══██║    ██╔══██╗     ████╗ ████║     ██╔══██╗     ██║     
     ██║    ███████║     ██╔████╔██║     ███████║     ██║     
██   ██║    ██╔══██║     ██║╚██╔╝██║     ██╔══██║     ██║     
╚█████╔╝ ██╗██║  ██║ ██╗ ██║ ╚═╝ ██║ ██╗ ██║  ██║ ██╗ ███████╗
 ╚════╝  ╚═╝╚═╝  ╚═╝ ╚═╝ ╚═╝     ╚═╝ ╚═╝ ╚═╝  ╚═╝ ╚═╝ ╚══════╝
    --- Your Authentic AI Collaborator ---
"""


# ── Public functions ──────────────────────────────────────────────────────────

def style_print(label: str, text: str) -> None:
    """Print a styled box with the given label and text content."""
    border = _BORDERS.get(label, _BORDERS["SYSTEM"])
    print(f"\n{border}")
    for line in text.strip().split("\n"):
        print(f"│ {line}")
    print(_FOOTER)


def streaming_open(label: str) -> None:
    """
    Open a styled box for streaming output.
    Call this BEFORE starting the stream, then let llm.stream() print tokens,
    then call streaming_close() when done.
    """
    border = _BORDERS.get(label, _BORDERS["SYSTEM"])
    print(f"\n{border}")
    print("│ ", end="", flush=True)


def streaming_close() -> None:
    """Close a streaming box."""
    print(f"\n{_FOOTER}")


def show_feature_list() -> None:
    title = t("Daftar perintah yang tersedia:", "Available commands:")
    lines = [title, ""]
    for cmd, desc in FEATURES.items():
        lines.append(f"  {cmd}")
        lines.append(f"    → {desc}")
    style_print("SYSTEM", "\n".join(lines))


def divider() -> None:
    print(f"\n{_LINE}")


def prompt_input() -> str:
    """Show the user input prompt and return stripped input."""
    return input(" 👤 YOU> ").strip()


def goodbye() -> None:
    msg = t("Sampai jumpa! Senang berinteraksi dengan Anda. 👋",
            "Goodbye! It was a pleasure. 👋")
    print(f"\n{msg}\n")
