"""
search.py — Web search with smart query optimization, retry logic,
and heuristic-first web-need detection.

Design goals:
  - Never do an LLM round-trip just to shorten a query if simple
    heuristics can do it faster.
  - Always retry with a fallback query if the first search fails
    or returns no usable results.
  - Rate-limit errors from DuckDuckGo are handled gracefully.
"""

from __future__ import annotations
import re
import time
from ddgs import DDGS
from profile import t, keyword_prompt
from llm import invoke, classify_needs_web

# ── Heuristic: keywords that almost always need fresh web data ────────────────
_WEB_TRIGGERS_ID = {
    "terbaru", "sekarang", "hari ini", "kemarin", "minggu ini", "bulan ini",
    "tahun ini", "berita", "harga", "jadwal", "cuaca", "terjadi", "update",
    "siapa yang menang", "hasil", "score", "skor", "live", "trending",
    "viral", "gempa", "banjir", "kebakaran", "kecelakaan", "meninggal",
    "dilantik", "terpilih", "dirilis", "launching", "rilis",
}
_WEB_TRIGGERS_EN = {
    "latest", "today", "now", "current", "news", "price", "schedule",
    "weather", "happened", "who won", "result", "live", "trending",
    "earthquake", "flood", "fire", "accident", "died", "elected",
    "released", "launched",
}
_QUESTION_WORDS   = {"apa", "siapa", "kapan", "dimana", "berapa", "bagaimana",
                     "what", "who", "when", "where", "how much", "how many"}
_YEAR_PATTERN     = re.compile(r"\b20(2[4-9]|3\d)\b")   # 2024–2039


# ── Public API ────────────────────────────────────────────────────────────────

def needs_web(text: str) -> bool:
    """
    Heuristic-first check. Only falls back to LLM if heuristics are
    inconclusive — saves 2–4 seconds on obvious cases.
    """
    lower = text.lower()

    # 1. Year pattern (e.g. "2025", "2026")
    if _YEAR_PATTERN.search(lower):
        return True

    # 2. Trigger keywords
    tokens = set(lower.split())
    if tokens & _WEB_TRIGGERS_ID or tokens & _WEB_TRIGGERS_EN:
        return True

    # 3. Question words paired with entity-like content (proper nouns / names)
    has_question_word = any(w in lower for w in _QUESTION_WORDS)
    has_proper_noun   = bool(re.search(r'\b[A-Z][a-z]{2,}', text))  # rough heuristic
    if has_question_word and has_proper_noun:
        return True

    # 4. LLM fallback for everything else
    return classify_needs_web(text)


def search(user_input: str) -> tuple[str, str]:
    """
    Full web search pipeline.
    Returns (facts_string, sources_string).

    Strategy:
      1. Extract a precise keyword via LLM.
      2. Search with region=id-id (most relevant for Indonesian users).
      3. If results are thin (< 2), retry without region restriction.
      4. If still nothing, retry with a simplified 2-word fallback query.
    """
    keyword = _extract_keyword(user_input)
    _log_searching(keyword)

    facts, sources = _ddgs_search(keyword, region="id-id", max_results=7)

    # Retry 1: drop region restriction
    if _is_thin(facts):
        facts, sources = _ddgs_search(keyword, max_results=7)

    # Retry 2: simplify query to first 2 meaningful words
    if _is_thin(facts):
        short_keyword = " ".join(keyword.split()[:2])
        _log_searching(short_keyword, retry=True)
        facts, sources = _ddgs_search(short_keyword, max_results=7)

    if _is_thin(facts):
        no_result = t(
            "⚠️  Tidak ditemukan hasil pencarian yang relevan. Saya akan menjawab dari pengetahuan internal.",
            "⚠️  No relevant search results found. I'll answer from internal knowledge."
        )
        return no_result, ""

    return facts, sources


# ── Internal helpers ──────────────────────────────────────────────────────────

def _extract_keyword(user_input: str) -> str:
    """
    Use LLM to extract a tight search keyword from the user's question.
    Takes only the first non-empty line to prevent multi-line hallucinations.
    """
    raw = invoke(keyword_prompt(user_input))
    # Take first line, strip punctuation clutter
    keyword = raw.split("\n")[0].strip().strip('"').strip("'").strip(".")
    # Remove common filler phrases the model sometimes adds
    for filler in ("kata kunci:", "keyword:", "search:", "pencarian:"):
        keyword = keyword.lower().replace(filler, "").strip()
    return keyword or user_input  # fallback to raw input if extraction fails


def _ddgs_search(keyword: str, region: str = "wt-wt",
                 max_results: int = 7) -> tuple[str, str]:
    """
    Execute a DuckDuckGo text search. Returns (facts, sources).
    Handles rate-limit errors with a short sleep + retry.
    """
    for attempt in range(2):
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(keyword, region=region,
                                         max_results=max_results))
            facts_list  = []
            sources_text = ""
            for i, r in enumerate(results, 1):
                body  = (r.get("body")  or "").strip()
                title = (r.get("title") or "").strip()
                href  = (r.get("href")  or "")
                if body:
                    facts_list.append(f"[Fakta {i}] {body}")
                sources_text += f"[{i}] {title}\n    Link: {href}\n"
            return "\n\n".join(facts_list), sources_text

        except Exception as e:
            err = str(e).lower()
            if "ratelimit" in err or "202" in err:
                if attempt == 0:
                    time.sleep(3)   # wait 3s then retry once
                    continue
            return f"⚠️  Search error: {e}", ""

    return "", ""


def _is_thin(facts: str) -> bool:
    """True if facts string is empty or just an error/no-result message."""
    return not facts or facts.startswith("⚠️")


def _log_searching(keyword: str, retry: bool = False) -> None:
    label = t("🔁 Mencoba ulang" if retry else "🔎 Mencari",
              "🔁 Retrying"     if retry else "🔎 Searching")
    print(f'\n   {label}: "{keyword}"...')
