"""
agent.py — J.A.M.A.L entry point.

This file contains ONLY the main loop and command routing.
All logic lives in the dedicated modules:
  profile.py  — identity & prompts
  memory.py   — conversation history
  llm.py      — model invocation & streaming
  search.py   — web search pipeline
  tools.py    — file system tools
  ui.py       — terminal display
"""

import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning)

import memory
import search
import tools
from llm    import get_llm, respond_chat, respond_rag, respond_code, invoke
from profile import set_language, welcome_message, t
from ui     import (
    HEADER, style_print, show_feature_list,
    streaming_open, streaming_close,
    divider, prompt_input, goodbye,
)

# Pass the LLM instance to memory so it can do smart compression
_llm = get_llm()


# ── Command handlers ──────────────────────────────────────────────────────────

def handle_search(query: str) -> None:
    if not query:
        style_print("SYSTEM", t("Gunakan: /search <pertanyaan>",
                                 "Usage: /search <question>"))
        return
    facts, sources = search.search(query)
    ctx = memory.get_context()
    streaming_open("JAMAL")
    ans = respond_rag(facts, query, ctx)
    streaming_close()
    if sources:
        style_print("WEB", sources)
    memory.add(t("User", "User"), query, _llm)
    memory.add("JAMAL", ans, _llm)


def handle_code(query: str) -> None:
    if not query:
        style_print("SYSTEM", t("Gunakan: /code <pertanyaan>",
                                 "Usage: /code <question>"))
        return
    ctx = memory.get_context()
    streaming_open("CODE")
    ans = respond_code(query, ctx)
    streaming_close()
    memory.add(t("User", "User"), query, _llm)
    memory.add("JAMAL", ans, _llm)


def handle_organize(folder: str) -> None:
    result = tools.organize_files(folder)
    style_print("FILE", result)
    memory.add(t("User", "User"), f"/organize {folder}", _llm)
    memory.add("JAMAL", result, _llm)


def handle_newfile(path: str) -> None:
    result = tools.create_file(path)
    style_print("FILE", result)
    memory.add(t("User", "User"), f"/newfile {path}", _llm)
    memory.add("JAMAL", result, _llm)


def handle_chat(user_input: str) -> None:
    """
    Auto-detect whether the query needs web search.
    Heuristics run first (instant); LLM classifier only fires when unsure.
    """
    if search.needs_web(user_input):
        facts, sources = search.search(user_input)
        ctx = memory.get_context()
        streaming_open("JAMAL")
        ans = respond_rag(facts, user_input, ctx)
        streaming_close()
        if sources:
            style_print("WEB", sources)
    else:
        ctx = memory.get_context()
        streaming_open("JAMAL")
        ans = respond_chat(user_input, ctx)
        streaming_close()

    memory.add(t("User", "User"), user_input, _llm)
    memory.add("JAMAL", ans, _llm)


# ── Main loop ─────────────────────────────────────────────────────────────────

def main() -> None:
    print(HEADER)
    style_print("JAMAL", welcome_message())
    show_feature_list()

    while True:
        try:
            divider()
            user_input = prompt_input()

            if not user_input:
                continue

            cmd   = user_input.lower()
            first = user_input.split()[0].lower()

            # ── Exit ─────────────────────────────────────────────
            if cmd in ("exit", "quit", "keluar", "/exit"):
                goodbye()
                break

            # ── /help ────────────────────────────────────────────
            elif first in ("/help", "help"):
                show_feature_list()

            # ── /clear ───────────────────────────────────────────
            elif first == "/clear":
                msg = memory.clear()
                style_print("SYSTEM", msg)

            # ── /lang ────────────────────────────────────────────
            elif first == "/lang":
                lang = user_input[5:].strip().lower()
                style_print("SYSTEM", set_language(lang))

            # ── /search ──────────────────────────────────────────
            elif first == "/search":
                handle_search(user_input[7:].strip())

            # ── /code ────────────────────────────────────────────
            elif first == "/code":
                handle_code(user_input[5:].strip())

            # ── /organize ────────────────────────────────────────
            elif first == "/organize":
                handle_organize(user_input[9:].strip())

            # ── /newfile ─────────────────────────────────────────
            elif first == "/newfile":
                handle_newfile(user_input[8:].strip())

            # ── Unknown command ───────────────────────────────────
            elif user_input.startswith("/"):
                style_print("SYSTEM",
                    t(f"Perintah tidak dikenal: '{first}'. Ketik /help untuk daftar perintah.",
                      f"Unknown command: '{first}'. Type /help for the command list."))

            # ── Normal chat ───────────────────────────────────────
            else:
                handle_chat(user_input)

        except KeyboardInterrupt:
            print()   # newline after ^C
            goodbye()
            break
        except Exception as e:
            style_print("ERROR", f"Terjadi kesalahan: {e}")


if __name__ == "__main__":
    main()
