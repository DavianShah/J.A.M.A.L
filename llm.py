"""
llm.py — LLM instance and all invoke helpers.

Streaming is enabled by default so the user sees tokens as they arrive
instead of waiting for the full response — makes a 3b model feel much faster.
"""

from __future__ import annotations
import sys
from langchain_ollama import OllamaLLM
from profile import system_prompt, rag_prompt, chat_prompt, code_prompt

# ── Model config ──────────────────────────────────────────────────────────────
# temperature=0.2 gives slightly more creative answers than 0.1
# while still being factually grounded.
_llm = OllamaLLM(model="qwen2.5-coder:3b", temperature=0.2)


# ── Public helpers ────────────────────────────────────────────────────────────

def get_llm() -> OllamaLLM:
    """Return the shared LLM instance (used by memory.py for compression)."""
    return _llm


def stream(prompt: str, prefix: str = "│ ") -> str:
    """
    Collect the full streamed response, then print it cleanly.
    Streaming token-by-token caused visible blank lines between numbered
    items because newlines were flushed before the next line arrived.
    Buffering first gives us clean, gap-free output.
    A progress dot is printed while waiting so the UI doesn't feel frozen.
    """
    full = ""
    try:
        print("│ ", end="", flush=True)  # show activity immediately
        dot_count = 0
        for chunk in _llm.stream(prompt):
            text = chunk if isinstance(chunk, str) else str(chunk)
            full += text
            # Print a dot every ~10 chunks so user sees progress
            dot_count += 1
            if dot_count % 10 == 0:
                sys.stdout.write(".")
                sys.stdout.flush()
        # Clear the progress dots, then print the clean buffered output
        sys.stdout.write("\r│ \033[K")   # carriage return + clear line
        sys.stdout.flush()
    except Exception:
        pass

    # Fallback if streaming failed or returned nothing
    if not full:
        full = _llm.invoke(prompt)

    full = full.strip()
    # Collapse multiple consecutive blank lines into one, then print
    import re
    cleaned = re.sub(r'\n{3,}', '\n\n', full)
    for line in cleaned.split("\n"):
        print(f"{prefix}{line}")
    return full.strip()


def invoke(prompt: str) -> str:
    """Non-streaming invoke — used for internal calls (keyword extraction, etc.)."""
    return _llm.invoke(prompt).strip()


# ── Response generators ───────────────────────────────────────────────────────

def respond_chat(user_input: str, context: str = "") -> str:
    """Standard chat response with streaming."""
    return stream(chat_prompt(user_input, context))


def respond_rag(facts: str, question: str, context: str = "") -> str:
    """Web-grounded response with streaming."""
    return stream(rag_prompt(facts, question, context))


def respond_code(user_input: str, context: str = "") -> str:
    """Code-focused response with streaming."""
    return stream(code_prompt(user_input, context))


def classify_needs_web(user_input: str) -> bool:
    """
    Ask the LLM to classify if a query needs live web data.
    Returns True if YES. Used only when heuristics are inconclusive.
    """
    prompt = (
        f"{system_prompt()}\n"
        f"Apakah pertanyaan ini membutuhkan data TERKINI dari internet untuk dijawab akurat? "
        f"Jawab HANYA: YES atau NO\n"
        f"Pertanyaan: {user_input}"
    )
    answer = invoke(prompt).upper()
    return "YES" in answer