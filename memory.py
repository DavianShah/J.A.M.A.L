"""
memory.py — Conversation memory with smart summarization.

Instead of simply dropping old turns when the buffer is full,
we compress them into a summary so early context is never fully lost.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from langchain_ollama import OllamaLLM

# ── Config ────────────────────────────────────────────────────────────────────
MAX_TURNS   = 12   # max full turns kept before compression
KEEP_RECENT =  6   # how many recent turns to keep verbatim after compression

# ── State ─────────────────────────────────────────────────────────────────────
_memory:  list[dict] = []   # {"role": str, "content": str}
_summary: str        = ""   # compressed older context


# ── Public API ────────────────────────────────────────────────────────────────

def add(role: str, content: str, llm: "OllamaLLM | None" = None) -> None:
    """
    Append a turn. If memory exceeds MAX_TURNS and an LLM is provided,
    compress the oldest half into a summary to preserve context.
    """
    global _summary
    _memory.append({"role": role, "content": content})

    if len(_memory) > MAX_TURNS * 2 and llm is not None:
        _compress(llm)


def get_context() -> str:
    """Return full context string: summary (if any) + recent turns."""
    parts = []
    if _summary:
        parts.append(f"[RINGKASAN PERCAKAPAN SEBELUMNYA]\n{_summary}\n")
    for m in _memory:
        parts.append(f"{m['role']}: {m['content']}")
    return "\n".join(parts)


def clear() -> str:
    """Wipe all memory and summary."""
    global _summary
    _memory.clear()
    _summary = ""
    return "✅ Riwayat percakapan dihapus."


def turn_count() -> int:
    return len(_memory) // 2


# ── Internal ──────────────────────────────────────────────────────────────────

def _compress(llm: "OllamaLLM") -> None:
    """
    Summarize the oldest turns into _summary, keep KEEP_RECENT turns verbatim.
    This runs silently in the background — the user never sees it.
    """
    global _summary, _memory

    cutoff   = len(_memory) - (KEEP_RECENT * 2)
    old_msgs = _memory[:cutoff]
    _memory  = _memory[cutoff:]

    old_text = "\n".join(f"{m['role']}: {m['content']}" for m in old_msgs)
    prompt   = (
        f"Berikut adalah potongan percakapan lama. "
        f"Ringkas menjadi 3-4 kalimat padat yang mencakup topik utama dan keputusan penting. "
        f"Balas HANYA ringkasan, tanpa penjelasan tambahan.\n\n"
        f"PERCAKAPAN:\n{old_text}\n\nRINGKASAN:"
    )
    try:
        new_summary = llm.invoke(prompt).strip()
        # Append to existing summary if there is one
        _summary = f"{_summary}\n{new_summary}".strip() if _summary else new_summary
    except Exception:
        # If compression fails, just drop the old turns silently
        pass
